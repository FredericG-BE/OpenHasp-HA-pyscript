# Introduction
This library facilitates controlling [openHASP](https://www.openhasp.com/) screens (plates) from Home Assistant using Python.


Traditionally the designs of the openHASP screen pages are described in json(l) while the interactions with Home Assistant (HA) are described in a yaml file using the standard openHASP integration for HA. This library provides an alternative by describing the pages design and the interactions with HA in a single definition  in Python. IMHO this results a much more readable and maintainable implementation of your designs. In addition, the approach allows to easily create more complex "objects" composed of basic openHASP objects, like a Media Player which are added to your design with just one line of code. Reuse is also much easier.


This library is based on [HACS pyscript](https://hacs-pyscript.readthedocs.io/en/latest/) and communicates directly via mqtt messages with openHASP devices.

<p align="center">
<img src="https://github.com/FredericG-BE/OpenHasp-HA-pyscript/assets/11998085/9b135649-75b5-46fd-aeea-e605f3431226">

<img src="https://github.com/FredericG-BE/OpenHasp-HA-pyscript/assets/11998085/af62ddb9-cdf4-494d-9c5f-e6b39b9b685c">
</p>



# State of the project
Today the library supports a subset of openHasp features. I have been adding features as I needed them.

# Supported features today
- Native objects:
    - **Obj**
    - **Label**
    - **Button**
    - **Switch**
    - **Slider**
    - **Line**
    - **Image**; Images are fetched, resized and stored in www/openhasp-pyscript/temp by the library to be fetched by the plate.
    - **MessageBox** (Basic support for now)
    - **Arc** (Basic support for now)
- "Composed" objects (combining native objects to form more complex functions):
    - **On/Off Button**
    - **Analog Clock**; Selectable HA entity providing the time and optional alarm time.
    - **Navigation Bar**
    - **Media Artwork**
    - **Media Player with Sonos extensions**
    - **Sonos Favorites**; Page with a (subset) of favorites to select from
    - **Camera Image**; For camera images that are exposed in HA via an entity; image is refreshed periodically when the page is visible.
- Integration with HA:
    - When an object is pushed: call a service, toggle a HA switch entity or call a Python function.
    - Link objects to HA entities so that the latter control text and/or color of the object.
    - For each plate the library can create an maintain entities showing statistics about the device, if it is running, the version, the URI, uptime, the FW version it is running, ...
- **Generate jsonl** and send to display when it comes online.    
- **Style definition** controlling colors, borders, fonts and so on for all objects. A style controls the whole project but can however be overwritten per object if needed.
- Support for **MQTT Watchdog**. For cases where a screen is not useful when disconnected from HA (and is displaying stale data), I created some custom code that resets the screen when no mqtt heartbeat messages are received for a few minutes.  
- External **Motion detector** can switch idle off.

# Features and enhancements in the pipeline
- More control on how an image is centered in the reserved canvas
- Better Message Box support
- Media Player enhancements:
    - More control over layout
    - Select from a list of speakers
    - Joining speakers
- Air Conditioner
- More elaborate Idle Handling by HA iso by openHASP
- Graphs 

# Getting started

- **MQTT** MQTT must be enabled on HA and connected to an MQTT broker. An openHASP screen must be configured and connected to the broker. Perhaps a good idea is to start from a standard setup with the standard HA integration to verify the MQTT/openHASP setup.
- **Install HACS pyscript.** [See the pysript manual](https://hacs-pyscript.readthedocs.io/en/latest/installation.html#option-2-manual). Configure pyscript as described in the [pyscript manual](https://hacs-pyscript.readthedocs.io/en/latest/reference.html#configuration) where I suggest to use the approach where a config.yaml in the pyscript directory. "hass_is_global" and "allow_all_imports" should be set to true. 
- **Add ```"dependencies": ["mqtt"]```** to YOUR_HASS_CONFIG_DIRECTORY/custom_components/pyscript/manifest.json. On my system it looks like this:
```
{
  "domain": "pyscript",
  ...
  "zeroconf": [],
  "dependencies": ["mqtt"]
}
```
- **Install the openHasp-HA-pyscript library**:
```
    cd YOUR_HASS_CONFIG_DIRECTORY    # same place as configuration.yaml
    cd pyscript
    unzip OpenHasp-HA-pyscript-main.zip
```
- **Make sure** the standard openHASP integration for HA is not/no longer active.
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

openhasp_demo.py provides a bit more elaborate example. 

The class HaspDemo derives from the library Manager class, allowing to instantiate multiple instances for multiple plates. This is done at the end of the file where the plate specific data is collected from the config.yaml; it could look like this:

```
pyscript:
  allow_all_imports: true
  hass_is_global: true

apps:

# openhasp_helloWorld: 

  openhasp_demo:
    - friendly_name: "Bureau"
      plate_name: "plate_test1"
      resolution_x: 480
      resolution_y: 320
      mediaplayer: "media_player.bureau"
      lamp: "light.bureau_spots"
      camera: "camera.oost" # This is optional

    - friendly_name: "Living"
      plate_name: "plate_test2"
      resolution_x: 480
      resolution_y: 320
      mediaplayer: "media_player.living"
      lamp: "light.living"
```  
While the screen resolutions are passed here, the layout is not adapted to the provided resolution and is made for 480x320.
This demo uses images, which will not work on devices without PSram.

<p align="center">
<img src="https://github.com/FredericG-BE/OpenHasp-HA-pyscript/assets/11998085/abf97b57-d402-4c2a-8781-d888de8cc778" width="250">
&nbsp
<img src="https://github.com/FredericG-BE/OpenHasp-HA-pyscript/assets/11998085/1784956a-d07f-4d1b-b9d4-9ebf7136d337" width="250">
&nbsp
<img src="https://github.com/FredericG-BE/OpenHasp-HA-pyscript/assets/11998085/bdbfdef6-975a-4479-b9c0-70171e402b10" width="250">
</p>


# Another example showing the state of a BambuLab 3D printer, openhasp_demo_bambuLab.py

This example assumes you have a BambuLab printer and the integration for HA installed. As in openhasp_demo.py, it requires to configured in config.yaml. An example could be:

```
apps:
  openhasp_demo_bambuLab:
    - friendly_name: "Bambu p1s"
      plate_name: "plate70"
      resolution_x: 800
      resolution_y: 480
      printer: "p1s_..."  # Fill in the exact name of the printer name in HA
      power_switch: "switch.printer"  # In case you have a switch to control control the power to your printer; this is optional
```

The red arc in the clock indicate the start en end time of the print.
<p align="center">
<img src="https://github.com/FredericG-BE/OpenHasp-HA-pyscript/assets/11998085/3b7f874f-10e5-47d9-bb0e-1402760dad78" width="500">
</p>

# More inspiration

Alarm clock, the red hand indicates the alarm time set in the Sonos speaker.

<img src="https://github.com/FredericG-BE/OpenHasp-HA-pyscript/assets/11998085/e15b603d-ca24-4aaa-83ab-27b6adf01c28" width="250">
<img src="https://github.com/FredericG-BE/OpenHasp-HA-pyscript/assets/11998085/caa568f8-01fd-4113-a90d-9a7cb17fbeb0" width="250">
<img src="https://github.com/FredericG-BE/OpenHasp-HA-pyscript/assets/11998085/f11ffbfb-9c91-4724-8675-bc138ce6b8ed" width="250">
