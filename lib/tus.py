from __future__ import print_function
import os
import base64
import logging
import argparse

import requests

LOG_LEVEL = logging.INFO
DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024
TUS_VERSION = '1.0.0'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())


class TusError(Exception):
    pass


def _init():
    fmt = "[%(asctime)s] %(levelname)s %(message)s"
    h = logging.StreamHandler()
    h.setLevel(LOG_LEVEL)
    h.setFormatter(logging.Formatter(fmt))
    logger.addHandler(h)


class DictAction(argparse.Action):
    def __init__(self, option_strings, dest, **kwargs):
        super(DictAction, self).__init__(
            option_strings, dest, nargs=2, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        key, value = values[0], values[1]
        d = getattr(namespace, self.dest)
        if d is None:
            setattr(namespace, self.dest, {})
        d = getattr(namespace, self.dest)
        d[key] = value


def _create_parent_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=argparse.FileType('rb'))
    parser.add_argument('--chunk-size', type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument(
        '--header',
        dest='headers',
        action=DictAction,
        help="A single key/value pair as 2 arguments"
        " to be sent as HTTP header."
        " Can be specified multiple times to send multiple headers.")
    return parser


def _cmd_upload():
    _init()

    parser = _create_parent_parser()
    parser.add_argument('tus_endpoint')
    parser.add_argument(
        '--file_name',
        help="Override uploaded file name."
        "Inferred from local file name if not specified.")
    parser.add_argument(
        '--metadata',
        action=DictAction,
        help="A single key/value pair as 2 arguments"
        " to be sent in Upload-Metadata header."
        " Can be specified multiple times to send more than one pair.")
    args = parser.parse_args()

    file_name = args.file_name or os.path.basename(args.file.name)
    file_size = _get_file_size(args.file)

    file_endpoint = create(
        args.tus_endpoint,
        file_name,
        file_size,
        headers=args.headers,
        metadata=args.metadata)

    print(file_endpoint)

    resume(
        args.file,
        file_endpoint,
        chunk_size=args.chunk_size,
        headers=args.headers,
        offset=0)


def _cmd_resume():
    _init()

    parser = _create_parent_parser()
    parser.add_argument('file_endpoint')
    args = parser.parse_args()

    resume(
        args.file,
        args.file_endpoint,
        chunk_size=args.chunk_size,
        headers=args.headers)


def upload(file_obj,
           tus_endpoint,
           chunk_size=DEFAULT_CHUNK_SIZE,
           file_name=None,
           headers=None,
           metadata=None):

    file_name = file_name or os.path.basename(file_obj.name)
    file_size = _get_file_size(file_obj)

    file_endpoint = create(
        tus_endpoint,
        file_name,
        file_size,
        headers=headers,
        metadata=metadata)

    resume(
        file_obj,
        file_endpoint,
        chunk_size=chunk_size,
        headers=headers,
        offset=0)


def _get_file_size(f):
    pos = f.tell()
    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.seek(pos)
    return size


def create(tus_endpoint, file_name, file_size, headers=None, metadata=None):
    logger.info("Creating file endpoint")

    h = {
        "Tus-Resumable": TUS_VERSION,
        "Upload-Length": str(file_size),
    }

    if headers:
        h.update(headers)

    if metadata:
        pairs = [
            k + ' ' + base64.b64encode(v.encode('utf-8')).decode()
            for k, v in metadata.items()
        ]
        h["Upload-Metadata"] = ','.join(pairs)

    response = requests.post(tus_endpoint, headers=h)
    if response.status_code != 201:
        raise TusError("Create failed: %s" % response)

    location = response.headers["Location"]
    logger.info("Created: %s", location)
    return location


def resume(file_obj,
           file_endpoint,
           chunk_size=DEFAULT_CHUNK_SIZE,
           headers=None,
           offset=None):

    if offset is None:
        offset = _get_offset(file_endpoint, headers=headers)

    total_sent = 0
    file_size = _get_file_size(file_obj)
    while offset < file_size:
        file_obj.seek(offset)
        data = file_obj.read(chunk_size)
        offset = _upload_chunk(data, offset, file_endpoint, headers=headers)
        total_sent += len(data)
        logger.info("Total bytes sent: %i", total_sent)


def _get_offset(file_endpoint, headers=None):
    logger.info("Getting offset")

    h = {"Tus-Resumable": TUS_VERSION}

    if headers:
        h.update(headers)

    response = requests.head(file_endpoint, headers=h)
    response.raise_for_status()

    offset = int(response.headers["Upload-Offset"])
    logger.info("offset=%i", offset)
    return offset


def _upload_chunk(data, offset, file_endpoint, headers=None):
    logger.info("Uploading %d bytes chunk from offset: %i", len(data), offset)

    h = {
        'Content-Type': 'application/offset+octet-stream',
        'Upload-Offset': str(offset),
        'Tus-Resumable': TUS_VERSION,
    }

    if headers:
        h.update(headers)

    response = requests.patch(file_endpoint, headers=h, data=data)
    if response.status_code != 204:
        raise TusError("Upload chunk failed: %s" % response)

    return int(response.headers["Upload-Offset"])
