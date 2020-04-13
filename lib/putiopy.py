# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
import os
import io
import json
import logging
import binascii
import webbrowser
import pkg_resources
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode
from datetime import datetime

import tus
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

__version__ = pkg_resources.get_distribution('putio.py').version

KB = 1024
MB = 1024 * KB

# Read and write operations are limited to this chunk size.
# This can make a big difference when dealing with large files.
CHUNK_SIZE = 256 * KB

BASE_URL = None
UPLOAD_URL = None
TUS_UPLOAD_URL = None
ACCESS_TOKEN_URL = None
AUTHENTICATION_URL = None
AUTHORIZATION_URL = None

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def _set_domain(domain='put.io', scheme='https'):
    global BASE_URL
    global UPLOAD_URL
    global TUS_UPLOAD_URL
    global ACCESS_TOKEN_URL
    global AUTHENTICATION_URL
    global AUTHORIZATION_URL

    api_base = '{scheme}://api.{domain}/v2'.format(scheme=scheme, domain=domain)
    upload_base = '{scheme}://upload.{domain}'.format(scheme=scheme, domain=domain)

    BASE_URL = api_base
    UPLOAD_URL = upload_base + '/v2/files/upload'
    TUS_UPLOAD_URL = upload_base + '/files/'
    ACCESS_TOKEN_URL = api_base + '/oauth2/access_token'
    AUTHENTICATION_URL = api_base + '/oauth2/authenticate'
    AUTHORIZATION_URL = api_base + '/oauth2/authorizations/clients/{client_id}/{fingerprint}'


_set_domain()


class APIError(Exception):
    """
    Must be created with following arguments:
        1. Response instance (requests.Response)
        2. Type of the error (str)
        3. Extra detail about the error (str, optional)
    """

    def __str__(self):
        s = "%s, %s, %d, %s" % (
                self.response.request.method,
                self.response.request.url,
                self.response.status_code,
                self.type,
        )
        if self.message:
            s += ', %r' % self.message
        return s

    @property
    def response(self):
        return self.args[0]

    @property
    def type(self):
        return self.args[1]

    @property
    def message(self):
        if len(self.args) > 2:
            return self.args[2]


class ClientError(APIError):
    pass


class ServerError(APIError):
    pass


class AuthHelper(object):

    def __init__(self, client_id, client_secret, redirect_uri, type='code'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.callback_url = redirect_uri
        self.type = type

    @property
    def authentication_url(self):
        """Redirect your users to here to authenticate them."""
        params = {
            'client_id': self.client_id,
            'response_type': self.type,
            'redirect_uri': self.callback_url
        }
        return AUTHENTICATION_URL + "?" + urlencode(params)

    def open_authentication_url(self):
        webbrowser.open(self.authentication_url)

    def get_access_token(self, code):
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': self.callback_url,
            'code': code
        }
        response = requests.get(ACCESS_TOKEN_URL, params=params)
        return _process_response(response)['access_token']


def create_access_token(client_id, client_secret, user, password, fingerprint=''):
    url = AUTHORIZATION_URL.format(client_id=client_id, fingerprint=fingerprint)
    data = {'client_secret': client_secret}
    auth = (user, password)
    response = requests.put(url, data=data, auth=auth)
    return _process_response(response)['access_token']


def revoke_access_token(access_token):
    url = BASE_URL + '/oauth/grants/logout'
    headers = {'Authorization': 'token %s' % access_token}
    response = requests.post(url, headers=headers)
    _process_response(response)


class Client(object):

    def __init__(self, access_token, use_retry=False, extra_headers=None, timeout=5):
        self.access_token = access_token
        self.session = requests.session()
        self.session.headers['User-Agent'] = 'putio.py/%s' % __version__
        self.session.headers['Accept'] = 'application/json'
        self.timeout = timeout
        if extra_headers:
            self.session.headers.update(extra_headers)

        if use_retry:
            # Retry maximum 10 times, backoff on each retry
            # Sleeps 1s, 2s, 4s, 8s, etc to a maximum of 120s between retries
            # Retries on HTTP status codes 500, 502, 503, 504
            retries = Retry(total=10,
                            backoff_factor=1,
                            status_forcelist=[500, 502, 503, 504])

            # Use the retry strategy for all HTTPS requests
            self.session.mount('https://', HTTPAdapter(max_retries=retries))

        # Keep resource classes as attributes of client.
        # Pass client to resource classes so resource object
        # can use the client.
        attributes = {'client': self}
        self.File = type('File', (_File,), attributes)
        self.Subtitle = type('Subtitle', (_Subtitle,), attributes)
        self.Transfer = type('Transfer', (_Transfer,), attributes)
        self.Account = type('Account', (_Account,), attributes)

    def close(self):
        self.session.close()

    def request(self, path, method='GET', params=None, data=None, files=None,
                headers=None, raw=False, allow_redirects=True, stream=False,
                timeout=None):
        """
        Wrapper around requests.request()

        Prepends BASE_URL to path.
        Adds self.oauth_token to authorization header.
        Parses response as JSON and returns it.

        """
        if not headers:
            headers = {}

        if timeout is None:
            timeout = self.timeout

        # All requests must include oauth_token
        headers['Authorization'] = 'token %s' % self.access_token

        if path.startswith(('http://', 'https://')):
            url = path
        else:
            url = BASE_URL + path
        logger.debug('url: %s', url)

        response = self.session.request(
            method, url, params=params, data=data, files=files,
            headers=headers, allow_redirects=allow_redirects, stream=stream,
            timeout=self.timeout)
        logger.debug('response: %s', response)
        if raw:
            return response

        return _process_response(response)


