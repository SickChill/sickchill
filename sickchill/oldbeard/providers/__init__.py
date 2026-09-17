import sys
from random import shuffle
from typing import List, Union

import sickchill.oldbeard.helpers
from sickchill import logger, settings
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
    jackett,
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
    "jackett",
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


def sorted_provider_list(randomize=False, only_enabled=False) -> List[Union[TorrentProvider, NZBProvider, TorrentRssProvider, GenericProvider]]:
    provider_types = List[Union[GenericProvider, TorrentProvider, NZBProvider, TorrentRssProvider]]
    # Built-ins must win on id collisions (e.g. a custom named "Jackett-SC" → jackett_sc).
    provider_dict: dict = {x.get_id(): x for x in (settings.providerList or [])}
    reserved_ids = set(provider_dict)
    for custom in (settings.newznab_provider_list or []) + (settings.torrent_rss_provider_list or []):
        custom_id = custom.get_id()
        if custom_id in reserved_ids:
            logger.warning(
                _(
                    "Custom provider '{name}' uses id '{provider_id}' which conflicts with a built-in provider. "
                    "Rename or remove the custom entry so the built-in provider can be used."
                ).format(name=custom.name, provider_id=custom_id)
            )
            continue
        provider_dict[custom_id] = custom

    new_provider_list: provider_types = []

    # add all modules in the priority list, in order
    for provider_id in settings.PROVIDER_ORDER:
        if provider_id in provider_dict:
            new_provider_list.append(provider_dict[provider_id])

    # add all enabled providers first
    for module in provider_dict.values():
        if module not in new_provider_list and module.is_active:
            new_provider_list.append(module)

    # add any modules that are missing from that list
    for module in provider_dict.values():
        if module not in new_provider_list:
            new_provider_list.append(module)

    if only_enabled:
        new_provider_list = [
            module
            for module in new_provider_list
            if (module.provider_type == GenericProvider.TORRENT and settings.USE_TORRENTS)
            or (module.provider_type == GenericProvider.NZB and settings.USE_NZBS)
        ]

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
    # Prefer built-ins when a custom provider reuses the same id (e.g. Newznab named "Jackett-SC")
    for provider in settings.providerList or []:
        if provider and provider.get_id() == provider_id:
            return provider
    provider_match = [x for x in (settings.newznab_provider_list or []) + (settings.torrent_rss_provider_list or []) if x and x.get_id() == provider_id]
    if len(provider_match) == 1:
        return provider_match[0]
    return None


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
                'No NZB/Torrent providers found or enabled for {searches}.<br/>Please <a href="{web_root}/config/providers/">check your settings</a>.'
            )
            sickchill.oldbeard.helpers.add_site_message(
                formatted_msg.format(searches=searches, web_root=settings.WEB_ROOT), tag="no_providers_enabled", level="danger"
            )
        else:
            sickchill.oldbeard.helpers.remove_site_message(tag="no_providers_enabled")
