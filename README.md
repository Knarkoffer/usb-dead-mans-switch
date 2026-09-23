# USB Dead Man’s Switch

A Python USB dead man's switch that locks a Windows workstation when its
configured USB device is unplugged.

`usb_dead_mans_switch.py` queries Windows Plug and Play devices through WMI. After all
configured device entries have been detected, it checks approximately every four
seconds and calls `LockWorkStation` when any entry disappears. Reconnecting the
device rearms monitoring; it does not unlock the workstation.

## Requirements and setup

This application requires Python 3.10 or newer on Windows, WMI, and a USB device
to monitor. The workstation-monitoring code cannot run on Linux or WSL. Its dependencies are
listed in `pyproject.toml`, including the required Windows extensions (`pywin32`).

From the repository directory, use your Python environment to install them:

```text
python -m pip install .
```

## Inspect newly connected devices

Compare devices before and after plugging one in:

```text
python usb_dead_mans_switch.py --baseline
```

Follow the unplug/insert prompts. This prints the names and device IDs of newly
connected Plug and Play devices, then exits without reading or writing
`config.yaml` or starting monitoring. If nothing changes, it reports that no new
devices were detected.

The default `pnp` mode uses `Win32_PnPEntity`. To query USB-specific
entries instead:

```text
python usb_dead_mans_switch.py --baseline usb
```

Baseline mode cannot be combined with `-id` or `--activate`.

## Choose a USB device

Copy `config.example.yaml` to `config.yaml` in the repository directory:

```powershell
Copy-Item config.example.yaml config.yaml
```

Edit `config.yaml` and replace the dummy `name` and `device_id` with the exact
values printed by `--baseline`. Keep device IDs single-quoted to preserve
backslashes. Add one entry under `devices` for each device entry to monitor;
all entries must be present before monitoring arms. Your `config.yaml` is
ignored by Git; the example contains dummy values only.

Alternatively, generate `config.yaml` using the identification flow:

```text
python usb_dead_mans_switch.py -id
```

Follow the prompts to establish a baseline with the device unplugged, then plug
it in. The script writes the newly detected device names and IDs to `config.yaml`
and asks whether to begin monitoring. This file is machine-specific and ignored
by Git. Run identification again to replace an existing configuration.

## Monitor the device

With `config.yaml` present, start monitoring:

```text
python usb_dead_mans_switch.py
```

Monitoring is enabled by default. The script waits for the configured device to
be connected before arming. Press Ctrl+C in the terminal to stop it.

The active removal action locks the workstation. Process termination is defined
as a helper but is not called by the monitoring loop.

## Known limitations

The monitoring logic needs runtime validation on the intended Windows machine.

## License

Licensed under the GNU General Public License, version 3 or later
(`GPL-3.0-or-later`), matching the notice in the source code. See [LICENSE](LICENSE)
for the full license text.
