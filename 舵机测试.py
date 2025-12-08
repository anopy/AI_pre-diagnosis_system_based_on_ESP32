from machine import Pin,PWM
import time

servo = PWM(Pin(26))
servo.freq(50)
servo.duty_u16(4915)
time.sleep(1)
servo.duty_u16(1638) # 舵机复位