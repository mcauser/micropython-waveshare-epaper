"""
MicroPython Waveshare 7.5" Black/White GDEW075T8 e-paper display driver
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
EPD_WIDTH  = const(800)
EPD_HEIGHT = const(480)

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
DATA_START_TRANSMISSION_2      = const(0x13)
DUAL_SPI                       = const(0x15)
#AUTO_SEQUENCE                  = const(0x17)
#KW_LUT_OPTION                  = const(0x2B)
PLL_CONTROL                    = const(0x30)
TEMPERATURE_CALIBRATION        = const(0x40)
#TEMPERATURE_SENSOR_SELECTION   = const(0x41)
#TEMPERATURE_SENSOR_WRITE       = const(0x42)
#TEMPERATURE_SENSOR_READ        = const(0x43)
#PANEL_BREAK_CHECK              = const(0x44)
VCOM_AND_DATA_INTERVAL_SETTING = const(0x50)
#LOW_POWER_DETECTION            = const(0x51)
TCON_SETTING                   = const(0x60)
RESOLUTION_SETTING             = const(0x61)
#GATE_SOURCE_START_SETTING      = const(0x65)
#REVISION                       = const(0x70)
GET_STATUS                     = const(0x71)
#AUTO_MEASUREMENT_VCOM          = const(0x80)
#READ_VCOM_VALUE                = const(0x81)
VCM_DC_SETTING                 = const(0x82)
#PARTIAL_WINDOW                 = const(0x90)
#PARTIAL_IN                     = const(0x91)
#PARTIAL_OUT                    = const(0x92)
#PROGRAM_MODE                   = const(0xA0)
#ACTIVE_PROGRAMMING             = const(0xA1)
#READ_OTP                       = const(0xA2)
#CASCADE_SETTING                = const(0xE0)
#POWER_SAVING                   = const(0xE3)
#LVD_VOLTAGE_SELECT             = const(0xE4)
#FORCE_TEMPERATURE              = const(0xE5)
#TEMPERATURE_BOUNDARY           = const(0xE7)

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

    def _command(self, command):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([command]))
        self.cs(1)

    def _data(self, data):
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([data]))
        self.cs(1)

    def init(self):
        self.reset()

        self._command(POWER_SETTING)
        self._data(0x07) #VGH=20V
        self._data(0x07) #VGL=-20V 
        self._data(0x3f) #VDH=15V
        self._data(0x3f) #VDL=-15V

        self._command(POWER_ON)
        sleep_ms(100)
        self.wait_until_idle()

        self._command(PANEL_SETTING)
        self._data(0x1F)

        self._command(RESOLUTION_SETTING)
        self._data(0x03)
        self._data(0x20)
        self._data(0x01)
        self._data(0xE0)

        self._command(DUAL_SPI)
        self._data(0x00)

        self._command(VCOM_AND_DATA_INTERVAL_SETTING)
        self._data(0x10)
        self._data(0x07)

        self._command(TCON_SETTING)
        self._data(0x22)

    def wait_until_idle(self):
        self._command(GET_STATUS)
        while self.busy.value() == BUSY:
            self._command(GET_STATUS)
        sleep_ms(200)

    def reset(self):
        self.rst(1)
        sleep_ms(200)
        self.rst(0)
        sleep_ms(2)
        self.rst(1)
        sleep_ms(200)

    # draw the current frame memory
    def display_frame(self, frame_buffer):
        self._command(DATA_START_TRANSMISSION_2)
        for i in range(0, self.width * self.height // 8):
            self._data(~frame_buffer[i])

        self._command(DISPLAY_REFRESH)
        sleep_ms(100)
        self.wait_until_idle()

    def clear(self):
        self._command(DATA_START_TRANSMISSION_1)
        for i in range(self.width * self.height // 8):
            self._data(0x00)

        self._command(DATA_START_TRANSMISSION_2)
        for i in range(self.width * self.height // 8):
            self._data(0x00)

        self._command(DISPLAY_REFRESH)
        sleep_ms(100)
        self.wait_until_idle()

    def sleep(self):
        self._command(POWER_OFF)
        self.wait_until_idle()
        self._command(DEEP_SLEEP)
        self._data(0xA5)
        self.rst(0)
        self.dc(0)
