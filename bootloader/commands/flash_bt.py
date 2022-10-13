from cleo import Command


# ============================================
#                FlashBtCommand
# ============================================
class FlashBtCommand(Command):
    """
    Used for flashing the bluetooth radio on a Dephy device.

    flash-bt
        {--level= : The bluetooth level to flash, e.g., `2`. Defaults to `2`.}
        {--p|port= : Name of the serial port to connect to, e.g., `/dev/ttyACM0`}
        {--a|address= : Bluetooth address of the device. If not given, we assume it's
            the same as the device id. If given, the device id is set to the same
            value.}
    """

    _level = None
    _device = None
    _port = None
    _address = None

    # -----
    # handle
    # -----
    def handle(self) -> None:
        """
        Entry point for the command.
        """
        self._level = int(self.option("level")) if self.option("level") else 2
        self._port = self.option("port") if self.option("port") else ""
        self._address = self.option("address")

        self.call("init")

        try:
            self._device = find_device(self._port)
        except DeviceNotFoundError as err:
            self.line(err)
            sys.exit(1)

        try:
            self._build_bt_image()
        except FileNotFoundError as err:
            msg = f"<error>Error: could not find file:</error>\n\t{err}"
            self.line(msg)
            sys.exit(1)
        except OSError as err:
            msg = f"<error>Error: command failed:</error>\n\t{err}"
            self.line(msg)
            sys.exit(1)

        try:
            self._flash()
        except OSError as err:
            msg = f"<error>Error: flashing failed:</error>\n\t{err}"
            self.line(err)
            sys.exit(1)

    # -----
    # _build_bt_image
    # -----
    def _build_bt_image(self) -> None:
        """
        Uses the bluetooth tools repo (downloaded as a part of `init`)
        to create a bluetooth image file with the correct address.
        """
        # Everything within the bt121 directory is self-contained and
        # self-referencing, so it's easiest to switch to that directory
        # first
        cwd = os.getcwd()
        os.chdir(os.path.join(toolsDir, "bt121_image_tools"))

        gattTemplate = os.path.join("gatt_files", f"{self._level}.xml")
        gattFile = os.path.join("dephy_gatt_broadcast_bt121", "gatt.xml")

        if not os.path.exists(gattTemplate):
            raise FileNotFoundError(gattTemplate)

        shutil.copyfile(gattTemplate, gattFile)

        proc = sub.Popen(["python3", "bt121_gatt_broadcast_img.py", f"{self._address}"])
        proc.wait()
        if proc.returncode == 1:
            raise OSError("bt121_gatt_broadcast_img.py")

        bgEXE = os.path.join("smart-ready-1.7.0-217", "bin", "bgbuild.exe")
        xmlFile = os.path.join("dephy_gatt_broadcast_bt121", "project.xml")
        proc = sub.Popen([bgExe, xmlFile])
        proc.wait()
        if proc.returncode == 1:
            raise OSError("bgbuild.exe")

        if os.path.exists("output"):
            files = glob.glob(os.path.join("output", "*.bin"))
            for file in files:
                os.remove(file)
        else:
            os.mkdir("output")

        btImageFile = f"dephy_gatt_broadcast_bt121_Exo-{self._address}.bin"
        shutil.move(os.path.join("dephy_gatt_broadcast_bt121", btImageFile), "output")
        btImageFile = os.path.join(os.getcwd(), "bt121_image_tools", "output", btImageFile)

        return btImageFile

    # -----
    # _flash
    # -----
    def _flash(self) -> None:
        set_tunnel_mode("BT121")
        cmd = [
            os.path.join(toolsDir, "stm32flash"),
            "-w",
            btImageFile,
            "-b",
            "115200",
            self._device.port
        ]
        proc = sub.Popen(cmd)
        proc.wait()
        if proc.returncode == 1:
            raise OSError(cmd)
