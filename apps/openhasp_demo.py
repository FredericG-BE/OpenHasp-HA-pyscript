import openhasp as oh
from openhasp import Manager
from openhasp.style1 import style as myStyle

# Adapt the settings below
MY_LAMP_ENTITY = "light.bureau_spots"


def transformOnOff(design, value):
    if value == "on":
        return f"The light is ON #FFFF00 {oh.ICON_LIGHTBULB_ON}#"
    else:
        return f"The light is OFF {oh.ICON_LIGHTBULB}"

class HaspDemo(Manager):

    def __init__(self, name, screenSize):
        self.Manager__init__(name, screenSize, keepHAState=True)   # Workaround as calling super() is not supported by pyscript

        self.sendPeriodicHeatbeats()
        design = self.design
        design.updateStyle(myStyle)

        self.PAGE_BUTTONS    = 1
        self.PAGE_CLOCKS     = 2

        #
        # Page: Buttons, Switches and Sliders
        #
        oh.Page(design, self.PAGE_BUTTONS, startupPage=True)

        obj = oh.Label(design, (0,0), (480/2,40), "OpenHasp Demo")
        obj.setBorder(width=2, radius=20, color="Red")

        obj = oh.Label(design, (480/2,0), (480/2,40), "The light is:")
        obj.linkText(MY_LAMP_ENTITY, transformOnOff)

        oh.Label(design, (0,50), (200,40), "Switch:")
        oh.Switch(design, (200,50), (200,40), MY_LAMP_ENTITY)
        
        oh.Label(design, (0,100), (200,40), "On/Off Button:")
        oh.OnOffButton(design, (200,100), (200,40), "Push me", MY_LAMP_ENTITY)

        oh.Label(design, (0,150), (200,40), "Button")
        obj = oh.Button(design, (200,150), (200,40), "CallService", MY_LAMP_ENTITY)
        obj.serviceOnPush("light", "toggle", entity_id=MY_LAMP_ENTITY)

        self.addNavbar()
        
        #
        # Page: Clocks
        #
        oh.Page(design, self.PAGE_CLOCKS)

        oh.AnalogClock(design, (480/2, 110), 100, timeSource="sensor.time")

        oh.Label(design, (20,110), (100,40), "Sunrise")
        oh.AnalogClock(design, (70,200), 50, timeSource="sun.sun.next_rising", timeFormat="%Y-%m-%dT%H:%M:%S.%f%z")
        
        oh.Label(design, (360,110), (100,40), "Sunset")
        oh.AnalogClock(design, (410,200), 50, timeSource="sun.sun.next_setting", timeFormat="%Y-%m-%dT%H:%M:%S.%f%z")
        
        self.addNavbar()

        
    def addNavbar(self):
        oh.NavButtons(self.design, (480/5, 50), 32, (
            (oh.ICON_LIGHTBULB, self.PAGE_BUTTONS),
            (oh.ICON_CLOCK_OUTLINE, self.PAGE_CLOCKS),
            ))
        

# Create a HaspDemo manager for each plate defined in the psyscript config.yaml
managers = []
for appConf in pyscript.app_config:
    plateName = appConf["plate_name"]
    log.info(f"Creating HaspDemo for '{plateName}'")
    manager = HaspDemo(plateName, (480,320))
    managers.append(manager)
    manager.sendDesign()