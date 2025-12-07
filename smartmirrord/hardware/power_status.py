import RPi.GPIO as GPIO
from smartmirrord.config import GPIO_POWER_STATUS_PIN

class PowerStatus:
    """
    Low-level hardware access for reading the TV's LED pin.
    LED pulses ON/OFF 1s for 5-6s when powering on.
    Converts raw GPIO pin state into a boolean.
    """

    def __init__(self, pin: int = GPIO_POWER_STATUS_PIN):
        self.pin = pin
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def is_on(self) -> bool:
        """
        Hardware logic:
          LOW  -> Power ON
          HIGH -> Power OFF
        """
        return GPIO.input(self.pin) == GPIO.LOW
