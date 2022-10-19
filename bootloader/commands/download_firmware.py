import os
import sys

from cleo import Command
from rsyncs3 import RsyncS3

from bootloader.exceptions.exceptions import S3DownloadError
from bootloader.exceptions.exceptions import UnknownMCUError
from bootloader.utilities.config import firmwareBucket
from bootloader.utilities.config import firmwareDir
from bootloader.utilities.config import mcuTargets


# ============================================
#           DownloadFirmwareCommand
# ============================================
class DownloadFirmwareCommand(Command):
    """
    Downloads the desired firmware, if it isn't already cached.

    download-firmware
        {fwVersion : Firmware version we want.}
        {deviceType : The type of device for which we want firmware, e.g., `actpack`}
        {mcu : The microcontroller we want firmware for, e.g., `mn`.}
        {hwVer : The device's rigid (hardware) version, e.g., 4.1}
    """

    _deviceType = None
    _fwFile = None
    _fwVer = None
    _hwVer = None
    _mcu = None

    # -----
    # handle
    # -----
    def handle(self) -> None:
        """
        Entry point for the command.
        """
        self._fwVer = self.argument("fwVersion")
        self._deviceType = self.argument("deviceType")
        self._mcu = self.argument("mcu")
        self._hwVer = self.argument("hwVer")

        try:
            self._build_firmware_file()
        except UnknownMCUError as err:
            self.line(err)
            sys.exit(1)

        self.write(f"Searching for firmware: {self._fwFile}...")

        if not self._firmware_exists():
            self.write("\n\t<warning>Firmware not found.</warning>")
            self.write("\n\tDownloading...")

            try:
                self._download_firmware()
            except S3DownloadError as err:
                self.line(err)
                sys.exit(1)

            self.overwrite("\n\tDownloading... <success>✓</success>\n")

        self.overwrite(
            f"Searching for firmware: {self._fwFile}...<success>✓</success>\n"
        )

    # -----
    # _build_firmware_file
    # -----
    def _build_firmware_file(self) -> None:
        """
        Constructs the name of the firmware file from the device and
        microcontroller information.
        """
        if self._mcu == "mn":
            ext = "dfu"
        elif self._mcu in ("ex", "re"):
            ext = "cyacd"
        elif self._mcu == "habs":
            ext = "hex"
        else:
            raise UnknownMCUError(self._mcu, mcuTargets)

        self._fwFile = f"{self._deviceType}_rigid-{self._hwVer}_{self._mcu}_"
        self._fwFile += f"firmware-{self._fwVer}.{ext}"

    # -----
    # _firmware_exists
    # -----
    def _firmware_exists(self) -> bool:
        """
        Checks to see if the constructed firmware file is already in the
        cache.
        """
        path = os.path.join(firmwareDir, self._fwVer, self._deviceType)
        return os.path.exists(os.path.join(path, self._fwFile))

    # -----
    # _download_firmware
    # -----
    def _download_firmware(self) -> None:
        """
        Downloads the desired firmware from S3.
        """
        dest = os.path.join(firmwareDir, self._fwVer, self._deviceType)

        # Not using os.path.join b/c I don't think AWS
        # supports Windows separators
        fwObj = f"{self._fwVer}/{self._deviceType}/{self._fwFile}"

        rs = RsyncS3(firmwareBucket, f"{fwObj}", dest)
        rs.sync()

        # As far as I can tell, boto3 doesn't raise an
        # exception if the file you're trying to download
        # either fails or doesn't exist. Here we check to
        # see if the file exists as a work-around
        if not os.path.exists(os.path.join(dest, self._fwFile)):
            raise S3DownloadError(firmwareBucket, self._fwFile, dest)
