from pathlib import Path
import subprocess as sub
import sys
from time import sleep
from typing import List

from cleo.helpers import argument
from cleo.helpers import option

from bootloader.commands.init import InitCommand
import bootloader.utilities.config as cfg


# ============================================
#             ConfigureXbeeCommand
# ============================================
class ConfigureXbeeCommand(InitCommand):
    name = "configure-xbee"
    description = "Configures the xbee radio on a Dephy device."
    arguments = [
        argument("address", "The address of the device to be flashed."),
        argument(
            "buddyAddress",
            "Bluetooth address of the device's buddy.",
        ),
        argument(
            "from",
            "Semantic version string of the firmware currently on the device.",
        ),
    ]
    options = [
        option(
            "port", "-p", "Name of the device's port, e.g., '/dev/ttyACM0'", flag=False
        ),
    ]
    help = """Command for configuring the xbee radio.

    The <info>address</info> argument is the bluetooth address of the current
    device and the <info>buddyAddress</info> argument is the bluetooth address
    of the device's companion.

    If <info>--port</info> is given then only that port is used. If it is
    not given, then we search through all available COM ports until we
    find a valid Dephy device. For this reason, it is recommended that
    <info>only one</info> device be connected when flashing without
    setting this option.

    Examples
    --------
    bootloader configure-xbee 1234 5678 7.2.0
    """

    _targets: List[str] = []

    # -----
    # handle
    # -----
    def handle(self) -> int:
        """
        Entry point for the command.
        """
        try:
            self._setup(self.option("port"), self.argument("from"))
        except ValueError:
            sys.exit(1)

        self.write("Setting tunnel mode for xbee...")
        if not self._device.set_tunnel_mode("xbee", 20):
            msg = "\n<error>Error</error>: failed to activate bootloader for: "
            msg += "<info>`xbee`</info>"
            self.line(msg)
            sys.exit(1)
        self.overwrite("Setting tunnel mode for xbee... <success>✓</success>\n")

        cmd = self._get_flash_cmd()

        with sub.Popen(cmd) as proc:
            self.write("Configuring xbee...")

        if proc.returncode == 1:
            msg = "<error>Error: configuring failed.</error>"
            self.line(msg)
            sys.exit(1)

        _ = self.ask(
            "<warning>Please power cycle the device, then press `ENTER`</warning>"
        )
        sleep(3)
        self.overwrite("Configuring xbee... <success>✓</success>\n")

        return 0

    # -----
    # _get_flash_cmd
    # -----
    def _get_flash_cmd(self) -> List[str]:
        cmd = [
            "python3",
            Path.joinpath(cfg.toolsDir, "xb24c.py"),
            self._device.port,
            self.option("address"),
            self.option("buddyAddress"),
            "upgrade",
        ]

        return cmd
