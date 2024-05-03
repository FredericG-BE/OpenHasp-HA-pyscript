import openhasp as oh
import openhasp.mdi as mdi
from openhasp import Manager, ComposedObj
from openhasp.style1 import style as myStyle


class BambuLabPrinter(ComposedObj):
    def __init__(self, design, coord, size, printer):
        self.ComposedObj__init__(design)
        self.printer = printer

        self.camera = oh.Camera(design, (0,0), size, f"image.{printer}_camera")

        infoWindowCoord = (coord[0]+15, coord[1]+15)
        infoWindowSize = (size[0]-30, 150)
        # obj = oh.EmptyObj(design, infoWindowCoord, infoWindowSize)
        # obj.setParam("bg_opa", 60*255/100)
        # obj.setParam("bg_color", None, "page.gb_color")
        # obj.setBorder(self.design.style["btn.border_width"], self.design.style["btn.radius"], self.design.style["text.color"])

        x = infoWindowCoord[0] + 15
        y = infoWindowCoord[1]        

        self.camera = oh.Camera(design, (x,y+10), (130, 130), f"image.{printer}_cover_image")
        x += 150

        self.statusLabel = oh.Label(design, (coord[0]+size[0]/2-200, 10), (400, 50), "", align="center")
        self.statusLabel.setParam("bg_opa", 80*255/100)
        self.statusLabel.setParam("bg_color", None, "page.gb_color")
        self.statusLabel.setBorder(self.design.style["btn.border_width"], self.design.style["btn.radius"], self.design.style["text.color"])

        self.tf1 = oh.triggerFactory_entityChange(f"sensor.{printer}_current_stage", self._onStateChange, self.design.manager.instanceId)
        self.tf2 = oh.triggerFactory_entityChange(f"sensor.{printer}_print_progress", self._onStateChange, self.design.manager.instanceId)
        self._onStateChange(self.design.manager.instanceId) # Mimic a change so that the correct value is filled in


        #self.statusLabel.linkText(f"sensor.{printer}_current_stage")
        x += 150
        # obj = oh.Label(design, (x,y), (200,50), "Remaining:", align="left")
        # obj.linkText(f"sensor.{printer}_remaining_time")
        # x += 100
        # obj = oh.Label(design, (x,y), (300,50), "Layer:", align="left")
        # obj.linkText(f"sensor.{printer}_current_layer")
        # x += 100
        # obj = oh.Label(design, (x,y), (300,50), "End Time:", align="left")
        # obj.linkText(f"sensor.{printer}_end_time")
        r = infoWindowSize[1] / 2 * .8# obj = oh.EmptyObj(design, infoWindowCoord, infoWindowSize)
        c = (infoWindowCoord[0]+infoWindowSize[0]-20-r,infoWindowCoord[1]+infoWindowSize[1]/2) 
        bpr = r*1.1
        obj = oh.EmptyObj(design, (c[0]-bpr, c[1]-bpr), (2*bpr,2*bpr))
        obj.setParam("bg_opa", 80*255/100)
        obj.setParam("bg_color", None, "page.gb_color")
        obj.setBorder(self.design.style["btn.border_width"], bpr, self.design.style["text.color"])

        self.clock = oh.AnalogClock(design, c, r)
        readyTime = oh.AnalogClock.Indicator(f"sensor.{printer}_end_time", timeFormat="%Y-%m-%d %H:%M:%S", color="Red") 
        self.clock.addIndicator(readyTime)
        

    def _onStateChange(self, id):
        if not self.design.manager._checkInstanceId(id, "Printer StateChange"):
            return
        stage = state.get(f"sensor.{self.printer}_current_stage")
        # if stage == "auto_bed_leveling":
        #     stage = "Auto Leveling"
        # elif stage.find("preheating") >= 0:
        #     stage = "Preheating"
        # else:
        stage = stage.replace("_", " ")
        stage = stage[0].upper()+stage[1:]
        progress = state.get(f"sensor.{self.printer}_print_progress")
        self.statusLabel.setText(f"{stage} {progress}%")
        



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
