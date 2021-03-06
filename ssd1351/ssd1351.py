 # -*- coding: utf-8 -*-

#----------------------------------------------------------------------
# ssd1351.py from https://github.com/saidalvarado/ssd1351
# ported by Said Alvarado
#
# This library works with
#   Adafruit's 128x128 SPI RGB OLED   https://www.adafruit.com/products/1431
#
# The code is based heavily on Adafruit's Arduino library
#   https://github.com/adafruit/Adafruit-SSD1351-library
# written by Limor Fried/Ladyada for Adafruit Industries.
#
# And also adapted from de py-gaugette library for python
#   https://github.com/guyc/py-gaugette
#
# Some important things to know about this device and SPI:
#
# SPI and GPIO calls are made through an abstraction library that calls
# the appropriate library for the platform.
# For the RaspberryPi:
#     wiring2
#     spidev
#
# It requires  Numpy (version >= 1.92) to speed up some of the image processing
#
#----------------------------------------------------------------------


import numpy as np
import time
# Imports for GPIO manipulation
import spidev
import wiringpi2
# This is the file with the text font
import glcdfont





# Class definition intended for GPIO manipulation.
class GPIO:
    def __init__(self):
        self.gpio = wiringpi2.GPIO(wiringpi2.GPIO.WPI_MODE_PINS)
        self.setup = self.wiringpi2_setup
        self.output = self.gpio.digitalWrite
        self.input = self.gpio.digitalRead
        self.OUT = self.gpio.OUTPUT
        self.IN = self.gpio.INPUT
        self.HIGH = self.gpio.HIGH
        self.LOW = self.gpio.LOW
        self.PUD_UP = self.gpio.PUD_UP
        self.PUD_DOWN = self.gpio.PUD_DOWN
        self.PUD_OFF = self.gpio.PUD_OFF

    def wiringpi2_setup(self, channel, direction, pull_up_down=None):
        self.gpio.pinMode(channel, direction)
        if pull_up_down is None: pull_up_down = self.gpio.PUD_OFF
        self.gpio.pullUpDnControl(channel, pull_up_down)






