import uuid

from beekeeper import API, VariableHandler, render_variables

from kodipydent.rpctohive import Hive

base_hive = {
    'root': 'http://{hostname}:{port}',
    'variables': {
        'hostname': {
            'type': 'url_replacement'
        },
        'port': {
            'type': 'url_replacement'
        },
        'username': {
            'type': 'http_basic_auth',
            'optional': True,
        },
        'password': {
            'type': 'http_basic_auth',
            'optional': True
        },
        'jsonrpc': {
            'value': '2.0',
            'type': 'json_rpc'
        },
        'request_id': {
            'type': 'json_rpc'
        }
    },
    'endpoints': {
        'rpc': {
            'path': '/jsonrpc',
            'methods': ['POST']
        }
    },
    'objects': {
        'API': {
            'actions': {
                'get': {
                    'endpoint': 'rpc',
                    'method': 'POST',
                    'traverse': ['result'],
                    'variables': {
                        'method': {
                            'value': 'JSONRPC.Introspect',
                            'type': 'json_rpc'
                        }
                    }
                }
            }
        }
    }
}

@VariableHandler('json_rpc')
def rpc_hander(rq, method, jsonrpc, request_id, **values):
    jrpc = {
        'x': {
            'mimetype': 'application/json',
            'value': {
                'id': request_id['value'],
                'method': method['value'],
                'jsonrpc': jsonrpc['value'],
                'params': {name: val['value'] for name, val in values.items()}
            }
        }
    }
    render_variables(rq, 'data', **jrpc)

def random_id_gen():
    return uuid.uuid4().hex

def Kodi(hostname, username='kodi', password=None, port=8080):
    get_rpc = API(
        base_hive,
        hostname=hostname,
        port=port,
        username=username,
        password=password,
        request_id=random_id_gen
    )
    hive = Hive(get_rpc.API.get())
    return API(
        hive,
        hostname=hostname,
        port=port,
        username=username,
        password=password,
        request_id=random_id_gen
    )
