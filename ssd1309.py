"""MicroPython SSD1309 OLED display driver (I2C适配版)"""
from micropython import const
from framebuf import FrameBuffer, MONO_VLSB
from utime import sleep_ms


class SSD1309:
    # 命令常量
    DISPLAY_OFF = const(0xAE)
    DISPLAY_ON = const(0xAF)
    SET_MEM_ADDR = const(0x20)
    SET_COL_ADDR = const(0x21)
    SET_PAGE_ADDR = const(0x22)
    SET_SEG_REMAP = const(0xA0)
    SET_COM_SCAN = const(0xC0)
    SET_COM_SCAN_FLIP = const(0xC8)
    SET_DISP_START_LINE = const(0x40)
    SET_CONTRAST = const(0x81)
    SET_CHARGE_PUMP = const(0x8D)
    SET_PRECHARGE = const(0xD9)
    SET_VCOM_DESEL = const(0xDB)
    SET_ENTIRE_ON = const(0xA4)
    SET_NORM_INV = const(0xA6)
    SET_DISP_OFFSET = const(0xD3)
    SET_MUX_RATIO = const(0xA8)
    SET_DISP_CLK_DIV = const(0xD5)
    SET_COM_PIN_CFG = const(0xDA)

    def __init__(self, i2c, width=128, height=64, addr=0x3C):
        self.i2c = i2c
        self.addr = addr
        self.width = width
        self.height = height
        self.pages = height // 8
        
        # 初始化帧缓冲区
        self.buffer = bytearray(self.pages * width)
        self.fb = FrameBuffer(self.buffer, width, height, MONO_VLSB)
        
        # 初始化屏幕
        self.init_display()

    def init_display(self):
        # 初始化命令序列
        init_cmds = [
            self.DISPLAY_OFF,
            self.SET_DISP_CLK_DIV, 0x80,  # 时钟分频
            self.SET_MUX_RATIO, self.height - 1,  # 多路复用比
            self.SET_DISP_OFFSET, 0x00,  # 显示偏移
            self.SET_DISP_START_LINE | 0x00,  # 起始行
            self.SET_CHARGE_PUMP, 0x14,  # 电荷泵使能
            self.SET_MEM_ADDR, 0x00,  # 水平地址模式
            self.SET_SEG_REMAP | 0x01,  # 段重映射
            self.SET_COM_SCAN_FLIP,  # COM扫描方向反转
            self.SET_COM_PIN_CFG, 0x12 if self.height == 64 else 0x02,  # COM引脚配置
            self.SET_CONTRAST, 0xFF,  # 对比度
            self.SET_PRECHARGE, 0xF1,  # 预充电周期
            self.SET_VCOM_DESEL, 0x40,  # VCOM电压
            self.SET_ENTIRE_ON,  # 显示RAM内容
            self.SET_NORM_INV,  # 正常显示
            self.DISPLAY_ON  # 打开显示
        ]
        
        for cmd in init_cmds:
            self.write_cmd(cmd)
        self.clear()

    def write_cmd(self, cmd):
        # I2C命令发送（0x00为命令标志）
        self.i2c.writeto_mem(self.addr, 0x00, bytearray([cmd]))

    def write_data(self, data):
        # I2C数据发送（0x40为数据标志）
        self.i2c.writeto_mem(self.addr, 0x40, data)

    def clear(self):
        # 清空缓冲区
        self.buffer[:] = b'\x00' * len(self.buffer)
        self.show()

    def show(self):
        # 设置列地址
        self.write_cmd(self.SET_COL_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.width - 1)
        # 设置页地址
        self.write_cmd(self.SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        # 发送缓冲区数据
        self.write_data(self.buffer)

    def text(self, string, x, y):
        # 兼容ssd1306的text方法（8x8字体）
        self.fb.text(string, x, y)

    def fill(self, color):
        # 兼容ssd1306的fill方法
        self.fb.fill(color)

    # 以下为扩展绘图方法（可选）
    def pixel(self, x, y, color):
        self.fb.pixel(x, y, color)

    def line(self, x1, y1, x2, y2, color):
        self.fb.line(x1, y1, x2, y2, color)

    def rect(self, x, y, w, h, color):
        self.fb.rect(x, y, w, h, color)

    def fill_rect(self, x, y, w, h, color):
        self.fb.fill_rect(x, y, w, h, color)