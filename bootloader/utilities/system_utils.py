import glob
import os
from pathlib import Path
import shutil
import subprocess as sub
from typing import Union

from serial.tools.list_ports import comports
from flexsea.device import Device

from bootloader.exceptions import exceptions
from bootloader.utilities import config as cfg


# ============================================
#                 find_device
# ============================================
def find_device(port: Union[str, None], cLibVersion: str) -> Device:
    """
    Tries to establish a connection to the Dephy device given by
    the user-supplied port. If no port is supplied, then we loop
    over all available serial ports to try and find a valid device.

    Parameters
    ----------
    port : Union[str, None]
        The name of the port to connect to, e.g., '/dev/ttyACM0'. If
        no port is given, we loop over all available serial ports.

    cLibVersion : str
        The semantic version string of the firmware currently on the device.

    Raises
    ------
    DeviceNotFoundError
        If no valid Dephy device can be found.

    Returns
    -------
    device : Device
        An instance of the `flexsea` `Device` class that provides an
        interface for communicating with the device.
    """
    device = None

    if not port:
        for _port in comports():
            _device = Device(_port.device, 230400, cLibVersion)
            try:
                _device.open()
            except IOError:
                continue
            device = _device
            break

    else:
        _device = Device(port, 230400, cLibVersion)
        try:
            _device.open()
        except IOError as err:
            raise exceptions.DeviceNotFoundError(port=port) from err
        device = _device

    if not device:
        raise exceptions.DeviceNotFoundError()

    return device


# ============================================
#              build_bt_image_file
# ============================================
def build_bt_image_file(level: int, address: str) -> Path:
    """
    Uses the bluetooth tools repo (downloaded as a part of `init`)
    to create a bluetooth image file with the correct address.

    Raises
    ------
    NoBluetoothImageError
        If the required gatt file isn't found.

    FlashFailedError
        If a subprocess returns a code of 1.
    """
    # Everything within the bt121 directory is self-contained and
    # self-referencing, so it's easiest to switch to that directory
    # first
    cwd = Path.cwd()
    os.chdir(Path.joinpath(cfg.toolsDir, "bt121_image_tools"))

    gattTemplate = Path("gatt_files").joinpath(f"{level}.xml")
    gattFile = Path("dephy_gatt_broadcast_bt121").joinpath("gatt.xml")

    if not Path.exists(gattTemplate):
        raise exceptions.NoBluetoothImageError(gattTemplate)

    shutil.copyfile(gattTemplate, gattFile)

    cmd = ["python3", "bt121_gatt_broadcast_img.py", f"{address}"]
    with sub.Popen(cmd) as proc:
        pass

    if proc.returncode == 1:
        raise exceptions.FlashFailedError("bt121_gatt_broadcast_img.py")

    bgExe = Path.joinpath("smart-ready-1.7.0-217", "bin", "bgbuild.exe")
    xmlFile = Path.joinpath("dephy_gatt_broadcast_bt121", "project.xml")
    with sub.Popen([bgExe, xmlFile]) as proc:
        pass

    if proc.returncode == 1:
        raise exceptions.FlashFailedError("bgbuild.exe")

    if Path("output").exists():
        files = glob.glob(os.path.join("output", "*.bin"))
        for file in files:
            os.remove(file)
    else:
        os.mkdir("output")

    btImageFileBase = f"dephy_gatt_broadcast_bt121_Exo-{address}.bin"
    shutil.move(Path.joinpath("dephy_gatt_broadcast_bt121", btImageFileBase), "output")
    btImageFile = Path.cwd().joinpath("bt121_image_tools", "output", btImageFileBase)

    os.chdir(cwd)

    return btImageFile
