from cleo.commands.command import Command


# ============================================
#                 BaseCommand
# ============================================
class BaseCommand(Command):

    # -----
    # constructor
    # -----
    def __init__(self) -> None:
        super().__init__()
        self._stylize()

    # -----
    # _styleize
    # -----
    def _stylize(self) -> None:
        self.add_style("info", fg="blue")
        self.add_style("warning", fg="yellow")
        self.add_style("error", fg="red")
        self.add_style("success", fg="green")

    # -----
    # handle
    # -----
    def handle(self) -> None:
        pass
