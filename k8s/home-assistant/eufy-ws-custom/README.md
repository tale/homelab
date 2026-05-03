# eufy-security-ws (custom build)

Builds [bropat/eufy-security-ws](https://github.com/bropat/eufy-security-ws)
against a fork of [bropat/eufy-security-client](https://github.com/bropat/eufy-security-client)
that adds Smart Lock C33 (T85L0) support over Eufy's `security-mqtt` broker.

The fork's `feat/t8l50-smart-lock-c33` branch layers
[nick-pape's PR #797](https://github.com/bropat/eufy-security-client/pull/797)
(`SecurityMQTTService` for MQTTS-based locks) plus a fix to skip the legacy
P2P address lookup when a device should use security MQTT, plus the T85L0
device-type registration.

Once nick-pape's MQTTS work is merged upstream and a new
`bropat/eufy-security-ws` image bundles it, this Dockerfile and the
`ghcr.io/tale/eufy-security-ws:mqtt-lock` tag can be retired in favor of the
upstream image.

## Build

```sh
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ghcr.io/tale/eufy-security-ws:mqtt-lock \
  --push .
```
