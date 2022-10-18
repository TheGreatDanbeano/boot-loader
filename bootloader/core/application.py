from typing import List

from cleo import Application
from cleo import Command
from cleo.config import ApplicationConfig as BaseApplicationConfig
from clikit.api.formatter import Style


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
        super().__init__(config=ApplicationConfig())
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
        commandList = []

        return commandList