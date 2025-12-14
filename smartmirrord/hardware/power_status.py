import gpiod
import threading
import time
from typing import Callable, Optional
from smartmirrord.config import GPIO_POWER_STATUS_PIN, GPIO_CHIP_PATH
from gpiod.line import Direction, Edge, Value


class PowerStatus:
    """
    Low-level hardware access for reading the TV's LED pin.
    Emits events when power state changes.
    """

    def __init__(
            self,
            pin: int = GPIO_POWER_STATUS_PIN,
            on_change: Optional[Callable[[bool], None]] = None,
            bouncetime_ms: int = 200,
            chip_path: str = GPIO_CHIP_PATH,
    ):
        self.pin = pin
        self.on_change = on_change
        self.bouncetime = bouncetime_ms / 1000.0
        self._last_event = 0
        self._stop_event = threading.Event()

        try:
            self.request = gpiod.request_lines(
                path=chip_path,
                config={pin: gpiod.LineSettings(direction=Direction.INPUT, edge_detection=Edge.BOTH)},
                consumer="smartmirrord",
            )
        except Exception as e:
            raise RuntimeError(f"Failed to request GPIO line {pin}: {e}") from e

        if self.on_change:
            self._thread = threading.Thread(target=self._event_loop, daemon=True)
            self._thread.start()

    def _read_power_state(self) -> bool:
        """Return True if power is ON (LED LOW)."""
        return self.request.get_values()[0] == Value.INACTIVE

    def _event_loop(self):
        while not self._stop_event.is_set():
            if self.request.wait_edge_events(timeout=None):
                for _ in self.request.read_edge_events():
                    now = time.monotonic()
                    if now - self._last_event >= self.bouncetime:
                        self._last_event = now
                        if self.on_change:
                            self.on_change(self._read_power_state())

    def close(self):
        self._stop_event.set()
        if hasattr(self, "_thread"):
            self._thread.join()
        self.request.release()
