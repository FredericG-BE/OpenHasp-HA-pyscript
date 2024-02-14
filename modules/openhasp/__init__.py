import json
import math
import time
import re

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


logEntityEvents = False
logMqttEvents = False
logDiscovery = True
logOnline = True
logSendDesign = True
logSendDesignDetail = False
logStaleMessages = False

screenName2manager = {}

class Link(object):
    pass

class Obj():

    def Obj__init__(self, design, type=None, extraPar=None):
        self.design = design
        self.type = type
        self.params = {}
        if type is not None:
            self.params["obj"] = type
        if extraPar is not None:
            self.params.update(extraPar)
        #assert isInstance(design, Design)
        self.sent = False # not sent to the device yet

        # Add this object to the design
        self.design.addObj(self)

    def getpb(self):
        return f"p{self.params['page']}b{self.params['id']}"

    def setParam(self, param, value, styleName=None):
        if value is None:
            # No value provided... can it be found in the style?
            value = self.design.style.get(styleName, None)
        if value is not None:
            self.params[param] = value
            if self.sent:
                self.design.manager.sendCmd(f"{self.getpb()}.{param}", f"{value}")

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

    def onStateMsg(self, topic, payload):
        # Handling an MQTT state update for this object
        if payload == '{"event":"down"}':
            if hasattr(self, "toggleOnPushEntity"):
                domain, name = self.toggleOnPushEntity.split(".")
                service.call(domain, "toggle", entity_id=self.toggleOnPushEntity)

            if hasattr(self, "actionOnPushFunc"):
                self.actionOnPushFunc(self)

            if hasattr(self, "serviceOnPushInfo"):
                log.info(f"self.serviceOnPush: {self.serviceOnPushInfo}")
                service.call(self.serviceOnPushInfo[0], self.serviceOnPushInfo[1], **self.serviceOnPushInfo[2])

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


class Page(Obj):

    def __init__(self, design, pageNbr, startupPage=False, extraPar=None):
        self.Obj__init__(design, type=None, extraPar=None)
        self.params["page"] = pageNbr
        self.setParam("bg_color", None, "page.gb_color")
        self.design.page = pageNbr

        if startupPage:
            self.design.manager.startupPage = pageNbr


class EmptyObj(Obj):

    def __init__(self, design, x, y, w, h, extraPar=None):
        self.Obj__init__(design, "Obj", extraPar)
        self.setParam("x", x)
        self.setParam("y", y)
        self.setParam("w", w)
        self.setParam("h", h)
        self.setParam("bg_opa", 0)
        self.setParam("border_side", 0)


class Label(Obj):

    def __init__(self, design, x, y, w, h, text, fontSize=None, textColor=None, align=None, mode=None, extraPar=None):
        self.Label__init__(design, x, y, w, h, text, fontSize, textColor, align, mode, extraPar)

    def Label__init__(self, design, x, y, w, h, text, fontSize=None, textColor=None, align=None, mode=None, extraPar=None):
        self.Obj__init__(design, "label", extraPar)
        self.params.update({"x":x, "y":y, "w":w, "h":h})
        self.params["text"] = text

        self.setParam("text_font", fontSize, "text.fontSize")
        self.setParam("text_color", textColor, "text.color")
        self.setParam("align", align, "text.align")

        if mode is not None:
            self.setParam("mode", mode)

        self.fontSize = fontSize
        self.links = []

    def setText(self, value):
        self.setParam("text", value)

    def getText(self):
        return self.params["text"]

    def setTextColor(self, color):
         self.setParam("text_color", color)

    def setBorder(self, width, radius, color=None):
        self.params["border_width"] = width
        self.params["radius"] = radius
        if color is not None:
            self.params["border_color"] = color

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
    def __init__(self, design, x, y, w, h, text, fontSize=None, align=None, extraPar=None):
        self.Button__init__(design, x, y, w, h, text, fontSize, align=None, extraPar=None)

    def Button__init__(self, design, x, y, w, h, text, fontSize, align=None, extraPar=None):
        self.Label__init__(design, x, y, w, h, text, fontSize, align=None, extraPar=None)
        self.params["obj"] = "btn"

        self.setParam("text_font", fontSize, "btn.fontSize")
        self.setParam("text_color", None, "btn.text_color")
        self.setParam("align", None, "btn.align")
        self.setParam("bg_color", None, "btn.bg_color")
        self.setParam("radius", None, "btn.radius")
        self.setParam("border_color", None, "btn.border_color")
        self.setParam("border_width", None, "btn.border_width")

    def addIcon(self, icon, x, y):
        self.setParam("value_str", icon)
        self.setParam("value_font", self.fontSize)
        self.setParam("value_ofs_x", x)
        self.setParam("value_ofs_y", y)
        self.setParam("value_color", None, "btn.text_color")


