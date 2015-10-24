""" Small example script to show how to print text on the screen with the ssd1351 library
"""

import ssd1351
import time

#Start OLED driver, it always starts on a black screen
oled = ssd1351.SSD1351()
oled.begin()

while(1):
    #Write some text at the top-left corner (default start, cursor = (0,0))

    oled.write("Hello, world!")
    time.sleep(4)

    #Write the text Cyan over magenta at the center of the screen
    oled.setCursor(8,8)
    oled.write("This is the center",oled.CYAN,oled.MAGENTA)
    time.sleep(4)

    #Overwrite the first line we wrote, now in green over black. And using the '\n' character to finish our sentence in line below
    oled.setCursor(0,0)
    oled.write("Oops! overwritting\n",oled.GREEN)
    oled.write("second line!",oled.GREEN)
    time.sleep(4)

    #Now, go back to the top left corner and write a really long text
    oled.setCursor(0,0)
    oled.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus placerat diam tincidunt purus imperdiet, nec maximus orci posuere. Duis egestas mattis nunc. In ultricies nunc vel elit imperdiet mollis. Donec pulvinar mollis odio pellentesque pharetra. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia")
    time.sleep(4)
    oled.fillScreen(0x00)
    oled.setCursor(0,0)
