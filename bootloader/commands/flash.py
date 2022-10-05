import os
import sys
from time import sleep
from typing import Dict
from typing import List

from cleo import Command
from flexsea.device import Device
from flexsea.fx_enums import APP_NAMES
from serial.tools.list_ports import comports

from bootloader.io.write import display_logo
from bootloader.utilities.config import cacheDir


# ============================================
#                FlashCommand
# ============================================
class FlashCommand(Command):
    """
    Flashes firmware onto a Dephy device. If no microcontroller is
    specified, flash all of them.

    flash
        {firmwareVersion : Semantic version string of the firmware to
            flash; e.g., 7.2.0}
        {--habs : Flash firmware onto the Habs microcontroller.}
        {--ex : Flash firmware onto the Execute microcontroller.}
        {--re : Flash firmware onto the Regulate microcontroller.}
        {--mn : Flash firmware onto the Manage microcontroller.}
        {--p|ports=* : Name of the port the device is connected to;
            e.g., /dev/ttyACM0. If not given, we try to determine the
            ports automatically.}
    """
    # -----
    # handle
    # -----
    def handle(self) -> None:
        """
        Entry point for the command. Steps:

            * Configures the environment, if needed

            * Attempts to determine the port the device is connected
                to if no port is given

            * Reads info from the device(s) in order to determine the
                appropriate firmware file for each device

            * Downloads the desired firmware if it isn't already
                cached

            * Flashes the firmware onto the device(s)

        Parameters
        ----------
        None

        Raises
        ------
        None

        Returns
        -------
        None
        """
        display_logo(self.line)
        self.call("init")

        microcontrollers = []

        if self.option("ex"):
            microcontrollers.append("ex")

        if self.option("re"):
            microcontrollers.append("re")

        if self.option("mn"):
            microcontrollers.append("mn")

        if not microcontrollers:
            microcontrollers = ["ex", "re", "mn"]

        # If no ports are given by the user, get all connected devices
        if not self.option("ports"):
            for port in comports():
                self.option("ports").append(port.name)

        devices = []

        # Loop over each port and see if it's a valid Dephy device
        for port in self.option("ports"):
            device = Device(port, 230400)

            try:
                device.open()
            except IOError:
                continue

            if 
            device.close()
            devices.append(device)
