import cv2
import pygame
import numpy as np
import os
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from dotenv import load_dotenv

from camera import Camera
from camera_calibration import calibrate
from color_detect import PRESETS, make_mask, find_objects, draw

from fire_scenario import EXAMPLE_SCENARIO, Scenario

#  Constants

BOARD_SIZE = 100
COORDS     = np.array([[0,0],[BOARD_SIZE,0],[BOARD_SIZE,BOARD_SIZE],[0,BOARD_SIZE]], dtype=np.float32)
CELL_SIZE  = 60
HUD_HEIGHT = 80

#  Board

class Board:
    def __init__(self, corners_px):
        self.corners_px = np.asarray(corners_px, dtype=np.float32).reshape(4, 2)
        self._h     = cv2.getPerspectiveTransform(self.corners_px, COORDS)
        self._h_inv = np.linalg.inv(self._h)

    @staticmethod
    def _apply(points, matrix):
        pts = np.asarray(points, dtype=np.float32).reshape(-1, 1, 2)
        return cv2.perspectiveTransform(pts, matrix).reshape(-1, 2)

    @staticmethod
    def contains(point_board, margin=0.0):
        x, y = point_board
        return -margin <= x <= BOARD_SIZE + margin and -margin <= y <= BOARD_SIZE + margin

    def to_board(self, points_px):
        return self._apply(points_px, self._h)


#  Game state

class Phase(Enum):
    SETUP  = auto()
    ACTIVE = auto()
    WIN    = auto()
    LOSS   = auto()


@dataclass
class TokenState:
    pos: tuple[int, int]
    hp:  int


@dataclass
class GameState:
    scenario:        Scenario
    firefighter:     TokenState
    trapped:         TokenState
    env:             dict          # scenario-specific state (e.g. fire, smoke)
    phase:           Phase = Phase.SETUP
    turn:            int   = 0
    ff_found_patient: bool = False

    #  Reachability

    def neighbors(self, cell):
        col, row = cell
        candidates = [(col-1,row-1),(col,row-1),(col+1,row-1),
                      (col-1,row),(col+1,row),
                      (col-1,row+1),(col,row+1),(col+1,row+1)]
        return [
            nb for nb in candidates
            if 0 <= nb[0] < self.scenario.cols
            and 0 <= nb[1] < self.scenario.rows
            and frozenset([cell, nb]) not in self.scenario.walls
        ]

    def reachable(self, start, max_steps, blocked: set = frozenset()):
        """BFS from start up to max_steps. Returns {cell: steps} for all reachable cells."""
        visited = {start: 0}
        queue   = deque([start])
        while queue:
            cell  = queue.popleft()
            steps = visited[cell]
            if steps >= max_steps:
                continue
            for nb in self.neighbors(cell):
                if nb not in visited and nb not in blocked:
                    visited[nb] = steps + 1
                    queue.append(nb)
        return visited

    #  Step

    def commit_step(self, ff_dest, tp_dest) -> list[str]:
        if self.phase != Phase.ACTIVE:
            return []

        events = []
        self.turn += 1

        # Move firefighter (fire cells are blocked)
        if ff_dest and ff_dest != self.firefighter.pos:
            if ff_dest in self.reachable(self.firefighter.pos, self.scenario.firefighter_moves, blocked=self.env.get("fire", set())):
                self.firefighter.pos = ff_dest
                events.append(f"Firefighter moved to {ff_dest}.")
            else:
                events.append(f"Firefighter move to {ff_dest} is invalid — skipped.")

        # Check escort
        if not self.ff_found_patient:
            if self.firefighter.pos == self.trapped.pos or self.trapped.pos in self.neighbors(self.firefighter.pos):
                self.ff_found_patient = True
                events.append("Firefighter has reached the patient!")

        # Move trapped person (only if escorted, fire cells blocked)
        if tp_dest and tp_dest != self.trapped.pos:
            if not self.ff_found_patient:
                events.append("Patient cannot move — firefighter has not reached them yet.")
            elif tp_dest in self.reachable(self.trapped.pos, self.scenario.trapped_moves, blocked=self.env.get("fire", set())):
                self.trapped.pos = tp_dest
                events.append(f"Patient moved to {tp_dest}.")
            else:
                events.append(f"Patient move to {tp_dest} is invalid — skipped.")

        # Scenario hooks
        events += self.scenario.on_step_end(self)
        result  = self.scenario.check_win_loss(self)
        if result is not None:
            self.phase = result

        return events


