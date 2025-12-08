from machine import Pin
import time

pin25 = Pin(25, Pin.OUT)
while True:
    pin25.value(0)
    time.sleep(0.5)
    pin25.value(1)
    time.sleep(0.5)
