import os
import subprocess as sub
import sys

from cleo import Command

from bootloader.exceptions.exceptions import DeviceNotFoundError
from bootloader.utilities.config import baudRate
from bootloader.utilities.config import toolsDir
from bootloader.utilities.system import find_device
from bootloader.utilities.system import set_tunnel_mode


# ============================================
#              FlashXBeeCommand
# ============================================
class FlashXBeeCommand(Command):
    """
    Flashes the xbee radio on a Dephy device.

    flash-xbee
        {address : The address of the current device.}
        {buddyAddress : The address of the device's partner.}
        {--p|port= : Name of the serial port to connect to, e.g., `/dev/ttyACM0`}
    """

    _device = None
    _port = ""
    _address = None
    _buddyAddress = None

    # -----
    # handle
    # -----
    def handle(self) -> None:
        """
        Entry point for the command.
        """
        self._address = self.argument("address")
        self._buddyAddress = self.argument("buddyAddress")
        self._port = self.option("port") if self.option("port") else ""

        try:
            self._device = find_device(self._port)
        except DeviceNotFoundError as err:
            self.line(err)
            sys.exit(1)

        set_tunnel_mode(self._port, baudRate, "XBee", 20)

        cmd = [
            "python3",
            os.path.join(toolsDir, "xb24c.py"),
            self._device.port,
            self._address,
            self._buddyAddress,
            "upgrade",
        ]

        with sub.Popen(cmd) as proc:
            self.line("Flashing...")

        if proc.returncode == 1:
            msg = "<error>Error: flashing xbee failed.</error>"
            self.line(msg)
            sys.exit(1)
