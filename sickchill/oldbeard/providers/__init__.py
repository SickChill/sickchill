import sys
from random import shuffle

import sickchill.oldbeard.helpers
from sickchill import settings
from sickchill.oldbeard.providers import (
    abnormal,
    alpharatio,
    archetorrent,
    binsearch,
    bitcannon,
    bjshare,
    btn,
    cpasbien,
    danishbits,
    demonoid,
    elitetorrent,
    eztv,
    filelist,
    gimmepeers,
    hd4free,
    hdbits,
    hdspace,
    hdtorrents,
    hdtorrents_it,
    horriblesubs,
    hounddawgs,
    ilcorsaronero,
    immortalseed,
    iptorrents,
    kat,
    limetorrents,
    magnetdl,
    morethantv,
    ncore,
    nebulance,
    newpct,
    norbits,
    nyaa,
    omgwtfnzbs,
    pretome,
    rarbg,
    scc,
    scenetime,
    shazbat,
    skytorrents,
    speedcd,
    thepiratebay,
    tntvillage,
    tokyotoshokan,
    torrent9,
    torrent_paradise,
    torrentbytes,
    torrentday,
    torrentleech,
    torrentproject,
    torrentz,
    tvchaosuk,
    xthor,
    yggtorrent,
)

__all__ = [
    "abnormal",
    "alpharatio",
    "archetorrent",
    "binsearch",
    "bitcannon",
    "bjshare",
    "btn",
    "cpasbien",
    "danishbits",
    "demonoid",
    "elitetorrent",
    "eztv",
    "filelist",
    "gimmepeers",
    "hd4free",
    "hdbits",
    "hdspace",
    "hdtorrents",
    "hdtorrents_it",
    "horriblesubs",
    "hounddawgs",
    "ilcorsaronero",
    "immortalseed",
    "iptorrents",
    "kat",
    "limetorrents",
    "magnetdl",
    "morethantv",
    "ncore",
    "nebulance",
    "newpct",
    "norbits",
    "nyaa",
    "omgwtfnzbs",
    "pretome",
    "rarbg",
    "scc",
    "scenetime",
    "shazbat",
    "skytorrents",
    "speedcd",
    "thepiratebay",
    "tntvillage",
    "tokyotoshokan",
    "torrent9",
    "torrent_paradise",
    "torrentbytes",
    "torrentday",
    "torrentleech",
    "torrentproject",
    "torrentz",
    "tvchaosuk",
    "xthor",
    "yggtorrent",
]

broken_providers = [
    # 'torrentz', 'yggtorrent'
]


def sortedProviderList(randomize=False):
    initialList = settings.providerList + settings.newznabProviderList + settings.torrentRssProviderList
    providerDict = {x.get_id(): x for x in initialList}

    newList = []

    # add all modules in the priority list, in order
    for curModule in settings.PROVIDER_ORDER:
        if curModule in providerDict:
            newList.append(providerDict[curModule])

    # add all enabled providers first
    for curModule in providerDict:
        if providerDict[curModule] not in newList and providerDict[curModule].is_enabled:
            newList.append(providerDict[curModule])

    # add any modules that are missing from that list
    for curModule in providerDict:
        if providerDict[curModule] not in newList:
            newList.append(providerDict[curModule])

    if randomize:
        shuffle(newList)

    return newList


def makeProviderList():
    # noinspection PyUnresolvedReferences
    return [x.Provider() for x in (getProviderModule(y) for y in __all__ if y not in broken_providers) if x]


def getProviderModule(name):
    name = name.lower()
    prefix = "sickchill.oldbeard.providers."
    if name in __all__ and prefix + name in sys.modules:
        return sys.modules[prefix + name]
    else:
        raise Exception("Can't find " + prefix + name + " in " + "Providers")


def getProviderClass(provider_id):
    providerMatch = [x for x in settings.providerList + settings.newznabProviderList + settings.torrentRssProviderList if x and x.get_id() == provider_id]

    if len(providerMatch) != 1:
        return None
    else:
        return providerMatch[0]


def check_enabled_providers():
    if not settings.DEVELOPER:
        backlog_enabled, daily_enabled = False, False
        for provider in sortedProviderList():
            if provider.is_active:
                if provider.enable_daily and provider.can_daily:
                    daily_enabled = True

                if provider.enable_backlog and provider.can_backlog:
                    backlog_enabled = True

                if backlog_enabled and daily_enabled:
                    break

        if not (daily_enabled and backlog_enabled):
            searches = ((_("daily searches and backlog searches"), _("daily searches"))[backlog_enabled], _("backlog searches"))[daily_enabled]
            formatted_msg = _(
                "No NZB/Torrent providers found or enabled for {searches}.<br/>" 'Please <a href="{web_root}/config/providers/">check your settings</a>.'
            )
            sickchill.oldbeard.helpers.add_site_message(
                formatted_msg.format(searches=searches, web_root=settings.WEB_ROOT), tag="no_providers_enabled", level="danger"
            )
        else:
            sickchill.oldbeard.helpers.remove_site_message(tag="no_providers_enabled")
