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
toolsBucket = "https://bootloader-tools-dephy-com.s3.us-east-2.amazonaws.com/"
firmwareBucket = "https://dephy-firmware.s3.us-east-2.amazonaws.com/"


# ============================================
#                Dependencies
# ============================================
bootloaderTools = [
    "psocbootloaderhost.exe",
    "bt121_image_tools-master.zip",
    "DfuSe_Demo_V3.0.6_Setup.exe",
    "flash_loader_demo_v2.8.0.exe",
    "stm32flash.exe",
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


# ============================================
#                 Constants
# ============================================
baudRate = 230400
supportedOS = [
    "windows",
]
