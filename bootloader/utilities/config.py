from pathlib import Path


# ============================================
#              Path Configuration
# ============================================

# Root directory of where to save bootloading tools and downloaded
# firmware
cacheDir = Path.joinpath(Path.home(), ".dephy", "bootloader")

# Directory to save bootloading tools
toolsDir = cacheDir.joinpath("tools")

# Directory to save firmware
firmwareDir = cacheDir.joinpath("firmware")


# ============================================
#              S3 Configuration
# ============================================

# Public bucket where bootloading tools are stored
toolsBucket = "dephy-bootloader-tools"

# Private bucket where the firmware is stored
firmwareBucket = "dephy-firmware"

# Credentials profile name
dephyProfile = "dephy"

# Dummy file to check AWS key authenticity
connectionFile = "connection_file.txt"

# AWS credentials file
credentialsFile = Path.joinpath(Path.home(), ".aws", "credentials")


# ============================================
#                Dependencies
# ============================================
bootloaderTools = {
    "windows": [
        "psocbootloaderhost.exe",
        "bt121_image_tools",
        "DfuSeCommand.exe",
        "STMFlashLoader.exe",
        "stm32flash.exe",
        "XB24C",
    ]
}


# ============================================
#                  Targets
# ============================================
mcuTargets = [
    "habs",
    "ex",
    "re",
    "mn",
]

availableTargets = ["all", "bt", "xbee"] + mcuTargets

fwExtensions = {"habs": "hex", "ex": "cyacd", "re": "cyacd", "mn": "dfu"}


# ============================================
#                 Constants
# ============================================
baudRate = 230400
supportedOS = [
    "windows",
]
