import os
import platform
import sys

from cleo import Command
from rsyncs3 import RsyncS3

from bootloader.exceptions.exceptions import AccessKeyError
from bootloader.exceptions.exceptions import S3DownloadError
from bootloader.exceptions.exceptions import UnsupportedOSError
from bootloader.io.write import display_logo
from bootloader.utilities.config import bootloaderTools
from bootloader.utilities.config import firmwareDir
from bootloader.utilities.config import supportedOS
from bootloader.utilities.config import toolsBucket
from bootloader.utilities.config import toolsDir


# ============================================
#                 InitCommand
# ============================================
class InitCommand(Command):
    """
    Lays the foundation for flashing a Dephy device.

    init
    """

    # -----
    # handle
    # -----
    def handle(self) -> None:
        """
        Entry point for the command. Steps:
        """
        display_logo(self.line)

        self.line("Welcome to the Dephy bootloader!")

        msg = "<warning>Please make sure the battery is removed!</warning>"
        if not self.confirm(msg):
            sys.exit(1)

        try:
            self._check_os()
        except UnsupportedOSError as err:
            self.line(err)
            sys.exit(1)

        self._setup_cache()

        try:
            self._check_tools()
        except S3DownloadError as err:
            self.line(err)
            sys.exit(1)

        try:
            self._check_keys()
        except AccessKeyError as err:
            self.line(err)
            sys.exit(1)

    # -----
    # _check_os
    # -----
    def _check_os(self) -> None:
        """
        Makes sure we're running on Windows because PSoC's tools don't
        work on Linux.

        Raises
        ------
        UnsupportedOSError
            If the detected operating system is not supported.
        """
        self.write("Checking OS...")

        currentOS = platform.system().lower()

        try:
            assert currentOS in supportedOS
        except AssertionError as err:
            raise UnsupportedOSError(currentOS, supportedOS) from err

        self.overwrite("Checking OS... <success>✓</success>\n")

    # -----
    # _setup_cache
    # -----
    def _setup_cache(self) -> None:
        """
        Creates the directories where the firmware files and bootloader
        tools are downloaded and installed to.
        """
        self.write("Setting up cache...")

        os.makedirs(firmwareDir, exist_ok=True)
        os.makedirs(toolsDir, exist_ok=True)

        self.overwrite("Setting up cache... <success>✓</success>\n")

    # -----
    # _check_tools
    # -----
    def _check_tools(self) -> None:
        """
        The bootloader requires tools from PSoC and STM in order to
        flash the microcontrollers. Here we make sure that those tools
        are installed. If they aren't, then we download and install
        them.

        Raises
        ------
        S3DownloadError
            If a tool fails to download.
        """
        for tool in bootloaderTools:
            self.write(f"Searching for: <info>{tool}</info>...")

            if not os.path.exists(os.path.join(toolsDir, tool)):
                self.line(f"\n\t<info>{tool}</info> <warning>not found.</warning>")

                self.write("\tDownloading...")

                with RsyncS3(toolsBucket, tool, toolsDir) as rs:
                    rs.sync()

                # rsyncs3 does not currently raise an exception if the
                # file doesn't exist, the bucket doesn't exist, or if
                # the download fails
                if not os.path.exists(os.path.join(toolsDir, tool)):
                    raise S3DownloadError(toolsBucket, tool, toolsDir)

                self.overwrite("\tDownloading... <success>✓</success>\n")

            else:
                msg = f"Searching for: <info>{tool}</info>...<success>✓</success>\n"
                self.overwrite(f"{msg}\n")

    # -----
    # _check_keys
    # -----
    def _check_keys(self) -> None:
        """
        Access to Dephy's firmware bucket on S3 requires a public and a
        prive access key, so here we make sure that those are saved in
        the user's environment.

        Raises
        ------
        AccessKeyError
            If either the public or secret key is not found.
        """
        self.write("Checking for access keys...")

        try:
            _ = os.environ["DEPHY_PUBLIC_KEY"]
        except KeyError as err:
            raise AccessKeyError("public") from err

        try:
            _ = os.environ["DEPHY_SECRET_KEY"]
        except KeyError as err:
            raise AccessKeyError("secret") from err

        self.overwrite("<info>Checking for access keys</info> <success>✓</success>\n")
