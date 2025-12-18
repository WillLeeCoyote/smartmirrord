import threading
import time
import cv2
from smartmirrord.hardware.camera import Camera
from smartmirrord.config import (
    MOTION_WIDTH, MOTION_HEIGHT, MOTION_THRESHOLD, MOTION_COOLDOWN_SEC
)
from typing import Optional, Callable


class MotionService:
    def __init__(self, on_motion: Optional[Callable[[], None]] = None):
        self.camera = Camera()
        self.on_motion = on_motion

        self.thread: Optional[threading.Thread] = None
        self.running = False

        self.last_frame = None
        self.last_motion_time = 0

        self.start()

    def start(self):
        if self.running:
            return  # already started

        self.camera.start()
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.thread:
            self.thread.join()
        self.camera.stop()

    def _run(self):
        while self.running:
            frame = self.camera.read_frame()
            if frame is None:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            gray = cv2.resize(gray, (MOTION_WIDTH, MOTION_HEIGHT))
            gray = cv2.GaussianBlur(gray, (5, 5), 0)

            if self.last_frame is None:
                self.last_frame = gray
                continue

            diff = cv2.absdiff(self.last_frame, gray)
            _, thresh = cv2.threshold(diff, 15, 255, cv2.THRESH_BINARY)
            motion_score = cv2.countNonZero(thresh)

            now = time.time()
            if motion_score > MOTION_THRESHOLD and now - self.last_motion_time >= MOTION_COOLDOWN_SEC:
                self.last_motion_time = now
                if self.on_motion:
                    self.on_motion()

            self.last_frame = gray
            time.sleep(0.05)
