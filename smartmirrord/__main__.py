import threading
import logging
import signal

from smartmirrord.logging_config import setup_logging
from smartmirrord.config import SCHEDULE_JSON, DISPLAY_POLICY_TIMEOUT
from smartmirrord.container import Container
from smartmirrord.web.routes import web_remote

logger = logging.getLogger(__name__)


def wait_for_shutdown(stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        stop_event.wait(timeout=60)


def start_services(container: Container) -> None:
    """Start all services in dependency order."""
    for service in container.startup_order():
        logger.info(f"Starting {service.__class__.__name__}")
        service.start()


def stop_services(container: Container) -> None:
    """Stop all services in reverse dependency order."""
    for service in reversed(container.startup_order()):
        logger.info(f"Stopping {service.__class__.__name__}")
        service.stop()


def main():
    setup_logging()

    # Create and configure container
    container = Container()
    container.config.from_dict({
        'display_policy_timeout': DISPLAY_POLICY_TIMEOUT,
        'schedule_json': SCHEDULE_JSON,
    })

    # Start services in correct order
    start_services(container)

    web_remote.config["IR_SERVICE"] = container.ir_service()
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
            stop_services(container)
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
