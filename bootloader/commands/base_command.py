from pathlib import Path
import sys
from time import sleep
from typing import List
from typing import Self

from cleo.commands.command import Command
from cleo.helpers import option
from flexsea.device import Device
from flexsea.utilities import download
from flexsea.utilities import find_port

import bootloader.utilities.config as cfg


# ============================================
#              BaseFlashCommand
# ============================================
class BaseFlashCommand(Command):
    options = [
        option("from", "-c", "Current firmware version, e.g., `7.2.0`.", flag=False),
        option("to", "-t", "Desired firmware version, e.g., `9.1.0`.", flag=False),
        option("hardware", "-r", "Board hardware version, e.g., `4.1B`.", flag=False),
        option("port", "-p", "Port the device is on, e.g., `COM3`.", flag=False),
        option("file", "-f", "Path to the firmware file.", flag=False),
        option("device", "-d", "Device to flash, e.g., `actpack`.", flag=False),
        option("interactive", "-i", "Guided tour through bootloading.", flag=True),
        option("baudRate", "-b", "Device baud rate.", flag=False, default=230400),
    ]

    _device: None | Device = None
    _fwFile: str = ""
    _flashCmd: List[str] = []

    # -----
    # setup
    # -----
    def setup(self: Self, target: str) -> None:
        self.call(
            [
                "init",
            ]
        )

        port = self.option("port")
        br = int(self.option("baudRate"))
        cv = self.option("from")

        if not port:
            port = find_port(br, cv)

        self._device = Device(port, br, cv)
        self._fwFile = self._build_firmware_file(target)

    # -----
    # _build_firmware_file
    # -----
    def _build_firmware_file(self: Self, target: str) -> None:
        if self.option("file"):
            return self.option("file")

        _name = self._device.deviceName
        hw = self.option("hardware")
        fw = self.option("to")
        ext = cfg.firmwareExtensions[target]

        fwFile = f"{_name}_rigid-{hw}_{target}_firmware-{fw}.{ext}"

        dest = Path(cfg.firmwareDir).joinpath(fwFile)

        if not dest.exists():
            # posix because S3 uses linux separators
            fwObj = Path(fw).joinpath(_name, hw, fwFile).as_posix()
            download(fwObj, cfg.firmwareBucket, str(dest), cfg.dephyProfile)

        return dest

    # -----
    # _set_tunnel_mode
    # -----
    def _set_tunnel_mode(self: Self, target: str) -> None:
        self.write(f"Setting tunnel mode for {target}...")

        if not self._device.set_tunnel_mode(target, 20):
            msg = "\n<error>Error</error>: failed to activate bootloader for: "
            msg += f"<info>`{target}`</info>"
            self.line(msg)
            sys.exit(1)

        self.overwrite(f"Setting tunnel mode for {target}... <success>✓</success>\n")

        sleep(3)

    # -----
    # handle
    # -----
    def handle(self) -> None:
        raise NotImplementedError