class SSD1351:

    # DELAYS_HWFILL = 3
    # DELAYS_HWLINE = 1

    # Colors
    BLACK         =  0x0000
    BLUE          =  0x001F
    RED           =  0xF800
    GREEN         =  0x07E0
    CYAN          =  0x07FF
    MAGENTA       =  0xF81F
    YELLOW        =  0xFFE0
    WHITE         =  0xFFFF




    # SSD1351 Commands
    CMD_SETCOLUMN          = 0x15
    CMD_SETROW             = 0x75
    CMD_WRITERAM           = 0x5C
    CMD_READRAM            = 0x5D
    CMD_SETREMAP           = 0xA0
    CMD_STARTLINE          = 0xA1
    CMD_DISPLAYOFFSET      = 0xA2
    CMD_DISPLAYALLOFF      = 0xA4
    CMD_DISPLAYALLON       = 0xA5
    CMD_NORMALDISPLAY      = 0xA6
    CMD_INVERTDISPLAY      = 0xA7
    CMD_FUNCTIONSELECT     = 0xAB
    CMD_DISPLAYOFF         = 0xAE
    CMD_DISPLAYON          = 0xAF
    CMD_PRECHARGE          = 0xB1
    CMD_DISPLAYENHANCE     = 0xB2
    CMD_CLOCKDIV           = 0xB3
    CMD_SETVSL             = 0xB4
    CMD_SETGPIO            = 0xB5
    CMD_PRECHARGE2         = 0xB6
    CMD_SETGRAY            = 0xB8
    CMD_USELUT             = 0xB9
    CMD_PRECHARGELEVEL     = 0xBB
    CMD_VCOMH              = 0xBE
    CMD_CONTRASTABC        = 0xC1
    CMD_CONTRASTMASTER     = 0xC7
    CMD_MUXRATIO           = 0xCA
    CMD_COMMANDLOCK        = 0xFD
    CMD_HORIZSCROLL        = 0x96
    CMD_STOPSCROLL         = 0x9E
    CMD_STARTSCROLL        = 0x9F

    SSD1351WIDTH           = 128
    SSD1351HEIGHT           = 128





    # Device name will be /dev/spidev-{bus}.{device}
    # dc_pin is the data/commmand pin.  This line is HIGH for data, LOW for command.
    # We will keep d/c low and bump it high only for commands with data
    # reset is normally HIGH, and pulled LOW to reset the display

    def __init__(self, bus=0, device=0, dc_pin=3, reset_pin=2, rows=128, cols=128, spiBufferSize = 4096):
        # Display size
        self.cols = cols
        self.rows = rows
        # Pins assigment
        self.dc_pin = dc_pin
        self.reset_pin = reset_pin
        # SPI port configuration
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = 16000000 #We set the bus to 16Mhz
        self.spi.mode = 3 # necessary!
        self.spi_buffer_size = spiBufferSize
        # GPIO port configuration. (The defition is at the start of the code)
        self.gpio = GPIO()
        self.gpio.setup(self.reset_pin, self.gpio.OUT)
        self.gpio.output(self.reset_pin, self.gpio.HIGH)
        self.gpio.setup(self.dc_pin, self.gpio.OUT)
        self.gpio.output(self.dc_pin, self.gpio.LOW)
        # Load de font
        self.font = np.asarray(glcdfont.font5x8,dtype = np.uint8)    #We make a copy
        self.font_size_x = glcdfont.x_size
        self.font_size_y = glcdfont.y_size
        self.cursor_x = 0
        self.cursor_y = 0
        #Frame buffer for speed optimization
        self.frame_buffer = np.full((rows,cols),0,dtype=np.uint16)
        #Toogle switch for speed optimization
        self.optimization = False #Becomes True in the begin() function


    # Reset display
    def reset(self):
        self.gpio.output(self.reset_pin, self.gpio.LOW)
        time.sleep(0.010) # 10ms
        self.gpio.output(self.reset_pin, self.gpio.HIGH)

    # Use the SPI bus to send a command to the display
    def writeCommand(self, command):

        #By default, the DC pin is always LOW
        self.spi.writebytes([command])


    # Use the SPI bus to send data to the display (following a command)
    def writeData(self, command):

        if type(command) != list:
            command = [command]

        # DC pin  <-- HIGH
        self.gpio.output(self.dc_pin, self.gpio.HIGH)
        # write data
        self.spi.writebytes(command)
        # DC pin  <-- LOW
        self.gpio.output(self.dc_pin, self.gpio.LOW)



    #Initialization sequence for the display
    def begin(self):
        time.sleep(0.001) # 1ms
        self.reset()

        self.writeCommand(self.CMD_COMMANDLOCK)   # set command lock
        self.writeData(0x12)

        self.writeCommand(self.CMD_COMMANDLOCK)   # set command lock
        self.writeData(0xB1)

        self.writeCommand(self.CMD_DISPLAYOFF)        # 0xAE

        self.writeCommand(self.CMD_CLOCKDIV)          # 0xB3
        self.writeCommand(0xF1)                          # 7:4 = Oscillator Frequency, 3:0 = CLK Div Ratio (A[3:0]+1 = 1..16)

        self.writeCommand(self.CMD_MUXRATIO)
        self.writeData(127)

        self.writeCommand(self.CMD_SETREMAP)
        self.writeData(0x74)

        self.writeCommand(self.CMD_SETCOLUMN)
        self.writeData(0x00)
        self.writeData(0x7F)

        self.writeCommand(self.CMD_SETROW)
        self.writeData(0x00)
        self.writeData(0x7F)

        self.writeCommand(self.CMD_STARTLINE)         # 0xA1
        self.writeData(0)

        self.writeCommand(self.CMD_DISPLAYOFFSET)     # 0xA2
        self.writeData(0x0)

        self.writeCommand(self.CMD_SETGPIO)
        self.writeData(0x00)

        self.writeCommand(self.CMD_FUNCTIONSELECT)
        self.writeData(0x01)  # internal (diode drop)

        self.writeCommand(self.CMD_PRECHARGE)        # 0xB1
        self.writeCommand(0x32)

        self.writeCommand(self.CMD_VCOMH)             #0xBE
        self.writeCommand(0x05)

        self.writeCommand(self.CMD_NORMALDISPLAY)     # 0xA6

        self.writeCommand(self.CMD_CONTRASTABC)
        self.writeData(0xC8)
        self.writeData(0x80)
        self.writeData(0xC8)

        self.writeCommand(self.CMD_CONTRASTMASTER)
        self.writeData(0x0F)

        self.writeCommand(self.CMD_SETVSL )
        self.writeData(0xA0)
        self.writeData(0xB5)
        self.writeData(0x55)

        self.writeCommand(self.CMD_PRECHARGE2)
        self.writeData(0x01)

        self.writeCommand(self.CMD_DISPLAYON)         #--turn on oled panel

        #Now we take the chance to clean the screen
        self.fillScreen(0)
        self.frame_buffer = np.full((128,128),0,dtype=np.uint16)
        self.optimization = True

    #Invert the display... whatever that means.
    def invert(self, v):   # v is a boolean
        """ Inverts the current colors displayed on the screen


        Parameters
        ----------
        v : boolean.
            TRUE  =>  Colors are inverted
            FALSE =>  Colors are displayed normally

        Returns
        --------
        Nothing

        """


        if v == True:
            self.writeCommand(self.CMD_INVERTDISPLAY)
        elif v == False:
            self.writeCommand(self.CMD_NORMALDISPLAY)


    # def flipDisplay(self, flipped=True):
    #     # self.flipped = flipped
    #     if flipped:
    #         self.writeCommand(self.COM_SCAN_INC)
    #         self.writeCommand(self.SEG_REMAP | 0x00)
    #     else:
    #         self.writeCommand(self.COM_SCAN_DEC)
    #         self.writeCommand(self.SET_COM_PINS, 0x02)

    # def normal_display(self):
    #     self.command(self.CMD_NORMALDISPLAY)

    # def set_contrast(self, contrast=0x7f):
    #     self.command(self.SET_CONTRAST, contrast)


    def goTo(self, x, y):
        """ ***NOT PART OF THE API***
            moves the internal cursor of the screen to a certain position


        Parameters
        ----------
        x : uint8.
            Horizontal coordinate.

        y : uint8.
            Vertical coordinate.

        Returns
        --------
        Nothing

        """
        if x >= self.SSD1351WIDTH or y >= self.SSD1351HEIGHT:
            return

        # set x cooordinate
        self.writeCommand(self.CMD_SETCOLUMN)
        self.writeData([x,self.SSD1351WIDTH-1])
        # self.writeData(self.SSD1351WIDTH-1)
        # set y coordinate
        self.writeCommand(self.CMD_SETROW)
        self.writeData([y,self.SSD1351HEIGHT-1])
        # self.writeData(self.SSD1351HEIGHT-1)
        # algo
        self.writeCommand(self.CMD_WRITERAM)



    def color565(self, (colorRGB)): # ints
        """ Converts a three-tuple representing an (RGB) color to a 16bit unsigned int representing
            such color


        Parameters
        ----------
        coloresRGB: three-tuple.
                    Tuple of colors (R,G,B) to be converted to a 16bits uint representation
                    5 bits red, 6 bits greenn y 5 bits blue.

        Returns
        --------
        c : uint16
            RGB color represented as an uint16, ready for the drawing functions.

        """
        r,g,b = colorRGB
        c = r >> 3
        c <<= 6
        c |= g >> 2
        c <<= 5
        c |= b >> 3
        return c


    def fillScreen(self, fillcolor): # int
        """ Colors the entire screen with "fillcolor"


        Parameters
        ----------
        fillcolor: uint16.
                   integer representing a 16bit color (e.g. 0xF800), the entire screen
                   gets painted with it.

        Returns
        --------
        Nothing

        """

        self.fillRect(0, 0, self.SSD1351WIDTH, self.SSD1351HEIGHT, fillcolor)


