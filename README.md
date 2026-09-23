# USB Dead Man’s Switch

A Python USB dead man's switch that locks a Windows workstation when its
configured USB device is unplugged.

`usb-dead-mans-switch.py` queries Windows Plug and Play devices through WMI. After all
configured device entries have been detected, it checks approximately every four
seconds and calls `LockWorkStation` when any entry disappears. Reconnecting the
device rearms monitoring; it does not unlock the workstation.

## Requirements and setup

This application requires Python 3 on Windows, WMI, and a USB device to monitor.
The workstation-monitoring code cannot run on Linux or WSL. Its dependencies are
listed in `requirements.txt`, including the required Windows extensions (`pywin32`).

From the repository directory, use your Python environment to install them:

```text
python -m pip install -r requirements.txt
```

## Inspect newly connected devices

Compare devices before and after plugging one in:

```text
python usb-dead-mans-switch.py --baseline
```

Follow the unplug/insert prompts. This prints the names and device IDs of newly
connected Plug and Play devices, then exits without reading or writing
`config.xml` or starting monitoring. If nothing changes, it reports that no new
devices were detected.

The default `pnp` mode uses `Win32_PnPEntity`. To use the original USB-specific
baseline query instead:

```text
python usb-dead-mans-switch.py --baseline usb
```

Baseline mode cannot be combined with `-id` or `--activate`.

## Choose a USB device

Run the identification flow from the repository directory:

```text
python usb-dead-mans-switch.py -id
```

Follow the prompts to establish a baseline with the device unplugged, then plug
it in. The script writes the newly detected device names and IDs to `config.xml`
and asks whether to begin monitoring. This file is machine-specific and ignored
by Git. Run identification again to replace an existing configuration.

The long option is spelled `--idententifyDevice` in the original implementation;
`-id` is the simpler equivalent.

## Monitor the device

With `config.xml` present, start monitoring:

```text
python usb-dead-mans-switch.py
```

Monitoring is enabled by default. The script waits for the configured device to
be connected before arming. Press Ctrl+C in the terminal to stop it.

The active removal action locks the workstation. Process termination is defined
as a helper but is not called by the monitoring loop.

## Supporting files

- `items.xml`: a small XML example, unused by the main script.

## Known limitations

The configuration reader expects multiple `<key>` entries; a device that produces
only one entry may fail to load. Devices with missing WMI captions may also cause
errors. The monitoring logic is preserved from the original script and needs
runtime validation on the intended Windows machine.

## License

Licensed under the GNU General Public License, version 3 or later
(`GPL-3.0-or-later`), matching the notice in the source code. See [LICENSE](LICENSE)
for the full license text.
