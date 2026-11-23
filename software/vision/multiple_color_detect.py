"""
multi_color_detect.py - track every preset color at the same time

Gets PRESETS from color_detect.py on each frame and tracks number of objects found of each color.

m - toggle showing the mask window
q - quit (or close the window)
"""

import cv2
import numpy as np
from camera import Camera
from color_detect import PRESETS, make_mask, find_objects, draw
from dotenv import load_dotenv
import os

# BGR colors used to draw each preset's boxes so they are easy to tell apart
DRAW_COLORS = {
    "red":    (0, 0, 255),
    "green":  (0, 255, 0),
    "blue":   (255, 0, 0),
    "yellow": (0, 255, 255),
    "orange": (0, 140, 255),
}


def detect_all(hsv, presets=PRESETS):
    found = {}
    combined = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for name, ranges in presets.items():
        mask = make_mask(hsv, ranges)
        found[name] = find_objects(mask)
        combined |= mask
    return found, combined


def main():
    show_mask = True
    main_win = "multi color detect"
    last_index = -1


    load_dotenv()
    with Camera(int(os.environ["CAMERA_DEVICE_NO"]), 0) as cam:
        while True:
            f = cam.read()
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("m"):
                show_mask = not show_mask
                if not show_mask:
                    cv2.destroyWindow("mask")

            if f is None or f.index == last_index:
                continue
            last_index = f.index

            frame = f.image.copy()
            blurred = cv2.GaussianBlur(frame, (11, 11), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

            found, mask = detect_all(hsv)


            
            for i, (name, objects) in enumerate(found.items()):
                color = DRAW_COLORS.get(name, (0, 255, 0))
                draw(frame, objects, name, color)
                cv2.putText(frame, f"{name}: {len(objects)} found",
                            (10, 25 + 25 * i), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, color, 2)

            cv2.imshow(main_win, frame)
            if show_mask:
                cv2.imshow("mask", mask)

            if cv2.getWindowProperty(main_win, cv2.WND_PROP_VISIBLE) < 1:
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()