## We are ignoring de rotation support, meybe i will add later. if this actually works
    def fillRect(self, x, y, w, h, fillcolor):
        """ Draws a solid rectangle anywhere on the screen.


        Parameters
        ----------
        x : uint8.
            Horizontal coordinate of the top-left corner of the rectangle, in pixels.

        y : uint8.
            Vertical coordinate of the top-left corner of the rectangle, in pixels.

        w : uint8.
            Widht of the rectangle, in pixels

        h : uint8.
            Height of the rectangle, in pixels

        fillcolor : uint16.
            Color of the rectangle, represented as a 16bit integer (e.g. 0xF800).

        Returns
        --------
        Nothing

        """


        # Bounds check
        if x >= self.SSD1351WIDTH or y >= self.SSD1351HEIGHT:
            return

        if y+h > self.SSD1351HEIGHT:
            h = self.SSD1351HEIGHT - y - 1

        if x+w > self.SSD1351WIDTH:
            w = self.SSD1351WIDTH - x - 1

        #Check if optimization is actually convinient
        # if self.optimization:
        #     total_pixels = float(w*h)
        #     time_normal = total_pixels/597956      #597956 pixels/sec  is the Normal speed of the fillRect function
        #     painted_pixels = [tt for tt in np.asarray(np.unique(self.frame_buffer[x:x+w ,y:y+h],return_counts=True)).T  if fillcolor in tt]
        #     if painted_pixels == []: painted_pixels = 0 #Border case where there are no painted pixels
        #     else: painted_pixels = painted_pixels[0][1]
        #     pixels_to_paint = total_pixels - painted_pixels
        #     time_pixelated = float(pixels_to_paint)/2501 #874 pixels/sec  is the Normal speed of the drawPixel function
        #     print "fillRect = {}ms,  drawPixel = {}ms for {}pixels totals and {}pixels real".format(time_normal*1000,time_pixelated*1000,total_pixels,pixels_to_paint)
        #     if time_pixelated < time_normal:
        #         print "pixelado!"
        #         [self.drawPixel(x1,y1,fillcolor) for x1 in range(x,x+w) for y1 in range(y,y+h)]

        #         #Escribimos en el frame_buffer
        #         block = np.full((w,h),fillcolor)
        #         self.frame_buffer[x:x+w ,y:y+h] = block
        #         return


        # set location
        self.writeCommand(self.CMD_SETCOLUMN)
        self.writeData([x,x+w-1])
        # self.writeData(x+w-1)
        self.writeCommand(self.CMD_SETROW)
        self.writeData([y,y+h-1])
        # self.writeData(y+h-1)
        # fill!
        self.writeCommand(self.CMD_WRITERAM)

        #We try to get around the limitation of the 4096 buffer size of the spidev module
        if 2*w*h > self.spi_buffer_size:
        #With this we split the transfer into a lot of 4096 bytes transfers
            for i in xrange(2*w*h/self.spi_buffer_size):
                self.writeData([fillcolor >> 8,fillcolor] * (self.spi_buffer_size/2))
            #     print"Enviadas 4096 trasnferencias"
            # print"Enviando ultimas {} transferencias".format((((2*w*h)%4096)/2))
            if ((2*w*h)%self.spi_buffer_size) > 0:
                #If there is still something to send, send it!
                self.writeData([fillcolor >> 8,fillcolor] * (((2*w*h)%self.spi_buffer_size)/2))
        else:
            self.writeData([fillcolor >> 8,fillcolor] * w*h)
        # for i in xrange(w*h):                                ##### Quizas se puede mejorar con un map
        #    self.writeData(fillcolor >> 8)
        #    self.writeData(fillcolor)

        #Escribimos en el frame_buffer
        block = np.full((w,h),fillcolor)
        self.frame_buffer[x:x+w ,y:y+h] = block



#This is necesary for the suppor with de GFX library
    def drawFastHLine(self, x, y, w, color):
        """ Draws an horizontal line on the screen, taking full advantage of any
            acceleration provided by the screen's driver chip.


        Parameters
        ----------
        x : uint8.
            Horizontal coordinate of the leftmost point of the line, in pixels.

        y : uint8.
            Vertical coordinate of the leftmost point of the line, in pixels.

        w : uint8.
            Widht of the rectangle, in pixels

        color : uint16.
            Color of the line, represented as a 16bit integer (e.g. 0xF800).

        Returns
        --------
        Nothing

        """
        # Bounds check
        if x >= self.SSD1351WIDTH or y >= self.SSD1351HEIGHT:
            return

        # X bounds check
        if x+w > self.SSD1351WIDTH:
            w = self.SSD1351WIDTH - x - 1
        if w < 0:
            return


        #Check if optimization is actually convinient
        # if self.optimization:
        #     total_pixels = float(w)
        #     time_normal = total_pixels/597956       #597956 pixels/sec  is the Normal speed of the fillRect function
        #     painted_pixels = [tt for tt in np.asarray(np.unique(self.frame_buffer[x:x+w ,y],return_counts=True)).T  if color in tt]
        #     if painted_pixels == []: painted_pixels = 0 #Border case where there are no painted pixels
        #     else: painted_pixels = painted_pixels[0][1]
        #     pixels_to_paint = total_pixels - painted_pixels
        #     time_pixelated = float(pixels_to_paint)/2501 #874 pixels/sec  is the Normal speed of the drawPixel function
        #     # print "fillRect = {}ms,  drawPixel = {}ms for {}pixels totals and {}pixels real".format(time_normal*1000,time_pixelated*1000,total_pixels,pixels_to_paint)
        #     if time_pixelated < time_normal:
        #         print "pixelado!"
        #         [self.drawPixel(x1,y,color) for x1 in range(x,x+w)]

        #         #Escribimos en el frame_buffer
        #         block = np.full((w,),color)
        #         self.frame_buffer[x:x+w ,y] = block
        #         return

        # set location
        self.writeCommand(self.CMD_SETCOLUMN)
        self.writeData([x,x+w-1])
        # self.writeData(x+w-1)
        self.writeCommand(self.CMD_SETROW)
        self.writeData([y,y])
        # self.writeData(y)
        # fill!
        self.writeCommand(self.CMD_WRITERAM)

        self.writeData([color >> 8,color] * w)
        # for i in range(w):                                ##### Quizas se puede mejorar con un map
        #    self.writeData(color >> 8)
        #    self.writeData(color)

        #Escribimos en el frame_buffer
        block = np.full((w,),color)
        self.frame_buffer[x:x+w ,y] = block
        return



