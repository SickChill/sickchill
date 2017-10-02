import time
from .. import jwt
from .taskrouter_config import TaskRouterConfig
from .workflow_config import WorkflowConfig
from .workflow_ruletarget import WorkflowRuleTarget
from .workflow_rule import WorkflowRule

import warnings
warnings.simplefilter('always', DeprecationWarning)

TASK_ROUTER_BASE_URL = 'https://taskrouter.twilio.com'
TASK_ROUTER_BASE_EVENTS_URL = 'https://event-bridge.twilio.com/v1/wschannels'
TASK_ROUTER_VERSION = "v1"

REQUIRED = {'required': True}
OPTIONAL = {'required': False}


def deprecated(func):
    def log_warning(*args, **kwargs):
        # stacklevel = 2 makes the warning refer to the caller of the
        # deprecation rather than the source of deprecation itself
        warnings.warn("Call to deprecated function {0}.".
                      format(func.__name__),
                      stacklevel=2,
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    return log_warning


class TaskRouterCapability(object):
    def __init__(self, account_sid, auth_token, workspace_sid, channel_id):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.policies = []

        self.workspace_sid = workspace_sid
        self.channel_id = channel_id
        self.base_url = "{0}/{1}/Workspaces/{2}".format(TASK_ROUTER_BASE_URL,
                                                        TASK_ROUTER_VERSION,
                                                        workspace_sid)

        # validate the JWT
        self.validate_jwt()

        # add permissions to GET and POST to the event-bridge channel
        self.allow_web_sockets(channel_id)

        # set up resources
        self.setup_resource()

        # add permissions to fetch the instance resource
        self.add_policy(self.resource_url, "GET", True)

    @property
    def channel_prefix(self):
        return self.channel_id[0:2]

    def setup_resource(self):
        if self.channel_prefix == "WS":
            self.resource_url = self.base_url
        elif self.channel_prefix == "WK":
            self.resource_url = self.base_url + "/Workers/" + self.channel_id

            activity_url = self.base_url + "/Activities"
            self.allow(activity_url, "GET")

            tasks_url = self.base_url + "/Tasks/**"
            self.allow(tasks_url, "GET")

            worker_reservations_url = self.resource_url + "/Reservations/**"
            self.allow(worker_reservations_url, "GET")

        elif self.channel_prefix == "WQ":
            self.resource_url = "{0}/TaskQueues/{1}".format(
                self.base_url, self.channel_id)

    def allow_web_sockets(self, channel_id):
        web_socket_url = "{0}/{1}/{2}".format(TASK_ROUTER_BASE_EVENTS_URL,
                                              self.account_sid,
                                              self.channel_id)

        self.policies.append(self.make_policy(web_socket_url, "GET", True))
        self.policies.append(self.make_policy(web_socket_url, "POST", True))

    def validate_jwt(self):
        if self.account_sid is None or self.account_sid[0:2] != "AC":
            raise ValueError('Invalid AccountSid provided: ' +
                             self.account_sid)
        if self.workspace_sid is None or self.workspace_sid[0:2] != "WS":
            raise ValueError('Invalid WorkspaceSid provided: ' +
                             self.workspace_sid)
        if self.channel_id is None:
            raise ValueError('ChannelId not provided')

        if self.channel_prefix != "WS" and self.channel_prefix != "WK" \
                and self.channel_prefix != "WQ":
            raise ValueError('Invalid ChannelId provided: ' + self.channel_id)

    def allow_fetch_subresources(self):
        self.allow(self.resource_url + "/**", "GET")

    def allow_updates(self):
        self.allow(self.resource_url, "POST")

    def allow_updates_subresources(self):
        self.allow(self.resource_url + "/**", "POST")

    def allow_delete(self):
        self.allow(self.resource_url, "DELETE")

    def allow_delete_subresources(self):
        self.allow(self.resource_url + "/**", "DELETE")

    @deprecated
    def allow_worker_fetch_attributes(self):
        if self.channel_prefix != "WK":
            raise ValueError("Deprecated func not applicable to non Worker")
        else:
            self.policies.append(self.make_policy(
                self.resource_url,
                'GET'))

    @deprecated
    def allow_worker_activity_updates(self):
        if self.channel_prefix == "WK":
            self.policies.append(self.make_policy(
                self.resource_url,
                'POST',
                True,
                post_filter={'ActivitySid': REQUIRED}))
        else:
            raise ValueError("Deprecated func not applicable to non Worker")

    @deprecated
    def allow_task_reservation_updates(self):
        if self.channel_prefix == "WK":
            tasks_url = self.base_url + "/Tasks/**"
            self.policies.append(self.make_policy(
                tasks_url,
                'POST',
                True))
        else:
            raise ValueError("Deprecated func not applicable to non Worker")

    def add_policy(self, url, method,
                   allowed, query_filter=None, post_filter=None):

        policy = self.make_policy(url, method,
                                  allowed, query_filter, post_filter)
        self.policies.append(policy)

    def allow(self, url, method, query_filter=None, post_filter=None):
        self.add_policy(url, method, True, query_filter, post_filter)

    def deny(self, url, method, query_filter=None, post_filter=None):
        self.add_policy(url, method, False, query_filter, post_filter)

    def make_policy(self, url, method,
                    allowed=True, query_filter=None, post_filter=None):

        """Create a policy dictionary for the given resource and method.
        :param str url: the resource URL to grant or deny access to
        :param str method: the HTTP method to allow or deny
        :param allowed bool: whether this request is allowed
        :param dict query_filter: specific GET parameter names
            to require or allow
        :param dict post_filter: POST parameter names
            to require or allow
        """

        return {
            'url': url,
            'method': method,
            'allow': allowed,
            'query_filter': query_filter or {},
            'post_filter': post_filter or {}
        }

    def get_resource_url(self):
        return self.resource_url

    def generate_token(self, ttl=3600):
        task_router_attributes = {
            'account_sid': self.account_sid,
            'workspace_sid': self.workspace_sid,
            'channel': self.channel_id
        }

        if self.channel_prefix == "WK":
            task_router_attributes["worker_sid"] = self.channel_id
        elif self.channel_prefix == "WQ":
            task_router_attributes["taskqueue_sid"] = self.channel_id

        return self._generate_token(ttl, task_router_attributes)

    def _generate_token(self, ttl, attributes=None):
        payload = {
            'iss': self.account_sid,
            'exp': int(time.time()) + ttl,
            'version': TASK_ROUTER_VERSION,
            'friendly_name': self.channel_id,
            'policies': self.policies,
        }

        if attributes is not None:
            payload.update(attributes)

        return jwt.encode(payload, self.auth_token, 'HS256')


class TaskRouterWorkerCapability(TaskRouterCapability):
    def __init__(self, account_sid, auth_token, workspace_sid, worker_sid):
        super(TaskRouterWorkerCapability, self).__init__(account_sid,
                                                         auth_token,
                                                         workspace_sid,
                                                         worker_sid)

        self.activity_url = self.base_url + "/Activities"
        self.reservations_url = self.base_url + "/Tasks/**"
        self.worker_reservations_url = self.resource_url + "/Reservations/**"

        # add permissions to fetch the
        # list of activities, tasks, and worker reservations
        self.allow(self.activity_url, "GET")
        self.allow(self.reservations_url, "GET")
        self.allow(self.worker_reservations_url, "GET")

    def setup_resource(self):
        self.resource_url = self.base_url + "/Workers/" + self.channel_id

    def allow_activity_updates(self):
        self.policies.append(self.make_policy(
            self.resource_url,
            'POST',
            True,
            post_filter={'ActivitySid': REQUIRED}))

    def allow_reservation_updates(self):
        self.policies.append(self.make_policy(
            self.reservations_url,
            'POST',
            True))
        self.policies.append(self.make_policy(
            self.worker_reservations_url,
            'POST',
            True))


class TaskRouterTaskQueueCapability(TaskRouterCapability):
    def setup_resource(self):
        self.resource_url = self.base_url + "/TaskQueues/" + self.channel_id


class TaskRouterWorkspaceCapability(TaskRouterCapability):
    def __init__(self, account_sid, auth_token, workspace_sid):
        super(TaskRouterWorkspaceCapability, self).__init__(account_sid,
                                                            auth_token,
                                                            workspace_sid,
                                                            workspace_sid)

    def setup_resource(self):
        self.resource_url = self.base_url
