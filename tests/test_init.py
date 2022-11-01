from cleo import CommandTester

from bootloader.commands.init import InitCommand
from bootloader.core.application import BootloaderApplication


# ============================================
#                 test_cache
# ============================================
def test_cache() -> None:
    """
    Makes sure that the cache is set up correctly if it doesn't exist
    and that nothing is overwritten if it does.
    """
    app = BootloaderApplication()
    command = app.find("init")
    commandTester = CommandTester(command)
    # This call will fail because no device is actually connected, but
    # we're just interested in checking the cache
    commandTester.execute()

    # Case 1: No cache exists when command is called
    # Case 2: Cache exists when command is called