#This is also necesary for the support of the GFX libray
    def drawFastVLine(self, x, y, h, color):
        """ Draws a vertical line on the screen, taking full advantage of any
            acceleration provided by the screen's driver chip.


        Parameters
        ----------
        x : uint8.
            Horizontal coordinate of the topmost point of the line, in pixels.

        y : uint8.
            Vertical coordinate of the topmost point of the line, in pixels.

        h : uint8.
            Height of the rectangle, in pixels

        color : uint16.
            Color of the line, represented as a 16bit integer (e.g. 0xF800).


        Returns
        --------
        Nothing

        """

        # Bounds check
        if x >= self.SSD1351WIDTH or y >= self.SSD1351HEIGHT:
            return

        # X bounds check
        if y+h > self.SSD1351HEIGHT:
            h = self.SSD1351HEIGHT - y - 1
        if h < 0:
            return

        #Check if optimization is actually convinient
        # if self.optimization:
        #     total_pixels = float(h)
        #     time_normal = total_pixels/597956       #3649 pixels/sec  is the Normal speed of the fillRect function
        #     painted_pixels = [tt for tt in np.asarray(np.unique(self.frame_buffer[x,y:y+h],return_counts=True)).T  if color in tt]
        #     if painted_pixels == []: painted_pixels = 0 #Border case where there are no painted pixels
        #     else: painted_pixels = painted_pixels[0][1]
        #     pixels_to_paint = total_pixels - painted_pixels
        #     time_pixelated = float(pixels_to_paint)/2501 #874 pixels/sec  is the Normal speed of the drawPixel function
        #     print "fillRect = {}ms,  drawPixel = {}ms for {}pixels totals and {}pixels real".format(time_normal*1000,time_pixelated*1000,total_pixels,pixels_to_paint)
        #     if time_pixelated < time_normal:
        #         print "pixelado!"
        #         [self.drawPixel(x,y1,color) for y1 in range(y,y+h)]

        #         #Escribimos en el frame_buffer
        #         block = np.full((h,),color)
        #         self.frame_buffer[x ,y:y+h] = block
        #         return

        # set location
        self.writeCommand(self.CMD_SETCOLUMN)
        self.writeData([x,x])
        # self.writeData(x)
        self.writeCommand(self.CMD_SETROW)
        self.writeData([y,y+h-1])
        # self.writeData(y+h-1)
        # fill!
        self.writeCommand(self.CMD_WRITERAM)

        self.writeData([color >> 8,color] * h)
        # for i in range(h):                                ##### Quizas se puede mejorar con un map
        #    self.writeData(color >> 8)
        #    self.writeData(color)

        #Escribimos en el frame_buffer
        block = np.full((h,),color)
        self.frame_buffer[x ,y:y+h] = block
        return


# Also necsary for compatibility with the GFX library
    def drawPixel(self, x, y, color):
        """ Paints a single pixel on the screen


        Parameters
        ----------
        x : uint8.
            Horizontal coordinate pixel, in pixels.

        y : uint8.
            Vertical coordinate of the pixel, in pixels.

        color : uint16.
            Color of the pixel, represented as a 16bit integer (e.g. 0xF800).


        Returns
        --------
        Nothing

        """


        # Bounds check
        if x >= self.SSD1351WIDTH or y >= self.SSD1351HEIGHT:
            return

        if x < 0 or y < 0:
            return


        #We check if the pixel is already the color we want

        if self.optimization == True and self.frame_buffer.item((x,y)) == color:
            return
        else:
            # set location
            self.goTo(x, y)
            #Write the data
            self.writeData([color >> 8,color])
            # self.writeData(color >> 8)
            # self.writeData(color)

            #Now we record the pixel to the frame buffer
            self.frame_buffer.itemset((x,y),color)



    # def drawBitmap(self, x, y, bitmap):
    #     h = len(bitmap)
    #     w = len(bitmap[0])

    #     self.command(self.CMD_SETCOLUMN, [x, w])
    #     self.command(self.CMD_SETROW, [y, h])
    #     self.command(self.CMD_WRITERAM)

    #     pixels = []

    #     for r in range(y, y+h):
    #         if len(pixels) + 4*w >= 1024:
    #             print "pixels!", pixels
    #             self.data(pixels)
    #             pixels = []

    #         for x in bitmap[r]:
    #             pixels = pixels + [(x >> 8) & 0xFF, x & 0xFF]

    #     print "pixels!", pixels
    #     self.data(pixels)


