import threading
from typing import Callable, Optional
from smartmirrord.hardware.power_status import PowerStatus


class PowerService:
    STABILITY_WINDOW = 1.2  # seconds required to consider stable

    def __init__(
            self,
            on_power_on: Optional[Callable[[], None]] = None,
            on_power_off: Optional[Callable[[], None]] = None,
    ):
        self._is_on: bool | None = None
        self.on_power_on = on_power_on
        self.on_power_off = on_power_off

        self._last_gpio_value: bool | None = None
        self._stability_timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

        self._power_gpio = PowerStatus(on_change=self._handle_power_change)

    def _handle_power_change(self, is_on: bool):
        with self._lock:
            self._last_gpio_value = is_on

            # Cancel any existing stability timer
            if self._stability_timer:
                self._stability_timer.cancel()

            # Start a new timer to fire after STABILITY_WINDOW
            self._stability_timer = threading.Timer(
                self.STABILITY_WINDOW, self._stable_callback, args=(is_on,)
            )
            self._stability_timer.daemon = True
            self._stability_timer.start()

    def _stable_callback(self, stable_value: bool):
        with self._lock:
            if self._is_on == stable_value:
                return

            self._is_on = stable_value

        try:
            if stable_value and self.on_power_on:
                self.on_power_on()
            elif not stable_value and self.on_power_off:
                self.on_power_off()
        except Exception:
            pass

    def is_power_on(self) -> bool:
        with self._lock:
            return bool(self._is_on)

    def is_power_off(self) -> bool:
        with self._lock:
            return not bool(self._is_on)