def _process_response(response):
    logger.debug('response: %s', response)
    logger.debug('content: %s', response.content)

    http_error_type = str(response.status_code)[0]
    exception_classes = {
            '2': None,
            '4': ClientError,
            '5': ServerError,
    }

    try:
        exception_class = exception_classes[http_error_type]
    except KeyError:
        raise ServerError(response, 'UnknownStatusCode', str(response.status_code))

    if exception_class:
        try:
            d = _parse_content(response)
            error_type = d['error_type']
            error_message = d['error_message']
        except Exception:
            error_type = 'UnknownError'
            error_message = None

        raise exception_class(response, error_type, error_message)

    return _parse_content(response)


def _parse_content(response):
    try:
        u = response.content.decode('utf-8')
    except ValueError:
        raise ServerError(response, 'InvalidEncoding', 'cannot decode as UTF-8')

    try:
        return json.loads(u)
    except ValueError:
        raise ServerError(response, 'InvalidJSON')


class _BaseResource(object):

    client = None

    def __init__(self, resource_dict):
        """Constructs the object from a dict."""
        # All resources must have id and name attributes
        self.id = None
        self.name = None
        self.__dict__.update(resource_dict)
        try:
            self.created_at = strptime(self.created_at)
        except Exception:
            self.created_at = None

    def __str__(self):
        return self.name.encode('utf-8')

    def __repr__(self):
        # shorten name for display
        name = self.name[:17] + '...' if len(self.name) > 20 else self.name
        return '<%s id=%r, name=%r>' % (
            self.__class__.__name__, self.id, name)


