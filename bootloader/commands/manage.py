from pathlib import Path
import subprocess as sub
import sys
from time import sleep
from typing import Self

import bootloader.utilities.config as cfg

from .base_flash_command import BaseFlashCommand


# ============================================
#             FlashManageCommand
# ============================================
class FlashManageCommand(BaseFlashCommand):
    name = "mn"
    description = "Flashes new firmware onto Manage."
    help = """
    Flashes new firmware onto Manage.

    Examples
    --------
    > bootload mn --from 7.2.0 --to 9.1.0 -r 4.1B -d actpack
    """
    _target: str = "mn"

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
        self._flashCmd = [
            f"{Path(cfg.toolsDir).joinpath('DfuSeCommand.exe')}",
            "-c",
            "-d",
            "--fn",
            f"{self._fwFile}",
        ]

    # -----
    # _flash
    # -----
    def _flash(self: Self) -> None:
        self.write(f"Flashing {self._target}...")

        # Before calling the flash command, we have to close our connection
        # to the serial port so the flash command can use it
        self._device.close()
        del self._device
        sleep(10)

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

        self.overwrite(f"Flashing {self._target}... <success>✓</success>\n")
