import openhasp as oh
import openhasp.mdi as mdi
from openhasp import Manager, ComposedObj
from openhasp.style1 import style as myStyle

import datetime
from homeassistant.util.dt import as_local

class BambuLabPrinter(ComposedObj):
    def __init__(self, design, coord, size, printer, powerSwitch=None):
        self.ComposedObj__init__(design)
        self.printer = printer

        self.camera = oh.Camera(design, coord, size, f"image.{printer}_camera")

        # Calculate X-coordinates and x-sizes
        margin = 15
        y = coord[1] + margin
        powerButtonSize = 0 if powerSwitch is None else 1
        xsCover, xsPower, xsLight, xsStatus, xsClock = oh.spreadHorizontally(coord[0], size[0], (3,powerButtonSize,1,10,3), .25)

        # Cover image
        self.coverImage = oh.Camera(design, (xsCover[0], y), (xsCover[1], xsCover[1]), f"image.{printer}_cover_image", refreshRateSec=None)

        # Clock
        clockR = xsClock[1]//2
        c = (xsClock[0] + clockR, y + clockR)

        # Clock backplate  
        # TODO: This could become a feature of AnalogClock
        bpr = clockR
        obj = oh.EmptyObj(design, (c[0]-bpr, c[1]-bpr), (2*bpr,2*bpr))
        obj.setParam("bg_opa", 80*255/100)
        obj.setParam("bg_color", None, "page.gb_color")
        obj.setBorder(self.design.style["btn.border_width"], bpr, self.design.style["text.color"])

        # PrintTime Arc
        # TODO: also this could a feature of AnalogClock
        arcR = clockR // 2
        self.printTimeArc = oh.Arc(design, (c[0]-arcR, c[1]-arcR), (2*arcR,2*arcR), min=0, max=100, value=100, rotation = 270, color="Red")
        self.printTimeArc.setHidden(True)

        # The Analog Clock itself
        self.clock = oh.AnalogClock(design, c, clockR*0.95)

        # Buttons
        if powerSwitch is not None:
            self.powerIcon = oh.OnOffButton(design, (xsPower[0], y), (xsPower[1], 50), text=oh.ICON_POWER, entity=powerSwitch)
        self.lightIcon = oh.OnOffButton(design, (xsLight[0], y), (xsLight[1], 50), text=oh.ICON_LIGHTBULB, entity=f"light.{self.printer}_chamber_light")

        # Status label
        self.statusLabel = oh.Label(design, (xsStatus[0], y), (xsStatus[1], 50), "", align="left")
        self.statusLabel.setParam("bg_opa", 80*255/100)
        self.statusLabel.setParam("bg_color", None, "page.gb_color")
        self.statusLabel.setBorder(self.design.style["btn.border_width"], self.design.style["btn.radius"], self.design.style["text.color"])

        # Even triggers
        self.tf1 = oh.triggerFactory_entityChange(f"sensor.{printer}_current_stage", self._onStateChange, self.design.manager.instanceId)
        self.tf2 = oh.triggerFactory_entityChange(f"sensor.{printer}_print_progress", self._onStateChange, self.design.manager.instanceId)
        self.tf3 = oh.triggerFactory_entityChange(f"sensor.{printer}_start_time", self._onStateChange, self.design.manager.instanceId)
        self.tf3 = oh.triggerFactory_entityChange(f"sensor.{printer}_end_time", self._onStateChange, self.design.manager.instanceId)
        self._onStateChange(self.design.manager.instanceId) # Mimic a change so that the correct value is filled in

    def _onStateChange(self, id):
        def time2Angle(dts, timeFormat):
            dt = datetime.datetime.strptime(dts, timeFormat)
            dt = as_local(dt)
            h = dt.hour
            m = dt.minute
            if h >= 12:
                h -= 12
            a = int((h+m/60)/12*360)
            # log.info(f"{dts} ===>  {h}:{m}  ==> {a}")
            return a

        if not self.design.manager._checkInstanceId(id, "Printer StateChange"):
            return

        stage = state.get(f"sensor.{self.printer}_current_stage")

        # Set status label
        status = stage.replace("_", " ")
        status = status[0].upper()+status[1:]
        if stage == "printing":
            status += " " + state.get(f"sensor.{self.printer}_print_progress") + "%"
        self.statusLabel.setText(" "+status)

        # Set start/end indicator
        if stage not in ("idle", "offline"):
            startTimeAngle = time2Angle(state.get(f"sensor.{self.printer}_start_time"), timeFormat="%Y-%m-%d %H:%M:%S")
            endTimeAngle = time2Angle(state.get(f"sensor.{self.printer}_end_time"), timeFormat="%Y-%m-%d %H:%M:%S")
            self.printTimeArc.setAngles(startTimeAngle, endTimeAngle)
            self.printTimeArc.setHidden(False)
        else:
            self.printTimeArc.setHidden(True)

        self.coverImage.refresh()



class MyPlateManager(Manager):

    def __init__(self, friendlyName, name, screenSize, printer, powerSwitch=None):
        self.Manager__init__(name, screenSize, keepHAState=True)   # Workaround as calling super() is not supported by pyscript

        self.friendlyName = friendlyName
        self.printer = printer

        self.sendPeriodicHeatbeats()
        design = self.design
        design.updateStyle(myStyle)

        oh.Page(design, 1)
        BambuLabPrinter(design, (0,0), screenSize, printer, powerSwitch)


managers = [] # This needs to be global so that it remains in scope

@time_trigger("startup")
def main():
    global managers
    for appConf in pyscript.app_config:

        name = appConf["friendly_name"]
        plateName = appConf["plate_name"]
        resolution = (appConf["resolution_x"], appConf["resolution_y"])
        printer = appConf["printer"]
        powerSwitch = appConf.get("power_switch", None)

        manager = MyPlateManager(name, plateName, resolution, printer, powerSwitch)
        managers.append(manager)
        manager.sendDesign()
