import sys

from cleo import Command
from serial.tools.list_ports import comports

from bootloader.exceptions.exceptions import DeviceNotFoundError
from bootloader.exceptions.exceptions import UnknownMCUError
from bootloader.utilities.config import mcuTargets


# ============================================
#               FlashMCUCommand
# ============================================
class FlashMCUCommand(Command):
    """
    Flashes a microcontroller on a Dephy device with the desired firmware.

    flash-mcu
        {target : The controller to flash. Can be: `habs`, `ex`, `re`, `mn`, or `all`.}
        {fwVersion : Semantic version string of the desired firmware, e.g., `7.2.0`.}
        {--p|port= : Name of the serial port to connect to, e.g., `/dev/ttyACM0`}
    """

    _target = None
    _fwVersion = None
    _device = None
    _port = ""

    # -----
    # handle
    # -----
    def handle(self) -> None:
        """
        Entry point for the command.
        """
        self._target = self.argument("target")
        self._fwVersion = self.argument("fwVersion") 
        self._port = self.option("port")

        self.call("init")

        try:
            self._device = find_device(self._port)
        except DeviceNotFoundError as err:
            self.line(err)
            sys.exit(1)

        try:
            self._get_targets()
        except UnknownMCUError as err:
            self.line(err)
            sys.exit(1)

        _fwv = self._fwVersion
        _devType = self._device.deviceType
        _hwVer = self._device.rigidVersion

        for mcu in self._targets:
            self.line(f"<info>Flashing {mcu}...</info>")
            self.call("download-firmware", f"{_fwv} {_devType} {mcu} {_hwVer}")
            fwFile = self._build_firmware_file(_fwv, _devType, _hwVer, mcu)
            set_tunnel_mode(mcu)

            if mcu == "habs":
                cmd = self._flash_habs(fwFile)
            elif mcu == "ex":
                cmd = self._flash_ex(fwFile)
            elif mcu == "re":
                cmd = self._flash_re(fwFile)
            elif mcu == "mn":
                cmd = self._flash_mn(fwFile)

            process = sub.Popen(cmd)
            process.wait()

            self.line(f"<info>Flashing {mcu}...</info> <success>✓</success>")
            _ = self.ask("Please power cycle the device, then press `ENTER`")
            sleep(3)
            self.line("")
            self.line("")


    # -----
    # _get_targets
    # -----
    def _get_targets(self) -> None:
        """
        Converts the given target into a list so as to be able to handle
        the `all` case more easily.
        """
        try:
            assert self._target in mcuTargets
        except AssertionError:
            raise UnknownMCUError(self._target, mcuTargets)

        if self._target == "all":
            self._targets = mcuTargets
        else:
            self._targets = [self._target,]

        if not self._device.hasHabs and "habs" in self._targets:
            self._targets.remove("habs")


    # -----
    # _build_firmware_file
    # -----
    def _build_firmware_file(self, fwVer, devType, hwVer, mcu) -> None:
        """
        Constructs the name of the firmware file from the device and
        microcontroller information.
        """
        path = os.path.join(
            firmwareDir,
            fwVer,
            deviceType
        )

        if mcu == "mn":
            ext = "dfu"
        elif mcu == "ex" or mcu == "re":
            ext = "cyacd"
        elif mcu == "habs":
            ext = "hex"
        else:
            raise UnknownMCUError(mcu, supportedMCUs)

        fwFile = f"{devType}_rigid-{hwVer}_{mcu}_firmware-{fwVer}.{ext}"

        return os.path.join(path, fwFile)

    # -----
    # _flash_habs
    # -----
    def _flash_habs(self, fwFile) -> List[str]:
        cmd = [
            f"{os.path.join(toolsDir, STMFlashLoader.exe)}",
            "-c",
            "--pn",
            f"{self._port}",
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
            "0xF00F"
        ]
        
        return cmd

    # -----
    # _flash_ex
    # -----
    def _flash_ex(self, fwFile) -> List[str]:
        cmd = [
            f"{os.path.join(toolsDir, psocbootloaderhost.exe)}",
            f"{self._port}",
            f"{fwFile}",
        ]

        return cmd

    # -----
    # _flash_re
    # -----
    def _flash_re(self, fwFile) -> List[str]:
        cmd = [
            f"{os.path.join(toolsDir, psocbootloaderhost.exe)}",
            f"{self._port}",
            f"{fwFile}",
        ]

        return cmd

    # -----
    # _flash_mn
    # -----
    def _flash_mn(self, fwFile) -> List[str]:
        cmd = [
            f"{os.path.join(toolsDir, DfuSeCommand.exe)}",
            "-c",
            "-d",
            "--fn",
            f"{fwFile}",
        ]

        return cmd