#########################################################################################################################
######                                         GFX Library                                                         ######
#########################################################################################################################


    # Draw a circle outline
    def drawCircle(self, x0, y0, r, color):
        """ Draws a hollow circle on the screen.


        Parameters
        ----------
        x0 : uint8.
            Horizontal coordinate of the center of the circle, in pixels.

        y0 : uint8.
            Vertical coordinate of the center of the circle, in pixels.

        r : uint8.
            Radius of the circle, in pixels.

        color : uint16.
            Color of the cicle's perimeter, represented as a 16bit integer (e.g. 0xF800).


        Returns
        --------
        Nothing

        """

        f = 1 - r
        ddF_x = 1
        ddF_y = -2 * r
        x = 0
        y = r

        self.drawPixel(x0  , y0+r, color)
        self.drawPixel(x0  , y0-r, color)
        self.drawPixel(x0+r, y0  , color)
        self.drawPixel(x0-r, y0  , color)

        while (x<y):

            if (f >= 0):
                y     -= 1
                ddF_y += 2
                f     += ddF_y

            x += 1
            ddF_x += 2
            f += ddF_x

            self.drawPixel(x0 + x, y0 + y, color)
            self.drawPixel(x0 - x, y0 + y, color)
            self.drawPixel(x0 + x, y0 - y, color)
            self.drawPixel(x0 - x, y0 - y, color)
            self.drawPixel(x0 + y, y0 + x, color)
            self.drawPixel(x0 - y, y0 + x, color)
            self.drawPixel(x0 + y, y0 - x, color)
            self.drawPixel(x0 - y, y0 - x, color)


    def drawCircleHelper(self, x0, y0, r, cornername, color):
        """ *NOT PART OF THE API*
            Auxiliary function to draw circles a rounded rectangles


        Parameters
        ----------
        x0 : uint8.
            Horizontal coordinate of the center of the circle, in pixels.

        y0 : uint8.
            Vertical coordinate of the center of the circle, in pixels.

        r : uint8.
            Radius of the circle, in pixels.

        cornername : ???
            ???

        color : uint16.
            Color of the cicle's perimeter, represented as a 16bit integer (e.g. 0xF800).


        Returns
        --------
        Nothing

        """
        f     = 1 - r
        ddF_x = 1
        ddF_y = -2 * r
        x     = 0
        y     = r

        while (x<y):

            if (f >= 0):
                y     -= 1
                ddF_y += 2
                f     += ddF_y

            x     += 1
            ddF_x += 2
            f     += ddF_x

            if (cornername & 0x4) != 0:
                self.drawPixel(x0 + x, y0 + y, color)
                self.drawPixel(x0 + y, y0 + x, color)

            if (cornername & 0x2) != 0:
                self.drawPixel(x0 + x, y0 - y, color)
                self.drawPixel(x0 + y, y0 - x, color)

            if (cornername & 0x8) != 0:
                self.drawPixel(x0 - y, y0 + x, color)
                self.drawPixel(x0 - x, y0 + y, color)

            if (cornername & 0x1) != 0:
                self.drawPixel(x0 - y, y0 - x, color)
                self.drawPixel(x0 - x, y0 - y, color)



    # Used to do circles and roundrects
    def fillCircleHelper(self, x0, y0, r, cornername, delta, color):
        """ *NOT PART OF THE API*
            Auxiliary function to draw circles a rounded rectangles


        Parameters
        ----------
        x0 : uint8.
            Horizontal coordinate of the center of the circle, in pixels.

        y0 : uint8.
            Vertical coordinate of the center of the circle, in pixels.

        r : uint8.
            Radius of the circle, in pixels.

        cornername : ???
            ???

        delta : ???
            ???

        color : uint16.
            Color of the cicle's perimeter, represented as a 16bit integer (e.g. 0xF800).


        Returns
        --------
        Nothing

        """
        f     = 1 - r
        ddF_x = 1
        ddF_y = -2 * r
        x     = 0
        y     = r

        while (x<y):

            if (f >= 0):
                y     -= 1
                ddF_y += 2
                f     += ddF_y

            x     += 1
            ddF_x += 2
            f     += ddF_x

            if (cornername & 0x1) != 0:
              self.drawFastVLine(x0+x, y0-y, 2*y+1+delta, color)
              self.drawFastVLine(x0+y, y0-x, 2*x+1+delta, color)

            if (cornername & 0x2) != 0:
              self.drawFastVLine(x0-x, y0-y, 2*y+1+delta, color)
              self.drawFastVLine(x0-y, y0-x, 2*x+1+delta, color)


    def fillCircle(self, x0, y0, r, color):
        """ Draws a solid circle on the screen.


        Parameters
        ----------
        x0 : uint8.
            Horizontal coordinate of the center of the circle, in pixels.

        y0 : uint8.
            Vertical coordinate of the center of the circle, in pixels.

        r : uint8.
            Radius of the circle, in pixels.

        color : uint16.
            Color of the cicle, represented as a 16bit integer (e.g. 0xF800).


        Returns
        --------
        Nothing

        """

        self.drawFastVLine(x0, y0-r, 2*r+1, color)
        self.fillCircleHelper(x0, y0, r, 3, 0, color)


    #We define the swap Macro
    def swap(self, x,y):
        """ *NOT PART OF THE API*
            small helper function
        """
        return y,x


    # Bresenham's algorithm - thx wikpedia
    def drawLine(self, x0, y0, x1, y1, color):
        """ Draws a line on the screen by connecting two specified points.
            can be horizontal, vertical or diagonal.


        Parameters
        ----------
        x0 : uint8.
            Horizontal coordinate of the first point of the line, in pixels.

        y0 : uint8.
            Vertical coordinate of the first point of the line, in pixels.

        x1 : uint8.
            Horizontal coordinate of the second point of the line, in pixels.

        y1 : uint8.
            Vertical coordinate of the second point of the line, in pixels.

        color : uint16.
            Color of the line, represented as a 16bit integer (e.g. 0xF800).


        Returns
        --------
        Nothing

        """


        steep = abs(y1 - y0) > abs(x1 - x0)

        if (steep):
            x0, y0 = self.swap(x0, y0)
            x1, y1 = self.swap(x1, y1)

        if (x0 > x1):
            x0, x1 = self.swap(x0, x1)
            y0, y1 = self.swap(y0, y1)

        dx = x1 - x0
        dy = abs(y1 - y0)

        err = dx / 2        # in Python 3 you should perform an explicit float --> int convertion, here it's fine, due to the integer division thingy in python 2
        ystep = 0

        if (y0 < y1):
            ystep = 1
        else:
            ystep = -1

        #for (; x0<=x1; x0++) {
        for x0 in range(x0,x1+1):
            if (steep):
                self.drawPixel(y0, x0, color)
            else:
                self.drawPixel(x0, y0, color)

            err -= dy
            if (err < 0):
                y0 += ystep
                err += dx

#Draws empty rectangles
    def drawRect(self, x, y, w, h,color):
        """ Draws an empty rectangle anywhere on the screen.


        Parameters
        ----------
        x : uint8.
            Horizontal coordinate of the top-left corner of the rectangle, in pixels.

        y : uint8.
            Vertical coordinate of the top-left corner of the rectangle, in pixels.

        w : uint8.
            Widht of the rectangle, in pixels

        h : uint8.
            Height of the rectangle, in pixels

        color : uint16.
            Color of the rectangle's perimeter, represented as a 16bit integer (e.g. 0xF800).


        Returns
        --------
        Nothing

        """
        self.drawFastHLine(x, y, w, color)
        self.drawFastHLine(x, y+h-1, w, color)
        self.drawFastVLine(x, y, h, color)
        self.drawFastVLine(x+w-1, y, h, color)

