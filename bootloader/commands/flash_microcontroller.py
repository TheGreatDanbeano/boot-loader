from pathlib import Path
import re
import subprocess as sub
import sys
from time import sleep
from typing import List
from typing import Self

from cleo.helpers import argument
from cleo.helpers import option
from flexsea.device import Device
from flexsea.utilities import download
from flexsea.utilities import find_port

from bootloader.utilities.aws import get_remote_file
import bootloader.utilities.config as cfg

from .init import InitCommand

# ============================================
#        FlashMicrocontrollerCommand
# ============================================
class FlashMicrocontrollerCommand(InitCommand):
    name = "microcontroller"

    description = "Flashes new firmware onto manage, execute, regulate, or habsolute."

    arguments = [
        argument("target", "Microcontroller to flash: habs, ex, mn, or re."),
        argument("from", "Current firmware version, e.g., `7.2.0`."),
        argument("to", "Desired firmware version, e.g., `9.1.0`."),
    ]

    options = [
        option("port", "-p", "Port the device is on, e.g., `COM3`.", flag=False),
        option("current-firmware-file", None, "Current firmware file.", flag=False),
        option("new-firmware-file", None, "New firmware file.", flag=False),
        option("hardware", "-r", "Board hardware version, e.g., `4.1B`.", flag=False),
        option("device", "-d", "Device to flash, e.g., `actpack`.", flag=False),
        option("side", "-s", "Either left or right.", flag=False),
        option("baudRate", "-b", "Device baud rate.", flag=False, default=230400),
    ]

    help = """
    Flashes new firmware onto manage, execute, regulate, or habsolute.

    Examples
    --------
    bootload microcontroller mn 7.2.0 9.1.0
    """

    _device: None | Device = None
    _fwFile: str = ""
    _flashCmd: List[str] = []
    _nRetries: int = 5
    _port: str = ""
    _target: str = ""

    # -----
    # handle
    # -----
    def handle(self: Self) -> int:
        self._stylize()
        self._setup_environment()
        self._get_device()
        self._get_new_firmware_file()
        self._set_tunnel_mode()
        self._flash()

        return 0

    # -----
    # _get_device
    # -----
    def _get_device(self: Self) -> None:
        # Only useful if using a file in a non-standard location or
        # with a non-standard name, which applies mainly to internal
        # Dephy use when testing, debugging, and developing
        if self.option("current-firmware-file"):
            libFile = self.option("current-firmware-file")
        else:
            libFile = ""

        self._port = self.option("port")
        br = int(self.option("baudRate"))

        if not self._port:
            self._port = find_port(br, self.argument("from"), libFile)

        self._device = Device(self._port, br, self.argument("from"), libFile=libFile)
        self._device.open()

    # -----
    # _get_new_firmware_file
    # -----
    def _get_new_firmware_file(self: Self) -> None:
        self._target = self.argument("target")
        ext = cfg.firmwareExtensions[self._target]
        fw = self.argument("to")

        if self.option("new-firmware-file"):
            if not Path(self.option("new-firmware-file")).exists():
                get_remote_file(self.option("new-firmware-file"), cfg.firmwareBucket)
            self._fwFile = self.option("new-firmware-file")
            return

        if self.option("device"):
            _name = self.option("device")
        else:
            _name = self._device.deviceName

        if self.option("hardware"):
            hw = self.option("hardware")
        else:
            hw = self._device.rigidVersion

        if self._target == "mn" and self._device.isChiral:
            if self.option("side"):
                side = self.option("side")
            else:
                side = self._device.deviceSide
            fwFile = (
                f"{_name}_rigid-{hw}_{self._target}_firmware-{fw}_side-{side}.{ext}"
            )

        else:
            fwFile = f"{_name}_rigid-{hw}_{self._target}_firmware-{fw}.{ext}"

        dest = Path(cfg.firmwareDir).joinpath(fwFile)

        if not dest.exists():
            # posix because S3 uses linux separators
            fwObj = Path(fw).joinpath(_name, hw, fwFile).as_posix()
            download(fwObj, cfg.firmwareBucket, str(dest), cfg.dephyProfile)

        self._fwFile = dest

    # -----
    # _set_tunnel_mode
    # -----
    def _set_tunnel_mode(self: Self) -> None:
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
    def _call_flash_tool(self: Self) -> None:
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
    # _flash
    # -----
    def _flash(self: Self) -> None:
        self.write(f"Flashing {self._target}...")

        if self._target == "mn":
            self._device.close()
            del self._device
            sleep(3)
            sleep(10)
            self._call_flash_tool()

        elif self._target == "ex":
            sleep(2)
            self._device.close()
            sleep(2)
            self._call_flash_tool()
            sleep(20)

        elif self._target == "re":
            sleep(3)
            self._device.close()
            self._call_flash_tool()

        elif self._target == "habs":
            self._device.close()
            sleep(6)
            self._call_flash_tool()
            sleep(20)

        if not self.confirm("Please power cycle device.", False):
            sys.exit(1)
        self.overwrite(f"Flashing {self._target}... <success>✓</success>\n")

    # -----
    # _flashCmd
    # -----
    @property
    def _flashCmd(self: Self) -> List[str]:
        if self._target == "mn":
            flashCmd = [
                f"{Path(cfg.toolsDir).joinpath('DfuSeCommand.exe')}",
                "-c",
                "-d",
                "--fn",
                f"{self._fwFile}",
            ]

        elif self._target in ("ex", "re"):
            flashCmd = [
                f"{Path.joinpath(cfg.toolsDir, 'psocbootloaderhost.exe')}",
                f"{self._port}",
                f"{self._fwFile}",
            ]

        elif self._target == "habs":
            cmd = Path.joinpath(
                cfg.toolsDir,
                "stm32_flash_loader",
                "stm32_flash_loader",
                "STMFlashLoader.exe",
            )
            portNum = re.search(r"\d+$", self._port).group(0)

            flashCmd = [
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

        else:
            raise ValueError("Unknown target.")

        return flashCmd
