from pathlib import Path
import subprocess as sub
import sys
from time import sleep
from typing import List

import botocore.exceptions as bce
from cleo.helpers import argument
from cleo.helpers import option
from flexsea.device import Device
import flexsea.utilities as fxu

from bootloader.commands.init import InitCommand
from bootloader.exceptions import exceptions
import bootloader.utilities.config as cfg


# ============================================
#               FlashCommand
# ============================================
class FlashCommand(InitCommand):
    name = "flash"
    description = "Flashes firmware onto the microcontrollers of a Dephy device."
    arguments = [
        argument("target", "The target to be flashed."),
        argument("from", "Current firmware's semantic version string, e.g., 7.2.0"),
        argument("to", "Desired firmware's semantic version string, e.g., 9.1.0"),
    ]
    options = [
        option(
            "port", "-p", "Name of the device's port, e.g., '/dev/ttyACM0'", flag=False
        ),
        option("hardware", "-r", "Semantic version string of the board version, e.g., `4.1`.", flag=False),
        option("firmware", "-f", "Manually specify firmware file location.", flag=False),
        option("force-habs", short_name=None, description="Used for when actpack firmware is on an exo.", flag=True),
    ]
    help = """Flashes new firmware onto the microcontrollers of a Dephy device.

    <info>target</info> can be:
        * mn
        * ex
        * re
        * habs
        * all (Aggregate option; flashes mn, ex, re, and habs, if applicable)

    <info>from</info> refers to the current firmware version on the microcontroller.
    This is necessary so we know which pre-compiled C libraries to use, since the
    communication protocol can change between major versions. This should be a
    semantic version string, e.g., `7.2.0`.

    <info>to</info> refers to the version of the firmware that you would like to
    flash onto the microcontroller. This should be a semantic version string, e.g.,
    `9.1.0`.

    <warning>NOTE</warning>: if `target` is `all`, then the current firmware version
    on each microcontroller is assumed to be the same.

    If <info>--port</info> is given then only that port is used. If it is
    not given, then we search through all available COM ports until we
    find a valid Dephy device. For this reason, it is recommended that
    <warning>only one</warning> device be connected when flashing without
    setting this option.

    Currently, the devices do not know their own hardware version, so the `--hardware`
    option has been introduced as a stop-gap until they do.

    The <info>--firmware</info> option allows you to manually specify a firmware file
    to use.

    Examples
    --------
    bootloader flash mn 7.2.0 9.1.0 -r 4.1
    bootloader flash all 8.0.0 7.2.0 -p /dev/ttyACM0 --hardware 4.1B
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

        for target in self._targets:
            if self.option("firmware"):
                fwFile = self.option("firmware")
            else:
                try:
                    fwFile = self._get_firmware(target)
                except exceptions.FirmwareNotFoundError as err:
                    self.line(err)
                    sys.exit(1)

            cmd = self._get_flash_cmd(target, fwFile)

            # The current communication has lots of finnicky timing issues, which
            # is why there are a bunch of seemingly random sleeps here
            # Further, when flashing manage, even if the device is closed,
            # the serial library still throws an exception for some reason
            # unless we delete the device object. This deletion happens implicitly
            # in the old bootloader since the device object was created in
            # the bootloader function and then garbage collected when that script
            # ended. It can't be deleted for ex and re, though, since those
            # flash commands need the serial port
            if target == "mn":
                _port = self._device.port
                _baudRate = self._device.baudRate
                _cLibVersion = self._device.cLibVersion
                _logLevel = self._device.logLevel
                _loggingEnabled = self._device.loggingEnabled

            self.write(f"Setting tunnel mode for {target}...")
            if not self._device.set_tunnel_mode(target, 20):
                msg = "\n<error>Error</error>: failed to activate bootloader for: "
                msg += f"<info>`{target}`</info>"
                self.line(msg)
                sys.exit(1)
            self.overwrite(
                f"Setting tunnel mode for {target}... <success>✓</success>\n"
            )

            if target != "mn":
                sleep(2)

            # Before calling the flash command, we have to close our connection
            # to the serial port so the flash command can use it
            self._device.close()
            if target == "mn":
                del self._device
                sleep(8)
            if target != "habs":
                sleep(2)

            self.write(f"Flashing {target}...")
            import pdb; pdb.set_trace()
            proc = sub.Popen(cmd, stdout=sub.PIPE)
            try:
                output, err = proc.communicate(timeout=360)
            except sub.TimeoutExpired:
                self.line("\n<error>Error:</error> flash command timed out.")
                proc.kill()
                output, err = proc.communicate()
                sys.exit(1)

            if proc.returncode == 1:
                msg = "\n<error>Error:</error> flashing failed."
                self.line(msg)
                sys.exit(1)

            self.overwrite(f"Flashing {target}... <success>✓</success>\n")

            _ = self.ask(
                "<warning>Please power cycle the device, then press `ENTER`</warning>"
            )
            if target == "mn":
                self._device = Device(_port, _baudRate, _cLibVersion, _logLevel, _loggingEnabled)

            sleep(3)
            self.line("\n\n")
            # Reopen our connection to the device so we can set tunnel mode
            # for the next target
            self._device.open()

        self.line("<success>Done!</success>")
        return 0

    # -----
    # _targets
    # -----
    @property
    def _targets(self) -> List[str]:
        """
        Converts the given target into a list so as to be able to handle
        the `all` case more easily.
        """
        targets = [
            self.argument("target"),
        ]

        if self.argument("target") == "all":
            targets = cfg.mcuTargets

        if not self.option("force-habs"):
            if not self._device.hasHabs and "habs" in targets:
                targets.remove("habs")

        return targets

    # -----
    # _get_flash_cmd
    # -----
    def _get_flash_cmd(self, target: str, fwFile: str) -> List[str]:
        if target == "habs":
            cmd = self._flash_habs(fwFile)
        elif target == "ex":
            cmd = self._flash_ex(fwFile)
        elif target == "re":
            cmd = self._flash_re(fwFile)
        elif target == "mn":
            cmd = self._flash_mn(fwFile)

        return cmd

    # -----
    # _get_firmware
    # -----
    def _get_firmware(self, target: str) -> Path:
        if self.option("hardware"):
            rigid = self.option("hardware")
        else:
            rigid = self._device.rigidVersion

        fwFile = f"{self._device.deviceName}_rigid-{rigid}_"
        fwFile += f"{target}_firmware-{self.argument('to')}."
        fwFile += f"{cfg.fwExtensions[target]}"

        dest = Path(cfg.firmwareDir).joinpath(fwFile)

        if not dest.exists():
            # posix is because I believe S3 doesn't support windows
            # separators
            fwObj = Path(self.argument("to")).joinpath(
                self._device.deviceName, rigid, fwFile
            ).as_posix()

            try:
                fxu.download(fwObj, cfg.firmwareBucket, str(dest), cfg.dephyProfile)
            except (
                bce.ProfileNotFound,
                bce.PartialCredentialsError,
                bce.ClientError,
                bce.EndpointConnectionError,
            ) as err:
                self.line(err)
                sys.exit(1)
            except AssertionError as err:
                raise exceptions.S3DownloadError(
                    cfg.firmwareBucket, fwObj, dest
                ) from err

        return dest

    # -----
    # _flash_habs
    # -----
    def _flash_habs(self, fwFile: str | Path) -> List[str]:

        cmd = [
            # When unzipping, the zipped folder is put into a folder of the same name as the zip
            # so there is a "nesting" effect
            f"{Path.joinpath(cfg.toolsDir, 'stm32_flash_loader', 'stm32_flash_loader', 'STMFlashLoader.exe')}",
            "-c",
            "--pn",
            # It requires the port number, so if port=COM3, we pass 3
            f"{self._device.port[-1]}",
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
