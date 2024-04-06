# Introduction
This library facilitates controlling [openHASP](https://www.openhasp.com/) screens (plates) from Home Assistant using Python.


Traditionally the designs of the openHASP screen pages are described in json(l) while the interactions with Home Assistant (HA) are described in a yaml file using the standard openHASP integration for HA. This library provides an alternative by describing the pages design and the interactions with HA in a single definition  in Python. IMHO this results a much more readable and maintainable implementation of your designs.


This library is based on [HACS pyscript](https://hacs-pyscript.readthedocs.io/en/latest/) and communicates directly via mqtt messages with openHASP devices.

![HelloWorld](https://github.com/FredericG-BE/OpenHasp-HA-pyscript/assets/11998085/9b135649-75b5-46fd-aeea-e605f3431226)


# State of the project
Today the library supports a subset of openHasp features. I have been adding features as I needed them. At the time of writing, this repository is still private and teh setup steps have not been verified by somebody else. 

# Supported features today
- Native objects:
    - **Obj**
    - **Label**
    - **Button**
    - **Switch**
    - **Slider**
    - **Line**
    - **Image**; Images are fetched and resized and stored in www/openhasp-pyscript/temp by the library to be fetched by the plate.
    - **MessageBox**
- Derived objects (combining native objects to form more complex functions):
    - **On/Off Button**
    - **Analog Clock**; Selectable HA entity providing the time and optional alarm time.
    - **Navigation Bar**
    - **Media Artwork**
    - **Media Player with Sonos extensions**
    - **Sonos Favorites**; Page with a (subset) of favorites to select from
- Integration with HA:
    - When an object is pushed: call a service, toggle a HA switch entity or call a Python function.
    - Link objects to HA entities so that the latter control text and/or color of the object.
- **Generate jsonl** and send to display when it comes online.    
- **Style definition** controlling colors, borders, fonts and so on for all objects. A style controls the whole project but can however be overwritten per object if needed.
- Support for **MQTT Watchdog**. For cases where a screen is not useful when disconnected from HA (and is displaying stale data), I created some custom code that resets the screen when no mqtt heartbeat messages are received for a few minutes.  
- External **Motion detector** can switch idle off.

# Features and enhancements in the pipeline
- Display Camera Image
- Better Message Box support
- Media Player enhancements:
    - More control over layout
    - Select from a list of speakers
    - Joining speakers
- Air Conditioner
- More elaborate Idle Handling by HA iso by openHASP
- Graphs 

# Getting started

- MQTT must be enabled on HA and connected to an MQTT broker. A openHASP screen must be configured and connected to the broker. Perhaps a good idea is to start from a standard setup with the standard HA integration to verify the MQTT/openHASP setup.
- **Install HACS pyscript.** [See the pysript manual](https://hacs-pyscript.readthedocs.io/en/latest/installation.html#option-2-manual). Configure pyscript as described in the [pyscript manual](https://hacs-pyscript.readthedocs.io/en/latest/reference.html#configuration) where I suggest to use the approach where a config.yaml in the pyscript directory. "hass_is_global" and "allow_all_imports" should be set to true. 
- Add *"dependencies": ["mqtt"]* to YOUR_HASS_CONFIG_DIRECTORY/custom_components/pyscript/manifest.json. On my system it looks like this:
```
{
  "domain": "pyscript",
  ...
  "zeroconf": [],
  "dependencies": ["mqtt"]
}
```
- Install the openhasp/pyscript library:
```
    cd YOUR_HASS_CONFIG_DIRECTORY    # same place as configuration.yaml
    cd pyscript
    unzip OpenHasp-HA-pyscript-main.zip
```
- **Run the openhasp_helloWorld.py**
    - Modify the settings in YOUR_HASS_CONFIG_DIRECTORY/pyscript/apps/openhasp_helloWorld
    - Add openhasp_helloWorld to your YOUR_HASS_CONFIG_DIRECTORY/pyscript/config.yaml:
    ```
    pyscript:
        allow_all_imports: true
        hass_is_global: true

        apps:
            openhasp_helloWorld:
    ``` 

# A more elaborate example openhasp_demo.py
TODO
