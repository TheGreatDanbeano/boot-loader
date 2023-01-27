from pathlib import Path
from typing import List

from botocore.client import BaseClient
from flexsea.utilities import download

from bootloader.utilities import config as cfg


# ============================================
#             get_s3_object_info
# ============================================
def get_s3_object_info(bucket: str) -> List[str] | dict:
    session = boto3.Session(profile_name=cfg.dephyProfile)
    client = session.client("s3")
    # The firmware and C libraries are in different buckets. The devices
    # and hardware can be obtained from the firmware bucket
    objs = get_s3_objects(bucket, client)
    client.close()

    if bucket == cfg.firmwareBucket:
        return self._parse_firmware_objects(objs)
    elif bucket == cfg.libsBucket:
        return self._parse_lib_objects(objs)
    else:
        raise ValueError("Unrecognized bucket.")


# ============================================
#                get_s3_objects
# ============================================
def get_s3_objects(bucket: str, client: BaseClient, prefix: str = "") -> List:
    """
    Recursively loops over all directories in a bucket and returns a
    list of files.

    Parameters
    ----------
    bucket : str
        The name of the bucket we're getting files from.

    client : botocore.client.BaseClient
        The object providing an interface to S3.

    prefix : str
        The directory we're looping over. If `""`, then we get the
        top-level directories.

    Returns
    -------
    List[str]
        A list of all the objects in the bucket.
    """
    objectList = []
    objects = client.list_objects_v2(Bucket=bucket, Delimiter="/", Prefix=prefix)

    if "CommonPrefixes" in objects:
        for pre in objects["CommonPrefixes"]:
            objectList += get_s3_objects(bucket, client, pre["Prefix"])

    if "Contents" in objects:
        return objectList + [obj["Key"] for obj in objects["Contents"][1:]]
    return objectList


# ============================================
#           _parse_firmware_objects
# ============================================
def _parse_firmware_objects(objects: List[str]) -> dict:
    """
    Converts the list of full-path firmware file names into a
    dictionary for easier display.

    Parameters
    ----------
    objects : List[str]
        List of full paths for firmware files from S3.

    Returns
    -------
    info : dict
        `objects` converted to a hierarchial dictionary form for
        cleaner display.
    """
    info = {}

    for obj in objects:
        version, device, hardware, _ = obj.split("/")
        if version not in info:
            info[version] = {
                hardware: set(
                    [
                        device,
                    ]
                )
            }
        else:
            if hardware not in info[version]:
                info[version][hardware] = set(
                    [
                        device,
                    ]
                )
            else:
                info[version][hardware].add(device)
    return info


# ============================================
#              _parse_lib_objects
# ============================================
def _parse_lib_objects(objects: List[str]) -> List[str]:
    libs = set()

    for obj in objects:
        lib = obj.split("/")[1]
        libs.add(lib)

    return sorted(list(libs))


# ============================================
#              get_remote_file
# ============================================
def get_remote_file(fName: str, bucket: str) -> None:
    """
    Searches the given aws bucket for the given file. 
    """
    fPath = Path(fName)
    # https://tinyurl.com/4scnuk6c
    session = boto3.Session(profile_name=cfg.dephyProfile)
    client = session.client("s3")
    paginator = client.get_paginator("list_objects_v2")
    pageIterator = paginator.paginate(Bucket=bucket)
    objects = pageIterator.search(f"Contents[?contains(Key, `{fPath.name}`)][]")
    # There should only be one match. If the match isn't the right file,
    # the hash check in download should catch it
    for item in objects:
        fileObj = item["Key"]
    download(fileObj, bucket, fName, cfg.dephyProfile)
