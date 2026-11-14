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
    seen: set = set()

    # Enabled providers: PROVIDER_ORDER priority, then any other enabled not listed
    for provider_id in settings.PROVIDER_ORDER:
        provider_id = provider_id.split(":", 1)[0] if provider_id else ""
        module = provider_dict.get(provider_id)
        if module is None or not getattr(module, "enabled", False):
            continue
        if provider_id in seen:
            continue
        new_provider_list.append(module)
        seen.add(provider_id)

    for module in provider_dict.values():
        provider_id = module.get_id()
        if provider_id in seen or not getattr(module, "enabled", False):
            continue
        new_provider_list.append(module)
        seen.add(provider_id)

    # Disabled providers: alphabetical by display name after the enabled block
    disabled = [module for module in provider_dict.values() if module.get_id() not in seen]
    disabled.sort(key=lambda provider: (provider.name or provider.get_id() or "").lower())
    new_provider_list.extend(disabled)

    if only_enabled:
        # Media-type filter (USE_NZBS / USE_TORRENTS), not checkbox-enabled
        new_provider_list = [
            module
            for module in new_provider_list
            if (module.provider_type == GenericProvider.TORRENT and settings.USE_TORRENTS)
            or (module.provider_type == GenericProvider.NZB and settings.USE_NZBS)
        ]

    if randomize:
        shuffle(new_provider_list)

    return new_provider_list


# Module name → provider.get_id() when they differ (everyone else uses module name as id).
_PROVIDER_MODULE_TO_ID = {
    "bjshare": "bj_share",
    "jackett": "jackett_sc",
    "kat": "kickasstorrents",
    "scc": "sceneaccess",
    "shazbat": "shazbat_tv",
}
_PROVIDER_ID_TO_MODULE = {pid: mod for mod, pid in _PROVIDER_MODULE_TO_ID.items()}


def provider_id_for_module(module_name: str) -> str:
    return _PROVIDER_MODULE_TO_ID.get(module_name, module_name)


def module_for_provider_id(provider_id: str) -> str | None:
    if provider_id in _PROVIDER_ID_TO_MODULE:
        return _PROVIDER_ID_TO_MODULE[provider_id]
    if provider_id in __all__:
        return provider_id
    return None


def makeProviderList(enabled_ids: set[str] | None = None):
    """
    Construct built-in Provider instances.

    When ``enabled_ids`` is set, only those providers are instantiated (startup).
    Pass ``None`` to load every built-in (Providers config UI).
    """
    # noinspection PyUnresolvedReferences
    providers = []
    for name in __all__:
        if name in broken_providers:
            continue
        if enabled_ids is not None and provider_id_for_module(name) not in enabled_ids:
            continue
        module = getProviderModule(name)
        if module:
            providers.append(module.Provider())
    return providers


def ensure_provider_loaded(provider_id: str):
    """Instantiate a built-in provider and append to providerList if missing."""
    existing = getProviderClass(provider_id)
    if existing is not None:
        return existing
    module_name = module_for_provider_id(provider_id)
    if not module_name or module_name in broken_providers:
        return None
    module = getProviderModule(module_name)
    if not module:
        return None
    provider = module.Provider()
    if settings.providerList is None:
        settings.providerList = []
    settings.providerList.append(provider)
    return provider


def ensure_all_builtin_providers_loaded():
    """Ensure every built-in Provider exists in providerList (for Providers UI)."""
    loaded = {p.get_id() for p in (settings.providerList or []) if p}
    for name in __all__:
        if name in broken_providers:
            continue
        pid = provider_id_for_module(name)
        if pid not in loaded:
            ensure_provider_loaded(pid)


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
