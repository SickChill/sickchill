from . import InstanceResource, ListResource


class Token(InstanceResource):
    """ A Token instance.

    .. attribute:: username

       The temporary username that uniquely identifies a Token.

    .. attribute:: password

       The temporary password that the username will use when
       authenticating with Twilio.

    .. attribute:: ttl

       The duration in seconds for which the username and password
       are valid, the default value is 86,400 (24 hours).

    .. attribute:: account_sid

       The unique id of the Account that created this Token.

    .. attribute:: ice_servers

       An array representing the ephemeral credentials and the
       STUN and TURN server URIs.

    .. attribute:: date_created

       The date that this resource was created, given in RFC 2822 format.

    .. attribute:: date_updated

       The date that this resource was last updated, given in RFC 2822 format.
    """
    id_key = "username"


class Tokens(ListResource):
    name = "Tokens"
    key = "tokens"
    instance = Token

    def create(self, ttl=None, **kwargs):
        """
        Create a new Token.

        :param int ttl: The duration in seconds for which the token
            is valid, the default value is 86,400 (24 hours).
        """
        kwargs['ttl'] = ttl
        return self.create_instance(kwargs)
