from openhasp import Manager, Design, Page, Label, NavButtons, AnalogClock, defaultState2Color, ICON_THERMOMETER

if True:
    manager = Manager("plate_test", (800, 480))
    design = manager.design

    design.style.update(  {"page.gb_color":         "Gray",
                            "clock.color":          "Gold",
                            "text.color":           "Gold",
                        })

    Page(design, 1)
    clock = AnalogClock(design, 200, 200, 180)

    obj = Label(design, 500, 50, 100, 50, ICON_THERMOMETER, 50)
    obj = Label(design, 560, 50, 200, 50, "", 50)
    obj.linkText("number.temp_living")

    manager.sendDesign()
