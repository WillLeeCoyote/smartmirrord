import RPi.GPIO as GPIO

# Global GPIO config
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(True)

def cleanup():
    print("Cleaning up GPIO...")
    # GPIO.cleanup()
