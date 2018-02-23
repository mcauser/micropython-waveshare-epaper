# MicroPython library for Waveshare 1.54" B/W/R e-paper display GDEW0154Z04

from micropython import const
from time import sleep_ms
import ustruct

# Display resolution
EPD_WIDTH  = const(200)
EPD_HEIGHT = const(200)

# Display commands
PANEL_SETTING                  = const(0x00) # in datasheet, but not in cmd table
POWER_SETTING                  = const(0x01)
POWER_OFF                      = const(0x02)
#POWER_OFF_SEQUENCE_SETTING     = const(0x03) # not in datasheet
POWER_ON                       = const(0x04)
#POWER_ON_MEASURE               = const(0x05) # not in datasheet
BOOSTER_SOFT_START             = const(0x06)
#DEEP_SLEEP                     = const(0x07) # not in datasheet
DATA_START_TRANSMISSION_1      = const(0x10)
#DATA_STOP                      = const(0x11) # not in datasheet
DISPLAY_REFRESH                = const(0x12)
DATA_START_TRANSMISSION_2      = const(0x13)
VCOM_LUT                       = const(0x20) # VCOM LUT
W2W_LUT                        = const(0x21) # White LUT
B2W_LUT                        = const(0x22) # Black LUT
W2B_LUT                        = const(0x23) # not in datasheet
B2B_LUT                        = const(0x24) # not in datasheet
LUT_RED_0                      = const(0x25) # Red VCOM LUT
LUT_RED_1                      = const(0x26) # Red0 LUT
LUT_RED_2                      = const(0x27) # RED1 LUT
#LUT_RED_3                      = const(0x28) # not in datasheet
PLL_CONTROL                    = const(0x30)
#TEMPERATURE_SENSOR_COMMAND     = const(0x40)
#TEMPERATURE_SENSOR_CALIBRATION = const(0x41)
#TEMPERATURE_SENSOR_WRITE       = const(0x42)
#TEMPERATURE_SENSOR_READ        = const(0x43)
VCOM_AND_DATA_INTERVAL_SETTING = const(0x50)
#LOW_POWER_DETECTION            = const(0x51) # not in datasheet
#TCON_SETTING                   = const(0x60) # not in datasheet
TCON_RESOLUTION                = const(0x61)
#SOURCE_AND_GATE_START_SETTING  = const(0x62) # not in datasheet
#GET_STATUS                     = const(0x71) # in datasheet, but not in cmd table
#AUTO_MEASURE_VCOM              = const(0x80) # not in datasheet
#VCOM_VALUE                     = const(0x81) # not in datasheet
VCM_DC_SETTING_REGISTER        = const(0x82)
#PROGRAM_MODE                   = const(0xA0) # not in datasheet
#ACTIVE_PROGRAM                 = const(0xA1) # not in datasheet
#READ_OTP_DATA                  = const(0xA2) # not in datasheet

