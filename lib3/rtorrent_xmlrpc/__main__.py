import shlex
from argparse import ArgumentParser
from xmlrpc.client import ServerProxy

from rtorrent_xmlrpc import SCGIServerProxy


ENTER_URI_MSG = 'server uri: '
QUIT_ALIASES = ('exit', 'quit', 'q')


def query_uri():
    try:
        response = None
        while not response:
            response = input(ENTER_URI_MSG).strip()
    except KeyboardInterrupt:
        exit(0)

    return response

def main_loop(server):
    while True:
        try:
            action = input('server> ').strip()
        except KeyboardInterrupt:
            print('')
            continue

        if action:
            method, *args = shlex.split(action)

            if method in QUIT_ALIASES:
                exit(0)

            try:
                response = getattr(server, method)(*args)
            except KeyboardInterrupt:
                print('Cancelled')
                continue
            except Exception as e:
                print('Failed', e)
                continue

            print(response)


parser = ArgumentParser(
    description='rtorrent xmlrpc tool',
    prog='python -m rtorrent_xmlrpc')
parser.add_argument('uri', nargs='?', default=None)

args = parser.parse_args()

uri = args.uri or query_uri()

if uri.startswith('scgi'):
    server = SCGIServerProxy(uri)
else:
    server = ServerProxy(uri)

try:
    client_version = server.system.client_version()
except Exception as e:
    print('Error communicating with server')
    print(e, e.message)

print('Connection with client ({}) is OK'.format(client_version))

main_loop(server)

