from time import sleep

from serial.tools.list_ports import comports
from flexsea.device import Device
import flexsea.fx_enums as fxe

from bootloader.exceptions.exceptions import DeviceNotFoundError


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
        except IOError as err:
            raise DeviceNotFoundError(port=port) from err
        device = _device

    if not device:
        raise DeviceNotFoundError()

    return device


# ============================================
#               set_tunnel_mode
# ============================================
def set_tunnel_mode(port: str, baudRate: int, target: str, timeout: int) -> bool:
    """
    Activate bootloader in target and wait until it's active.
    """
    # 6 is least verbose, 0 is most verbose
    debug_logging_level = 0
    result = False

    try:
        device = Device(port, baudRate)
    except OSError as err:
        raise OSError("Failed to load pre-compiled flexsea C libraries.") from err

    try:
        device.open(log_level=debug_logging_level)
    except IOError as err:
        raise RuntimeError(f"Failed to open device at {port}") from err

    app_type = device.app_type

    try:
        print(f"Your device is an {fxe.APP_NAMES[app_type.value]}", flush=True)
    except KeyError as err:
        raise RuntimeError(f"Unknown application type: {app_type.value}") from err

    wait_step = 1
    state = fxe.FX_FAILURE.value
    while timeout > 0 and state != fxe.FX_SUCCESS.value:
        if timeout % 5 == 0:
            try:
                device.activate_bootloader(target)
            except (IOError, ValueError):
                pass
        sleep(wait_step)
        timeout -= wait_step
        try:
            state = device.is_bootloader_activated()
        except ValueError as err:
            raise RuntimeError from err
        except IOError as err:
            pass

    if state == fxe.FX_SUCCESS.value:
        result = True

    try:
        device.close()
    except ValueError:
        pass

    return result
