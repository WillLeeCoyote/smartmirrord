import time
import gpiod
from gpiod.line import Direction, Value
from smartmirrord.config import GPIO_IR_INPUT_PIN, GPIO_CHIP_PATH
from .ir_codes import CODES, SAMSUNG_PREFIX
from .ir_timing import (
    LEADER_LOW, LEADER_HIGH,
    BIT_LOW, BIT_HIGH_0, BIT_HIGH_1,
    STOP_LOW
)


def us_to_seconds(us: int) -> float:
    return us / 1_000_000.0


class IREmulator:
    def __init__(self, pin: int = GPIO_IR_INPUT_PIN):
        self.pin = pin
        self._running = False
        self.request = None

    def start(self):
        if self._running:
            return

        settings = gpiod.LineSettings()
        settings.direction = Direction.OUTPUT

        try:
            self.request = gpiod.request_lines(
                path=GPIO_CHIP_PATH,
                config={self.pin: settings},
                consumer="smartmirrord",
                output_values={self.pin: Value.ACTIVE},
            )
        except Exception as e:
            raise RuntimeError(f"Failed to request GPIO line {self.pin}: {e}") from e

        self._running = True

    def stop(self):
        if not self._running:
            return

        try:
            if self.request:
                self.request.set_value(self.pin, Value.ACTIVE)
                self.request.release()
        finally:
            self.request = None
            self._running = False

    def generate_pulses(self, command_value: int):
        pulses = [(0, LEADER_LOW), (1, LEADER_HIGH)]

        full_code = (SAMSUNG_PREFIX << 16) | command_value

        for i in range(32):
            bit = (full_code >> (31 - i)) & 1
            pulses.append((0, BIT_LOW))
            pulses.append((1, BIT_HIGH_1 if bit else BIT_HIGH_0))

        pulses.append((0, STOP_LOW))
        return pulses

    def send_raw(self, pulses):
        if not self._running:
            raise RuntimeError("IREmulator is not running")

        for level, duration in pulses:
            self.request.set_value(self.pin, Value.ACTIVE if level else Value.INACTIVE)

            end = time.perf_counter() + us_to_seconds(duration)
            while time.perf_counter() < end:
                pass

        self.request.set_value(self.pin, Value.ACTIVE)

    def send(self, command: str):
        if not self._running:
            raise RuntimeError("IREmulator is not running")

        command = command.lower()
        if command not in CODES:
            raise ValueError(f"Unknown IR command: {command}")

        pulses = self.generate_pulses(CODES[command])
        # bit bang style sends here. Maybe a python timing issue, but this works for now.
        for _ in range(5):
            self.send_raw(pulses)
            time.sleep(0.005)
