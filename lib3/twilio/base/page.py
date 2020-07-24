import json

from twilio.base.exceptions import TwilioException


class Page(object):
    """
    Represents a page of records in a collection.

    A `Page` lets you iterate over its records and fetch the next and previous
    pages in the collection.
    """
    META_KEYS = {
        'end',
        'first_page_uri',
        'next_page_uri',
        'last_page_uri',
        'page',
        'page_size',
        'previous_page_uri',
        'total',
        'num_pages',
        'start',
        'uri'
    }

    def __init__(self, version, response):
        payload = self.process_response(response)

        self._version = version
        self._payload = payload
        self._solution = {}
        self._records = iter(self.load_page(payload))

    def __iter__(self):
        """
        A `Page` is a valid iterator.
        """
        return self

    def __next__(self):
        return self.next()

    def next(self):
        """
        Returns the next record in the `Page`.
        """
        return self.get_instance(next(self._records))

    @classmethod
    def process_response(cls, response):
        """
        Load a JSON response.

        :param Response response: The HTTP response.
        :return dict: The JSON-loaded content.
        """
        if response.status_code != 200:
            raise TwilioException('Unable to fetch page', response)

        return json.loads(response.text)

    def load_page(self, payload):
        """
        Parses the collection of records out of a list payload.

        :param dict payload: The JSON-loaded content.
        :return list: The list of records.
        """
        if 'meta' in payload and 'key' in payload['meta']:
            return payload[payload['meta']['key']]
        else:
            keys = set(payload.keys())
            key = keys - self.META_KEYS
            if len(key) == 1:
                return payload[key.pop()]

        raise TwilioException('Page Records can not be deserialized')

    @property
    def previous_page_url(self):
        """
        :return str: Returns a link to the previous_page_url or None if doesn't exist.
        """
        if 'meta' in self._payload and 'previous_page_url' in self._payload['meta']:
            return self._payload['meta']['previous_page_url']
        elif 'previous_page_uri' in self._payload and self._payload['previous_page_uri']:
            return self._version.domain.absolute_url(self._payload['previous_page_uri'])

        return None

    @property
    def next_page_url(self):
        """
        :return str: Returns a link to the next_page_url or None if doesn't exist.
        """
        if 'meta' in self._payload and 'next_page_url' in self._payload['meta']:
            return self._payload['meta']['next_page_url']
        elif 'next_page_uri' in self._payload and self._payload['next_page_uri']:
            return self._version.domain.absolute_url(self._payload['next_page_uri'])

        return None

    def get_instance(self, payload):
        """
        :param dict payload: A JSON-loaded representation of an instance record.
        :return: A rich, resource-dependent object.
        """
        raise TwilioException('Page.get_instance() must be implemented in the derived class')

    def next_page(self):
        """
        Return the `Page` after this one.
        :return Page: The next page.
        """
        if not self.next_page_url:
            return None

        response = self._version.domain.twilio.request('GET', self.next_page_url)
        cls = type(self)
        return cls(self._version, response, self._solution)

    def previous_page(self):
        """
        Return the `Page` before this one.
        :return Page: The previous page.
        """
        if not self.previous_page_url:
            return None

        response = self._version.domain.twilio.request('GET', self.previous_page_url)
        cls = type(self)
        return cls(self._version, response, self._solution)

    def __repr__(self):
        return '<Page>'
