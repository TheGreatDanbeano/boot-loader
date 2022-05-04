"""List firmware command"""

from cleo import Command


class ListFwCommand(Command):
    """
    List available firmware

    list
        {path=~/.dephy/bootload/firmware : specify the firmware path}
    """

    def handle(self):
        """handle command"""
        path = self.argument('path')

        if path:
            text = 'Hello {}'.format(path)

        self.line(text)
