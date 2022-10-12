from .application import BootloaderApplication


# ============================================
#                    main
# ============================================
def main() -> None:
    """
    Entry point. Creates an instance of the command-line interface
    (CLI) object and runs it.
    """
    BootloaderApplication().run()
