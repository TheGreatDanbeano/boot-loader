"""List firmware command"""

import datetime
import os

import bucket_utils as bu
from cleo import Command


class Cmd(Command):
    """docstring for Cmd"""

    def __init__(self, preferences):
        self._prefs = preferences
        super().__init__()

    @staticmethod
    def get_time() -> dict:
        return f"[{datetime.datetime.now().replace(microsecond=0).isoformat()}] "

    def info(self, val, print_time=False) -> None:
        time = self.get_time() if print_time else ""
        self.line(f"<info>{time}{val}</info>")

    def title(self, val) -> None:
        self.add_style("title", options=["bold"])
        self.line(f"<title>{val}</title>")

    def err(self, val, print_time=False) -> None:
        time = self.get_time() if print_time else ""
        self.line(f"<error>[e] {time}{val}</error>")

    def handle(self) -> int:
        """
        Executes the command.
        """
        raise NotImplementedError()


class ListFirmwareCmd(Cmd):
    """
    List available firmware

    list
        {path? : specify the firmware path}
    """

    def handle(self):
        """handle command"""
        path = self.argument("path")
        if not path:
            path = self._prefs["abs_paths"]["fw"]
        path = os.path.abspath(os.path.expanduser(path))

        try:
            # TODO(CA): Add more filtering to files in path
            firmware_list = os.listdir(path)

            self.title(f"Available Firmware at {path}:")
            for firmware in firmware_list:
                self.info(f"- {firmware}")
        except FileNotFoundError as err:
            self.err(f"Firmware path not found: {path}", print_time=True)
            self.err(f"{err}")
