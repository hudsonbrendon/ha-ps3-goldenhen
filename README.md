<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="custom_components/ps3_goldenhen/brand/dark_logo.png">
    <img src="custom_components/ps3_goldenhen/brand/logo.png" alt="PlayStation 3" width="420">
  </picture>
</p>

# PS3 GoldenHEN for Home Assistant

[![Tests](https://github.com/hudsonbrendon/ha-ps3-goldenhen/actions/workflows/tests.yml/badge.svg)](https://github.com/hudsonbrendon/ha-ps3-goldenhen/actions/workflows/tests.yml)
[![Hassfest](https://github.com/hudsonbrendon/ha-ps3-goldenhen/actions/workflows/hassfest.yml/badge.svg)](https://github.com/hudsonbrendon/ha-ps3-goldenhen/actions/workflows/hassfest.yml)
[![Validate](https://github.com/hudsonbrendon/ha-ps3-goldenhen/actions/workflows/validate.yml/badge.svg)](https://github.com/hudsonbrendon/ha-ps3-goldenhen/actions/workflows/validate.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![Release](https://img.shields.io/github/v/release/hudsonbrendon/ha-ps3-goldenhen)](https://github.com/hudsonbrendon/ha-ps3-goldenhen/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Monitor and control a jailbroken **PlayStation 3** (GoldenHEN) from Home Assistant over
the [**webMAN MOD**](https://github.com/aldostools/webMAN-MOD) HTTP API — CPU/RSX
temperatures, fan speed, free memory, firmware, the running game and online status, plus
reboot/shutdown, eject/insert disc, fan control, on-screen popups, the buzzer, and
launch-a-game.

> Talks to webMAN MOD's HTTP server (default port `80`) using its web commands
> (`/cpursx.ps3`, `/shutdown.ps3`, `/restart.ps3`, `/play.ps3`, `/popup.ps3`, …).
> Everything runs on your LAN — no cloud, no account. Not affiliated with Sony or the
> webMAN MOD / GoldenHEN developers.

## Features

- 🎮 **Now playing** — the running game (parsed from webMAN); `unknown` while the console
  sits in the XMB menu.
- 🌡️ **Temperatures** — CPU (CELL) and RSX sensors (°C).
- 🌀 **Fan** — speed sensor (%) plus an optimistic **Fan auto** switch (dynamic ⟷ manual)
  and a `set_fan_speed` service.
- 🧠 **Memory** — free system memory (MB).
- 🧩 **Firmware** — the console's firmware version.
- 📡 **Online status** — a connectivity binary sensor that flips off when the console is
  unreachable (powered off / asleep).
- 🔁 **Power** — Restart, Soft reboot, Hard reboot, and Shutdown buttons.
- 💿 **Disc** — Eject and Insert buttons.
- 🖼️ **Game cover** — an image entity for the running game's cover art (best-effort).
- 🔔 **Popup & buzzer** — a `notify` service to show an on-screen message and a `buzzer`
  service to play the internal buzzer.
- 🚀 **Launch game** — a `launch_game` service to start a game/ISO by path.
- 🏠 **Local polling** — no cloud; talks straight to webMAN MOD on your network.
- 🌐 **Localized** — UI and entities translated to English, Português (Brasil),
  Português, and Español.

> ⚡ **Power-ON is not supported.** The PS3 does not respond to Wake-on-LAN, so the
> integration cannot turn it on over the network (same limitation as RGH/JTAG Xbox 360).
> To power it on remotely, pair this with a smart plug as a separate device — see
> [Power on](#power-on).

## Requirements

**On the console:**

- A jailbroken PS3 running **GoldenHEN** (or another HEN/CFW) **with
  [webMAN MOD](https://github.com/aldostools/webMAN-MOD/releases) installed and running**.
  - GoldenHEN alone is **not enough** — it only enables homebrew. webMAN MOD is what
    exposes the HTTP API.
  - Confirm it works by opening `http://<PS3_IP>/` in a browser — the webMAN panel should
    load.
- A static / reserved IP for the PS3 is recommended.

**On Home Assistant:**

- Home Assistant **2024.12** or newer.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open this repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=hudsonbrendon&repository=ha-ps3-goldenhen&category=integration)

1. In Home Assistant, open **HACS → ⋮ (top right) → Custom repositories**.
2. Add `https://github.com/hudsonbrendon/ha-ps3-goldenhen` and choose the **Integration**
   category — or use the button above.
3. Search for **PS3 GoldenHEN** in HACS, install it, and **restart Home Assistant**.

### Manual

1. Copy `custom_components/ps3_goldenhen/` into your Home Assistant
   `config/custom_components/` directory.
2. Restart Home Assistant.

## Setup

1. Go to **Settings → Devices & Services → Add Integration → PS3 GoldenHEN**.
2. Enter the PS3's **host (IP address)** and **port** (default `80`).

You can later change the polling interval via **Configure** (options flow).

## Entities

### Binary sensor

| Entity | Description |
|--------|-------------|
| `binary_sensor.<name>_online` | On while webMAN MOD is reachable; off when the console is unreachable. |

### Sensors

| Entity | Description |
|--------|-------------|
| `sensor.<name>_cpu_temperature` | CPU (CELL) temperature (°C) |
| `sensor.<name>_rsx_temperature` | RSX (GPU) temperature (°C) |
| `sensor.<name>_fan_speed` | Fan speed (%) |
| `sensor.<name>_free_memory` | Free system memory (MB) |
| `sensor.<name>_firmware` | Firmware version (diagnostic) |
| `sensor.<name>_current_game` | Running game, or `unknown` in the XMB |

### Switch (optimistic)

| Entity | Description |
|--------|-------------|
| `switch.<name>_fan_auto` | On = dynamic (auto) fan, off = manual. State is optimistic. |

### Buttons

| Entity | Web command |
|--------|-------------|
| `button.<name>_restart` | `/restart.ps3` |
| `button.<name>_soft_reboot` | `/reboot.ps3?soft` |
| `button.<name>_hard_reboot` | `/reboot.ps3?hard` |
| `button.<name>_shutdown` | `/shutdown.ps3` |
| `button.<name>_eject` | `/eject.ps3` |
| `button.<name>_insert` | `/insert.ps3` |

### Image

| Entity | Description |
|--------|-------------|
| `image.<name>_game_cover` | Cover art of the running game (best-effort; see notes). |

## Services

| Service | Description |
|---------|-------------|
| `ps3_goldenhen.notify` | Show an on-screen popup on the PS3. |
| `ps3_goldenhen.buzzer` | Play the internal buzzer (pattern `0`–`9`). |
| `ps3_goldenhen.launch_game` | Launch a game/ISO by path (e.g. `/dev_hdd0/PS3ISO/Game.iso`). |
| `ps3_goldenhen.set_fan_speed` | Set the fan speed (0–100%, manual mode). |

## Power on

The PS3 has **no Wake-on-LAN**, so this integration cannot turn the console on over the
network. Reboot/shutdown work normally (via webMAN); only powering *on* is out of reach.

To turn it on remotely, pair this with a **smart plug**: switch the plug on and the PS3
boots if its "auto power on" is enabled (or use the physical power button). You can then
build an automation that turns the plug on before using the console.

## Notes & limitations

- ⚡ **No power-on** — the PS3 doesn't support Wake-on-LAN; use a smart plug (above).
- 🖼️ **Game cover & current game** depend on the exact HTML that *your* webMAN version
  returns from `/cpursx.ps3`. The parser targets the common format; on some versions the
  current game and/or cover may stay empty until the parser is tuned to your console's
  output.
- 🌀 **Fan switch is optimistic** — webMAN doesn't reliably report the fan mode, so the
  switch assumes its state after sending the command.
- 🌐 **LAN only, no auth** — webMAN MOD's HTTP server is unauthenticated by design; keep
  your PS3 on a trusted network.

## License

[MIT](LICENSE)
