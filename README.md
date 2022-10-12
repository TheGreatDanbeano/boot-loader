# Bootloader

This is a tool for loading firmware onto Dephy's devices.


# Questions for Carlos

* Why do we not need to call start_streaming before getting the app_type?
  * It's part of the connection message when calling fxOpen

* Do we need to start streaming before getting rigid and firmware versions?
  * No

* Should we call start_streaming in open in order to get this info, then close
after getting it?
  * Don't need to

* Why are there two get_firmware functions? What is the difference between them?
  * One sends request to device, the other reads it

* Why is the firmware version not in the __fields__? (in dev_spec)
  * Doesn't need to be

* What happens if we call Device(port, baudRate) and port is NOT a dephy device? Like, a usb stick or something? No return code will be obtained, right, since the device doesn't know our communication protocol? Or does it generically send an error code in such a case? This is for when I'm looping over all of the available serial ports and trying to open them to determine which ports belong to valid dephy devices
  * Time out? Exception? Need to check
