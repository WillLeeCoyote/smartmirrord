import logging
from typing import Optional

logger = logging.getLogger(__name__)


class VideoMuteService:

    def __init__(self, dispatcher, uart):
        self._uart = uart

        self._panel_muted: Optional[bool] = None
        self._backlight_on: Optional[bool] = None

        self._desired_muted: Optional[bool] = None

        dispatcher.register_handler(self)

        logger.info("VideoMuteService initialized (state unknown)")

    def mute(self) -> None:
        logger.info("VideoMuteService: mute() requested")

        self._desired_muted = True

        if self._is_currently_muted():
            logger.debug("Already muted; no action needed")
            return

        self._apply_mute_sequence()

    def unmute(self) -> None:
        logger.info("VideoMuteService: unmute() requested")

        self._desired_muted = False

        if self._is_currently_unmuted():
            logger.debug("Already unmuted; no action needed")
            return

        self._apply_unmute_sequence()

    def is_muted(self) -> bool:
        return bool(
            self._panel_muted is True and self._backlight_on is False
        )

    def _is_currently_muted(self) -> bool:
        return (
            self._panel_muted is True
            and self._backlight_on is False
        )

    def _is_currently_unmuted(self) -> bool:
        return (
            self._panel_muted is False
            and self._backlight_on is True
        )

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
        logger.debug("VideoMuteService RX: %s", line)

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
        if self._desired_muted is None:
            return

        if self._desired_muted and self._is_currently_muted():
            logger.debug("Desired mute state achieved")

        elif not self._desired_muted and self._is_currently_unmuted():
            logger.debug("Desired unmute state achieved")
