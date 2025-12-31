import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)


class DisplayAvailabilityService:
    POWER_ON_TIMEOUT = 20
    POWER_OFF_DELAY = 2

    def __init__(self, power_service, ir_service):
        self._power_service = power_service
        self._ir_service = ir_service

        self._waiting_for_power_on = False
        self._power_on_event = threading.Event()

        self._retry_timer: Optional[threading.Timer] = None
        self._power_off_delay_timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

        self._running = False

        logger.info("DisplayAvailabilityService constructed")

    def start(self):
        if self._running:
            return

        self._power_service.register_on_power_on(self._on_power_on)
        self._power_service.register_on_power_off(self._on_power_off)

        self._running = True
        logger.info("DisplayAvailabilityService started")

    def stop(self):
        if not self._running:
            return

        with self._lock:
            self._running = False
            self._waiting_for_power_on = False
            self._power_on_event.set()

            if self._retry_timer:
                self._retry_timer.cancel()
                self._retry_timer = None

            if self._power_off_delay_timer:
                self._power_off_delay_timer.cancel()
                self._power_off_delay_timer = None

        logger.info("DisplayAvailabilityService stopped")

    def _on_power_on(self) -> None:
        if not self._running:
            return

        with self._lock:
            self._waiting_for_power_on = False
            self._power_on_event.set()

            if self._retry_timer:
                self._retry_timer.cancel()
                self._retry_timer = None

        logger.info("Display power confirmed ON")

    def _on_power_off(self) -> None:
        if not self._running:
            return

        logger.warning("Display power OFF detected; asserting power ON")

        with self._lock:
            self._waiting_for_power_on = True
            self._power_on_event.clear()

        # Start a timer for the delay before trying to power on
        self._start_power_off_delay_timer()

    def _start_power_off_delay_timer(self) -> None:
        if not self._running:
            return

        if self._power_off_delay_timer:
            self._power_off_delay_timer.cancel()

        self._power_off_delay_timer = threading.Timer(
            self.POWER_OFF_DELAY,
            self._send_power_command,
        )
        self._power_off_delay_timer.daemon = True
        self._power_off_delay_timer.start()

    def _send_power_command(self) -> None:
        if not self._running:
            return

        try:
            self._ir_service.send_command("power")
            logger.debug("IR power command sent")
        except Exception:
            logger.exception("Failed to send IR power command")

        self._start_power_on_timeout()

    def _start_power_on_timeout(self) -> None:
        if not self._running:
            return

        if self._retry_timer:
            self._retry_timer.cancel()

        self._retry_timer = threading.Timer(
            self.POWER_ON_TIMEOUT,
            self._on_power_on_timeout,
        )
        self._retry_timer.daemon = True
        self._retry_timer.start()

    def _on_power_on_timeout(self) -> None:
        with self._lock:
            if not self._running or not self._waiting_for_power_on:
                return

        logger.error(
            "Display failed to power on within %.1fs; retrying IR power",
            self.POWER_ON_TIMEOUT,
        )

        self._send_power_command()
        self._start_power_on_timeout()

    def wait_until_powered_on(self, timeout: Optional[float] = None) -> bool:
        return self._power_on_event.wait(timeout)
