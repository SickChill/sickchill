import urllib2

from hashlib import sha1
 
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

    # if the username isn't given then it failed
    if username and password:
        password = sha1(password).hexdigest()
        data["username"] = username
        data["password"] = password

    # replace the API string with what we found
    method = method.replace("%API%", api)

    # take the URL params and make a json object out of them
    encoded_data = json.dumps(data)

    # request the URL from trakt and parse the result as json
    try:
        #logger.log("trakt: Calling method http://api.trakt.tv/" + method + ", with data" + encoded_data, logger.DEBUG)
        stream = urllib2.urlopen("http://api.trakt.tv/" + method, encoded_data)
        resp = stream.read()

        resp = json.loads(resp)

        if ("error" in resp):
            raise Exception(resp["error"])

    except (IOError):
        #logger.log("trakt: Failed calling method", logger.ERROR)
        return None

    #logger.log("trakt: Failed calling method", logger.ERROR)
    return resp