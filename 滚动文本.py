from machine import SoftI2C, Pin
import ssd1309
import time

# 初始化I2C（SCL=13，SDA=12，与你的硬件匹配）
i2c = SoftI2C(scl=Pin(13), sda=Pin(14), freq=400000)

# 初始化SSD1309屏幕（128x64分辨率）
oled = ssd1309.SSD1309(i2c, width=128, height=64)

# 要滚动的文本
scroll_text = "saki!saki!"

# 滚动参数
x_pos = 128  # 初始X坐标（从屏幕右侧外面开始）
y_pos = 20   # 固定Y坐标（垂直居中）
speed = 50   # 滚动速度（毫秒，值越小越快）
text_width = len(scroll_text) * 8  # 文本总宽度（8x8字体，每个字符占8像素宽）

try:
    while True:
        # 清屏（清空缓冲区）
        oled.fill(0)
        
        # 绘制文本（当前X坐标）
        oled.text(scroll_text, x_pos, y_pos)
        
        # 刷新屏幕（将缓冲区内容显示出来）
        oled.show()
        
        # 更新X坐标（向左滚动，每次减1）
        x_pos -= 1
        
        # 当文本完全滚出屏幕左侧后，重置到右侧重新开始
        if x_pos < -text_width:
            x_pos = 128
        
        # 控制滚动速度
        time.sleep_ms(speed)

except KeyboardInterrupt:
    # 按Ctrl+C停止时清屏
    oled.fill(0)
    oled.show()
    print("滚动已停止")
