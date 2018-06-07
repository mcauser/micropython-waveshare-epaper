"""
MicroPython Waveshare 4.2" Black/White GDEW042T2 e-paper display driver
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
EPD_WIDTH  = const(400)
EPD_HEIGHT = const(300)

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
LUT_FOR_VCOM                   = const(0x20)
LUT_WHITE_TO_WHITE             = const(0x21)
LUT_BLACK_TO_WHITE             = const(0x22)
LUT_WHITE_TO_BLACK             = const(0x23)
LUT_BLACK_TO_BLACK             = const(0x24)
PLL_CONTROL                    = const(0x30)
#TEMPERATURE_SENSOR_COMMAND     = const(0x40)
#TEMPERATURE_SENSOR_SELECTION   = const(0x41)
#TEMPERATURE_SENSOR_WRITE       = const(0x42)
#TEMPERATURE_SENSOR_READ        = const(0x43)
VCOM_AND_DATA_INTERVAL_SETTING = const(0x50)
#LOW_POWER_DETECTION            = const(0x51)
#TCON_SETTING                   = const(0x60)
RESOLUTION_SETTING             = const(0x61)
#GSST_SETTING                   = const(0x65)
#GET_STATUS                     = const(0x71)
#AUTO_MEASUREMENT_VCOM          = const(0x80)
#READ_VCOM_VALUE                = const(0x81)
VCM_DC_SETTING                 = const(0x82)
#PARTIAL_WINDOW                 = const(0x90)
#PARTIAL_IN                     = const(0x91)
#PARTIAL_OUT                    = const(0x92)

#PROGRAM_MODE                   = const(0xA0)
#ACTIVE_PROGRAMMING             = const(0xA1)
#READ_OTP                       = const(0xA2)
#POWER_SAVING                   = const(0xE3)

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

    # 44/42 bytes (look up tables)
    LUT_VCOM0 = bytearray(b'\x00\x17\x00\x00\x00\x02\x00\x17\x17\x00\x00\x02\x00\x0A\x01\x00\x00\x01\x00\x0E\x0E\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    LUT_WW    = bytearray(b'\x40\x17\x00\x00\x00\x02\x90\x17\x17\x00\x00\x02\x40\x0A\x01\x00\x00\x01\xA0\x0E\x0E\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    LUT_BW    = LUT_WW
    LUT_BB    = bytearray(b'\x80\x17\x00\x00\x00\x02\x90\x17\x17\x00\x00\x02\x80\x0A\x01\x00\x00\x01\x50\x0E\x0E\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    LUT_WB    = LUT_BB

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
        self._command(POWER_SETTING, b'\x03\x00\x2B\x2B\xFF') # VDS_EN VDG_EN, VCOM_HV VGHL_LV[1] VGHL_LV[0], VDH, VDL, VDHR
        self._command(BOOSTER_SOFT_START, b'\x17\x17\x17') # 07 0f 17 1f 27 2F 37 2f
        self._command(POWER_ON)
        self.wait_until_idle()
        self._command(PANEL_SETTING, b'\xBF\x0B') # KW-BF   KWR-AF  BWROTP 0f
        self._command(PLL_CONTROL, b'\x3C') # 3A 100HZ   29 150Hz 39 200HZ  31 171HZ

    def wait_until_idle(self):
        while self.busy.value() == BUSY:
            sleep_ms(100)

    def reset(self):
        self.rst(0)
        sleep_ms(200)
        self.rst(1)
        sleep_ms(200)

    def set_lut(self):
        self._command(LUT_FOR_VCOM, self.LUT_VCOM0)    # vcom
        self._command(LUT_WHITE_TO_WHITE, self.LUT_WW) # ww --
        self._command(LUT_BLACK_TO_WHITE, self.LUT_BW) # bw r
        self._command(LUT_WHITE_TO_BLACK, self.LUT_BB) # wb w
        self._command(LUT_BLACK_TO_BLACK, self.LUT_WB) # bb b

    # draw the current frame memory
    def display_frame(self, frame_buffer):
        self._command(RESOLUTION_SETTING, ustruct.pack(">HH", EPD_WIDTH, EPD_HEIGHT))
        self._command(VCM_DC_SETTING, b'\x12')
        self._command(VCOM_AND_DATA_INTERVAL_SETTING)
        self._command(0x97) # VBDF 17|D7 VBDW 97  VBDB 57  VBDF F7  VBDW 77  VBDB 37  VBDR B7
        # TODO should ^ this be _data(0x97), not sure what it does

        if (frame_buffer != None):
            self._command(DATA_START_TRANSMISSION_1)
            for i in range(0, self.width * self.height // 8):
                self._data(bytearray([0xFF])) # bit set: white, bit reset: black
            sleep_ms(2)
            self._command(DATA_START_TRANSMISSION_2)
            for i in range(0, self.width * self.height // 8):
                self._data(bytearray([frame_buffer[i]]))
            sleep_ms(2)

        self.set_lut()
        self._command(DISPLAY_REFRESH)
        sleep_ms(100)
        self.wait_until_idle()

    # to wake call reset() or init()
    def sleep(self):
        self._command(VCOM_AND_DATA_INTERVAL_SETTING, b'\x17') # border floating
        self._command(VCM_DC_SETTING) # VCOM to 0V
        self._command(PANEL_SETTING)
        sleep_ms(100)
        self._command(POWER_SETTING, b'\x00\x00\x00\x00\x00') # VG&VS to 0V fast
        sleep_ms(100)
        self._command(POWER_OFF)
        self.wait_until_idle()
        self._command(DEEP_SLEEP, b'\xA5')
