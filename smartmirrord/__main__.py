import threading
import time

from smartmirrord.logging_config import setup_logging
from smartmirrord.services.power_service import PowerService
from smartmirrord.services.ir_service import IRService
from smartmirrord.services.display_availability_service import DisplayAvailabilityService
from smartmirrord.services.motion_service import MotionService
from smartmirrord.services.display_policy_service import DisplayPolicyService
from smartmirrord.web.routes import web_remote

from smartmirrord.hardware.uart_transport import UartTransport
from smartmirrord.services.uart_dispatcher import UartDispatcher
from smartmirrord.services.videomute_service import VideoMuteService


def main():
    setup_logging()

    def on_power_on():
        print("TV Power: ON")

    def on_power_off():
        print("TV Power: OFF")

    def on_motion():
        print("Motion detected! " + time.strftime("%H:%M:%S"))

    schedule_json = {
        "quiet_hours": [
            {"start": "23:00", "end": "06:00"}
        ]
    }

    # Construct core services
    power_service = PowerService()
    ir_service = IRService()
    uart = UartTransport()
    dispatcher = UartDispatcher(uart)
    videomute_service = VideoMuteService(dispatcher, uart, power_service)
    motion_service = MotionService()
    display_availability_service = DisplayAvailabilityService(power_service, ir_service)
    display_policy_service = DisplayPolicyService(videomute_service, motion_service, power_service, 15, schedule_json)

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

    # Register event handlers
    power_service.register_on_power_on(on_power_on)
    power_service.register_on_power_off(on_power_off)
    motion_service.register_on_motion_on(on_motion)

    # Start core services
    ir_service.start()
    display_availability_service.start()
    display_policy_service.start()
    power_service.start()
    uart.start()
    motion_service.start()
    web_thread.start()

    print("SmartMirror daemon running:")

    stop_event = threading.Event()
    try:
        while not stop_event.is_set():
            stop_event.wait(timeout=60)
    except KeyboardInterrupt:
        print("\nShutting down SmartMirror...")
    finally:
        motion_service.stop()
        display_availability_service.stop()
        display_policy_service.stop()
        uart.stop()
        power_service.stop()
        ir_service.stop()

        print("Cleanup complete.")


if __name__ == "__main__":
    main()