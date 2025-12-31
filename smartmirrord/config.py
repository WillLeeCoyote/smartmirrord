import os
import serial


def get_bool_env(key, default):
    """Parse boolean environment variable."""
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')


def get_int_env(key, default):
    """Parse integer environment variable."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_float_env(key, default):
    """Parse float environment variable."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_TO_CONSOLE = get_bool_env("LOG_TO_CONSOLE", True)
LOG_TO_FILE = get_bool_env("LOG_TO_FILE", True)
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "../log/smartmirrord.log")

# Fine-grained control
UART_DEBUG = get_bool_env("UART_DEBUG", False)

# Hardware config
GPIO_CHIP_PATH = os.getenv("GPIO_CHIP_PATH", "/dev/gpiochip0")
GPIO_POWER_STATUS_PIN = get_int_env("GPIO_POWER_STATUS_PIN", 23)
GPIO_IR_INPUT_PIN = get_int_env("GPIO_IR_INPUT_PIN", 27)

CAMERA_WIDTH = get_int_env("CAMERA_WIDTH", 640)
CAMERA_HEIGHT = get_int_env("CAMERA_HEIGHT", 480)

MOTION_WIDTH = get_int_env("MOTION_WIDTH", 320)
MOTION_HEIGHT = get_int_env("MOTION_HEIGHT", 240)

MOTION_THRESHOLD = get_int_env("MOTION_THRESHOLD", 150)
MOTION_COOLDOWN_SEC = get_int_env("MOTION_COOLDOWN_SEC", 6)

UART_PORT = os.getenv("UART_PORT", "/dev/serial0")
UART_BAUDRATE = get_int_env("UART_BAUDRATE", 115200)
UART_PARITY = serial.PARITY_NONE
UART_STOPBITS = serial.STOPBITS_ONE
UART_BYTESIZE = serial.EIGHTBITS
UART_TIMEOUT = .1
UART_READ_CHUNK_SIZE = 1024
UART_WRITE_EOL = '\n'

# Policy level config
SCHEDULE_JSON = {
    "quiet_hours": [
        {"start": "23:00", "end": "06:00"}
    ]
}

DISPLAY_POLICY_TIMEOUT = get_int_env("DISPLAY_POLICY_TIMEOUT", 15)
