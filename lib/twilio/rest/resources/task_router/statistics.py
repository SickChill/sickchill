from .. import NextGenInstanceResource, NextGenListResource, transform_params


class StatisticsInstance(NextGenInstanceResource):
    """
    A resource representing collected statistics about TaskRouter
    resources.

    See the `TaskRouter API reference
    <https://www.twilio.com/docs/taskrouter/statistics>_`
    for more information.
    """
    def __init__(self, parent):
        self.parent = parent
        super(StatisticsInstance, self).__init__(
            parent,
            None,
        )


class Statistics(NextGenListResource):
    name = 'Statistics'
    key = 'statistics'
    instance = StatisticsInstance

    def get(self, **kwargs):
        params = transform_params(kwargs)
        _, data = self.request('GET', self.uri, params=params)
        return self.load_instance(data)

    def load_instance(self, data):
        # Overridden because Statistics instances
        # don't contain sids
        instance = self.instance(self)
        instance.load(data)
        return instance
