from __future__ import annotations

import sys
from unittest.mock import Mock, patch

from sickchill import settings
from sickchill.oldbeard.event_queue import Events
from sickchill.views.server_settings import SCWebServer


def test_web_server_shutdown_stops_the_serving_ioloop():
    server = SCWebServer.__new__(SCWebServer)
    server.alive = True
    http_server = Mock()
    ioloop = Mock()
    server.server = http_server
    server.ioloop = ioloop

    server.shutdown()

    assert server.alive is False
    ioloop.add_callback.assert_called_once_with(server._stop_serving)
    ioloop.stop.assert_not_called()
    http_server.stop.assert_not_called()

    server._stop_serving()

    http_server.stop.assert_called_once_with()
    ioloop.stop.assert_called_once_with()
    assert server.server is None


@patch("sickchill.views.server_settings.IOLoop")
@patch("sickchill.views.server_settings.logger")
def test_run_honors_shutdown_requested_before_ioloop(_logger, ioloop_cls):
    listener = Mock()
    ioloop = Mock()
    ioloop_cls.current.return_value = ioloop

    server = SCWebServer.__new__(SCWebServer)
    server.alive = True
    server.enable_https = False
    server.options = {"host": "127.0.0.1", "port": 8081}
    server.app = Mock()
    server.app.listen.return_value = listener
    server.server = None
    server.ioloop = None

    server.shutdown()
    server.run()

    server.app.listen.assert_called_once()
    listener.stop.assert_called_once_with()
    ioloop.start.assert_not_called()
    ioloop.stop.assert_called_once_with()
    ioloop.close.assert_called_once_with(True)
    assert server.server is None
    assert server.alive is False


def _restore_restart_settings(started, no_restart, fullname, args):
    settings.started = started
    settings.NO_RESTART = no_restart
    settings.MY_FULLNAME = fullname
    settings.MY_ARGS = args


@patch("SickChill.os._exit")
@patch("SickChill.subprocess.Popen")
@patch("SickChill.remove_pid_file")
@patch("SickChill.logger")
@patch("sickchill.start.save_all")
@patch("sickchill.start.halt")
def test_restart_spawns_after_web_server_stops(halt, save_all, logger, remove_pid_file, popen, exit_fn):
    from SickChill import SickChill

    saved = (settings.started, settings.NO_RESTART, settings.MY_FULLNAME, settings.MY_ARGS)
    settings.started = {"0": True}
    settings.NO_RESTART = False
    settings.MY_FULLNAME = "/opt/sickchill/SickChill.py"
    settings.MY_ARGS = ["--datadir=/data"]
    try:
        app = SickChill.__new__(SickChill)
        app.web_server = Mock()
        app.web_server.is_alive.return_value = False
        app.flask_server = None

        app.shutdown(Events.SystemEvent.RESTART)

        halt.assert_called_once_with()
        save_all.assert_called_once_with()
        app.web_server.shutdown.assert_called_once_with()
        app.web_server.join.assert_called_once_with(10)
        popen.assert_called_once()
        args, kwargs = popen.call_args
        assert args[0][:2] == [sys.executable, settings.MY_FULLNAME]
        assert "--datadir=/data" in args[0]
        assert "--nolaunch" in args[0]
        assert kwargs["start_new_session"] is True
        exit_fn.assert_called_once_with(0)
        logger.shutdown.assert_called()
        remove_pid_file.assert_called_once_with()
    finally:
        _restore_restart_settings(*saved)


@patch("SickChill.os._exit")
@patch("SickChill.subprocess.Popen")
@patch("SickChill.remove_pid_file")
@patch("SickChill.logger")
@patch("sickchill.start.save_all")
@patch("sickchill.start.halt")
def test_restart_does_not_spawn_if_web_server_still_running(halt, save_all, logger, remove_pid_file, popen, exit_fn):
    from SickChill import SickChill

    saved = (settings.started, settings.NO_RESTART, settings.MY_FULLNAME, settings.MY_ARGS)
    settings.started = {"0": True}
    settings.NO_RESTART = False
    settings.MY_FULLNAME = "/opt/sickchill/SickChill.py"
    settings.MY_ARGS = []
    try:
        app = SickChill.__new__(SickChill)
        app.web_server = Mock()
        app.web_server.is_alive.return_value = True
        app.flask_server = None

        app.shutdown(Events.SystemEvent.RESTART)

        popen.assert_not_called()
        logger.warning.assert_called()
        exit_fn.assert_called_once_with(0)
        remove_pid_file.assert_called_once_with()
        save_all.assert_called_once_with()
        halt.assert_called_once_with()
    finally:
        _restore_restart_settings(*saved)
