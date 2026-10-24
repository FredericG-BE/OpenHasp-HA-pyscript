# OpenHASP Pyscript Library Overview

## Purpose

OpenHASP-HA-pyscript is a Python library for building and controlling openHASP
touchscreen plates from Home Assistant. It runs inside Pyscript and communicates
with plates over MQTT.

The library combines plate page layouts, JSONL generation, Home Assistant entity
bindings, event callbacks, and service calls in Python. This lets a Pyscript app
define both what a plate displays and how it interacts with Home Assistant.
The implementation is a practical subset of openHASP functionality, rather
than a complete implementation of every openHASP object or protocol feature.

## Package layout on `develop`

The `develop` branch is intended to be cloned directly into
`pyscript/modules/openhasp`. The Python package files are at the repository
root:

```text
openhasp/
├── __init__.py
├── imageHandling.py
├── mdi.py
├── style1.py
├── style2.py
├── README.md
└── examples/
    ├── openhasp_helloWorld.py
    ├── openhasp_demo.py
    └── openhasp_demo_bambuLab.py
```

Home Assistant applications are separate from the library: copy an example
into `pyscript/apps/` and configure it with Pyscript. The examples import the
library as `openhasp`.

## Architecture

The main module, `__init__.py`, contains the plate object model and Home
Assistant/Pyscript integration:

- `Obj` is the base display object. It holds openHASP parameters, serializes
  them for JSONL, and sends incremental updates.
- `Page` groups objects. `Design` manages pages, object IDs, styles, and page
  changes.
- Native object classes include `Label`, `Button`, `Switch`, `Slider`, `Line`,
  `Image`, and `Arc`. `OnOffButton` combines common button behavior.
- `ComposedObj` is the base for higher-level controls, including navigation
  buttons, cameras, media artwork and players, Sonos favorites, and an analog
  clock.
- `Manager` owns a plate's MQTT interaction, design transmission, navigation,
  watchdog state, and optional Home Assistant diagnostic entity.
- Trigger factory helpers register time, entity-state, entity-attribute,
  attribute, and MQTT triggers for Pyscript applications.

`imageHandling.py` downloads or reads images, optionally resizes them, prepares
plate-compatible image data, and exposes generated files through Home
Assistant's `/local` path. `mdi.py` provides Material Design Icon glyphs.
`style1.py` and `style2.py` provide reusable style dictionaries that can be
overridden per object.

### Runtime flow

1. A Pyscript app creates a `Manager` for a plate and builds a `Design`.
2. It creates pages and objects; those objects register with the design and
   receive page/object identifiers.
3. The app attaches entity links and callbacks, then sends the design.
4. The manager publishes JSONL and commands over MQTT. When a plate reports
   online, the manager sends the design and selects the startup page.
5. Home Assistant state changes update linked display properties. Plate events
   invoke registered callbacks or Home Assistant services.
6. Pyscript timers support periodic updates such as clock/camera refresh and
   watchdog checks.

The manager subscribes to the plate's `hasp/<plate>/state/#` and `LWT` topics,
as well as openHASP discovery topics. It publishes commands to
`hasp/<plate>/command/<command>`.

## Home Assistant requirements

The library expects an environment with:

- Home Assistant, HACS Pyscript, MQTT configured in Home Assistant, and an
  openHASP plate connected to that broker.
- Pyscript configured with `allow_all_imports: true` and
  `hass_is_global: true`.
- The MQTT dependency enabled for Pyscript as described in the repository
  `README.md`.
- The standard Home Assistant openHASP integration disabled, to prevent it
  from competing with this library.
- The package installed at `pyscript/modules/openhasp`, and application scripts
  copied into `pyscript/apps/` and enabled in Pyscript configuration.

The implementation relies on Pyscript globals, decorators, triggers, and
services. Image features additionally use Pillow and `requests`, write
temporary files under `/config/www/openhasp-pyscript/temp`, and serve them
through Home Assistant's `/local` URL. Image-heavy apps may need a plate with
enough memory, such as a device with PSRAM.

For exact installation steps and configuration snippets, see `README.md`.

## Main versus develop

These branch names refer to branches in this standalone library repository.
They are distinct from the branch of a Home Assistant configuration repository
that may include this project as a submodule.

The standalone `main` branch keeps the library under `modules/openhasp/` and
example applications under `apps/`. `develop` changes the repository layout so
the library files are at the root and examples are under `examples/`. This
allows the repository to be cloned directly into `pyscript/modules/openhasp`;
applications are then copied from `examples/` into the consuming Home
Assistant installation's `pyscript/apps/`.

Before the layout change, `develop` also added:

- `Obj.setBorderColor()` and `Obj.setOpacity()`.
- `Line.setColor()`.
- An optional font argument for `Button.addIcon()`.
- Broader error handling in the library.
- An hourglass placeholder image in the demo when a camera is configured.
- Style entries for `btn.disabled` text/background colors and `climate.off`,
  `climate.cool`, and `climate.heat` colors.

The standalone library does not currently implement a reusable HVAC/climate
control. That functionality exists in the consuming Home Assistant app, in
`pyscript/apps/alarmClocks.py`'s `Climate` class, and appears to be intended as
a future reusable library control. The README's air-conditioner roadmap item
is consistent with that direction, though the library history does not show
the extraction having happened yet.

The app uses `climate.off.color` to gray the HVAC controls when the climate
entity is off. The library also provides `setDisabled()` for suppressing
incoming object events, with disabled text/background/border/icon styling for
buttons. The HVAC app applies it to the adjustable target arc, temperature +/-
buttons, and fan-mode buttons while off; HVAC mode selectors remain enabled so
the user can switch modes. Target-temperature adjustments are also guarded in
the app's callback. This is a small reusable primitive, not a complete climate
control: the HVAC layout, entity bindings, service calls, and mode-specific
logic remain in `pyscript/apps/alarmClocks.py`.

The `develop` branch therefore contains both these feature changes and the
installation-layout migration relative to `main`. Consult the branch README
and commit history when updating an existing installation, since the example
locations and package import layout differ between the branches.

## Examples and project status

- `examples/openhasp_helloWorld.py` is the minimal starting point: it creates
  a manager, page, label, and button, then sends the design.
- `examples/openhasp_demo.py` demonstrates common objects, entity bindings,
  navigation, media controls, images, cameras, and composed objects.
- `examples/openhasp_demo_bambuLab.py` demonstrates a printer-specific
  composed object and plate manager.

The repository does not currently include tracked unit tests or a separate
Python packaging/build configuration. The examples and README are the primary
usage and configuration references.
