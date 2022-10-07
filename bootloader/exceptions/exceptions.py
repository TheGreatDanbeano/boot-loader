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
    def __init__(self, device: str, mcu: str) -> None:
        self.device = device
        self.mcu = mcu

    # -----
    # __str__
    # -----
    def __str__(self) -> str:
        msg = f"<error>Error: unknown microcontroller</error>:\n\tMCU: {self.mcu}\n\t"
        msg += f "device: {self.device}"
        return msg


# ============================================
#                DownloadError
# ============================================
class S3DownloadError(Exception):
    """
    Raised when a file fails to download from S3.
    """
    # -----
    # constructor
    # -----
    def __init__(self, bucket: str, file: str, path: str) -> None:
        self.bucket = bucket
        self.file = file
        self.path = path

    # -----
    # __str__
    # -----
    def __str__(self) -> str:
        msg = f"<error>Error: failed to download:</error>\n\tfile: {self.file}\n\t"
        msg += f "bucket: {self.bucket}\n\tdestination: {self.path}"
        return msg
