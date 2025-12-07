import time
from smartmirrord.hardware.power_status import PowerStatusGPIO
from smartmirrord.services.power_service import PowerService

def main():
    power_gpio = PowerStatusGPIO()
    power_service = PowerService(power_gpio)

    try:
        print("Starting SmartMirror power monitor...")
        while True:
            if power_service.is_power_on():
                print("TV Power: ON")
            else:
                print("TV Power: OFF")
            # Pulses on/off every second for 5-6 seconds when powering on
            time.sleep(.25)

    except KeyboardInterrupt:
        print("\nExiting power monitor.")
    finally:
        # Optional: clean up GPIO if needed
        print("Cleanup complete.")


if __name__ == "__main__":
    main()
