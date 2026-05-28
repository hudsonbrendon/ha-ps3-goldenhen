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
reboot/shutdown, eject/insert disc, fan control, on-screen popups, the buzzer, launch a
game, LED control, memory peek/poke, raw commands, and console diagnostics.

> Talks to webMAN MOD's HTTP server (default port `80`) and ps3mapi using its web commands
> (`/cpursx.ps3`, `/shutdown.ps3`, `/restart.ps3`, `/play.ps3`, `/popup.ps3`, `/ps3mapi.ps3`, …).
> Everything runs on your LAN — no cloud, no account. Not affiliated with Sony or the
> webMAN MOD / GoldenHEN developers.

## Features

- 🎮 **Now playing** — the running game (parsed from webMAN); `unknown` while the console
  sits in the XMB menu.
- 🌡️ **Temperatures** — CPU (CELL) and RSX sensors (°C).
- 🌀 **Fan** — speed sensor (%), fan mode sensor, **Fan auto** switch, fan speed **number**
  (0–100 %, slider), fan target temperature **number** (40–80 °C), and a **Fan mode select**
  (Dynamic / Manual).
- 🧠 **Memory** — free system memory (KB) and free HDD space (GB).
- 🧩 **Firmware** — the console's firmware version.
- ⏱️ **Uptime & boot count** — total runtime string and boot-on counter sensor.
- 🖥️ **Console diagnostics** — console type (CEX/DEX/COBRA), HEN version, webMAN version,
  connection type (WLAN/LAN), MAC address, Blu-ray drive model, and flash type (NOR/NAND).
- 📡 **Online status** — a connectivity binary sensor that flips off when the console is
  unreachable (powered off / asleep).
- 🐍 **COBRA mode** — binary sensor reporting whether COBRA firmware is active.
- 🎮 **Game running** — binary sensor that is on while a game is active.
- 🔁 **Power** — Restart, Soft reboot, Hard reboot, Quick reboot, and Shutdown buttons.
- 💿 **Disc** — Eject and Insert buttons.
- 🌀 **Fan buttons** — Fan + and Fan − step buttons.
- 📂 **Game management** — Refresh games and Unmount game buttons.
- 🔔 **Beep** — Beep ×1, ×2, and ×3 buttons.
- 🖼️ **Game images** — image entities for the running game's cover art and background
  (PIC1) (best-effort).
- 🔔 **Popup & buzzer** — a `notify` service (with optional icon/sound) to show an
  on-screen message and a `buzzer` service to play the internal buzzer.
- 🚀 **Launch & mount** — `launch_game` and `mount` services to start or mount a game/ISO
  by path.
- 💡 **LED control** — `led` service to set the PS3 LED color and mode via ps3mapi.
- 🧬 **Memory peek/poke** — `read_memory` (returns data) and `write_memory` (⚠️ advanced)
  services via ps3mapi.
- 📡 **Raw command** — `send_command` service to fire any webMAN web command directly.
- 📣 **Events** — fires `ps3_goldenhen_event` on the HA event bus when the running game
  changes, enabling automations.
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

### Media player

| Entity | Description |
|--------|-------------|
| `media_player.<name>` | PlayStation 3 media player (receiver class). State: `off` when unreachable, `playing` while a game runs, `idle` in the XMB. Supports `select_source` (launches a game from `/dev_hdd0/game` via PARAM.SFO) and `turn_off` (shutdown). Game list populated from `/dev_hdd0/game` PARAM.SFO files. |

### Binary sensors

| Entity | Description |
|--------|-------------|
| `binary_sensor.<name>_online` | On while webMAN MOD is reachable; off when the console is unreachable. |
| `binary_sensor.<name>_game_running` | On while a game is actively running (not in the XMB menu). |
| `binary_sensor.<name>_cobra_mode` | On when the console is running under COBRA firmware (diagnostic). |

### Sensors

| Entity | Description |
|--------|-------------|
| `sensor.<name>_cpu_temperature` | CPU (CELL) temperature (°C) |
| `sensor.<name>_rsx_temperature` | RSX (GPU) temperature (°C) |
| `sensor.<name>_fan_speed` | Fan speed (%) |
| `sensor.<name>_free_memory` | Free system memory (KB) |
| `sensor.<name>_hdd_free` | HDD free space (GB) |
| `sensor.<name>_firmware` | Firmware version |
| `sensor.<name>_current_game` | Running game, or `unknown` in the XMB |
| `sensor.<name>_runtime` | Total runtime string (e.g. `178d 02:32:24`) — diagnostic |
| `sensor.<name>_boots_on` | Number of power-on boots — diagnostic |
| `sensor.<name>_fan_mode` | Current fan mode (`Dynamic` / `Manual`) |
| `sensor.<name>_console_type` | Console type (e.g. `CEX COBRA`) — diagnostic |
| `sensor.<name>_hen_version` | HEN version string (e.g. `PS3HEN 3.3.0`) — diagnostic |
| `sensor.<name>_webman_version` | webMAN MOD version string — diagnostic |
| `sensor.<name>_connection` | Network connection type (`WLAN` / `LAN`) — diagnostic |
| `sensor.<name>_mac_address` | Console MAC address — diagnostic |
| `sensor.<name>_bd_drive` | Blu-ray drive model string — diagnostic |
| `sensor.<name>_flash_type` | Flash type (`NOR` / `NAND`) — diagnostic |
| `sensor.<name>_game_title_id` | Title ID of the running game (e.g. `NPUA80637`) — diagnostic |

