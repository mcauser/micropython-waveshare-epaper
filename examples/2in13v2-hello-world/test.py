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
e.init(e.FULL_UPDATE)

h = 250
w = 122
x = 0
y = 0

# --------------------

import framebuf
buf = bytearray(w * h // 8)
fb = framebuf.FrameBuffer(buf, w, h, framebuf.MONO_HLSB)
black = 0
white = 1
fb.fill(white)
fb.text('Hello World',20, 60, black)
#fb.pixel(30, 10, black)
#fb.hline(30, 30, 10, black)
#fb.vline(30, 50, 10, black)
#fb.line(30, 70, 40, 80, black)
#fb.rect(30, 90, 10, 10, black)
#fb.fill_rect(20, 0, 10, 10, black)
#for row in range(0,37):
#	fb.text(str(row),0,row*8,black)
#fb.text('Line 36',0,288,black)
#fb.text('text2',30, 110, black)

fb.text('00', 0, 00, black)
fb.text('20', 0, 20, black)
fb.text('40', 0, 40, black)
fb.text('50', 0, 50, black)
fb.text('70', 0, 70, black)
fb.text('80', 0, 80, black)
fb.text('100', 0, 100, black)
fb.text('120', 0, 120, black)
fb.text('140', 0, 140, black)
fb.text('110', 0, 110, black)
fb.text('130', 0, 130, black)
fb.text('150', 0, 150, black)
fb.text('170', 0, 170, black)
fb.text('190', 0, 190, black)
fb.text('210', 0, 210, black)
fb.text('230', 0, 230, black)
fb.text('240', 0, 240, black)
e.display(buf)

e.sleep()
print("Waiting 3s")
sleep_ms(3000)
print("Wake up")
e.wakeup()
fb.rect(30, 90, 10, 10, black)
e.display(buf)
e.sleep()

