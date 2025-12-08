import struct
import gc

# 核心配置（按需修改）
PCM_INPUT = "rec.pcm"       # 根目录输入PCM文件
WAV_OUTPUT = "rec_adjusted.wav"  # 输出调音量后的WAV
VOLUME_RATIO = 4          # 音量倍率（0.1~2.0，超2.0易失真）
SAMPLE_RATE = 16000         # 固定16k采样率
CHANNELS = 1                # 固定单声道
BIT_DEPTH = 16              # 固定16bit位深
BUFFER_SIZE = 4096          # 4KB分块缓存（平衡速度和内存）

bytes_per_sample = BIT_DEPTH // 8
byte_rate = SAMPLE_RATE * CHANNELS * bytes_per_sample
block_align = CHANNELS * bytes_per_sample

def pcm_to_wav_with_volume():
    # 第一步：获取PCM总长度（用于构建WAV头部）
    with open(PCM_INPUT, "rb") as f:
        f.seek(0, 2)  # 移到文件末尾
        pcm_total_size = f.tell()
    wav_file_size = 36 + pcm_total_size  # WAV头部36字节 + 数据长度

    # 构建WAV头部
    wav_header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", wav_file_size, b"WAVE", b"fmt ",
        16, 1, CHANNELS, SAMPLE_RATE,
        byte_rate, block_align, BIT_DEPTH,
        b"data", pcm_total_size
    )

    # 第二步：分块读取PCM → 调节音量 → 写入WAV
    with open(WAV_OUTPUT, "wb") as wav_f:
        wav_f.write(wav_header)  # 先写头部
        with open(PCM_INPUT, "rb") as pcm_f:
            while chunk := pcm_f.read(BUFFER_SIZE):
                adjusted_chunk = bytearray()
                # 遍历每个16bit采样点，调节音量
                for i in range(0, len(chunk), bytes_per_sample):
                    # 读取16bit有符号采样值（小端）
                    sample = struct.unpack("<h", chunk[i:i+2])[0]
                    # 缩放音量 + 限制范围（防溢出失真）
                    adjusted_sample = int(sample * VOLUME_RATIO)
                    adjusted_sample = max(-32768, min(32767, adjusted_sample))
                    # 重新打包成字节
                    adjusted_chunk.extend(struct.pack("<h", adjusted_sample))
                wav_f.write(adjusted_chunk)  # 写调节后的块

    # 清理内存
    del wav_header, adjusted_chunk
    gc.collect()
    print(f"完成！输出文件：{WAV_OUTPUT}")
    print(f"剩余内存：{gc.mem_free()} 字节")

# 执行整合流程
pcm_to_wav_with_volume()