### Switch (optimistic)

| Entity | Description |
|--------|-------------|
| `switch.<name>_fan_auto` | On = dynamic (auto) fan, off = manual. Reflects real fan_mode when available. |

### Number

| Entity | Description |
|--------|-------------|
| `number.<name>_fan_speed` | Manual fan speed (0–100 %, step 5). Sends the speed command immediately. |
| `number.<name>_fan_target_temp` | Fan target temperature for dynamic mode (40–80 °C). |

### Select

| Entity | Description |
|--------|-------------|
| `select.<name>_fan_mode_select` | Fan control mode: `Dynamic` or `Manual`. |
| `select.<name>_game_launcher` | Game launcher — options are game names read from `/dev_hdd0/game` PARAM.SFO files; selecting a game launches it via `/play.ps3`. |

### Buttons

| Entity | Web command |
|--------|-------------|
| `button.<name>_restart` | `/restart.ps3` |
| `button.<name>_soft_reboot` | `/reboot.ps3?soft` |
| `button.<name>_hard_reboot` | `/reboot.ps3?hard` |
| `button.<name>_quick_reboot` | `/reboot.ps3?quick` |
| `button.<name>_shutdown` | `/shutdown.ps3` |
| `button.<name>_eject` | `/eject.ps3` |
| `button.<name>_insert` | `/insert.ps3` |
| `button.<name>_fan_up` | `/cpursx.ps3?up` — increase fan one step |
| `button.<name>_fan_down` | `/cpursx.ps3?dn` — decrease fan one step |
| `button.<name>_refresh_games` | `/refresh.ps3` — refresh the game list |
| `button.<name>_unmount` | `/mount.ps3/unmount` — unmount the current game |
| `button.<name>_beep1` | `/beep.ps3?1` — single beep |
| `button.<name>_beep2` | `/beep.ps3?2` — double beep |
| `button.<name>_beep3` | `/beep.ps3?3` — triple beep |

### Image

| Entity | Description |
|--------|-------------|
| `image.<name>_game_cover` | Cover art (ICON0.PNG) of the running game (best-effort). |
| `image.<name>_game_background` | Background art (PIC1.PNG) of the running game (best-effort). |

## Services

| Service | Description |
|---------|-------------|
| `ps3_goldenhen.notify` | Show an on-screen popup. Optional `icon` (0–50) and `sound` (0–9) parameters. |
| `ps3_goldenhen.buzzer` | Play the internal buzzer with a given pattern (0–9). |
| `ps3_goldenhen.launch_game` | Launch a game/ISO by path (e.g. `/dev_hdd0/PS3ISO/Game.iso`). |
| `ps3_goldenhen.mount` | Mount a game/ISO by path without launching it. |
| `ps3_goldenhen.set_fan_speed` | Set the fan speed (0–100 %, manual mode). |
| `ps3_goldenhen.set_fan_target_temp` | Set the fan target temperature for dynamic mode (40–80 °C). |
| `ps3_goldenhen.led` | Set the PS3 LED color and mode via ps3mapi. |
| `ps3_goldenhen.send_command` | Send any raw webMAN web command (e.g. `/popup.ps3/hello`). |
| `ps3_goldenhen.read_memory` | Read process memory via ps3mapi. Returns `{"data": <response>}`. |
| `ps3_goldenhen.write_memory` | ⚠️ Write process memory via ps3mapi. Advanced / potentially dangerous. |

## Events

The integration fires **`ps3_goldenhen_event`** on the Home Assistant event bus whenever
the running game changes (Title ID transitions to a new non-null value).

Event data:

```yaml
type: game_changed
title_id: "NPUA80637"
title: "God of War®: Chains of Olympus (Digital)"
```

Example automation — send a notification when a new game starts:

```yaml
automation:
  trigger:
    - platform: event
      event_type: ps3_goldenhen_event
      event_data:
        type: game_changed
  action:
    - service: notify.mobile_app_my_phone
      data:
        message: "Now playing: {{ trigger.event.data.title }}"
```

## Diagnostics

Download Diagnostics is supported (via **Settings → Devices & Services → your PS3 entry →
⋮ → Download diagnostics**). The report redacts sensitive fields: `mac_address`,
`ip_address`, and `host`.

## Power on

The PS3 has **no Wake-on-LAN**, so this integration cannot turn the console on over the
network. Reboot/shutdown work normally (via webMAN); only powering *on* is out of reach.

To turn it on remotely, pair this with a **smart plug**: switch the plug on and the PS3
boots if its "auto power on" is enabled (or use the physical power button). You can then
build an automation that turns the plug on before using the console.

## Notes & limitations

- ⚡ **No power-on** — the PS3 doesn't support Wake-on-LAN; use a smart plug (above).
- 🖼️ **Game images & current game** depend on the exact HTML that *your* webMAN version
  returns from `/cpursx.ps3`. The parser targets the common format; on some versions the
  current game and/or cover may stay empty until the parser is tuned to your console's
  output.
- 🌀 **Fan switch** reflects the real fan mode reported by webMAN when available (Manual =
  off, any other value = on).
- 🌐 **LAN only, no auth** — webMAN MOD's HTTP server is unauthenticated by design; keep
  your PS3 on a trusted network.
- ⚠️ **write_memory** can crash or corrupt the console process — use with extreme caution.

## License

[MIT](LICENSE)
