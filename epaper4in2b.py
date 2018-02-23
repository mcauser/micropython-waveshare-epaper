# MicroPython library for Waveshare 4.2" B/W/R e-paper display GDEW042Z15

from micropython import const
from time import sleep_ms

# Display resolution
EPD_WIDTH  = const(400)
EPD_HEIGHT = const(300)

# Display commands
PANEL_SETTING                  = const(0x00)
#POWER_SETTING                  = const(0x01)
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
#VCOM_LUT                       = const(0x20)
#W2W_LUT                        = const(0x21)
#B2W_LUT                        = const(0x22)
#W2B_LUT                        = const(0x23)
#B2B_LUT                        = const(0x24)
#PLL_CONTROL                    = const(0x30)
#TEMPERATURE_SENSOR_CALIBRATION = const(0x40)
#TEMPERATURE_SENSOR_SELECTION   = const(0x41)
#TEMPERATURE_SENSOR_WRITE       = const(0x42)
#TEMPERATURE_SENSOR_READ        = const(0x43)
VCOM_AND_DATA_INTERVAL_SETTING = const(0x50)
#LOW_POWER_DETECTION            = const(0x51)
#TCON_SETTING                   = const(0x60)
#RESOLUTION_SETTING             = const(0x61)
#GSST_SETTING                   = const(0x65)
#GET_STATUS                     = const(0x71)
#AUTO_MEASURE_VCOM              = const(0x80)
#VCOM_VALUE                     = const(0x81)
#VCM_DC_SETTING                 = const(0x82)
#PARTIAL_WINDOW                 = const(0x90)
#PARTIAL_IN                     = const(0x91)
#PARTIAL_OUT                    = const(0x92)
#PROGRAM_MODE                   = const(0xA0)
#ACTIVE_PROGRAM                 = const(0xA1)
#READ_OTP_DATA                  = const(0xA2)
#POWER_SAVING                   = const(0xE3)

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
        self._command(BOOSTER_SOFT_START, b'\x17\x17\x17') # 07 0f 17 1f 27 2F 37 2f
        self._command(POWER_ON)
        self.wait_until_idle()
        self._command(PANEL_SETTING, b'\x0F') # LUT from OTP

    def wait_until_idle(self):
        while self.busy.value() == 1:
            sleep_ms(100)

    def reset(self):
        self.rst.low()
        sleep_ms(200)
        self.rst.high()
        sleep_ms(200)

    # draw the current frame memory
    def display_frame(self, frame_buffer_black, frame_buffer_red):
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

    # to wake call reset() or init()
    def sleep(self):
        self._command(VCOM_AND_DATA_INTERVAL_SETTING, b'\xF7') # border floating
        self._command(POWER_OFF)
        self.wait_until_idle()
        self._command(DEEP_SLEEP, b'\xA5') # check code
