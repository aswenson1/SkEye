"""
Adds replay functionality to board.py
TODO: abstract replay functionality into replay.py

Press q to quit the program
Press s to save a replay (creates a new file in the replay directory)
    press s again to stop the recording
Press x to play back the most recent replay

References:
https://www.geeksforgeeks.org/python/get-current-date-and-time-using-python
https://www.geeksforgeeks.org/python/writing-to-file-in-python
https://www.geeksforgeeks.org/python/reading-and-writing-json-to-a-file-in-python
"""

import cv2
import numpy as np

# Imports for board test program (not related to class)
import os
from datetime import datetime as dt # replay
import json                         # replay
from camera_calibration import calibrate
from collections import deque
from dotenv import load_dotenv
from camera import Camera
from corner_detection import detect_markers, detect_corners_from_markers
from color_detect import PRESETS, PRESET_KEYS, make_mask, find_objects, draw


# Allows us to test different coordinate sizes
BOARD_SIZE = 100
# Final Coordinate Plane (0,0) top-left to (BOARD_SIZE, BOARD_SIZE) bottom-right
COORDS = np.array([[0, 0], [BOARD_SIZE, 0], [BOARD_SIZE, BOARD_SIZE], [0, BOARD_SIZE]], dtype=np.float32)


# Directory where replay files are stored

from pathlib import Path

REPLAY_DIR = Path("replays")


def load_latest_replay():
    files = [p for p in REPLAY_DIR.glob("*.jsonl") if p.is_file()]
    if not files:
        return None

    latest = max(files, key=lambda p: p.stat().st_mtime)
    points = []

    with latest.open("r") as replay:
        for line in replay:
            if line.strip():
                step = json.loads(line)
                points.append((float(step["bx"]), float(step["by"])))

    return points


class Board:
    def __init__(self, corners_px):
        # corners_px: 4x2 camera-pixel corners ordered TL, TR, BR, BL.
        self.corners_px = np.asarray(corners_px, dtype=np.float32).reshape(4, 2)
        # computes homography matrix using opencv built in function
        self._h = cv2.getPerspectiveTransform(self.corners_px, COORDS)
        # computes inverse matrix for conversion
        self._h_inv = np.linalg.inv(self._h)

    # applies matrix
    @staticmethod
    def _apply(points, matrix):
        pts = np.asarray(points, dtype=np.float32).reshape(-1, 1, 2)
        return cv2.perspectiveTransform(pts, matrix).reshape(-1, 2)

    # is the point on the board?
    @staticmethod
    def contains(point_board, margin=0.0):
        x, y = point_board
        return -margin <= x <= BOARD_SIZE + margin and -margin <= y <= BOARD_SIZE + margin

    # converts camera pixels to board coordinates
    def to_board(self, points_px):
        return self._apply(points_px, self._h)

    # converts board coordinates to camera pixels
    def to_camera(self, points_board):
        return self._apply(points_board, self._h_inv)

# test program to create a board and render it to the screen
if __name__ == "__main__":
    PLANE_PX = 500
    TRAIL_LEN = 40
    GRID_STEP = 10

    def draw_plane(trail):
        s = PLANE_PX
        canvas = np.zeros((s, s, 3), np.uint8)
        for v in range(0, BOARD_SIZE + 1, GRID_STEP):
            p = int(v / BOARD_SIZE * (s - 1))
            cv2.line(canvas, (p, 0), (p, s - 1), (50, 50, 50), 1)
            cv2.line(canvas, (0, p), (s - 1, p), (50, 50, 50), 1)
        pts = [(int(x / BOARD_SIZE * (s - 1)), int(y / BOARD_SIZE * (s - 1)))
               for x, y in trail]
        for a, b in zip(pts, pts[1:]):
            cv2.line(canvas, a, b, (0, 140, 0), 2)
        if pts:
            cv2.circle(canvas, pts[-1], 10, (0, 255, 0), -1)
            bx, by = trail[-1]
            cv2.putText(canvas, f"({bx:.0f}, {by:.0f})", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return canvas

    load_dotenv()
    current = "red"
    board = None
    trail = deque(maxlen=TRAIL_LEN)
    last_index = -1

    with Camera(int(os.environ["CAMERA_DEVICE_NO"])) as cam:

        corners = calibrate(cam)
        if corners is None:
            raise SystemExit("Calibration failed or was cancelled.")

        board = Board(corners)

        print("Board locked. Corners (px):", board.corners_px.tolist())
        print("1-5 changes color, r recalibrates, q quits")

        saving_replay = False
        recording_path = None

        playback_points = []
        playback_index = 0
        playing_replay = False

        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key in PRESET_KEYS:
                current = PRESET_KEYS[key]
                trail.clear()
            # recalibrate
            if key == ord("r"):
                new_corners = calibrate(cam)
                if new_corners is None:
                    print("Recalibration cancelled, keeping the old board.")
                else:
                    board = Board(new_corners)
                    print("Board relocked. Corners (px):", board.corners_px.tolist())
                trail.clear()
                last_index = -1
            # save a replay
            if key == ord("s"):
                if not saving_replay:
                    REPLAY_DIR.mkdir(parents=True, exist_ok=True)
                    timestamp = dt.now().strftime("%Y%m%d_%H%M%S_%f")
                    recording_path = REPLAY_DIR / f"{timestamp}.jsonl"
                    saving_replay = True
                    print(f"Recording to {recording_path}")
                else:
                    saving_replay = False
                    recording_path = None
                    print("Recording stopped.")
            # play a replay
            if key == ord("x"):
                points = load_latest_replay()
                if not points:
                    print("No replay found, or the latest replay is empty.")
                    playing_replay = False
                else:
                    playback_points = points
                    playback_index = 0
                    playing_replay = True
                    print(f"Playing replay ({len(playback_points)} points).")

            f = cam.read()
            if f is None or f.index == last_index:
                continue
            last_index = f.index
            frame = f.image.copy()

            hsv = cv2.cvtColor(cv2.GaussianBlur(frame, (11, 11), 0), cv2.COLOR_BGR2HSV)
            objects = find_objects(make_mask(hsv, PRESETS[current]))
            draw(frame, objects, current)

            if board is None:
                cv2.putText(frame, "Searching for markers...", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                cv2.polylines(frame, [board.corners_px.astype(np.int32)], True, (0, 255, 0), 2)
                if objects:
                    biggest = max(objects, key=lambda o: o["area"])
                    bx, by = board.to_board([biggest["center"]])[0]
                    if Board.contains((bx, by)):
                        trail.append((float(bx), float(by)))

                    if saving_replay:
                        replay_step = {
                            "object": current,
                            "bx": float(bx),
                            "by": float(by),
                        }
                        with recording_path.open("a") as replay:
                            json.dump(replay_step, replay)
                            replay.write("\n")


            cv2.imshow("camera", frame)
            if playing_replay:
                replay_trail = deque(
                    playback_points[:playback_index + 1],
                    maxlen=TRAIL_LEN,
                )
                cv2.imshow("plane", draw_plane(replay_trail))

                playback_index += 1
                if playback_index >= len(playback_points):
                    playing_replay = False
            else:
                cv2.imshow("plane", draw_plane(trail))


            # if cv2.getWindowProperty("camera", cv2.WND_PROP_VISIBLE) < 1:
            #     break
    cv2.destroyAllWindows()
