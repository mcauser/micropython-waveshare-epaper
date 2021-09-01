import epaper2in13
from machine import Pin,SPI
from time import sleep_ms

# SPI #2 on ESP32
spi = SPI(2,baudrate=2000000, polarity=0, phase=0) # miso=Pin(12), mosi=Pin(23), sck=Pin(18))
cs = Pin(5)
dc = Pin(2)
rst = Pin(15)
busy = Pin(4)

e = epaper2in13.EPD(spi, cs, dc, rst, busy)
e.init(e.FULL_UPDATE)

y_start = 6   # Y addresses start at 6 due to the memory layout

import framebuf
buf = bytearray(e.width * e.height // 8)
fb = framebuf.FrameBuffer(buf, e.height, e.width, framebuf.MONO_VLSB)


# --------------------

fb.fill(0)
fb.text('MicroPython!', 2, y_start + 2, 0xffff)
fb.rect(0, y_start, 250, 122, 0xffff)
e.set_frame_memory(buf,0,0,e.width,e.height)
e.display_frame()

sleep_ms(2000)  # wait for 2 seconds before doing a partial update

# --------------------

e.init(e.PART_UPDATE)

fb = framebuf.FrameBuffer(buf, 200, 32, framebuf.MONO_VLSB)
fb.fill(0x0)
for i in range(0,32/2-1,2):
    fb.rect(i, i, 200-i*2, 32-i*2, 0xffff)

e.set_frame_memory(buf,8,32,32,200) # 8px from bottom, 25px from left

e.display_frame()

