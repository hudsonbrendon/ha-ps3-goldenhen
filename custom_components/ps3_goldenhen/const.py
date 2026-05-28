"""Constants for the PS3 GoldenHEN integration."""

DOMAIN = "ps3_goldenhen"
DEFAULT_NAME = "PlayStation 3"
DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 600
HTTP_TIMEOUT = 10

CONF_SCAN_INTERVAL = "scan_interval"

# webMAN MOD HTTP web commands (relative paths)
CMD_STATUS = "/cpursx.ps3"
CMD_RESTART = "/restart.ps3"
CMD_SOFT_REBOOT = "/reboot.ps3?soft"
CMD_HARD_REBOOT = "/reboot.ps3?hard"
CMD_QUICK_REBOOT = "/reboot.ps3?quick"
CMD_SHUTDOWN = "/shutdown.ps3"
CMD_EJECT = "/eject.ps3"
CMD_INSERT = "/insert.ps3"
CMD_FAN_AUTO = "/cpursx.ps3?dyn"
CMD_FAN_MANUAL = "/cpursx.ps3?man"
CMD_FAN_SPEED = "/cpursx.ps3?fan={speed}"
CMD_POPUP = "/popup.ps3"
CMD_BEEP = "/beep.ps3?{n}"
CMD_PLAY = "/play.ps3"
CMD_PLAY_PATH = "/play.ps3"
GAMES_PATH = "/dev_hdd0/game"
CMD_MOUNT = "/mount.ps3"
CMD_REFRESH = "/refresh.ps3"
CMD_UNMOUNT = "/mount.ps3/unmount"
CMD_FAN_UP = "/cpursx.ps3?up"
CMD_FAN_DOWN = "/cpursx.ps3?dn"
CMD_FAN_TARGET = "/cpursx.ps3?max={temp}"

# Fan modes (rótulos internos)
FAN_MODE_AUTO = "auto"
FAN_MODE_MANUAL = "manual"
