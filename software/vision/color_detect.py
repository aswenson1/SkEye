"""
  keys 1-5 - pick a preset color (red, green, blue, yellow, orange)
  m - toggle showing the mask window
  q - quit (or close the window)
"""

import cv2
import numpy as np
from camera import Camera


PRESETS = {
    "red":    [((0, 120, 70), (10, 255, 255)), ((170, 120, 70), (179, 255, 255))],
    "green":  [((40, 70, 70), (80, 255, 255))],
    "blue":   [((95, 120, 70), (130, 255, 255))],
    "yellow": [((20, 100, 100), (35, 255, 255))],
    "orange": [((10, 120, 100), (20, 255, 255))],
}
PRESET_KEYS = {ord("1"): "red", ord("2"): "green", ord("3"): "blue",
               ord("4"): "yellow", ord("5"): "orange"}

MIN_AREA = 800
KERNEL = np.ones((5, 5), np.uint8)

def make_mask(hsv, ranges):
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lo, hi in ranges:
        mask |= cv2.inRange(hsv, np.array(lo), np.array(hi))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, KERNEL)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, KERNEL)
    return mask


def find_objects(mask, min_area=MIN_AREA):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    objects = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(c)
        m = cv2.moments(c)
        cx = int(m["m10"] / m["m00"]) if m["m00"] else x + w // 2
        cy = int(m["m01"] / m["m00"]) if m["m00"] else y + h // 2
        objects.append({"box": (x, y, w, h), "center": (cx, cy), "area": area})
    return objects


def draw(img, objects, label, color=(0, 255, 0)):
    for o in objects:
        x, y, w, h = o["box"]
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
        cv2.circle(img, o["center"], 4, (0, 0, 255), -1)
        cv2.putText(img, label, (x, max(y - 8, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


def main():
    current = "red"
    show_mask = True
    main_win = "color detect"
    last_index = -1

    with Camera(0) as cam:
        while True:
            f = cam.read()
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key in PRESET_KEYS:
                current = PRESET_KEYS[key]
            elif key == ord("m"):
                show_mask = not show_mask
                if not show_mask:
                    cv2.destroyWindow("mask")

            if f is None or f.index == last_index:
                continue
            last_index = f.index

            frame = f.image.copy()
            blurred = cv2.GaussianBlur(frame, (11, 11), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

            mask = make_mask(hsv, PRESETS[current])
            objects = find_objects(mask)
            draw(frame, objects, current)

            cv2.putText(frame, f"{current}: {len(objects)} found",
                        (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow(main_win, frame)
            if show_mask:
                cv2.imshow("mask", mask)

            # Make the window's X button work.
            if cv2.getWindowProperty(main_win, cv2.WND_PROP_VISIBLE) < 1:
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
