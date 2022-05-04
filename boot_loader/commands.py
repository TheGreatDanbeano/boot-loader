"""List firmware command"""

from cleo import Command
import os
import datetime

class Cmd(Command):
    """docstring for Cmd"""

    @staticmethod
    def get_time():
        return f"[{datetime.datetime.now().replace(microsecond=0).isoformat()}] "

    def info(self, val, print_time=False):
        time = self.get_time() if print_time else ""
        self.line(f"<info>{time}{val}</info>")

    def title(self, val):
        self.add_style("title", options=["bold"])
        self.line(f"<title>{val}</title>")

    def err(self, val, print_time=False):
        time = self.get_time() if print_time else ""
        self.line(f"<error>{time}{val}</error>")



class ListFirmwareCmd(Cmd):
    """
    List available firmware

    list
        {path=~/.dephy/bootload/firmware : specify the firmware path}
    """

    def handle(self):
        """handle command"""
        path = self.argument("path")
        path = os.path.abspath(os.path.expanduser(path))

        try:

            firmware_list = [file for file in os.listdir(path) if os.path.isdir(file)]
            firmware_list = [file for file in os.listdir(path)]

            self.title(f"Available Firmware at {path}")
            for firmware in firmware_list:
                self.info(f"- {firmware}")
        except FileNotFoundError as err:
            self.err(f"Firmware path not found: {path}", print_time=True)
            self.err(f"{err}")
