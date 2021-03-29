from feedparser import parse

from .. import logger


def getFeed(url, params=None, request_hook=None):
    try:
        data = request_hook(url, params=params, returns="text", timeout=30)
        if not data:
            raise Exception

        feed = parse(data, response_headers={"content-type": "application/xml"})
        if feed:
            if "entries" in feed:
                return feed
            elif "error" in feed.feed:
                err_code = feed.feed["error"]["code"]
                err_desc = feed.feed["error"]["description"]
                logger.debug("RSS ERROR:[{0}] CODE:[{1}]".format(err_desc, err_code))
        else:
            logger.debug("RSS error loading data: " + url)

    except Exception as e:
        logger.debug("RSS error: " + str(e))

    return {"entries": []}