class OnOffButton(Button):
    def __init__(self, design, x, y, w, h, text, fontSize, entity, icon=None, align=None, extraPar=None):
        self.Button__init__(design, x, y, w, h, text, fontSize, align=None, extraPar=None)
        self.entity = entity

        if icon is not None:
            self.addIcon(icon, -w//2+fontSize, 0)
        self.linkColor(entity, param="bg_color", transform=defaultState2ButtonColor)
        self.toggleOnPush(entity)


class Line(Obj):
    def __init__(self, design, points, width=None, color=None, extraPar=None):
        self.Obj__init__(design, "line", extraPar)
        self.setPoints(points)

        self.setParam("line_width", width, "line.width")
        self.setParam("line_color", color, "line.color")

    def setPoints(self, points):
        self.setParam("points", "[" + ",".join([f"[{a},{b}]" for a,b in points]) + "]")


class Image(Obj):
    def __init__(self, design, coord, size, src):
        self.Obj__init__(design, "img")
        self.setParam("x", coord[0])
        self.setParam("y", coord[1])
        self.setParam("w", size[0])
        self.setParam("h", size[1])
        self.setParam("src", src)  

class Switch(Obj):
    def __init__(self, design, coord, size):
        self.Obj__init__(design, "switch")
        self.setParam("x", coord[0])
        self.setParam("y", coord[1])
        self.setParam("w", size[0])
        self.setParam("h", size[1])   

        self.setParam("border_color", None, "switch.border_color")
        self.setParam("bg_color00", None, "switch.off.bg_color")  
        self.setParam("bg_color10", None, "switch.on.bg_color")
        self.setParam("bg_color20", None, "switch.knob_color")
          

class Design():
    def __init__(self, manager, screenSize, style=None):
        self.manager = manager
        self.screenSize = screenSize
        self.page = 0
        self.id = 1
        self.currId = 0
        self.style = style if style is not None else {}
        self.screenBackgroundColor = "Black"
        self.objs = []  # These are HASP objects that are displayed
        self.otherObjs = [] # Objects that are no HAPS objects but for which a reference needs to be kept
        self.pageIds = [0]*12
        self.pbs = {}

    def updateStyle(self, style):
        self.style.update(style)

    def addObj(self, obj):
        if type(obj) == Page:
            pass
        else:
            obj.setParam("page", self.page)
            self.pageIds[self.page] += 1
            obj.setParam("id", self.pageIds[self.page])
            self.pbs[f"p{obj.params['page']}b{obj.params['id']}"] = obj

        self.objs.append(obj)
        return obj

class NavButtons():
    def __init__(self, design, w, h, fontsize, tabs):
        self.design = design

        dx = (design.screenSize[0] - w*(len(tabs))) // len(tabs)
        y = design.screenSize[1] - h - 5
        x = dx // 2
        for tab in tabs:
            obj = Button(design, x, y, w, h, tab[0], fontsize)
            obj.setParam("text_color", design.style["nav.active.text_color" if tab[1] == design.page else "nav.text_color"])
            obj.setParam("bg_color", design.style["nav.active.bg_color" if tab[1] == design.page else "nav.bg_color"])
            obj.actionOnPush(self._onPush)
            obj.pageToGo = tab[1]
            x += w + dx

    def _onPush(self, obj):
        #log.info(f"---> On Push {self} {obj}")
        obj.design.manager.gotoPage(obj.pageToGo)


class MediaPlayer():
    def __init__(self, design, player, coord, size, dispName=None, volumes=None, sonosSleepTimer=False, favoritesPage=None):
        self.design = design
        self.player = player
        self.favoritesPage = favoritesPage

        fontsize = None

        x,y = coord
        h = 60
        dx = 20 # space between the buttons
        dy = 70

        if dispName is not None:
            obj = Label(design, x, y, size[0], h, dispName, align="left")
            y += dy

        # Media title
        obj = Label(design, x, y, size[0], h, "",) # mode="loop")
        obj.setBorder(self.design.style["btn.border_width"], self.design.style["btn.radius"], self.design.style["text.color"])
        obj.linkText(player+".media_title")

        # Volumes
        if volumes is not None:
            y += dy
            w = (size[0] - (len(volumes)-1)*dx) // len(volumes)
            x = coord[0]
            for volume in volumes:
                obj = Button(design, x, y, w, h, ICON_VOLUME_HIGH + f" {volume}%", fontsize)
                obj.volume = volume
                obj.player = player
                obj.actionOnPush(self._onVolumePush)
                x += w + dx

        # Buttons
        y += dy
        nbButtons = 5
        w = (size[0] - (nbButtons-1)*dx) // nbButtons
        x = coord[0]
        
        obj = Button(design, x, y, w, h, ICON_VOLUME_MEDIUM, fontsize)
        obj.serviceOnPush("media_player", "volume_down", entity_id=player)
        x += w + dx

        obj = Button(design, x, y, w, h, ICON_SKIP_PREVIOUS, fontsize)
        obj.serviceOnPush("media_player", "media_previous_track", entity_id=player)
        x += w + dx

        obj = Button(design, x, y, w, h, ICON_PLAY, fontsize)
        obj.serviceOnPush("media_player", "media_play_pause", entity_id=player)
        obj.linkText(player, self._playerState2Icon)
        x += w + dx

        obj = Button(design, x, y, w, h, ICON_SKIP_NEXT, fontsize)
        obj.serviceOnPush("media_player", "media_next_track", entity_id=player)
        x += w + dx

        obj = Button(design, x, y, w, h, ICON_VOLUME_HIGH, fontsize)
        obj.serviceOnPush("media_player", "volume_up", entity_id=player)
        x += w + dx


        nbButtons = 1
        if sonosSleepTimer:
            nbButtons += 2
        w = (size[0] - ((nbButtons-1)*dx)) // nbButtons
        x = coord[0]
        y += dy

        if sonosSleepTimer:
            obj = Button(design, x, y, w, h, "Sleep 15\"", fontsize)
            obj.serviceOnPush("sonos", "SET_SLEEP_TIMER", entity_id=player, sleep_time=15*60)
            x += w + dx

            obj = Button(design, x, y, w, h, "Sleep 30\"", fontsize)
            obj.serviceOnPush("sonos", "SET_SLEEP_TIMER", entity_id=player, sleep_time=30+60)
            x += w + dx

        obj = Button(design, x, y, w, h, ICON_MUSIC, fontsize)
        obj.page = favoritesPage
        obj.actionOnPush(self._onFavPush)
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

class SonosFavorites():
    def __init__(self, design, player, coord, size, favList, returnPage):
        self.returnPage = returnPage
        self.favList = favList
        self.player = player

        x,y = coord
        fontsize = None
        h = 60
        dy = 70
        dx = 10 # space between the buttons
        favPerRow = 3
        w = (size[0] - (favPerRow-1)*dx) // favPerRow
        rowCnt = 1

        for favShortName in favList:
            obj = Button(design, x, y, w, h, favShortName, fontsize) 
            obj.favObj = self
            obj.actionOnPush(self._onFavPushed)
            x += w + dx
            rowCnt += 1
            if rowCnt > favPerRow:
                y += dy
                x = coord[0]
                rowCnt = 1
        obj = Button(design, x, y, w, h, ICON_CHECK, fontsize)
        obj.page = returnPage
        obj.actionOnPush(self._onDonePush)

    def _onFavPushed(self, obj):
        favShortName = obj.getText()
        log.info(f"Fav shortName {favShortName}")

        favName = obj.favObj.favList[favShortName]
        log.info(f"Fav Name {favName}")

        for id, name in state.get_attr("sensor.sonos_favorites")["items"].items():
            if name == favName:
                log.info(f"Fav ID={id}")
                service.call("media_player", "play_media", entity_id=obj.favObj.player, media_content_type = "favorite_item_id", media_content_id = id)
                obj.design.manager.gotoPage(obj.favObj.returnPage)
                return
            
        log.warning("Sonos Favorite \"{favName}\" not found")
        
    def _onDonePush(self, obj):
        obj.design.manager.gotoPage(obj.page)


class AnalogClock():
    def __init__(self, design, cx, cy, r, timeSource="sensor.time", color=None, showSec=False, alarmSource=None, alarmColor=None):
        self.design = design
        self.cx = cx
        self.cy = cy
        self.r = r
        self.timeSource=timeSource
        self.alarmSource=alarmSource

        if color is None:
            color = self.design.style.get("clock.color", None)

        width = int(r/25)+1

        for m in range(0, 60, 5):
            points = self._getPoints(m, .8*r if m % 15 == 0 else .9*r, r)
            Line(design, points, width=width, color=color)

        self.smallHand = Line(design, ((cx, cy), (cx, cy)), width=width, color=color)
        self.bigHand = Line(design, ((cx, cy), (cx, cy)), width=width, color=color)
        self.tfMain = triggerFactory_entityChange(timeSource, self._onTimeChange, self.design.manager.instanceId)
        self._onTimeChange(self.design.manager.instanceId) # Mimic a change so that the correct value is filled in

        if alarmSource is not None:
            self.alarmHand = Line(design, ((cx, cy), (cx, cy)), width=(width//2)+1, color=alarmColor)
            self.tfAlarm = triggerFactory_entityChange(alarmSource, self._onAlarmChange, self.design.manager.instanceId)
            self._onAlarmChange(self.design.manager.instanceId) # Mimic a change so that the correct value is filled in

        self.design.otherObjs.append(self) # Keep a reference to this object to keep the references to the trigger functions

    def _onTimeChange(self, id):
        if not self.design.manager._checkInstanceId(id, "AnalogClock TimeChange"):
            return
        # log.info(f"AnalogClock._onTimeChange self={self}")

        try:
            h,m = state.get(self.timeSource).split(":")
            m = int(m)
            h = int(h) + m/60
            r = self.r
        except:
            r = 0
            h = 0
            m = 0
        self.smallHand.setPoints(self._getPoints(h*5, r*-.1, r*.55))
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
        return ((self.cx + int(x*r1),self.cy - int(y*r1)), (self.cx + int(x*r2),self.cy - int(y*r2)))


class Manager():
    class State:
        def __init__(self, entity):
             self.entity = entity
             state.set(entity, "unknown")

        def set(self, item, value):
            state.setattr(f"{self.entity}.{item}", value)

        def inc(self, item):
            try:
                value = int(state.getattr(self.entity)[item])
            except:
                value = 0 
            state.setattr(f"{self.entity}.{item}", value+1)


    def __init__(self, name, screenSize, watchdogActive=False):
        self.Manager__init__(name, screenSize, watchdogActive)

    def Manager__init__(self, name, screenSize, startupPage=1):
        global screenName2manager
        self.name = name
        self.sendHeartbeat = False
        self.design = Design(self, screenSize)
        self.startupPage = startupPage
        self.style = {}
        self.designSentTime = None
        self.state = None
        self.instanceId = id(self)

        screenName2manager[name] = self.instanceId

        self.mqttTrigger1 = triggerFactory_mqtt(f"hasp/{self.name}/state/#",self._onMqttEvt, self.instanceId)
        self.mqttTrigger2 = triggerFactory_mqtt(f"hasp/{self.name}/LWT",self._onMqttEvt, self.instanceId)
        self.mqttTrigger3 = triggerFactory_mqtt(f"hasp/discovery/#",self._onMqttDiscovery, self.instanceId)
            

    def keepState(self, entity=None):
        if entity is None:
            entity = f"sensor.{self.name}"
        self.state = Manager.State(entity)    

    def sendPeriodicHeatbeats(self):
        self.sendHeartbeat = True
        self.timeTrigger = triggerFactory_entityChange("sensor.time", self._onTimeChange, self.design.manager.instanceId)
       
    def _onTimeChange(self, id):
        if not self.design.manager._checkInstanceId(id, "Manager TimeChange"):
            return
        if self.sendHeartbeat:
            self.sendHeatbeat()
        
    def _checkInstanceId(self, id, descr=""):
        global screenName2manager
        if id != screenName2manager[self.name]:
            if logStaleMessages: log.warning(f"Received STALE message {descr}")
            if self.state is not None:
                self.state.inc("stale_message")
            return False
        else:
            return True
        
    def sendHeatbeat(self):
        self.sendCmd("custom/heartbeat")

    def sendMsgBox(self, text, autoclose=1000):
        self.sendCmd("jsonl", "{" + f'"page":0,"id":255,"obj":"msgbox","text":"{text}","auto_close":{autoclose}' + "}")

    def setBacklight(self, level):
        state = "on" if level > 0 else "off"
        self.sendCmd("backlight", "{" + f'"state":"{state}","brightness":{(level * 255) // 100}'+ "}")

    def sendCmd(self, cmd, payload=""):
        mqtt.publish(topic=f"hasp/{self.name}/command/{cmd}", payload=payload, qos=2)

    def sendDesign(self):
        if logSendDesign: log.info(f"Sending design to \"{self.name}\" manager={self}")

        if self.state is not None:
            self.state.inc("desing_sent")

        self.sendCmd("clearpage", "all")
        self.setBacklight(50)
        self.sendMsgBox("Receiving design form HA...")

        jsonl = ""
        for obj in self.design.objs:
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

        self.sendMsgBox("Design Complete")

    def gotoPage(self, page):
        self.sendCmd("page", f"{page}")

    def _onMqttEvt(self, topic, payload, id):
        if not self._checkInstanceId(id, f"mqttEvnt topic={topic}"):
            return

        if logMqttEvents: log.info(f"mqtt Msg {topic} {payload}")

        topic = topic.split("/")

        if topic[2] == "LWT":
            if payload == "online":
                if logOnline: log.info(f"Plate {self.name} Online")
                if (self.designSentTime is None) or (time.time()-self.designSentTime > 5): # Sometimes online event come quickly after one another
                    designSentTime = time.time()
                    self.sendDesign()
                    self.gotoPage(self.startupPage)
        elif topic[2] == "state":
                obj = topic[3]
                if re.search("p[0-9]+b[0-9]+", obj) is not None:
                    # it has the pb format
                    try:
                        self.design.pbs[obj].onStateMsg(topic, payload)
                    except KeyError:
                        log.info(f"MQTT event on unknown pb {obj}")

    def _onMqttDiscovery(self, topic, payload, id):
        if self._checkInstanceId(id, "Discovery"):
            payload = json.loads(payload)
            if payload["node"] == self.name:
                if logDiscovery: log.info(f"Discovery {topic} node={payload['node']}")
                if self.state is not None:
                    self.state.set("uri", payload["uri"])
                    self.state.set("sw", payload["sw"])

def triggerFactory_entityChange(entity, func, cookie):
    if logEntityEvents: log.info(f">> Configure trigger on \"{entity}\" func={func} cookie={cookie}")

    @state_trigger(entity)
    def func_trig(value=None):
        if logEntityEvents: log.info(f">> Triggered on \"{entity}\" change: func={func} cookie={cookie}")
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
