import logging

logger = logging.getLogger(__name__)


class UartDispatcher:
    def __init__(self, transport):
        self._handlers = []
        self._transport = transport
        self._transport.register_listener(self._on_line)

    def register_handler(self, handler) -> None:
        """
        Register a handler.

        Handler must implement:
          - can_handle(line: str) -> bool
          - handle(line: str) -> None
        """
        self._handlers.append(handler)

    def _on_line(self, line: str) -> None:
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
