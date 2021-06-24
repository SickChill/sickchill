#!/usr/bin/python
# -- Content-Encoding: UTF-8 --
"""
Defines a request dispatcher, a HTTP request handler, a HTTP server and a
CGI request handler.

:authors: Josh Marshall, Thomas Calmant
:copyright: Copyright 2020, Thomas Calmant
:license: Apache License 2.0
:version: 0.4.2

..

    Copyright 2020 Thomas Calmant

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

# We use print() in the CGI request handler
from __future__ import print_function

# Standard library
import logging
import socket
import sys
import traceback

try:
    # Python 3
    # pylint: disable=F0401,E0611
    import xmlrpc.server as xmlrpcserver

    # Make sure the module is complete.
    # The "future" package under python2.7 provides an incomplete
    # variant of this package.
    SimpleXMLRPCDispatcher = xmlrpcserver.SimpleXMLRPCDispatcher
    SimpleXMLRPCRequestHandler = xmlrpcserver.SimpleXMLRPCRequestHandler
    CGIXMLRPCRequestHandler = xmlrpcserver.CGIXMLRPCRequestHandler
    resolve_dotted_attribute = xmlrpcserver.resolve_dotted_attribute  # type: ignore  # noqa: E501  # pylint: disable=invalid-name,line-too-long
    import socketserver
except (ImportError, AttributeError):
    # Python 2 or IronPython
    # pylint: disable=F0401,E0611
    import SimpleXMLRPCServer as xmlrpcserver  # type: ignore

    SimpleXMLRPCDispatcher = xmlrpcserver.SimpleXMLRPCDispatcher  # type: ignore  # noqa: E501  # pylint: disable=invalid-name,line-too-long
    SimpleXMLRPCRequestHandler = xmlrpcserver.SimpleXMLRPCRequestHandler  # type: ignore  # noqa: E501  # pylint: disable=invalid-name,line-too-long
    CGIXMLRPCRequestHandler = xmlrpcserver.CGIXMLRPCRequestHandler  # type: ignore  # noqa: E501  # pylint: disable=invalid-name,line-too-long
    resolve_dotted_attribute = xmlrpcserver.resolve_dotted_attribute  # type: ignore  # noqa: E501  # pylint: disable=invalid-name,line-too-long
    import SocketServer as socketserver  # type: ignore

try:
    # Windows
    import fcntl
except ImportError:
    # Other systems
    # pylint: disable=C0103
    fcntl = None  # type: ignore

try:
    # Python with support for Unix socket
    _AF_UNIX = socket.AF_UNIX
except AttributeError:
    # Unix sockets are not supported, use a dummy value
    _AF_UNIX = -1  # type: ignore

# Local modules
from jsonrpclib import Fault
import jsonrpclib.config
import jsonrpclib.utils as utils
import jsonrpclib.threadpool

# ------------------------------------------------------------------------------

# Module version
__version_info__ = (0, 4, 2)
__version__ = ".".join(str(x) for x in __version_info__)

# Documentation strings format
__docformat__ = "restructuredtext en"

# Prepare the logger
_logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------


def get_version(request):
    """
    Computes the JSON-RPC version

    :param request: A request dictionary
    :return: The JSON-RPC version or None
    """
    if "jsonrpc" in request:
        return 2.0
    elif "id" in request:
        return 1.0

    return None


def validate_request(request, json_config):
    """
    Validates the format of a request dictionary

    :param request: A request dictionary
    :param json_config: A JSONRPClib Config instance
    :return: True if the dictionary is valid, else a Fault object
    """
    if not isinstance(request, utils.DictType):
        # Invalid request type
        fault = Fault(
            -32600,
            "Request must be a dict, not {0}".format(type(request).__name__),
            config=json_config,
        )
        _logger.warning("Invalid request content: %s", fault)
        return fault

    # Get the request ID
    rpcid = request.get("id", None)

    # Check request version
    version = get_version(request)
    if not version:
        fault = Fault(
            -32600,
            "Request {0} invalid.".format(request),
            rpcid=rpcid,
            config=json_config,
        )
        _logger.warning("No version in request: %s", fault)
        return fault

    # Default parameters: empty list
    request.setdefault("params", [])

    # Check parameters
    method = request.get("method", None)
    params = request.get("params")
    param_types = (utils.ListType, utils.DictType, utils.TupleType)

    if (
        not method
        or not isinstance(method, utils.STRING_TYPES)
        or not isinstance(params, param_types)
    ):
        # Invalid type of method name or parameters
        fault = Fault(
            -32600,
            "Invalid request parameters or method.",
            rpcid=rpcid,
            config=json_config,
        )
        _logger.warning("Invalid request content: %s", fault)
        return fault

    # Valid request
    return True


# ------------------------------------------------------------------------------


class NoMulticallResult(Exception):
    """
    No result in multicall
    """


class SimpleJSONRPCDispatcher(SimpleXMLRPCDispatcher, object):
    """
    Mix-in class that dispatches JSON-RPC requests.

    This class is used to register JSON-RPC method handlers
    and then to dispatch them. This class doesn't need to be
    instanced directly when used by SimpleJSONRPCServer.
    """

    def __init__(self, encoding=None, config=jsonrpclib.config.DEFAULT):
        """
        Sets up the dispatcher with the given encoding.
        None values are allowed.
        """
        SimpleXMLRPCDispatcher.__init__(
            self, allow_none=True, encoding=encoding or "UTF-8"
        )
        self.json_config = config

        # Notification thread pool
        self.__notification_pool = None

    def set_notification_pool(self, thread_pool):
        """
        Sets the thread pool to use to handle notifications
        """
        self.__notification_pool = thread_pool

    def _unmarshaled_dispatch(self, request, dispatch_method=None):
        """
        Loads the request dictionary (unmarshaled), calls the method(s)
        accordingly and returns a JSON-RPC dictionary (not marshaled)

        :param request: JSON-RPC request dictionary (or list of)
        :param dispatch_method: Custom dispatch method (for method resolution)
        :return: A JSON-RPC dictionary (or an array of) or None if the request
                 was a notification
        :raise NoMulticallResult: No result in batch
        """
        if not request:
            # Invalid request dictionary
            fault = Fault(
                -32600,
                "Request invalid -- no request data.",
                config=self.json_config,
            )
            _logger.warning("Invalid request: %s", fault)
            return fault.dump()

        if isinstance(request, utils.ListType):
            # This SHOULD be a batch, by spec
            responses = []
            for req_entry in request:
                # Validate the request
                result = validate_request(req_entry, self.json_config)
                if isinstance(result, Fault):
                    responses.append(result.dump())
                    continue

                # Call the method
                resp_entry = self._marshaled_single_dispatch(
                    req_entry, dispatch_method
                )

                # Store its result
                if isinstance(resp_entry, Fault):
                    # pylint: disable=E1103
                    responses.append(resp_entry.dump())
                elif resp_entry is not None:
                    responses.append(resp_entry)

            if not responses:
                # No non-None result
                _logger.error("No result in Multicall")
                raise NoMulticallResult("No result")

            return responses

        else:
            # Single call
            result = validate_request(request, self.json_config)
            if isinstance(result, Fault):
                return result.dump()

            # Call the method
            response = self._marshaled_single_dispatch(request, dispatch_method)
            if isinstance(response, Fault):
                # pylint: disable=E1103
                return response.dump()

            return response

    def _marshaled_dispatch(self, data, dispatch_method=None, path=None):
        """
        Parses the request data (marshaled), calls method(s) and returns a
        JSON string (marshaled)

        :param data: A JSON request string
        :param dispatch_method: Custom dispatch method (for method resolution)
        :param path: Unused parameter, to keep compatibility with xmlrpclib
        :return: A JSON-RPC response string (marshaled)
        """
        # Parse the request
        try:
            request = jsonrpclib.loads(data, self.json_config)
        except Exception as ex:
            # Parsing/loading error
            fault = Fault(
                -32700,
                "Request {0} invalid. ({1}:{2})".format(
                    data, type(ex).__name__, ex
                ),
                config=self.json_config,
            )
            _logger.warning("Error parsing request: %s", fault)
            return fault.response()

        # Get the response dictionary
        try:
            response = self._unmarshaled_dispatch(request, dispatch_method)
            if response is not None:
                # Compute the string representation of the dictionary/list
                return jsonrpclib.jdumps(response, self.encoding)
            else:
                # No result (notification)
                return ""
        except NoMulticallResult:
            # Return an empty string (jsonrpclib internal behaviour)
            return ""

    def _marshaled_single_dispatch(self, request, dispatch_method=None):
        """
        Dispatches a single method call

        :param request: A validated request dictionary
        :param dispatch_method: Custom dispatch method (for method resolution)
        :return: A JSON-RPC response dictionary, or None if it was a
                 notification request
        """
        method = request.get("method")
        params = request.get("params")

        # Prepare a request-specific configuration
        if "jsonrpc" not in request and self.json_config.version >= 2:
            # JSON-RPC 1.0 request on a JSON-RPC 2.0
            # => compatibility needed
            config = self.json_config.copy()
            config.version = 1.0
        else:
            # Keep server configuration as is
            config = self.json_config

        # Test if this is a notification request
        is_notification = "id" not in request or request["id"] in (None, "")
        if is_notification and self.__notification_pool is not None:
            # Use the thread pool for notifications
            if dispatch_method is not None:
                self.__notification_pool.enqueue(
                    dispatch_method, method, params
                )
            else:
                self.__notification_pool.enqueue(
                    self._dispatch, method, params, config
                )

            # Return immediately
            return None
        else:
            # Synchronous call
            try:
                # Call the method
                if dispatch_method is not None:
                    response = dispatch_method(method, params)
                else:
                    response = self._dispatch(method, params, config)
            except Exception as ex:
                # Return a fault
                fault = Fault(
                    -32603,
                    "{0}:{1}".format(type(ex).__name__, ex),
                    config=config,
                )
                _logger.error("Error calling method %s: %s", method, fault)
                return fault.dump()

            if is_notification:
                # It's a notification, no result needed
                # Do not use 'not id' as it might be the integer 0
                return None

        # Prepare a JSON-RPC dictionary
        try:
            return jsonrpclib.dump(
                response, rpcid=request["id"], is_response=True, config=config
            )
        except Exception as ex:
            # JSON conversion exception
            fault = Fault(
                -32603, "{0}:{1}".format(type(ex).__name__, ex), config=config
            )
            _logger.error("Error preparing JSON-RPC result: %s", fault)
            return fault.dump()

    def _dispatch(self, method, params, config=None):
        """
        Default method resolver and caller

        :param method: Name of the method to call
        :param params: List of arguments to give to the method
        :param config: Request-specific configuration
        :return: The result of the method
        """
        config = config or self.json_config

        func = None
        try:
            # Look into registered methods
            func = self.funcs[method]
        except KeyError:
            if self.instance is not None:
                # Try with the registered instance
                try:
                    # Instance has a custom dispatcher
                    return getattr(self.instance, "_dispatch")(method, params)
                except AttributeError:
                    # Resolve the method name in the instance
                    try:
                        func = resolve_dotted_attribute(
                            self.instance, method, True
                        )
                    except AttributeError:
                        # Unknown method
                        pass

        if func is not None:
            try:
                # Call the method
                if isinstance(params, utils.ListType):
                    return func(*params)
                else:
                    return func(**params)
            except TypeError as ex:
                # Maybe the parameters are wrong
                fault = Fault(
                    -32602, "Invalid parameters: {0}".format(ex), config=config
                )
                _logger.warning("Invalid call parameters: %s", fault)
                return fault
            except:
                # Method exception
                err_lines = traceback.format_exception(*sys.exc_info())
                trace_string = "{0} | {1}".format(
                    err_lines[-2].splitlines()[0].strip(), err_lines[-1]
                )
                fault = Fault(
                    -32603,
                    "Server error: {0}".format(trace_string),
                    config=config,
                )
                _logger.exception("Server-side exception: %s", fault)
                return fault
        else:
            # Unknown method
            fault = Fault(
                -32601,
                "Method {0} not supported.".format(method),
                config=config,
            )
            _logger.warning("Unknown method: %s", fault)
            return fault


# ------------------------------------------------------------------------------


class SimpleJSONRPCRequestHandler(SimpleXMLRPCRequestHandler):
    """
    HTTP request handler.

    The server that receives the requests must have a json_config member,
    containing a JSONRPClib Config instance
    """

    def do_POST(self):
        """
        Handles POST requests
        """
        if not self.is_rpc_path_valid():
            self.report_404()
            return

        # Retrieve the configuration
        config = getattr(self.server, "json_config", jsonrpclib.config.DEFAULT)

        try:
            # Read the request body
            max_chunk_size = 10 * 1024 * 1024
            size_remaining = int(self.headers["content-length"])
            chunks = []
            while size_remaining:
                chunk_size = min(size_remaining, max_chunk_size)
                raw_chunk = self.rfile.read(chunk_size)
                if not raw_chunk:
                    break
                chunks.append(utils.from_bytes(raw_chunk))
                size_remaining -= len(raw_chunk)
            data = "".join(chunks)

            try:
                # Decode content
                data = self.decode_request_content(data)
                if data is None:
                    # Unknown encoding, response has been sent
                    return
            except AttributeError:
                # Available since Python 2.7
                pass

            # Execute the method
            response = self.server._marshaled_dispatch(
                data, getattr(self, "_dispatch", None), self.path
            )

            # No exception: send a 200 OK
            self.send_response(200)
        except:
            # Exception: send 500 Server Error
            self.send_response(500)
            err_lines = traceback.format_exception(*sys.exc_info())
            trace_string = "{0} | {1}".format(
                err_lines[-2].splitlines()[0].strip(), err_lines[-1]
            )
            fault = jsonrpclib.Fault(
                -32603, "Server error: {0}".format(trace_string), config=config
            )
            _logger.exception("Server-side error: %s", fault)
            response = fault.response()

        if response is None:
            # Avoid to send None
            response = ""

        # Convert the response to the valid string format
        response = utils.to_bytes(response)

        # Send it
        self.send_header("Content-type", config.content_type)
        self.send_header("Content-length", str(len(response)))
        self.end_headers()
        if response:
            self.wfile.write(response)


# ------------------------------------------------------------------------------


class SimpleJSONRPCServer(socketserver.TCPServer, SimpleJSONRPCDispatcher):
    """
    JSON-RPC server (and dispatcher)
    """

    # This simplifies server restart after error
    allow_reuse_address = True

    # pylint: disable=C0103
    def __init__(
        self,
        addr,
        requestHandler=SimpleJSONRPCRequestHandler,
        logRequests=True,
        encoding=None,
        bind_and_activate=True,
        address_family=socket.AF_INET,
        config=jsonrpclib.config.DEFAULT,
    ):
        """
        Sets up the server and the dispatcher

        :param addr: The server listening address
        :param requestHandler: Custom request handler
        :param logRequests: Flag to(de)activate requests logging
        :param encoding: The dispatcher request encoding
        :param bind_and_activate: If True, starts the server immediately
        :param address_family: The server listening address family
        :param config: A JSONRPClib Config instance
        """
        # Set up the dispatcher fields
        SimpleJSONRPCDispatcher.__init__(self, encoding, config)

        # Flag to ease handling of Unix socket mode
        unix_socket = address_family == _AF_UNIX

        # Disable the reuse address flag when in Unix socket mode, or an
        # exception will raise when binding the socket
        self.allow_reuse_address = self.allow_reuse_address and not unix_socket

        # Prepare the server configuration
        self.address_family = address_family
        self.json_config = config

        # logRequests is used by SimpleXMLRPCRequestHandler
        # This must be disabled in Unix socket mode (or an exception will raise
        # at each connection)
        self.logRequests = logRequests and not unix_socket

        # Work on the request handler
        class RequestHandlerWrapper(requestHandler, object):
            """
            Wraps the request handle to have access to the configuration
            """

            def __init__(self, *args, **kwargs):
                """
                Constructs the wrapper after having stored the configuration
                """
                self.config = config

                if unix_socket:
                    # Disable TCP features over Unix socket, or an
                    # "invalid argument" error will raise
                    self.disable_nagle_algorithm = False

                super(RequestHandlerWrapper, self).__init__(*args, **kwargs)

        # Set up the server
        socketserver.TCPServer.__init__(
            self, addr, RequestHandlerWrapper, bind_and_activate
        )

        # Windows-specific
        if fcntl is not None and hasattr(fcntl, "FD_CLOEXEC"):
            flags = fcntl.fcntl(self.fileno(), fcntl.F_GETFD)
            flags |= fcntl.FD_CLOEXEC
            fcntl.fcntl(self.fileno(), fcntl.F_SETFD, flags)


# ------------------------------------------------------------------------------


class PooledJSONRPCServer(SimpleJSONRPCServer, socketserver.ThreadingMixIn):
    """
    JSON-RPC server based on a thread pool
    """

    def __init__(
        self,
        addr,
        requestHandler=SimpleJSONRPCRequestHandler,
        logRequests=True,
        encoding=None,
        bind_and_activate=True,
        address_family=socket.AF_INET,
        config=jsonrpclib.config.DEFAULT,
        thread_pool=None,
    ):
        """
        Sets up the server and the dispatcher

        :param addr: The server listening address
        :param requestHandler: Custom request handler
        :param logRequests: Flag to(de)activate requests logging
        :param encoding: The dispatcher request encoding
        :param bind_and_activate: If True, starts the server immediately
        :param address_family: The server listening address family
        :param config: A JSONRPClib Config instance
        :param thread_pool: A ThreadPool object. The pool must be started.
        """
        # Normalize the thread pool
        if thread_pool is None:
            # Start a thread pool with  30 threads max, 0 thread min
            thread_pool = jsonrpclib.threadpool.ThreadPool(
                30, 0, logname="PooledJSONRPCServer"
            )
            thread_pool.start()

        # Store the thread pool
        self.__request_pool = thread_pool

        # Prepare the server
        SimpleJSONRPCServer.__init__(
            self,
            addr,
            requestHandler,
            logRequests,
            encoding,
            bind_and_activate,
            address_family,
            config,
        )

    def process_request(self, request, client_address):
        """
        Handle a client request: queue it in the thread pool
        """
        self.__request_pool.enqueue(
            self.process_request_thread, request, client_address
        )

    def server_close(self):
        """
        Clean up the server
        """
        SimpleJSONRPCServer.shutdown(self)
        SimpleJSONRPCServer.server_close(self)
        self.__request_pool.stop()


# ------------------------------------------------------------------------------


class CGIJSONRPCRequestHandler(
    SimpleJSONRPCDispatcher, CGIXMLRPCRequestHandler
):
    """
    JSON-RPC CGI handler (and dispatcher)
    """

    def __init__(self, encoding="UTF-8", config=jsonrpclib.config.DEFAULT):
        """
        Sets up the dispatcher

        :param encoding: Dispatcher encoding
        :param config: A JSONRPClib Config instance
        """
        SimpleJSONRPCDispatcher.__init__(self, encoding, config)
        CGIXMLRPCRequestHandler.__init__(self, encoding=encoding)

    def handle_jsonrpc(self, request_text):
        """
        Handle a JSON-RPC request
        """
        try:
            writer = sys.stdout.buffer
        except AttributeError:
            writer = sys.stdout

        response = self._marshaled_dispatch(request_text)
        response = response.encode(self.encoding)
        print("Content-Type:", self.json_config.content_type)
        print("Content-Length:", len(response))
        print()
        sys.stdout.flush()
        writer.write(response)
        writer.flush()

    # XML-RPC alias
    handle_xmlrpc = handle_jsonrpc
