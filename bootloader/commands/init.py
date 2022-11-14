import os
from pathlib import Path
import platform
import sys
import tempfile
import zipfile

import botocore.exceptions as bce
from cleo import Command
from cleo.helpers import option
import flexsea.config as fxc
from flexsea.device import Device
import flexsea.utilities as fxu

from bootloader.exceptions import exceptions
import bootloader.utilities.config as cfg
from bootloader.utilities import logo
from bootloader.utilities import system_utils as su


# ============================================
#                 InitCommand
# ============================================
class InitCommand(Command):
    name = "init"
    description = "Sets up the environment for flashing."
    options = [
        option(
            "port", "-p", "Name of the device's port, e.g., '/dev/ttyACM0'", flag=False
        ),
        option(
            "firmware",
            "-f",
            "Semantic version string of the device's current firmware, e.g. 7.2.0",
            flag=False,
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
            self._setup(self.option("port"), self.option("firmware"))
        except ValueError:
            return 1

        return 0

    # -----
    # _setup
    # -----
    def _setup(self, port: str = "", cLibVersion: str = fxc.LTS) -> None:
        """
        Runs the setup process.

        The work is done here instead of in `handle` so that child
        classes can have access.

        Parameters
        ----------
        port : str (optional)
            The name of the COM port the device to be flashed is connected
            to.

        cLibVersion : str
            The semantic version string of the firmware currently on the device.

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

        msg = "<warning>Please make sure the battery is removed!</warning>"
        if not self.confirm(msg, False):
            raise ValueError

        # try:
        #     self._check_os()
        # except exceptions.UnsupportedOSError as err:
        #     self.line(err)
        #     sys.exit(1)

        self._setup_cache()

        try:
            self._check_keys()
        except (
            bce.ClientError,
            bce.ProfileNotFound,
            bce.PartialCredentialsError,
            bce.EndpointConnectionError,
            exceptions.S3DownloadError,
        ) as err:
            self.line(err)
            sys.exit(1)

        try:
            self._check_tools()
        except (bce.EndpointConnectionError, exceptions.S3DownloadError) as err:
            self.line(err)
            sys.exit(1)

        # In case init is called more than once
        if not self._device:
            try:
                self._device = su.find_device(port, cLibVersion)
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

        cfg.firmwareDir.mkdir(parents=True, exist_ok=True)
        cfg.toolsDir.mkdir(parents=True, exist_ok=True)

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
        botocore.exceptions.ClientError
            If one or both of the keys are invalid.

        botocore.exceptions.PartialCredentialsError
            If one or both of the required keys are missing.

        botocore.exceptions.EndpointConnectionError
            If we cannot connect to AWS.

        botocore.exceptions.ProfileNotFound
            If the `dephy` profile doesn't exist in the AWS
            credentials file, or the credentials file doesn't exist.

        S3DownloadError
            If the download fails.
        """
        self.write("Checking for access keys...")

        # If a key is invalid, we won't know until we try to download
        # something, and it's easier to check that now
        with tempfile.NamedTemporaryFile() as fd:
            try:
                fxu.download(
                    cfg.connectionFile, cfg.firmwareBucket, fd.name, cfg.dephyProfile
                )
            except (
                bce.ClientError,
                bce.ProfileNotFound,
                bce.PartialCredentialsError,
                bce.EndpointConnectionError,
            ) as err:
                raise err
            except AssertionError as err:
                raise exceptions.S3DownloadError(
                    cfg.firmwareBucket, cfg.connectionFile, fd.name
                ) from err
            finally:
                fd.close()

        self.overwrite("Checking for access keys... <success>✓</success>\n")

    # -----
    # _check_tools
    # -----
    def _check_tools(self) -> None:
        """
        The bootloader requires tools from PSoC and STM in order to
        flash the microcontrollers. Here we make sure that those tools
        are installed. If they aren't, then we download and install
        them.

        S3 does not have a hierarchial structure like a normal file system.
        Instead, this behavior is mimicked with names that use /.

        Downloading "recursively" is only possible by looping over the
        `objects` of a `Bucket` object. Unfortunately, it does not appear
        to be possible to configure credential profiles in this way. To
        use credential profiles, a `Session` and `Client` object are
        needed.

        Such objects can "list" `objects`, but the response is a json
        packet whose structure is subject to change and needs to be
        manually parsed. As such, those tools that are directories are
        zipped into a single archive and then extracted once downloaded
        in order to avoid the "recursion" problem all together.

        Raises
        ------
        botocore.exceptions.EndpointConnectionError
            If we cannot connect to AWS.

        S3DownloadError
            If a tool fails to download.
        """
        _os = platform.system().lower()
        _bootloaderTools = cfg.bootloaderTools[_os]

        for tool in _bootloaderTools:
            self.write(f"Searching for: <info>{tool}</info>...")

            dest = cfg.toolsDir.joinpath(tool)

            if not dest.exists():
                self.line(f"\n\t<info>{tool}</info> <warning>not found.</warning>")

                self.write("\tDownloading...")

                try:
                    # boto3 requires dest be either IOBase or str
                    toolObj = str(Path(_os).joinpath(tool).as_posix())
                    fxu.download(toolObj, cfg.toolsBucket, str(dest), cfg.dephyProfile)
                except bce.EndpointConnectionError as err:
                    raise err
                except AssertionError as err:
                    raise exceptions.S3DownloadError(
                        cfg.toolsBucket, toolObj, str(dest)
                    ) from err

                if zipfile.is_zipfile(dest):
                    with zipfile.ZipFile(dest, "r") as archive:
                        base = dest.name.split(".")[0]
                        extractedDest = Path(os.path.dirname(dest)).joinpath(base)
                        archive.extractall(extractedDest)

                self.overwrite("\tDownloading... <success>✓</success>\n")

            else:
                msg = f"Searching for: <info>{tool}</info>...<success>✓</success>\n"
                self.overwrite(f"{msg}\n")
