from machine import I2C, Pin
import ssd1309
import time

# 初始化I2C，SCL=13，SDA=12
i2c = I2C(0, scl=Pin(13), sda=Pin(12), freq=400000)

# 初始化SSD1309显示屏
oled = ssd1309.SSD1309(i2c, width=128, height=64)

# 清除屏幕
oled.clear()

# 显示文本（8x8字体，每行高度8像素）
oled.text("Hello World!", 0, 0)    # 第一行
oled.text("SSD1309 Demo", 0, 10)   # 第二行（偏移10像素）
oled.text("I2C Pins:", 0, 20)      # 第三行
oled.text("SCL:13 SDA:12", 0, 30)  # 第四行
oled.text("MicroPython", 0, 40)    # 第五行
oled.text("1234567890", 0, 50)     # 第六行

# 将缓冲区内容显示到屏幕
oled.show()
