import threading
import logging
import signal

from smartmirrord.logging_config import setup_logging
from smartmirrord.config import SCHEDULE_JSON, DISPLAY_POLICY_TIMEOUT
from smartmirrord.services.power_service import PowerService
from smartmirrord.services.ir_service import IRService
from smartmirrord.services.display_availability_service import DisplayAvailabilityService
from smartmirrord.services.motion_service import MotionService
from smartmirrord.services.display_policy_service import DisplayPolicyService
from smartmirrord.web.routes import web_remote
from smartmirrord.hardware.uart_transport import UartTransport
from smartmirrord.services.uart_dispatcher import UartDispatcher
from smartmirrord.services.videomute_service import VideoMuteService

logger = logging.getLogger(__name__)


def wait_for_shutdown(stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        stop_event.wait(timeout=60)


def initialize_services(schedule_json):
    # Core services
    power_service = PowerService()
    ir_service = IRService()
    uart = UartTransport()
    dispatcher = UartDispatcher(uart)
    motion_service = MotionService()

    # Core policy services
    videomute_service = VideoMuteService(dispatcher, uart, power_service)
    display_availability_service = DisplayAvailabilityService(power_service, ir_service)
    display_policy_service = DisplayPolicyService(
        videomute_service,
        motion_service,
        power_service,
        DISPLAY_POLICY_TIMEOUT,
        schedule_json,
    )

    return {
        "power_service": power_service,
        "ir_service": ir_service,
        "uart": uart,
        "dispatcher": dispatcher,
        "motion_service": motion_service,
        "videomute_service": videomute_service,
        "display_availability_service": display_availability_service,
        "display_policy_service": display_policy_service,
    }


def start_services(services):
    for service in services.values():
        logger.info(f"Starting {service.__class__.__name__}")
        service.start()


def stop_services(services):
    for service in services.values():
        logger.info(f"Stopping {service.__class__.__name__}")
        service.stop()


def main():
    setup_logging()

    services = initialize_services(SCHEDULE_JSON)
    start_services(services)

    web_remote.config["IR_SERVICE"] = services["ir_service"]
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

    stop_event = threading.Event()

    def handle_shutdown_signal(signum=None, frame=None):
        if stop_event.is_set():
            return
        logger.info("Shutdown signal received. Stopping services...")
        try:
            stop_services(services)
            logger.info("Cleanup complete.")
        finally:
            stop_event.set()

    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    signal.signal(signal.SIGINT, handle_shutdown_signal)

    logger.info("SmartMirror daemon running.")

    try:
        wait_for_shutdown(stop_event)
    finally:
        handle_shutdown_signal()


if __name__ == "__main__":
    main()
