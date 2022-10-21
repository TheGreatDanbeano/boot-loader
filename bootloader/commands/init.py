import os
import platform
import sys
import tempfile

import boto3
import botocore.exceptions as bce
from cleo import Command

from bootloader.exceptions import exceptions
from bootloader.utilities import config as cfg
from bootloader.utilities.logo import dephyLogo
from bootloader.utilities.logo import dephyLogoPlain
from bootloader.utilities.system import endrun


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
        Entry point for the command.
        """
        try:
            self.line(dephyLogo)
        except UnicodeEncodeError:
            self.line(dephyLogoPlain)

        self.line("Welcome to the Dephy bootloader!")

        msg = "<warning>Please make sure the battery is removed![y|n]</warning>"
        if not self.confirm(msg, False):
            sys.exit(1)

        try:
            self._check_os()
        except exceptions.UnsupportedOSError as err:
            endrun(err, self.line)

        self._setup_cache()

        try:
            self._check_tools()
        except (exceptions.NetworkError, exceptions.S3DownloadError) as err:
            endrun(err, self.line)

        try:
            self._check_keys()
        except (
            exceptions.NoCredentialsError,
            exceptions.NoProfileError,
            exceptions.MissingKeyError,
            exceptions.InvalidKeyError,
            exceptions.NetworkError,
        ) as err:
            endrun(err, self.line)

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

        os.makedirs(cfg.firmwareDir, exist_ok=True)
        os.makedirs(cfg.toolsDir, exist_ok=True)

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
        NetworkError
            If we cannot connect to AWS.

        S3DownloadError
            If a tool fails to download.
        """
        s3 = boto3.resource("s3")
        bucket = s3.Bucket(cfg.toolsBucket)

        for tool in cfg.bootloaderTools:
            self.write(f"Searching for: <info>{tool}</info>...")

            if not os.path.exists(os.path.join(cfg.toolsDir, tool)):
                self.line(f"\n\t<info>{tool}</info> <warning>not found.</warning>")

                self.write("\tDownloading...")

                try:
                    bucket.download_file(tool, os.path.join(cfg.toolsDir, tool))
                except bce.EndpointConnectionError as err:
                    raise exceptions.NetworkError from err

                if not os.path.exists(os.path.join(cfg.toolsDir, tool)):
                    raise exceptions.S3DownloadError(
                        cfg.toolsBucket, tool, cfg.toolsDir
                    )

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

        if not os.path.exists(cfg.credentialsFile):
            raise exceptions.NoCredentialsError

        try:
            session = boto3.Session(profile_name=cfg.dephyProfile)
        except bce.ProfileNotFound as err:
            raise exceptions.NoProfileError from err

        try:
            client = session.client("s3")
        except bce.PartialCredentialsError as err:
            raise exceptions.MissingKeyError from err

        # If a key is invalid, we won't know until we try to download
        # something, and it's easier to check that now
        with tempfile.TemporaryFile() as fd:
            try:
                client.download_fileobj(cfg.firmwareBucket, cfg.connectionFile, fd)
            except bce.ClientError as err:
                raise exceptions.InvalidKeyError from err
            except bce.EndpointConnectionError as err:
                raise exceptions.NetworkError from err
            finally:
                fd.close()

        self.overwrite("<info>Checking for access keys</info> <success>✓</success>\n")
