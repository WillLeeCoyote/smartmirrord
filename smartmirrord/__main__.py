import threading
import time

from smartmirrord.services.power_service import PowerService
from smartmirrord.services.ir_service import IRService
from smartmirrord.services.motion_service import MotionService
from smartmirrord.web.routes import web_remote


def main():
    def on_power_on():
        print("TV Power: ON")

    def on_power_off():
        print("TV Power: OFF")
        # ir_service.send_command("power")
        # time.sleep(12)

    power_service = PowerService(
        on_power_on=on_power_on,
        on_power_off=on_power_off,
    )
    ir_service = IRService()
    web_remote.config["IR_SERVICE"] = ir_service

    web_thread = threading.Thread(
        target=web_remote.run,
        kwargs=dict(
            host="0.0.0.0",
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=False,
        ),
        daemon=True,
    )
    web_thread.start()

    def on_motion():
        print("Motion detected!" + time.strftime("%H:%M:%S"))

    motion_service = MotionService(on_motion=on_motion)

    print("SmartMirror daemon running:")

    stop_event = threading.Event()
    try:
        while not stop_event.is_set():
            stop_event.wait(timeout=60)
    except KeyboardInterrupt:
        print("\nShutting down SmartMirror...")
    finally:
        motion_service.stop()
        for svc in (
                getattr(ir_service, "ir_emulator", None),
                getattr(power_service, "power_status", None)
        ):
            if svc:
                svc.close()
        print("Cleanup complete.")

if __name__ == "__main__":
    main()
