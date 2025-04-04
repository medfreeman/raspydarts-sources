#!/usr/bin/python3
import time
import os
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

try:
    print("Start vibrating...waiting...")
    vibration = 1
    while True:
        if GPIO.input(20) == GPIO.HIGH :
            print("vibrate power ! ", vibration)
            vibration = vibration + 1
        time.sleep(0.1)
        
        
except KeyboardInterrupt:
    GPIO.cleanup()