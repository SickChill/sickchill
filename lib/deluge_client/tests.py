import os
import sys

import pytest

from .client import DelugeRPCClient, LocalDelugeRPCClient, RemoteException


if sys.version_info > (3,):
    long = int


def client_factory(**kw):
    """Create a disconnected client for test purposes."""
    if sys.platform.startswith('win'):
        auth_path = os.path.join(os.getenv('APPDATA'), 'deluge', 'auth')
    else:
        auth_path = os.path.expanduser("~/.config/deluge/auth")

    with open(auth_path, 'rb') as f:
        filedata = f.read().decode("utf-8").split('\n')[0].split(':')

    username, password = filedata[:2]
    ip = '127.0.0.1'
    port = 58846
    kwargs = {'decode_utf8': True}
    if kw:
        kwargs.update(kw)        
    client = DelugeRPCClient(ip, port, username, password, **kwargs)
    return client


@pytest.fixture
def client(request):
    client = client_factory(**getattr(request, 'param', {}))
    client.connect()
    yield client

    try:
        client.disconnect()
    except:
        pass


def test_connect(client):
    assert client.connected


def test_call_method(client):
    assert isinstance(client.call('core.get_free_space'), (int, long))


def test_call_method_arguments(client):
    assert isinstance(client.call('core.get_free_space', '/'), (int, long))


@pytest.mark.parametrize('client',
                         [{'decode_utf8': True}, {'decode_utf8': False}],
                         ids=['decode_utf8_on', 'decode_utf8_off'],
                         indirect=True)
def test_call_method_exception(client):
    with pytest.raises(RemoteException) as ex_info:
        client.call('core.get_free_space', '1', '2')
    assert ('takes at most 2 arguments' in str(ex_info.value) or
            'takes from 1 to 2 positional arguments' in str(ex_info.value))  # deluge 2.0


def test_attr_caller(client):
    assert isinstance(client.core.get_free_space(), (int, long))
    assert isinstance(client.core.get_free_space('/'), (int, long))


def test_call_method_context_manager():
    with client_factory() as client:
        assert isinstance(client.call('core.get_free_space'), (int, long))


def test_local_client_connect():
    with LocalDelugeRPCClient() as local_client:
        assert local_client.connected


def test_local_client_method():
    with LocalDelugeRPCClient() as local_client:
            assert isinstance(local_client.call('core.get_free_space'), (int, long))
