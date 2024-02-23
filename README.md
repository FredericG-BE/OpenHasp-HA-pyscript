# Introduction
This library provides an alternative way of integrating openhasp screens in Home Assistant. <br><br>
The screen design and how this integrates with HA is described in a single python file, replacing the jsonl files and the yaml files one traditionally would have to write.

# State of the project

# Supported features today
- Style definition that define colors, borders, fonts and so on for all objects
- Native objects:
    - Obj
    - Label
    - Button
    - Switch
    - Line
- Derived objects
    - On/Off Button
    - Analog Clock
    - Navigation Bar
    - MediaPlayer with Sonos extensions
- Support for MQTT Watchdog
- Motion detector can switch idle off

# Getting started

- Install HACS pyscript. [See the pysript manual](https://hacs-pyscript.readthedocs.io/en/latest/installation.html#option-2-manual). Configure pyscript: As described in the [pyscript manual](https://hacs-pyscript.readthedocs.io/en/latest/configuration.html). "hass_is_global" should be set to true.


- Install the openhasp/pyscript library:
```
    cd YOUR_HASS_CONFIG_DIRECTORY    # same place as configuration.yaml
    cd pyscript
    unzip OpenHasp-HA-pyscript-main.zip
```
-