# Draw a rounded rectangle
    def drawRoundRect(self, x, y, w, h, r, color):
        """ Draws an empty rectangle with rounded corners anywhere on the screen.


        Parameters
        ----------
        x : uint8.
            Horizontal coordinate of the top-left corner of the rectangle, in pixels.

        y : uint8.
            Vertical coordinate of the top-left corner of the rectangle, in pixels.

        w : uint8.
            Widht of the rectangle, in pixels

        h : uint8.
            Height of the rectangle, in pixels

        r : uint8.
            Radius of the rounded corner, in pixels

        color : uint16.
            Color of the rectangle's perimeter, represented as a 16bit integer (e.g. 0xF800).


        Returns
        --------
        Nothing

        """
        #  smarter version
        self.drawFastHLine(x+r  , y    , w-2*r, color) #  Top
        self.drawFastHLine(x+r  , y+h-1, w-2*r, color) #  Bottom
        self.drawFastVLine(x    , y+r  , h-2*r, color) #  Left
        self.drawFastVLine(x+w-1, y+r  , h-2*r, color) #  Right
        #  draw four corners
        self.drawCircleHelper(x+r    , y+r    , r, 1, color)
        self.drawCircleHelper(x+w-r-1, y+r    , r, 2, color)
        self.drawCircleHelper(x+w-r-1, y+h-r-1, r, 4, color)
        self.drawCircleHelper(x+r    , y+h-r-1, r, 8, color)


# Fill a rounded rectangle
    def fillRoundRect(self, x, y, w, h, r, color):
        """ Draws a solid rectangle with rounded corners anywhere on the screen.


        Parameters
        ----------
        x : uint8.
            Horizontal coordinate of the top-left corner of the rectangle, in pixels.

        y : uint8.
            Vertical coordinate of the top-left corner of the rectangle, in pixels.

        w : uint8.
            Widht of the rectangle, in pixels

        h : uint8.
            Height of the rectangle, in pixels

        r : uint8.
            Radius of the rounded corner, in pixels

        color : uint16.
            Color of the rectangle, represented as a 16bit integer (e.g. 0xF800).


        Returns
        --------
        Nothing

        """
        #  smarter version
        self.fillRect(x+r, y, w-2*r, h, color)

        #  draw four corners
        self.fillCircleHelper(x+w-r-1, y+r, r, 1, h-2*r-1, color)
        self.fillCircleHelper(x+r    , y+r, r, 2, h-2*r-1, color)


#  Draw a triangle
    def drawTriangle(self, x0, y0, x1, y1, x2, y2, color):
        """ Draws an empty triangle, especified by three points, anywhere on the screen.


        Parameters
        ----------
        x0 : uint8.
            Horizontal coordinate of the first point of the triangle, in pixels.

        y0 : uint8.
            Vertical coordinate of the first point of the triangle, in pixels.

        x1 : uint8.
            Horizontal coordinate of the second point of the triangle, in pixels.

        y1 : uint8.
            Vertical coordinate of the second point of the triangle, in pixels.

        x2 : uint8.
            Horizontal coordinate of the thrid point of the triangle, in pixels.

        y2 : uint8.
            Vertical coordinate of the thrid point of the triangle, in pixels.

        color : uint16.
            Color of the triangle's perimeter, represented as a 16bit integer (e.g. 0xF800).


        Returns
        --------
        Nothing

        """
        self.drawLine(x0, y0, x1, y1, color)
        self.drawLine(x1, y1, x2, y2, color)
        self.drawLine(x2, y2, x0, y0, color)



#  Fill a triangle
    def fillTriangle (self, x0, y0, x1, y1, x2, y2, color):
        """ Draws a solid triangle, especified by three points, anywhere on the screen.


        Parameters
        ----------
        x0 : uint8.
            Horizontal coordinate of the first point of the triangle, in pixels.

        y0 : uint8.
            Vertical coordinate of the first point of the triangle, in pixels.

        x1 : uint8.
            Horizontal coordinate of the second point of the triangle, in pixels.

        y1 : uint8.
            Vertical coordinate of the second point of the triangle, in pixels.

        x2 : uint8.
            Horizontal coordinate of the thrid point of the triangle, in pixels.

        y2 : uint8.
            Vertical coordinate of the thrid point of the triangle, in pixels.

        color : uint16.
            Color of the triangle, represented as a 16bit integer (e.g. 0xF800).


        Returns
        --------
        Nothing

        """
        a = 0
        b = 0
        y = 0
        last = 0

        #  Sort coordinates by Y order (y2 >= y1 >= y0)
        if (y0 > y1):
            y0, y1 = self.swap(y0, y1)
            x0, x1 = self.swap(x0, x1)

        if (y1 > y2):
            y2, y1 = self.swap(y2, y1)
            x2, x1 = self.swap(x2, x1)

        if (y0 > y1):
            y0, y1 = self.swap(y0, y1)
            x0, x1 = self.swap(x0, x1)


        if(y0 == y2):  #  Handle awkward all-on-same-line case as its own thing
            b = x0
            a = x0

            if   (x1 < a): a = x1
            elif (x1 > b): b = x1

            if   (x2 < a): a = x2
            elif (x2 > b): b = x2

            self.drawFastHLine(a, y0, b-a+1, color)
            return


        # int16_t
        dx01 = x1 - x0
        dy01 = y1 - y0
        dx02 = x2 - x0
        dy02 = y2 - y0
        dx12 = x2 - x1
        dy12 = y2 - y1
        # int32_t
        sa   = 0
        sb   = 0

          #  For upper part of triangle, find scanline crossings for segments
          #  0-1 and 0-2.  If y1=y2 (flat-bottomed triangle), the scanline y1
          #  is included here (and second loop will be skipped, avoiding a /0
          #  error there), otherwise scanline y1 is skipped here and handled
          #  in the second loop...which also avoids a /0 error here if y0=y1
          #  (flat-topped triangle).

        if (y1 == y2):  last = y1;   #  Include y1 scanline
        else:           last = y1-1; #  Skip it

          # for(y=y0; y<=last; y++) {
        for y in xrange(y0,last+1):

            if dy01 == 0 or dy02 == 0: continue

            a   = x0 + sa / dy01
            b   = x0 + sb / dy02
            sa += dx01
            sb += dx02
            # /* longhand
            # a = x0 + (x1 - x0) * (y - y0) / (y1 - y0);
            # b = x0 + (x2 - x0) * (y - y0) / (y2 - y0);
            # */

            if (a > b): a,b = self.swap(a,b)
            self.drawFastHLine(a, y, b-a+1, color)

        # For lower part of triangle, find scanline crossings for segments
        # 0-2 and 1-2.  This loop is skipped if y1=y2.
        sa = dx12 * (y - y1)
        sb = dx02 * (y - y0)

