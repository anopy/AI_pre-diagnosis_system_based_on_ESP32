import urequests
import time
import ubinascii
import gc
import hashlib
import network
import random
import ure

# -------------------------- 基础配置 --------------------------
WIFI_SSID = "iPhone 16"
WIFI_PASSWORD = "0d000721"
APP_KEY = "6816d7fc77e186a0"
APP_SECRET = "G1WLNQJ0zuvbHhNqZA874QQO4i1Mo8DN"

ASR_AUDIO_FILE = "rec_adjusted.wav"
ASR_API_URL = "http://openapi.youdao.com/asrapi"
TTS_API_URL = "http://openapi.youdao.com/ttsapi"
TTS_OUTPUT_FILE = "tts_result.wav"
CHUNK_SIZE = 256  # 内存安全分块
MAX_AUDIO_SIZE = 300 * 1024  # 限制音频最大300KB（≈9秒），避免请求体过大

# URL编码（严格遵循RFC3986，适配API要求）
def url_encode(s):
    safe_chars = set(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~')
    encoded = []
    for c in s.encode('utf-8'):
        if c in safe_chars:
            encoded.append(chr(c))
        else:
            encoded.append(f'%{c:02X}')
    return ''.join(encoded)

# -------------------------- ASR核心重构（合规+省内存） --------------------------
def get_audio_data_chunks(file_path):
    """分块读取音频，返回迭代器（不占内存）"""
    with open(file_path, 'rb') as f:
        while chunk := f.read(CHUNK_SIZE):
            yield chunk

def calculate_full_b64_length(file_path):
    """精确计算完整Base64长度（用于签名和请求体）"""
    total_len = 0
    for chunk in get_audio_data_chunks(file_path):
        total_len += len(ubinascii.b2a_base64(chunk).decode().replace('\n', ''))
    return total_len

def generate_full_q(file_path):
    """生成完整URL编码后的Base64字符串（迭代器形式，不占内存）"""
    for chunk in get_audio_data_chunks(file_path):
        b64 = ubinascii.b2a_base64(chunk).decode().replace('\n', '')
        yield url_encode(b64)

def generate_sign(q_trunc, salt, curtime):
    sign_str = f"{APP_KEY}{q_trunc}{salt}{curtime}{APP_SECRET}"
    return ubinascii.hexlify(hashlib.sha256(sign_str.encode()).digest()).decode().upper()

def generate_salt():
    return f"{int(time.time())}{random.randint(1000, 9999)}"

def youdao_asr():
    spk1data = ""
    try:
        # 1. 检查音频大小（避免请求体过大被重置）
        with open(ASR_AUDIO_FILE, 'rb') as f:
            f.seek(0, 2)
            audio_size = f.tell()
        if audio_size == 0:
            raise Exception("音频文件为空")
        if audio_size > MAX_AUDIO_SIZE:
            raise Exception(f"音频过大（{audio_size}字节），建议≤300KB")
        print(f"\n📤 音频文件大小：{audio_size} 字节")
        
        # 2. 精确计算Base64总长度（用于构造合规请求头）
        print("📏 计算Base64总长度...")
        full_b64_len = calculate_full_b64_length(ASR_AUDIO_FILE)
        
        # 3. 生成合规签名（按文档：前10+长度+后10）
        print("📝 生成合规签名...")
        # 读取首尾块用于q_trunc
        first_b64 = ""
        last_b64 = []
        for i, chunk in enumerate(generate_full_q(ASR_AUDIO_FILE)):
            if i == 0:
                first_b64 = chunk[:10]  # 取第一块前10字符
            last_b64.append(chunk)
        last_b64_str = ''.join(last_b64)[-10:]  # 取最后10字符
        q_trunc = f"{first_b64}{full_b64_len}{last_b64_str}"
        
        salt = generate_salt()
        curtime = str(int(time.time()))
        sign = generate_sign(q_trunc, salt, curtime)
        
        # 4. 构造固定参数（所有参数严格URL编码）
        print("📋 构造合规请求参数...")
        fixed_params = {
            "appKey": url_encode(APP_KEY),
            "langType": url_encode("zh-CHS"),
            "salt": url_encode(salt),
            "curtime": url_encode(curtime),
            "sign": url_encode(sign),
            "signType": url_encode("v3"),
            "format": url_encode("wav"),
            "rate": url_encode("16000"),
            "channel": url_encode("1"),
            "type": url_encode("1")
        }
        fixed_part = "&".join([f"{k}={v}" for k, v in fixed_params.items()])
        
        # 5. 计算完整请求体长度（固定参数+q参数）
        total_request_len = len(fixed_part) + 1 + full_b64_len  # 1是"&q="的长度
        
        # 6. 发送请求（分块发送，请求头完整合规）
        print("🚀 发送合规ASR请求...")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Content-Length": str(total_request_len),  # 关键：告知服务器总长度
            "Connection": "Keep-Alive",
            "User-Agent": "ESP32-MicroPython"  # 新增：模拟标准客户端
        }
        
        # 建立连接，分两部分发送
        conn = urequests.request('POST', ASR_API_URL, headers=headers)
        # 先发送固定参数+q参数前缀
        conn.raw.write(f"{fixed_part}&q=".encode())
        # 再分块发送URL编码后的Base64数据
        for q_chunk in generate_full_q(ASR_AUDIO_FILE):
            conn.raw.write(q_chunk.encode())
            gc.collect()
            print(f"已发送：{len(q_chunk)} 字节（剩余内存：{gc.mem_free()}）", end='\r')
        
        # 7. 接收并解析响应
        print("\n📥 接收识别结果...")
        response = conn.raw.read()
        conn.close()
        
        if not response:
            raise Exception("服务器返回空响应")
        
        # 解析JSON（处理可能的编码问题）
        import json
        try:
            result = json.loads(response.decode('utf-8', errors='ignore'))
        except:
            raise Exception(f"响应解析失败，原始数据：{response[:100]}...")
        
        if result.get("errorCode") == "0":
            spk1data = result["result"][0] if result.get("result") else ""
            print(f"🎉 ASR识别成功：{spk1data}")
        else:
            error_msg = {
                "202": "签名校验失败（检查APP_KEY/SECRET或参数格式）",
                "3001": "音频格式不支持（需16k单声道wav）",
                "3007": "音频文件过大（≤10M）",
                "3008": "音频时长过长（≤60秒）",
                "401": "权限不足（未开通ASR服务）"
            }.get(result.get("errorCode"), f"错误码：{result.get('errorCode')}")
            raise Exception(f"识别失败：{error_msg}")
    
    except Exception as e:
        print(f"\n❌ ASR异常：{e}")
    finally:
        gc.collect()
    return spk1data

