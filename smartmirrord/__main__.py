import threading
import time

from smartmirrord.logging_config import setup_logging
from smartmirrord.services.power_service import PowerService
from smartmirrord.services.ir_service import IRService
from smartmirrord.services.display_availability_service import DisplayAvailabilityService
from smartmirrord.services.motion_service import MotionService
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
        # ir_service.send_command("power")
        # time.sleep(12)

    power_service = PowerService()
    power_service.register_on_power_on(on_power_on)
    power_service.register_on_power_off(on_power_off)

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

    display_availability_service = DisplayAvailabilityService(power_service, ir_service)

    # ------------------------------------------------------------
    # UART + Dispatcher + VideoMute
    # ------------------------------------------------------------

    uart = UartTransport()
    uart.start()

    dispatcher = UartDispatcher(uart)
    videomute_service = VideoMuteService(dispatcher, uart, power_service)

    # ------------------------------------------------------------
    # Motion → Unmute immediately → Auto-mute after 5s
    # ------------------------------------------------------------

    mute_timer = None
    mute_timer_lock = threading.Lock()

    def schedule_mute():
        nonlocal mute_timer

        def do_mute():
            print("Auto-muting after inactivity")
            videomute_service.mute()

        with mute_timer_lock:
            if mute_timer:
                mute_timer.cancel()

            mute_timer = threading.Timer(5.0, do_mute)
            mute_timer.daemon = True
            mute_timer.start()

    def on_motion():
        print("Motion detected! " + time.strftime("%H:%M:%S"))

        videomute_service.unmute()
        schedule_mute()

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

        with mute_timer_lock:
            if mute_timer:
                mute_timer.cancel()

        uart.stop()

        for svc in (
            getattr(ir_service, "ir_emulator", None),
            getattr(power_service, "power_status", None),
        ):
            if svc:
                svc.close()

        print("Cleanup complete.")


if __name__ == "__main__":
    main()