def new_game(scenario: Scenario) -> GameState:
    return GameState(
        scenario    = scenario,
        firefighter = TokenState(pos=scenario.firefighter_start, hp=scenario.firefighter_hp),
        trapped     = TokenState(pos=scenario.trapped_start,     hp=scenario.trapped_hp),
        env         = scenario.initial_env(),
    )


#  CV

def detect_both(frame, board: Board, scenario: Scenario):
    hsv = cv2.cvtColor(cv2.GaussianBlur(frame, (11, 11), 0), cv2.COLOR_BGR2HSV)

    ff_objects = find_objects(make_mask(hsv, PRESETS[scenario.firefighter_color]))
    tp_objects = find_objects(make_mask(hsv, PRESETS[scenario.trapped_color]))

    draw(frame, ff_objects, scenario.firefighter_color)
    draw(frame, tp_objects, scenario.trapped_color)

    def best_pos(objects):
        if not objects:
            return None
        center   = max(objects, key=lambda o: o["area"])["center"]
        board_pt = tuple(board.to_board([center])[0])
        return board_pt if Board.contains(board_pt) else None

    return best_pos(ff_objects), best_pos(tp_objects)


def board_to_grid(board_pos, scenario: Scenario):
    bx, by = board_pos
    col = int(bx / BOARD_SIZE * scenario.cols)
    row = int(by / BOARD_SIZE * scenario.rows)
    return (max(0, min(scenario.cols - 1, col)),
            max(0, min(scenario.rows - 1, row)))


#  Pygame rendering

C_BG      = (40,  40,  40)
C_GRID    = (80,  80,  80)
C_WALL    = (200, 200, 200)
C_EXIT    = (0,   220, 100)
C_FF      = (220, 60,  60)
C_TRAPPED = (60,  100, 220)
C_HUD_BG  = (20,  20,  20)
C_TEXT    = (230, 230, 230)
C_WIN     = (30,  180, 30)
C_LOSS    = (180, 30,  30)

# Scenario-supplied env keys to colors — renderable if present in env
ENV_COLORS = {
    "fire":  (220, 100, 0),
    "smoke": (120, 120, 120),
}


