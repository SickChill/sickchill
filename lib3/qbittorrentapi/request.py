from os import environ
import logging
from pkg_resources import parse_version
from time import sleep
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

try:  # python 3
    from collections.abc import Iterable
    from urllib.parse import urlparse
except ImportError:  # python 2
    from collections import Iterable
    from urlparse import urlparse

import requests
import six

from qbittorrentapi.decorators import login_required
from qbittorrentapi.exceptions import APIConnectionError
from qbittorrentapi.exceptions import HTTPError
from qbittorrentapi.exceptions import HTTP5XXError
from qbittorrentapi.exceptions import LoginFailed
from qbittorrentapi.exceptions import MissingRequiredParameters400Error
from qbittorrentapi.exceptions import InvalidRequest400Error
from qbittorrentapi.exceptions import Unauthorized401Error
from qbittorrentapi.exceptions import Forbidden403Error
from qbittorrentapi.exceptions import NotFound404Error
from qbittorrentapi.exceptions import Conflict409Error
from qbittorrentapi.exceptions import UnsupportedMediaType415Error
from qbittorrentapi.exceptions import InternalServerError500Error
from qbittorrentapi.definitions import APINames

logger = logging.getLogger(__name__)


class Request(object):
    """Facilitates HTTP requests to qBittorrent."""

    def __init__(self, host='', port=None, username=None, password=None, **kwargs):
        self.host = host
        self.port = port
        self.username = username or ''
        self._password = password or ''

        # defaults that should not change
        self._API_URL_BASE_PATH = 'api'
        self._API_URL_API_VERSION = 'v2'

        # state, context, and caching variables
        #   These variables are deleted if the connection to qBittorrent is reset
        #   or a new login is required. All of these (except the SID cookie) should
        #   be reset in _initialize_connection().
        self._SID = None  # authorization cookie
        self._cached_web_api_version = None
        self._application = None
        self._transfer = None
        self._torrents = None
        self._torrent_categories = None
        self._torrent_tags = None
        self._log = None
        self._sync = None
        self._rss = None
        self._search = None
        self._API_URL_BASE = None

        # Configuration variables
        self._VERIFY_WEBUI_CERTIFICATE = kwargs.pop('VERIFY_WEBUI_CERTIFICATE', True)
        self._RAISE_UNIMPLEMENTEDERROR_FOR_UNIMPLEMENTED_API_ENDPOINTS = kwargs.pop(
            'RAISE_UNIMPLEMENTEDERROR_FOR_UNIMPLEMENTED_API_ENDPOINTS',
            kwargs.pop('RAISE_NOTIMPLEMENTEDERROR_FOR_UNIMPLEMENTED_API_ENDPOINTS', False))
        self._VERBOSE_RESPONSE_LOGGING = kwargs.pop('VERBOSE_RESPONSE_LOGGING', False)
        self._PRINT_STACK_FOR_EACH_REQUEST = kwargs.pop('PRINT_STACK_FOR_EACH_REQUEST', False)
        self._SIMPLE_RESPONSES = kwargs.pop('SIMPLE_RESPONSES', False)

        if kwargs.pop('DISABLE_LOGGING_DEBUG_OUTPUT', False):
            logging.getLogger('qbittorrentapi').setLevel(logging.INFO)
            logging.getLogger('requests').setLevel(logging.INFO)
            logging.getLogger('urllib3').setLevel(logging.INFO)

        # Environment variables have lowest priority
        if self.host == '' and environ.get('PYTHON_QBITTORRENTAPI_HOST') is not None:
            logger.debug('Using PYTHON_QBITTORRENTAPI_HOST env variable for qBittorrent hostname')
            self.host = environ['PYTHON_QBITTORRENTAPI_HOST']
        if self.username == '' and environ.get('PYTHON_QBITTORRENTAPI_USERNAME') is not None:
            logger.debug('Using PYTHON_QBITTORRENTAPI_USERNAME env variable for username')
            self.username = environ['PYTHON_QBITTORRENTAPI_USERNAME']

        if self._password == '' and environ.get('PYTHON_QBITTORRENTAPI_PASSWORD') is not None:
            logger.debug('Using PYTHON_QBITTORRENTAPI_PASSWORD env variable for password')
            self._password = environ['PYTHON_QBITTORRENTAPI_PASSWORD']

        if self._VERIFY_WEBUI_CERTIFICATE is True and environ.get('PYTHON_QBITTORRENTAPI_DO_NOT_VERIFY_WEBUI_CERTIFICATE') is not None:
            self._VERIFY_WEBUI_CERTIFICATE = False

        # Mocking variables until better unit testing exists
        self._MOCK_WEB_API_VERSION = kwargs.pop('MOCK_WEB_API_VERSION', None)

    ########################################
    # Authorization Endpoints
    ########################################
    @property
    def is_logged_in(self):
        return bool(self._SID)

    def auth_log_in(self, username=None, password=None):
        """
        Log in to qBittorrent host.

        :raises LoginFailed: if credentials failed to log in
        :raises Forbidden403Error: if user user is banned...or not logged in

        :param username: user name for qBittorrent client
        :param password: password for qBittorrent client
        :return: None
        """
        if username:
            self.username = username or ''
            self._password = password or ''

        try:
            self._initialize_context()
            response = self._post(_name=APINames.Authorization,
                                  _method='login',
                                  data={'username': self.username, 'password': self._password})
            self._SID = response.cookies['SID']
        except KeyError:
            logger.debug('Login failed for user "%s"' % self.username)
            raise self._suppress_context(LoginFailed('Login authorization failed for user "%s"' % self.username))
        else:
            logger.debug('Login successful for user "%s"' % self.username)
            logger.debug('SID: %s' % self._SID)

    @login_required
    def auth_log_out(self, **kwargs):
        """End session with qBittorrent."""
        self._get(_name=APINames.Authorization, _method='logout', **kwargs)

    ########################################
    # Helpers
    ########################################
    @classmethod
    def _list2string(cls, input_list=None, delimiter="|"):
        """
        Convert entries in a list to a concatenated string

        :param input_list: list to convert
        :param delimiter: delimiter for concatenation
        :return: if input is a list, concatenated string...else whatever the input was
        """
        if not isinstance(input_list, six.string_types) and isinstance(input_list, Iterable):
            return delimiter.join(map(str, input_list))
        return input_list

    @classmethod
    def _suppress_context(cls, exc):
        """
        This is used to mask an exception with another one.

        For instance, below, the divide by zero error is masked by the CustomException.
            try:
                1/0
            except ZeroDivisionError:
                raise suppress_context(CustomException())

        Note: In python 3, the last line would simply be raise CustomException() from None
        :param exc: new Exception that will be raised
        :return: Exception to be raised
        """
        exc.__cause__ = None
        return exc

    @classmethod
    def _is_version_less_than(cls, ver1, ver2, lteq=True):
        """
        Determine if ver1 is equal to or later than ver2.

        Note: changes need to be reflected in decorators._is_version_less_than as well

        :param ver1: version to check
        :param ver2: current version of application
        :param lteq: True for Less Than or Equals; False for just Less Than
        :return: True or False
        """
        if lteq:
            return parse_version(ver1) <= parse_version(ver2)
        return parse_version(ver1) < parse_version(ver2)

    ########################################
    # HTTP Requests
    ########################################
    def _initialize_context(self):
        """Reset context. This is necessary when the auth cookie needs to be replaced."""
        # cache to avoid perf hit from version checking certain endpoints
        self._cached_web_api_version = None

        # reset URL so the full URL is derived again (primarily allows for switching scheme for WebUI: HTTP <-> HTTPS)
        self._API_URL_BASE = None

        # reinitialize interaction layers
        self._application = None
        self._transfer = None
        self._torrents = None
        self._torrent_categories = None
        self._torrent_tags = None
        self._log = None
        self._sync = None
        self._rss = None
        self._search = None

    def _get(self, _name=APINames.EMPTY, _method='', **kwargs):
        return self._request_wrapper(http_method='get', api_name=_name, api_method=_method, **kwargs)

    def _post(self, _name=APINames.EMPTY, _method='', **kwargs):
        return self._request_wrapper(http_method='post', api_name=_name, api_method=_method, **kwargs)

    def _request_wrapper(self, _retries=2, _retry_backoff_factor=.3, **kwargs):
        """
        Wrapper to manage requests retries.
        This should retry at least twice to account for the Web API switching from HTTP to HTTPS.
        During the second attempt, the URL is rebuilt using HTTP or HTTPS as appropriate.
        """
        max_retries = _retries if _retries > 1 else 2
        for retry in range(0, (max_retries + 1)):
            try:
                return self._request(**kwargs)
            except HTTPError as e:
                # retry the request for HTTP 500 statuses, raise immediately for everything else (e.g. 4XX statuses)
                if not isinstance(e, HTTP5XXError) or retry >= max_retries:
                    raise
            except Exception as e:
                if retry >= max_retries:
                    error_prologue = 'Failed to connect to qBittorrent. '
                    error_messages = {
                        requests.exceptions.SSLError:
                            'This is likely due to using an untrusted certificate (likely self-signed) '
                            'for HTTPS qBittorrent WebUI. To suppress this error (and skip certificate '
                            'verification consequently exposing the HTTPS connection to man-in-the-middle '
                            'attacks), set VERIFY_WEBUI_CERTIFICATE=False when instantiating Client or set '
                            'environment variable PYTHON_QBITTORRENTAPI_DO_NOT_VERIFY_WEBUI_CERTIFICATE '
                            'to a non-null value. SSL Error: %s' % repr(e),
                        requests.exceptions.HTTPError: 'Invalid HTTP Response: %s' % repr(e),
                        requests.exceptions.TooManyRedirects: 'Too many redirects: %s' % repr(e),
                        requests.exceptions.ConnectionError: 'Connection Error: %s' % repr(e),
                        requests.exceptions.Timeout: 'Timeout Error: %s' % repr(e),
                        requests.exceptions.RequestException: 'Requests Error: %s' % repr(e)
                    }
                    error_message = error_prologue + error_messages.get(type(e), 'Unknown Error: %s' % repr(e))
                    logger.debug(error_message)
                    response = getattr(e, 'response', None)
                    raise APIConnectionError(error_message, response=response)

            # back off on attempting each subsequent retry. first retry is always immediate.
            # if the backoff factor is 0.1, then sleep() will sleep for [0.0s, 0.2s, 0.4s, 0.8s, ...] between retries.
            if retry > 0:
                backoff_time = _retry_backoff_factor * (2 ** ((retry + 1) - 1))
                sleep(backoff_time if backoff_time < 30 else 30)
            logger.debug('Retry attempt %d' % (retry+1))
            self._initialize_context()

    def _request(self, http_method, api_name, api_method,
                 data=None, params=None, files=None, headers=None, requests_params=None, **kwargs):
        _ = kwargs.pop('SIMPLE_RESPONSES', kwargs.pop('SIMPLE_RESPONSE', False))  # ensure SIMPLE_RESPONSE(S) isn't sent

        if isinstance(api_name, APINames):
            api_name = api_name.value
        api_path_list = (self._API_URL_BASE_PATH, self._API_URL_API_VERSION, api_name, api_method)
        url = self._build_url(base_url=self._API_URL_BASE,
                              host=self.host,
                              port=self.port,
                              api_path_list=api_path_list)

        # preserve URL without the path so we don't have to rebuild it next time
        self._API_URL_BASE = url._replace(path='')

        # mechanism to send additional arguments to Requests for individual API calls
        requests_params = requests_params or dict()

        # support for custom params to API
        data = data or dict()
        params = params or dict()
        files = files or dict()
        if http_method == 'get':
            params.update(kwargs)
        if http_method == 'post':
            data.update(kwargs)

        # set up headers
        headers = headers or dict()
        headers['Referer'] = self._API_URL_BASE.geturl()
        headers['Origin'] = self._API_URL_BASE.geturl()
        # send Content-Length zero for empty POSTs
        # Requests will not send Content-Length if data is empty
        if http_method == 'post' and not any(filter(None, data.values())):
            headers['Content-Length'] = '0'

        # include the SID auth cookie unless we're trying to log in and get a SID
        cookies = {'SID': self._SID if 'auth/login' not in url.path else ''}

        # turn off console-printed warnings about SSL certificate issues (e.g. untrusted since it is self-signed)
        if not self._VERIFY_WEBUI_CERTIFICATE:
            disable_warnings(InsecureRequestWarning)

        response = requests.request(method=http_method,
                                    url=url.geturl(),
                                    headers=headers,
                                    cookies=cookies,
                                    verify=self._VERIFY_WEBUI_CERTIFICATE,
                                    data=data,
                                    params=params,
                                    files=files,
                                    **requests_params)

        self.verbose_logging(http_method, response, url)
        self.handle_error_responses(data, params, response)
        return response

    @staticmethod
    def handle_error_responses(data, params, response):
        """Raise proper exception if qBittorrent returns Error HTTP Status."""
        if response.status_code < 400:
            # short circuit for non-error statuses
            return
        elif response.status_code == 400:
            # Returned for malformed requests such as missing or invalid parameters.
            #
            # If an error_message isn't returned, qBittorrent didn't receive all required parameters.
            # APIErrorType::BadParams
            if response.text == '':
                raise MissingRequiredParameters400Error()
            raise InvalidRequest400Error(response.text)

        elif response.status_code == 401:
            # Primarily reserved for XSS and host header issues. Is also
            raise Unauthorized401Error(response.text)

        elif response.status_code == 403:
            # Not logged in or calling an API method that isn't public
            # APIErrorType::AccessDenied
            raise Forbidden403Error(response.text)

        elif response.status_code == 404:
            # API method doesn't exist or more likely, torrent not found
            # APIErrorType::NotFound
            error_message = response.text
            if error_message == '':
                error_torrent_hash = ''
                if data:
                    error_torrent_hash = data.get('hash', error_torrent_hash)
                    error_torrent_hash = data.get('hashes', error_torrent_hash)
                if params and error_torrent_hash == '':
                    error_torrent_hash = params.get('hash', error_torrent_hash)
                    error_torrent_hash = params.get('hashes', error_torrent_hash)
                if error_torrent_hash:
                    error_message = 'Torrent hash(es): %s' % error_torrent_hash
            raise NotFound404Error(error_message)

        elif response.status_code == 409:
            # APIErrorType::Conflict
            raise Conflict409Error(response.text)

        elif response.status_code == 415:
            # APIErrorType::BadData
            raise UnsupportedMediaType415Error(response.text)

        elif response.status_code >= 500:
            raise InternalServerError500Error(response.text)

        elif response.status_code >= 400:
            # Unaccounted for errors from API
            raise HTTPError(response.text)

    def verbose_logging(self, http_method, response, url):
        """Log verbose information about request. Can be useful during development."""
        if self._VERBOSE_RESPONSE_LOGGING:
            resp_logger = logger.debug
            max_text_length_to_log = 254
            if response.status_code != 200:
                max_text_length_to_log = 10000  # log as much as possible in a error condition

            resp_logger('Request URL: (%s) %s' % (http_method.upper(), response.url))
            if str(response.request.body) not in ('None', '') and 'auth/login' not in url.path:
                body_len = max_text_length_to_log if len(response.request.body) > max_text_length_to_log else len(response.request.body)
                resp_logger('Request body: %s%s' % (response.request.body[:body_len], '...<truncated>' if body_len >= 80 else ''))

            resp_logger('Response status: %s (%s)' % (response.status_code, response.reason))
            if response.text:
                text_len = max_text_length_to_log if len(response.text) > max_text_length_to_log else len(response.text)
                resp_logger(
                    'Response text: %s%s' % (response.text[:text_len], '...<truncated>' if text_len >= 80 else ''))
        if self._PRINT_STACK_FOR_EACH_REQUEST:
            from traceback import print_stack
            print_stack()

    @staticmethod
    def _build_url(base_url=None, host='', port=None, api_path_list=None):
        """
        Create a fully qualified URL (minus query parameters that Requests will add later).

        Supports detecting whether HTTPS is enabled for WebUI.

        :param base_url: if the URL was already built, this is the base URL
        :param host: user provided hostname for WebUI
        :param api_path_list: list of strings for API endpoint path (e.g. ['api', 'v2', 'app', 'version'])
        :return: full URL for WebUI API endpoint
        """
        # build full URL if it's the first time we're here
        if base_url is None:
            if not host.lower().startswith(('http:', 'https:', '//')):
                host = '//' + host
            base_url = urlparse(url=host)
            # force scheme to HTTP even if host was provided with HTTPS scheme
            base_url = base_url._replace(scheme='http')
            # add port number if host doesn't contain one
            if port is not None and not isinstance(base_url.port, int):
                base_url = base_url._replace(netloc='%s:%s' % (base_url.netloc, port))

            # detect whether Web API is configured for HTTP or HTTPS
            logger.debug('Detecting scheme for URL...')
            try:
                r = requests.head(base_url.geturl(), allow_redirects=True)
                # if WebUI eventually supports sending a redirect from HTTP to HTTPS then
                # Requests will automatically provide a URL using HTTPS.
                # For instance, the URL returned below will use the HTTPS scheme.
                #  >>> requests.head('http://grc.com', allow_redirects=True).url
                scheme = urlparse(r.url).scheme
            except requests.exceptions.RequestException:
                # qBittorrent will reject the connection if WebUI is configured for HTTPS.
                # If something else caused this exception, we'll properly handle that
                # later during the actual API request.
                scheme = 'https'

            # use detected scheme
            logger.debug('Using %s scheme' % scheme.upper())
            base_url = base_url._replace(scheme=scheme)

            logger.debug('Base URL: %s' % base_url.geturl())

        # add the full API path to complete the URL
        return base_url._replace(path='/'.join(map(lambda s: s.strip('/'), map(str, api_path_list))))
