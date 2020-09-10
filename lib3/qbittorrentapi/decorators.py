import logging
from functools import wraps
from json import loads
from pkg_resources import parse_version

from qbittorrentapi.exceptions import APIError
from qbittorrentapi.exceptions import HTTP403Error

logger = logging.getLogger(__name__)


def _is_version_less_than(ver1, ver2, lteq=True):
    """
    Determine if ver1 is equal to or later than ver2.

    Note: changes need to be reflected in request.Request._is_version_less_than as well

    :param ver1: version to check
    :param ver2: current version of application
    :param lteq: True for Less Than or Equals; False for just Less Than
    :return: True or False
    """
    if lteq:
        return parse_version(ver1) <= parse_version(ver2)
    return parse_version(ver1) < parse_version(ver2)


class Alias(object):

    """
    Alias class that can be used as a decorator for making methods callable
    through other names (or "aliases").
    Note: This decorator must be used inside an @aliased -decorated class.
    For example, if you want to make the method shout() be also callable as
    yell() and scream(), you can use alias like this:

        @alias('yell', 'scream')
        def shout(message):
            # ....
    """

    def __init__(self, *aliases):
        self.aliases = set(aliases)

    def __call__(self, f):
        """
        Method call wrapper. As this decorator has arguments, this method will
        only be called once as a part of the decoration process, receiving only
        one argument: the decorated function ('f'). As a result of this kind of
        decorator, this method must return the callable that will wrap the
        decorated function.
        """
        f._aliases = self.aliases
        return f


def aliased(aliased_class):
    """
    Decorator function that *must* be used in combination with @alias
    decorator. This class will make the magic happen!
    @aliased classes will have their aliased method (via @alias) actually aliased.
    This method simply iterates over the member attributes of 'aliased_class'
    seeking for those which have an '_aliases' attribute and then defines new
    members in the class using those aliases as mere pointer functions to the
    original ones.

    Usage:
        @aliased
        class MyClass(object):
            @alias('coolMethod', 'myKinkyMethod')
            def boring_method():
                # ...

        i = MyClass()
        i.coolMethod() # equivalent to i.myKinkyMethod() and i.boring_method()
    """
    original_methods = aliased_class.__dict__.copy()
    for method in original_methods.values():
        if hasattr(method, '_aliases'):
            # Add the aliases for 'method', but don't override any
            # previously-defined attribute of 'aliased_class'
            # noinspection PyProtectedMember
            for method_alias in method._aliases - set(original_methods):
                setattr(aliased_class, method_alias, method)
    return aliased_class


def login_required(f):
    """Ensure client is logged in before calling API methods."""

    @wraps(f)
    def wrapper(obj, *args, **kwargs):
        if not obj.is_logged_in:
            logger.debug('Not logged in...attempting login')
            obj.auth_log_in()
        try:
            return f(obj, *args, **kwargs)
        except HTTP403Error:
            logger.debug('Login may have expired...attempting new login')
            obj.auth_log_in()

        return f(obj, *args, **kwargs)

    return wrapper


def response_text(response_class):
    """
    Return the UTF-8 encoding of the API response.

    :param response_class: class to cast the response to
    :return: Text of the response casted to the specified class
    """

    def _inner(f):
        @wraps(f)
        def wrapper(obj, *args, **kwargs):
            result = f(obj, *args, **kwargs)
            if isinstance(result, response_class):
                return result
            try:
                return response_class(result.text)
            except Exception:
                logger.debug('Exception during response parsing.', exc_info=True)
                raise APIError('Exception during response parsing')

        return wrapper

    return _inner


def response_json(response_class):

    """
    Return the JSON in the API response. JSON is parsed as instance of response_class.

    :param response_class: class to parse the JSON in to
    :return: JSON as the response class
    """

    def _inner(f):
        @wraps(f)
        def wrapper(obj, *args, **kwargs):
            simple_response = obj._SIMPLE_RESPONSES or kwargs.pop('SIMPLE_RESPONSES', kwargs.pop('SIMPLE_RESPONSE', False))
            response = f(obj, *args, **kwargs)
            try:
                if isinstance(response, response_class):
                    return response
                else:
                    try:
                        result = response.json()
                    except AttributeError:
                        # just in case the requests package is old and doesn't contain json()
                        result = loads(response.text)
                    if simple_response:
                        return result
                    return response_class(result, obj)
            except Exception as e:
                logger.debug('Exception during response parsing.', exc_info=True)
                raise APIError('Exception during response parsing. Error: %s' % repr(e))

        return wrapper

    return _inner


def version_implemented(version_introduced, endpoint, end_point_params=None):
    """
    Prevent hitting an endpoint or sending a parameter if the host doesn't support it.

    :param version_introduced: version endpoint was made available
    :param endpoint: API endpoint (e.g. /torrents/categories)
    :param end_point_params: list of arguments of API call that are version specific
    """

    def _inner(f):
        # noinspection PyProtectedMember
        @wraps(f)
        def wrapper(obj, *args, **kwargs):
            current_version = obj._app_web_api_version_from_version_checker()
            # if the installed version of the API is less than what's required:
            if _is_version_less_than(current_version, version_introduced, lteq=False):
                # clear the unsupported end_point_params
                if end_point_params:
                    parameters_list = end_point_params
                    if not isinstance(end_point_params, list):
                        parameters_list = [end_point_params]
                    # each tuple should be ('python param name', 'api param name')
                    for parameter, api_parameter in [t for t in parameters_list if t[0] in kwargs]:
                        if kwargs[parameter] is None:
                            continue
                        error_message = 'WARNING: Parameter "%s (%s)" for endpoint "%s" is Not Implemented. ' \
                                        'Web API v%s is installed. This endpoint parameter is available starting ' \
                                        'in Web API v%s.' \
                                        % (api_parameter, parameter, endpoint, current_version, version_introduced)
                        logger.debug(error_message)
                        if obj._RAISE_UNIMPLEMENTEDERROR_FOR_UNIMPLEMENTED_API_ENDPOINTS:
                            raise NotImplementedError(error_message)
                        kwargs[parameter] = None
                # or skip running unsupported API calls
                if not end_point_params:
                    error_message = 'ERROR: Endpoint "%s" is Not Implemented. Web API v%s is installed. This endpoint' \
                                    ' is available starting in Web API v%s.' \
                                    % (endpoint, current_version, version_introduced)
                    logger.debug(error_message)
                    if obj._RAISE_UNIMPLEMENTEDERROR_FOR_UNIMPLEMENTED_API_ENDPOINTS:
                        raise NotImplementedError(error_message)
                    return None
            return f(obj, *args, **kwargs)

        return wrapper

    return _inner