# I belive this function has an error here somewhere, that generates division by 0, but not sure where.

        # for(; y<=y2; y++) {
        for y in xrange(y,y2+1):

            if dy02 == 0 or dy12 == 0: continue

            a   = x1 + sa / dy12
            b   = x0 + sb / dy02
            sa += dx12
            sb += dx02
            # /* longhand:
            # a = x1 + (x2 - x1) * (y - y1) / (y2 - y1);
                # b = x0 + (x2 - x0) * (y - y0) / (y2 - y0);
            # */
            if(a > b): a,b =  self.swap(a,b)
            self.drawFastHLine(a, y, b-a+1, color)




#### Aqui empiezan las funciones de escritura! ###

    def setCursor(self, x, y):
        """ Sets de writing cursor of the screen to a certan position, all subsequent calls
            to the write() fucntion will print it's characters starting at that position


        Parameters
        ----------
        x : uint8.
            Horizontal position of the cursor, accepted values are from 0 to 21.

        y : uint8.
            Vertical position of the cursor, accepted values are from 0 to 16.


        Returns
        --------
        Nothing

        """
        #Bound check
        if (x > self.SSD1351WIDTH/self.font_size_x): x = int(x > self.SSD1351WIDTH/self.font_size_x - 1)
        if (y > self.SSD1351HEIGHT/self.font_size_y): y = int(x > self.SSD1351HEIGHT/self.font_size_y - 1)

        self.cursor_x = x
        self.cursor_y = y

    def getCursor(self):
        """ Returns the current position of the writing cursor


        Parameters
        ----------
        Nothing


        Returns
        --------
        out : two-tuple.
            Tuple with (X,Y) with the current position of the writing cursor.

        """
        return (self.cursor_x, self.cursor_y)


#It still doesn't support variable size letters
    def drawChar(self, x, y, c,  color= 0xffff, bg = 0x0000,  size = 1):
        """ Prints an 6x8 ASCII character anywhere on the screen, as defined by the font on "glcdfont.py"


        Parameters
        ----------
        x : uint8.
            Horizontal coordinate of the top-left corner of the 6x8 character, in pixels.

        y : uint8.
            Vertical coordinate of the top-left corner of the 6x8 character, in pixels.

        c : char, uint8.
            Character to print, may also be a number from 0 to 254 if you want to directly
            reference the font array.

        color : uint16.
            Color of the pixels needed to draw the charater, represented as a 16bit integer (e.g. 0xF800).
            default => WHITE

        bg : uint16.
            Color of the pixels intended as bachground to the charater, represented as a 16bit integer (e.g. 0xF800).
            default => BLACK

        size : uint8.
            Scaling factor for the size of the font. *NOT IMPLEMENTED*


        Returns
        --------
        Nothing

        """
        #Bounds check
        if ((x >= self.SSD1351WIDTH) or (y >= self.SSD1351HEIGHT) or ((x + (self.font_size_x + 1) * size - 1) < 0) or ((y + self.font_size_y * size - 1) < 0)):
            return

        if type(c) == str:
            #Convert charater to index
            letter = ord(c) & 0x7F
            if letter < 0: letter = 0
            # else: letter -= ord(' ')    #The Adafruit font already knows where to start. 32 is "space"
        elif type(c) == int:
            letter = c
        else: return

        #We create a flat list of each color that it's needed to draw the letter.
        letter_bits = np.unpackbits(np.asarray(np.append(self.font[letter],[0]),dtype = np.uint8) )
        letter_bits = np.asarray(map(lambda x:(bg,color)[x == 1], letter_bits) ,dtype = np.uint16) #We change the bit array to a color/background array
        letter_array = np.flipud(np.reshape(letter_bits,(6,8)).T) #Reorient the array
        self.drawBitmap(letter_array,x,y)

        # for j in xrange(self.font_size_x + 1):    #The adafruit glcd font only stores 5 of the 6 columns of the fonts. to save space.
        #     for i in xrange(self.font_size_y):
        #         if (j < self.font_size_x):  line = self.font[letter][j]
        #         else: line = 0x00 #This is the separator between the characters
        #         if ( line & (0x01 << i) != 0 ):
        #             self.drawPixelFB(x+j,y+i,color)
        #         elif bg == None: continue
        #         else:
        #             self.drawPixelFB(x+j,y+i,bg)




#Function for writing strings of text
    def write(self, text, color= 0xffff, bg = 0x0000 ):
        """ Prints an string on the screen on the current position of the writing cursor.
            the writing cursor self actualizes and automatically wraps the text.
            '\n' charater is supported.
            uses the 6x8 font defined  on "glcdfont.py"


        Parameters
        ----------
        text : string, list of ints.
            String to be printed on the screen, may also be a list of integers representing positions
            on the font array.

        color : uint16.
            Color of the pixels needed to draw the charater, represented as a 16bit integer (e.g. 0xF800).
            default => WHITE

        bg : uint16.
            Color of the pixels intended as bachground to the charater, represented as a 16bit integer (e.g. 0xF800).
            default => BLACK


        Returns
        --------
        Nothing

        """
        for c in text:
            if c == '\n':
                self.cursor_x = 0
                self.cursor_y += 1
            else:
                if c == '°':  c = [247]               #Font number for the little degree circle

                self.drawChar(self.cursor_x * (self.font_size_x + 1) , self.cursor_y * self.font_size_y, c, color,bg )
                self.cursor_x += 1
                if self.cursor_x * (self.font_size_x + 1) > self.SSD1351WIDTH - (self.font_size_x + 1):
                    #Wrap!
                    self.cursor_x = 0
                    self.cursor_y += 1
                    #Bound check on the Y axis
                    if self.cursor_y * self.font_size_y > self.SSD1351HEIGHT - self.font_size_y:
                        #Back to the start
                        self.cursor_x = 0
                        self.cursor_y = 0

        # # We draw the letter as a bitmap
        # print "almost in"
        # self.drawBitmap(self.frame_buffer[init_y*self.font_size_y:(self.cursor_y + 1)*self.font_size_y,init_x*self.font_size_x:(self.cursor_x + 1)*self.font_size_x], init_y*self.font_size_y, init_x*self.font_size_x)
        # print "out!"


