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
ATTR_HEATINGMETHOD = 'heatingmethod'
ATTR_OP_MODE = 'operating_mode'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_HOST, default='localhost'): cv.string,
    vol.Optional(CONF_PORT, default=3000): cv.port
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the Nefit Easy thermostat."""
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)

    add_devices([NefitEasyThermostat(host, port)])
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

        update_url = 'http://{}:{}{}'.format(self._host, self._port, '/api/status')

        try:
            with urllib.request.urlopen(update_url) as url:
                data = json.loads(url.read())

        except HTTPError as ex:
            _LOGGER.error(ex.read())
            return

        self._current_temperature = data['in house temp']
        self._target_temperature = data['temp setpoint']
        self._state = data['boiler indicator']  #'boiler indicator' : { 'CH' : 'central heating', 'HW' : 'hot water', 'No' : 'off' }
        self._usermode = data['user mode']

    @property
    def device_state_attributes(self):
        """Return the device specific state attributes."""
        return {
            ATTR_HEATINGMETHOD: self._state,
            ATTR_OP_MODE: self._usermode
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
        if state == 'central heating':
            return STATE_HEAT
        elif state == 'hot water':
            return STATE_HOTWATER
        elif state == 'off':
            return STATE_IDLE

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

