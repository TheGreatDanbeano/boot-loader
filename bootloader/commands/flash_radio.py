from cleo import Command


# ============================================
#              FlashRadioCommand
# ============================================
class FlashRadioCommand(Command):
    """
    Used for flashing the radios on a Dephy device.

    flash-radio
        {target : The radio to flash. Can be: `bt121` or `xbee`.}
    """
