import json

class Hive(dict):

    def __init__(self, rpc):
        dict.__init__(self)
        self['root'] = 'http://{hostname}:{port}'
        self['objects'] = {}
        self['endpoints'] = {'SingleEndpoint': {'path':'/jsonrpc','methods':['POST']}}
        self['variable_settings'] = {
            'default_type': 'json_rpc',
            'custom_types': {
                'json_rpc': {
                    'description': 'Takes all vars and puts them in a body JSON object'
                }
            }
        }
        self['variables'] = {
            'hostname': {
                'type': 'url_replacement'
            },
            'port': {
                'type': 'url_replacement'
            },
            'jsonrpc': {
                'type': 'json_rpc',
                'value': '2.0'
            },
            'request_id': {
                'type': 'json_rpc'
            },
            'username': {
                'type': 'http_basic_auth',
                'optional': True,
            },
            'password': {
                'type': 'http_basic_auth',
                'optional': True
            }
        }
        for name, method in rpc['methods'].items():
            self.add_method(name, method)

    def add_method(self, name, method):
        obj, action = name.split('.', 1)
        if obj not in self['objects']:
            self['objects'][obj] = {'actions':{}}
        self['objects'][obj]['actions'][action] = Method(name, method)

    def dump(self, file):
        with open(file, 'w') as out:
            json.dump(self, out, indent=4)

class Method(dict):

    def __init__(self, name, method):
        dict.__init__(self)
        self['description'] = method['description']
        self['endpoint'] = 'SingleEndpoint'
        self['method'] = 'POST'
        self['variables'] = Variables(method['params'])
        self['variables']['method'] = {
            'type': 'json_rpc',
            'value': name
        }

class Variables(dict):

    def __init__(self, variables):
        dict.__init__(self)
        for each in variables:
            self.add_var(each)

    def add_var(self, variable):
        out = {}
        if not variable.get('required', False):
            out['optional'] = True
        out['type'] = 'json_rpc'
        if 'default' in variable:
            out['value'] = variable['default']
        if 'description' in variable:
            out['description'] = variable['description']
        self[variable['name']] = out