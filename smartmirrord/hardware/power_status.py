import RPi.GPIO as GPIO
from typing import Callable, Optional
from smartmirrord.config import GPIO_POWER_STATUS_PIN


class PowerStatus:
    """
    Low-level hardware access for reading the TV's LED pin.
    Emits events when power state changes.
    """

    def __init__(
            self,
            pin: int = GPIO_POWER_STATUS_PIN,
            on_change: Optional[Callable[[bool], None]] = None,
            bouncetime_ms: int = 200,
    ):
        self.pin = pin
        self.on_change = on_change

        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        GPIO.add_event_detect(
            self.pin,
            GPIO.BOTH,
            callback=self._gpio_callback,
            bouncetime=bouncetime_ms,
        )

    def _gpio_callback(self, channel: int):
        is_on = self._read_power_state()

        if self.on_change:
            self.on_change(is_on)

    def _read_power_state(self) -> bool:
        """
        Hardware logic:
          LOW  -> Power ON
          HIGH -> Power OFF
        """
        return GPIO.input(self.pin) == GPIO.LOW
