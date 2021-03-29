import datetime
from urllib.parse import urljoin

from sickchill import logger, settings

from . import helpers

session = helpers.make_session()


def sendNZB(nzb):  # pylint:disable=too-many-return-statements, too-many-branches, too-many-statements
    """
    Sends an NZB to SABnzbd via the API.

    :param nzb: The NZBSearchResult object to send to SAB
    """

    category = settings.SAB_CATEGORY
    if nzb.show.is_anime:
        category = settings.SAB_CATEGORY_ANIME

    # if it aired more than 7 days ago, override with the backlog category IDs
    for curEp in nzb.episodes:
        if datetime.date.today() - curEp.airdate > datetime.timedelta(days=7):
            category = settings.SAB_CATEGORY_ANIME_BACKLOG if nzb.show.is_anime else settings.SAB_CATEGORY_BACKLOG

    # set up a dict with the URL params in it
    params = {"output": "json"}
    if settings.SAB_USERNAME:
        params["ma_username"] = settings.SAB_USERNAME
    if settings.SAB_PASSWORD:
        params["ma_password"] = settings.SAB_PASSWORD
    if settings.SAB_APIKEY:
        params["apikey"] = settings.SAB_APIKEY

    if category:
        params["cat"] = category

    if nzb.priority:
        params["priority"] = 2 if settings.SAB_FORCED else 1

    logger.info("Sending NZB to SABnzbd")
    url = urljoin(settings.SAB_HOST, "api")

    if nzb.resultType == "nzb":
        params["mode"] = "addurl"
        params["name"] = nzb.url
        jdata = helpers.getURL(url, params=params, session=session, returns="json", verify=False)
    elif nzb.resultType == "nzbdata":
        params["mode"] = "addfile"
        multiPartParams = {"nzbfile": (nzb.name + ".nzb", nzb.extraInfo[0])}
        jdata = helpers.getURL(url, params=params, file=multiPartParams, session=session, returns="json", verify=False)

    if not jdata:
        logger.info("Error connecting to sab, no data returned")
        return False

    logger.debug("Result text from SAB: {0}".format(jdata))

    result, error_ = _checkSabResponse(jdata)
    return result


def _checkSabResponse(jdata):
    """
    Check response from SAB

    :param jdata: Response from requests api call
    :return: a list of (Boolean, string) which is True if SAB is not reporting an error
    """
    if "error" in jdata:
        logger.exception(jdata["error"])
        return False, jdata["error"]
    else:
        return True, jdata


def getSabAccesMethod(host=None):
    """
    Find out how we should connect to SAB

    :param host: hostname where SAB lives
    :return: (boolean, string) with True if method was successful
    """
    params = {"mode": "auth", "output": "json"}
    url = urljoin(host, "api")
    data = helpers.getURL(url, params=params, session=session, returns="json", verify=False)
    if not data:
        return False, data

    return _checkSabResponse(data)


def testAuthentication(host=None, username=None, password=None, apikey=None):
    """
    Sends a simple API request to SAB to determine if the given connection information is connect

    :param host: The host where SAB is running (incl port)
    :param username: The username to use for the HTTP request
    :param password: The password to use for the HTTP request
    :param apikey: The API key to provide to SAB
    :return: A tuple containing the success boolean and a message
    """

    # build up the URL parameters
    params = {"mode": "queue", "output": "json", "ma_username": username, "ma_password": password, "apikey": apikey}

    url = urljoin(host, "api")

    data = helpers.getURL(url, params=params, session=session, returns="json", verify=False)
    if not data:
        return False, data

    # check the result and determine if it's good or not
    result, sabText = _checkSabResponse(data)
    if not result:
        return False, sabText

    return True, "Success"
