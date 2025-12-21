import logging

logger = logging.getLogger(__name__)


class VideoMuteService:

    def __init__(self, dispatcher, uart):
        self._uart = uart

        # Hardware state (as last reported by UART)
        self._panel_muted = None
        self._backlight_on = None

        dispatcher.register_handler(self)

    def mute(self) -> None:
        logger.info("VideoMuteService: mute()")

        # Step 1: panel black
        self._uart.write("videomute 0 1")

        # Step 2: backlight off
        self._uart.write("videomute 1 1")

    def unmute(self) -> None:
        logger.info("VideoMuteService: unmute()")

        # Step 1: backlight on
        self._uart.write("videomute 1 0")

        # Step 2: panel active
        self._uart.write("videomute 0 0")

    def is_muted(self) -> bool:
        return bool(self._panel_muted and self._backlight_on is False)

    # Dispatcher interface
    def can_handle(self, line: str) -> bool:
        return (
            line.startswith("Video Mute")
            or line.startswith("PORT_SW_INVERTER")
        )

    def handle(self, line: str) -> None:
        logger.debug("VideoMuteService RX: %s", line)

        if line == "Video Mute on":
            self._panel_muted = True
            return

        if line == "Video Mute off":
            self._panel_muted = False
            return

        if line == "PORT_SW_INVERTER on":
            self._backlight_on = True
            return

        if line == "PORT_SW_INVERTER off":
            self._backlight_on = False
            return
