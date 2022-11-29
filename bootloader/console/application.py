from typing import List

from cleo import Application
from cleo import Command
from cleo.config import ApplicationConfig as BaseApplicationConfig
from clikit.api.formatter import Style

from bootloader import __version__
from bootloader.commands.configure_bt import ConfigureBT121Command
from bootloader.commands.configure_xbee import ConfigureXbeeCommand
from bootloader.commands.flash import FlashCommand
from bootloader.commands.init import InitCommand


# ============================================
#              ApplicationConfig
# ============================================
class ApplicationConfig(BaseApplicationConfig):
    """
    Controls the configuration and styling of the CLI object.
    """

    # -----
    # configure
    # -----
    def configure(self) -> None:
        """
        Sets the color of various message types.
        """
        super().configure()

        self.add_style(Style("info").fg("cyan"))
        self.add_style(Style("error").fg("red").bold())
        self.add_style(Style("warning").fg("yellow").bold())
        self.add_style(Style("success").fg("green"))


# ============================================
#           BootloaderApplication
# ============================================
class BootloaderApplication(Application):
    """
    The CLI object.
    """

    # -----
    # constructor
    # -----
    def __init__(self) -> None:
        super().__init__(config=ApplicationConfig("bootloader", __version__))

        for command in self._get_commands():
            self.add(command())

    # -----
    # _get_commands
    # -----
    def _get_commands(self) -> List[Command]:
        """
        Helper method for telling the CLI about the commands available to
        it.

        Returns
        -------
        commandList : List[Command]
            A list of commands available to the CLI.
        """
        commandList = [
            ConfigureBT121Command,
            ConfigureXbeeCommand,
            FlashCommand,
            InitCommand,
        ]

        return commandList