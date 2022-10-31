from pathlib import Path
import platform
import sys
import tempfile

import botocore.exceptions as bce
from cleo.helpers import option
from flexsea.device import Device

from bootloader.commands.download import DownloadCommand
from bootloader.exceptions import exceptions
import bootloader.utilities.config as cfg
from bootloader.utilities import logo
from bootloader.utilities import system_utils as su


# ============================================
#                 InitCommand
# ============================================
class InitCommand(DownloadCommand):
    name = "init"
    description = "Sets up the environment for flashing."
    options = [
        option(
            "port", "-p", "Name of the device's port, e.g., '/dev/ttyACM0'", flag=False
        ),
    ]
    help = """Performs the following steps:
        * Prompts to make sure the battery is removed from the device
        * Makes sure a supported OS is being used
        * Locates the device to be flashed
        * Makes sure that the required STM and PSoC tools are installed
            * Downloads them if they are not
        * Makes sure the required firmware is available, if applicable
            * Downloads it if not

        Examples
        --------
        bootloader init
        bootloader init -f=7.2.0
        """

    _device: Device | None = None

    # -----
    # handle
    # -----
    def handle(self) -> int:
        """
        Entry point for the command.
        """
        try:
            self._setup(self.option("port"))
        except ValueError:
            return 1

        return 0

    # -----
    # _setup
    # -----
    def _setup(self, port: str = "") -> None:
        """
        Runs the setup process.

        The work is done here instead of in `handle` so that child
        classes can have access.

        Parameters
        ----------
        port : str (optional)
            The name of the COM port the device to be flashed is connected
            to.

        Raises
        ------
        ValueError
            If the user does not confirm the battery is removed from
            the device.
        """
        try:
            self.line(logo.dephyLogo)
        except UnicodeEncodeError:
            self.line(logo.dephyLogoPlain)

        self.line("Welcome to the Dephy bootloader!")

        msg = "<warning>Please make sure the battery is removed![y|n]</warning>"
        if not self.confirm(msg, False):
            raise ValueError

        try:
            self._check_os()
        except exceptions.UnsupportedOSError as err:
            self.line(err)
            sys.exit(1)

        self._setup_cache()

        try:
            self._check_keys()
        except (
            exceptions.InvalidKeyError,
            exceptions.MissingKeyError,
            exceptions.NetworkError,
            exceptions.NoCredentialsError,
            exceptions.NoProfileError,
        ) as err:
            self.line(err)
            sys.exit(1)

        try:
            self._check_tools()
        except (exceptions.NetworkError, exceptions.S3DownloadError) as err:
            self.line(err)
            sys.exit(1)

        # In case init is called more than once
        if not self._device:
            try:
                self._device = su.find_device(port)
            except exceptions.DeviceNotFoundError as err:
                self.line(err)
                sys.exit(1)

    # -----
    # _check_os
    # -----
    def _check_os(self) -> None:
        """
        Makes sure we're running on a supported OS.

        Raises
        ------
        UnsupportedOSError
            If the detected operating system is not supported.
        """
        self.write("Checking OS...")

        currentOS = platform.system().lower()

        try:
            assert currentOS in cfg.supportedOS
        except AssertionError as err:
            raise exceptions.UnsupportedOSError(currentOS, cfg.supportedOS) from err

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

        Path(cfg.firmwareDir).mkdir(parents=True, exist_ok=True)
        Path(cfg.toolsDir).mkdir(parents=True, exist_ok=True)

        self.overwrite("Setting up cache... <success>✓</success>\n")

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
        InvalidKeyError
            If one or both of the keys are invalid.

        MissingKeyError
            If one or both of the required keys are missing.

        NetworkError
            If we cannot connect to AWS.

        NoCredentialsError
            If the `~/.aws/credentials` file doesn't exist.

        NoProfileError
            If the `dephy` profile doesn't exist in the AWS
            credentials file.
        """
        self.write("Checking for access keys...")

        # If a key is invalid, we won't know until we try to download
        # something, and it's easier to check that now
        with tempfile.TemporaryFile() as fd:
            try:
                self._download(
                    cfg.connectionFile, cfg.firmwareBucket, fd, cfg.dephyProfile
                )
            except bce.ClientError as err:
                raise exceptions.InvalidKeyError from err
            except bce.EndpointConnectionError as err:
                raise exceptions.NetworkError from err
            finally:
                fd.close()

        self.overwrite("<info>Checking for access keys</info> <success>✓</success>\n")

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
        NetworkError
            If we cannot connect to AWS.

        S3DownloadError
            If a tool fails to download.
        """
        for tool in cfg.bootloaderTools:
            self.write(f"Searching for: <info>{tool}</info>...")

            dest = Path(cfg.toolsDir).joinpath(tool)

            if not dest.exists():
                self.line(f"\n\t<info>{tool}</info> <warning>not found.</warning>")

                self.write("\tDownloading...")

                try:
                    self._download(tool, cfg.toolsBucket, dest, cfg.dephyProfile)
                except bce.EndpointConnectionError as err:
                    raise exceptions.NetworkError from err

                if not dest.exists():
                    raise exceptions.S3DownloadError(
                        cfg.toolsBucket, tool, cfg.toolsDir
                    )

                self.overwrite("\tDownloading... <success>✓</success>\n")

            else:
                msg = f"Searching for: <info>{tool}</info>...<success>✓</success>\n"
                self.overwrite(f"{msg}\n")
