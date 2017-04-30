"""
Support for the Nefit Easy thermostat using the NodeJS library nefit-easy-core and nefit-easy-http-server

https://github.com/robertklep/nefit-easy-core
https://github.com/robertklep/nefit-easy-http-server
"""
import logging
import json
import urllib.request
from urllib.error import HTTPError

import voluptuous as vol

from homeassistant.components.climate import (
    STATE_HEAT, STATE_IDLE,
    ClimateDevice, PLATFORM_SCHEMA)
from homeassistant.const import (
    TEMP_CELSIUS, ATTR_TEMPERATURE, CONF_HOST, CONF_PORT)
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = []

_LOGGER = logging.getLogger(__name__)

STATE_HOTWATER = 'hotwater'

ATTR_HEATINGSTATUS = 'heatingstatus'
ATTR_OP_MODE = 'operating_mode'
ATTR_HOTWATER_ACTIVE = 'hotwater_active'
ATTR_SUPPLYTEMP = 'supply_temp'
ATTR_OUTDOOR_TEMP = 'outdoor_temp'
ATTR_SYSTEM_PRESSURE = 'system_pressure'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST, default='localhost'): cv.string,
    vol.Optional(CONF_PORT, default=3000): cv.port
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Nefit Easy thermostat."""
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)

    nefit = NefitEasyThermostat(host, port)

    add_devices([nefit])

    return True


class NefitEasyThermostat(ClimateDevice):
    """Representation a Nefit Easy thermostat."""

    def __init__(self, host, port):
        """Initialize the thermostat."""
        self._host = host
        self._port = port
        self._current_temperature = None
        self._target_temperature = None
        self._state = None
        self._usermode = None
        self._hotwater_active = None
        self._supply_temp = None
        self._outdoor_temp = None
        self._system_pressure = None

        # initial data
        self.update()

    def postUrl(self, location, data):
        url = 'http://{}:{}{}'.format(self._host, self._port, location)
        try:
            request = urllib.request.Request(
                url,
                data=json.dumps({"value" : data}).encode("utf-8"),
                headers={'Content-type': 'application/json'})

            with urllib.request.urlopen(request) as response:
                response_body = response.read().decode("utf-8")
                _LOGGER.debug(response_body)
        except HTTPError as ex:
            _LOGGER.error(ex.read())
            return

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Nefit Easy'

    @property
    def should_poll(self):
        """Polling needed for thermostat."""
        return True

    def update(self):
        """Update the data from the thermostat."""

        update_url_status = 'http://{}:{}{}'.format(self._host, self._port, '/bridge/ecus/rrc/uiStatus')
        update_url_supply = 'http://{}:{}{}'.format(self._host, self._port, '/bridge/heatingCircuits/hc1/actualSupplyTemperature')
        update_url_outdoor = 'http://{}:{}{}'.format(self._host, self._port, '/bridge/system/sensors/temperatures/outdoor_t1')
        update_url_pressure = 'http://{}:{}{}'.format(self._host, self._port, '/bridge/system/appliance/systemPressure')

        try:
            with urllib.request.urlopen(update_url_status) as url:
                data = json.loads(url.read().decode("utf-8"))
            with urllib.request.urlopen(update_url_supply) as url:
                data_supply = json.loads(url.read().decode("utf-8"))
            with urllib.request.urlopen(update_url_outdoor) as url:
                data_outdoor = json.loads(url.read().decode("utf-8"))
            with urllib.request.urlopen(update_url_pressure) as url:
                data_pressure = json.loads(url.read().decode("utf-8"))

        except HTTPError as ex:
            _LOGGER.error(ex.read())
            return

        try:
            self._current_temperature = float(data['value']['IHT'])
            self._target_temperature = float(data['value']['TSP'])
            self._state = data['value']['BAI']
            self._usermode = data['value']['UMD']
            self._hotwater_active = (data['value']['DHW'] == 'on')

            self._supply_temp = float(data_supply['value'])

            self._outdoor_temp = float(data_outdoor['value'])
            
            self._system_pressure = float(data_pressure['value'])
        except:
            _LOGGER.error('Nefit api returned invalid data')

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        return {
            ATTR_HEATINGSTATUS: self._state,
            ATTR_OP_MODE: self._usermode,
            ATTR_HOTWATER_ACTIVE: self._hotwater_active,
            ATTR_SUPPLYTEMP: self._supply_temp,
            ATTR_OUTDOOR_TEMP: self._outdoor_temp,
            ATTR_SYSTEM_PRESSURE: self._system_pressure
        }

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def current_operation(self):
        """Return the current state of the thermostat."""
        state = self._state
        if state == 'CH':
            return STATE_HEAT
        elif state == 'HW':
            return STATE_HOTWATER
        elif state == 'No':
            return STATE_IDLE

    @property
    def min_temp(self):
        """Set min temp to limit unrealistic temperatures."""
        return convert_temperature(15, TEMP_CELSIUS, self.temperature_unit)

    @property
    def max_temp(self):
        """Set max temp to limit unrealistic temperatures."""
        return convert_temperature(26, TEMP_CELSIUS, self.temperature_unit)

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        #set temp
        if self._usermode == 'manual':
            self.postUrl('/bridge/heatingCircuits/hc1/temperatureRoomManual', temperature)
        else:
            self.postUrl('/bridge/heatingCircuits/hc1/manualTempOverride/temperature', temperature)
            self.postUrl('/bridge/heatingCircuits/hc1/manualTempOverride/status', 'on')
