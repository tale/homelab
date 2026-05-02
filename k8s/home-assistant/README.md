# Home Assistant

[Home Assistant](https://home-assistant.io) is a nice home automation platform.
I prefer it over something like Homebridge because its a lot more mature,
stable, and useful, while still supporting the HomeKit integrations that we
use in our home.

### Setup

- Custom namespace with lax security context to allow host networking
- Home Assistant runs using host networking for discovery
- Web UI is publicly accessible through Envoy gateway
- [eufy-security-ws](https://github.com/bropat/eufy-security-ws) provides MQTT integration with Eufy cameras and locks
- Scrypted for HomeKit Secure Video integration with a Ring doorbell
