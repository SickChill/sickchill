import datetime

from sickchill.show.History import History

from . import db
from .common import FAILED, Quality, SNATCHED, SUBTITLED


def _logHistoryItem(action, showid, season, episode, quality, resource, provider, version=-1):
    """
    Insert a history item in DB

    :param action: action taken (snatch, download, etc)
    :param showid: showid this entry is about
    :param season: show season
    :param episode: show episode
    :param quality: media quality
    :param resource: resource used
    :param provider: provider used
    :param version: tracked version of file (defaults to -1)
    """
    logDate = datetime.datetime.today().strftime(History.date_format)

    main_db_con = db.DBConnection()
    main_db_con.action(
        "INSERT INTO history (action, date, showid, season, episode, quality, resource, provider, version) VALUES (?,?,?,?,?,?,?,?,?)",
        [action, logDate, showid, season, episode, quality, resource, provider, version],
    )


def logSnatch(searchResult):
    """
    Log history of snatch

    :param searchResult: search result object
    """
    for curEpObj in searchResult.episodes:

        showid = int(curEpObj.show.indexerid)
        season = int(curEpObj.season)
        episode = int(curEpObj.episode)
        quality = searchResult.quality
        version = searchResult.version

        providerClass = searchResult.provider
        if providerClass is not None:
            provider = providerClass.name
        else:
            provider = "unknown"

        action = Quality.compositeStatus(SNATCHED, searchResult.quality)

        resource = searchResult.name

        _logHistoryItem(action, showid, season, episode, quality, resource, provider, version)


def logDownload(episode, filename, new_ep_quality, release_group=None, version=-1):
    """
    Log history of download

    :param episode: episode of show
    :param filename: file on disk where the download is
    :param new_ep_quality: Quality of download
    :param release_group: Release group
    :param version: Version of file (defaults to -1)
    """
    showid = int(episode.show.indexerid)
    season = int(episode.season)
    epNum = int(episode.episode)

    quality = new_ep_quality

    # store the release group as the provider if possible
    if release_group:
        provider = release_group
    else:
        provider = -1

    action = episode.status

    _logHistoryItem(action, showid, season, epNum, quality, filename, provider, version)


def logSubtitle(showid, season, episode, status, subtitleResult):
    """
    Log download of subtitle

    :param showid: Showid of download
    :param season: Show season
    :param episode: Show episode
    :param status: Status of download
    :param subtitleResult: Result object
    """
    resource = subtitleResult.language.opensubtitles
    provider = subtitleResult.provider_name

    status, quality = Quality.splitCompositeStatus(status)
    action = Quality.compositeStatus(SUBTITLED, quality)

    _logHistoryItem(action, showid, season, episode, quality, resource, provider)


def logFailed(epObj, release, provider=None):
    """
    Log a failed download

    :param epObj: Episode object
    :param release: Release group
    :param provider: Provider used for snatch
    """
    showid = int(epObj.show.indexerid)
    season = int(epObj.season)
    epNum = int(epObj.episode)
    status, quality = Quality.splitCompositeStatus(epObj.status)
    action = Quality.compositeStatus(FAILED, quality)

    _logHistoryItem(action, showid, season, epNum, quality, release, provider)
