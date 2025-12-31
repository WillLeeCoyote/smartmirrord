import threading
import time
import cv2
import logging
from typing import Callable, Optional, List
from smartmirrord.hardware.camera import Camera
from smartmirrord.config import (
    MOTION_WIDTH, MOTION_HEIGHT, MOTION_THRESHOLD, MOTION_COOLDOWN_SEC
)

logger = logging.getLogger(__name__)


class MotionService:
    def __init__(self):
        self.camera = Camera()

        self._handlers: List[Callable[[], None]] = []

        self.thread: Optional[threading.Thread] = None
        self.running = False

        self.last_frame = None
        self.last_motion_time = 0

        self._lock = threading.Lock()

    def register_on_motion_on(self, handler: Callable[[], None]) -> None:
        with self._lock:
            self._handlers.append(handler)
        logger.debug("Registered motion handler: %s", getattr(handler, "__name__", repr(handler)))

    def start(self):
        if self.running:
            logger.debug("MotionService already running; start() ignored")
            return

        self.camera.start()
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True, name="MotionService")
        self.thread.start()
        logger.debug("MotionService thread started")

    def stop(self):
        if not self.running:
            logger.debug("MotionService not running; stop() ignored")
            return

        self.running = False
        if self.thread:
            self.thread.join()
            self.thread = None

        self.camera.stop()
        self.last_frame = None
        logger.debug("MotionService stopped")

    def _emit_motion(self):
        with self._lock:
            handlers = list(self._handlers)

        for handler in handlers:
            try:
                handler()
            except Exception:
                logger.exception(
                    "Motion handler error (%s)",
                    getattr(handler, "__name__", handler.__class__.__name__),
                )

    def _run(self):
        logger.debug("MotionService loop running")
        while self.running:
            frame = self.camera.read_frame()
            if frame is None:
                time.sleep(0.01)
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
            if (
                motion_score > MOTION_THRESHOLD
                and now - self.last_motion_time >= MOTION_COOLDOWN_SEC
            ):
                self.last_motion_time = now
                logger.info("Motion detected (score=%s)", motion_score)
                self._emit_motion()

            self.last_frame = gray
            time.sleep(0.05)

        logger.debug("MotionService loop exiting")
