""" Small script that renders a gif of peanut butter jelly time read from 7 .jpg
    it uses scipy library to read the images. It requires about half a minute before showing the animation
    due to the slowness of converting each image to 16bit color before displaying
"""

from scipy import misc
import ssd1351

#load frames
frames = [0,0,0,0,0,0,0]
for i in range(7):
    frames[i] = misc.imread("frame_" + str(i) + ".png")

#Start OLED driver
oled = ssd1351.SSD1351()
oled.begin()

#Test OLED
oled.fillCircle(64,64,20,0xf800)

#Transform bitmap to 16bit color format
frames16b = [oled.convertBitmap565(x) for x in frames]

#Start the fun (tittle)
oled.write("     Peanut Butter \n      Jelly Time!")


#Show every frame in order
while(1):

    for frame in frames16b:
        oled.drawBitmap(frame,0,29)
        # the code is slow enough, so it doesn't requires a delay
