from typing import List
from typing import Self

import boto3
from cleo.helpers import option

from bootloader.utilities.aws import get_s3_objects
import bootloader.utilities.config as cfg

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
        option("versions", None, "List firmware versions.", flag=True),
    ]

    help = """
    Displays the devices, hardware versions, and firmware versions that are
    available for bootloading.

    Examples
    --------
    # Show all
    > bootload ls

    # Show only devices
    > bootload ls --devices
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
        showVersions = self.option("versions")

        _all = not (showDevices or showHardware or showVersions)

        session = boto3.Session(profile_name=cfg.dephyProfile)
        client = session.client("s3")
        objects = get_s3_objects(cfg.firmwareBucket, client)
        client.close()

        info = self._parse_firmware_objects(objects)

        if showDevices:
            self._list_devices(info)
        if showHardware:
            self._list_hardware(info)
        if showVersions:
            self._list_versions(info)
        if _all:
            self._list_all(info)

        return 0

    # -----
    # _parse_firmware_objects
    # -----
    def _parse_firmware_objects(self: Self, objects: List[str]) -> dict:
        """
        Converts the list of full-path firmware file names into a
        dictionary for easier display.

        Parameters
        ----------
        objects : List[str]
            List of full paths for firmware files from S3.

        Returns
        -------
        info : dict
            `objects` converted to a hierarchial dictionary form for
            cleaner display.
        """
        info = {}

        for obj in objects:
            version, device, hardware, _ = obj.split("/")
            if version not in info:
                info[version] = {
                    hardware: set(
                        [
                            device,
                        ]
                    )
                }
            else:
                if hardware not in info[version]:
                    info[version][hardware] = set(
                        [
                            device,
                        ]
                    )
                else:
                    info[version][hardware].add(device)
        return info

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
    # _list_versions
    # -----
    def _list_versions(self: Self, info: dict) -> None:
        self.line("Available versions:")
        for version in info:
            self.line(f"\t- <info>{version}</info>")

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
