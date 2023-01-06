from typing import Self

from cleo.commands.command import Command


# ============================================
#                BaseCommand
# ============================================
class BaseCommand(Command):

    _pad: str = "    "

    # -----
    # setup
    # -----
    def setup(self: Self) -> None:
        self._stylize()
        self.call(
            [
                "init",
            ]
        )

    # -----
    # _styleize
    # -----
    def _stylize(self: Self) -> None:
        self.add_style("info", fg="blue")
        self.add_style("warning", fg="yellow")
        self.add_style("error", fg="red")
        self.add_style("success", fg="green")

    # -----
    # handle
    # -----
    def handle(self) -> None:
        raise NotImplementedError