# -------------------------- TTS部分（复用合规逻辑） --------------------------
def youdao_tts(text):
    if not text:
        raise Exception("TTS输入文本为空")
    try:
        print(f"\n📢 开始TTS合成（文本：{text}）...")
        salt = generate_salt()
        curtime = str(int(time.time()))
        sign_str = f"{APP_KEY}{text}{salt}{curtime}{APP_SECRET}"
        sign = ubinascii.hexlify(hashlib.sha256(sign_str.encode()).digest()).decode().upper()
        
        params = {
            "appKey": APP_KEY,
            "q": url_encode(text),
            "salt": salt,
            "curtime": curtime,
            "sign": sign,
            "signType": "v3",
            "voice": VOICE_TYPE,
            "speed": SPEED,
            "volume": VOLUME,
            "format": "wav",
            "langType": "zh-CHS"
        }
        data = "&".join([f"{k}={v}" for k, v in params.items()])
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Content-Length": str(len(data)),
            "Connection": "Keep-Alive"
        }
        
        response = urequests.post(TTS_API_URL, headers=headers, data=data, timeout=15)
        if response.status_code == 200:
            with open(TTS_OUTPUT_FILE, "wb") as f:
                while chunk := response.raw.read(CHUNK_SIZE):
                    f.write(chunk)
                    gc.collect()
            print(f"✅ TTS合成完成！输出文件：{TTS_OUTPUT_FILE}")
        else:
            import json
            result = json.loads(response.text)
            raise Exception(f"TTS失败（错误码：{result.get('errorCode')}）")
        response.close()
    except Exception as e:
        print(f"❌ TTS异常：{e}")
    finally:
        gc.collect()

# -------------------------- 主程序入口 --------------------------
if __name__ == "__main__":
    print("=====================================")
    print("  ESP32 有道ASR→TTS（合规终极版）")
    print("=====================================")
    
    try:
        asr_result = youdao_asr()
        if asr_result:
            youdao_tts(asr_result)
        print("\n📌 流程结束！")
    except Exception as e:
        print(f"\n❌ 程序异常：{e}")
    finally:
        gc.collect()
    print("=====================================")