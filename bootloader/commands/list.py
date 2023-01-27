from typing import List
from typing import Self

import boto3
from cleo.helpers import option

from bootloader.utilities.aws import get_s3_objects
import bootloader.utilities.config as cfg

from bootloader.utilities.aws import get_s3_object_info

from .init import InitCommand


# ============================================
#                 ListCommand
# ============================================
class ListCommand(InitCommand):

    name = "list"

    description = "Lists firmware, devices, and hardware available for bootloading."

    options = [
        option("devices", "-d", "List devices that can be bootloaded.", flag=True),
        option("hardware", "-r", "List available hardware versions.", flag=True),
        option("firmware", None, "List firmware versions.", flag=True),
        option("c-libraries", None, "List available C libraries.", flag=True),
    ]

    help = """
    Displays the devices, hardware versions, firmware versions, and versions
    of the pre-compiled C libraries that are available for bootloading.

    Examples
    --------
    # Show all
    > bootload list

    # Show only devices
    > bootload list --devices
    """

    # -----
    # handle
    # -----
    def handle(self: Self) -> int:
        """
        Entry point for the command.
        """
        self._stylize()
        self._check_keys()

        showDevices = self.option("devices")
        showHardware = self.option("hardware")
        showFirmware = self.option("firmware")
        showLibraries = self.option("c-libraries")

        _all = not (showDevices or showHardware or showFirmware or showLibraries)

        fwInfo = get_s3_object_info(cfg.firmwareBucket)
        libsInfo = get_s3_object_info(cfg.libsBucket)

        if showDevices:
            self._list_devices(fwInfo)
        if showHardware:
            self._list_hardware(fwInfo)
        if showFirmware:
            self._list_firmware(fwInfo)
        if showLibraries:
            self._list_libraries(libsInfo)
        if _all:
            self._list_all(fwInfo)
            self._list_libraries(libsInfo)

        return 0

    # -----
    # _list_devices
    # -----
    def _list_devices(self: Self, info: dict) -> None:
        devices = set()

        for versionDict in info.values():
            for deviceSet in versionDict.values():
                devices.update(deviceSet)

        self.line("Available devices:")
        for device in devices:
            self.line(f"\t- <info>{device}</info>")

    # -----
    # _list_hardware
    # -----
    def _list_hardware(self: Self, info: dict) -> None:
        hardware = set()

        for versionDict in info.values():
            for hw in versionDict:
                hardware.add(hw)

        self.line("Available hardware:")
        for hw in hardware:
            self.line(f"\t- <info>{hw}</info>")

    # -----
    # _list_firmware
    # -----
    def _list_firmware(self: Self, info: dict) -> None:
        self.line("Available versions:")
        for version in info:
            self.line(f"\t- <info>{version}</info>")

    # -----
    # _list_libraries
    # -----
    def _list_libraries(self: Self, libs: List[str]) -> None:
        self.line("Available pre-compiled C libraries:")
        for lib in libs:
            self.line(f"\t- <info>{lib}</info>")

    # -----
    # _list_all
    # -----
    def _list_all(self: Self, info: dict) -> None:
        for version in info:
            self.line(f"<info>Version</info>: {version}")
            for hw, devices in info[version].items():
                self.line(f"{self._pad}<info>Hardware</info> {hw}")
                for device in devices:
                    self.line(f"{self._pad}{self._pad}- <warning>{device}</warning>")
