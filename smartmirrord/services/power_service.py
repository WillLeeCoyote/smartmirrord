import threading
import logging
from typing import Callable, Optional
from smartmirrord.hardware.power_status import PowerStatus

log = logging.getLogger(__name__)


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

        log.info("PowerService starting")

        self._power_gpio = PowerStatus(on_change=self._handle_power_change)

        # Read current GPIO level once and start stability timer.
        initial_state = self._power_gpio.read()
        log.info("Initial power GPIO read: %s", "ON" if initial_state else "OFF")

        self._start_stability_timer(initial_state)

    def _start_stability_timer(self, is_on: bool):
        with self._lock:
            self._last_gpio_value = is_on

            if self._stability_timer:
                self._stability_timer.cancel()
                log.debug("Cancelled previous stability timer")

            log.debug(
                "Starting stability timer (%.1fs) for state=%s",
                self.STABILITY_WINDOW,
                "ON" if is_on else "OFF",
            )

            self._stability_timer = threading.Timer(
                self.STABILITY_WINDOW, self._stable_callback, args=(is_on,)
            )
            self._stability_timer.daemon = True
            self._stability_timer.start()

    def _handle_power_change(self, is_on: bool):
        log.debug("GPIO edge detected: %s", "ON" if is_on else "OFF")
        self._start_stability_timer(is_on)

    def _stable_callback(self, stable_value: bool):
        with self._lock:
            if self._is_on == stable_value:
                log.debug(
                    "Stability timer fired but state unchanged (%s)",
                    "ON" if stable_value else "OFF",
                )
                return

            self._is_on = stable_value

        log.info(
            "Power state stabilized: %s",
            "ON" if stable_value else "OFF",
        )

        try:
            if stable_value and self.on_power_on:
                self.on_power_on()
            elif not stable_value and self.on_power_off:
                self.on_power_off()
        except Exception:
            log.exception("Exception in power state callback")

    def is_power_on(self) -> bool:
        with self._lock:
            return bool(self._is_on)

    def is_power_off(self) -> bool:
        with self._lock:
            return not bool(self._is_on)
