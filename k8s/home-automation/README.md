# home-automation

| Package            | Runs                              | Reached at              |
| ------------------ | --------------------------------- | ----------------------- |
| `home-assistant`   | Home Assistant                    | `home.tale.me`          |
| `eufy-security-ws` | Eufy lock bridge                  | `eufy-security-ws:3000` |
| `scrypted`         | Ring camera, HomeKit Secure Video | node IP, port 10443     |
| `samba`            | SMB share                         | `10.0.0.230`            |

The garage lock (C33 / T85L0) needs the custom `mqtt-lock` image. Upstream 3.1.0
tries P2P instead of MQTT and can't control it; [#797](https://github.com/bropat/eufy-security-client/pull/797)
closed without merging the fix. The Dockerfile is in commit `a1a9968` at
`k8s/home-assistant/eufy-ws-custom/Dockerfile`.
