import openhasp as oh
from openhasp import Manager
from openhasp.style1 import style as myStyle

def transformOnOff(design, value):
    if value == "on":
        return f"The light is ON #FFFF00 {oh.ICON_LIGHTBULB_ON}#"
    else:
        return f"The light is OFF {oh.ICON_LIGHTBULB}"
    
def transformTime(design, value):
    t = value.split(":")
    return f"{t[0]}h {t[1]}m"


class HaspDemo(Manager):

    def __init__(self, friendlyName, name, screenSize, mediaPlayer, lamp):
        self.Manager__init__(name, screenSize, keepHAState=True)   # Workaround as calling super() is not supported by pyscript

        self.friendlyName = friendlyName
        self.mediaPlayer = mediaPlayer
        self.lamp = lamp

        self.sendPeriodicHeatbeats()
        design = self.design
        design.updateStyle(myStyle)

        self.PAGE_LABELS    = 1
        self.PAGE_BUTTONS   = 2
        self.PAGE_CLOCKS    = 3
        self.PAGE_PLAYER    = 4
        self.PAGE_IMAGE     = 5

        #
        # Page: Labels
        #
        oh.Page(design, self.PAGE_LABELS)

        obj = oh.Label(design, (10,0), (460,40), f"OpenHasp Demo - {self.friendlyName}")
        obj.setBorder(width=2, radius=20, color="Red")

        oh.Label(design, (10,80), (460,40), "Text linked to Entity:", align="left")
        obj = oh.Label(design, (10,80), (460,40), "", align="right")
        obj.linkText("sensor.time") # linking the object text to a HA entity can also be done with buttons

        oh.Label(design, (10,120), (460,40), "Linked to transformed Entity:", align="left")
        obj = oh.Label(design, (10,120), (460,40), "", align="right")
        obj.linkText("sensor.time", transformTime) # linking the object text to a HA entity can also be done with buttons

        obj = oh.Label(design, (10,160), (460,40), "PUSH ME to change color", align="left")
        obj.actionOnPush(self.onChangeColor) # Calling a function when pushed can also be done with many other objects

        self.addNavbar()

        #
        # Page: Buttons, Switches and Sliders
        #
        oh.Page(design, self.PAGE_BUTTONS, startupPage=True)

        obj = oh.Label(design, (0,0), (480,40), "")
        obj.linkText(self.lamp, transformOnOff)

        oh.Label(design, (0,50), (200,40), "Switch:")
        oh.Switch(design, (200,50), (80,40), self.lamp)
        
        oh.Label(design, (0,100), (200,40), "On/Off Button:")
        obj = oh.OnOffButton(design, (200,100), (270,40), "On/Off", self.lamp)

        oh.Label(design, (0,150), (200,40), "Button")
        obj = oh.Button(design, (200,150), (270,40), "Call Toggle Serv.", self.lamp)
        obj.serviceOnPush("light", "toggle", entity_id=self.lamp)

        oh.Label(design, (0,200), (200,40), "Button")
        obj = oh.Button(design, (200,200), (270,40), "Call Func", self.lamp)
        obj.actionOnPush(self.onButtonPushed)

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

        #
        # Page: Player
        #
        oh.Page(design, self.PAGE_PLAYER)

        oh.MediaPlayer( design, 
                self.mediaPlayer, 
                (0,0), (480//2,270), 
                dispName=f"Player {self.friendlyName}",
                volumes = (4,8,20),
                sonosSleepTimer=False, 
                favoritesPage=None, 
                sonosTvMode=False,
                artwork = ((480//2+5,0), (480/2-5, 270)))

        self.addNavbar()


        #
        # Page: Image
        #
        oh.Page(design, self.PAGE_IMAGE)

        oh.Image(design, (0,0), (480,280), "https://cdn.pixabay.com/photo/2024/02/28/07/42/european-shorthair-8601492_1280.jpg")
        
        self.addNavbar()

        
    def addNavbar(self):
        oh.NavButtons(self.design, (480/5, 50), 32, (
            ("Label", self.PAGE_LABELS),
            (oh.ICON_LIGHTBULB, self.PAGE_BUTTONS),
            (oh.ICON_CLOCK_OUTLINE, self.PAGE_CLOCKS),
            (oh.ICON_MUSIC, self.PAGE_PLAYER),
            ("Img", self.PAGE_IMAGE)
            ))
        
    def onChangeColor(self, obj):
        color = obj.getTextColor() 
        if color == "Red":
            color = "Green"
        elif color == "Green":
            color = "Blue"
        else:
            color = "Red"
        obj.setTextColor(color)

    def onButtonPushed(self, obj):
        self.sendMsgBox("Function Called!", autoClose=2000)
        

# Create a HaspDemo manager for each plate defined in the psyscript config.yaml, see readme
managers = []
for appConf in pyscript.app_config:

    name = appConf["friendly_name"]
    plateName = appConf["plate_name"]
    resolution = (appConf["resolution_x"], appConf["resolution_y"])
    mediaPlayer = appConf["mediaplayer"]
    lamp = appConf["lamp"]

    log.info(f"Creating HaspDemo for '{plateName}'")
    
    manager = HaspDemo(name, plateName, resolution, mediaPlayer, lamp)
    managers.append(manager)
    manager.sendDesign()