def render(screen, font, big_font, state: GameState, pending_ff, pending_tp):
    scenario = state.scenario
    screen.fill(C_BG)

    # Cells
    for col in range(scenario.cols):
        for row in range(scenario.rows):
            cell = (col, row)
            rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)

            # Draw env layers in order (smoke under fire)
            cell_color = C_BG
            for key in ("smoke", "fire"):
                if key in state.env and cell in state.env[key]:
                    cell_color = ENV_COLORS[key]

            if cell == scenario.exit_cell:
                cell_color = C_EXIT

            pygame.draw.rect(screen, cell_color, rect)
            pygame.draw.rect(screen, C_GRID, rect, 1)

    # Walls
    for w in scenario.walls:
        a, b   = tuple(w)
        ac, ar = a
        bc, br = b
        if ac == bc:  # horizontal wall
            top_row = min(ar, br) + 1
            x0 = ac * CELL_SIZE
            y  = top_row * CELL_SIZE
            pygame.draw.line(screen, C_WALL, (x0, y), (x0 + CELL_SIZE, y), 3)
        else:         # vertical wall
            left_col = min(ac, bc) + 1
            x  = left_col * CELL_SIZE
            y0 = ar * CELL_SIZE
            pygame.draw.line(screen, C_WALL, (x, y0), (x, y0 + CELL_SIZE), 3)

    # Tokens
    for token, color in ((state.firefighter, C_FF), (state.trapped, C_TRAPPED)):
        col, row = token.pos
        cx = col * CELL_SIZE + CELL_SIZE // 2
        cy = row * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(screen, color, (cx, cy), CELL_SIZE // 3)

    # Pending positions (live CV detections, not yet committed)
    for pending, color, label in (
        (pending_ff, C_FF,      "Firefighter"),
        (pending_tp, C_TRAPPED, "Patient"),
    ):
        if pending is None:
            continue
        col, row  = pending
        cx = col * CELL_SIZE + CELL_SIZE // 2
        cy = row * CELL_SIZE + CELL_SIZE // 2

        # Hollow circle to distinguish from committed position
        pygame.draw.circle(screen, color, (cx, cy), CELL_SIZE // 3, 2)

        # Check validity
        if label == "Firefighter":
            blocked = state.env.get("fire", set())
            valid   = pending in state.reachable(state.firefighter.pos, state.scenario.firefighter_moves, blocked)
        else:
            blocked = state.env.get("fire", set())
            valid   = state.ff_found_patient and pending in state.reachable(state.trapped.pos, state.scenario.trapped_moves, blocked)

        if not valid:
            warning = font.render("Invalid", True, (255, 60, 60))
            screen.blit(warning, (cx + CELL_SIZE // 2, cy - 10))

    # HUD
    hud_y = scenario.rows * CELL_SIZE
    pygame.draw.rect(screen, C_HUD_BG, pygame.Rect(0, hud_y, scenario.cols * CELL_SIZE, HUD_HEIGHT))
    screen.blit(font.render(f"Firefighter HP : {state.firefighter.hp}  Turn: {state.turn}", True, C_FF),      (20, hud_y + 15))
    screen.blit(font.render(f"Patient HP     : {state.trapped.hp}",                          True, C_TRAPPED), (20, hud_y + 45))

    # Win / loss overlay
    if state.phase in (Phase.WIN, Phase.LOSS):
        overlay = pygame.Surface((scenario.cols * CELL_SIZE, scenario.rows * CELL_SIZE), pygame.SRCALPHA)
        color   = C_WIN if state.phase == Phase.WIN else C_LOSS
        overlay.fill((*color, 180))
        screen.blit(overlay, (0, 0))
        label = "Successful Rescue!" if state.phase == Phase.WIN else "Rescue Failed."
        text  = big_font.render(label, True, (255, 255, 255))
        screen.blit(text, text.get_rect(center=(scenario.cols * CELL_SIZE // 2, scenario.rows * CELL_SIZE // 2)))

    pygame.display.flip()


def render_setup(screen, font, scenario: Scenario):
    screen.fill(C_BG)
    for i, line in enumerate(scenario.setup_instructions(scenario)):
        screen.blit(font.render(line, True, C_TEXT), (40, 80 + i * 40))
    pygame.display.flip()


#  Main loop

def main():
    load_dotenv()
    scenario = EXAMPLE_SCENARIO

    pygame.init()
    screen   = pygame.display.set_mode((scenario.cols * CELL_SIZE, scenario.rows * CELL_SIZE + HUD_HEIGHT))
    pygame.display.set_caption(f"Fire Evacuation — {scenario.name}")
    font     = pygame.font.SysFont("monospace", 20)
    big_font = pygame.font.SysFont("monospace", 36, bold=True)
    clock    = pygame.time.Clock()

    state      = new_game(scenario)
    board      = None
    last_index = -1
    pending_ff = None
    pending_tp = None

    with Camera(int(os.environ["CAMERA_DEVICE_NO"])) as cam:
        corners = calibrate(cam)
        if corners is None:
            raise SystemExit("Calibration failed.")
        board = Board(corners)
        print("Board locked. SPACE to start, N to commit a step, R to recalibrate, Q to quit.")

        running = True
        while running:

            # OpenCV input
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                running = False
            if key == ord("r"):
                new_corners = calibrate(cam)
                if new_corners is not None:
                    board = Board(new_corners)

            # Capture + detect
            f = cam.read()
            if f is not None and f.index != last_index:
                last_index = f.index
                frame = f.image.copy()
                pending_ff, pending_tp = detect_both(frame, board, scenario)
                cv2.polylines(frame, [board.corners_px.astype(np.int32)], True, (0, 255, 0), 2)
                cv2.imshow("camera", frame)

            # Pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE and state.phase == Phase.SETUP:
                        state.phase = Phase.ACTIVE
                        print("Game started.")
                    elif event.key == pygame.K_n and state.phase == Phase.ACTIVE:
                        ff_grid = board_to_grid(pending_ff, scenario) if pending_ff else None
                        tp_grid = board_to_grid(pending_tp, scenario) if pending_tp else None
                        for e in state.commit_step(ff_grid, tp_grid):
                            print(e)
                    elif event.key == pygame.K_r and state.phase in (Phase.WIN, Phase.LOSS):
                        state = new_game(scenario)

            # Render
            if state.phase == Phase.SETUP:
                render_setup(screen, font, scenario)
            else:
                ff_grid_pending = board_to_grid(pending_ff, scenario) if pending_ff else None
                tp_grid_pending = board_to_grid(pending_tp, scenario) if pending_tp else None
                render(screen, font, big_font, state, ff_grid_pending, tp_grid_pending)

            clock.tick(30)

    cv2.destroyAllWindows()
    pygame.quit()


if __name__ == "__main__":
    main()