class _File(_BaseResource):

    @classmethod
    def get(cls, id):
        d = cls.client.request('/files/%i' % id, method='GET')
        t = d['file']
        return cls(t)

    @classmethod
    def list(cls, parent_id=0, per_page=1000, sort_by=None, content_type=None,
             file_type=None, stream_url=False, stream_url_parent=False, mp4_stream_url=False,
             mp4_stream_url_parent=False, hidden=False, mp4_status=False):
        """ List files and their properties.

         parent_id List files under a folder. If not specified, it will show files listed at the root folder

         """
        params = {
                'parent_id': parent_id,
                'per_page': str(per_page),
                'sort_by': sort_by or '',
                'content_type': content_type or '',
                'file_type': file_type or '',
                'stream_url': str(stream_url),
                'stream_url_parent': str(stream_url_parent),
                'mp4_stream_url':  str(mp4_stream_url),
                'mp4_stream_url_parent': str(mp4_stream_url_parent),
                'hidden': str(hidden),
                'mp4_status':  str(mp4_status),
        }
        d = cls.client.request('/files/list', params=params)
        files = d['files']
        while d['cursor']:
            d = cls.client.request('/files/list/continue', method='POST', data={'cursor': d['cursor']})
            files.extend(d['files'])

        return [cls(f) for f in files]

    @classmethod
    def upload(cls, path, name=None, parent_id=0):
        """ If the uploaded file is a torrent file, starts it as a transfer. This endpoint must be used with upload.put.io domain.
        name: override the file name
        parent_id: where to put the file
        """
        with io.open(path, 'rb') as f:
            if name:
                files = {'file': (name, f)}
            else:
                files = {'file': f}
            d = cls.client.request(UPLOAD_URL, method='POST',
                                   data={'parent_id': parent_id}, files=files)

        try:
            return cls(d['file'])
        except KeyError:
            # server returns a transfer info if file is a torrent
            return cls.client.Transfer(d['transfer'])

    @classmethod
    def upload_tus(cls, path, name=None, parent_id=0):
        headers = {'Authorization': 'token %s' % cls.client.access_token}
        metadata = {'parent_id': str(parent_id)}
        if name:
            metadata['name'] = name
        else:
            metadata['name'] = os.path.basename(path)
        with io.open(path, 'rb') as f:
            tus.upload(f, TUS_UPLOAD_URL, file_name=name, headers=headers, metadata=metadata)

    @classmethod
    def search(cls, query, per_page=100):
        """
        Search makes a search request with the given query
        query: The keyword to search
        per_page: Number of files to be returned in response.
        """
        path = '/files/search'
        result = cls.client.request(path, params={'query': query, 'per_page': per_page})
        files = result['files']
        return [cls(f) for f in files]

    def dir(self):
        """List the files under directory."""
        return self.list(parent_id=self.id)

    def download(self, dest='.', delete_after_download=False, chunk_size=CHUNK_SIZE):
        if self.content_type == 'application/x-directory':
            self._download_directory(dest, delete_after_download, chunk_size)
        else:
            self._download_file(dest, delete_after_download, chunk_size)

    def _download_directory(self, dest, delete_after_download, chunk_size):
        name = _str(self.name)

        dest = os.path.join(dest, name)
        if not os.path.exists(dest):
            os.mkdir(dest)

        for sub_file in self.dir():
            sub_file.download(dest, delete_after_download, chunk_size)

        if delete_after_download:
            self.delete()

    def _verify_file(self, filepath):
        logger.info('verifying crc32...')
        filesize = os.path.getsize(filepath)
        if self.size != filesize:
            logging.error('file %s is %d bytes, should be %s bytes' % (filepath, filesize, self.size))
            return False

        crcbin = 0
        with io.open(filepath, 'rb') as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break

                crcbin = binascii.crc32(chunk, crcbin) & 0xffffffff

        crc32 = '%08x' % crcbin

        if crc32 != self.crc32:
            logging.error('file %s CRC32 is %s, should be %s' % (filepath, crc32, self.crc32))
            return False

        logger.info('crc OK')
        return True

    def _download_file(self, dest, delete_after_download, chunk_size):
        name = _str(self.name)

        filepath = os.path.join(dest, name)
        logger.info('downloading file to: %s', filepath)
        if os.path.exists(filepath):
            first_byte = os.path.getsize(filepath)

            if first_byte == self.size:
                logger.warning('file %s exists and is the correct size %d' % (filepath, self.size))
        else:
            first_byte = 0

        logger.debug('file %s is currently %d, should be %d' % (filepath, first_byte, self.size))

        if self.size == 0:
            # Create an empty file
            io.open(filepath, 'wb').close()
            logger.debug('created empty file %s' % filepath)
        else:
            if first_byte < self.size:
                with io.open(filepath, 'ab') as f:
                    headers = {'Range': 'bytes=%d-' % first_byte}

                    logger.debug('request range: bytes=%d-' % first_byte)
                    path = '/files/%d/url' % self.id
                    response = self.client.request(path, raw=True)
                    if str(response.status_code)[0] != '2':
                        # Raises exception on 4xx and 5xx
                        _process_response(response)
                    
                    download_link = str(response.json().get('url'))
                    response = self.client.request(download_link,
                                                   headers=headers,
                                                   raw=True,
                                                   stream=True)
                    if str(response.status_code)[0] != '2':
                        # Raises exception on 4xx and 5xx
                        _process_response(response)

                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)

        if self._verify_file(filepath):
            if delete_after_download:
                self.delete()

    def _get_link(self, path, params):
        response = self.client.request(path, method='HEAD', params=params, raw=True, allow_redirects=False)
        if str(response.status_code)[0] == '2':
            return response.url
        elif response.status_code == 302:
            return response.headers['Location']

        # Raises exception on 4xx and 5xx
        _process_response(response)

    def get_stream_link(self, tunnel=True, prefer_mp4=False):
        if prefer_mp4 and self.get_mp4_status()['status'] == 'COMPLETED':
            path = '/files/%d/mp4/stream' % self.id
        else:
            path = '/files/%d/stream' % self.id

        params = {}
        if not tunnel:
            params['notunnel'] = '1'

        return self._get_link(path, params)

    def get_download_link(self):
        path = '/files/%d/download' % self.id
        params = {}

        return self._get_link(path, params)

    def convert_to_mp4(self):
        path = '/files/%d/mp4' % self.id
        self.client.request(path, method='POST')

    def get_mp4_status(self):
        path = '/files/%d/mp4' % self.id
        response = self.client.request(path)
        return response['mp4']

    def get_subtitles(cls):
        path = '/files/%d/subtitles' % cls.id
        response = cls.client.request(path, method='GET')
        json_subtitles = response['subtitles']

        return [cls.client.Subtitle(s, cls.id) for s in json_subtitles]

    def delete(self, skip_nonexistents=False):
        data = {'file_id': self.id}
        if skip_nonexistents:
            data['skip_nonexistents'] = 1
        return self.client.request('/files/delete', method='POST', data=data)

    @classmethod
    def delete_multi(cls, ids, skip_nonexistents=False):
        data = {'file_ids': ','.join(map(str, ids))}
        if skip_nonexistents:
            data['skip_nonexistents'] = 1
        return cls.client.request('/files/delete', method='POST', data=data)

    def move(self, parent_id):
        return self.client.request('/files/move', method='POST',
                                   data={'file_ids': str(self.id), 'parent_id': str(parent_id)})

    def rename(self, name):
        return self.client.request('/files/rename', method='POST',
                                   data={'file_id': str(self.id), 'name': str(name)})

    @classmethod
    def create_folder(cls, name, parent_id=0):
        r = cls.client.request('/files/create-folder', method='POST',
                               data={'name': name, 'parent_id': str(parent_id)})
        f = r['file']
        return cls(f)


