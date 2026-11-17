"""
detect the four L-shaped pieces to map the corners of the board

CORNER_COLOR can be a key in CORNER_PRESETS below or any preset from color_detect.py.

Press q to quit the program
"""

import cv2
import numpy as np
from camera import Camera
from color_detect import PRESETS, make_mask
from dotenv import load_dotenv
import os

CORNER_COLOR = "red"
CORNER_PRESETS = {}

#smallest possible size accepted as a corner
MIN_AREA_FRAC = 0.0005

MIN_SOLIDITY = 0.25
MAX_SOLIDITY = 0.80

#true - board corner is inside vertex of the L, so the pieces sit outside the board
#false - board corner is outside vertex of the L, so the pieces are part of the board
USE_INNER_CORNER = True


def detect_shapes(image, color=CORNER_COLOR, min_area_frac=MIN_AREA_FRAC):
    blurred = cv2.GaussianBlur(image, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    mask = make_mask(hsv, CORNER_PRESETS.get(color) or PRESETS[color])

    min_area = min_area_frac * mask.shape[0] * mask.shape[1]
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    shapes = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue
        hull_area = cv2.contourArea(cv2.convexHull(c))
        if hull_area <= 0:
            continue
        solidity = area / hull_area
        if not (MIN_SOLIDITY <= solidity <= MAX_SOLIDITY):
            continue
        m = cv2.moments(c)
        shapes.append({
            "contour": c,
            "center": (m["m10"] / m["m00"], m["m01"] / m["m00"]),
            "area": area,
            "solidity": solidity,
        })
    return shapes


def _inner_vertex(contour):
    """The concave vertex of an L is its deepest convexity defect."""
    hull = cv2.convexHull(contour, returnPoints=False)
    if hull is None or len(hull) < 4:
        return None
    try:
        defects = cv2.convexityDefects(contour, hull)
    except cv2.error:
        return None
    if defects is None:
        return None

    defects = defects.reshape(-1, 4)
    far_idx = defects[np.argmax(defects[:, 3]), 2]
    return contour.reshape(-1, 2)[far_idx]


def _outer_vertex(contour, group_center):
    hull = cv2.convexHull(contour).reshape(-1, 2)
    dists = np.linalg.norm(hull - group_center, axis=1)
    return hull[np.argmax(dists)]


def detect_corners_from_shapes(shapes):
    if len(shapes) != 4:
        return None

    group_center = np.array([s["center"] for s in shapes]).mean(axis=0)

    pts = []
    for s in shapes:
        if USE_INNER_CORNER:
            p = _inner_vertex(s["contour"])
        else:
            p = _outer_vertex(s["contour"], group_center)
        if p is None:
            return None
        pts.append(p)
    pts = np.array(pts, dtype=np.int32)

    #put the four points in drawing order
    sums = pts.sum(axis=1)
    diffs = pts[:, 0] - pts[:, 1]
    order = [np.argmin(sums),
             np.argmax(diffs),
             np.argmax(sums),
             np.argmin(diffs)]

    if len(set(order)) != 4:
        return None
    return pts[order]


def detect_corners(image):
    return detect_corners_from_shapes(detect_shapes(image))


def main():
    load_dotenv()
    with Camera(int(os.environ["CAMERA_DEVICE_NO"]), 0) as cam:
        while True:
            frame = cam.read()
            if frame is None:
                continue

            img = frame.image.copy()
            shapes = detect_shapes(img)
            cv2.drawContours(img, [s["contour"] for s in shapes], -1, (0, 255, 0), 2)

            board_bounds = detect_corners_from_shapes(shapes)
            if board_bounds is not None:
                cv2.polylines(img, [board_bounds], True, (0, 255, 0), 3)
                for p in board_bounds:
                    cv2.circle(img, tuple(int(v) for v in p), 6, (255, 0, 255), -1)
                print("board_bounds:", board_bounds)

            cv2.putText(img, f"{CORNER_COLOR} L pieces: {len(shapes)}/4", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow("L Detection", img)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()