from pathlib import Path
from typing import Self

from .base_command import BaseFlashCommand


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
    _target = "mn"

    # -----
    # handle
    # -----
    def handle(self: Self) -> int:
        self.setup(self._target)
        self._build_flash_command()
        self._set_tunnel_mode(self._target)


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
