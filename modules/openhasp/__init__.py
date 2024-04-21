import json
import math
import time
import re
import datetime

from homeassistant.util.dt import as_local
from homeassistant.helpers.network import get_url

from . import imageHandling

ICON_CHECK = "\uE12C"
ICON_CLOCK_OUTLINE = "\uE150"
ICON_THERMOMETER = "\uE50F"
ICON_POWERPLUG = "\uE6A5"
ICON_LIGHTBULB = "\uE335"
ICON_LIGHTBULB_ON = "\uE6E8"
ICON_WALL_SCONCE = "\uE91C"
ICON_SPREAKER = "\uE4C3"
ICON_HOME = "\uE2DC"
ICON_HOME_OUTLINE = "\uE6A1"
ICON_TIMER_OUTLINE = "\uE150"
ICON_MUSIC = "\uE75A"
ICON_LIGHTNING_BOLT = "\uF40B"
ICON_BLINDS = "\uE0AC"
ICON_CLOSE = "\uE156"
ICON_VOLUME_MEDIUM = "\uE580"
ICON_VOLUME_HIGH = "\uE57E"
ICON_SKIP_PREVIOUS = "\uE4AE"
ICON_SKIP_NEXT = "\uE4AD"
ICON_PLAY = "\uE40A"
ICON_PAUSE = "\uE3E4"
ICON_POWER = "\uE425"
ICON_LAMP = "\uE6B5"
ICON_SILVERWARE_FORK_KNIFE = "\uEA70"
ICON_COFFEE = "\uE176"
ICON_TELEVISION = "\uE502"
ICON_CCTV = "\uE7AE"
ICON_RECYCLE_VARIANT = "\uF39D"
ICON_LEAF = "\uE32A"

logEntityEvents = False
logMqttEvents = False
logDiscovery = True
logOnline = True
logSendDesign = True
logSendDesignDetail = False
logStaleMessages = False
logImageHandling = False
logVisible = True

screenName2manager = {}

class Link(object):
    pass

class Obj():

    def __init__(self, design, coord=None, size=None, extraPar=None):
        self.Obj__init__(design, "Obj", coord, size, extraPar)

    def Obj__init__(self, design, type=None, coord=None, size=None, extraPar=None):
        self.design = design
        self.type = type
        self.params = {}
        if type is not None:
            self.params["obj"] = type
        if extraPar is not None:
            self.params.update(extraPar)
        #assert isInstance(design, Design)
        self.sent = False # not sent to the device yet

        self.links = []

        if coord is not None:
            self.setCoord(coord)
        if size is not None:
            self.setSize(size)


        # Add this object to the design, page and ID will be added there
        self.design.addObj(self)

    def getpb(self):
        return f"p{self.params['page']}b{self.params['id']}"
    
    def setCoord(self, coord):
        self.setParam("x", int(coord[0]))
        self.setParam("y", int(coord[1]))

    def setSize(self, size):
        self.setParam("w", int(size[0]))
        self.setParam("h", int(size[1]))

    def setFont(self, font):
        self.setParam("text_font", font, "text.font")

    def setHidden(self, hidden):
        self.setParam("hidden", "1" if hidden else "0")

    def setClipCorner(self):
        self.setParam("clip_corner", 1)

    def setParent(self, parent):
        self.setParam("parentid", parent.params['id'])

    def setShadow(self, shadow, objType):
        if shadow is None:
            shadow = self.design.style.get(objType+".shadow", None)

        if shadow is not None:
            self.setParam("shadow_color", shadow[0])
            self.setParam("shadow_opa", shadow[1]) 
            self.setParam("shadow_width", shadow[2])
            self.setParam("shadow_ofs_x", shadow[3][0])
            self.setParam("shadow_ofs_y", shadow[3][1])    

    def setBorder(self, width, radius, color=None):
        self.setParam("border_width", width)
        self.setParam("radius", radius)
        if color is not None:
            self.setParam("border_color", color)    

    def setParam(self, param, value, styleName=None):
        if value is None:
            # No value provided... can it be found in the style?
            value = self.design.style.get(styleName, None)
        if value is None:
            raise Exception(f"Cannot set Param {param}")
        self.params[param] = value
        if self.sent:
            if param == "text":
                # Send all parameters so that text is passed as json 
                self.send()
            else:
                # only update the one parameter that has changed
                self.design.manager.sendCmd(f"{self.getpb()}.{param}", value)

    def getJsonl(self):
        return json.dumps(self.params)

    def send(self):
        self.design.manager.sendCmd("jsonl", self.getJsonl())
        self.sent = True

    def toggleOnPush(self, entity):
        self.toggleOnPushEntity = entity

    def actionOnPush(self, func):
        self.actionOnPushFunc = func

    def serviceOnPush(self, domain, name, **kvargs):
        self.serviceOnPushInfo = (domain, name, kvargs)

    def actionOnVal(self, func):
        self.actionOnValFunc = func

    def onStateMsg(self, topic, payload):
        # Handling an MQTT state update for this object
        payload = json.loads(payload)
        try:
            event = payload["event"]
        except KeyError:
            pass
        else:
            if event == "down":
                if hasattr(self, "toggleOnPushEntity"):
                    domain, name = self.toggleOnPushEntity.split(".")
                    service.call(domain, "toggle", entity_id=self.toggleOnPushEntity)

                if hasattr(self, "actionOnPushFunc"):
                    self.actionOnPushFunc(self)

                if hasattr(self, "serviceOnPushInfo"):
                    log.info(f"self.serviceOnPush: {self.serviceOnPushInfo}")
                    service.call(self.serviceOnPushInfo[0], self.serviceOnPushInfo[1], **self.serviceOnPushInfo[2])
            
            elif event == "up":
                try:
                    val = payload["val"]
                except KeyError:
                    pass
                else:
                    if hasattr(self, "actionOnValFunc"):  
                        self.actionOnValFunc(self, val)  

    def _onEntityChange(self, cookie):
        link = cookie
        if not self.design.manager._checkInstanceId(link.instanceId, f"EntityChange {link.entity}"):
            return
        # An entity linked to this object has changed
        if logEntityEvents: log.info(f"_onEntityChange self={self} link={link}")
        try:
            value = state.get(link.entity)
        except AttributeError:
            log.warning(f"Failure to read {link.entity}")
            value = ""
        if link.transform is not None:
            value = link.transform(self.design, value)
        self.setParam(link.param, value)

    # FIXME?: unify _onEntityChange and _onEntityAttrChange?
    def _onEntityAttrChange(self, cookie):
        link = cookie
        if not self.design.manager._checkInstanceId(link.instanceId, f"EntityChange {link.entity}"):
            return
        # An entity linked to this object has changed
        if logEntityEvents: log.info(f"_onEntityAttrChange self={self} link={link}")
        try:
            value = state.getattr(link.entity)[link.entityAttr]
        except (AttributeError, KeyError):
            log.warning(f"Failure to read {link.entity}.{link.entityAttr}")
            value = ""
        if link.transform is not None:
            value = link.transform(self.design, value)
        # log.info(f"EntityChange {value}") 
        self.setParam(link.param, value)

