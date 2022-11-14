from pathlib import Path
import subprocess as sub
import sys
from time import sleep
from typing import List

from cleo.helpers import argument
from cleo.helpers import option

from bootloader.commands.init import InitCommand
import bootloader.utilities.config as cfg
from bootloader.utilities import system_utils as su


# ============================================
#            ConfigureBT121Command
# ============================================
class ConfigureBT121Command(InitCommand):
    name = "configure-bt"
    description = "Configures bluetooth for a Dephy device."
    arguments = [
        argument("level", "The bluetooth gatt file level to use."),
        argument("address", "Bluetooth address of the device."),
        argument(
            "from", "Semantic version string of the firmware currently on the device."
        ),
    ]
    options = [
        option(
            "port", "-p", "Name of the device's port, e.g., '/dev/ttyACM0'", flag=False
        ),
    ]
    help = """Command for configuring bluetooth.

    The `level` argument refers to the gatt file level. `from` is the version
    of the firmware currently flashed on the device.

    If <info>--port</info> is given then only that port is used. If it is
    not given, then we search through all available COM ports until we
    find a valid Dephy device. For this reason, it is recommended that
    <info>only one</info> device be connected when flashing without
    setting this option.

    Examples
    --------
    bootloader configure-bt 2 1234 7.2.0
    """

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

        self.write("Setting tunnel mode for bt121...")
        if not self._device.set_tunnel_mode("bt", 20):
            msg = "\n<error>Error</error>: failed to activate bootloader for: "
            msg += "<info>`bt`</info>"
            self.line(msg)
            sys.exit(1)
        self.overwrite("Setting tunnel mode for bt121... <success>✓</success>\n")

        cmd = self._get_flash_cmd()

        with sub.Popen(cmd) as proc:
            self.write("Configuring bluetooth...")

        if proc.returncode == 1:
            msg = "<error>Error: configuring failed.</error>"
            self.line(msg)
            sys.exit(1)

        _ = self.ask(
            "<warning>Please power cycle the device, then press `ENTER`</warning>"
        )
        sleep(3)
        self.overwrite("Configuring bluetooth... <success>✓</success>\n")

        return 0

    # -----
    # _get_flash_cmd
    # -----
    def _get_flash_cmd(self) -> List[str]:
        btImageFile = su.build_bt_image_file(
            self.argument("level"), self.argument("address")
        )
        cmd = [
            Path.joinpath(cfg.toolsDir, "stm32flash"),
            "-w",
            btImageFile,
            "-b",
            "115200",
            self._device.port,
        ]

        return cmd
