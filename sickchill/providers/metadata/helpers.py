import requests

from sickchill import logger, settings
from sickchill.oldbeard import helpers

meta_session = helpers.make_session()


def getShowImage(url, imgNum=None):
    if not url:
        return None

    # if they provided a fanart number try to use it instead
    if imgNum is not None:
        temp_url = url.split("-")[0] + "-" + str(imgNum) + ".jpg"
    else:
        temp_url = url

    logger.debug("Fetching image from " + temp_url)

    try:
        image_data = helpers.getURL(temp_url, session=meta_session, returns="content", allow_proxy=settings.PROXY_INDEXERS)
    except requests.exceptions.RequestException:
        image_data = None

    if not image_data:
        logger.warning("There was an error trying to retrieve the image, aborting")
        return

    return image_data
