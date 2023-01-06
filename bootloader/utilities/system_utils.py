import glob
import os
from pathlib import Path
import shutil
import subprocess as sub

from bootloader.exceptions import exceptions
from bootloader.utilities import config as cfg


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
    # When unzipping, the zipped folder gets put into a folder with the same name as
    # the archive, creating a "nesting" effect
    os.chdir(Path.joinpath(cfg.toolsDir, "bt121_image_tools", "bt121_image_tools"))

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
