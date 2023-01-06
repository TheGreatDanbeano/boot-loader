from pathlib import Path
import re
import subprocess as sub
import sys
from time import sleep
from typing import Self

import bootloader.utilities.config as cfg

from .base_flash_command import BaseFlashCommand


# ============================================
#             FlashHabsoluteCommand
# ============================================
class FlashHabsoluteCommand(BaseFlashCommand):
    name = "habs"
    description = "Flashes new firmware onto Habsolute."
    help = """
    Flashes new firmware onto Habsolute.

    Examples
    --------
    > bootload habs --from 7.2.0 --to 9.1.0 -r 4.1B -d actpack
    """
    _target: str = "habs"

    # -----
    # handle
    # -----
    def handle(self: Self) -> int:
        self.prep_device(self._target)
        self._build_flash_command()
        self._set_tunnel_mode(self._target)
        self._flash()

        return 0

    # -----
    # _build_flash_command
    # -----
    def _build_flash_command(self: Self) -> None:
        cmd = Path.joinpath(
            cfg.toolsDir,
            "stm32_flash_loader",
            "stm32_flash_loader",
            "STMFlashLoader.exe",
        )
        portNum = re.search(r"\d+$", self._device.port).group(0)

        self._flashCmd = [
            f"{cmd}",
            "-c",
            "--pn",
            f"{portNum}",
            "--br",
            "115200",
            "--db",
            "8",
            "--pr",
            "NONE",
            "-i",
            "STM32F3_7x_8x_256K",
            "-e",
            "--all",
            "-d",
            "--fn",
            f"{self._fwFile}",
            "-o",
            "--set",
            "--vals",
            "--User",
            "0xF00F",
        ]

    # -----
    # _flash
    # -----
    def _flash(self: Self) -> None:
        self.write(f"Flashing {self._target}...")

        self._device.close()
        del self._device

        sleep(3)

        with sub.Popen(self._flashCmd, stdout=sub.PIPE) as proc:
            try:
                output, err = proc.communicate(timeout=360)
            except sub.TimeoutExpired:
                self.line("\n<error>Error:</error> flash command timed out.")
                proc.kill()
                output, err = proc.communicate()
                self.line(output)
                self.line(err)
                sys.exit(1)

            if proc.returncode == 1:
                msg = "\n<error>Error:</error> flashing failed."
                self.line(msg)
                sys.exit(1)

        sleep(20)

        self.overwrite(f"Flashing {self._target}... <success>✓</success>\n")
