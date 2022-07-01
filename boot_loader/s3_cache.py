"""Cache S3 buckets to local storage.
Based on this issue : https://github.com/boto/boto/issues/3343
"""


import copy
import hashlib
import logging
import multiprocessing
import os
import shutil
import tempfile
from functools import partial

import boto3 as boto

log = logging.getLogger(__name__)


class S3Cache:
    """Provides a local cache of an S3 bucket on disk,
    with the ability to sync up to the latest version of all files.
    """

    _DEFAULT_PATH = os.path.join(tempfile.gettempdir(), __name__)

    def __init__(self, bucket_name, prefix="", path=None):
        """Init Method

        :param bucket_name: str, the name of the S3 bucket
        :param prefix: str, the prefix up to which you want to sync
        :param path: (optional, str) a path to store the local files
        """
        self.bucket_name = bucket_name
        self.prefix = prefix

        if not path:
            path = os.path.join(self._DEFAULT_PATH, self.bucket_name)

        self.path = path
        os.makedirs(path, exist_ok=True)

        s3_resource = boto.resource("s3")
        self.bucket = s3_resource.Bucket(self.bucket_name)

    def __enter__(self):
        """Provides a context manager which will open but not sync, then delete the cache on exit"""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Provides a context manager which will open but not sync, then delete the cache on exit"""
        self.close()

    def __getstate__(self):
        """Pickle and un-pickle the self object between multiprocessing pools"""
        out = copy.copy(self.__dict__)
        out["bucket"] = None
        return out

    def __setstate__(self, state_dict):
        """Pickle and un-pickle the self object between multiprocessing pools"""
        s3_resource = boto.resource("s3")
        state_dict["bucket"] = s3_resource.Bucket(state_dict["bucket_name"])
        self.__dict__ = state_dict

    def get_path(self, key):
        """Returns the local file storage path for a given file key"""
        return os.path.join(self.path, self.prefix, key)

    def calculate_s3_etag(self, file, key, tag):
        """Calculates the S3 custom e-tag (a specially formatted MD5 hash)"""
        md5s = []

        chunk_count = 0
        while True:
            data = file.read(self._get_chunk_size(key, tag, chunk_count))
            chunk_count += 1
            if data:
                md5s.append(hashlib.md5(data))
            else:
                break

        if len(md5s) == 1:
            return '"{}"'.format(md5s[0].hexdigest())

        digests = b"".join(m.digest() for m in md5s)
        digests_md5 = hashlib.md5(digests)
        return '"{}-{}"'.format(digests_md5.hexdigest(), len(md5s))

    def _get_obj(self, key, tag):
        """Downloads an object at key to file path.
        Checks to see if an existing file matches the current hash
        """
        path = os.path.join(self.path, key)
        print(f"Getting {path}")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        is_file = path[-1] != "/"
        if is_file:
            should_download = True
            try:
                with open(path, "rb") as file:
                    computed_tag = self.calculate_s3_etag(file, key, tag)
                    if tag == computed_tag:
                        print("Cache Hit")
                        should_download = False
                    else:
                        print(f"Cache Miss {tag} :: {computed_tag}")
            except FileNotFoundError:
                pass

            if should_download:
                self.bucket.download_file(key, path)

    def _get_chunk_size(self, key, tag, chunk=0):
        try:
            parts = tag.split("-")[1]
        except IndexError:
            parts = 0
        if parts:
            client = boto.client(service_name='s3', use_ssl=True)

            response = client.head_object(
                Bucket=self.bucket_name,
                Key=key,
                PartNumber=chunk
            )
            return int(response["ContentLength"])

        return 8 * 1024 *1024

    def sync(self):
        """Syncs the local and remote S3 copies"""
        with multiprocessing.Pool(1) as pool:
            keys = [
                (obj.key, obj.e_tag)
                for obj in self.bucket.objects.filter(Prefix=self.prefix)
            ]
            pool.starmap(self._get_obj, keys)

    def close(self):
        """Deletes all local files"""
        shutil.rmtree(self.path)
