import datetime
import http.client
import xmlrpc.client
from base64 import standard_b64encode

from sickchill import logger, settings
from sickchill.helper.common import try_int
from sickchill.oldbeard.helpers import make_context

from .common import Quality


def sendNZB(nzb, proper=False):
    """
    Sends NZB to NZBGet client

    :param nzb: nzb object
    :param proper: True if this is a Proper download, False if not. Defaults to False
    """
    if not settings.NZBGET_HOST:
        logger.warning("No NZBget host found in configuration. Please configure it.")
        return False

    addToTop = False
    nzbgetprio = 0
    category = settings.NZBGET_CATEGORY
    if nzb.show.is_anime:
        category = settings.NZBGET_CATEGORY_ANIME

    url = "http{0}://{1}:{2}@{3}/xmlrpc".format(
        "s" if settings.NZBGET_USE_HTTPS else "", settings.NZBGET_USERNAME, settings.NZBGET_PASSWORD, settings.NZBGET_HOST
    )

    nzbGetRPC = xmlrpc.client.ServerProxy(url, context=make_context(settings.SSL_VERIFY))
    try:
        if nzbGetRPC.writelog("INFO", "SickChill connected to drop off {0} any moment now.".format(nzb.name + ".nzb")):
            logger.debug("Successfully connected to NZBget")
        else:
            logger.warning("Successfully connected to NZBget, but unable to send a message")

    except http.client.error:
        logger.warning("Please check your NZBget host and port (if it is running). NZBget is not responding to this combination")
        return False

    except xmlrpc.client.ProtocolError as e:
        if e.errmsg == "Unauthorized":
            logger.warning("NZBget username or password is incorrect.")
        else:
            logger.exception("Protocol Error: " + e.errmsg)
        return False

    dupekey = ""
    dupescore = 0
    # if it aired recently make it high priority and generate DupeKey/Score
    for curEp in nzb.episodes:
        if dupekey == "":
            if curEp.show.indexer == 1:
                dupekey = "SickChill-" + str(curEp.show.indexerid)
            elif curEp.show.indexer == 2:
                dupekey = "SickChill-tvr" + str(curEp.show.indexerid)
        dupekey += "-" + str(curEp.season) + "." + str(curEp.episode)
        if datetime.date.today() - curEp.airdate <= datetime.timedelta(days=7):
            addToTop = True
            nzbgetprio = settings.NZBGET_PRIORITY
        else:
            category = settings.NZBGET_CATEGORY_BACKLOG
            if nzb.show.is_anime:
                category = settings.NZBGET_CATEGORY_ANIME_BACKLOG

    if nzb.quality != Quality.UNKNOWN:
        dupescore = nzb.quality * 100
    if proper:
        dupescore += 10

    nzbcontent64 = None
    if nzb.resultType == "nzbdata":
        data = nzb.extraInfo[0]
        nzbcontent64 = standard_b64encode(data)

    logger.info("Sending NZB to NZBget")
    logger.debug("URL: " + url)

    try:
        # Find out if nzbget supports priority (Version 9.0+), old versions beginning with a 0.x will use the old command
        nzbget_version_str = nzbGetRPC.version()
        nzbget_version = try_int(nzbget_version_str[: nzbget_version_str.find(".")])
        if nzbget_version == 0:
            if nzbcontent64:
                nzbget_result = nzbGetRPC.append(nzb.name + ".nzb", category, addToTop, nzbcontent64)
            else:
                if nzb.resultType == "nzb":
                    if not nzb.provider.login():
                        return False

                    data = nzb.provider.get_url(nzb.url, returns="content")
                    if data is None:
                        return False

                    nzbcontent64 = standard_b64encode(data)

                nzbget_result = nzbGetRPC.append(nzb.name + ".nzb", category, addToTop, nzbcontent64)
        elif nzbget_version == 12:
            if nzbcontent64 is not None:
                nzbget_result = nzbGetRPC.append(nzb.name + ".nzb", category, nzbgetprio, False, nzbcontent64, False, dupekey, dupescore, "score")
            else:
                nzbget_result = nzbGetRPC.appendurl(nzb.name + ".nzb", category, nzbgetprio, False, nzb.url, False, dupekey, dupescore, "score")
        # v13+ has a new combined append method that accepts both (url and content)
        # also the return value has changed from boolean to integer
        # (Positive number representing NZBID of the queue item. 0 and negative numbers represent error codes.)
        elif nzbget_version >= 13:
            nzbget_result = (
                nzbGetRPC.append(
                    nzb.name + ".nzb", nzbcontent64 if nzbcontent64 is not None else nzb.url, category, nzbgetprio, False, False, dupekey, dupescore, "score"
                )
                > 0
            )
        else:
            if nzbcontent64 is not None:
                nzbget_result = nzbGetRPC.append(nzb.name + ".nzb", category, nzbgetprio, False, nzbcontent64)
            else:
                nzbget_result = nzbGetRPC.appendurl(nzb.name + ".nzb", category, nzbgetprio, False, nzb.url)

        if nzbget_result:
            logger.debug("NZB sent to NZBget successfully")
            return True
        else:
            logger.warning("NZBget could not add {0} to the queue".format(nzb.name + ".nzb"))
            return False
    except Exception:
        logger.warning("Connect Error to NZBget: could not add {0} to the queue".format(nzb.name + ".nzb"))
        return False
