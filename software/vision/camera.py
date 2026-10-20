"""
camera.py - frame source for SkEye.

Accepts a device index (webcam).
For live cameras, a background thread always keeps the newest frame so slow
processing never builds up lag.

References:
https://www.geeksforgeeks.org/python/how-to-get-properties-of-python-cv2-videocapture-object/
"""

import threading
import time
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

@dataclass
class Frame:
    image: np.ndarray
    timestamp: float
    index: int 


class Camera:
    def __init__(self, source: int = 0, width: int = 1280, height: int = 720,
                 fps: Optional[int] = None):
        self._cap = cv2.VideoCapture(source)
        if not self._cap.isOpened():
            raise RuntimeError(f"Could not open camera source: {source}")

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self._cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
        if fps:
            self._cap.set(cv2.CAP_PROP_FPS, fps)

        self.width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self._frame: Optional[Frame] = None
        self._index = 0
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._running:
            return self
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        self._cap.release()

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()

    def read(self) -> Optional[Frame]:
        """Newest frame, or None if no frame has arrived yet."""
        with self._lock:
            return self._frame

    def _loop(self):
        while self._running:
            ok, img = self._cap.read()
            if not ok:
                time.sleep(0.01)
                continue
            frame = Frame(img, time.perf_counter(), self._index + 1)
            with self._lock:
                self._frame = frame
                self._index += 1


if __name__ == "__main__":
    last = -1
    with Camera(0) as cam:
        print(f"Opened {cam.width}x{cam.height}")
        while True:
            f = cam.read()
            if f is None or f.index == last:   # no new frame yet
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                continue
            last = f.index
            cv2.imshow("camera", f.image)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    cv2.destroyAllWindows()