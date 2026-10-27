"""
Detect the four ArUco markers at the corners of the board (6x6_250 ids 0 to 4) [2]

Press q to quit the program

References:
1. https://www.geeksforgeeks.org/computer-vision/detecting-aruco-markers-with-opencv-and-python-1
2. https://www.arucogrid.com/dictionaries/6x6-250
"""

import cv2
import numpy as np
from camera import Camera

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
detector = cv2.aruco.ArucoDetector(aruco_dict, cv2.aruco.DetectorParameters())

"""
Detects all visible ArUco markers
"""
def detect_markers(image):
    gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = detector.detectMarkers(gray_img)
    return corners, ids


"""
Attempts to find the corners of the board

Returns a NumPy array with the xy coordinates of each corner of the board
Returns None if not all four ArUco markers are detected
"""
def detect_corners(image):
    corners, ids = detect_markers(image)
    return detect_corners_from_markers(corners, ids)


def detect_corners_from_markers(corners, ids):
    if len(corners) != 4:
        return None

    marker_centers = np.array([
        marker[0].mean(axis=0) for marker in corners
    ])

    group_center = marker_centers.mean(axis=0)

    box = np.array([
        marker[0][np.argmax(np.linalg.norm(marker[0] - group_center, axis=1))]
        for marker in corners
    ], dtype=np.int32)

    # Put the four selected corners in drawing order
    sums = box.sum(axis=1)
    diffs = box[:, 0] - box[:, 1]

    return np.array([
        box[np.argmin(sums)],   # top-left
        box[np.argmax(diffs)],  # top-right
        box[np.argmax(sums)],   # bottom-right
        box[np.argmin(diffs)],  # bottom-left
    ])


def main():
    with Camera(1,0) as cam:
        while True:
            frame = cam.read()
            if frame is None:
                continue

            img = frame.image
            corners, ids = detect_markers(img)

            if ids is not None:
                cv2.aruco.drawDetectedMarkers(img, corners, ids)

            board_bounds = detect_corners_from_markers(corners, ids)
            cv2.polylines(img, [board_bounds], True, (0, 255, 0), 3)

            if board_bounds is not None:
                print("board_bounds:", board_bounds)

            cv2.imshow("ArUco Detection", img)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
