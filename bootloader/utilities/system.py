# ============================================
#                 find_device
# ============================================
def find_device(port: str) -> Device:
    """
    Tries to establish a connection to the Dephy device given by
    the user-supplied port. If no port is supplied, then we loop
    over all available serial ports to try and find a valid device.
    """
    device = None

    if not port:
        for _port in comports():
            _device = Device(_port, 230400)
            try:
                _device.open()
            except IOError:
                continue
            device = _device
            break

    else:
        _device = Device(port, 230400)
        try:
            _device.open()
        except IOError:
            raise DeviceNotFoundError(port=port)
        device = _device

    if not device:
        raise DeviceNotFoundError()

    return device
