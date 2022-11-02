from pathlib import Path
import subprocess as sub
import sys
from time import sleep
from typing import List

from cleo.helpers import argument
from cleo.helpers import option

from bootloader.commands.init import InitCommand
from bootloader.exceptions import exceptions
import bootloader.utilities.config as cfg
from bootloader.utilities import system_utils as su


# ============================================
#               FlashCommand
# ============================================
class FlashCommand(InitCommand):
    name = "flash"
    description = "Flashes firmware onto a Dephy device."
    arguments = [argument("target", "The target to be flashed.")]
    options = [
        option(
            "firmware",
            "-f",
            "Semantic version string of the firmware to flash.",
            flag=False,
        ),
        option(
            "level",
            "-l",
            "The bluetooth level to flash, e.g., `2`.",
            flag=False,
            default=2,
        ),
        option(
            "address",
            "-a",
            "Bluetooth address of the device.",
            flag=False,
        ),
        option(
            "buddyAddress",
            "-b",
            "Bluetooth address of the device's buddy.",
            flag=False,
        ),
        option(
            "port", "-p", "Name of the device's port, e.g., '/dev/ttyACM0'", flag=False
        ),
    ]
    help = """Meta command for flashing. <info>target</info> can be:
        * mn
        * ex
        * re
        * habs
        * mcu (Aggregate option; flashes mn, ex, re, and habs, if applicable)
        * bt (bluetooth)
        * xbee

    If flashing mn, ex, re, or habs, <info>--firmware</info> refers to the
    semantic version string of the firmware you'd like to flash, e.g., 7.2.0.
    If flashing bluetooth, it refers to the level, e.g., 2.

    If <info>--port</info> is given then only that port is used. If it is
    not given, then we search through all available COM ports until we
    find a valid Dephy device. For this reason, it is recommended that
    <info>only one</info> device be connected when flashing without
    setting this option.

    Examples
    --------
    bootloader flash mn -f=7.2.0
    bootloader flash mcu --firmware=8.0.0 -p=/dev/ttyACM0
    bootloader flash bt -f=2 -a=1234
    bootloader flash xbee -a=1234 -b=5678
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
            self._setup(self.option("port"))
        except ValueError:
            sys.exit(1)

        try:
            self._get_targets()
        except exceptions.UnknownMCUError as err:
            self.line(err)
            sys.exit(1)

        for target in self._targets:
            try:
                self._set_tunnel_mode(target)
            except (IOError, OSError, RuntimeError) as err:
                self.line(err)
                sys.exit(1)

            try:
                cmd = self._get_flash_cmd(target)
            except exceptions.FirmwareNotFoundError as err:
                self.line(err)
                sys.exit(1)

            with sub.Popen(cmd) as proc:
                self.write(f"Flashing {target}...")

            if proc.returncode == 1:
                msg = "<error>Error: flashing failed.</error>"
                self.line(msg)
                sys.exit(1)

            self.overwrite(f"Flashing {target}... <success>✓</success>\n")
            _ = self.ask("Please power cycle the device, then press `ENTER`")
            sleep(3)
            self.line("\n\n")

        return 0

    # -----
    # _get_targets
    # -----
    def _get_targets(self) -> None:
        """
        Converts the given target into a list so as to be able to handle
        the `all` case more easily.
        """
        try:
            assert self.argument("target") in cfg.availableTargets
        except AssertionError as err:
            raise exceptions.UnknownMCUError(
                self.argument("target"), cfg.mcuTargets
            ) from err

        if self.argument("target") == "mcu":
            self._targets = cfg.mcuTargets
        else:
            self._targets = [
                self.argument("target"),
            ]

        if not self._device.hasHabs and "habs" in self._targets:
            self._targets.remove("habs")

    # -----
    # _set_tunnel_mode
    # -----
    def _set_tunnel_mode(self, target: str) -> None:
        self.write(f"Setting tunnel mode for {target}...")
        su.set_tunnel_mode(self._device, target, 20)
        self.overwrite(f"Setting tunnel mode for {target}... <success>✓</success>\n")

    # -----
    # _get_flash_cmd
    # -----
    def _get_flash_cmd(self, target: str) -> List[str]:
        if target in cfg.mcuTargets:
            fwFile = self._get_firmware(target)

        if target == "habs":
            cmd = self._flash_habs(fwFile)
        elif target == "ex":
            cmd = self._flash_ex(fwFile)
        elif target == "re":
            cmd = self._flash_re(fwFile)
        elif target == "mn":
            cmd = self._flash_mn(fwFile)
        elif target == "bt":
            cmd = self._flash_bt()
        elif target == "xbee":
            cmd = self._flash_xbee()

        return cmd

    # -----
    # _get_firmware
    # -----
    def _get_firmware(self, target: str) -> Path:
        fwFile = f"{self._device.deviceType}_rigid-{self._device.rigidVersion}_"
        fwFile += f"{target}_{self.option('firmware')}."
        fwFile += f"{cfg.fwExtensions[target]}"

        dest = Path(cfg.firmwareDir).joinpath(fwFile)

        if not dest.exists():
            # posix is because I believe S3 doesn't support windows
            # separators
            fwObj = Path.joinpath(
                self.option("firmware"), self._device.deviceType, fwFile
            ).as_posix()

            try:
                self._download(fwObj, cfg.firmwareBucket, dest, cfg.dephyProfile)
            except (
                exceptions.NoCredentialsError,
                exceptions.NoProfileError,
                exceptions.MissingKeyError,
                TypeError,
            ) as err:
                self.line(err)
                sys.exit(1)

            if not dest.exists():
                raise exceptions.FirmwareNotFoundError(
                    fwObj,
                    self.option("firmware"),
                    self._device.deviceType,
                    target,
                )

        return dest

    # -----
    # _flash_habs
    # -----
    def _flash_habs(self, fwFile: str | Path) -> List[str]:

        cmd = [
            f"{Path.joinpath(cfg.toolsDir, 'STMFlashLoader.exe')}",
            "-c",
            "--pn",
            f"{self._device.port}",
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
            f"{fwFile}",
            "-o",
            "--set",
            "--vals",
            "--User",
            "0xF00F",
        ]

        return cmd

    # -----
    # _flash_ex
    # -----
    def _flash_ex(self, fwFile: str | Path) -> List[str]:
        cmd = [
            f"{Path.joinpath(cfg.toolsDir, 'psocbootloaderhost.exe')}",
            f"{self._device.port}",
            f"{fwFile}",
        ]

        return cmd

    # -----
    # _flash_re
    # -----
    def _flash_re(self, fwFile: str | Path) -> List[str]:
        cmd = [
            f"{Path.joinpath(cfg.toolsDir, 'psocbootloaderhost.exe')}",
            f"{self._device.port}",
            f"{fwFile}",
        ]

        return cmd

    # -----
    # _flash_mn
    # -----
    def _flash_mn(self, fwFile: str | Path) -> List[str]:
        cmd = [
            f"{Path.joinpath(cfg.toolsDir, 'DfuSeCommand.exe')}",
            "-c",
            "-d",
            "--fn",
            f"{fwFile}",
        ]

        return cmd

    # -----
    # _flash_bt
    # -----
    def _flash_bt(self) -> List[str]:
        btImageFile = su.build_bt_image_file(
            self.option("level"), self.option("address")
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

    # -----
    # _flash_xbee
    # -----
    def _flash_xbee(self) -> List[str]:
        cmd = [
            "python3",
            Path.joinpath(cfg.toolsDir, "xb24c.py"),
            self._device.port,
            self.option("address"),
            self.option("buddyAddress"),
            "upgrade",
        ]

        return cmd
