# Nilan Connect
Component to directly integrate Nilan Gateway and Genvex Connect devices into Home Assistant.
The integrationen uses a custom libary [Nilan Proxy](https://github.com/HairingX/nilan_proxy) which handles all communication with the devices locally. Have a look in that repo for more information about the more technical side of the project.

This integration needs the user to have a Nilan Gateway or Genvex Connect connected to their device or own the newer Optima devices, which already have integrated gateways.

### Supported controller models
|Controller         | Gateway requiured     | Supported       | Tested  |
|------------------:|:---------------------:|:---------------:|:-------:|
|Optima 250         | Yes, internet gateway | ✅              |       |
|Optima 251         | Yes, internet gateway | ✅              |       |
|Optima 260         | Yes, internet gateway | ✅              |         |
|Optima 270         | Built in              | ✅              |      |
|Optima 301         | Yes, internet gateway | ✅              |      |
|Optima 312         | Yes, internet gateway | ✅              |         |
|Optima 314         | Built in              | ✅              |         |
|Nilan CTS400       | Yes, nilan gateway    | ✅              | ✅     |
|Nilan CTS602       | Yes, nilan gateway    | ✅              |      |
|Nilan CTS602 Light | Yes, nilan gateway    | ✅              |         |
|Nilan CTS602 Geo   | Yes, nilan gateway    | ✅              |         |

## Installation (HACS)

The preferred method to install is to use HACS. You need to add this repo https://github.com/HairingX/nilan_connect as a custom repo. See https://hacs.xyz/docs/faq/custom_repositories for details.

## Installation (No HACS)

If you don't have/want HACS installed, you will need to manually install the integration

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. Drag the `custom_components` folder into your HA configuration folder.
3. Restart Home Assistant

## Setup
To setup the integration, go into "Configuration" -> "Integrations" and press on the "+" button. Find Nilan Connect from the list.
The integration should search for your device and let you choose which one to use. You then need to provide it with the same email as used in the Nilan or Genvex Connect app. This is case sensitive.
Then if all goes well, your device should be added and working in Home Assistant.

### Device addresses and DHCP
When you pick a discovered device, only the device id is stored, never its IP address. The address is looked up again through discovery every time Home Assistant starts, and also while reconnecting after a dropped connection. Your device is therefore free to get a new address from DHCP, and you do **not** need to give it a static IP.

The "Manual" option is a fallback for networks where the discovery broadcast does not reach the device, for example when it sits on another subnet or VLAN. It stores the address you type, so in that case you should give the device a static IP or a DHCP reservation, otherwise the integration stops working when the address changes. Only literal IPv4 addresses are accepted here, hostnames are not.

## Warning
Some users have posted, that Nilan have locked them out of their gateway after accessing it with other devices than their app.
I cannot confirm the validity of the posts, but to avoid getting into that situation i recommend that you

**Block all internet access for your Nilan Gateway, and only access it through the Home Assistant integration, if you choose to use that.**

## A little note to Genvex/Nilan
I know fully well that you have the ability to remotely update your devices and closing local connections are quite simple to do.
Please do not use that power irresponsibly.
The method of connecting locally does require you to know the exact email used in the app and the capabilities are the same as the ones your users connecting directly through Modbus have.
This shouldn't be a security concern and only gives your Gateway solutions much more value to the end user.

# Obligatory statement
I am not personally or in any way responsible for any damages should you choose to use the integration. No warranty provided.
Be especially observant when trying the integration with untested controller models and settings values.

## Credit
This library would not be possible without the time and effort put in by superrob, who initiated this integration.
I branched out this codebase to tailor it mainly towards Nilan units. It ended up being a big code overhaul to get it where I wanted it.

In the end the solution provided an improved home assistant device for Nilan and Genvex units.

For more info on the original solution, you can find superrob's repository here: https://github.com/superrob/genvexconnect

# Example Card
The device can be displayed in many ways. Here is an example of how I like it displayed for inspiration:

![image](https://github.com/user-attachments/assets/446f2ad9-af58-4585-ad68-cb884363be71)

Explanations on the values in the card:
- At the inlets and outlets the temperature and fan speed % is displayed.
- In the center of the unit, bypass/defrost/ventilation state is displayed by 3 different icons.
- Above the unit the efficiency percentage is displayed.
- Below the unit the active state (Auto/OFF) and active level is displayed.
- Below that is the humidity %
- In the bottom the filter change is displayed.
- When an alarm is active a big red alert icon will be displayed beside the filter change.

Below the house i have placed general controls to handle the unit.

Note that the card needs two background images for it to be displayed correctly in both light and dark modes. The images should be copied into the `www` folder of Home Assistant to be accessed by the card.

The `www` folder is typically located in the config directory where you find `configuration.yaml`, `automations`, `blueprints`, etc. If the `www` folder does not exist, you can create it and place the images inside.

You find the background images in the `assets` folder of this repository.
- assets/hvac_background_dark.png
- assets/hvac_background_light.png

Here is the code for the card above:
```yaml
type: vertical-stack
cards:
  - type: picture-elements
    elements:
      - entity: sensor.nilan_temperature_outside_air
        style:
          color: var(--primary-text-color)
          font-size: 150%
          left: 30.5%
          top: 7.0%
        type: state-label
      - entity: sensor.nilan_temperature_exhaust_air
        style:
          color: var(--primary-text-color)
          font-size: 150%
          left: 71.5%
          top: 7.0%
        type: state-label
      - entity: sensor.nilan_temperature_extract_air
        style:
          color: var(--primary-text-color)
          font-size: 150%
          left: 30.5%
          top: 66.5%
        type: state-label
      - entity: sensor.nilan_temperature_supply_air
        style:
          color: var(--primary-text-color)
          font-size: 150%
          left: 71.5%
          top: 66.5%
        type: state-label
      - entity: sensor.nilan_humidity
        style:
          color: var(--primary-text-color)
          font-size: 130%
          left: 51.0%
          top: 79.2%
        type: state-label
      - entity: select.nilan_fan_level
        style:
          color: var(--primary-text-color)
          font-size: 100%
          left: 50.0%
          top: 60.0%
        type: state-label
      - entity: sensor.nilan_fan_speed_supply
        style:
          color: var(--primary-text-color)
          font-size: 100%
          left: 76.0%
          top: 55.0%
        type: state-label
      - entity: sensor.nilan_fan_speed_extract
        style:
          color: var(--primary-text-color)
          font-size: 100%
          left: 24.0%
          top: 55.0%
        type: state-label
      - entity: sensor.nilan_efficiency
        style:
          color: var(--primary-text-color)
          font-size: 100%
          left: 50.0%
          top: 25.2%
        type: state-label
      - entity: climate.nilan_hvac
        style:
          color: var(--primary-text-color)
          font-size: 100%
          left: 50.0%
          top: 55.2%
        type: state-label
      - entity: sensor.nilan_next_filter_change
        style:
          color: var(--primary-text-color)
          font-size: 130%
          left: 51.0%
          top: 91%
        type: state-label
      - type: icon
        icon: mdi:air-filter
        style:
          left: 42.0%
          top: 91%
      - type: conditional
        conditions:
          - entity: binary_sensor.nilan_defrost_active
            state: "on"
        elements:
          - entity: binary_sensor.nilan_defrost_active
            type: icon
            icon: mdi:snowflake-melt
            style:
              background-color: var(--card-background-color)
              border-radius: 50%
              color: var(--primary-text-color)
              left: 49.7%
              top: 40.3%
              transform: translate(-50%, -50%) scale(3,3)
        title: Defrost Indicator
      - type: conditional
        conditions:
          - entity: binary_sensor.nilan_defrost_active
            state: "off"
          - entity: binary_sensor.nilan_bypass_active
            state: "on"
        elements:
          - entity: binary_sensor.nilan_bypass_active
            type: icon
            icon: mdi:valve-open
            style:
              background-color: var(--card-background-color)
              border-radius: 50%
              color: var(--primary-text-color)
              left: 49.7%
              top: 40.3%
              transform: translate(-50%, -50%) scale(3,3) rotate(90deg)
        title: Bypass indicator
      - type: conditional
        conditions:
          - condition: state
            entity: binary_sensor.nilan_bypass_active
            state: "on"
        elements:
          - type: icon
            icon: hidden
            style:
              background-color: var(--card-background-color)
              left: 49.7%
              top: 25%
              transform: translate(-50%, -50%) scale(3,1)
        title: Bypass hide efficiency
      - type: conditional
        conditions:
          - condition: state
            entity: binary_sensor.nilan_alarm_status
            state: "on"
        elements:
          - type: icon
            icon: mdi:alert
            style:
              color: red
              right: 25%
              bottom: 12%
              transform: translate(-50%, -50%) scale(2.5)
            entity: binary_sensor.nilan_alarm_status
        title: Alarm ON
    image: /local/hvac_background_light.png
    dark_mode_image: /local/hvac_background_dark.png
  - type: entities
    entities:
      - entity: climate.nilan_hvac
      - entity: button.nilan_reset_filter
        secondary_info: none
      - entity: button.nilan_reset_alarm
    show_header_toggle: false
    state_color: false
```
