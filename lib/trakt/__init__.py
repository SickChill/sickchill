import hashlib
import requests

def TraktCall(method, api, username=None, password=None, data={}):
    base_url = 'http://api.trakt.tv/'

    # if the API isn't given then it failed
    if not api:
        return None

    # if username and password given then encode password with sha1
    auth = None
    if username and password:
        auth = (username, hashlib.sha1(password.encode('utf-8')).hexdigest())

    # request the URL from trakt and parse the result as json
    try:
        resp = requests.get(base_url + method.replace("%API%", api), auth=auth, data=data).json()
        if isinstance(resp, dict) and resp.get('status', False) == 'failure':
            raise Exception(resp.get('error', 'Unknown Error'))
    except:
        return None

    return resp