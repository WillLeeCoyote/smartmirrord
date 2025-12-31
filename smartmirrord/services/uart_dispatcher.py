import logging

logger = logging.getLogger(__name__)


class UartDispatcher:
    def __init__(self, transport):
        self._handlers = []
        self._transport = transport
        self._running = False

    def register_handler(self, handler) -> None:
        """
        Register a handler.

        Handler must implement:
          - can_handle(line: str) -> bool
          - handle(line: str) -> None
        """
        self._handlers.append(handler)

    def start(self):
        if self._running:
            return

        self._transport.register_listener(self._on_line)
        self._running = True
        logger.info("UartDispatcher started")

    def stop(self):
        if not self._running:
            return

        self._running = False
        logger.info("UartDispatcher stopped")

    def _on_line(self, line: str) -> None:
        if not self._running:
            return

        logger.debug("Dispatcher RX: %s", line)

        for handler in self._handlers:
            try:
                if handler.can_handle(line):
                    handler.handle(line)
            except Exception:
                logger.exception(
                    "UART handler error (%s)",
                    handler.__class__.__name__,
                )
