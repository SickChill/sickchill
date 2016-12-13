from .notifications import Notifications
from .recordings import Recordings
from twilio.rest.resources.call_feedback import (
    CallFeedbackFactory,
    CallFeedbackSummary,
)
from .util import normalize_dates, parse_date, transform_params
from . import InstanceResource, ListResource


class Call(InstanceResource):
    """ A call resource """

    BUSY = "busy"
    CANCELED = "canceled"
    COMPLETED = "completed"
    FAILED = "failed"
    IN_PROGRESS = "in-progress"
    NO_ANSWER = "no-answer"
    QUEUED = "queued"
    RINGING = "ringing"

    subresources = [
        Notifications,
        Recordings,
        CallFeedbackFactory,
    ]

    def hangup(self):
        """ If this call is currenlty active, hang up the call.
        If this call is scheduled to be made, remove the call
        from the queue
        """
        a = self.parent.hangup(self.name)
        self.load(a.__dict__)

    def cancel(self):
        """ If the called is queued or rining, cancel the calls.
        Will not affect in progress calls
        """
        a = self.parent.cancel(self.name)
        self.load(a.__dict__)

    def route(self, **kwargs):
        """Route the specified :class:`Call` to another url.

        :param url: A valid URL that returns TwiML.
        :param method: HTTP method Twilio uses when requesting the above URL.
        """
        a = self.parent.route(self.name, **kwargs)
        self.load(a.__dict__)

    def delete(self):
        """Delete the specified :class:`Call` record from Twilio."""
        return self.parent.delete(self.name)


class Calls(ListResource):
    """ A list of Call resources """

    name = "Calls"
    instance = Call

    def __init__(self, *args, **kwargs):
        super(Calls, self).__init__(*args, **kwargs)
        self.summary = CallFeedbackSummary(self, *args, **kwargs)

    @normalize_dates
    def list(self, from_=None, ended_after=None,
             ended_before=None, ended=None, started_before=None,
             started_after=None, started=None, **kwargs):
        """
        Returns a page of :class:`Call` resources as a list. For paging
        informtion see :class:`ListResource`

        :param date after: Only list calls started after this datetime
        :param date before: Only list calls started before this datetime
        """
        kwargs["from"] = from_
        kwargs["StartTime<"] = started_before
        kwargs["StartTime>"] = started_after
        kwargs["StartTime"] = parse_date(started)
        kwargs["EndTime<"] = ended_before
        kwargs["EndTime>"] = ended_after
        kwargs["EndTime"] = parse_date(ended)
        return self.get_instances(kwargs)

    @normalize_dates
    def iter(self, from_=None, ended_after=None,
             ended_before=None, ended=None, started_before=None,
             started_after=None, started=None, **kwargs):
        """
        Returns an iterator of :class:`Call` resources.

        :param date after: Only list calls started after this datetime
        :param date before: Only list calls started before this datetime
        """
        kwargs["from"] = from_
        kwargs["StartTime<"] = started_before
        kwargs["StartTime>"] = started_after
        kwargs["StartTime"] = parse_date(started)
        kwargs["EndTime<"] = ended_before
        kwargs["EndTime>"] = ended_after
        kwargs["EndTime"] = parse_date(ended)
        return super(Calls, self).iter(**kwargs)

    def create(self, to, from_, url, status_method=None, status_events=None,
               **kwargs):
        """
        Make a phone call to a number.

        :param str to: The phone number to call
        :param str `from_`: The caller ID (must be a verified Twilio number)
        :param str url: The URL to read TwiML from when the call connects
        :param method: The HTTP method Twilio should use to request the url
        :type method: None (defaults to 'POST'), 'GET', or 'POST'
        :param str fallback_url: A URL that Twilio will request if an error
            occurs requesting or executing the TwiML at url
        :param str fallback_method: The HTTP method that Twilio should use
            to request the fallback_url
        :type fallback_method: None (will make 'POST' request),
                               'GET', or 'POST'
        :param str status_callback: A URL that Twilio will request when the
            call ends to notify your app.
        :param str status_method: The HTTP method Twilio should use when
            requesting the above URL.
        :param list status_events: A list of call progress events Twilio
            should send status callback requests on. One or more of:
            'initiated', 'ringing', 'answered', 'completed'. Defaults to
            ['completed'] if not provided. 'completed' events are sent
            free of charge; see twilio.com for current pricing on others.
        :param str if_machine: Tell Twilio to try and determine if a machine
            (like voicemail) or a human has answered the call.
            See more in our `answering machine documentation
            <http://www.twilio.com/docs/api/rest/making_calls>`_.
        :type if_machine: None, 'Continue', or 'Hangup'
        :param str send_digits: A string of keys to dial after
            connecting to the number.
        :type send_digits: None or any combination of
            (0-9), '#', '*' or 'w' (to insert a half second pause).
        :param int timeout: The integer number of seconds that Twilio should
            allow the phone to ring before assuming there is no answer.
        :param str application_sid: The 34 character sid of the application
            Twilio should use to handle this phone call.
            Should not be used in conjunction with the url parameter.

        :return: A :class:`Call` object
        """
        kwargs["from"] = from_
        kwargs["to"] = to
        kwargs["url"] = url
        kwargs["status_callback_method"] = status_method
        kwargs["status_callback_event"] = status_events
        return self.create_instance(kwargs)

    def update(self, sid, **kwargs):
        return self.update_instance(sid, kwargs)

    def cancel(self, sid):
        """ If this call is queued or ringing, cancel the call.
        Will not affect in-progress calls.

        :param sid: A Call Sid for a specific call
        :returns: Updated :class:`Call` resource
        """
        return self.update(sid, status=Call.CANCELED)

    def hangup(self, sid):
        """ If this call is currently active, hang up the call. If this call is
        scheduled to be made, remove the call from the queue.

        :param sid: A Call Sid for a specific call
        :returns: Updated :class:`Call` resource
        """
        return self.update(sid, status=Call.COMPLETED)

    def route(self, sid, url, method="POST"):
        """Route the specified :class:`Call` to another url.

        :param sid: A Call Sid for a specific call
        :param url: A valid URL that returns TwiML.
        :param method: The HTTP method Twilio uses when requesting the URL.
        :returns: Updated :class:`Call` resource
        """
        return self.update(sid, url=url, method=method)

    def feedback(self, sid, quality_score, issue=None):
        """ Create feedback for the given call.

        :param sid: A Call Sid for a specific call
        :param quality_score: The quality of the call
        :param issue: A list of issues experienced during the call
        :returns: A :class:`CallFeedback` object
        """
        uri = "%s/%s" % (self.uri, sid)
        call_feedback_factory = CallFeedbackFactory(
            uri, self.auth, self.timeout
        )
        return call_feedback_factory.create(
            quality_score=quality_score, issue=issue
        )

    def delete(self, sid):
        """Delete the given Call record from Twilio."""
        return self.delete_instance(sid)
