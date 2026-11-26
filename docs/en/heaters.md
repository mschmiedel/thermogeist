# Heaters with stages

**English** | [Deutsch](../de/heaters.md)

Some heaters are not controlled by a valve but switched: a smart plug or relay in front of a fan
convector (plinth heater), an infrared panel, an electric towel rail, a fan heater with several
stages. Thermogeist controls them like radiators – same room target, same windows and central
mode – but switches them on and off instead of moving a valve.

A room has **either thermostats or heaters**. Combining both in one room (e.g. a fan as booster
on a radiator with a valve) is planned.

## Adding a heater

Room → gear icon → **Add heater** (when creating a room: *Add a heater*).

| Field | What to enter |
|---|---|
| Switch | The entity that switches the heater on and off (`switch` or `input_boolean`). |
| Heat from | **Heating circuit** when the heat comes from the heating water (plinth heater, fan convector): its output then depends on the flow temperature, like a radiator. **Electric** for infrared, fan heaters and electric towel rails: the output is fixed. |
| Number of stages | 1 for a plain on/off heater. |
| Heat output per stage | One value per stage in W, from low to high, separated by commas: `1300, 1700`. Heating circuit: the output at 75/65/20 °C from the data sheet. Electric: the output itself. **Not** the power the fan draws – a fan that draws 22 W can move 1700 W of heat. |

Under **Stages and details**:

| Field | What to enter |
|---|---|
| Stage sensor | An entity that says which stage runs: `0` = not running, `1`, `2` … (see [Templates](#templates)). Required for more than one stage unless you have a stage setter. Also reports a heater that is switched on but does not run. |
| Stage setter | A `number` or `input_number` that takes the stage `1`, `2` … and switches your device. Without it Thermogeist only switches on and off, and the heater keeps the stage it is set to. |
| Heat output while off | Heat the heater gives while switched off, e.g. heating water flowing through a plinth heater whose fan stands. From the data sheet, usually 0. |
| Exponent | Only for the heating circuit: how the output changes with the water temperature. Radiators 1.3 (default), fan convectors about 1.0. With 1.0 a fan convector gives much more at a low flow temperature than a radiator with the same rated output. |

## How Thermogeist switches

Thermogeist plans a share of the heater's top output, e.g. 60 %. Within a cycle of 20 minutes it
then runs the heater on the two stages around that share:

- **With a stage setter** it picks the lowest stages that cover the demand: a small demand
  switches between off and stage 1, a large one between stage 1 and stage 2. That is quieter
  than switching the top stage on and off.
- **Without a stage setter** it switches between off and the stage the heater runs on (from the
  stage sensor, otherwise the top stage).

Each stage runs at least 5 minutes, so relay and fan do not switch every minute. What a cycle
cannot run because of that is added to the next one, so even a small demand is met on average.
A new plan applies from the next cycle; an open window or the central stop switch off at once.

In **observe mode** the heater only shows what it would do (attribute `planned_stage`); in
**control mode** Thermogeist sets the switch and the stage setter. When you switch control off,
both go back to the state they had before.

## Templates

Thermogeist does not know your device. Two small templates adapt it.

**Stage sensor from the power of a smart plug** (a fan that draws about 11 W on stage 1 and
22 W on stage 2; the limits lie between the values):

```yaml
template:
  - sensor:
      - name: "Plinth heater stage"
        state: >
          {% set w = states('sensor.plinth_plug_power') | float(0) %}
          {{ 0 if w < 5 else 1 if w < 16 else 2 }}
```

**Stage setter for a heater with two relays** (one output per stage):

```yaml
template:
  - number:
      - name: "Fan heater stage"
        min: 1
        max: 2
        step: 1
        state: "{{ 2 if is_state('switch.fan_heater_high', 'on') else 1 }}"
        set_value:
          - action: "switch.turn_{{ 'on' if value | int == 2 else 'off' }}"
            target:
              entity_id: switch.fan_heater_high
```

## What you see

- **Stage *heater*** – the stage that runs now. Attributes: `planned_stage`, `lower_stage`,
  `upper_stage`, `upper_share_pct` (share of the cycle on the upper stage), `cycle_started`,
  `on_since` / `off_since`, `heat_output_w`, `stage_source` (`stage_sensor`, `stage_setter` or
  `switch`) and what you entered.
- **Planned heat share** on the room – the share of the heaters' top output Thermogeist plans,
  with the same parts as the planned valve position of radiators.
- **Estimated radiator output** – the output of the running stage at the current temperatures.
- **_heater_ not running** (only with a stage sensor) – see the
  [FAQ](faq/heater_not_running.md).

The radiator size check is not done for rooms with heaters: it assumes radiators with valves.
