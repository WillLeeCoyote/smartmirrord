from smartmirrord.hardware.ir_emulator import IREmulator
from smartmirrord.hardware.ir_codes import CODES


class IRService:
    def __init__(self):
        self.ir_emulator = IREmulator()
        self.commands = list(CODES.keys())

    def list_commands(self):
        """Return all available IR commands."""
        return self.commands

    def send_command(self, command: str):
        """Send an IR command."""
        command = command.lower()
        if command not in self.commands:
            raise ValueError(f"Unknown IR command: {command}")
        self.ir_emulator.send(command)
