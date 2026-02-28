from picamera2 import Picamera2
from smartmirrord import config
import time


class Camera:
    def __init__(
        self,
        width: int = config.CAMERA_WIDTH,
        height: int = config.CAMERA_HEIGHT,
    ):
        self.picam2 = None
        self._width = width
        self._height = height

    def start(self):
        try:
            self.picam2 = Picamera2()

            camera_config = self.picam2.create_video_configuration(
                main={
                    "size": (self._width, self._height),
                    "format": "RGB888",
                }
            )

            self.picam2.configure(camera_config)
            self.picam2.start()

            # Allow sensor + pipeline to stabilize
            time.sleep(0.2)

        except Exception as e:
            raise RuntimeError(f"Failed to initialize Picamera2: {e}")

    def read_frame(self):
        if self.picam2 is None:
            return None

        try:
            frame = self.picam2.capture_array()
        except Exception:
            return None

        if frame is None or frame.size == 0:
            return None

        return frame

    def stop(self):
        if self.picam2:
            self.picam2.stop()
            self.picam2.close()
            self.picam2 = None
