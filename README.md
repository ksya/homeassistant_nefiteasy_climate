# Nefit Easy™ Home Assistant component

Let [Home Assistant](http://home-assistant.io) communicate with your Nefit/Bosch smart thermostat.

Unless you're implementing a client yourself, this library is probably not what you're looking for.

## Installation

1. First install [Nefit Easy™ HTTP server](https://github.com/robertklep/nefit-easy-http-server)
2. Copy the nefit_easy.py file to `*your homeassistant config dir*/custom_components/climate`
3. Add the compontent to your `configuration.yaml`:
```
climate:
  platform: nefit_easy
  host: localhost (optional)
  port: 3000 (optional)
```
Default host is localhost, default port is 3000.
4. Restart Home Assistant