# Display orientation
ROTATE_0   = const(0)
ROTATE_90  = const(1)
ROTATE_180 = const(2)
ROTATE_270 = const(3)

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

    LUT_VCOM0 = bytearray(b'\x0E\x14\x01\x0A\x06\x04\x0A\x0A\x0F\x03\x03\x0C\x06\x0A\x00')
    LUT_W     = bytearray(b'\x0E\x14\x01\x0A\x46\x04\x8A\x4A\x0F\x83\x43\x0C\x86\x0A\x04')
    LUT_B     = bytearray(b'\x0E\x14\x01\x8A\x06\x04\x8A\x4A\x0F\x83\x43\x0C\x06\x4A\x04')
    LUT_G1    = bytearray(b'\x8E\x94\x01\x8A\x06\x04\x8A\x4A\x0F\x83\x43\x0C\x06\x0A\x04')
    LUT_G2    = LUT_G1
    LUT_VCOM1 = bytearray(b'\x03\x1D\x01\x01\x08\x23\x37\x37\x01\x00\x00\x00\x00\x00\x00')
    LUT_RED0  = bytearray(b'\x83\x5D\x01\x81\x48\x23\x77\x77\x01\x00\x00\x00\x00\x00\x00')
    LUT_RED1  = LUT_VCOM1

    def _command(self, command, data=None):
        self.dc.low()
        self.cs.low()
        self.spi.write(bytearray([command]))
        self.cs.high()
        if data is not None:
            self._data(data)

    def _data(self, data):
        self.dc.high()
        self.cs.low()
        self.spi.write(data)
        self.cs.high()

    def init(self):
        self.reset()
        self._command(POWER_SETTING, b'\x07\x00\x08\x00')
        self._command(BOOSTER_SOFT_START, b'\x07\x07\x07')
        self._command(POWER_ON)
        self.wait_until_idle()
        self._command(PANEL_SETTING, b'\xCF')
        self._command(VCOM_AND_DATA_INTERVAL_SETTING, b'\x17') # for this panel, must be 0x17
        self._command(PLL_CONTROL, b'\x39')
        self._command(TCON_RESOLUTION, ustruct.pack(">BH", EPD_WIDTH, EPD_HEIGHT))
        self._command(VCM_DC_SETTING_REGISTER, b'\x0E') # -1.4V
        self.set_lut_bw()
        self.set_lut_red()

    def wait_until_idle(self):
        while self.busy.value() == 1:
            sleep_ms(100)

    def reset(self):
        self.rst.low()
        sleep_ms(200)
        self.rst.high()
        sleep_ms(200)

    def set_lut_bw(self):
        self._command(VCOM_LUT, self.LUT_VCOM0) # vcom
        self._command(W2W_LUT, self.LUT_W)      # ww --
        self._command(B2W_LUT, self.LUT_B)      # bw r
        self._command(W2B_LUT, self.LUT_G1)     # wb w
        self._command(B2B_LUT, self.LUT_G2)     # bb b

    def set_lut_red(self):
        self._command(LUT_RED_0, self.LUT_VCOM1)
        self._command(LUT_RED_1, self.LUT_RED0)
        self._command(LUT_RED_2, self.LUT_RED1)

    def display_frame(self, frame_buffer_black, frame_buffer_red):
        if (frame_buffer_black != None):
            self._command(DATA_START_TRANSMISSION_1)
            sleep_ms(2)
            for i in range(0, self.width * self.height // 8):
                temp = 0x00
                for bit in range(0, 4):
                    if (frame_buffer_black[i] & (0x80 >> bit) != 0):
                        temp |= 0xC0 >> (bit * 2)
                self._data(bytearray([temp]))
                temp = 0x00
                for bit in range(4, 8):
                    if (frame_buffer_black[i] & (0x80 >> bit) != 0):
                        temp |= 0xC0 >> ((bit - 4) * 2)
                self._data(bytearray([temp]))
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
            frame_buffer[(x + y * EPD_WIDTH) // 8] &= ~(0x80 >> (x % 8))
        else:
            frame_buffer[(x + y * EPD_WIDTH) // 8] |= 0x80 >> (x % 8)

    def display_string_at(self, frame_buffer, x, y, text, font, colored):
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
            self.draw_horizontal_line(frame_buffer, x + x_pos, y + y_pos, 2 * (-x_pos) + 1, colored)
            self.draw_horizontal_line(frame_buffer, x + x_pos, y - y_pos, 2 * (-x_pos) + 1, colored)
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
        # TODO do we need to reset these here?
        self._command(VCOM_AND_DATA_INTERVAL_SETTING, b'\x17') # for this panel, must be 0x17
        self._command(VCM_DC_SETTING_REGISTER, b'\x00') # to solve Vcom drop
        self._command(POWER_SETTING, b'\x02\x00\x00\x00') # gate switch to external
        # /TODO
        self.wait_until_idle()
        self._command(POWER_OFF)
