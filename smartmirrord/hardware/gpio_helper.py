import RPi.GPIO as GPIO

# Global GPIO config
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

def cleanup():
    GPIO.cleanup()
