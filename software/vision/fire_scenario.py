"""
Everything specific to the fire evacuation scenario.
Swap this file out (or add more scenario files) to create new scenarios.
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core import GameState, Phase


#  Hooks

def on_step_end(state: GameState) -> list[str]:
    """Called at the end of each step. Handles spread and HP decay."""
    events = []

    # HP decay from smoke
    for token, label in ((state.firefighter, "Firefighter"), (state.trapped, "Patient")):
        if token.pos in state.env["smoke"]:
            token.hp -= 1
            events.append(f"{label} is in smoke — HP now {token.hp}.")

    # Fire spreads to one random adjacent non-wall cell per fire cell
    new_fire = set()
    for cell in state.env["fire"]:
        candidates = [nb for nb in state.neighbors(cell) if nb not in state.env["fire"]]
        if candidates:
            new_fire.add(random.choice(candidates))
    state.env["fire"] |= new_fire
    state.env["smoke"] |= state.env["fire"]

    # Smoke spreads 2 steps from any smoke cell, ignoring walls
    frontier = set(state.env["smoke"])
    for _ in range(2):
        next_frontier = set()
        for cell in frontier:
            col, row = cell
            for nb in [(col+1,row),(col-1,row),(col,row+1),(col,row-1)]:
                if 0 <= nb[0] < state.scenario.cols and 0 <= nb[1] < state.scenario.rows:
                    if nb not in state.env["smoke"]:
                        next_frontier.add(nb)
        state.env["smoke"] |= next_frontier
        frontier = next_frontier

    return events


def check_win_loss(state: GameState):
    """Returns a Phase if the game has ended, otherwise None."""
    from core import Phase
    if state.firefighter.hp <= 0 or state.trapped.hp <= 0:
        return Phase.LOSS
    if state.trapped.pos == state.scenario.exit_cell and state.ff_found_patient:
        return Phase.WIN
    return None


def setup_instructions(scenario: Scenario) -> list[str]:
    return [
        "Place tokens on the board:",
        f"  RED token   → cell {scenario.firefighter_start}",
        f"  BLUE token  → cell {scenario.trapped_start}",
        "",
        "Press SPACE when ready.",
    ]


#  Scenario dataclass

@dataclass
class Scenario:
    name:               str
    cols:               int
    rows:               int
    walls:              set[frozenset]
    fire_origin:        tuple[int, int]
    exit_cell:          tuple[int, int]
    firefighter_start:  tuple[int, int]
    trapped_start:      tuple[int, int]
    firefighter_color:  str = "red"
    trapped_color:      str = "blue"
    firefighter_moves:  int = 4
    trapped_moves:      int = 2
    firefighter_hp:     int = 10
    trapped_hp:         int = 5

    # Hooks — default to the fire scenario implementations above
    on_step_end:         callable = field(default=on_step_end,         repr=False)
    check_win_loss:      callable = field(default=check_win_loss,      repr=False)
    setup_instructions:  callable = field(default=setup_instructions,  repr=False)

    # Initial environment state — anything a scenario's hooks need to track
    def initial_env(self) -> dict:
        return {
            "fire":  {self.fire_origin},
            "smoke": {self.fire_origin},
        }


#  Wall helpers

def wall(a, b):
    return frozenset([a, b])

def h_wall(walls, row, col_start, col_end):
    """Blocks passage between row-1 and row for columns col_start..col_end-1."""
    for c in range(col_start, col_end):
        walls.add(wall((c, row - 1), (c, row)))

def v_wall(walls, col, row_start, row_end):
    """Blocks passage between col-1 and col for rows row_start..row_end-1."""
    for r in range(row_start, row_end):
        walls.add(wall((col - 1, r), (col, r)))


#  Example scenario

def _build_example_walls():
    walls = set()

    # Vertical dividers
    v_wall(walls, 3, 0, 4)   # left cluster | center (rows 0–3)
    v_wall(walls, 7, 0, 4)   # center | right cluster (rows 0–3)
    v_wall(walls, 3, 6, 10)  # left big room | right big room (rows 6–9)
    v_wall(walls, 5, 4, 6)   # central column in mid-section

    # Horizontal dividers
    h_wall(walls, 4, 0, 3)   # bottom of left rooms
    h_wall(walls, 4, 7, 10)  # bottom of right rooms
    h_wall(walls, 6, 0, 5)   # top of lower-left big room
    h_wall(walls, 6, 5, 10)  # top of lower-right big room

    #  Doorways (remove individual wall segments to open passages)

    # Top-left room → center hallway (gap in vertical wall at col 3, row 2)
    walls.discard(wall((2, 2), (3, 2)))

    # Top-right room → center hallway (gap in vertical wall at col 7, row 2)
    walls.discard(wall((6, 2), (7, 2)))

    # Top-left room → lower-left big room (gap in horizontal wall at row 4, col 1)
    walls.discard(wall((1, 3), (1, 4)))

    # Top-right room → lower-right big room (gap in horizontal wall at row 4, col 8)
    walls.discard(wall((8, 3), (8, 4)))

    # Lower-left big room → mid-section (gap in horizontal wall at row 6, col 1)
    walls.discard(wall((1, 5), (1, 6)))

    # Lower-right big room → mid-section (gap in horizontal wall at row 6, col 7)
    walls.discard(wall((7, 5), (7, 6)))

    # Left big room → right big room (gap in vertical wall at col 3, row 8)
    walls.discard(wall((2, 8), (3, 8)))

    return walls


EXAMPLE_SCENARIO = Scenario(
    name              = "example",
    cols              = 10,
    rows              = 10,
    walls             = _build_example_walls(),
    fire_origin       = (9, 8),
    exit_cell         = (0, 5),
    firefighter_start = (0, 5),
    trapped_start     = (9, 2),
)
