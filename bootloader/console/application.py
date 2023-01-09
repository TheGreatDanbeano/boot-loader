from typing import List

from cleo.application import Application
from cleo.commands.command import Command

from bootloader import __version__

from bootloader.commands.flash_microcontroller import FlashMicrocontrollerCommand
from bootloader.commands.init import InitCommand
from bootloader.commands.list import ListCommand


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
        super().__init__("bootload", __version__)

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
            FlashMicrocontrollerCommand,
            InitCommand,
            ListCommand,
        ]

        return commandList
