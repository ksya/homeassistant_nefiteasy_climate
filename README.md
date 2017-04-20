# Nefit Easy™ Home Assistant component

Let [Home Assistant](http://home-assistant.io) communicate with your Nefit/Bosch smart thermostat.
You can view the current temprature, the status (idle, hot water, heat) and set a target temperature. You can also view some additional data, such as the supply temperature and system pressure.

## Installation

1. First install [Nefit Easy™ HTTP server](https://github.com/robertklep/nefit-easy-http-server)
2. Copy the nefit_easy.py file to `*your homeassistant config dir*/custom_components/climate`
3. Add the compontent to your `configuration.yaml` (see Configuration below)
4. Restart Home Assistant

## Configuration
The default host is localhost, default port is 3000.
```
climate:
  platform: nefit_easy
  host: localhost (optional)
  port: 3000 (optional)
```

You can add custom sensors for the following info:
* supply_temp (system temperature)
* hotwater_active (weather hot water is available)
* heatingstatus (idle, hotwater, heat)
* operating_mode (clock or manual)
* system_pressure (system pressure)
* outdoor_temp (outdoor temperature)

These sensors can be added in the following way in your `configuration.yaml`:

```
sensor nefit:
- platform: template
  sensors:
    nefit_supply_temp: 
      friendly_name: "System temperature"
      value_template: "{{ states.climate.nefit_easy.attributes.supply_temp }}"
      entity_id: 'climate.nefit_easy'
      unit_of_measurement: '°'

binary_sensor nefit:
- platform: template
  sensors:
    nefit_hotwater_active: 
      friendly_name: "Hot water available"
      value_template: "{{ states.climate.nefit_easy.attributes.hotwater_active }}"
      entity_id: 'climate.nefit_easy'
```
