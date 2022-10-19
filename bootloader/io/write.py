from typing import Callable

from bootloader.utilities.logo import dephyLogo
from bootloader.utilities.logo import dephyLogoPlainTxt


# ============================================
#                display_logo
# ============================================
def display_logo(print_function: Callable[[str], None]) -> None:
    """
    Uses the given `print_function` to display Dephy's logo to stdout.

    Parameters
    ----------
    print_function : Callable[[str], None]
        The function to use for displaying the logo.
    """
    try:
        print_function(dephyLogo)
    except UnicodeEncodeError:
        print_function(dephyLogoPlainTxt)
