"""
new corner detection method using dots rather than arucos.
WIP

dot_detection.py - detect the four brightly colored dots at the corners of the board

Place one dot of CORNER_COLOR on each corner of the workable area. The center of
each dot is treated as the corner of the board.

Press q to quit the program
"""

import cv2
import numpy as np
from camera import Camera
from color_detect import PRESETS, make_mask, find_objects, draw
from dotenv import load_dotenv
import os

CORNER_COLOR = "magenta"
CORNER_PRESETS = {
    "magenta": [((140, 100, 70), (165, 255, 255))],
}

# Dots are much smaller than the objects color_detect looks for (default 800)
CORNER_MIN_AREA = 150


def detect_dots(image, color=CORNER_COLOR, min_area=CORNER_MIN_AREA):
    """
    Detects all visible dots of the corner color
    Returns a list of dicts with "box", "center" and "area" (see color_detect.find_objects)
    """
    blurred = cv2.GaussianBlur(image, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    mask = make_mask(hsv, CORNER_PRESETS.get(color) or PRESETS[color])
    return find_objects(mask, min_area=min_area)


def detect_corners_from_dots(dots):
    """
    Orders four detected dots into board corners
    Returns a NumPy array with the xy coordinates of each corner of the board,
    in the order top-left, top-right, bottom-right, bottom-left
    Returns None if exactly four dots were not detected
    """
    if len(dots) != 4:
        return None

    pts = np.array([d["center"] for d in dots], dtype=np.int32)

    sums = pts.sum(axis=1)
    diffs = pts[:, 0] - pts[:, 1]

    return np.array([
        pts[np.argmin(sums)],
        pts[np.argmax(diffs)],
        pts[np.argmax(sums)],
        pts[np.argmin(diffs)],
    ])


def detect_corners(image):
    """
    Attempts to find the corners of the board

    Returns a NumPy array with the xy coordinates of each corner of the board
    Returns None if not all four dots are detected
    """
    return detect_corners_from_dots(detect_dots(image))


def main():
    load_dotenv()
    with Camera(int(os.environ["CAMERA_DEVICE_NO"]), 0) as cam:
        while True:
            frame = cam.read()
            if frame is None:
                continue

            img = frame.image.copy()
            dots = detect_dots(img)
            draw(img, dots, "corner")

            board_bounds = detect_corners_from_dots(dots)
            if board_bounds is not None:
                cv2.polylines(img, [board_bounds], True, (0, 255, 0), 3)
                print("board_bounds:", board_bounds)

            cv2.putText(img, f"{CORNER_COLOR} dots: {len(dots)}/4", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow("Corner Detection", img)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()