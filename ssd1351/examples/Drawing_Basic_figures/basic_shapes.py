""" Small example script to show the drawing functions of the library
"""

import ssd1351
import time

#Start OLED driver, it always starts on a black screen
oled = ssd1351.SSD1351()
oled.begin()

while(1):
    #TV COLOR BARS
    #top bars
    oled.fillRect(0,0,16,100, oled.WHITE)        # oled.WHITE    ==  0xFFFF
    oled.fillRect(16,0,16,100, oled.YELLOW)      # oled.YELLOW   ==  0xFFE0
    oled.fillRect(32,0,16,100, oled.CYAN)        # oled.CYAN     ==  0x07FF
    oled.fillRect(48,0,16,100, oled.GREEN)       # oled.GREEN    ==  0x07E0
    oled.fillRect(64,0,16,100, oled.MAGENTA)     # oled.MAGENTA  ==  0xF8F1
    oled.fillRect(80,0,16,100, oled.RED)         # oled.RED      ==  0xF800
    oled.fillRect(96,0,16,100, oled.BLUE)        # oled.BLUE     ==  0x001F
    oled.fillRect(112,0,16,100, oled.BLACK)      # oled.BLACK    ==  0x0000
    #bottom bars
    oled.fillRect(0,100,32,28,  oled.color565((0,0,0)) )        # black
    oled.fillRect(32,100,32,28, oled.color565((80,80,80)) )     # dark gray
    oled.fillRect(64,100,32,28, oled.color565((170,170,170)) )  # light gray
    oled.fillRect(96,100,32,28, oled.color565((255,255,255)) )  # white

    time.sleep(5)
    oled.fillScreen(0x000) #We clean the screen

    #SHOOTING TARGET
    oled.fillCircle(64,64,60,oled.RED)
    oled.fillCircle(64,64,50,oled.WHITE)
    oled.fillCircle(64,64,40,oled.RED)
    oled.fillCircle(64,64,30,oled.WHITE)
    oled.fillCircle(64,64,20,oled.RED)
    oled.fillCircle(64,64,10,oled.WHITE)
    time.sleep(5)
    oled.fillScreen(0x00)#We clean the screen


    #RADIATING LINES
    for i in range(8):
        oled.drawLine(0,0,i*16,128,oled.CYAN)
    for i in range(8):
        oled.drawLine(0,0,128,i*16,oled.CYAN)
    time.sleep(5)
    oled.fillScreen(0x00)#We clean the screen

    #TRIFORCE
    oled.fillTriangle(64,0,32,64,96,64,oled.YELLOW)
    oled.fillTriangle(0,128,32,64,64,128,oled.YELLOW)
    oled.fillTriangle(64,128,128,128,96,64,oled.YELLOW)
    time.sleep(5)
    oled.fillScreen(0x00)#We clean the screen