#Draw bitmap (the bitmap is a numpy array)
    def drawBitmap(self, bitmap, x, y):
        """ Draws an image to the screen. The image must be a two-dimensional numpy array with each
        element being a 16bit color integer(NOT an RGB tuple).

        NOTE: if the image is too big for the screen, or positioned in such a way that it doesn't fit the
        screen. Nothing will be displayed, the function will just return.


        Parameters
        ----------
        bitmap : 2-dimensional ndarray.
            image to be drawn on the screen

        x : uint8.
            Horizontal coordinate of the top-left corner of the image, in pixels.

        y : uint8.
            Vertical coordinate of the top-left corner of the image, in pixels.


        Returns
        --------
        Nothing

        """



        w = bitmap.shape[1]
        h = bitmap.shape[0]

        # Bounds check
        if x >= self.SSD1351WIDTH or y >= self.SSD1351HEIGHT:
            return

        if y+h > self.SSD1351HEIGHT:
            return

        if x+w > self.SSD1351WIDTH:
            return


        # If the image is not transformed to 16bits color
        if len(bitmap.shape) == 3:
            return
            # bitmap565 = np.zeros_like(bitmap[:,:,0],dtype=np.uint16)
            # for j in range(bitmap.shape[0]):
            #     for k in range(bitmap.shape[1]):
            #         bitmap565.itemset((j,k), self.color565(bitmap[j][k]))
            # # Transform the array into a list
            # bitmap = [ list(z) for z in bitmap565]


        flat_bitmap = [int(item) for sublist in bitmap for item in sublist]
        # flat_bitmap = [int(i) for i in flat_bitmap]
        flat_bitmap2 = [[i >> 8, i] for i in flat_bitmap]
        flat_bitmap3 = [item for sublist in flat_bitmap2 for item in sublist]

        # set location
        self.writeCommand(self.CMD_SETCOLUMN)
        self.writeData([x,x+w-1])
        # self.writeData(x+w-1)
        self.writeCommand(self.CMD_SETROW)

        self.writeData([y,y+h-1])
        # self.writeData(y+h-1)
        # fill!
        self.writeCommand(self.CMD_WRITERAM)

        #Write the bitmap
        #We try to get around the 4096 buffer size limitation
        if len(flat_bitmap3) > self.spi_buffer_size:
        #With this we split the transfer into a lot of 4096 bytes transfers
            bloques = len(flat_bitmap3)/self.spi_buffer_size
            sobrante = len(flat_bitmap3)%self.spi_buffer_size
            # Splitting guide for the array
            split_guide = [ (i+1)*self.spi_buffer_size for i in xrange(bloques)]
            # We add the the last division
            split_guide = split_guide + [split_guide[-1]+sobrante]
            for block in np.split(np.asarray(flat_bitmap3),split_guide):
                if len(block) > 0:
                    self.writeData(list(block))
            return

        self.writeData(flat_bitmap3)
        # self.frame_buffer[y:y+h,x:x+w] = bitmap


# Pretransform bitmaps to 16bit arrays
    def convertBitmap565(self,bitmap):
        """ Converts a Numpy array representing an image with RGB tuples, to a numpy array
        representing an image with 16bits integer coded colors. The returned array may be passed
        to the "drawBitmap() function.


        Parameters
        ----------
        bitmap : image ndarray.
            Image to be converted from (RGB) tuples to 16bit color

        Returns
        --------
        out : 16bit color image ndarray.
            Image converted to 16bit color

        """
        # If the image is not transformed to 16bits color
        if len(bitmap.shape) == 3:
            bitmap565 = np.zeros_like(bitmap[:,:,0],dtype=np.uint16)
            for j in range(bitmap.shape[0]):
                for k in range(bitmap.shape[1]):
                    bitmap565.itemset((j,k), self.color565(bitmap[j][k]))

        return bitmap565


#########################################################################################################################
######                               FRAMEBUFFER OPTIMIZATION                                                      ######
#########################################################################################################################

#This is necesary for the suppor with de GFX library
    def drawFastHLineFB(self, x, y, w, color):
        # Bounds check
        if x >= self.SSD1351WIDTH or y >= self.SSD1351HEIGHT:
            return

        # X bounds check
        if x+w > self.SSD1351WIDTH:
            w = self.SSD1351WIDTH - x - 1
        if w < 0:
            return

        self.frame_buffer[x:x+w ,y] = color
        return


#This is also necesary for the support of the GFX libray
    def drawFastVLineFB(self, x, y, h, color):
        # Bounds check
        if x >= self.SSD1351WIDTH or y >= self.SSD1351HEIGHT:
            return

        # X bounds check
        if y+h > self.SSD1351HEIGHT:
            h = self.SSD1351HEIGHT - y - 1
        if h < 0:
            return

        #Write the frame_buffer
        self.frame_buffer[x ,y:y+h] = color
        return


# Also necsary for compatibility with the GFX library
    def drawPixelFB(self, x, y, color):
        # Bounds check
        if x >= self.SSD1351WIDTH or y >= self.SSD1351HEIGHT:
            return

        if x < 0 or y < 0:
            return


        #We check if the pixel is already the color we want

        if self.frame_buffer.item((y,x)) != color:
            #Now we record the pixel to the frame buffer
            self.frame_buffer.itemset((y,x),color)
