from smartmirrord.hardware.power_status import PowerStatus

class PowerService:
    """
    Semantic methods for power control.
    """

    def __init__(self, hardware: PowerStatus | None = None):
        self.hardware = hardware or PowerStatus()

    def is_power_on(self) -> bool:
        return self.hardware.is_on()

    def is_power_off(self) -> bool:
        return not self.hardware.is_on()
