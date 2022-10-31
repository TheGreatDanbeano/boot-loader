import os


# ============================================
#              Path Configuration
# ============================================

# Root directory of where to save bootloading tools and downloaded
# firmware
cacheDir = os.path.join(os.environ["HOME"], ".dephy", "bootloader")

# Directory to save bootloading tools
toolsDir = os.path.join(cacheDir, "tools")

# Directory to save firmware
firmwareDir = os.path.join(cacheDir, "firmware")


# ============================================
#              S3 Configuration
# ============================================

# Public bucket where bootloading tools are stored
toolsBucket = "https://dephy-bootloader-tools.s3.us-east-2.amazonaws.com/"

# Private bucket where the firmware is stored
firmwareBucket = "https://dephy-firmware.s3.us-east-2.amazonaws.com/"

# Credentials profile name
dephyProfile = "dephy"

# Dummy file to check AWS key authenticity
connectionFile = "connection_file.txt"

# AWS credentials file
credentialsFile = os.path.join(os.environ["HOME"], ".aws", "credentials")


# ============================================
#                Dependencies
# ============================================
bootloaderTools = [
    "psocbootloaderhost.exe",
    "bt121_image_tools",
    "DfuSeCommand.exe",
    "STMFlashLoader.exe",
    "stm32flash.exe",
    "XB24C",
]


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
