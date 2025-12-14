import threading
import time

from smartmirrord.hardware import gpio_helper
from smartmirrord.services.power_service import PowerService
from smartmirrord.services.ir_service import IRService
from smartmirrord.web.routes import web_remote


def main():
    ir_service = IRService()

    def on_power_on():
        print("TV Power: ON")

    def on_power_off():
        print("TV Power: OFF")
        # ir_emulator.send("power")
        # time.sleep(12)

    power_service = PowerService(
        on_power_on=on_power_on,
        on_power_off=on_power_off,
    )

    web_thread = threading.Thread(
        target=lambda: web_remote.run(
            host="0.0.0.0",
            port=5000,
            debug=True,
            use_reloader=False,
            threaded=False,
        ),
        daemon=True,
    )
    web_thread.start()

    print("SmartMirror daemon running:")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nShutting down SmartMirror...")
    finally:
        gpio_helper.cleanup()
        print("Cleanup complete.")


if __name__ == "__main__":
    main()
