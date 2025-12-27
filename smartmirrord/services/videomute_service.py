import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)


class VideoMuteService:
    TRANSITION_TIMEOUT = 8

    def __init__(self, dispatcher, uart):
        self._uart = uart

        self._panel_muted: Optional[bool] = None
        self._backlight_on: Optional[bool] = None
        self._desired_muted: Optional[bool] = None

        self._power_on = False
        self._transition_active = False
        self._converged_event = threading.Event()
        self._transition_timer: Optional[threading.Timer] = None

        dispatcher.register_handler(self)

        logger.info("VideoMuteService initialized (power unknown, state unknown)")

    def mute(self) -> None:
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
        logger.debug("VideoMute RX: %s", line)

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
        logger.info("Power on detected; assuming unmuted baseline")
        # ToDo: The known baseline is good if the panel did just power on, but NOT
        #  if the service started and the panel was already on. I think we can handle this by checking if the power_on
        #  is set to NONE in the constructor and then setting it to True here.
        #  Then, if the power_on is still None, we can assume the panel was already on and force a mute.

        self._power_on = True
        self._panel_muted = False
        self._backlight_on = True
        self._transition_active = False
        self._converged_event.clear()

        if self._desired_muted is True:
            logger.info("Desired mute pending; applying after power on")
            self._start_transition()
            self._apply_mute_sequence()

    def on_power_off(self) -> None:
        logger.warning("Power off detected; invalidating VideoMute state")

        self._power_on = False
        self._panel_muted = None
        self._backlight_on = None
        self._transition_active = False

        # On the next power cycle we want to start in a muted state but also respect any changes between now and then.
        self._desired_muted = True

        if self._transition_timer:
            self._transition_timer.cancel()
            self._transition_timer = None

        self._converged_event.clear()
