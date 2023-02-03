import os
import sys
from time import sleep
from typing import List

from cleo.helpers import argument

from bootloader.utilities import config as cfg

from .base_flash_command import BaseFlashCommand


# ============================================
#              FlashXBeeCommand
# ============================================
class FlashXbeeCommand(BaseFlashCommand):
    name = "xbee"
    description = "Sets up inter-device communication via xbee radio."
    help = """
    Sets up inter-device communication via xbee radio.

    `address` is the the bluetooth address of the device being flashed.
    `buddyAddress` is the bluetooth address of the current device's companion.

    Examples
    --------
    bootload xbee 1234 5678 7.2.0
    """

    _address = None
    _buddyAddress = None

    # -----
    # __new__
    # -----
    def __new__(cls):
        obj = super().__new__(cls)

        args = [
            argument("address", "The bluetooth address of the current device."),
            argument("buddyAddress", "Bluetooth address of device's companion."),
        ]

        obj.arguments = args + obj.arguments

        return obj

    # -----
    # handle
    # -----
    def handle(self) -> None:
        """
        Entry point for the command.
        """
        self._address = self.argument("address")
        self._buddyAddress = self.argument("buddyAddress")
        self._target = "xbee"

        self.call("init")
        self._get_device()
        self._set_tunnel_mode()

        self.write("Flashing xbee...")
        self._device.close()
        sleep(3)
        self._call_flash_tool()
        sleep(20)

        if not self.confirm("Please power cycle device.", False):
            sys.exit(1)
        self.overwrite(f"Flashing {self._target}... <success>✓</success>\n")

    # -----
    # _flashCmd
    # -----
    @property
    def _flashCmd(self) -> List[str]:
        cmd = [
            "python3",
            os.path.join(cfg.toolsDir, "xb24c.py"),
            self._device.port,
            self._address,
            self._buddyAddress,
            "upgrade",
        ]

        return cmd
