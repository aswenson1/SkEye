"""
Detect a brightly colored object within the board

COLOR_TO_DETECT can be any preset from color_detect.py

Press q to quit the program
"""

COLOR_TO_DETECT = "red"

import cv2
import numpy as np
from camera import Camera
from corner_detection import detect_corners
from color_detect import PRESETS, make_mask, find_objects, draw


def main():
    with Camera(1,0) as cam:
        while True:
            frame = cam.read()
            if frame is None:
                continue

            img = frame.image

            board_bounds = detect_corners(img)
            cv2.polylines(img, [board_bounds], True, (0, 255, 0), 3)

            if board_bounds is not None:
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

                color_mask = make_mask(hsv, PRESETS[COLOR_TO_DETECT])

                board_mask = np.zeros(img.shape[:2], dtype=np.uint8)
                cv2.fillPoly(board_mask, [board_bounds.astype(np.int32)], 255)

                objects = find_objects(cv2.bitwise_and(color_mask, board_mask))

                if objects:
                    draw(img, objects, "object")
                    print("Objects in board:", objects)

            cv2.imshow("Board", img)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
