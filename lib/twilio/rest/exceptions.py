# -*- coding: utf-8 -*-
import sys

from six import u

# Backwards compatibility.
from ..version import __version__, __version_info__

from ..exceptions import TwilioException


class TwilioRestException(TwilioException):
    """ A generic 400 or 500 level exception from the Twilio API

    :param int status: the HTTP status that was returned for the exception
    :param str uri: The URI that caused the exception
    :param str msg: A human-readable message for the error
    :param str method: The HTTP method used to make the request
    :param int|None code: A Twilio-specific error code for the error. This is
         not available for all errors.
    """

    def __init__(self, status, uri, msg="", code=None, method='GET'):
        self.uri = uri
        self.status = status
        self.msg = msg
        self.code = code
        self.method = method

    def __str__(self):
        """ Try to pretty-print the exception, if this is going on screen. """

        def red(words):
            return u("\033[31m\033[49m%s\033[0m") % words

        def white(words):
            return u("\033[37m\033[49m%s\033[0m") % words

        def blue(words):
            return u("\033[34m\033[49m%s\033[0m") % words

        def teal(words):
            return u("\033[36m\033[49m%s\033[0m") % words

        def get_uri(code):
            return "https://www.twilio.com/docs/errors/{0}".format(code)

        # If it makes sense to print a human readable error message, try to
        # do it. The one problem is that someone might catch this error and
        # try to display the message from it to an end user.
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            msg = (
                "\n{red_error} {request_was}\n\n{http_line}"
                "\n\n{twilio_returned}\n\n{message}\n".format(
                    red_error=red("HTTP Error"),
                    request_was=white("Your request was:"),
                    http_line=teal("%s %s" % (self.method, self.uri)),
                    twilio_returned=white(
                        "Twilio returned the following information:"),
                    message=blue(str(self.msg))
                ))
            if self.code:
                msg = "".join([msg, "\n{more_info}\n\n{uri}\n\n".format(
                    more_info=white("More information may be available here:"),
                    uri=blue(get_uri(self.code))),
                ])
            return msg
        else:
            return "HTTP {0} error: {1}".format(self.status, self.msg)
