# Introduction
This library facilitates describing OpenHasp pages and their interactions with Home Assistant entities in Python. This single Python definition replaces the jsonl and yaml files one traditionally would have to write. The library communicates directly via mqtt messages with OpenHasp devices.  

![HelloWorld](https://github.com/FredericG-BE/OpenHasp-HA-pyscript/assets/11998085/9b135649-75b5-46fd-aeea-e605f3431226)

This approach comes IMHO with many advantages.

# State of the project
Today the library supports a subset of OpenHasp. I add features as I need them. 

# Supported features today
- **Style definition** controlling colors, borders, fonts and so on for all objects. A style controls the whole projects but can however be overwritten per object if needed.
- Native objects:
    - **Obj**
    - **Label**
    - **Button**
    - **Switch**
    - **Slider**
    - **Line**
    - **Image**; Images are fetched and resized by the library.
    - **MessageBox**
- Derived objects (combining native objects to form more complex functions):
    - **On/Off Button**
    - **Analog Clock**; Selectable HA entity providing the time and alarm time.
    - **Navigation Bar**
    - **MediaArtwork**
    - **MediaPlayer with Sonos extensions**
- Integration with HA:
    - When an object is pushed: call a service, toggle a HA switch entity or call a Python function.
    - Link objects to HA entities so that the latter control text and/or color of the object.
- **Generate jsonl** and send to display when it comes online.    
- Support for **MQTT Watchdog**. In cases where a screen is not useful when not connected in HA and displaying stale data needs to be avoided, I created some custom code that resets the screen when no mqtt heartbeat messages are received for a few minutes.  
- **Motion detector** can switch idle off.

# Getting started

- Install HACS pyscript. [See the pysript manual](https://hacs-pyscript.readthedocs.io/en/latest/installation.html#option-2-manual). Configure pyscript: As described in the [pyscript manual](https://hacs-pyscript.readthedocs.io/en/latest/configuration.html). "hass_is_global" should be set to true.


- Install the openhasp/pyscript library:
```
    cd YOUR_HASS_CONFIG_DIRECTORY    # same place as configuration.yaml
    cd pyscript
    unzip OpenHasp-HA-pyscript-main.zip
```
-
