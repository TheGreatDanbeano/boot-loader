from typing import List

from botocore.client import BaseClient


def get_s3_objects(bucket: str, client: BaseClient, prefix: str="") -> List:
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

    return objectList + [obj["Key"] for obj in objects["Contents"][1:]]
