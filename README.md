# Dephy Bootloader

This is a tool for loading firmware onto Dephy's devices.

## AWS Keys

Contact the software team lead (Carlos Asmat: casmat@dephy.com) and request access to AWS. This is
where the device version python libraries are stored and can only be accessed via the secure keys.
Once you receive your keys, create a folder in the home directory (~) called .aws and create a file
within this directory called credentials. Edit the credentials file to contain the following:

```bash
[default]
aws_access_key_id=<YOUR ACCES KEY ID HERE>
aws_secret_access_key=<YOUR SECRET ACCESS KEY HERE>

[dephy]
aws_access_key_id=<YOUR ACCES KEY ID HERE>
aws_secret_access_key=<YOUR SECRET ACCESS KEY HERE>
```

## Installation

It is **highly recommended**, but not required, that you install `flexsea` in a virtual
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

This package provides the `bootload` command-line tool. To see the available commands,
simply run `bootload --help`. Additionally, each subcommand has a `--help` option
that will give you more information on its usage.

The main commands of interest are:  `microcontroller`, `bt121`, `xbee`, and `list`.

### Microcontroller

The `microcontroller` command is used for updating the firmware on Manage, Execute,
Regulate, and Habsolute. The usage pattern is:

```bash
bootload microcontroller <target> [options]
```

`target` is the microcontroller you want to bootload. It can be:
    * `mn`
    * `ex`
    * `re`
    * `habs`

The available options are:
    * `--from` : The semantic version string of the firmware currently on the device. This is not required for devices running version "10.0.0" or higher. If not given, but needed, the bootloader will prompt you for this information.
    * `--to` : The semantic version string of the firmware you'd like to bootload onto the device. If not given, the bootloader will prompt you to enter this information.
    * `--hardware` : The version of the device's rigid board. This is not needed for devices running version "10.0.0" or higher. If not given, but needed, the bootloader will prompt you for this information.
    * `--port` : The name of the serial port the device is connected to, e.g., "COM3" or "/dev/ttyACM0". If this is not given, the bootloader will attempt to find the device automatically.
    * `--file` : If you'd like to manually specify the firmware file to bootload, this is the option for you. If the file is not found locally in the `~/.dephy/bootloader/firmware` directory, then the `dephy-firmware` bucket on S3 will be searched and the file downloaded, if found.
    * `--device` : The name of the device being bootloaded, e.g., "actpack" or "eb60". This is not needed if the device is running version "10.0.0" or higher. If not given, but needed, the bootloader will prompt you for this information.
    * `--side` : When bootloading "Mn" for a device with chirality, this allows you to specify either "left" or "right". This is not needed if the device is running version "10.0.0" or higher. If not given, but needed, the bootloader will prompt you for this information.
    * `--baudRate` : Allows you to specify the baud rate used for communicating with the device. This is only needed if the required baud rate is different than the default value of `230400`.

The bootloader will check to make sure that you have all of the required tools needed to update the firmware. If you do not, then it will download them for you.

#### Examples
The goal is to have the command "read" fluidly. To that end, in order to bootload Regulate on an actpack from version 7.2.0 to version 9.1.0, we would do

```bash
bootload microcontroller re --from 7.2.0 --to 9.1.0 --hardware 4.1B --device actpack
```


### List

The `list` command is used to display information about what firmware is available to be bootloaded. The usage is:

```bash
bootload list [options]
```

The available options are:
    * `--devices` : Displays the types of devices that can be bootloaded
    * `--hardware` : Displays the rigid board versions that can be bootloaded
    * `--versions` : Displays the firmware versions available to be bootloaded

If no options are given, then the available devices, hardware, and versions are all shown.
