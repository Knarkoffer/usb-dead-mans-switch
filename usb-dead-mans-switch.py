#!python3
# coding: utf-8

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


print("\r")
print("USB Dead Man's Switch (Project 483)")
print("Copyright (c) Knarkoffer 2016")
print("\r")

import argparse

# import lxml.etree
# import lxml.builder
import subprocess
import sys
import time
import wmi  # "pip install wmi", requires pywin32, get @ https://sourceforge.net/projects/pywin32/
import xmltodict
from yattag import Doc, indent

parser = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
)

modes = parser.add_mutually_exclusive_group()
modes.add_argument(
    "-id",
    "--idententifyDevice",
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
    help="List newly connected devices and exit (default: pnp; usb uses Win32_USBDevice)",
)

# -- Convert input arguments to variables
args = parser.parse_args()

# --idententifyDevice :
idententifyDevice = args.idententifyDevice

# --idententifyDevice :
activateMonitoring = args.activate

dMSDevices = []

localWMI = wmi.WMI()

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

    input("Make sure the device is NOT plugged in, then press Enter")

    defaultDevices = []

    for item in localWMI.query("select * from Win32_PnPEntity"):

        deviceName = item.Caption
        deviceID = item.DeviceID

        defaultDevices.append(deviceName + "|" + deviceID)
    #

    input("USB baseline established, please insert device, then press Enter")

    global dMSDevices
    dMSDevices = []

    for item in localWMI.query("select * from Win32_PnPEntity"):

        deviceName = item.Caption
        deviceID = item.DeviceID

        if not str(deviceName + "|" + deviceID) in defaultDevices:

            if not "STORAGE#VOLUME#" in deviceID:

                if not "USBSTOR#DISK" in deviceID:

                    dMSDevices.append(deviceName + "|" + deviceID)
                #
            #
        #

    #

    if not len(dMSDevices) == 0:

        doc, tag, text = Doc().tagtext()

        with tag("config"):
            for dMSDeviceInfo in dMSDevices:

                dMSDeviceInfo = dMSDeviceInfo.split("|")
                dMSDeviceName = dMSDeviceInfo[0]
                dMSDeviceID = dMSDeviceInfo[1]

                # print('Name: ' + str(dMSDeviceName))
                # print('ID: ' + str(dMSDeviceID))

                with tag("key"):
                    with tag("Name"):
                        text(str(dMSDeviceName))
                    #
                    with tag("DeviceID"):
                        text(str(dMSDeviceID))
                    #
                #
                #
            #
            # DOn't forget to replace '&amp;' with '&' when reading file
        #
        result = indent(
            doc.getvalue(),
            indentation="\t",
            # newline = '\r\n'
            newline="\n",
        )

        configFile = open("config.xml", "w")
        configFile.write(result)
        configFile.close()

        activateMonitoring = query_yes_no(
            "Key detection rules created successfully, start monitoring?"
        )

        if not activateMonitoring:
            sys.exit("Exiting script")
        #

    else:

        sys.exit("Problems detecting your key, exiting script")

    #


#


def ReadKeyfile():

    print("Reading keyfile")  # XYZZY

    with open("config.xml") as fd:

        doc = xmltodict.parse(fd.read())
        #

        keyItems = doc["config"]["key"]

        for key in keyItems:

            deviceName = key["Name"]
            deviceID = key["DeviceID"]
            deviceID.replace("&amp;", "&")

            dMSDevices.append(deviceName + "|" + deviceID)

        #
    #


#


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
        raise ValueError("invalid default answer: '%s'" % default)
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

        deviceName = item.Caption
        deviceID = item.DeviceID

        # print('deviceName: ' + str(deviceName))
        # print('deviceID: ' + str(deviceID))

        connectedDevices.append(deviceName + "|" + deviceID)
        pass
    #

    foundDevices = set(expectedDevices).intersection(connectedDevices)

    for expectedDevice in expectedDevices:
        # print(expectedDevice)
        pass

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
                results = ExecuteCommand(
                    "rundll32.exe user32.dll,LockWorkStation", False
                )
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


if args.baseline:
    EstablishBaseline(args.baseline)
    sys.exit(0)


if idententifyDevice:

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
