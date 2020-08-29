"""
MicroPython Waveshare 2.13" Black/White V2 e-paper display driver
https://github.com/mcauser/micropython-waveshare-epaper

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
import ustruct
from time import sleep_ms
from machine import Pin

# Display resolution
EPD_WIDTH       = 122
EPD_HEIGHT      = 250
# datasheet says 250x122 (increased to 128 to be multiples of 8)

# Display commands
DRIVER_OUTPUT_CONTROL                = const(0x01)
GATE_DRV_VOLTAGE_CTRL                = const(0x03)
SRC_DRV_VOLTAGE_CTRL                 = const(0x04)
DEEP_SLEEP_MODE                      = const(0x10)
DATA_ENTRY_MODE_SETTING              = const(0x11)
SW_RESET                             = const(0x12)
MASTER_ACTIVATION                    = const(0x20)
DISPLAY_UPDATE_CONTROL_2             = const(0x22)
WRITE_RAM                            = const(0x24)
WRITE_VCOM_REGISTER                  = const(0x2C)
WRITE_LUT_REGISTER                   = const(0x32)
SET_DUMMY_LINE_PERIOD                = const(0x3A)
SET_GATE_LINE_WIDTH                  = const(0x3B)
BORDER_WAVEFORM_CONTROL              = const(0x3C)
SET_RAM_X_ADDRESS_START_END_POSITION = const(0x44)
SET_RAM_Y_ADDRESS_START_END_POSITION = const(0x45)
SET_RAM_X_ADDRESS_COUNTER            = const(0x4E)
SET_RAM_Y_ADDRESS_COUNTER            = const(0x4F)
SET_ANALOG_CTRL                      = const(0x74)
SET_DIGITAL_CTRL                     = const(0x7E)

X_DECR_Y_DECR                        = const(0x00)
X_INCR_Y_DECR                        = const(0x01)
X_DECR_Y_INCR                        = const(0x01)
X_INCR_Y_INCR                        = const(0x03)

X_DIR                                = const(0x00)
Y_DIR                                = const(0x04)

SLEEP_NORMAL                         = const(0x00) #Sleeps and keeps access to RAM and controller
SLEEP_MODE_1                         = const(0x01) #Sleeps without access to RAM/controller but keeps RAM content
SLEEP_MODE_2                         = const(0x11) #Same as MODE_1 but RAM content is not kept

class EPD:
    def __init__(self, spi, cs, dc, rst, busy):
        self.spi = spi
        self.dc = dc
        self.busy = busy
        self.rst = rst
        self.cs = cs
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        self.sleep_mode = SLEEP_MODE_1

        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=0)
        self.busy.init(self.busy.IN)


    FULL_UPDATE = 0
    PART_UPDATE = 1

    lut_full_update= [
        0x80,0x60,0x40,0x00,0x00,0x00,0x00,             #LUT0: BB:     VS 0 ~7
        0x10,0x60,0x20,0x00,0x00,0x00,0x00,             #LUT1: BW:     VS 0 ~7
        0x80,0x60,0x40,0x00,0x00,0x00,0x00,             #LUT2: WB:     VS 0 ~7
        0x10,0x60,0x20,0x00,0x00,0x00,0x00,             #LUT3: WW:     VS 0 ~7
        0x00,0x00,0x00,0x00,0x00,0x00,0x00,             #LUT4: VCOM:   VS 0 ~7

        0x03,0x03,0x00,0x00,0x02,                       # TP0 A~D RP0
        0x09,0x09,0x00,0x00,0x02,                       # TP1 A~D RP1
        0x03,0x03,0x00,0x00,0x02,                       # TP2 A~D RP2
        0x00,0x00,0x00,0x00,0x00,                       # TP3 A~D RP3
        0x00,0x00,0x00,0x00,0x00,                       # TP4 A~D RP4
        0x00,0x00,0x00,0x00,0x00,                       # TP5 A~D RP5
        0x00,0x00,0x00,0x00,0x00,                       # TP6 A~D RP6

        0x15,0x41,0xA8,0x32,0x30,0x0A,
    ]

    lut_partial_update = [ #20 bytes
        0x00,0x00,0x00,0x00,0x00,0x00,0x00,             #LUT0: BB:     VS 0 ~7
        0x80,0x00,0x00,0x00,0x00,0x00,0x00,             #LUT1: BW:     VS 0 ~7
        0x40,0x00,0x00,0x00,0x00,0x00,0x00,             #LUT2: WB:     VS 0 ~7
        0x00,0x00,0x00,0x00,0x00,0x00,0x00,             #LUT3: WW:     VS 0 ~7
        0x00,0x00,0x00,0x00,0x00,0x00,0x00,             #LUT4: VCOM:   VS 0 ~7

        0x0A,0x00,0x00,0x00,0x00,                       # TP0 A~D RP0
        0x00,0x00,0x00,0x00,0x00,                       # TP1 A~D RP1
        0x00,0x00,0x00,0x00,0x00,                       # TP2 A~D RP2
        0x00,0x00,0x00,0x00,0x00,                       # TP3 A~D RP3
        0x00,0x00,0x00,0x00,0x00,                       # TP4 A~D RP4
        0x00,0x00,0x00,0x00,0x00,                       # TP5 A~D RP5
        0x00,0x00,0x00,0x00,0x00,                       # TP6 A~D RP6

        0x15,0x41,0xA8,0x32,0x30,0x0A,
    ]

    # Hardware reset
    def reset_display(self):
        self.rst(1)
        sleep_ms(200)
        self.rst(0)
        sleep_ms(10)
        self.rst(1)
        sleep_ms(200)

    def send_command(self, command, data=None):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([command]))
        self.cs(1)
        if data is not None:
            self.send_data(data)

    def send_data(self, data):
        self.dc(1)
        self.cs(0)
        self.spi.write(data)
        self.cs(1)

    def set_lut(self, lut):
        self.send_command(WRITE_LUT_REGISTER, bytearray(lut[:70]))

    def wait_display(self):
        while self.busy.value() == 1 :
            sleep_ms(100)

    def update_display(self):
        self.send_command(DISPLAY_UPDATE_CONTROL_2, b'\xc7')
        self.send_command(MASTER_ACTIVATION)
        self.wait_display()

    def update_display_partial(self):
        self.send_command(DISPLAY_UPDATE_CONTROL_2, b'\x0c')
        self.send_command(MASTER_ACTIVATION)
        self.wait_display()

    def init(self, update):
        # EPD hardware init start
        self.reset_display()
        if (update == self.FULL_UPDATE):
            self.wait_display()
            self.send_command(SW_RESET) # soft reset
            self.wait_display()

            self.send_command(SET_ANALOG_CTRL, b'\x54') #set analog block control
            self.send_command(SET_DIGITAL_CTRL, b'\x3b') #set digital block control

            self.send_command(DRIVER_OUTPUT_CONTROL)
            self.send_data(bytearray([(self.height - 1) & 0xFF]))
            self.send_data(bytearray([((self.height - 1) >> 8) & 0xFF]))
            self.send_data(bytearray([0x00])) # GD = 0 SM = 0 TB = 0

            self.send_command(DATA_ENTRY_MODE_SETTING, bytearray([X_INCR_Y_INCR | X_DIR])) #data entry mode

            self.send_command(BORDER_WAVEFORM_CONTROL, b'\x03') #BorderWavefrom

            self.send_command(WRITE_VCOM_REGISTER, b'\x55')     #VCOM Voltage

            self.send_command(GATE_DRV_VOLTAGE_CTRL)
            self.send_data(bytearray([self.lut_full_update[70]]))

            self.send_command(SRC_DRV_VOLTAGE_CTRL) 
            self.send_data(bytearray([self.lut_full_update[71]]))
            self.send_data(bytearray([self.lut_full_update[72]]))
            self.send_data(bytearray([self.lut_full_update[73]]))

            self.send_command(SET_DUMMY_LINE_PERIOD)     #Dummy Line
            self.send_data(bytearray([self.lut_full_update[74]]))
            self.send_command(SET_GATE_LINE_WIDTH)     #Gate time
            self.send_data(bytearray([self.lut_full_update[75]]))
            self.set_lut(self.lut_full_update)

            self.wait_display()
        else:
            self.send_command(WRITE_VCOM_REGISTER, b'\x26')     #VCOM Voltage
            self.wait_display()

            self.set_lut(self.lut_partial_update)

            self.send_command(0x37, b'\x00\x00\x00\x00\x40\x00\x00')
            self.send_command(DISPLAY_UPDATE_CONTROL_2, b'\xc0')
            self.send_command(MASTER_ACTIVATION)
            self.wait_display()

            self.send_command(BORDER_WAVEFORM_CONTROL, b'\x01') #BorderWavefrom
        return 0

    # specify the memory area for data R/W
    def set_memory_area(self, x0, y0, xw, yh):
          self.send_command(SET_RAM_X_ADDRESS_START_END_POSITION, bytearray([(x0 >> 3) & 0xff, (xw >>3) & 0xff]))
          self.send_command(SET_RAM_Y_ADDRESS_START_END_POSITION, ustruct.pack("<HH", y0, yh))

    # specify the start point for data R/W
    def set_memory_pointer(self, x, y):
        self.send_command(SET_RAM_X_ADDRESS_COUNTER)
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self.send_data(bytearray([(x >> 3) & 0xFF]))
        self.send_command(SET_RAM_Y_ADDRESS_COUNTER, ustruct.pack("<H", y))
        self.wait_display()

    def display(self, image):
        print("Display buffer")
        if self.width % 8 == 0:
            linewidth = self.width / 8
        else:
            linewidth = self.width // 8 + 1
        self.set_memory_area(0, 0, self.width - 1 , self.height - 1)
        self.set_memory_pointer(0, 0)
        self.send_command(WRITE_RAM)
        for i in range(0, self.height * self.width // 8):
            self.send_data(bytearray([image[i]]))
        self.update_display()

    def display_partial(self, image):
        if self.width % 8 == 0:
            linewidth = self.width / 8
        else:
            linewidth = self.width // 8 + 1

        self.send_command(WRITE_RAM)
        for j in range(0, self.height):
            for i in range(0, linewidth):
                self.send_data(bytearray([image[i + (j * linewidth)]]))

        # self.send_command(0x26)
        # for j in range(0, self.height):
            # for i in range(0, linewidth):
                # self.send_data(~image[i + j * linewidth])
        self.update_display_partial()

    def displayPartBaseImage(self, image):
        if self.width % 8 == 0:
            linewidth = self.width / 8
        else:
            linewidth = self.width // 8 + 1

        self.send_command(WRITE_RAM)
        for j in range(0, self.height):
            for i in range(0, linewidth):
                self.send_data(bytearray([image[i + j * linewidth]]))


        self.send_command(0x26)
        for j in range(0, self.height):
            for i in range(0, linewidth):
                self.send_data(bytearray([image[i + j * linewidth]]))
        self.update_display()

    def clear_display(self, color):
        print("Clear display")
        if self.width % 8 == 0:
            linewidth = self.width / 8
        else:
            linewidth = self.width // 8 + 1

        self.send_command(WRITE_RAM)
        for j in range(0, self.height * linewidth // 8):
                self.send_data(bytearray([color]))
        self.update_display()

    def set_sleep_mode(self, mode):
        self.sleep_mode = mode

    def sleep(self):
        print("Going into sleep %d" % self.sleep_mode)
        self.wait_display()
        self.send_command(DISPLAY_UPDATE_CONTROL_2, b'\xc3') #POWER OFF
        self.send_command(MASTER_ACTIVATION)

        self.send_command(DEEP_SLEEP_MODE, bytearray([self.sleep_mode]))
        sleep_ms(100)
        self.rst(0)

    def wakeup(self):
        print("wakeup")
        self.init()
### END OF FILE ###


