import logging
import platform
import os

from twilio.exceptions import TwilioException
from twilio.rest.resources import Connection
from twilio.rest.resources import UNSET_TIMEOUT
from twilio.rest.resources import make_request
from twilio.version import __version__ as LIBRARY_VERSION


def find_credentials(environ=None):
    """
    Look in the current environment for Twilio credentials

    :param environ: the environment to check
    """
    environment = environ or os.environ
    try:
        account = environment["TWILIO_ACCOUNT_SID"]
        token = environment["TWILIO_AUTH_TOKEN"]
        return account, token
    except KeyError:
        return None, None


def set_twilio_proxy(proxy_url, proxy_port):
    Connection.set_proxy_info(proxy_url, proxy_port)


class TwilioClient(object):
    def __init__(self, account=None, token=None, base="https://api.twilio.com",
                 version="2010-04-01", timeout=UNSET_TIMEOUT,
                 request_account=None):
        """
        Create a Twilio API client.
        """

        # Get account credentials
        if not account or not token:
            account, token = find_credentials()
            if not account or not token:
                raise TwilioException("""
Twilio could not find your account credentials. Pass them into the
TwilioRestClient constructor like this:

    client = TwilioRestClient(account='AC38135355602040856210245275870',
                              token='2flnf5tdp7so0lmfdu3d')

Or, add your credentials to your shell environment. From the terminal, run

    echo "export TWILIO_ACCOUNT_SID=AC3813535560204085626521" >> ~/.bashrc
    echo "export TWILIO_AUTH_TOKEN=2flnf5tdp7so0lmfdu3d7wod" >> ~/.bashrc

and be sure to replace the values for the Account SID and auth token with the
values from your Twilio Account at https://www.twilio.com/user/account.
""")
        self.base = base
        self.auth = (account, token)
        self.timeout = timeout
        req_account = request_account if request_account else account
        self.account_uri = "{0}/{1}/Accounts/{2}".format(base,
                                                         version, req_account)

    def request(self, path, method=None, vars=None):
        """sends a request and gets a response from the Twilio REST API

        .. deprecated:: 3.0

        :param path: the URL (relative to the endpoint URL, after the /v1
        :param url: the HTTP method to use, defaults to POST
        :param vars: for POST or PUT, a dict of data to send

        :returns: Twilio response in XML or raises an exception on error
        :raises: a :exc:`ValueError` if the path is invalid
        :raises: a :exc:`NotImplementedError` if the method is unknown

        This method is only included for backwards compatability reasons.
        It will be removed in a future version
        """
        logging.warning(":meth:`TwilioRestClient.request` is deprecated and "
                        "will be removed in a future version")

        vars = vars or {}
        params = None
        data = None

        if not path or len(path) < 1:
            raise ValueError('Invalid path parameter')
        if method and method not in ['GET', 'POST', 'DELETE', 'PUT']:
            raise NotImplementedError(
                'HTTP %s method not implemented' % method)

        if path[0] == '/':
            uri = self.base + path
        else:
            uri = self.base + '/' + path

        if method == "GET":
            params = vars
        elif method == "POST" or method == "PUT":
            data = vars

        user_agent = "twilio-python %s (python-%s)" % (
            LIBRARY_VERSION,
            platform.python_version(),
        )

        headers = {
            "User-Agent": user_agent,
            "Accept-Charset": "utf-8",
        }

        resp = make_request(method, uri, auth=self.auth, data=data,
                            params=params, headers=headers)

        return resp.content