class Page(Obj):

    def __init__(self, design, pageNbr, isStartupPage=False, extraPar=None):
        self.pageNbr = pageNbr # Obj__init__ will register the page and the page number needs to be known, would be better if the constructors would not register immediately 
        self.Obj__init__(design=design, type=None, extraPar=None) # Will add the page to the design
        self.params["page"] = pageNbr
        self.setParam("bg_color", None, "page.gb_color")

        self.isStartupPage = isStartupPage
        self.objs = []
        self.composedObjs = []

        if isStartupPage:
            self.design.manager.startupPage = pageNbr

    def addObj(self, obj):
        obj.setParam("page", self.pageNbr)
        id = len(self.objs) + 1
        assert id <= 255, "Too many objects on same page"
        obj.setParam("id", id)
        #self.pbs[f"p{obj.params['page']}b{obj.params['id']}"] = obj

        self.objs.append(obj)
        return obj
    
    def registerComposedObj(self, composedObj):
        self.composedObjs.append(composedObj)   
    
    def onVisible(self, visible):
        if logVisible: log.info(f"Page {self.pageNbr} visible:{visible}")
        for obj in self.composedObjs: # Native objs don't get the onVisible 
            obj.onVisible(visible)


class EmptyObj(Obj):

    def __init__(self, design, coord, size, extraPar=None):
        self.Obj__init__(design=design, type="Obj", coord=coord, size=size, extraPar = extraPar)
        self.setParam("bg_opa", 0)
        self.setParam("border_side", 0)


class Label(Obj):

    def __init__(self, design, coord, size, text, font=None, textColor=None, align=None, mode=None, extraPar=None):
        self.Label__init__(design, coord, size, text, font, textColor, align, mode, extraPar)

    def Label__init__(self, design, coord, size, text, font=None, textColor=None, align=None, mode=None, extraPar=None):
        self.Obj__init__(design=design, type="label", size=size, coord=coord, extraPar=extraPar)
        self.params["text"] = text
        self.setParam("text_font", font, "text.font")
        self.setParam("text_color", textColor, "text.color")
        self.setParam("align", align, "text.align")

        if mode is not None:
            self.setParam("mode", mode)

        self.font = font

    def setText(self, value):
        self.setParam("text", value)

    def getText(self):
        return self.params["text"]

    def setTextColor(self, color):
         self.setParam("text_color", color)

    def getTextColor(self):
        return self.params["text_color"]

    def linkText(self, entity, transform=None):
        link = Link()
        link.entity = entity
        link.param = "text"
        link.transform = transform
        link.instanceId = self.design.manager.instanceId
        link.trigger = triggerFactory_entityChange(entity, self._onEntityChange, link)
        self.links.append(link)
        self._onEntityChange(link) # Mimic a change so that the correct value is filled in

    def linkColor(self, entity, param="text_color", transform=None):
        link = Link()
        link.entity = entity
        link.param = param
        link.transform = transform
        link.instanceId = self.design.manager.instanceId
        link.trigger = triggerFactory_entityChange(entity, self._onEntityChange, link)
        self.links.append(link)
        self._onEntityChange(link) # Mimic a change so that the correct value is filled in


class Button(Label):
    def __init__(self, design, coord, size, text, font=None, align=None, extraPar=None):
        self.Button__init__(design, coord, size, text, font, align, extraPar)

    def Button__init__(self, design, coord, size, text, font=None, align=None, extraPar=None):
        self.Label__init__(design=design, coord=coord, size=size, text=text, font=font, align=align, extraPar=extraPar)
        self.params["obj"] = "btn"

        self.setParam("text_font", font, "btn.font")
        self.setParam("text_color", None, "btn.text_color")
        self.setParam("align", align, "btn.align")
        self.setParam("bg_color", None, "btn.bg_color")
        self.setParam("radius", None, "btn.radius")
        self.setParam("border_color", None, "btn.border_color")
        self.setParam("border_width", None, "btn.border_width")

        self.setShadow(None, "btn")


    def addIcon(self, icon, x, y):
        self.setParam("value_str", icon)
        self.setParam("value_font", None, "btn.icon.font")
        self.setParam("value_ofs_x", x)
        self.setParam("value_ofs_y", y)
        self.setParam("value_color", None, "btn.text_color")


