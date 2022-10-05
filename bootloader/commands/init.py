import os
import platform
import shutil
import subprocess as sub
import sys
from typing import List

from cleo import Command
from rsyncs3 import RsyncS3

from bootloader.utilities.config import dependencies
from bootloader.utilities.config import firmwareDir
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

            * Checks to make sure we're on Windows because PSoC
              doesn't work on Linux

            * Creates the cache directory, if needed

            * Checks to make sure the STM32 and PSoC tools are
              installed. If not, attempts to download and install them

            * Checks for S3 access keys in the environment

        Parameters
        ----------
        None

        Raises
        ------
        None

        Returns
        -------
        None
        """
        self._check_os()
        self._setup_cache()
        toInstall = self._check_tools()
        self._install_tools(toInstall)
        self._check_keys()

    # -----
    # _check_os
    # -----
    def _check_os(self) -> None:
        """
        Makes sure we're running on Windows because PSoC's tools don't
        work on Linux.

        Parameters
        ----------
        None

        Raises
        ------
        None

        Returns
        -------
        None
        """
        self.write("<info>Checking OS...</info>")

        try:
            assert "win" in platform.system().lower()
        except AssertionError:
            msg = "\n\t<error>Invalid OS!</error>"
            msg += "\n\tThis tool requires <warning>Windows</warning>."
            self.line(msg)
            sys.exit(1)

        self.overwrite("<info>Checking OS</info> <success>✓</success>\n")
    
    # -----
    # _setup_cache
    # -----
    def _setup_cache(self) -> None:
        """
        Creates the directories where the firmware files and bootloader
        tools are downloaded and saved to, if necessary.

        Parameters
        ----------
        None

        Raises
        ------
        None

        Returns
        -------
        None
        """
        self.write("<info>Setting up cache...</info>")

        os.makedirs(firmwareDir, exist_ok=True)
        os.makedirs(toolsDir, exist_ok=True)

        self.overwrite("<info>Setting up cache</info> <success>✓</success>\n")

    # -----
    # _check_tools
    # -----
    def _check_tools(self) -> List[str]:
        """
        The bootloader requires tools from PSoC and STM in order to
        flash the microcontrollers. Here we make sure that those tools
        are installed. If they aren't, then we download and install
        them.

        Parameters
        ----------
        None

        Raises
        ------
        None

        Returns
        -------
        toInstall : List[str]
            A list of dependencies that had to be downloaded and,
            therefore, need to be installed.
        """
        toInstall = []

        for tool in dependencies:
            self.write(f"Searching for: <warning>{tool}</warning>...")

            if shutil.which(tool) is None:
                self.line(f"\tTool: {tool} not found.")
                tool = os.path.join(toolsDir, tool)

                self.write("\tDownloading...")

                with RsyncS3(toolsBucket, os.path.basename(tool), toolsDir) as rs:
                    rs.sync()
                toInstall.append(tool)

                self.overwrite("\tDownloading <success>✓</success>\n")

            else:
                msg = f"<warning>{tool}</warning> <success>✓</success>\n"
                self.overwrite(f"{msg}\n")

        return toInstall

    # -----
    # _install_tools
    # -----
    def _install_tools(toInstall: List[str]) -> None:
        """
        Takes in a list of dependencies that had to be downloaded and
        installs them.

        The rationale for if-else approach is that some .exe files
        do not need to be executed and others do. Also, the bluetooth
        zip needs to be unzipped and nothing else, but if other zip
        archives are added in the future then they might be more
        involved to process.

        Parameters
        ----------
        toInstall : List[str]
            List of dependency names that have to be installed.

        Raises
        ------
        None

        Returns
        -------
        None
        """
        for dependency in toInstall:
            self.write(f"<info>Installing {dependency}...</info>")

            if "psocbootloaderhost" in dependency or "stm32flash" in dependency:
                if toolsDir not in os.environ["PATH"]:
                    # Add the tools director to the current shell session
                    p = sub.Popen(["export", f"{os.environ["PATH"]}=$PATH:{toolsDir}"])
                    p.wait()

                    # Add the tools directory to the path permanently
                    shell = os.path.basename(os.environ["SHELL"])
                    profile = os.path.join(os.environ["HOME"], f".{shell}rc")

                    with open(profile, "a") as fd:
                        fd.write(f"\nexport PATH=$PATH:{toolsDir}")

            elif "bt121_image_tools-master.zip" in dependency:
                p = sub.Popen(["unzip", dependency, toolsDir])
                p.wait()

                # Add the tools director to the current shell session
                btPath = os.path.join(toolsDir, dependency.split(".")[0])
                p = sub.Popen(["export", f"{os.environ["PATH"]}=$PATH:{btPath}"])
                p.wait()

                # Add the tools directory to the path permanently
                shell = os.path.basename(os.environ["SHELL"])
                profile = os.path.join(os.environ["HOME"], f".{shell}rc")

                with open(profile, "a") as fd:
                    fd.write(f"\nexport PATH=$PATH:{btPath}")

            elif "DfuSe" in dependency or "flash_loader_demo" in dependency:
                p = sub.Popen([dependency])
                p.wait()

            msg = f"<info>Installing {dependency}</info> <success>✓</success>\n"
            self.overwrite(f"{msg}\n")

    # -----
    # _check_keys
    # -----
    def _check_keys(self) -> None:
        """
        Access to Dephy's firmware bucket on S3 requires a public and a
        prive access key, so here we make sure that those are saved in
        the user's environment.

        Parameters
        ----------
        None

        Raises
        ------
        None

        Returns
        -------
        None
        """
        self.write("<info>Checking for access keys...</info>")

        try:
            publicKey = os.environ["DEPHY_PUBLIC_KEY"]
            secretKey = os.environ["DEPHY_SECRET_KEY"]
        except KeyError:
            msg = "\t<error>Access keys not found!</error>:\n"
            msg += "\tPlease save your keys in the following environment variables:\n"
            msg += "\t\tpublic key : `<info>DEPHY_PUBLIC_KEY</info>`\n"
            msg += "\t\tsecret key : `<info>DEPHY_SECRET_KEY</info>`\n\n"
            self.line("")
            self.line(msg)
            sys.exit(1)

        self.overwrite("<info>Checking for access keys</info> <success>✓</success>\n")
