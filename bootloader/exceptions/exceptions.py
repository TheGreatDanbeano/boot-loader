from typing import List


# ============================================
#               AccessKeyError
# ============================================
class AccessKeyError(Exception):
    """
    Raised when either the public or private AWS S3 access key for the
    firmware isn't found.
    """

    # -----
    # __str__
    # -----
    def __str__(self) -> str:
        msg = "<error>Error: AWS access keys not found!</error>"
        msg += "\n\tPlease save your keys in <info>`~/.aws/credentials`</info> as:"
        msg += "\n\n\t\t<info>[dephy]\n\t\taws_access_key_id=XXXX"
        msg += "\n\t\taws_secret_access_key=YYYY\n\n</info>"
        msg += "\nYou should have received access to these keys with your purchase.\n"
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
    def __init__(self, cmd: List) -> None:
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
#               InvalidKeyError
# ============================================
class InvalidKeyError(Exception):
    """
    Raised if one (or both) of the AWS access key is (are) incorrect.
    """

    # -----
    # __str__
    # -----
    def __str__(self) -> str:
        msg = "<error>Error: invalid keys.</error>"
        return msg


# ============================================
#               MissingKeyError
# ============================================
class MissingKeyError(Exception):
    """
    Raised if one (or both) of the required AWS keys is (are) missing.
    """

    # -----
    # __str__
    # -----
    def __str__(self) -> str:
        msg = "<error>Error: Missing keys.</error>\n\t"
        msg += "Need both `aws_access_key_id` and `aws_secret_access_key` in\n\t"
        msg += "the `[dephy]` profile.\n\t"
        msg += "See: <info>https://tinyurl.com/4sc3rwut</info>"
        return msg


# ============================================
#                NetworkError
# ============================================
class NetworkError(Exception):
    """
    Raised if we cannot connect to AWS.
    """

    # -----
    # __str__
    # -----
    def __str__(self) -> str:
        msg = "<error>Error: could not connect to AWS.</error>\n\t"
        msg += "Check your internet connection."
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
    def __init__(self, imgFile: str) -> None:
        self._imgFile = imgFile

    # -----
    # __str__
    # -----
    def __str__(self) -> str:
        msg = f"<error>Error: could not find file:</error>\n\t{self._imgFile}"
        return msg


# ============================================
#              NoCredentialsError
# ============================================
class NoCredentialsError(Exception):
    """
    Raised if `boto3` cannot find any credentials.
    """

    # -----
    # __str__
    # -----
    def __str__(self) -> str:
        msg = "<error>Error: `~/.aws/credentials` file not found.</error>"
        return msg


# ============================================
#               NoProfileError
# ============================================
class NoProfileError(Exception):
    """
    Raised if the `[dephy]` profile isn't present in the AWS
    credentials file.
    """

    # -----
    # __str__
    # -----
    def __str__(self) -> str:
        msg = "<error>Error: `dephy` profile not found.</error>\n\t"
        msg += "Please save the access keys under `[dephy]` in `~/.aws/credentials`"
        msg += "\n\tSee: <info>https://tinyurl.com/4sc3rwut</info>"
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
