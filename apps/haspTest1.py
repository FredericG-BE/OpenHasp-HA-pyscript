import openhasp as oh
from openhasp.style3 import style as myStyle


def onTestMePushed(obj):
    log.info("TestMe pushed")
    input_number.demo.increment()


manager = oh.Manager("plate_test", (800, 480))
design = manager.design

design.updateStyle(myStyle)

oh.Page(design, 1)

obj = oh.Button(design, 10, 10, 200, 100, "TestMe", 50)
obj.actionOnPush(onTestMePushed)

obj = oh.Label(design, 250, 33, 200, 100, "NA", 50)
obj.linkText("input_number.demo")

obj = oh.Button(design, 10, 150, 400, 100, "Call Service", 50)
obj.serviceOnPush("light", "toggle", entity_id="light.bureau_rail")


manager.sendDesign()
