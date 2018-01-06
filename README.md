# wow-addon-manager
A simple addon manager for World of Warcraft, inspired by [wow-addon-updater](https://github.com/kuhnerdm/wow-addon-updater).

:warning: **Warning:** This addon manager will delete all files in the `AddOns` folder that are not part of the managed addons, so please configure it before using.

## Requirements
- Python 3

## Configuration
Set the `WoWAddonFolder` variable in `config.ini` and add your addons, as shown by `[Example]`.

Set the `IgnoreVersion` variable (optional) to `yes` if you want to always download the latest version. This is useful for addons like [The Undermine Journal on CurseForge](https://www.curseforge.com/wow/addons/undermine-journal), which has no version specified.

### Supported sites:
- [CurseForge](https://www.curseforge.com/wow/addons)
- [WoWInterface](https://wowinterface.com/addons.php)
- [Tukui](https://www.tukui.org/download.php?ui=tukui) and [ElvUI](https://www.tukui.org/download.php?ui=elvui) (including [addons](https://www.tukui.org/addons.php))
- [WowAce](https://www.wowace.com/addons)

## Usage
```bash
./wow-addon-manager.py
# or
python3 wow-addon-manager.py
```

## License
[MIT](LICENSE)
