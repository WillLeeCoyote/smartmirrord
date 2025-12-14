from typing import Callable, Optional
from smartmirrord.hardware.power_status import PowerStatus


class PowerService:
    def __init__(
            self,
            on_power_on: Optional[Callable[[], None]] = None,
            on_power_off: Optional[Callable[[], None]] = None,
    ):
        self._is_on: bool | None = None
        self.on_power_on = on_power_on
        self.on_power_off = on_power_off

        self._power_gpio = PowerStatus(on_change=self.handle_power_change)

    def handle_power_change(self, is_on: bool):
        """
        Called by hardware layer when GPIO state changes.
        """
        if self._is_on == is_on:
            return

        self._is_on = is_on

        if is_on:
            if self.on_power_on:
                self.on_power_on()
        else:
            if self.on_power_off:
                self.on_power_off()

    def is_power_on(self) -> bool:
        return bool(self._is_on)

    def is_power_off(self) -> bool:
        return not bool(self._is_on)
