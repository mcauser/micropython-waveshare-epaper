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

# --------------------

# write hello world with black bg and white text
from image_dark import hello_world_dark
e.clear_frame_memory(b'\xFF')
e.set_frame_memory(hello_world_dark, x, y, w, h)
e.display_frame()

# --------------------

# write hello world with white bg and black text
from image_light import hello_world_light
e.clear_frame_memory(b'\xFF')
e.set_frame_memory(hello_world_light, x, y, w, h)
e.display_frame()

# --------------------

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

# --------------------

# wrap text inside a box
import framebuf
buf = bytearray(128 * 296 // 8)
fb = framebuf.FrameBuffer(buf, 128, 296, framebuf.MONO_HLSB)
black = 0
white = 1
# clear
fb.fill(white)
e.set_frame_memory(buf, x, y, w, h)
e.display_frame()
# display as much as this as fits in the box
str = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam vel neque in elit tristique vulputate at et dui. Maecenas nec felis lectus. Pellentesque sit amet facilisis dui. Maecenas ac arcu euismod, tempor massa quis, ultricies est.'

# this could be useful as a new method in FrameBuffer
def text_wrap(str,x,y,color,w,h,border=None):
	# optional box border
	if border is not None:
		fb.rect(x, y, w, h, border)
	cols = w // 8
	# for each row
	j = 0
	for i in range(0, len(str), cols):
		# draw as many chars fit on the line
		fb.text(str[i:i+cols], x, y + j, color)
		j += 8
		# dont overflow text outside the box
		if j >= h:
			break

# clear
fb.fill(white)

# draw text box 1
# box position and dimensions
bx = 8
by = 8
bw = w - 16 # 112 = 14 cols
bh = w - 16 # 112 = 14 rows (196 chars in total)
text_wrap(str,bx,by,black,bw,bh,black)
e.set_frame_memory(buf, x, y, w, h)
e.display_frame()

# draw text box 2
bx = 0
by = 128
bw = w # 128 = 16 cols
bh = 6 * 8 # 48 = 6 rows (96 chars in total)
text_wrap(str,bx,by,black,bw,bh,black)
e.set_frame_memory(buf, x, y, w, h)
e.display_frame()

# draw text box 3
bx = 0
by = 184
bw = w//2 # 64 = 8 cols
bh = 8 * 8 # 64 = 8 rows (64 chars in total)
text_wrap(str,bx,by,black,bw,bh,None)
e.set_frame_memory(buf, x, y, w, h)
e.display_frame()

# --------------------
