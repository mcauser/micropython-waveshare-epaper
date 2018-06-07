"""
MicroPython Waveshare 2.7" Black/White/Red GDEW027C44 e-paper display driver
https://github.com/mcauser/micropython-waveshare-epaper

MIT License
Copyright (c) 2017 Waveshare
Copyright (c) 2018 Mike Causer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# is there a black/white/yellow panel?

from micropython import const
from time import sleep_ms
import ustruct

# Display resolution
EPD_WIDTH  = const(176)
EPD_HEIGHT = const(264)

# Display commands
PANEL_SETTING                     = const(0x00)
POWER_SETTING                     = const(0x01)
#POWER_OFF                         = const(0x02)
#POWER_OFF_SEQUENCE_SETTING        = const(0x03)
POWER_ON                          = const(0x04)
#POWER_ON_MEASURE                  = const(0x05)
BOOSTER_SOFT_START                = const(0x06)
DEEP_SLEEP                        = const(0x07)
#DATA_START_TRANSMISSION_1         = const(0x10)
#DATA_STOP                         = const(0x11)
DISPLAY_REFRESH                   = const(0x12)
DATA_START_TRANSMISSION_2         = const(0x13)
#PARTIAL_DATA_START_TRANSMISSION_1 = const(0x14)
#PARTIAL_DATA_START_TRANSMISSION_2 = const(0x15)
PARTIAL_DISPLAY_REFRESH           = const(0x16)
LUT_FOR_VCOM                      = const(0x20)
LUT_WHITE_TO_WHITE                = const(0x21)
LUT_BLACK_TO_WHITE                = const(0x22)
LUT_WHITE_TO_BLACK                = const(0x23)
LUT_BLACK_TO_BLACK                = const(0x24)
PLL_CONTROL                       = const(0x30)
#TEMPERATURE_SENSOR_COMMAND        = const(0x40)
#TEMPERATURE_SENSOR_CALIBRATION    = const(0x41)
#TEMPERATURE_SENSOR_WRITE          = const(0x42)
#TEMPERATURE_SENSOR_READ           = const(0x43)
VCOM_AND_DATA_INTERVAL_SETTING    = const(0x50)
#LOW_POWER_DETECTION               = const(0x51)
#TCON_SETTING                      = const(0x60)
TCON_RESOLUTION                   = const(0x61)
#SOURCE_AND_GATE_START_SETTING     = const(0x62)
#GET_STATUS                        = const(0x71)
#AUTO_MEASURE_VCOM                 = const(0x80)
#VCOM_VALUE                        = const(0x81)
VCM_DC_SETTING_REGISTER           = const(0x82)
#PROGRAM_MODE                      = const(0xA0)
#ACTIVE_PROGRAM                    = const(0xA1)
#READ_OTP_DATA                     = const(0xA2)
POWER_OPTIMIZATION                = const(0xF8) # Power optimization in flow diagram

# Display orientation
ROTATE_0   = const(0)
ROTATE_90  = const(1)
ROTATE_180 = const(2)
ROTATE_270 = const(3)

BUSY = const(0)  # 0=busy, 1=idle

class EPD:
    def __init__(self, spi, cs, dc, rst, busy):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.busy = busy
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=0)
        self.busy.init(self.busy.IN)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.rotate = ROTATE_0

    LUT_VCOM_DC = bytearray(b'\x00\x00\x00\x1A\x1A\x00\x00\x01\x00\x0A\x0A\x00\x00\x08\x00\x0E\x01\x0E\x01\x10\x00\x0A\x0A\x00\x00\x08\x00\x04\x10\x00\x00\x05\x00\x03\x0E\x00\x00\x0A\x00\x23\x00\x00\x00\x01')
    LUT_WW      = bytearray(b'\x90\x1A\x1A\x00\x00\x01\x40\x0A\x0A\x00\x00\x08\x84\x0E\x01\x0E\x01\x10\x80\x0A\x0A\x00\x00\x08\x00\x04\x10\x00\x00\x05\x00\x03\x0E\x00\x00\x0A\x00\x23\x00\x00\x00\x01') # R21H
    LUT_BW      = bytearray(b'\xA0\x1A\x1A\x00\x00\x01\x00\x0A\x0A\x00\x00\x08\x84\x0E\x01\x0E\x01\x10\x90\x0A\x0A\x00\x00\x08\xB0\x04\x10\x00\x00\x05\xB0\x03\x0E\x00\x00\x0A\xC0\x23\x00\x00\x00\x01') # R22H r
    LUT_BB      = LUT_WW # R23H w
    LUT_WB      = bytearray(b'\x90\x1A\x1A\x00\x00\x01\x20\x0A\x0A\x00\x00\x08\x84\x0E\x01\x0E\x01\x10\x10\x0A\x0A\x00\x00\x08\x00\x04\x10\x00\x00\x05\x00\x03\x0E\x00\x00\x0A\x00\x23\x00\x00\x00\x01') # R24H b

    def _command(self, command, data=None):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([command]))
        self.cs(1)
        if data is not None:
            self._data(data)

    def _data(self, data):
        self.dc(1)
        self.cs(0)
        self.spi.write(data)
        self.cs(1)

    def init(self):
        self.reset()
        self._command(POWER_ON)
        self.wait_until_idle()
        self._command(PANEL_SETTING, b'\xAF') # (296x160, LUT from register, B/W/R run both LU1 LU2, scan up, shift right, bootster on) KW-BF   KWR-AF    BWROTP 0f
        self._command(PLL_CONTROL, b'\x3A') # 3A 100HZ   29 150Hz 39 200HZ    31 171HZ
        self._command(POWER_SETTING, b'\x03\x00\x2b\x2b\x09') # VDS_EN VDG_EN, VCOM_HV VGHL_LV[1] VGHL_LV[0], VDH, VDL, VDHR
        self._command(BOOSTER_SOFT_START, b'\x07\x07\x17')
        self._command(POWER_OPTIMIZATION, b'\x60\xA5')
        self._command(POWER_OPTIMIZATION, b'\x89\xA5')
        self._command(POWER_OPTIMIZATION, b'\x90\x00')
        self._command(POWER_OPTIMIZATION, b'\x93\x2A')
        self._command(POWER_OPTIMIZATION, b'\x73\x41')
        self._command(VCM_DC_SETTING_REGISTER, b'\x12')
        self._command(VCOM_AND_DATA_INTERVAL_SETTING, b'\x87') # define by OTP
        self.set_lut()
        self._command(PARTIAL_DISPLAY_REFRESH, b'\x00')

    def wait_until_idle(self):
        while self.busy.value() == BUSY:
            sleep_ms(100)

    def reset(self):
        self.rst(0)
        sleep_ms(200)
        self.rst(1)
        sleep_ms(200)

    def set_lut(self):
        self._command(LUT_FOR_VCOM, self.LUT_VCOM_DC)  # vcom
        self._command(LUT_WHITE_TO_WHITE, self.LUT_WW) # ww --
        self._command(LUT_BLACK_TO_WHITE, self.LUT_BW) # bw r
        self._command(LUT_WHITE_TO_BLACK, self.LUT_BB) # wb w
        self._command(LUT_BLACK_TO_BLACK, self.LUT_WB) # bb b

    def display_frame(self, frame_buffer_black, frame_buffer_red):
        self._command(TCON_RESOLUTION, ustruct.pack(">HH", EPD_WIDTH, EPD_HEIGHT))

        if (frame_buffer_black != None):
            self._command(DATA_START_TRANSMISSION_1)
            sleep_ms(2)
            for i in range(0, self.width * self.height // 8):
                self._data(bytearray([frame_buffer_black[i]]))
            sleep_ms(2)
        if (frame_buffer_red != None):
            self._command(DATA_START_TRANSMISSION_2)
            sleep_ms(2)
            for i in range(0, self.width * self.height // 8):
                self._data(bytearray([frame_buffer_red[i]]))
            sleep_ms(2)

        self._command(DISPLAY_REFRESH)
        self.wait_until_idle()

    def set_rotate(self, rotate):
        if (rotate == ROTATE_0):
            self.rotate = ROTATE_0
            self.width = EPD_WIDTH
            self.height = EPD_HEIGHT
        elif (rotate == ROTATE_90):
            self.rotate = ROTATE_90
            self.width = EPD_HEIGHT
            self.height = EPD_WIDTH
        elif (rotate == ROTATE_180):
            self.rotate = ROTATE_180
            self.width = EPD_WIDTH
            self.height = EPD_HEIGHT
        elif (rotate == ROTATE_270):
            self.rotate = ROTATE_270
            self.width = EPD_HEIGHT
            self.height = EPD_WIDTH

    def set_pixel(self, frame_buffer, x, y, colored):
        if (x < 0 or x >= self.width or y < 0 or y >= self.height):
            return
        if (self.rotate == ROTATE_0):
            self.set_absolute_pixel(frame_buffer, x, y, colored)
        elif (self.rotate == ROTATE_90):
            point_temp = x
            x = EPD_WIDTH - y
            y = point_temp
            self.set_absolute_pixel(frame_buffer, x, y, colored)
        elif (self.rotate == ROTATE_180):
            x = EPD_WIDTH - x
            y = EPD_HEIGHT- y
            self.set_absolute_pixel(frame_buffer, x, y, colored)
        elif (self.rotate == ROTATE_270):
            point_temp = x
            x = y
            y = EPD_HEIGHT - point_temp
            self.set_absolute_pixel(frame_buffer, x, y, colored)

    def set_absolute_pixel(self, frame_buffer, x, y, colored):
        # To avoid display orientation effects
        # use EPD_WIDTH instead of self.width
        # use EPD_HEIGHT instead of self.height
        if (x < 0 or x >= EPD_WIDTH or y < 0 or y >= EPD_HEIGHT):
            return
        if (colored):
            frame_buffer[(x + y * EPD_WIDTH) // 8] |= 0x80 >> (x % 8)
        else:
            frame_buffer[(x + y * EPD_WIDTH) // 8] &= ~(0x80 >> (x % 8))

    def draw_string_at(self, frame_buffer, x, y, text, font, colored):
        image = Image.new('1', (self.width, self.height))
        draw = ImageDraw.Draw(image)
        draw.text((x, y), text, font = font, fill = 255)
        # Set buffer to value of Python Imaging Library image.
        # Image must be in mode 1.
        pixels = image.load()
        for y in range(self.height):
            for x in range(self.width):
                # Set the bits for the column of pixels at the current position.
                if pixels[x, y] != 0:
                    self.set_pixel(frame_buffer, x, y, colored)

    def draw_line(self, frame_buffer, x0, y0, x1, y1, colored):
        # Bresenham algorithm
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while((x0 != x1) and (y0 != y1)):
            self.set_pixel(frame_buffer, x0, y0 , colored)
            if (2 * err >= dy):
                err += dy
                x0 += sx
            if (2 * err <= dx):
                err += dx
                y0 += sy

    def draw_horizontal_line(self, frame_buffer, x, y, width, colored):
        for i in range(x, x + width):
            self.set_pixel(frame_buffer, i, y, colored)

    def draw_vertical_line(self, frame_buffer, x, y, height, colored):
        for i in range(y, y + height):
            self.set_pixel(frame_buffer, x, i, colored)

    def draw_rectangle(self, frame_buffer, x0, y0, x1, y1, colored):
        min_x = x0 if x1 > x0 else x1
        max_x = x1 if x1 > x0 else x0
        min_y = y0 if y1 > y0 else y1
        max_y = y1 if y1 > y0 else y0
        self.draw_horizontal_line(frame_buffer, min_x, min_y, max_x - min_x + 1, colored)
        self.draw_horizontal_line(frame_buffer, min_x, max_y, max_x - min_x + 1, colored)
        self.draw_vertical_line(frame_buffer, min_x, min_y, max_y - min_y + 1, colored)
        self.draw_vertical_line(frame_buffer, max_x, min_y, max_y - min_y + 1, colored)

    def draw_filled_rectangle(self, frame_buffer, x0, y0, x1, y1, colored):
        min_x = x0 if x1 > x0 else x1
        max_x = x1 if x1 > x0 else x0
        min_y = y0 if y1 > y0 else y1
        max_y = y1 if y1 > y0 else y0
        for i in range(min_x, max_x + 1):
            self.draw_vertical_line(frame_buffer, i, min_y, max_y - min_y + 1, colored)

    def draw_circle(self, frame_buffer, x, y, radius, colored):
        # Bresenham algorithm
        x_pos = -radius
        y_pos = 0
        err = 2 - 2 * radius
        if (x >= self.width or y >= self.height):
            return
        while True:
            self.set_pixel(frame_buffer, x - x_pos, y + y_pos, colored)
            self.set_pixel(frame_buffer, x + x_pos, y + y_pos, colored)
            self.set_pixel(frame_buffer, x + x_pos, y - y_pos, colored)
            self.set_pixel(frame_buffer, x - x_pos, y - y_pos, colored)
            e2 = err
            if (e2 <= y_pos):
                y_pos += 1
                err += y_pos * 2 + 1
                if(-x_pos == y_pos and e2 <= x_pos):
                    e2 = 0
            if (e2 > x_pos):
                x_pos += 1
                err += x_pos * 2 + 1
            if x_pos > 0:
                break

    def draw_filled_circle(self, frame_buffer, x, y, radius, colored):
        # Bresenham algorithm
        x_pos = -radius
        y_pos = 0
        err = 2 - 2 * radius
        if (x >= self.width or y >= self.height):
            return
        while True:
            self.set_pixel(frame_buffer, x - x_pos, y + y_pos, colored)
            self.set_pixel(frame_buffer, x + x_pos, y + y_pos, colored)
            self.set_pixel(frame_buffer, x + x_pos, y - y_pos, colored)
            self.set_pixel(frame_buffer, x - x_pos, y - y_pos, colored)
            self.draw_horizontal_line(frame_buffer, x + x_pos, y + y_pos, 2 * (-x_pos) + 1, colored);
            self.draw_horizontal_line(frame_buffer, x + x_pos, y - y_pos, 2 * (-x_pos) + 1, colored);
            e2 = err
            if (e2 <= y_pos):
                y_pos += 1
                err += y_pos * 2 + 1
                if(-x_pos == y_pos and e2 <= x_pos):
                    e2 = 0
            if (e2 > x_pos):
                x_pos  += 1
                err += x_pos * 2 + 1
            if x_pos > 0:
                break

    # to wake call reset() or init()
    def sleep(self):
        self._command(DEEP_SLEEP, b'\xA5')
