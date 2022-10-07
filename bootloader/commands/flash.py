import os
import sys
from time import sleep
from typing import List

from cleo import Command
from flexsea.device import Device
from rsyncs3 import RsyncS3
from serial.tools.list_ports import comports

from bootloader.exceptions.exceptions import S3DownloadError
from bootloader.exceptions.exceptions import UnknownMCUError
from bootloader.io.write import display_logo
from bootloader.utilities.config import firmwareBucket
from bootloader.utilities.config import firmwareDir


# ============================================
#                FlashCommand
# ============================================
class FlashCommand(Command):
    """
    Flashes firmware onto a Dephy device. If no microcontroller is
    specified, flash all of them.

    flash
        {firmwareVersion : Semantic version string of the firmware to
            flash; e.g., 7.2.0}
        {--habs : Flash firmware onto the Habs microcontroller.}
        {--ex : Flash firmware onto the Execute microcontroller.}
        {--re : Flash firmware onto the Regulate microcontroller.}
        {--mn : Flash firmware onto the Manage microcontroller.}
        {--p|ports=* : Name of the port the device is connected to;
            e.g., /dev/ttyACM0. If not given, we try to determine the
            ports automatically.}
    """
    # -----
    # constructor
    # -----
    def __init__(self) -> None:
        super().__init__()
        self._microcontrollers = []
        self._devices = []

    # -----
    # handle
    # -----
    def handle(self) -> None:
        """
        Entry point for the command. Steps:

            * Configures the environment, if needed

            * Attempts to determine the port the device is connected
                to if no port is given

            * Reads info from the device(s) in order to determine the
                appropriate firmware file for each device

            * Downloads the desired firmware if it isn't already
                cached

            * Flashes the firmware onto the device(s)
        """
        display_logo(self.line)
        self.call("init")
        self._get_microcontrollers()

        try:
            self._find_devices()
        except ValueError:
            msg = "<error>Error: unable to find any devices.</error>"
            self.line(msg)
            sys.exit(1)

        try:
            self._get_firmware()
        except UnknownMCUError as err:
            self.line(err)
            sys.exit(1)
        except S3DownloadError as err:
            self.line(err)
            sys.exit(1)

        self._flash()

    # -----
    # _get_microcontrollers
    # -----
    def _get_microcontrollers(self) -> None
        """
        Constructs a list of microcontrollers to flash based on the
        flags passed by the user.
        """
        if self.option("habs"):
            self._microcontrollers.append("habs")

        if self.option("ex"):
            self._microcontrollers.append("ex")

        if self.option("re"):
            self._microcontrollers.append("re")

        if self.option("mn"):
            self._microcontrollers.append("mn")

        if not microcontrollers:
            self._microcontrollers = ["habs", "ex", "re", "mn"]

    # -----
    # _find_devices
    # -----
    def _find_devices(self)- > None:
        """
        Searches the given ports or available ports for valid Dephy
        devices. These are the devices that will be flashed.
        """
        if not self.option("ports"):
            for port in comports():
                self.option("ports").append(port.name)

        for port in self.option("ports"):
            device = Device(port, 230400)

            try:
                device.open()
            except IOError:
                continue

            device.close()
            self._devices.append(device)

        if not self._devices:
            raise ValueError

    # -----
    # _get_firmware
    # -----
    def _get_firmware(self) -> None:
        """
        Checks to see if the necessary firmware files exist in the
        cache. If they don't, we download them.
        """
        for device in self._devices:
            for mcu in self._microcontrollers:
                if mcu == "habs" and not device.hasHabs:
                    continue

                fwFile = self._build_firmware_file(device, mcu)

                path = os.path.join(
                    firmwareDir,
                    self.argument("firmwareVersion"), 
                    device.deviceType
                )

                if not os.path.exists(os.path.join(path, fwFile)):
                    # Not using os.path.join b/c I don't think AWS
                    # supports Windows separators
                    fwObj = f"{self.argument('firmwareVersion')}/{device.deviceType}/"
                    fwObj += f"{fwFile}"

                    rs = RsyncS3(firmwareBucket, f"{fwObj}", path)
                    rs.sync()

                    # As far as I can tell, boto3 doesn't raise an
                    # exception if the file you're trying to download
                    # either fails or doesn't exist. Here we check to
                    # see if the file exists as a work-around
                    if not os.path.exists(os.path.join(path, fwFile)):
                        raise S3DownloadError(firmwareBucket, fwFile, path)

    # -----
    # _build_firmware_file
    # -----
    def _build_firmware_file(self, device, mcu):
        """
        Constructs the name of the firmware file from the device and
        microcontroller information.
        """
        devType = device.deviceType
        rigid = device.rigid
        fwVer = self.argument("firmwareVersion")

        if mcu == "mn":
            ext = "dfu"
        elif mcu == "ex" or mcu == "re":
            ext = "cyacd"
        elif mcu == "habs":
            ext = "hex"
        else:
            raise UnknownMCUError(device, mcu)

        return f"{devType}_rigid-{rigid}_{mcu}_firmware-{fwVer}.{ext}"

    # -----
    # _flash
    # -----
    def _flash(self):
        """
        Uses the STM32 and PSoC flashing tools to flash each device
        with the desired firmware.

        NOTE: There should be version checks. That is, if you're on
        version x and want to flash version y, make sure this is
        possible. Also have a check per microcontroller. That is, if
        the major version of ex or re is changing to be different than
        mn (because mn wasn't selected to be flashed by user), then we
        should abort, because mn won't be able to communicate, and
        vice versa

        NOTE: These flashes are all retried a max of 5 times and there
        are sleeps between them
        """
        for device in self._devices:
            path = os.path.join(
                firmwareDir,
                self.argument("firmwareVersion"), 
                device.deviceType,
            )
            # Ensure that we flash the microcontrollers on the device
            # in the right order (so we can't loop over
            # _microcontrollers)
            if "habs" in self._microcontrollers:
                if not device.hasHabs:
                    msg = "<warning>Warning:</warning> Flashing Habs was requested, "
                    msg += f"but `{device.deviceType}` does not have Habs. Skipping."
                    self.line(msg)
                else:
                    fwFile = self._build_firmware_file(device, mcu)
                    fwFile = os.path.join(path, fwFile)
                    set_tunnel_mode("Habs") # Uses bootloader.py, so pull that code in here
                    # This is pulled from bootload.sh, so needs to be cleaned
                    # $1 is the name of the firmware file to flash
                    STMFlashLoader.exe -c --pn ${COM_PORT//[!0-9]/} --br 115200 --db 8 --pr NONE -i STM32F3_7x_8x_256K -e --all -d --fn "$1" -o --set --vals --User 0xF00F

            if "ex" in self._microcontrollers:
                set_tunnel_model("Exe")
                psocbootloaderhost.exe ${COM_PORT} "$1" # $1 is the fw file
            if "re" in self._microcontrollers:
                set_tunnel_model("Reg")
                psocbootloaderhost.exe ${COM_PORT} "$1" # $1 is the fw file
            if "mn" in self._microcontrollers:
                set_tunnel_mode("Mn")
                DfuSeCommand.exe -c -d --fn "$1" # $1 is the fw file
