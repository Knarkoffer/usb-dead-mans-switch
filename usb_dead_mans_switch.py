#!python3

"""
---------------------------------

USB Dead Man's Switch (Project 483)

My own take on a computer dead man's switch / "You'll never take me alive"-function.
Build to detect specific USB-devices, and act when they are removed/unplugged.

Copyright (c) Knarkoffer 2016

This script is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This script is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

---------------------------------
"""


import argparse
import subprocess
import sys
import time

import wmi
import yaml

dMSDevices = []

localWMI = None

connectedDevices = []

userPrompted = False
firstRunTime = True
deviceIsConnected = None
deviceWasConnected = True


def EstablishBaseline(device_type):
    """Print devices added after an interactive baseline, then return."""
    device_class = {
        "pnp": "Win32_PnPEntity",
        "usb": "Win32_USBDevice",
    }[device_type]
    query = f"select * from {device_class}"
    input("Make sure the device is NOT plugged in, then press Enter")
    baseline = {item.DeviceID for item in localWMI.query(query)}
    input("Baseline established; insert the device, then press Enter")
    found = False
    for item in localWMI.query(query):
        if item.DeviceID not in baseline:
            print("[New device:]")
            print(item.Caption or "(unnamed device)")
            print(item.DeviceID)
            found = True
    if not found:
        print("No new devices detected.")


def CreateKeyfile():
    """Detect newly connected devices and write the YAML configuration."""
    input("Make sure the device is NOT plugged in, then press Enter")
    baseline = {
        item.DeviceID for item in localWMI.query("select * from Win32_PnPEntity")
    }
    input("USB baseline established, please insert device, then press Enter")
    devices = []
    for item in localWMI.query("select * from Win32_PnPEntity"):
        device_id = item.DeviceID
        if (
            device_id not in baseline
            and "STORAGE#VOLUME#" not in device_id
            and "USBSTOR#DISK" not in device_id
        ):
            devices.append(
                {"name": item.Caption or "(unnamed device)", "device_id": device_id}
            )

    if not devices:
        sys.exit("Problems detecting your key, exiting script")

    try:
        with open("config.yaml", "w", encoding="utf-8") as config_file:
            yaml.safe_dump(
                {"devices": devices}, config_file, sort_keys=False, allow_unicode=True
            )
    except OSError as exc:
        sys.exit(f"Cannot write config.yaml: {exc}")

    dMSDevices[:] = [device["name"] + "|" + device["device_id"] for device in devices]
    if not query_yes_no("config.yaml created successfully, start monitoring?"):
        sys.exit("Exiting script")


def ReadKeyfile():
    """Read and validate the user-owned YAML configuration."""
    print("Reading config.yaml")
    try:
        with open("config.yaml", encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)
    except FileNotFoundError:
        sys.exit(
            "config.yaml not found. Copy config.example.yaml to config.yaml "
            "and enter your device values, or run with -id."
        )
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        sys.exit(f"Cannot read config.yaml: {exc}")

    if not isinstance(config, dict) or set(config) != {"devices"}:
        sys.exit(
            "Invalid config.yaml: expected a 'devices' list as the only top-level key."
        )
    devices = config["devices"]
    if not isinstance(devices, list) or not devices:
        sys.exit("Invalid config.yaml: 'devices' must be a non-empty list.")

    configured = []
    for index, device in enumerate(devices, start=1):
        if (
            not isinstance(device, dict)
            or set(device) != {"name", "device_id"}
            or any(
                not isinstance(device[key], str) or not device[key].strip()
                for key in ("name", "device_id")
            )
        ):
            sys.exit(
                f"Invalid config.yaml: device {index} must contain non-empty "
                "strings for 'name' and 'device_id' only."
            )
        configured.append(device["name"] + "|" + device["device_id"])
    dMSDevices[:] = configured


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
    It must be "yes" (the default), "no" or None (meaning
    an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}

    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError(f"invalid default answer: '{default}'")
    #

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()

        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")
        #
    #


#


def ShutdownProcess(processName, returnOutput):

    results = subprocess.Popen(
        "taskkill /IM " + str(processName) + " /F", shell=True, stdout=subprocess.PIPE
    ).stdout.read()

    if returnOutput:
        results = results.decode()
    else:
        results = "Command executed!"
    #

    return results


