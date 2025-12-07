import time

from smartmirrord.hardware import gpio_helper
from smartmirrord.hardware.power_status import PowerStatus
from smartmirrord.services.power_service import PowerService
from smartmirrord.hardware.ir_emulator import IREmulator

def main():
    power_gpio = PowerStatus()
    power_service = PowerService(power_gpio)
    ir_emulator = IREmulator()

    try:
        print("Starting SmartMirror power monitor...")
        while True:
            if power_service.is_power_on():
                print("TV Power: ON")
            else:
                print("TV Power: OFF")
                ir_emulator.send("power")
                time.sleep(12)
            # Pulses on/off every second for 5-6 seconds when powering on
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nExiting power monitor.")
    finally:
        gpio_helper.cleanup()
        print("Cleanup complete.")


if __name__ == "__main__":
    main()
