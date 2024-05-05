import openhasp as oh
import openhasp.mdi as mdi
from openhasp import Manager, ComposedObj, Obj
from openhasp.style1 import style as myStyle

import datetime
from homeassistant.util.dt import as_local


class Arc(Obj):
    def __init__(self, design, coord, size, min=0, max=100, value=50, rotation=0, color=None, adjustable=False, startAngle=None, endAngle=None, startAngle10=None, endAngle10=None):
        self.Obj__init__(design=design, type="arc", coord=coord, size=size)
        
        self.setParam("min", min)
        self.setParam("max", max)
        self.setParam("val", value)
        self.setParam("rotation", rotation)
        if adjustable is not None:
            self.setParam("adjustable", adjustable)
        if startAngle is not None:    
            self.setParam("start_angle", startAngle)
        if endAngle is not None:
            self.setParam("endAngle", endAngle)
        if startAngle10 is not None:
            self.setParam("start_angle10", startAngle10)
        if endAngle10 is not None:
            self.setParam("end_angle10", endAngle10)

        if color is not None:
            self.setParam("line_color10", color)

    def setValue(self, value):
        self.setParam("val", value)
        


class BambuLabPrinter(ComposedObj):
    def __init__(self, design, coord, size, printer):
        self.ComposedObj__init__(design)
        self.printer = printer

        self.camera = oh.Camera(design, coord, size, f"image.{printer}_camera")

        clockR = 70
        margin = 15
        y = coord[1] + margin
        
        self.coverImage = oh.Camera(design, (coord[0]+15, y), (clockR*2, clockR*2), f"image.{printer}_cover_image", refreshRateSec=None)

        self.statusLabel = oh.Label(design, (coord[0]+size[0]/2-200, 10), (400, 50), "", align="center")
        self.statusLabel.setParam("bg_opa", 80*255/100)
        self.statusLabel.setParam("bg_color", None, "page.gb_color")
        self.statusLabel.setBorder(self.design.style["btn.border_width"], self.design.style["btn.radius"], self.design.style["text.color"])
        
        # Clock backplate
        c = (coord[0] + size[0] - margin - clockR, y + clockR) 
        
        bpr = clockR
        obj = oh.EmptyObj(design, (c[0]-bpr, c[1]-bpr), (2*bpr,2*bpr))
        obj.setParam("bg_opa", 80*255/100)
        obj.setParam("bg_color", None, "page.gb_color")
        obj.setBorder(self.design.style["btn.border_width"], bpr, self.design.style["text.color"])

        # PrintTime Arc
        arcR = clockR // 2
        self.printTimeArc = Arc(design, (c[0]-arcR, c[1]-arcR), (2*arcR,2*arcR), rotation=-90, value=100, color="Red")
        self.printTimeArc.setHidden(True)

        # Clock
        self.clock = oh.AnalogClock(design, c, clockR*0.95)
        
        self.tf1 = oh.triggerFactory_entityChange(f"sensor.{printer}_current_stage", self._onStateChange, self.design.manager.instanceId)
        self.tf2 = oh.triggerFactory_entityChange(f"sensor.{printer}_print_progress", self._onStateChange, self.design.manager.instanceId)
        self.tf3 = oh.triggerFactory_entityChange(f"sensor.{printer}_start_time", self._onStateChange, self.design.manager.instanceId)
        self.tf3 = oh.triggerFactory_entityChange(f"sensor.{printer}_end_time", self._onStateChange, self.design.manager.instanceId)
        self._onStateChange(self.design.manager.instanceId) # Mimic a change so that the correct value is filled in        

    def _onStateChange(self, id):
        def time2Angle(dts, timeFormat):
            #try:
            dt = datetime.datetime.strptime(dts, timeFormat)
            dt = as_local(dt)
            h = dt.hour
            m = dt.minute
            # except:
            #     log.error(f"Failed to parse time '{dts}'")
            #     h = 0
            #     m = 0
            if h >= 12: 
                h -= 12
            return int((h+m/60)/12*360)

        if not self.design.manager._checkInstanceId(id, "Printer StateChange"):
            return
        
        stage = state.get(f"sensor.{self.printer}_current_stage") 
        
        # Set status label
        status = stage.replace("_", " ")
        status = status[0].upper()+status[1:]
        if stage == "printing":
            status += " " + state.get(f"sensor.{self.printer}_print_progress") + "%"
        self.statusLabel.setText(status)

        # Set start/end indicator
        if stage != "idle":
            startTimeAngle = time2Angle(state.get(f"sensor.{self.printer}_start_time"), timeFormat="%Y-%m-%d %H:%M:%S")
            endTimeAngle = time2Angle(state.get(f"sensor.{self.printer}_end_time"), timeFormat="%Y-%m-%d %H:%M:%S")
            self.printTimeArc.setParam("start_angle", startTimeAngle)
            self.printTimeArc.setParam("end_angle", endTimeAngle)
            self.printTimeArc.setHidden(False)
        else:
            self.printTimeArc.setHidden(True)
        
        self.coverImage.refresh()


class MyPlateManager(Manager):

    def __init__(self, friendlyName, name, screenSize, printer):
        self.Manager__init__(name, screenSize, keepHAState=True)   # Workaround as calling super() is not supported by pyscript

        self.friendlyName = friendlyName
        self.printer = printer

        self.sendPeriodicHeatbeats()
        design = self.design
        design.updateStyle(myStyle)

        oh.Page(design, 1)
        BambuLabPrinter(design, (0,0), screenSize, printer)


managers = [] # This needs to be global so that it remains in scope

@time_trigger("startup")
def main():
    global managers
    for appConf in pyscript.app_config:

        name = appConf["friendly_name"]
        plateName = appConf["plate_name"]
        resolution = (appConf["resolution_x"], appConf["resolution_y"])
        printer = appConf["printer"]
        
        manager = MyPlateManager(name, plateName, resolution, printer)
        managers.append(manager)
        manager.sendDesign()

