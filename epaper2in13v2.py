"""
MicroPython Waveshare 2.13" V2 Black/White GDEH0213B72/HINK-E0213A22-A0 e-paper display driver
https://github.com/mcauser/micropython-waveshare-epaper
https://www.good-display.com/product/2.13-inch-e-ink-screen-panel-partial-refresh,-GDEH0213B72-218.html

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

# Display resolution in default (portrait) orientation
EPD_WIDTH  = const(128)
EPD_HEIGHT = const(250)
# datasheet says 250x122 (increased to 128 to be multiples of 8)

# Display commands
DRIVER_OUTPUT_CONTROL                = const(0x01)
# Gate Driving Voltage Control       0x03
# Source Driving voltage Control     0x04
BOOSTER_SOFT_START_CONTROL           = const(0x0C) # not in datasheet
#GATE_SCAN_START_POSITION             = const(0x0F) # not in datasheet
DEEP_SLEEP_MODE                      = const(0x10)
DATA_ENTRY_MODE_SETTING              = const(0x11)
SW_RESET                             = const(0x12)
#TEMPERATURE_SENSOR_CONTROL           = const(0x1A)
MASTER_ACTIVATION                    = const(0x20)
#DISPLAY_UPDATE_CONTROL_1             = const(0x21)
DISPLAY_UPDATE_CONTROL_2             = const(0x22)
# Panel Break Detection              0x23
WRITE_RAM                            = const(0x24)
WRITE_RAM_2                          = const(0x26)
WRITE_VCOM_REGISTER                  = const(0x2C)
# Status Bit Read                    0x2F
WRITE_LUT_REGISTER                   = const(0x32)
SET_DUMMY_LINE_PERIOD                = const(0x3A)
SET_GATE_TIME                        = const(0x3B)
BORDER_WAVEFORM_CONTROL              = const(0x3C)
SET_RAM_X_ADDRESS_START_END_POSITION = const(0x44)
SET_RAM_Y_ADDRESS_START_END_POSITION = const(0x45)
SET_RAM_X_ADDRESS_COUNTER            = const(0x4E)
SET_RAM_Y_ADDRESS_COUNTER            = const(0x4F)
TERMINATE_FRAME_READ_WRITE           = const(0xFF) # not in datasheet, aka NOOP

BUSY = const(1)  # 1=busy, 0=idle

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
        self.update = -1    # Not initialised yet

    FULL_UPDATE = 0
    PART_UPDATE = 1
    LUT_FULL_UPDATE    = bytearray(b'\x80\x60\x40\x00\x00\x00\x00\x10\x60\x20\x00\x00\x00\x00\x80\x60\x40\x00\x00\x00\x00\x10\x60\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x03\x00\x00\x02\x09\x09\x00\x00\x02\x03\x03\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    LUT_PARTIAL_UPDATE = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

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

    def init(self, update):
        # update = FULL_UPDATE/PART_UPDATE
        self.update = update    # store full/partial update for use in set_frame_memory()

        self.reset()
        self.wait_until_idle()

        if(update == self.FULL_UPDATE):
            self._command(SW_RESET) # soft reset
            self.wait_until_idle()

            self._command(0x74, b'\x54') #set analog block control
            self._command(0x7E, b'\x3B') #set digital block control

            self._command(DRIVER_OUTPUT_CONTROL) #Driver output control
            self._data(bytearray([(EPD_HEIGHT - 1) & 0xFF]))
            self._data(bytearray([((EPD_HEIGHT - 1) >> 8) & 0xFF]))
            self._data(bytearray([0x00])) # GD = 0 SM = 0 TB = 0

            self._command(DATA_ENTRY_MODE_SETTING, b'\x01') #data entry mode. X+, Y- from bottom left in landscape

            self._command(BORDER_WAVEFORM_CONTROL, b'\x03') #BorderWavefrom

            self._command(WRITE_VCOM_REGISTER, b'\x55')     #VCOM Voltage

            self._command(0x03, b'\x15') # Gate Driving Voltage Control

            self._command(0x04, b'\x41\xA8\x32') # Source Driving voltage Control

            self._command(SET_DUMMY_LINE_PERIOD, b'\x30')     #Dummy Line
            self._command(SET_GATE_TIME, b'\x0A')     #Gate time

            self.set_lut(self.LUT_FULL_UPDATE)
        else:
            self._command(WRITE_VCOM_REGISTER, b'\x26')
            self.wait_until_idle()

            self.set_lut(self.LUT_PARTIAL_UPDATE)

            self._command(0x37, b'\x00\x00\x00\x00\x40\x00\x00')

            self._command(DISPLAY_UPDATE_CONTROL_2, b'\xC0')
            self._command(MASTER_ACTIVATION)
            self.wait_until_idle()

            self._command(BORDER_WAVEFORM_CONTROL, b'\x01')
            
    def wait_until_idle(self):
        while self.busy.value() == BUSY:
            sleep_ms(100)
      
    def reset(self):
        self.rst(0)
        sleep_ms(200)
        self.rst(1)
        sleep_ms(200)

    def set_lut(self, lut):
        self._command(WRITE_LUT_REGISTER, lut)

    # put an image in the frame memory
    def set_frame_memory(self, image, x, y, w, h):
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        x = x & 0xF8
        w = w & 0xF8

        if (x + w >= self.width):
            x_end = self.width - 1
        else:
            x_end = x + w - 1

        if (y + h >= self.height):
            y_end = self.height - 1
        else:
            y_end = y + h - 1

        # The controller for this display appears to step through y axis "backwards" hence the flipping of y(_start) and y_end.
        self.set_memory_area(x, y_end, x_end, y)
        # Similarly, the memory pointer needs y_end
        self.set_memory_pointer(x, y_end)
        if (self.update == self.FULL_UPDATE):
            self.display_landscape(image, WRITE_RAM,w,h)
        else:
            self.display_landscape(image, WRITE_RAM,w,h)
            self.display_landscape(image, WRITE_RAM_2,w,h)


    def display_landscape(self,buf,write_cmd,w,h):
        # Display in Landscape.
        # To do a partial update:
        # epd.display_landscape(buf,WRITE_RAM)
        # epd.display_landscape(buf,WRITE_RAM_2)
        # adapted from https://github.com/peterhinch/micropython-nano-gui/blob/master/drivers/epaper/epd29.py
        # ram starts at bottom right corner, proceding up in 8 pixel (byte) columns then left in 1 pixel rows
        buf1 = bytearray(1)
        mvb = memoryview(buf)
        cmd = self._command
        dat = self._data
        wid = h
        tbc = w // 8  # Vertical bytes per column
        iidx = wid * tbc - 1 # start at the end of the buffer
        #iidx -= wid #skip bottom 8 lines
        idx = iidx  # Index into framebuf
        vbc = 0  # Current vertical byte count
        hpc = 0  # Horizontal pixel count
        cmd(write_cmd)
        for i in range(wid * tbc):
            if (write_cmd == WRITE_RAM):
                buf1[0] = ~mvb[idx]
            else:
                buf1[0] = mvb[idx]  # GDEH0213B72 docs says RAM_2 is for red colour but it appears to need to be set to inverse of RAM_1 for partial update to work
            dat(buf1)
            idx -= wid    # up one line
            vbc += 1
            vbc %= tbc
            if not vbc:
                hpc += 1
                idx = iidx - hpc # left one column

    # replace the frame memory with the specified color
    def clear_frame_memory(self, color):
        self.set_memory_area(0, self.height-1, self.width-1, 0)
        self.set_memory_pointer(0, self.height-1)
        self._command(WRITE_RAM)
        # send the color data
        for i in range(0, self.width // 8 * self.height):
            self._data(bytearray([color]))

    # draw the current frame memory and switch to the next memory area
    def display_frame(self):
        self._command(DISPLAY_UPDATE_CONTROL_2, b'\xC7')
        self._command(MASTER_ACTIVATION)
        self._command(TERMINATE_FRAME_READ_WRITE)
        self.wait_until_idle()

    # specify the memory area for data R/W
    def set_memory_area(self, x_start, y_start, x_end, y_end):
        self._command(SET_RAM_X_ADDRESS_START_END_POSITION)
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self._data(bytearray([(x_start >> 3) & 0xFF]))
        self._data(bytearray([(x_end >> 3) & 0xFF]))
        self._command(SET_RAM_Y_ADDRESS_START_END_POSITION, ustruct.pack("<HH", y_start, y_end))

    # specify the start point for data R/W
    def set_memory_pointer(self, x, y):
        self._command(SET_RAM_X_ADDRESS_COUNTER)
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self._data(bytearray([(x >> 3) & 0xFF]))
        self._command(SET_RAM_Y_ADDRESS_COUNTER, ustruct.pack("<H", y))
        self.wait_until_idle()

    # to wake call reset() or init()
    def sleep(self):
        self._command(DISPLAY_UPDATE_CONTROL_2, b'\xC3')
        self._command(MASTER_ACTIVATION)

        self._command(DEEP_SLEEP_MODE,b'\x01')
        self.wait_until_idle()

