import subprocess as sub
import sys
from typing import List

from cleo.helpers import argument
from cleo.helpers import option
from flexsea.device import Device

from .base_command import BaseCommand


# ============================================
#              BaseFlashCommand
# ============================================
class BaseFlashCommand(BaseCommand):
    arguments = [
        argument("currentFirmware", "Current firmware version, e.g., `7.2.0`."),
    ]

    options = [
        option("baudRate", "-b", "Device baud rate.", flag=False, default=230400),
        option("lib", "-l", "C lib for interacting with current firmware.", flag=False),
        option("port", "-p", "Port the device is on, e.g., `COM3`.", flag=False),
    ]

    _device: None | Device = None
    _nRetries: int = 5
    _port: str = ""
    _flashCmd: List[str] = []
    _fwFile: str = ""
    _target: str = ""

    # -----
    # _get_device
    # -----
    def _get_device(self) -> None:
        self._device = Device(
            self.option("port"),
            int(self.option("baudRate")),
            self.argument("currentFirmware"),
            libFile=self.option("lib"),
        )
        self._port = self._device.port
        self._device.open()

    # -----
    # _set_tunnel_mode
    # -----
    def _set_tunnel_mode(self) -> None:
        msg = "<warning>Please make sure the battery is removed "
        msg += "and/or the power supply is disconnected!</warning>"
        if not self.confirm(msg, False):
            sys.exit(1)
        self.write(f"Setting tunnel mode for {self._target}...")

        if not self._device.set_tunnel_mode(self._target, 20):
            msg = "\n<error>Error</error>: failed to activate bootloader for: "
            msg += f"<info>`{self._target}`</info>"
            self.line(msg)
            sys.exit(1)

        self.overwrite(
            f"Setting tunnel mode for {self._target}... <success>✓</success>\n"
        )

    # -----
    # _call_flash_tool
    # -----
    def _call_flash_tool(self) -> None:
        for _ in range(self._nRetries):
            try:
                proc = sub.run(
                    self._flashCmd, capture_output=False, check=True, timeout=360
                )
            except sub.CalledProcessError:
                continue
            except sub.TimeoutExpired:
                self.line("Timeout.")
                sys.exit(1)
            if proc.returncode == 0:
                break
        if proc.returncode != 0:
            self.line("Error.")
            sys.exit(1)

    # -----
    # _flashCmd
    # -----
    @property
    def _flashCmd(self) -> None:
        pass

    # -----
    # handle
    # -----
    def handle(self) -> None:
        pass
