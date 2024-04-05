import openhasp as oh
import openhasp.style2 as myStyle # Or select another style

# Adapt the settings below
PLATE_NAME = "plate_testing"
PLATE_RESOLUTION = (480,320)
MY_LAMP_ENTITY = "light.bureau_spots"


# Create a manager for the plate
manager = oh.Manager(PLATE_NAME, PLATE_RESOLUTION)

# A manager has one design where will be add our object to. 
design = manager.design 

# Add a style to the design
design.updateStyle(myStyle.style)

# Add a page to the design
oh.Page(design, 1)

# Add a label to the design saying "Hello World!"
oh.Label(design, coord=(5,5), size=(235,50), text="Hello World!", align="left")

# Add a label that reflects the current time
obj = oh.Label(design, coord=(235,5), size=(235,50), text="Time goes here", align="right")
obj.linkText("sensor.time") # Link the label text to HA entity sensor.time 

# Add analog clock
oh.AnalogClock(design, center=(480/2,130), r=100, timeSource="sensor.time")

# Add a on/off button controlling a light
oh.OnOffButton(design, coord=(50,250), size=(380,60), text="Push me", entity=MY_LAMP_ENTITY, icon=oh.ICON_WALL_SCONCE)

# Send the design now (and also later when the plate would restart)
manager.sendDesign()

