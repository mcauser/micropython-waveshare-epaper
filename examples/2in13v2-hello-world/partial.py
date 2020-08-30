import epaper2in13v2
from machine import Pin, SPI
from time import sleep_ms

sck=Pin(14)
miso=Pin(12)
mosi=Pin(13)
cs=Pin(15)
hsspi = SPI(1, baudrate=4000000, polarity=0, phase=0)
dc = Pin(2)
rst = Pin(4)
busy = Pin(10)

e = epaper2in13v2.EPD(hsspi, cs, dc, rst, busy)
e.init()

h = 250
w = 128 # actually it is 122 but better to be a multiple of 8
x = 0
y = 0

# --------------------
e.clear_display(0xff)

import framebuf
buf = bytearray(w * h // 8)
fb = framebuf.FrameBuffer(buf, w, h, framebuf.MONO_HLSB)
black = 0
white = 1
fb.fill(white)
fb.fill_rect(2, 2, 118, 98, black)
fb.text('Hello World',16, 60, white)
##fb.line(30, 70, 40, 80, black)
##fb.rect(30, 90, 10, 10, black)
##fb.fill_rect(20, 0, 10, 10, black)
e.display_master_image(buf)
e.set_partial_update_mode()
e.init()

fb.rect(12, 56, 96, 16, white)
e.display(buf)

e.sleep()
fb.fill_rect(56, 20, 20, 20, white)
e.display(buf)

e.wakeup()
fb.text("wakeup", 10, 20, white)
e.display(buf)
e.clear_display(0xff)
e.sleep()
