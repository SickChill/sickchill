from requests.exceptions import HTTPError

from sickchill import logger, settings
from sickchill.oldbeard import helpers

meta_session = helpers.make_session()


def getShowImage(url, imgNum=None):
    if not url:
        return None

    # if they provided a fanart number try to use it instead
    if imgNum is not None:
        tempURL = url.split('-')[0] + "-" + str(imgNum) + ".jpg"
    else:
        tempURL = url

    logger.debug("Fetching image from " + tempURL)

    try:
        image_data = helpers.getURL(tempURL, session=meta_session, returns='content', allow_proxy=settings.PROXY_INDEXERS)
    except HTTPError:
        image_data = None

    if image_data is None:
        logger.warning("There was an error trying to retrieve the image, aborting")
        return

    return image_data
