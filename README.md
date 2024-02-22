# Introduction
This library provides an alternative way of integrating openhasp screens in Home Assistant. <br><br>
The screen design and how this integrates with HA is described in a single python file, replacing the jsonl files and the yaml files one traditionally would have to write.



# Getting started

- Install HACS pyscript. [See the pysript manual](https://hacs-pyscript.readthedocs.io/en/latest/installation.html#option-2-manual)
- Configure pyscript: As described in the [pyscript manual](https://hacs-pyscript.readthedocs.io/en/latest/configuration.html). "hass_is_global" should be set to true


- Install the openhasp/pyscript library:
```
    cd YOUR_HASS_CONFIG_DIRECTORY    # same place as configuration.yaml
    cd pyscript
    unzip OpenHasp-HA-pyscript-main.zip
```
-
