from machine import I2S, Pin
import os
 
def init_i2s():
    i2s = I2S(
        0,          # 使用 I2S0
        sck=Pin(4),       # 串行时钟引脚
        ws=Pin(2),        # 字选择（LRCLK）引脚
        sd=Pin(16),        # 串行数据引脚
        mode=I2S.RX,       # 接收模式
        bits=16,           # 16 位采样
        format=I2S.MONO,   # 单声道
        rate=16000,        # 16kHz 采样率
        # ibuf=4096          # 缓冲区大小
        ibuf=2048
    )
    return i2s
 
 
# 录制音频函数：
 
def record_audio(i2s, duration_seconds, file_name):
    with open(file_name, 'wb') as f:
        total_bytes_read = 0
        samples_per_second = 16000
        bytes_per_sample = 2  # 16 位
        total_samples = samples_per_second * duration_seconds
        total_bytes = total_samples * bytes_per_sample
        buffer = bytearray(1024)
 
        try:
            while total_bytes_read < total_bytes:
                num_bytes_read = i2s.readinto(buffer)
                if num_bytes_read:
                    f.write(buffer[:num_bytes_read])
                    total_bytes_read += num_bytes_read
        finally:
            i2s.deinit()
 
            
i2s = init_i2s()
record_audio(i2s, duration_seconds=3, file_name='rec.pcm')    