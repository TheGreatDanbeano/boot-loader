import glob
import os
import shutil
import subprocess as sub
import sys
from time import sleep
from typing import List
from typing import Self

from cleo.helpers import option

import bootloader.utilities.config as cfg

from .base_flash_command import BaseFlashCommand


# ============================================
#             FlashBT121Command
# ============================================
class FlashBT121Command(BaseFlashCommand):
    name = "bt121"

    description = "Flashes the bluetooth radio."

    help = """
    Creates a new bluetooth file with the desired GATT level and flashes it
    onto the device's bt121 radio.

    `--level` is the level of the gatt file to use. Default is 2.

    `--address` is the desired bluetooth address. If not specificed, the device ID
    is used.

    Examples
    --------
    bootload bt121 7.2.0
    bootload bt121 9.1.0 --level 2 --address 0001
    """

    _level: int | None = None
    _address: str = ""

    # -----
    # __new__
    # -----
    def __new__(cls):
        obj = super().__new__(cls)
        opts = [
            option("level", "-l", "Desired level, e.g., 2.", flag=False, default=2),
            option("address", "-a", "Bluetooth address.", flag=False),
        ]
        obj.options += opts

        return obj

    # -----
    # handle
    # -----
    def handle(self: Self) -> int:
        self.call("init")

        self._level = self.option("level")
        self._address = self.option("address")
        self._target = "bt121"

        self._get_device()
        self._build_bt_image()
        self._set_tunnel_mode()
        self._flash()

        return 0

    # -----
    # _build_bt_image
    # -----
    def _build_bt_image(self) -> None:
        """
        Uses the bluetooth tools repo (downloaded as a part of `init`)
        to create a bluetooth image file with the correct address.
        """
        self.write("Building bluetooth image...")
        # Everything within the bt121 directory is self-contained and
        # self-referencing, so it's easiest to switch to that directory
        # first
        cwd = os.getcwd()
        os.chdir(os.path.join(cfg.toolsDir, "bt121_image_tools"))

        gattTemplate = os.path.join("gatt_files", f"{self._level}.xml")
        gattFile = os.path.join("dephy_gatt_broadcast_bt121", "gatt.xml")

        if not os.path.exists(gattTemplate):
            raise FileNotFoundError(f"Could not find: `{gattTemplate}`.")

        shutil.copyfile(gattTemplate, gattFile)

        cmd = ["python3", "bt121_gatt_broadcast_img.py", f"{self._address}"]
        proc = sub.run(cmd, capture_output=False, check=True, timeout=360)

        if proc.returncode != 0:
            raise RuntimeError("bt121_gatt_broadcast_img.py failed.")

        bgExe = os.path.join("smart-ready-1.7.0-217", "bin", "bgbuild.exe")
        xmlFile = os.path.join("dephy_gatt_broadcast_bt121", "project.xml")
        proc = sub.run([bgExe, xmlFile], capture_output=False, check=True, timeout=360)

        if proc.returncode != 0:
            raise RuntimeError("bgbuild.exe failed.")

        if os.path.exists("output"):
            files = glob.glob(os.path.join("output", "*.bin"))
            for file in files:
                os.remove(file)
        else:
            os.mkdir("output")

        btImageFile = f"dephy_gatt_broadcast_bt121_Exo-{self._address}.bin"
        shutil.move(os.path.join("dephy_gatt_broadcast_bt121", btImageFile), "output")
        btImageFile = os.path.join(
            os.getcwd(), "bt121_image_tools", "output", btImageFile
        )

        os.chdir(cwd)

        self._fwFile = btImageFile
        self.overwrite("Building bluetooth image... <success>✓</success>\n")

    # -----
    # _flash
    # -----
    def _flash(self) -> None:
        self.write(f"Flashing {self._target}...")

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
            os.path.join(cfg.toolsDir, "stm32flash"),
            "-w",
            f"{self._fwFile}",
            "-b",
            "115200",
            self._device.port,
        ]

        return cmd
