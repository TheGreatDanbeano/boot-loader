#!/usr/bin/env python

"""Dephy's firmware loading tool."""

import os
from pathlib import Path

import boto3
import yaml
from cleo import Application
from commands import ListFirmwareCmd
import bucket_utils as bu


def load_cfg(path):
    """Loads config form yaml file"""
    with open(path, "r") as file:
        return yaml.safe_load(file)


def init_dirs(paths):
    """Initializes directories for the app"""
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def download_utils(path, bucket):
    """Download """
    # Empty
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        os.remove(file_path)

    bu.download_dir(bucket, '/', path)

client = boto3.client('s3')

download_dir(client, 'bucket-name', 'path/to/data', 'downloads')

def main():
    """Main Bootloader app"""

    # Load Config
    cfg_path = "config.yaml"
    cfg = load_cfg(cfg_path)

    # Construct and init paths
    cfg["abs_paths"] = {}
    cfg["abs_paths"]["app"] = os.path.abspath(os.path.expanduser(cfg["app_dir"]))
    cfg["abs_paths"]["fw"] = os.path.join(cfg["abs_paths"]["app"], cfg["fw_dir"])
    cfg["abs_paths"]["utils"] = os.path.join(cfg["abs_paths"]["app"], cfg["utils_dir"])
    init_dirs(cfg["abs_paths"].values())

    download_utils(cfg["abs_paths"]["utils"])

    application = Application()
    application.add(ListFirmwareCmd(cfg))
    application.run()


if __name__ == "__main__":
    main()
