import logging
from smartmirrord.hardware.ir_emulator import IREmulator
from smartmirrord.hardware.ir_codes import CODES

log = logging.getLogger(__name__)


class IRService:
    def __init__(self):
        self._ir_emulator = IREmulator()
        self._commands = list(CODES.keys())
        self._running = False

        log.info("IRService constructed")

    def start(self):
        if self._running:
            log.debug("IRService already running")
            return

        self._ir_emulator.start()
        self._running = True

        log.info("IRService started")

    def stop(self):
        if not self._running:
            return

        self._ir_emulator.stop()
        self._running = False

        log.info("IRService stopped")

    def list_commands(self):
        return self._commands

    def send_command(self, command: str):
        if not self._running:
            log.warning("Attempted IR send while service not running")
            raise RuntimeError("IRService is not running")

        command = command.lower()
        if command not in self._commands:
            raise ValueError(f"Unknown IR command: {command}")

        log.debug("Sending IR command: %s", command)
        self._ir_emulator.send(command)
