import ssd1309
import time
from machine import sleep, SoftI2C, Pin, Timer
from utime import ticks_diff, ticks_us
from max30102 import MAX30102, MAX30105_PULSE_AMP_MEDIUM
from hrcalc import calc_hr_and_spo2
pin25 = Pin(25, Pin.OUT)  # 继电器引脚
BEATS = 0  # 存储心率
FINGER_FLAG = False  # 默认表示未检测到手指
SPO2 = 0  # 存储血氧
TEMPERATURE = 0  # 存储温度
HREAT_LIST = []  # 存储心率的最新30次数据
TEMP_LIST = []  # 存储温度的最新10次数据
DETECT_COMPLETE = False  # 检测完成标志
pin25.value(0)
# 初始化I2C（SCL=13，SDA=12，与你的硬件匹配）
i2c = SoftI2C(scl=Pin(13), sda=Pin(12), freq=400000)

# 初始化SSD1309屏幕（128x64分辨率）
oled = ssd1309.SSD1309(i2c, width=128, height=64)

# ---------------------------------------------------- #
oled.clear()

second = 's'
def display_info(t):
    global HREAT_LIST, TEMP_LIST, DETECT_COMPLETE
    
    if FINGER_FLAG is False:
        HREAT_LIST.clear()
        TEMP_LIST.clear()
        return
    oled.clear()
    oled.text('HR: ',20,24)
    oled.text(str(BEATS),20,34)
    oled.text('TEMP',20,44)
    oled.text(str(TEMPERATURE),20,54)
    oled.show()

    if len(HREAT_LIST) < 18:
        HREAT_LIST.append(BEATS)
        HREAT_LIST = HREAT_LIST[-18:]
        a = "DO NOT MOVE&TALK"
        b = 18 - len(HREAT_LIST)
        oled.text(str(a),0,0)
        oled.text(str(b),10,12)
        oled.text(second,30,12)
        oled.text('left',42,12)
        oled.show()
    elif len(TEMP_LIST) < 10:
        TEMP_LIST.append(TEMPERATURE)
        TEMP_LIST = TEMP_LIST[-10:]
        a1 = "DO NOT MOVE&TALK"
        b1 = 10 - len(TEMP_LIST)
        oled.text(str(a1),0,0)
        oled.text(str(b1),10,12)
        oled.text(second,30,12)
        oled.text('left',42,12)
        oled.show()
    else:
        oled.clear()
        oled.text("----complete----",0,0)
        oled.show()
        DETECT_COMPLETE = True  # 标记检测完成


def main():
    global BEATS, FINGER_FLAG, SPO2, TEMPERATURE, DETECT_COMPLETE
    
    # 创建I2C对象(检测MAX30102)
    i2c = SoftI2C(sda=Pin(27), scl=Pin(14), freq=400000)

    # 创建传感器对象
    sensor = MAX30102(i2c=i2c)

    # 检测是否有传感器
    if sensor.i2c_address not in i2c.scan():
        print("没有找到传感器")
        return
    elif not (sensor.check_part_id()):
        print("检测到的I2C设备不是MAX30102或者MAX30105")
        return
    else:
        oled.text("Module Detected",6,28)
        oled.show()
        time.sleep(2.5)
        oled.clear()
        tt = 5
        pin25.value(1
                    )
        while tt >0:
            oled.text("Put your finger",2,28)
            oled.text("in",40,40)
            oled.text(str(tt),62,40)
            oled.text(second,73,40)
            oled.show()
            time.sleep(1)
            oled.clear()
            tt = tt - 1

    # 配置
    sensor.setup_sensor()
    sensor.set_sample_rate(400)
    sensor.set_fifo_average(8)
    sensor.set_active_leds_amplitude(MAX30105_PULSE_AMP_MEDIUM)

    t_start = ticks_us()
    MAX_HISTORY = 32
    history = []
    beats_history = []
    beat = False
    red_list = []
    ir_list = []

    while True:
        # 检测完成则退出循环
        if DETECT_COMPLETE:
            oled.clear()
            oled.text("Success!",38,5)
            oled.text('HR: ',20,20)
            oled.text(str(BEATS),20,30)
            oled.text('TEMP:',20,40)
            oled.text(str(TEMPERATURE),20,50)
            oled.show()
            pin25.value(0)
            break
            
        sensor.check()
        if sensor.available():
            red_reading = sensor.pop_red_from_storage()
            ir_reading = sensor.pop_ir_from_storage()
            
            if red_reading < 1000:
                oled.clear()
                oled.text('Error! No Finger',0,25)
                oled.show()
                pin25.value(0)
                FINGER_FLAG = False
                time.sleep(1)
                break
            else:
                FINGER_FLAG = True

            if len(HREAT_LIST) < 18:
                history.append(red_reading)
                history = history[-MAX_HISTORY:]
                
                minima, maxima = min(history), max(history)
                threshold_on = (minima + maxima * 3) // 4
                threshold_off = (minima + maxima) // 2
                
                if not beat and red_reading > threshold_on:
                    beat = True                    
                    t_us = ticks_diff(ticks_us(), t_start)
                    t_s = t_us/1000000
                    f = 1/t_s
                    bpm = f * 60
                    if bpm < 500:
                        t_start = ticks_us()
                        beats_history.append(bpm)                    
                        beats_history = beats_history[-MAX_HISTORY:]
                        BEATS = round(sum(beats_history)/len(beats_history), 2)
                if beat and red_reading < threshold_off:
                    beat = False
            elif len(TEMP_LIST) < 10:
                TEMPERATURE = sensor.read_temperature()
    
    # 停止定时器并释放资源
    timer.deinit()

# ---------------------------------------------------------------- #
if __name__ == '__main__':
    timer = Timer(1)
    timer.init(period=1000, mode=Timer.PERIODIC, callback=display_info)
    main()
# ---------------------------------------------------------------- #


