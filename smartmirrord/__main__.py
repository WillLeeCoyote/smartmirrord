import time
import threading

from smartmirrord.hardware import gpio_helper
from smartmirrord.hardware.power_status import PowerStatus
from smartmirrord.services.power_service import PowerService
from smartmirrord.hardware.ir_emulator import IREmulator
from smartmirrord.web.routes import web_remote

def power_monitor_loop(power_service, ir_emulator):
    try:
        print("Starting SmartMirror power monitor...")
        while True:
            if power_service.is_power_on():
                print("TV Power: ON")
            else:
                print("TV Power: OFF")
                # ir_emulator.send("power")
                # time.sleep(12)
            # Pulses on/off every second for 5-6 seconds when powering on
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting power monitor.")

def main():
    power_gpio = PowerStatus()
    power_service = PowerService(power_gpio)
    ir_emulator = IREmulator()

    web_thread = threading.Thread(
        target=lambda: web_remote.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False, threaded=False),
        daemon=True
    )
    web_thread.start()

    try:
        power_monitor_loop(power_service, ir_emulator)
    finally:
        gpio_helper.cleanup()
        print("Cleanup complete.")

if __name__ == "__main__":
    main()
