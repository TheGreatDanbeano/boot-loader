from io import IOBase
from pathlib import Path
from typing import IO

import boto3
import botocore.exceptions as bce
from cleo import Command
from cleo.helpers import argument

from bootloader.exceptions import exceptions


# ============================================
#              DownloadCommand
# ============================================
class DownloadCommand(Command):
    name = "download"
    description = "Downloads a file from S3."
    arguments = [
        argument("obj", "The object to download from S3."),
        argument("bucket", "Bucket to download from."),
        argument("dest", "Location to save downloaded file."),
        argument("profile", "AWS credentials profile to use."),
    ]
    help = """Downloads the given file <info>obj</info> from the given
        bucket <info>bucket</info> to the given destination <info>dest</info>
        using the given credentials profile <info>profile</info>.

        Examples
        --------
        bootloader download stm32flash.exe dephy-bootloader-tools ./stflash dephy
        """

    # -----
    # handle
    # -----
    def handle(self) -> None:
        """
        Entry point for the command.
        """
        self._download(
            self.argument("obj"),
            self.option("bucket"),
            self.option("dest"),
            self.option("profile"),
        )

        return 0

    # -----
    # _download
    # -----
    def _download(
        self, fileobj: str, bucket: str, dest: str | IO, profile: str
    ) -> None:
        """
        Downloads `fileobj` from `bucket` to `dest` with the AWS
        credentials profile `profile`.

        Raises
        ------
        NoCredentialsError
            If no AWS credentials file is found

        NoProfileError
            If the given profile does not exist in the AWS credentials file.

        MissingKeyError
            If the given profile is missing one or more required keys.

        TypeError
            If the given dest is not a string or file-like object.
        """
        credentialsFile = Path.joinpath(Path.home(), ".aws", "credentials")

        if not Path.exists(credentialsFile):
            raise exceptions.NoCredentialsError

        try:
            session = boto3.Session(profile_name=profile)
        except bce.ProfileNotFound as err:
            raise exceptions.NoProfileError(profile) from err

        try:
            client = session.client("s3")
        except bce.PartialCredentialsError as err:
            raise exceptions.MissingKeyError from err

        if isinstance(dest, IOBase):
            client.download_fileobj(bucket, fileobj, dest)
        elif isinstance(dest, str):
            client.download_file(bucket, fileobj, dest)
        else:
            raise TypeError
