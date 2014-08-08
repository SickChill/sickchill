from urllib2 import Request, urlopen, HTTPError, URLError

import base64
from sha import new as sha1

try:
    import json
except ImportError:
    from lib import simplejson as json

def TraktCall(method, api, username=None, password=None, data={}):
    """
    A generic method for communicating with trakt. Uses the method and data provided along
    with the auth info to send the command.

    method: The URL to use at trakt, relative, no leading slash.
    api: The API string to provide to trakt
    username: The username to use when logging in
    password: The unencrypted password to use when logging in

    Returns: A boolean representing success
    """
    #logger.log("trakt: Call method " + method, logger.DEBUG)

    # if the API isn't given then it failed
    if not api:
        return None

    # replace the API string with what we found
    method = method.replace("%API%", api)

    # make the full url
    url = 'https://api.trakt.tv/' + method
    
    # take the URL params and make a json object out of them
    encoded_data = json.JSONEncoder().encode(data)
    
    request = Request(url, encoded_data)

    # if the username isn't given then it failed
    if username and password:
        pwdsha1 = sha1(password).hexdigest()
        base64string = base64.encodestring('%s:%s' % (username, pwdsha1)).replace('\n', '')
        request.add_header("Accept", "*/*")
        request.add_header("User-Agent", "CPython/2.7.5 Unknown/Unknown")
        request.add_header("Authorization", "Basic %s" % base64string)

    # request the URL from trakt and parse the result as json
    try:
        #logger.log("trakt: Calling method http://api.trakt.tv/" + method + ", with data" + encoded_data, logger.DEBUG)
        stream = urlopen(request).read()

        # check if results are valid
        if stream == '[]':
            resp = 'NULL'
        else:
            resp = json.JSONDecoder().decode(stream)

        if ("error" in resp):
            raise Exception(resp["error"])

    except (IOError):
        #logger.log("trakt: Failed calling method", logger.ERROR)
        return None

    #logger.log("trakt: Failed calling method", logger.ERROR)
    return resp