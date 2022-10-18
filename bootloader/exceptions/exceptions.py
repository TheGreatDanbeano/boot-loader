from typing import List


# ============================================
#                UnknownMCUError
# ============================================
class UnknownMCUError(Exception):
    """
    Raised when trying to flash an unexpected, unknown, or unsupported
    microcontroller.
    """

    # -----
    # constructor
    # -----
    def __init__(self, mcu: str, supportedMCUs: List) -> None:
        self._mcu = mcu
        self._supportedMCUs = supportedMCUs

    # -----
    # __str__
    # -----
    def __str__(self) -> str:
        msg = "<error>Error: unknown microcontroller</error>:"
        msg += f"\n\tMicrocontroller: <info>{self._mcu}</info>"
        msg += "\n\tSupported:"
        for mcu in self._supportedMCUs:
            msg += f"\n\t\t* <info>{mcu}</info>"
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


# ============================================
#               AccessKeyError
# ============================================
class AccessKeyError(Exception):
    """
    Raised when either the public or private AWS S3 access key for the
    firmware isn't found.
    """

    # -----
    # constructor
    # -----
    def __init__(self, key) -> None:
        self._key = key

    # -----
    # __str__
    # -----
    def __str__(self) -> str:
        msg = f"<error>Error: `{self._key}` key not found!</error>"
        msg += "\n\tPlease save your key in the following environment variable:"
        if self._key == "public":
            msg += "\n\t\t<info>DEPHY_PUBLIC_KEY</info>"
        elif self._key == "secret":
            msg += "\n\t\t<info>DEPHY_SECRET_KEY</info>"
        else:
            raise ValueError("`key` must be either `public` or `secret`.")
        return msg


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