#


def ExecuteCommand(stringCommand, returnOutput):

    results = subprocess.Popen(
        stringCommand, shell=True, stdout=subprocess.PIPE
    ).stdout.read()

    if returnOutput:
        results = results.decode()
    else:
        results = "Command executed!"
    #

    return results


#


def CheckKeyConnected():

    expectedDevices = dMSDevices
    connectedDevices = []

    for item in localWMI.query("select * from Win32_PnPEntity"):

        deviceName = item.Caption or "(unnamed device)"
        deviceID = item.DeviceID

        # print('deviceName: ' + str(deviceName))
        # print('deviceID: ' + str(deviceID))

        connectedDevices.append(deviceName + "|" + deviceID)
        pass
    #

    foundDevices = set(expectedDevices).intersection(connectedDevices)

    # print('Overlapping devices found: ' + str(foundDevices))#XYZZY

    if len(foundDevices) == len(expectedDevices):
        deviceConnected = True
        # print('All devices connected')
    else:
        deviceConnected = False
        # print('Not all devices connected')

    #
    return deviceConnected


#


def dualOutput(informationString):

    # timeStamp = time.strftime("%Y-%m-%d %H:%M:%S")
    timeStamp = time.strftime("%H:%M:%S")

    print("[" + timeStamp + "] " + informationString)


#


def StartMonitoring():

    global firstRunTime
    global deviceIsConnected
    global deviceWasConnected
    global userPrompted

    while True:

        if firstRunTime:
            while firstRunTime:

                deviceIsConnected = CheckKeyConnected()
                if not deviceIsConnected:
                    if not userPrompted:
                        dualOutput("Please connect the key")
                        userPrompted = True
                    else:
                        pass
                    #
                else:
                    dualOutput("Key connected, initializing")
                    firstRunTime = False
                time.sleep(5)
            #
        else:
            deviceIsConnected = CheckKeyConnected()
        #

        if not deviceIsConnected:
            if deviceWasConnected:
                dualOutput("Key is not connected anymore, EXECUTE")
                # print('LockComp')
                # print(ShutdownProcess('calc.exe', True))
                ExecuteCommand("rundll32.exe user32.dll,LockWorkStation", False)
                deviceWasConnected = False
            else:
                dualOutput("Key was already recognized as disconnected, do nothing")
        else:
            if firstRunTime:
                dualOutput("Key is connected, do nothing")
            else:
                dualOutput("Key reconnected, do nothing")
            deviceWasConnected = True
        #

        time.sleep(4)
    #


#


def main():
    global localWMI

    print("\r")
    print("USB Dead Man's Switch (Project 483)")
    print("Copyright (c) Knarkoffer 2016")
    print("\r")

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "-id",
        "--identify-device",
        action="store_true",
        default=False,
        help="Helps you identify the device to be used as a Dead man's switch (DMS)",
    )
    modes.add_argument(
        "-a",
        "--activate",
        action="store_true",
        default=True,
        help="Activate the monitoring, enabled by default",
    )

    modes.add_argument(
        "--baseline",
        nargs="?",
        const="pnp",
        choices=("pnp", "usb"),
        help=(
            "List newly connected devices and exit "
            "(default: pnp; usb uses Win32_USBDevice)"
        ),
    )

    args = parser.parse_args()

    identify_device = args.identify_device

    activateMonitoring = args.activate

    localWMI = wmi.WMI()

    if args.baseline:
        EstablishBaseline(args.baseline)
        sys.exit(0)

    if identify_device:

        CreateKeyfile()

    #

    if activateMonitoring:

        print("Activating monitoring")  # XYZZY

        if len(dMSDevices) < 1:
            print("Need to read keyfile")  # XYZZY
            ReadKeyfile()

            if not len(dMSDevices) < 1:
                StartMonitoring()
            else:
                sys.exit("Keyfile read, but no devices found in it. Problem!")
            #

        else:

            StartMonitoring()

            pass
        #

        pass
    #


if __name__ == "__main__":
    main()
