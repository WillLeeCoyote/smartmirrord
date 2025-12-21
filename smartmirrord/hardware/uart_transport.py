import threading
import logging
import serial

from smartmirrord.config import (
    UART_PORT,
    UART_BAUDRATE,
    UART_PARITY,
    UART_STOPBITS,
    UART_BYTESIZE,
    UART_TIMEOUT,
    UART_READ_CHUNK_SIZE,
    UART_WRITE_EOL,
)

logger = logging.getLogger(__name__)


class UartTransport:
    def __init__(self):
        self._serial = None
        self._running = False
        self._thread = None

        self._listeners = []
        self._write_lock = threading.Lock()

        self._rx_buffer = ""

    def start(self) -> None:
        """Open UART and start reader thread."""
        if self._running:
            return

        logger.info("Starting UART transport on %s", UART_PORT)

        self._serial = serial.Serial(
            port=UART_PORT,
            baudrate=UART_BAUDRATE,
            parity=UART_PARITY,
            stopbits=UART_STOPBITS,
            bytesize=UART_BYTESIZE,
            timeout=UART_TIMEOUT,
        )

        self._running = True
        self._thread = threading.Thread(
            target=self._read_loop,
            name="uart-reader",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        if not self._running:
            return

        logger.info("Stopping UART transport")

        self._running = False

        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

        if self._serial:
            try:
                self._serial.close()
            except Exception:
                logger.exception("Error closing UART")
            finally:
                self._serial = None

    def write(self, command: str) -> None:
        if not self._serial:
            raise RuntimeError("UART transport not started")

        data = (command + UART_WRITE_EOL).encode("utf-8")

        with self._write_lock:
            logger.debug("UART TX: %s", command)
            self._serial.write(data)

    def register_listener(self, callback) -> None:
        self._listeners.append(callback)

    def _read_loop(self) -> None:
        logger.debug("UART reader thread started")

        try:
            while self._running:
                try:
                    data = self._serial.read(UART_READ_CHUNK_SIZE)
                except serial.SerialException:
                    logger.exception("UART read error")
                    break

                if not data:
                    continue

                try:
                    text = data.decode("utf-8", errors="ignore")
                except Exception:
                    logger.exception("UART decode error")
                    continue

                self._rx_buffer += text

                while "\n" in self._rx_buffer:
                    line, self._rx_buffer = self._rx_buffer.split("\n", 1)
                    line = line.strip()

                    if not line:
                        continue

                    logger.debug("UART RX: %s", line)
                    self._dispatch_line(line)

        finally:
            logger.debug("UART reader thread exiting")
            self._running = False

    def _dispatch_line(self, line: str) -> None:
        for listener in self._listeners:
            try:
                listener(line)
            except Exception:
                logger.exception("UART listener error")