class _Transfer(_BaseResource):

    @classmethod
    def list(cls):
        """ List all transfers """

        d = cls.client.request('/transfers/list')
        transfers = d['transfers']
        return [cls(t) for t in transfers]

    @classmethod
    def get(cls, id):
        """ Get transfer details """
        d = cls.client.request('/transfers/%i' % id, method='GET')
        t = d['transfer']
        return cls(t)

    @classmethod
    def add_url(cls, url, parent_id=0, callback_url=None):
        """ Add new transfer from URI"""

        data = {'url': url, 'save_parent_id': parent_id}
        if callback_url:
            data['callback_url'] = callback_url

        d = cls.client.request('/transfers/add', method='POST', data=data)
        return cls(d['transfer'])

    @classmethod
    def add_torrent(cls, path, parent_id=0, callback_url=None):
        params = {'torrent': 'true'}
        data = {'parent_id': parent_id}
        if callback_url:
            data['callback_url'] = callback_url

        with io.open(path, 'rb') as f:
            files = {'file': f}
            d = cls.client.request(UPLOAD_URL, method='POST', params=params, data=data, files=files)

        return cls(d['transfer'])

    @classmethod
    def clean(cls):
        """ Clean finished transfers"""

        return cls.client.request('/transfers/clean', method='POST')

    def cancel(self):
        """ Cancel or remove  transfers"""

        return self.client.request('/transfers/cancel',
                                   method='POST',
                                   data={'transfer_ids': self.id})

    @classmethod
    def cancel_multi(cls, ids):
        return cls.client.request('/transfers/cancel',
                                  method='POST',
                                  data={'transfer_ids': ','.join(map(str, ids))})


class _Account(_BaseResource):

    @classmethod
    def info(cls):
        """ Get Account info"""
        return cls.client.request('/account/info', method='GET')

    @classmethod
    def settings(cls):
        """ Get account settings"""
        return cls.client.request('/account/settings', method='GET')


class _Subtitle(_BaseResource):

    def __init__(self, resource_dict, file_id):
        self.__dict__.update(resource_dict)
        self.file_id = file_id

    def get_download_link(self):
        path = '/files/%d/subtitles/%s' % (self.file_id, self.key)
        params = {}

        response = self.client.request(path, method='HEAD', params=params, raw=True, allow_redirects=False)

        if str(response.status_code)[0] == '2':
            return response.url
        elif response.status_code == 302:
            return response.headers['Location']

    def download(self, dest):
        name = _str(self.name)
        path = self.get_download_link()

        filepath = os.path.join(dest, name)
        logger.info('downloading subtitle file to: %s', filepath)
        response = self.client.request(path, method='GET', raw=True)
        with io.open(filepath, 'wb') as f:
            f.write(response.content)

        return filepath


# Due to a nasty bug in datetime module, datetime.strptime calls
# are not thread-safe and can throw a TypeError. Details: https://bugs.python.org/issue7980
# Here we are implementing simple RFC3339 parser which is used in Put.io APIv2.
def strptime(date):
    """Returns datetime object from the given date, which is in a specific format: YYYY-MM-ddTHH:mm:ss"""
    d = {
        'year': date[0:4],
        'month': date[5:7],
        'day': date[8:10],
        'hour': date[11:13],
        'minute': date[14:16],
        'second': date[17:],
    }

    d = dict((k, int(v)) for k, v in d.items())

    return datetime(**d)


def _str(s):
    """Python 3 compatibility function for converting to str."""
    try:
        if isinstance(s, unicode):
            return s.encode('utf-8', 'replace')
    except NameError:
        pass
    return s
