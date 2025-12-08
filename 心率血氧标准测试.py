from machine import sleep, SoftI2C, Pin, Timer
import time
from utime import ticks_diff, ticks_us
from max30102 import MAX30102, MAX30105_PULSE_AMP_MEDIUM
from hrcalc import calc_hr_and_spo2


BEATS = 0  # 存储心率
FINGER_FLAG = False  # 默认表示未检测到手指
SPO2 = 0  # 存储血氧
TEMPERATURE = 0  # 存储温度
HREAT_LIST = []  # 存储心率的最新30次数据
TEMP_LIST = []  # 存储温度的最新10次数据
DETECT_COMPLETE = False  # 检测完成标志


def display_info(t):
    global HREAT_LIST, TEMP_LIST, DETECT_COMPLETE
    
    if FINGER_FLAG is False:
        HREAT_LIST.clear()
        TEMP_LIST.clear()
        return

    print('心率: ', BEATS, " 温度：", TEMPERATURE)

    if len(HREAT_LIST) < 20:
        HREAT_LIST.append(BEATS)
        HREAT_LIST = HREAT_LIST[-20:]
        a = ("BPM Testing...", 20 - len(HREAT_LIST))
        print(a)
    elif len(TEMP_LIST) < 10:
        TEMP_LIST.append(TEMPERATURE)
        TEMP_LIST = TEMP_LIST[-10:]
        print("正在检测【温度】...", 10 - len(TEMP_LIST))
    else:
        print("----------已完成检测----------")
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
        print("传感器已识别到")

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
            print("检测完成，退出程序")
            break
            
        sensor.check()
        if sensor.available():
            red_reading = sensor.pop_red_from_storage()
            ir_reading = sensor.pop_ir_from_storage()
            
            if red_reading < 1000:
                print('No finger')
                FINGER_FLAG = False
                time.sleep(1)
                continue
            else:
                FINGER_FLAG = True

            if len(HREAT_LIST) < 20:
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


if __name__ == '__main__':
    timer = Timer(1)
    timer.init(period=1000, mode=Timer.PERIODIC, callback=display_info)
    main()

