from pathlib import Path


# ============================================
#              DeviceNotFoundError
# ============================================
class DeviceNotFoundError(Exception):
    """
    Raised if we are unable to connect to a valid Dephy device.
    """

    # -----
    # constructor
    # -----
    def __init__(self, port: str = "") -> None:
        self._port = port

    # -----
    # __str__
    # -----
    def __str__(self) -> str:
        msg = "<error>Error: could not find a device.</error>"
        if self._port:
            msg += f"\n\tPort given: <info>{self._port}</info>"
        return msg


# ============================================
#              FlashFailedError
# ============================================
class FlashFailedError(Exception):
    """
    Raised when the flashing process fails.
    """

    # -----
    # constructor
    # -----
    def __init__(self, cmd: str) -> None:
        self._cmd = cmd

    # -----
    # __str__
    # -----
    def __str__(self) -> str:
        msg = "<error>Error: flashing failed:</error>"
        for cmdPiece in self._cmd:
            msg += f"\n\t{cmdPiece}"
        return msg


# ============================================
#            FirmwareNotFoundError
# ============================================
class FirmwareNotFoundError(Exception):
    """
    Raised when the desired firmware cannot be found on S3.
    """

    # -----
    # constructor
    # -----
    def __init__(self, fwObj: Path, fwVer: str, deviceType: str, target: str) -> None:
        self._fwObj = fwObj
        self._fwVer = fwVer
        self._deviceType = deviceType
        self._target = target

    # -----
    # __str__
    # -----
    def __str__(self) -> str:
        msg = "<error>Error: unable to locate firmware file.</error>"
        msg += f"\n\tS3 object: {self._fwObj}"
        msg += f"\n\tFirmware version: {self._fwVer}"
        msg += f"\n\tDevice type: {self._deviceType}"
        msg += f"\n\tTarget: {self._target}"

        return msg


# ============================================
#             NoBluetoothImageError
# ============================================
class NoBluetoothImageError(Exception):
    """
    Raised when we cannot find the required bluetooth file.
    """

    # -----
    # constructor
    # -----
    def __init__(self, imgFile: Path) -> None:
        self._imgFile = imgFile

    # -----
    # __str__
    # -----
    def __str__(self) -> str:
        msg = f"<error>Error: could not find file:</error>\n\t{self._imgFile}"
        return msg


# ============================================
#               S3DownloadError
# ============================================
class S3DownloadError(Exception):
    """
    Raised when a file fails to download from S3.
    """

    # -----
    # constructor
    # -----
    def __init__(self, bucket: str, file: str, path: str) -> None:
        self._bucket = bucket
        self._file = file
        self._path = path

    # -----
    # __str__
    # -----
    def __str__(self) -> str:
        msg = "<error>Error: failed to download from S3:</error>"
        msg += f"\n\tFile: <info>{self._file}</info>"
        msg += f"\n\tBucket: <info>{self._bucket}</info>"
        msg += f"\n\tDestination: <info>{self._path}</info>"
        return msg


# ============================================
#             UnsupportedOSError
# ============================================
class UnsupportedOSError(Exception):
    """
    Raised when running on an unsupported operating system.
    """

    # -----
    # constructor
    # -----
    def __init__(self, currentOS, supportedOS) -> None:
        self._currentOS = currentOS
        self._supportedOS = supportedOS

    # -----
    # __str__
    # -----
    def __str__(self) -> str:
        msg = "<error>Error: unsupported OS!"
        msg += f"\n\tDetected: <info>{self._currentOS}"
        msg += "\n\tSupported:"
        for operatingSystem in self._supportedOS:
            msg += f"\n\t\t* <info>{operatingSystem}</info>"
        return msg
