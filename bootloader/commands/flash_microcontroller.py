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

from bootloader.utilities.aws import get_s3_object_info
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
    ]

    options = [
        option("from", "-c", "Current firmware version, e.g., `7.2.0`.", flag=False),
        option("to", "-t", "Desired firmware version, e.g., `9.1.0`.", flag=False),
        option("hardware", "-r", "Board hardware version, e.g., `4.1B`.", flag=False),
        option("port", "-p", "Port the device is on, e.g., `COM3`.", flag=False),
        option("file", "-f", "Path to the firmware file.", flag=False),
        option("device", "-d", "Device to flash, e.g., `actpack`.", flag=False),
        option("side", "-s", "Either left or right.", flag=False),
        option("baudRate", "-b", "Device baud rate.", flag=False, default=230400),
    ]

    help = """
    Flashes new firmware onto manage, execute, regulate, or habsolute.

    Examples
    --------
    bootload microcontroller mn --from 7.2.0 --to 9.1.0
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
        self._prep_device()
        self._set_tunnel_mode()
        self._flash()

        return 0

    # -----
    # _prep_device
    # -----
    def _prep_device(self: Self) -> None:
        self._stylize()
        self._setup()

        msg = "<warning>Please make sure the battery is removed "
        msg += "and/or the power supply is disconnected!</warning>"
        if not self.confirm(msg, False):
            sys.exit(1)

        self._target = self.argument("target")
        assert self._target in cfg.microcontrollers

        port = self.option("port")
        br = int(self.option("baudRate"))

        if self.option("from"):
            cv = self.option("from")
        else:
            libs = get_s3_object_info(cfg.libsBucket)
            msg = "Please select the version of the firmware currently on the device:"
            cv = self.choice(msg, libs)

        if not port:
            port = find_port(br, cv)

        self._device = Device(port, br, cv)
        self._device.open()
        # Still need access to the port after the device has been deleted
        self._port = port
        self._fwFile = self._build_firmware_file()

    # -----
    # _build_firmware_file
    # -----
    def _build_firmware_file(self: Self) -> None:
        if self.option("file"):
            try:
                assert Path(self.option("file")).exists()
            except AssertionError:
                get_remote_file(self.option("file"), cfg.firmwareBucket)
            return self.option("file")

        if self.option("device"):
            _name = self.option("device")
        else:
            _name = self._device.deviceName

        if self.option("hardware"):
            hw = self.option("hardware")
        else:
            raise RuntimeError("Must provide hardware.")

        if self.option("to"):
            fw = self.option("to")
        else:
            raise RuntimeError("Must provide to version.")

        ext = cfg.firmwareExtensions[self._target]

        # Legacy devices don't know their side (left or right)
        if self._target == "mn" and _name != "actpack":
            if self.option("side"):
                side = self.option("side")
            else:
                raise RuntimeError("Must provide side information.")
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

        return dest

    # -----
    # _set_tunnel_mode
    # -----
    def _set_tunnel_mode(self: Self) -> None:
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
