import sys
from random import shuffle
from typing import List, Union

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
    torrent911,
    torrent_paradise,
    torrentbytes,
    torrentday,
    torrentleech,
    torrentproject,
    torrentz,
    tvchaosuk,
    xthor,
    yggtorrent,
    zamunda,
)
from sickchill.oldbeard.providers.newznab import NewznabProvider
from sickchill.oldbeard.providers.rsstorrent import TorrentRssProvider
from sickchill.providers.GenericProvider import GenericProvider
from sickchill.providers.nzb.NZBProvider import NZBProvider
from sickchill.providers.torrent.TorrentProvider import TorrentProvider

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
    "torrent911",
    "torrent_paradise",
    "torrentbytes",
    "torrentday",
    "torrentleech",
    "torrentproject",
    "torrentz",
    "tvchaosuk",
    "xthor",
    "yggtorrent",
    "zamunda",
]

broken_providers = [
    # 'torrentz', 'yggtorrent'
]


def sorted_provider_list(randomize=False, only_enabled=False) -> List[Union[TorrentProvider, NZBProvider, TorrentRssProvider, NZBProvider, GenericProvider]]:
    initial_list = settings.providerList + settings.newznab_provider_list + settings.torrent_rss_provider_list

    provider_dict = {x.get_id(): x for x in initial_list}

    new_provider_list = []

    # add all modules in the priority list, in order
    for current_module in settings.PROVIDER_ORDER:
        if current_module in provider_dict:
            new_provider_list.append(provider_dict[current_module])

    # add all enabled providers first
    for current_module in provider_dict:
        if current_module not in new_provider_list and provider_dict[current_module].is_enabled:
            new_provider_list.append(provider_dict[current_module])

    # add any modules that are missing from that list
    for current_module in provider_dict:
        if provider_dict[current_module] not in new_provider_list:
            new_provider_list.append(provider_dict[current_module])

    if only_enabled:
        new_provider_list = [provider for provider in new_provider_list if (provider.provider_type == GenericProvider.TORRENT and settings.USE_TORRENTS) or (provider.provider_type == GenericProvider.NZB and settings.USE_NZBS)]

    if randomize:
        shuffle(new_provider_list)

    return new_provider_list


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
    provider_match = [x for x in settings.providerList + settings.newznab_provider_list + settings.torrent_rss_provider_list if x and x.get_id() == provider_id]

    if len(provider_match) != 1:
        return None
    else:
        return provider_match[0]


def check_enabled_providers():
    if not settings.DEVELOPER:
        backlog_enabled, daily_enabled = False, False
        for provider in sorted_provider_list():
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
