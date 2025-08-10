# Home Assistant
[Home Assistant](https://home-assistant.io) is a nice home automation platform.
I prefer it over something like Homebridge because its a lot more mature,
stable, and useful, while still supporting the HomeKit integrations that we
use in our home.

### Setup
- Custom namespace with lax security context to allow host networking
- Home Assistant runs using host networking for discovery
- Web UI is publicly accessible through Envoy gateway
