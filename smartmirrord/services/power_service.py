import threading
import logging
from typing import Callable, List, Optional
from smartmirrord.hardware.power_status import PowerStatus

log = logging.getLogger(__name__)

class PowerService:
    STABILITY_WINDOW = 1.2  # seconds required to consider stable

    def __init__(self):
        self._on_power_on_handlers: List[Callable[[], None]] = []
        self._on_power_off_handlers: List[Callable[[], None]] = []

        self._is_on: bool | None = None
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

        # Emit the appropriate events based on the power state.
        if stable_value:
            self._emit_power_on()
        else:
            self._emit_power_off()

    def _emit_power_on(self):
        for handler in self._on_power_on_handlers:
            try:
                handler()
            except Exception:
                log.exception("Exception in on_power_on handler")

    def _emit_power_off(self):
        for handler in self._on_power_off_handlers:
            try:
                handler()
            except Exception:
                log.exception("Exception in on_power_off handler")

    def register_on_power_on(self, handler: Callable[[], None]):
        with self._lock:
            self._on_power_on_handlers.append(handler)
            log.info("Registered new on_power_on handler.")

    def register_on_power_off(self, handler: Callable[[], None]):
        with self._lock:
            self._on_power_off_handlers.append(handler)
            log.info("Registered new on_power_off handler.")

    def is_power_on(self) -> bool:
        with self._lock:
            return bool(self._is_on)

    def is_power_off(self) -> bool:
        with self._lock:
            return not bool(self._is_on)
