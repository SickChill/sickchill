import re
import urlparse
from feedparser.api import parse
from feedparser.util import FeedParserDict

from sickbeard import logger
from sickrage.helper.exceptions import ex

def getFeed(url, request_headers=None, handlers=None):
    parsed = list(urlparse.urlparse(url))
    parsed[2] = re.sub("/{2,}", "/", parsed[2])  # replace two or more / with one

    try:
        feed = parse(url, False, False, request_headers, handlers=handlers)

        if feed:
            if 'entries' in feed:
                return feed
            elif 'error' in feed.feed:
                err_code = feed.feed['error']['code']
                err_desc = feed.feed['error']['description']
                logger.log(u'RSS ERROR:[%s] CODE:[%s]' % (err_desc, err_code), logger.DEBUG)
        else:
            logger.log(u'RSS error loading url: ' + url, logger.DEBUG)

    except Exception as e:
        logger.log(u'RSS error: ' + ex(e), logger.DEBUG)

    return FeedParserDict()