class OnOffButton(Button):
    def __init__(self, design, coord, size, text, entity, font=None, icon=None, align=None, extraPar=None):
        self.Button__init__(design=design, coord=coord, size=size, text=text, font=font, align=align, extraPar=extraPar)
        self.entity = entity

        font = self.params["text_font"]
        if icon is not None:
            self.addIcon(icon, -size[0]//2+font, 0)
        self.linkColor(entity, param="bg_color", transform=defaultState2ButtonColor)
        self.toggleOnPush(entity)


class Line(Obj):
    def __init__(self, design, points, width=None, color=None, extraPar=None):
        self.Obj__init__(design=design, type="line", extraPar=extraPar)
        self.setPoints(points)

        self.setParam("line_width", width, "line.width")
        self.setParam("line_color", color, "line.color")

    def setPoints(self, points):
        self.setParam("points", "[" + ",".join([f"[{a},{b}]" for a,b in points]) + "]")


class Image(Obj):
    def __init__(self, design, coord, size=None, src=None, resize=False, center=True):
        self.Obj__init__(design=design, type="img", coord=coord, size=size)
        self.size = size
        self.coord = coord
        self.resize = resize
        self.center = center
        self.lastLocalPrepSrc = None
        if src is not None:
            self.setSrc(src)

    def setSrc(self, src):
        coord = self.coord # This is where the image source needs to be, will have to be changed if image needs to be zoomed
        prepLocalSrc, prepPublicSrc, prepSize = imageHandling.prepareImage( src, 
                                                        namePrefix=self.design.manager.name, 
                                                        canvasSize=self.size, 
                                                        resize=self.resize)
        if logImageHandling: log.info(f"Image prepared src=\"{prepPublicSrc}\" size=\"{prepSize}\"")
        if self.center:
            # self.size is the canvas, prepPublicSrc is the size of the prepared image
            newCoord = (coord[0] + (self.size[0]-prepSize[0])//2, coord[1] + (self.size[1]-prepSize[1])//2) 
        else:
            newCoord = coord
        self.setCoord(newCoord)
        self.setParam("src", prepPublicSrc)

        # Delete old file?
        if self.lastLocalPrepSrc is not None:
            r, e = imageHandling.deleteFile(self.lastLocalPrepSrc)
            if r:
                if logImageHandling: log.info(f"Removed temp file \"{self.lastLocalPrepSrc}\"")
            else:
                if logImageHandling: log.info(f"FAILED to Remove temp file \"{self.lastLocalPrepSrc}\" {e}")
        self.lastLocalPrepSrc = prepLocalSrc    

class Switch(Obj):
    def __init__(self, design, coord, size, entity=None):
        self.Obj__init__(design=design, type="switch", size=size, coord=coord)
        
        self.setParam("border_color", None, "switch.border_color")
        self.setParam("bg_color00", None, "switch.off.bg_color")  
        self.setParam("bg_color10", None, "switch.on.bg_color")
        self.setParam("bg_color20", None, "switch.knob_color")

        if entity is not None:
            self.linkEntity(entity)

    def linkEntity(self, entity):
        self.entity = entity

        # Entity On/Off state => Button Val
        link = Link()
        link.entity = entity
        link.param = "val"
        link.transform = onOff2Val
        link.instanceId = self.design.manager.instanceId
        link.trigger = triggerFactory_entityChange(entity, self._onEntityChange, link)
        self.links.append(link)
        self._onEntityChange(link) # Mimic a change so that the correct value is filled in
    
        # Button Val => Entity On/Off
        self.actionOnVal(self._onVal)

    def _onVal(self, obj, val):
        service.call("homeassistant","turn_on" if val==1 else "turn_off", entity_id=self.entity)

class Slider(Obj):
    def __init__(self, design, coord, size, entityBrightness=None, adaptColorTemp=False):
        self.Obj__init__(design=design, type="slider")
        self.setCoord(coord)
        self.setSize(size)
        
        self.setParam("border_color", None, "slider.border_color")
        self.setParam("bg_color00", None, "slider.off.bg_color")  
        self.setParam("bg_color10", None, "slider.on.bg_color")
        self.setParam("bg_color20", None, "slider.knob_color")
        self.setParam("radius", None, "slider.radius")

        self.setShadow(None, "slider")

        if entityBrightness is not None:
            self.linkEntityBrightness(entityBrightness, adaptColorTemp)  
         
    def linkEntityBrightness(self, entity, adaptColorTemp=False):
        self.entity = entity
        self.adaptColorTemp = adaptColorTemp

        # Slider state => Button Val
        link = Link()
        link.entity = entity
        link.entityAttr = "brightness"
        link.param = "val"
        link.transform = brightness2Val
        link.instanceId = self.design.manager.instanceId
        link.trigger = triggerFactory_entityAttrChange(link.entity, link.entityAttr, self._onEntityAttrChange, link)
        self.links.append(link)
        self._onEntityAttrChange(link) # Mimic a change so that the correct value is filled in
    
        # Slider Val => Entity brightness
        self.actionOnVal(self._onVal)

    def _onVal(self, obj, val):
        log.info(f"setting dimmer {val}")
        if val > 0:
            args = {}
            args["brightness"] = int(val*255/100)
            if self.adaptColorTemp:
                args["color_temp"] = 600 - val*5 
            log.info(args)
            service.call("homeassistant","turn_on", entity_id=self.entity, **args)
        else:
            service.call("homeassistant","turn_off", entity_id=self.entity)

class Design():
    def __init__(self, manager, screenSize, style=None):
        self.manager = manager
        self.screenSize = screenSize
        self.id = 1
        self.lastPageAdded = None
        self.style = style if style is not None else {}
        self.screenBackgroundColor = "Black"

        self.pages = {}
        self.otherObjs = [] # Objects that are no HAPS objects but for which a reference needs to be kept
        self.timeTickObjs = [] # objects that need a timertick
        self.currPageNbr = None    # The page that is being displayed

    def updateStyle(self, style):
        self.style.update(style)

    def addPage(self, page):
        assert type(page) == Page
        self.lastPageAdded = page
        self.pages[page.pageNbr] = page  
        return page

    def addObj(self, obj):
        if type(obj) == Page:
            return self.addPage(obj)
        else:
            # The object is added to the page that was last defined
            return self.lastPageAdded.addObj(obj)
        
    def registerComposedObj(self, composedObj):
        # The object is added to the page that was last defined
        return self.lastPageAdded.registerComposedObj(composedObj)
    
    def registerForTimerTick(self, obj):
        self.timeTickObjs.append(obj)

    def onTimerTick(self):
        for obj in self.timeTickObjs:
            obj.onTimerTick()

    def pageChanged(self, pageNbr):
        if self.currPageNbr is not None:
            if pageNbr != self.currPageNbr:
                self.pages[self.currPageNbr].onVisible(False)
        self.currPageNbr = pageNbr
        self.pages[self.currPageNbr].onVisible(True)


class ComposedObj():
    def __init__(self, design):
        self.ComposedObj__init__(design)

    def ComposedObj__init__(self, design):
        self.design = design
        design.registerComposedObj(self)

    def onVisible(self, visisble):
        pass


class NavButtons(ComposedObj):
    def __init__(self, design, size, tabs, font=None):
        self.ComposedObj__init__(design)

        dx = (design.screenSize[0] - size[0]*(len(tabs))) // len(tabs)
        y = design.screenSize[1] - size[1] - 5
        x = dx // 2
        currPageNbr = design.lastPageAdded.pageNbr
        for tab in tabs:
            obj = Button(design, (x, y), size, tab[0])
            obj.setParam("text_color", design.style["nav.active.text_color" if tab[1] == currPageNbr else "nav.text_color"])
            obj.setParam("bg_color", design.style["nav.active.bg_color" if tab[1] == currPageNbr else "nav.bg_color"])
            obj.setParam("text_font", font, "nav.font")
            obj.actionOnPush(self._onPush)
            obj.pageToGo = tab[1]
            x += size[0] + dx

    def _onPush(self, obj):
        obj.design.manager.gotoPage(obj.pageToGo)


class Camera(ComposedObj):
    def __init__(self, design, coord, size, camera, refreshRateSec=5):
        self.ComposedObj__init__(design)        
        self.camera = camera
        self.refreshRateSec = refreshRateSec
        self.refreshActive = False
        
        self.image = Image(design, coord, size)
        self.image.setHidden(True)

        design.registerForTimerTick(self)

    def startRefreshing(self):
        self.image.setHidden(False)
        self.refresh()
        self.refreshCountDown = self.refreshRateSec 
        self.refreshActive = True

    def stopRefreshing(self): 
        self.image.setHidden(True)
        self.refreshActive = False

    def onVisible(self, visible):
        if logVisible: log.info(f"Camera {self.camera} Visible:{visible}")
        if visible:
            self.startRefreshing()
        else:
            self.stopRefreshing()

    def onTimerTick(self):
        if self.refreshActive:
            self.refreshCountDown -= 1
            if self.refreshCountDown == 0:
                self.refresh()
                self.refreshCountDown = self.refreshRateSec 

    def refresh(self):
        # log.info("Camera Refresh")
        cameraEntityAttr = state.getattr(self.camera)
        src = get_url(hass, allow_external=False)+cameraEntityAttr["entity_picture"]
        self.image.setSrc(src)


class MediaArtwork(ComposedObj):
    def __init__(self, design, player, coord, size):
        self.ComposedObj__init__(design)
        self.player = player
        self.coord = coord
        self.size = size

        self.imageObj = Image(design, coord, size, center=True)
        self.imageObj.setBorder(self.design.style["btn.border_width"], self.design.style["btn.radius"], self.design.style["btn.border_color"])
        self.imageObj.setClipCorner()
        self.imageObj.setHidden(True)

        self.playerStateTf = triggerFactory_entityChange(player+".entity_picture", self._onChange, self.design.manager.instanceId)
        self._onChange(self.design.manager.instanceId) # Mimic a change so that the correct value is filled in

        self.design.otherObjs.append(self) # Keep a reference to this object to keep the references to the trigger functions

    def _onChange(self, id):
        if not self.design.manager._checkInstanceId(id, "MediaArtwork Change"):
            return
        try:
            entity_picture = state.getattr(self.player)["entity_picture"]
        except KeyError:
            self.imageObj.setHidden(True)
        else:
            self.imageObj.setSrc(get_url(hass, allow_external=False)+entity_picture)
            self.imageObj.setHidden(False)


class MediaSourceInfo(ComposedObj):
    def __init__(self, design, player, coord, size, audioFormat=None, font=None):
        self.ComposedObj__init__(design)
        self.player = player
        self.audioFormat = audioFormat

        self.sourceInfo = Label(design, coord, size, text="", font=font)
        self.sourceInfo.setBorder(self.design.style["btn.border_width"], self.design.style["btn.radius"], self.design.style["text.color"])
        self.sourceInfo.setHidden(True)

        self.playerSourceIf = triggerFactory_entityChange(player+".source", self._onSourceChange, self.design.manager.instanceId)
        if audioFormat is not None:
            self.audioFormatIf = triggerFactory_entityChange(audioFormat, self._onSourceChange, self.design.manager.instanceId)
        self._onSourceChange(self.design.manager.instanceId) # Mimic a change so that the correct value is filled in

        self.design.otherObjs.append(self) # Keep a reference to this object to keep the references to the trigger functions

    def _onSourceChange(self, id):
        if not self.design.manager._checkInstanceId(id, "MediaArtwork Change"):
            return
        source = state.getattr(self.player).get("source", None)

        sourceInfo = ""

        if source is not None:
            sourceInfo = source
            if source == "TV":
                if self.audioFormat is not None:
                    format = state.get(self.audioFormat)
                    newFormat = ""
                    if format.find("No input") >= 0: 
                        newFormat = "No Input"
                    elif format.find("Atmos") >= 0: 
                        newFormat = "Dolby Atmos"
                    elif format.find("Dolby") >= 0: 
                        newFormat = "Dolby"
                        if format.find("5.1") >= 0: 
                            newFormat += " 5.1"
                        elif format.find("2.0") >= 0: 
                            newFormat += " 2.0"
                    elif format.find("PCM") >= 0: 
                        newFormat = "PCM"
                        if format.find("5.1") >= 0: 
                            newFormat += " 5.1"
                        elif format.find("2.0") >= 0: 
                            newFormat += " 2.0"
                    else: newFormat = format
                    
                    #format = state.get(self.audioFormat)
                    sourceInfo += "\n" + newFormat
            self.sourceInfo.setText(sourceInfo)
            self.sourceInfo.setHidden(False)
        else:
            self.sourceInfo.setHidden(True)

class MediaPlayer(ComposedObj):
    def __init__(   self, 
                    design, 
                    player, 
                    coord, 
                    size, 
                    dispName=None, 
                    volumes=None, 
                    sonosSleepTimer=False, 
                    sonosTvMode=False, 
                    favoritesPage=None, 
                    artwork=None, 
                    sourceInfo=None):
        
        self.ComposedObj__init__(design)
        self.player = player
        self.favoritesPage = favoritesPage

        font = None # TODO

        x,y = coord
        h = 50
        dx = (size[0] // 50) + 1 # space between the buttons
        dy = 60

        yTotal = 2*dy # media title + main buttons
        if dispName is not None: yTotal += dy
        if volumes is not None: yTotal += dy
        if sonosSleepTimer or favoritesPage is not None or sonosTvMode: yTotal += dy
            
        if size[1] > yTotal:   
            y += (size[1] - yTotal) // 2 # center vertically
        else:
            log.error("Media player needs more room than provided")
        
        if artwork is not None:
            self.artwork = MediaArtwork(design, player, *artwork)
        if sourceInfo is not None:
            self.artwork = MediaSourceInfo(design, player, *sourceInfo)

        if dispName is not None:
            obj = Label(design, (x, y), (size[0], h), text=dispName, align="center")
            y += dy

        # Media title
        obj = Label(design, (x, y), (size[0], h), "",) # mode="loop")
        obj.setBorder(self.design.style["btn.border_width"], self.design.style["btn.radius"], self.design.style["text.color"])
        obj.setClipCorner()
        obj.linkText(player+".media_title")

        # Volumes
        if volumes is not None:
            y += dy
            w = (size[0] - (len(volumes)-1)*dx) // len(volumes)
            x = coord[0]
            for volume in volumes:
                obj = Button(design, (x, y), (w, h), text=ICON_VOLUME_HIGH + f" {volume}%", font=font)
                obj.volume = volume
                obj.player = player
                obj.actionOnPush(self._onVolumePush) # FIXME: can we not just use obj.serviceOnPush() iso of calling a function?
                x += w + dx

        # Main Buttons
        y += dy
        nbButtons = 5
        w = (size[0] - (nbButtons-1)*dx) // nbButtons
        x = coord[0]
        
        obj = Button(design, (x, y), (w, h), text=ICON_VOLUME_MEDIUM, font=font)
        obj.serviceOnPush("media_player", "volume_down", entity_id=player)
        x += w + dx

        obj = Button(design, (x, y), (w, h), text=ICON_SKIP_PREVIOUS, font=font)
        obj.serviceOnPush("media_player", "media_previous_track", entity_id=player)
        x += w + dx

        obj = Button(design, (x, y), (w, h), text=ICON_PLAY, font=font)
        obj.serviceOnPush("media_player", "media_play_pause", entity_id=player)
        obj.linkText(player, self._playerState2Icon)
        x += w + dx

        obj = Button(design, (x, y), (w, h), text=ICON_SKIP_NEXT, font=font)
        obj.serviceOnPush("media_player", "media_next_track", entity_id=player)
        x += w + dx

        obj = Button(design, (x, y), (w, h), text=ICON_VOLUME_HIGH, font=font)
        obj.serviceOnPush("media_player", "volume_up", entity_id=player)
        x += w + dx

        # Buttons: sleep, favorites, TV 
        if sonosSleepTimer or favoritesPage is not None or sonosTvMode:
            nbButtons = 1
            if sonosSleepTimer:
                nbButtons += 2
            if sonosTvMode:
                nbButtons += 1
            w = (size[0] - ((nbButtons-1)*dx)) // nbButtons
            x = coord[0]
            y += dy

            if sonosSleepTimer:
                obj = Button(design, (x, y), (w, h), "Sleep 15'", font=font)
                obj.serviceOnPush("sonos", "SET_SLEEP_TIMER", entity_id=player, sleep_time=15*60)
                x += w + dx

                obj = Button(design, (x, y), (w, h), "Sleep 30'", font=font)
                obj.serviceOnPush("sonos", "SET_SLEEP_TIMER", entity_id=player, sleep_time=30*60)
                x += w + dx

            if favoritesPage is not None:
                obj = Button(design, (x, y), (w, h), ICON_MUSIC, font=font)
                obj.page = favoritesPage
                obj.actionOnPush(self._onFavPush)
                x += w + dx
            
            if sonosTvMode:
                obj = Button(design, (x, y), (w, h), ICON_TELEVISION, font=font)
                obj.serviceOnPush("media_player", "select_source", entity_id=player, source="TV")
                x += w + dx

    def _playerState2Icon(self, design, value):
        if value == "playing":
            return ICON_PAUSE
        else:
            return ICON_PLAY

    def _onFavPush(self, obj):
        obj.design.manager.gotoPage(obj.page)

    def _onVolumePush(self, obj):
        service.call("media_player", "volume_set", entity_id=obj.player, volume_level=obj.volume/100)


class SonosFavorites(ComposedObj):
    def __init__(self, design, player, coord, size, favList, returnPage):
        self.ComposedObj__init__(design)
        self.returnPage = returnPage
        self.favList = favList
        self.player = player

        x,y = coord
        font = None
        h = 60
        dy = 70
        dx = 10 # space between the buttons
        favPerRow = 3
        w = (size[0] - (favPerRow-1)*dx) // favPerRow
        rowCnt = 1

        for favShortName in favList:
            obj = Button(design, (x, y), (w, h), favShortName, font=font) 
            obj.favObj = self
            obj.actionOnPush(self._onFavPushed)
            x += w + dx
            rowCnt += 1
            if rowCnt > favPerRow:
                y += dy
                x = coord[0]
                rowCnt = 1
        obj = Button(design, (x, y), (w, h), ICON_CHECK, font=font)
        obj.page = returnPage
        obj.actionOnPush(self._onDonePush)

    def _onFavPushed(self, obj):
        favShortName = obj.getText()
        log.info(f"Fav shortName {favShortName}")

        favName = obj.favObj.favList[favShortName]
        log.info(f"Fav Name {favName}")

        for id, name in state.getattr("sensor.sonos_favorites")["items"].items():
            if name == favName:
                log.info(f"Fav ID={id}")
                service.call("media_player", "play_media", entity_id=obj.favObj.player, media_content_type = "favorite_item_id", media_content_id = id)
                obj.design.manager.gotoPage(obj.favObj.returnPage)
                return
            
        log.warning(f"Sonos Favorite \"{favName}\" not found")
        
    def _onDonePush(self, obj):
        obj.design.manager.gotoPage(obj.page)


class AnalogClock(ComposedObj):
    def __init__(self, design, center, r, timeSource="sensor.time", timeFormat="%H:%M", lineWidth = None, color=None, showSec=False, alarmSource=None, alarmColor=None):
        self.ComposedObj__init__(design)
        self.center = center
        self.r = r
        self.timeSource=timeSource
        self.alarmSource=alarmSource
        self.timeFormat=timeFormat

        if color is None:
            color = self.design.style.get("clock.color", None)

        width = lineWidth
        if width is None: 
            width = int(r/25)+1

        for m in range(0, 60, 5):
            points = self._getPoints(m, .8*r if m % 15 == 0 else .9*r, r)
            Line(design, points, width=width, color=color)

        self.smallHand = Line(design, (center, center), width=width, color=color)
        self.bigHand = Line(design, (center, center), width=width, color=color)
        self.tfMain = triggerFactory_entityChange(timeSource, self._onTimeChange, self.design.manager.instanceId)
        self._onTimeChange(self.design.manager.instanceId) # Mimic a change so that the correct value is filled in

        if alarmSource is not None:
            self.alarmHand = Line(design, (center, center), width=(width//2)+1, color=alarmColor)
            self.tfAlarm = triggerFactory_entityChange(alarmSource, self._onAlarmChange, self.design.manager.instanceId)
            self._onAlarmChange(self.design.manager.instanceId) # Mimic a change so that the correct value is filled in

        self.design.otherObjs.append(self) # Keep a reference to this object to keep the references to the trigger functions

    def _onTimeChange(self, id):
        if not self.design.manager._checkInstanceId(id, "AnalogClock TimeChange"):
            return
        dts = state.get(self.timeSource)
        try:
            dt = datetime.datetime.strptime(dts, self.timeFormat)
            dt = as_local(dt)
            h = dt.hour
            m = dt.minute
            r = self.r
        except:
            log.error(f"Failed to parse time '{dts}'")
            r = 0
            h = 0
            m = 0
        self.smallHand.setPoints(self._getPoints((h+m/60)*5, r*-.1, r*.55))
        self.bigHand.setPoints(self._getPoints(m, r*-.1, r*.77))

    def _onAlarmChange(self, id):
        if not self.design.manager._checkInstanceId(id, "AnalogClock AlarmChange"):
            return
        if self.alarmSource is not None:
            try:
                h,m = state.get(self.alarmSource).split(":")[:2]
                m = int(m)
                h = int(h) + m/60
                r = self.r
            except:
                r = 0
                h = 0
                m = 0
            self.alarmHand.setPoints(self._getPoints(h*5, r*-.1, r*.60))

    def _getPoints(self, min, r1, r2):
        a = min / 60 * 2*3.14
        x = math.sin(a)
        y = math.cos(a)
        return ((self.center[0] + int(x*r1),self.center[1] - int(y*r1)), (self.center[0] + int(x*r2),self.center[1] - int(y*r2)))


class Manager():
    class State:
        def __init__(self, entity, enabled):
             self.entity = entity
             self.enabled = enabled
             self.state = None
             self.noActivityCnt = 0
             self.set("unknown")

        def activityDetected(self):
            self.noActivityCnt = 0
            self.set("up")    

        def tick(self):
            self.noActivityCnt += 1
            if self.noActivityCnt > 5:
                self.set("down")   

        def set(self, value):
            if self.state != value:
                self.state = value
                if self.enabled:
                    state.set(self.entity, value)

        def setAttr(self, attr, value):
            if self.enabled:
                state.setattr(f"{self.entity}.{attr}", value)

        def incAttr(self, attr):
            if self.enabled:
                try:
                    value = int(state.getattr(self.entity)[attr])
                except:
                    value = 0 
                state.setattr(f"{self.entity}.{attr}", value+1)


    def __init__(self, name, screenSize, startupPage=1, keepHAState=False):
        self.Manager__init__(name, screenSize, startupPage, keepHAState)

    def Manager__init__(self, name, screenSize, startupPage=1, keepHAState=False):
        global screenName2manager
        self.name = name
        self.sendHeartbeat = False
        self.design = Design(self, screenSize)
        self.startupPage = startupPage
        self.style = {}
        self.designSentTime = None
        self.state = Manager.State(f"sensor.{self.name}", keepHAState)    
        self.instanceId = id(self)

        screenName2manager[name] = self.instanceId

        self.mqttTrigger1 = triggerFactory_mqtt(f"hasp/{self.name}/state/#",self._onMqttEvt, self.instanceId)
        self.mqttTrigger2 = triggerFactory_mqtt(f"hasp/{self.name}/LWT",self._onMqttEvt, self.instanceId)
        self.mqttTrigger3 = triggerFactory_mqtt(f"hasp/discovery/#",self._onMqttDiscovery, self.instanceId)

        self.timeTickTrigger = triggerFactory_time("period(0:00,1sec)", self._onTimerTick, self.instanceId)


    def sendPeriodicHeatbeats(self):
        self.sendHeartbeat = True
        self.timeTrigger = triggerFactory_entityChange("sensor.time", self._onTimeChange, self.design.manager.instanceId)

    def setMontionSensor(self, entity):
        self.montionSensorEntity = entity
        self.montionSensorTrigger = triggerFactory_entityChange(entity, self._onMotionSensor, self.instanceId)
          
    def _onMotionSensor(self, id):
        if not self.design.manager._checkInstanceId(id, "MontionSensor"):
            return
        if state.get(self.montionSensorEntity) == "on":
            self.sendIdle("off")
    
    def _onTimerTick(self, id):
        if not self.design.manager._checkInstanceId(id, "Manager TimerTick"):
            return
        # log.info(f"TimerTick {self.name}")
        self.design.onTimerTick()
        
    def _onTimeChange(self, id):
        if not self.design.manager._checkInstanceId(id, "Manager TimeChange"):
            return
        if self.sendHeartbeat:
            self.sendHeatbeat()
        self.state.tick()
        
    def _checkInstanceId(self, id, descr=""):
        global screenName2manager
        if id != screenName2manager[self.name]:
            if logStaleMessages: log.warning(f"Received STALE message {descr}")
            self.state.incAttr("stale_message")
            return False
        else:
            return True
        
    def sendHeatbeat(self):
        self.sendCmd("custom/heartbeat")

    def sendMsgBox(self, text, textColor=None, bgColor=None, autoClose=1000):
        jsonl = "{" 
        jsonl += f'"page":0,"id":255,"obj":"msgbox","text":"{text}","auto_close":{autoClose},"radius":15' 
        if textColor is not None:
            jsonl += f',"text_color":"{textColor}"'
        if bgColor is not None:
            jsonl += f',"bg_color":"{bgColor}"'
        jsonl += "}"
        self.sendCmd("jsonl", jsonl)

    def setBacklight(self, level):
        state = "on" if level > 0 else "off"
        self.sendCmd("backlight", "{" + f'"state":"{state}","brightness":{(level * 255) // 100}'+ "}")

    def sendIdle(self, state):
        self.sendCmd("idle", state)

    def sendCmd(self, cmd, payload=""):
        mqtt.publish(topic=f"hasp/{self.name}/command/{cmd}", payload=payload, qos=2)

    def sendDesign(self):
        if logSendDesign: log.info(f"Sending design to \"{self.name}\" manager={self}")

        self.state.incAttr("desing_sent")
        self.state.setAttr("stale_message", 0)

        self.sendIdle("off")
        task.sleep(1)
        self.sendCmd("clearpage", "all")
        task.sleep(3)
        self.sendMsgBox("Receiving design form HA...", bgColor="Orange", textColor="White", autoClose=10000)
        
        jsonl = ""
        for page in self.design.pages.values():
            jsonl += page.getJsonl()
            page.sent = True
            for obj in page.objs:
                n = obj.getJsonl()
                if len(jsonl)+len(n) > 2000:
                    self.sendCmd("jsonl", jsonl)
                    if logSendDesignDetail: log.info(f"Sending {len(jsonl)} bytes of json")
                    jsonl = n
                else:
                    jsonl += n + "\r\n"
                obj.sent = True
        if len(jsonl) > 0:
            if logSendDesignDetail: log.info(f"Sending (final) {len(jsonl)} bytes of json")
            self.sendCmd("jsonl", jsonl)

        task.sleep(5)
        self.sendMsgBox("Design Received from HA", textColor="White", bgColor="Green")

    def gotoPage(self, pageNbr):
        self.sendCmd("page", f"{pageNbr}")
        self.design.pageChanged(pageNbr)
        
    def _onMqttEvt(self, topic, payload, id):
        if not self._checkInstanceId(id, f"mqttEvnt topic={topic}"):
            return

        if logMqttEvents: log.info(f"mqtt Msg {topic} {payload}")

        topic = topic.split("/")

        if topic[2] == "LWT":
            if payload == "online":
                if logOnline: log.info(f"Plate {self.name} Online")
                self.state.activityDetected()
                if (self.designSentTime is None) or (time.time()-self.designSentTime > 5): # Sometimes online event come quickly after one another
                    designSentTime = time.time()
                    self.sendDesign()
                    self.gotoPage(self.startupPage)
        elif topic[2] == "state":
            obj = topic[3]
            #log.info(f"===> state of obj {obj}")
            if re.search("p[0-9]+b[0-9]+", obj) is not None:
                # it has the pb format
                pb = obj.split("b")
                p = int(pb[0][1:])
                b = int(pb[1])
                log.info(f"p={p} b={b} {len(self.design.pages)} {len(self.design.pages[p].objs)} ")
                try:
                    self.design.pages[p].objs[b-1].onStateMsg(topic, payload)
                except KeyError:
                    log.info(f"MQTT event on unknown pb {obj}")
            elif obj == "sensors":
                sensors = json.loads(payload)
                self.state.activityDetected()
                self.state.setAttr("uptime", sensors["uptime"])
            elif obj == "page":
                self.design.pageChanged(int(payload))
        else:
            log.info(f"Unexpected topic {topic[2]}")

    def _onMqttDiscovery(self, topic, payload, id):
        if self._checkInstanceId(id, "Discovery"):
            payload = json.loads(payload)
            if payload["node"] == self.name:
                if logDiscovery: log.info(f"Discovery {topic} node={payload['node']}")
                self.state.activityDetected()
                self.state.setAttr("uri", payload["uri"])
                self.state.setAttr("sw", payload["sw"])

def triggerFactory_time(timeSpec, func, cookie):
    if logEntityEvents: log.info(f">> Configure time trigger \"{timeSpec}\" func={func} cookie={cookie}")

    @time_trigger(timeSpec)
    def func_trig(value=None):
        if logEntityEvents: log.info(f">> Time trigger \"{timeSpec}\" change: func={func} cookie={cookie}")
        func(cookie)

    return func_trig

def triggerFactory_entityChange(entity, func, cookie):
    if logEntityEvents: log.info(f">> Configure trigger on \"{entity}\" func={func} cookie={cookie}")

    @state_trigger(entity)
    def func_trig(value=None):
        if logEntityEvents: log.info(f">> Triggered on \"{entity}\" change: func={func} cookie={cookie}")
        func(cookie)

    return func_trig

def triggerFactory_entityAttrChange(entity, attr, func, cookie):
    if logEntityEvents: log.info(f">> Configure trigger on \"{entity}.{attr}\" func={func} cookie={cookie}")

    @state_trigger(f"{entity}.{attr}")
    def func_trig(value=None):
        if logEntityEvents: log.info(f">> Triggered on \"{entity}.{attr}\" change: func={func} cookie={cookie}")
        func(cookie)

    return func_trig

def triggerFactory_attributeChange(entity, attribute, func, cookie):
    if logEntityEvents: log.info(f">> Configure trigger on \"{entity}.{attribute}\" func={func} cookie={cookie}")

    @state_trigger(entity+"."+attribute)
    def func_trig(value=None):
        if logEntityEvents: log.info(f">> Triggered on \"{entity}.{attribute}\" change: func={func} cookie={cookie}")
        func(cookie)

    return func_trig

def triggerFactory_mqtt(topic, func, cookie):

    @mqtt_trigger(topic)
    def func_trig(topic, payload):
        func(topic, payload, cookie)

    return func_trig

def defaultState2ButtonColor(design, state):
    styleId = f"btn.{state}.bg_color"
    try:
        color = design.style[styleId]
    except KeyError:
        log.warning(f"style ID \"{styleId}\" not found")
        color = "White"
    #log.info(f"state {state} to color {color}")
    return color

def defaultState2Color(design, state):
    styleId = f"text.{state}.color"
    try:
        color = design.style[styleId]
    except KeyError:
        log.warning(f"style ID \"{styleId}\" not found")
        color = "White"
    #log.info(f"state {state} to color {color}")
    return color

def onOff2Val(design, state):
    return "1" if state == "on" else "0"

def brightness2Val(desing, state):
    if state is None:
        state = 0
    return int(int(state) / 255 * 100)
