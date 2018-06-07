"""
MicroPython Waveshare 5.83" Black/White/Red GDEW0583Z21 e-paper display driver
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

from micropython import const
from time import sleep_ms
import ustruct

# Display resolution
EPD_WIDTH  = const(600)
EPD_HEIGHT = const(448)

# Display commands
PANEL_SETTING                  = const(0x00)
POWER_SETTING                  = const(0x01)
POWER_OFF                      = const(0x02)
#POWER_OFF_SEQUENCE_SETTING     = const(0x03)
POWER_ON                       = const(0x04)
#POWER_ON_MEASURE               = const(0x05)
BOOSTER_SOFT_START             = const(0x06)
DEEP_SLEEP                     = const(0x07)
DATA_START_TRANSMISSION_1      = const(0x10)
#DATA_STOP                      = const(0x11)
DISPLAY_REFRESH                = const(0x12)
#IMAGE_PROCESS                  = const(0x13)
#LUT_FOR_VCOM                   = const(0x20)
#LUT_BLUE                       = const(0x21)
#LUT_WHITE                      = const(0x22)
#LUT_GRAY_1                     = const(0x23)
#LUT_GRAY_2                     = const(0x24)
#LUT_RED_0                      = const(0x25)
#LUT_RED_1                      = const(0x26)
#LUT_RED_2                      = const(0x27)
#LUT_RED_3                      = const(0x28)
#LUT_XON                        = const(0x29)
PLL_CONTROL                    = const(0x30)
#TEMPERATURE_SENSOR_COMMAND     = const(0x40)
TEMPERATURE_CALIBRATION        = const(0x41)
#TEMPERATURE_SENSOR_WRITE       = const(0x42)
#TEMPERATURE_SENSOR_READ        = const(0x43)
VCOM_AND_DATA_INTERVAL_SETTING = const(0x50)
#LOW_POWER_DETECTION            = const(0x51)
TCON_SETTING                   = const(0x60)
TCON_RESOLUTION                = const(0x61)
#SPI_FLASH_CONTROL              = const(0x65)
#REVISION                       = const(0x70)
#GET_STATUS                     = const(0x71)
#AUTO_MEASUREMENT_VCOM          = const(0x80)
#READ_VCOM_VALUE                = const(0x81)
VCM_DC_SETTING                 = const(0x82)
FLASH_MODE                     = const(0xE5)

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
        self._command(POWER_SETTING, b'\x37\x00')
        self._command(PANEL_SETTING, b'\xCF\x08')
        self._command(BOOSTER_SOFT_START, b'\xC7\xCC\x28')
        self._command(POWER_ON)
        self.wait_until_idle()
        self._command(PLL_CONTROL, b'\x3C')
        self._command(TEMPERATURE_CALIBRATION, b'\x00')
        self._command(VCOM_AND_DATA_INTERVAL_SETTING, b'\x77')
        self._command(TCON_SETTING, b'\x22')
        self._command(TCON_RESOLUTION, ustruct.pack(">HH", EPD_WIDTH, EPD_HEIGHT))
        self._command(VCM_DC_SETTING, b'\x20') # decide by LUT file
        self._command(FLASH_MODE, b'\x03')

    def wait_until_idle(self):
        while self.busy.value() == BUSY:
            sleep_ms(100)

    def reset(self):
        self.rst.low()
        sleep_ms(200)
        self.rst.high()
        sleep_ms(200)

    # draw the current frame memory
    def display_frame(self, frame_buffer_black, frame_buffer_red):
        if (frame_buffer != None and frame_buffer_red != None):
            self._command(DATA_START_TRANSMISSION_1)
            for i in range(0, self.width * self.height // 8):
                temp1 = frame_buffer_black[i]
                temp2 = frame_buffer_red[i]
                j = 0
                while (j < 8):
                    if ((temp2 & 0x80) == 0x00):
                        temp3 = 0x04                #red
                    elif ((temp1 & 0x80) == 0x00):
                        temp3 = 0x00                #black
                    else:
                        temp3 = 0x03                #white

                    temp3 = (temp3 << 4) & 0xFF
                    temp1 = (temp1 << 1) & 0xFF
                    temp2 = (temp2 << 1) & 0xFF
                    j += 1
                    if ((temp2 & 0x80) == 0x00):
                        temp3 |= 0x04              #red
                    elif ((temp1 & 0x80) == 0x00):
                        temp3 |= 0x00              #black
                    else:
                        temp3 |= 0x03              #white
                    temp1 = (temp1 << 1) & 0xFF
                    temp2 = (temp2 << 1) & 0xFF
                    self._data(bytearray([temp3]))
                    j += 1
        self._command(DISPLAY_REFRESH)
        sleep_ms(100)
        self.wait_until_idle()

    # to wake call reset() or init()
    def sleep(self):
        self._command(POWER_OFF)
        self.wait_until_idle()
        self._command(DEEP_SLEEP, b'\xA5')
