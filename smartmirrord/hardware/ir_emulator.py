import time
import RPi.GPIO as GPIO

from smartmirrord.config import GPIO_IR_INPUT_PIN
from .ir_codes import CODES, SAMSUNG_PREFIX
from .ir_timing import (
    LEADER_LOW, LEADER_HIGH,
    BIT_LOW, BIT_HIGH_0, BIT_HIGH_1,
    STOP_LOW
)

def us_to_seconds(us):
    return us / 1_000_000.0


class IREmulator:
    def __init__(self, pin: int = GPIO_IR_INPUT_PIN):
        self.pin = pin
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)

    def generate_pulses(self, command_value):
        pulses = [(0, LEADER_LOW), (1, LEADER_HIGH)]

        full_code = (SAMSUNG_PREFIX << 16) | command_value

        for i in range(32):
            bit = (full_code >> (31 - i)) & 1
            pulses.append((0, BIT_LOW))
            pulses.append((1, BIT_HIGH_1 if bit else BIT_HIGH_0))

        pulses.append((0, STOP_LOW))
        return pulses

    def send_raw(self, pulses):
        try:
            for level, duration in pulses:
                GPIO.output(self.pin, level)
                time.sleep(us_to_seconds(duration))
        except:
            raise IOError("IR send failed")
        finally:
            GPIO.output(self.pin, 1)

    def send(self, command):
        command = command.lower()
        if command not in CODES:
            raise ValueError(f"Unknown IR command: {command}")

        pulses = self.generate_pulses(CODES[command])
        for _ in range(5):
            self.send_raw(pulses)
            time.sleep(0.005)
