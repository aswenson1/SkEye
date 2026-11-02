"""
camera_calibration.py - camera utilities for SkEye

Allows for calibration of the camera based on the four 
corner markers.

References: 

https://docs.opencv.org/4.13.0/dc/dbb/tutorial_py_calibration.html
"""

from camera import Camera
from dotenv import load_dotenv
from collections import deque
import cv2
import os
import time
import sys
import numpy as np
from corner_detection import detect_markers, detect_corners_from_markers


# Config Variables!
load_dotenv() # loads variables specific to each developer
STABLE_FRAMES = 30            
CONNECT_TIMEOUT_S = 5.0
EDGE_MARGIN_PX = 10
MIN_BOARD_AREA_FRAC = 0.15 
MAX_ASPECT_SKEW = 0.35
MIN_BRIGHTNESS = 60
MAX_BRIGHTNESS = 200
MIN_SHARPNESS = 50.0
MAX_JITTER_PX = 2.0 
 
GREEN, RED = (0, 200, 0), (0, 0, 255)

# Tests return a status boolean and a message
# Checks if all four corner markers were found
def check_markers(ids):
    found = set() if ids is None else set(int(i) for i in ids.flatten())
    missing = {0, 1, 2, 3} - found
    if missing:
        return False, f"Markers missing: {sorted(missing)}"
    if found != {0, 1, 2, 3}:
        return False, f"Unexpected markers visible: {sorted(found - {0, 1, 2, 3})}"
    return True, "All 4 markers detected"

# Checks if the board is in frame correctly or not
def check_in_frame(board, shape):
    h, w = shape[:2]
    m = EDGE_MARGIN_PX
    ok = np.all((board[:, 0] >= m) & (board[:, 0] <= w - m) &
                (board[:, 1] >= m) & (board[:, 1] <= h - m))
    return bool(ok), ("Board fully in frame" if ok
                      else "Board too close to / outside frame edge")

# check if environment is bright enough
def check_brightness(gray):
    mean = float(gray.mean())
    ok = MIN_BRIGHTNESS <= mean <= MAX_BRIGHTNESS
    return ok, f"Brightness {mean:.0f} (want {MIN_BRIGHTNESS}-{MAX_BRIGHTNESS})"
 
 # check if camera quality is within a specific margin
def check_sharpness(gray):
    score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    ok = score >= MIN_SHARPNESS
    return ok, f"Sharpness {score:.0f} (min {MIN_SHARPNESS:.0f})"
 
# check to see if the hardware is holding the camera steady
def check_stability(history):
    if len(history) < STABLE_FRAMES:
        return False, f"Holding steady: {len(history)}/{STABLE_FRAMES}"
    jitter = float(np.stack(history).std(axis=0).max())
    ok = jitter <= MAX_JITTER_PX
    return ok, f"Corner jitter {jitter:.1f}px (max {MAX_JITTER_PX}px)"

# Checks that the board covers enough of the frame
def check_size(board, shape):
    h, w = shape[:2]
    area = cv2.contourArea(board.astype(np.float32).reshape(-1, 1, 2))
    frac = area / float(w * h)
    ok = frac >= MIN_BOARD_AREA_FRAC
    return ok, f"Board covers {frac:.0%} of frame (min {MIN_BOARD_AREA_FRAC:.0%})"


# Checks that the board isn't too skewed (assumes corners ordered TL, TR, BR, BL)
def check_shape(board):
    top = np.linalg.norm(board[1] - board[0])
    bottom = np.linalg.norm(board[2] - board[3])
    left = np.linalg.norm(board[3] - board[0])
    right = np.linalg.norm(board[2] - board[1])
    skew = max(abs(top - bottom) / max(top, bottom),
               abs(left - right) / max(left, right))
    ok = skew <= MAX_ASPECT_SKEW
    return ok, f"Board skew {skew:.2f} (max {MAX_ASPECT_SKEW})"

def evaluate_frame(img, history):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    corners, ids = detect_markers(img)
    results = [check_markers(ids), check_brightness(gray), check_sharpness(gray)]

    board = detect_corners_from_markers(corners, ids) if results[0][0] else None
    if board is None:
        history.clear()  # lost the board, restart the stability count
        return results, None

    board = np.asarray(board, dtype=np.float32)
    history.append(board)
    results += [check_in_frame(board, img.shape),
                check_size(board, img.shape),
                check_shape(board),
                check_stability(history)]
    return results, board

# Script to check if camera is calibrated correctly
# Corner markers are meant to be aligned with the corners of the projection
def main():
    # Try to instantiate the camera.
    print("Attempting to connect to Device 1...")
    try:
        cam = Camera(int(os.environ["CAMERA_DEVICE_NO"]), 0)  
    except RuntimeError as e:
        print(f"Camera unable to be connected ({e}). Please reconnect and try again.")
        return 1
    print("Camera connected successfully!\n")

    results = []
    last_index = -1
    history = deque(maxlen=STABLE_FRAMES)
    last_new_frame = time.time()
    window_name = "SkEye Calibration View"
    start_time = time.time()

    with cam:
        # Calibration should only run for a minute
        while time.time() - start_time < 60:
            f = cam.read()

            if f is None or f.index == last_index:
                if time.time() - last_new_frame > CONNECT_TIMEOUT_S:
                    print("No frames received from camera.")
                    cv2.destroyAllWindows()
                    return 1
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                continue

            last_index = f.index
            last_new_frame = time.time()
            results, board = evaluate_frame(f.image, history)

            if len(results) == 7 and all(ok for ok, _ in results):
                break

            # Live feedback overlay
            overlay = f.image.copy()
            elapsed = time.time() - start_time
            cv2.putText(overlay, f"Time since calibration start: {elapsed:.1f}s. Max time 60s",
                        (10, 25 + 22 * len(results)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        (255, 255, 255), 1, cv2.LINE_AA)
            # show current calibration statuses
            for i, (ok, msg) in enumerate(results):
                cv2.putText(overlay, msg, (10, 25 + 22 * i),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                            GREEN if ok else RED, 1, cv2.LINE_AA)
            cv2.imshow(window_name, overlay)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            # Closing the window with the X also exits
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

    cv2.destroyAllWindows()

    print("Calibration report:")
    for ok, msg in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {msg}")

    if len(results) == 7 and all(ok for ok, _ in results):
        print("\nCalibration successful!")
        return 0
    print("\nCalibration unsuccessful. Please read the report and try again.")
    return 1

if __name__ == "__main__":
    sys.exit(main())