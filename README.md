# Bootloader

This is a tool for loading firmware onto Dephy's devices.


## Installation

It is highly recommended, but not required, that you install `flexsea` in a virtual
environment. This helps keep your python and associated packages sandboxed from the
rest of your system and, potentially, other versions of the same packages required by
`flexsea`.

You can create a virtual environment via (these commands are for Linux. See the **NOTE**
below for Windows):

```bash
mkdir ~/.venvs
python3 -m venv ~/.venvs/dephy
```

Activate the virtual environment with:

```bash
source ~/.venvs/dephy/bin/activate
```

**NOTE**: If you're on Windows, the activation command is: `source ~/.venvs/dephy/Scripts/activate`.
Additionally, replace `python3` with `python`.


### From Source

To install from source:

```bash
git clone https://github.com/DephyInc/boot-loader.git
cd boot-loader/
git checkout main # Or whichever branch you're interested in
python3 -m pip install .
```


### From PyPI

```bash
python3 -m pip install dephy-bootloader
```


## Usage

This package provides the `bootloader` command-line tool. To see the available commands,
simply run `bootloader --help`. Additionally, each subcommand has a `--help` option
that will give you more information on its usage.

The three main commands of interest are: `flash`, `configure-bt`, and `configure-xbee`.

### Flash

The `flash` command is used for updating the firmware on Manage, Execute, Regulate, and
Habsolute. The usage pattern is:

```bash
bootloader flash <target> <from> <to> [--port|-p=<port name>]
```

The CLI will first check to make sure that you have all of the required tools needed
to update the firmware. If you do not, then it will download them for you.

`target` is the microcontroller you want to flash. It can be:
    * `mn`
    * `ex`
    * `re`
    * `habs`
    * `all`

If `all` is selected, the command will flash `mn`, `ex`, `re`, and `habs`, if applicable.

`from` is the semantic version string of the firmware that is currently on the target,
e.g., `7.2.0`. The reason this is needed is so that the correct version of the
pre-compiled C++ libraries used for communicating with the device can be downloaded
and used.

`to` is the semantic version string of the firmware you'd like to flash onto the
microcontroller, e.g., `9.1.0`.

If the `to` and/or `from` versions of the firmware are not cached on your machine, then
they will be downloaded for you.

The `--port` option is used for manually specifiy the name of the COM port the device
is connected to, e.g., `COM3` or `/dev/ttyACM0`. If this is not given, then the command
will automatically look for a valid Dephy device and use the first one that it finds.


### Configure-bt

This command is used for updating the bt121 radio. Its usage is:

```bash
bootloader configure-bt <level> <address> <from> [--port|-p]
```

`level` specifies the Bluetooth gatt file level to use, e.g., `2`.

`address` is the Bluetooth address of the device.

`from` is the semantic version string of the firmware currently on Manage. This is
necessary because the communication to the bt121 radio goes through manage. If this
firmware isn't on your computer, it will be downloaded for you.

The `--port` option is used for manually specifiy the name of the COM port the device
is connected to, e.g., `COM3` or `/dev/ttyACM0`. If this is not given, then the command
will automatically look for a valid Dephy device and use the first one that it finds.


### Configure-xbee

This command configures the xbee radio on the device. Its usage is:

```bash
bootloader configure-xbee <address> <buddy address> <from> [--port|-p]
```

`address` is the Bluetooth address of the device being configured.

`buddy address` is the Bluetooth address of the device's companion.

`from` is the semantic version string of the firmware currently on Manage. This is
necessary because the communication to the bt121 radio goes through manage. If this
firmware isn't on your computer, it will be downloaded for you.

The `--port` option is used for manually specifiy the name of the COM port the device
is connected to, e.g., `COM3` or `/dev/ttyACM0`. If this is not given, then the command
will automatically look for a valid Dephy device and use the first one that it finds.
