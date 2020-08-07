# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import requests
import tempfile
from datetime import datetime
try:
    from base64 import encodebytes
except ImportError:
    from base64 import encodestring as encodebytes

import diskcache
from dateutil.tz import tzutc
from dateutil.parser import parse
import boto.utils
from six.moves.urllib.parse import urlparse, parse_qs, quote
from boto import provider
from boto.connection import HTTPRequest
from boto.auth import HmacAuthV3HTTPHandler

from .constants import APP_KEY, HOST, USER_AGENT, BASE_URI


class ZuluHmacAuthV3HTTPHandler(HmacAuthV3HTTPHandler):

    def sign_string(self, string_to_sign):
        new_hmac = self._get_hmac()
        new_hmac.update(string_to_sign)
        return encodebytes(new_hmac.digest()).decode('utf-8').strip()

    def headers_to_sign(self, http_request):
        headers_to_sign = {'Host': self.host}
        for name, value in http_request.headers.items():
            lname = name.lower()
            if lname.startswith('x-amz'):
                headers_to_sign[name] = value
        return headers_to_sign

    def canonical_query_string(self, http_request):
        if http_request.method == 'POST':
            return ''
        qs_parts = []
        for param in sorted(http_request.params):
            value = boto.utils.get_utf8_value(http_request.params[param])
            param_ = quote(param, safe='-_.~')
            value_ = quote(value, safe='-_.~')
            qs_parts.append('{0}={1}'.format(param_, value_))
        return '&'.join(qs_parts)

    def string_to_sign(self, http_request):
        headers_to_sign = self.headers_to_sign(http_request)
        canonical_qs = self.canonical_query_string(http_request)
        canonical_headers = self.canonical_headers(headers_to_sign)
        string_to_sign = '\n'.join((
            http_request.method,
            http_request.path,
            canonical_qs,
            canonical_headers,
            '',
            http_request.body
        ))
        return string_to_sign, headers_to_sign


def _get_credentials():
    url = '{0}/authentication/credentials/temporary/ios82'.format(BASE_URI)
    response = requests.post(
        url, json={'appKey': APP_KEY}, headers={'User-Agent': USER_AGENT}
    )
    response.raise_for_status()
    return json.loads(response.content.decode('utf8'))['resource']


class Auth(object):

    SOON_EXPIRES_SECONDS = 60
    _CREDS_STORAGE_KEY = 'imdbpie-credentials'

    def __init__(self, creds=None):
        self._cachedir = tempfile.gettempdir()

    def _get_creds(self):
        with diskcache.Cache(directory=self._cachedir) as cache:
            return cache.get(self._CREDS_STORAGE_KEY)

    def _set_creds(self, creds):
        with diskcache.Cache(directory=self._cachedir) as cache:
            cache[self._CREDS_STORAGE_KEY] = creds
        return creds

    def clear_cached_credentials(self):
        with diskcache.Cache(directory=self._cachedir) as cache:
            cache.delete(self._CREDS_STORAGE_KEY)

    def _creds_soon_expiring(self):
        creds = self._get_creds()
        if not creds:
            return creds, True
        expires_at = parse(creds['expirationTimeStamp'])
        now = datetime.now(tzutc())
        if now < expires_at:
            time_diff = expires_at - now
            if time_diff.total_seconds() < self.SOON_EXPIRES_SECONDS:
                # creds will soon expire, so renew them
                return creds, True
            return creds, False
        else:
            return creds, True

    def get_auth_headers(self, url_path):
        creds, soon_expires = self._creds_soon_expiring()
        if soon_expires:
            creds = self._set_creds(creds=_get_credentials())

        handler = ZuluHmacAuthV3HTTPHandler(
            host=HOST,
            config={},
            provider=provider.Provider(
                name='aws',
                access_key=creds['accessKeyId'],
                secret_key=creds['secretAccessKey'],
                security_token=creds['sessionToken'],
            )
        )
        parsed_url = urlparse(url_path)
        params = {
            key: val[0] for key, val in parse_qs(parsed_url.query).items()
        }
        request = HTTPRequest(
            method='GET', protocol='https', host=HOST,
            port=443, path=parsed_url.path, auth_path=None, params=params,
            headers={}, body=''
        )
        handler.add_auth(req=request)
        headers = request.headers
        headers['User-Agent'] = USER_AGENT
        return headers
