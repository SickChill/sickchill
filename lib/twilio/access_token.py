import time
from twilio import jwt


class IpMessagingGrant(object):
    """ Grant to access Twilio IP Messaging """
    def __init__(self, service_sid=None, endpoint_id=None,
                 deployment_role_sid=None, push_credential_sid=None):
        self.service_sid = service_sid
        self.endpoint_id = endpoint_id
        self.deployment_role_sid = deployment_role_sid
        self.push_credential_sid = push_credential_sid

    @property
    def key(self):
        return "ip_messaging"

    def to_payload(self):
        grant = {}
        if self.service_sid:
            grant['service_sid'] = self.service_sid
        if self.endpoint_id:
            grant['endpoint_id'] = self.endpoint_id
        if self.deployment_role_sid:
            grant['deployment_role_sid'] = self.deployment_role_sid
        if self.push_credential_sid:
            grant['push_credential_sid'] = self.push_credential_sid

        return grant


class ConversationsGrant(object):
    """ Grant to access Twilio Conversations """
    def __init__(self, configuration_profile_sid=None):
        self.configuration_profile_sid = configuration_profile_sid

    @property
    def key(self):
        return "rtc"

    def to_payload(self):
        grant = {}
        if self.configuration_profile_sid:
            grant['configuration_profile_sid'] = self.configuration_profile_sid

        return grant


class VoiceGrant(object):
    """ Grant to access Twilio Programmable Voice"""
    def __init__(self,
                 outgoing_application_sid=None,
                 outgoing_application_params=None,
                 push_credential_sid=None,
                 endpoint_id=None):
        self.outgoing_application_sid = outgoing_application_sid
        """ :type : str """
        self.outgoing_application_params = outgoing_application_params
        """ :type : dict """
        self.push_credential_sid = push_credential_sid
        """ :type : str """
        self.endpoint_id = endpoint_id
        """ :type : str """

    @property
    def key(self):
        return "voice"

    def to_payload(self):
        grant = {}
        if self.outgoing_application_sid:
            grant['outgoing'] = {}
            grant['outgoing']['application_sid'] = \
                self.outgoing_application_sid

            if self.outgoing_application_params:
                grant['outgoing']['params'] = self.outgoing_application_params

        if self.push_credential_sid:
            grant['push_credential_sid'] = self.push_credential_sid

        if self.endpoint_id:
            grant['endpoint_id'] = self.endpoint_id

        return grant


class VideoGrant(object):
    """ Grant to access Twilio Video """
    def __init__(self, configuration_profile_sid=None):
        self.configuration_profile_sid = configuration_profile_sid

    @property
    def key(self):
        return "video"

    def to_payload(self):
        grant = {}
        if self.configuration_profile_sid:
            grant['configuration_profile_sid'] = self.configuration_profile_sid

        return grant


class AccessToken(object):
    """ Access Token used to access Twilio Resources """
    def __init__(self, account_sid, signing_key_sid, secret,
                 identity=None, ttl=3600, nbf=None):
        self.account_sid = account_sid
        self.signing_key_sid = signing_key_sid
        self.secret = secret

        self.identity = identity
        self.ttl = ttl
        self.nbf = nbf
        self.grants = []

    def add_grant(self, grant):
        self.grants.append(grant)

    def to_jwt(self, algorithm='HS256'):
        now = int(time.time())
        headers = {
            "typ": "JWT",
            "cty": "twilio-fpa;v=1"
        }

        grants = {}
        if self.identity:
            grants["identity"] = self.identity

        for grant in self.grants:
            grants[grant.key] = grant.to_payload()

        payload = {
            "jti": '{0}-{1}'.format(self.signing_key_sid, now),
            "iss": self.signing_key_sid,
            "sub": self.account_sid,
            "exp": now + self.ttl,
            "grants": grants
        }

        if self.nbf is not None:
            payload['nbf'] = self.nbf

        return jwt.encode(payload, self.secret, headers=headers,
                          algorithm=algorithm)

    def __str__(self):
        return self.to_jwt()
