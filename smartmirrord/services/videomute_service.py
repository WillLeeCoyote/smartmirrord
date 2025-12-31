import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)


class VideoMuteService:
    TRANSITION_TIMEOUT = 8

    def __init__(self, dispatcher, uart, power_service):
        self._dispatcher = dispatcher
        self._uart = uart
        self._power_service = power_service

        self._panel_muted: Optional[bool] = None
        self._backlight_on: Optional[bool] = None
        self._desired_muted: Optional[bool] = None

        self._power_on = False
        self._transition_active = False
        self._converged_event = threading.Event()
        self._transition_timer: Optional[threading.Timer] = None
        self._running = False

        logger.info("VideoMuteService constructed")

    def start(self) -> None:
        if self._running:
            return

        self._dispatcher.register_handler(self)
        self._power_service.register_on_power_on(self.on_power_on)
        self._power_service.register_on_power_off(self.on_power_off)

        self._running = True
        logger.info("VideoMuteService started")

    def stop(self) -> None:
        if not self._running:
            return

        self._running = False

        if self._transition_timer:
            self._transition_timer.cancel()
            self._transition_timer = None

        self._transition_active = False
        self._desired_muted = None
        self._converged_event.clear()

        logger.info("VideoMuteService stopped")

    def mute(self) -> None:
        if not self._running:
            raise RuntimeError("VideoMuteService is not running")

        logger.info("VideoMuteService: mute() requested")
        self._desired_muted = True

        if not self._power_on:
            logger.debug("Power off; deferring mute")
            return

        if self._is_currently_muted():
            logger.debug("Already muted; no action needed")
            self._converged_event.set()
            return

        self._start_transition()
        self._apply_mute_sequence()

    def unmute(self) -> None:
        if not self._running:
            raise RuntimeError("VideoMuteService is not running")

        logger.info("VideoMuteService: unmute() requested")
        self._desired_muted = False

        if not self._power_on:
            logger.debug("Power off; deferring unmute")
            return

        if self._is_currently_unmuted():
            logger.debug("Already unmuted; no action needed")
            self._converged_event.set()
            return

        self._start_transition()
        self._apply_unmute_sequence()

    def is_muted(self) -> bool:
        return bool(self._panel_muted is True and self._backlight_on is False)

    def is_transitioning(self) -> bool:
        return self._transition_active

    def wait_for_convergence(self, timeout: Optional[float] = None) -> bool:
        return self._converged_event.wait(timeout)

    def _is_currently_muted(self) -> bool:
        return self._panel_muted is True and self._backlight_on is False

    def _is_currently_unmuted(self) -> bool:
        return self._panel_muted is False and self._backlight_on is True

    def _start_transition(self) -> None:
        self._transition_active = True
        self._converged_event.clear()

        if self._transition_timer:
            self._transition_timer.cancel()

        self._transition_timer = threading.Timer(
            self.TRANSITION_TIMEOUT,
            self._on_transition_timeout,
        )
        self._transition_timer.daemon = True
        self._transition_timer.start()

        logger.debug("Transition started (desired_muted=%s)", self._desired_muted)

    def _complete_transition(self) -> None:
        self._transition_active = False
        self._converged_event.set()

        if self._transition_timer:
            self._transition_timer.cancel()
            self._transition_timer = None

        logger.info(
            "VideoMute converged: panel_muted=%s backlight_on=%s",
            self._panel_muted,
            self._backlight_on,
        )

    def _on_transition_timeout(self) -> None:
        if not self._running:
            return

        logger.error(
            "VideoMute transition timeout "
            "(desired_muted=%s panel_muted=%s backlight_on=%s)",
            self._desired_muted,
            self._panel_muted,
            self._backlight_on,
        )

        self._transition_active = False
        self._desired_muted = None
        self._converged_event.set()

    def _apply_mute_sequence(self) -> None:
        logger.debug(
            "Applying mute sequence (panel_muted=%s backlight_on=%s)",
            self._panel_muted,
            self._backlight_on,
        )

        self._uart.write("videomute 0 1")  # panel black
        self._uart.write("videomute 1 1")  # backlight off

    def _apply_unmute_sequence(self) -> None:
        logger.debug(
            "Applying unmute sequence (panel_muted=%s backlight_on=%s)",
            self._panel_muted,
            self._backlight_on,
        )

        self._uart.write("videomute 1 0")  # backlight on
        self._uart.write("videomute 0 0")  # panel active

    def can_handle(self, line: str) -> bool:
        return (
            line.startswith("Video Mute")
            or line.startswith("PORT_SW_INVERTER")
        )

    def handle(self, line: str) -> None:
        if not self._running:
            return

        prev_state = (self._panel_muted, self._backlight_on)

        if line == "Video Mute on":
            self._panel_muted = True
        elif line == "Video Mute off":
            self._panel_muted = False
        elif line == "PORT_SW_INVERTER on":
            self._backlight_on = True
        elif line == "PORT_SW_INVERTER off":
            self._backlight_on = False
        else:
            return

        if prev_state != (self._panel_muted, self._backlight_on):
            logger.info(
                "VideoMute state update: panel_muted=%s backlight_on=%s",
                self._panel_muted,
                self._backlight_on,
            )

        self._check_desired_convergence()

    def _check_desired_convergence(self) -> None:
        if self._desired_muted is None or not self._power_on:
            return

        if self._desired_muted and self._is_currently_muted():
            self._complete_transition()
        elif not self._desired_muted and self._is_currently_unmuted():
            self._complete_transition()

    def on_power_on(self) -> None:
        if not self._running:
            return

        logger.info("Power on detected")

        self._power_on = True

    def on_power_off(self) -> None:
        if not self._running:
            return

        logger.warning("Power off detected; invalidating VideoMute state")

        self._power_on = False
        self._panel_muted = None
        self._backlight_on = None
        self._transition_active = False
        self._desired_muted = None

        if self._transition_timer:
            self._transition_timer.cancel()
            self._transition_timer = None

        self._converged_event.clear()
