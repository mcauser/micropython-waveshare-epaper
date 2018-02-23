import epaper2in9
from pyb import SPI

# SPI3 on Black STM32F407VET6
spi = SPI(3, SPI.MASTER, baudrate=2000000, polarity=0, phase=0)
cs = pyb.Pin('PB6')
dc = pyb.Pin('PB7')
rst = pyb.Pin('PB8')
busy = pyb.Pin('PB9')

e = epaper2in9.EPD(spi, cs, dc, rst, busy)
e.init()

w = 128
h = 296
x = 0
y = 0

# write hello world with black bg and white text
from image_dark import hello_world_dark
e.clear_frame_memory(b'\xFF')
e.set_frame_memory(hello_world_dark, x, y, w, h)
e.display_frame()

# write hello world with white bg and black text
from image_light import hello_world_light
e.clear_frame_memory(b'\xFF')
e.set_frame_memory(hello_world_light, x, y, w, h)
e.display_frame()

# clear display
e.clear_frame_memory(b'\xFF')
e.display_frame()

# use a frame buffer
# 128 * 296 / 8 = 4736 - thats a lot of pixels
import framebuf
buf = bytearray(128 * 296 // 8)
fb = framebuf.FrameBuffer(buf, 128, 296, framebuf.MONO_HLSB)
black = 0
white = 1
fb.fill(white)
fb.text('Hello World',30,0,black)
fb.pixel(30, 10, black)
fb.hline(30, 30, 10, black)
fb.vline(30, 50, 10, black)
fb.line(30, 70, 40, 80, black)
fb.rect(30, 90, 10, 10, black)
fb.fill_rect(30, 110, 10, 10, black)
for row in range(0,37):
	fb.text(str(row),0,row*8,black)
fb.text('Line 36',0,288,black)
e.set_frame_memory(buf, x, y, w, h)
e.display_frame()
