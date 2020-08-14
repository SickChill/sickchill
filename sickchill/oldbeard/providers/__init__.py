from random import shuffle

from subliminal.extensions import RegistrableExtensionManager

from sickchill import settings
from sickchill.oldbeard import helpers


manager = RegistrableExtensionManager('sickchill.providers', [
    'hdspace = sickchill.oldbeard.providers.hdspace:Provider',
    'ncore_cc = sickchill.oldbeard.providers.ncore:Provider',
    'tntvillage = sickchill.oldbeard.providers.tntvillage:Provider',
    'rarbg = sickchill.oldbeard.providers.rarbg:Provider',
    'elitetorrent = sickchill.oldbeard.providers.elitetorrent:Provider',
    'hd4free = sickchill.oldbeard.providers.hd4free:Provider',
    'horriblesubs = sickchill.oldbeard.providers.horriblesubs:Provider',
    'limetorrents = sickchill.oldbeard.providers.limetorrents:Provider',
    'cpasbien = sickchill.oldbeard.providers.cpasbien:Provider',
    'bj_share = sickchill.oldbeard.providers.bjshare:Provider',
    'tvchaosuk = sickchill.oldbeard.providers.tvchaosuk:Provider',
    'eztv = sickchill.oldbeard.providers.eztv:Provider',
    'shazbat_tv = sickchill.oldbeard.providers.shazbat:Provider',
    'sceneaccess = sickchill.oldbeard.providers.scc:Provider',
    'thepiratebay = sickchill.oldbeard.providers.thepiratebay:Provider',
    'nyaa = sickchill.oldbeard.providers.nyaa:Provider',
    'bitcannon = sickchill.oldbeard.providers.bitcannon:Provider',
    'magnetdl = sickchill.oldbeard.providers.magnetdl:Provider',
    'hdtorrents_it = sickchill.oldbeard.providers.hdtorrents_it:Provider_IT',
    'skytorrents = sickchill.oldbeard.providers.skytorrents:SkyTorrents',
    'xthor = sickchill.oldbeard.providers.xthor:Provider',
    'norbits = sickchill.oldbeard.providers.norbits:Provider',
    # 'yggtorrent = sickchill.oldbeard.providers.yggtorrent:Provider',
    'torrentbytes = sickchill.oldbeard.providers.torrentbytes:Provider',
    'btn = sickchill.oldbeard.providers.btn:Provider',
    'demonoid = sickchill.oldbeard.providers.demonoid:Provider',
    'tokyotoshokan = sickchill.oldbeard.providers.tokyotoshokan:Provider',
    'speedcd = sickchill.oldbeard.providers.speedcd:Provider',
    'kickasstorrents = sickchill.oldbeard.providers.kat:Provider',
    'scenetime = sickchill.oldbeard.providers.scenetime:Provider',
    'alpharatio = sickchill.oldbeard.providers.alpharatio:Provider',
    'hounddawgs = sickchill.oldbeard.providers.hounddawgs:Provider',
    'hdbits = sickchill.oldbeard.providers.hdbits:Provider',
    'pretome = sickchill.oldbeard.providers.pretome:Provider',
    # 'binsearch = sickchill.oldbeard.providers.binsearch:Provider',
    'morethantv = sickchill.oldbeard.providers.morethantv:Provider',
    # 'torrentz = sickchill.oldbeard.providers.torrentz:Provider',
    'archetorrent = sickchill.oldbeard.providers.archetorrent:Provider',
    'hdtorrents = sickchill.oldbeard.providers.hdtorrents:Provider',
    'immortalseed = sickchill.oldbeard.providers.immortalseed:Provider',
    'ilcorsaronero = sickchill.oldbeard.providers.ilcorsaronero:Provider',
    'iptorrents = sickchill.oldbeard.providers.iptorrents:Provider',
    'torrent9 = sickchill.oldbeard.providers.torrent9:Provider',
    'newpct = sickchill.oldbeard.providers.newpct:Provider',
    'gftracker = sickchill.oldbeard.providers.gftracker:Provider',
    'filelist = sickchill.oldbeard.providers.filelist:Provider',
    'abnormal = sickchill.oldbeard.providers.abnormal:Provider',
    'torrentproject = sickchill.oldbeard.providers.torrentproject:Provider',
    'danishbits = sickchill.oldbeard.providers.danishbits:Provider',
    'omgwtfnzbs = sickchill.oldbeard.providers.omgwtfnzbs:Provider',
    'gimmepeers = sickchill.oldbeard.providers.gimmepeers:Provider',
    'nebulance = sickchill.oldbeard.providers.nebulance:Provider',
    'torrentday = sickchill.oldbeard.providers.torrentday:Provider',
    'torrentleech = sickchill.oldbeard.providers.torrentleech:Provider',
], invoke_on_load=True, propagate_map_exceptions=True)


def sorted_provider_list(randomize=False, active=False, daily=False, backlog=False, public=False, skip=False):
    order = settings.PROVIDER_ORDER
    if randomize:
        shuffle(order)

    manager.extensions.sort(key=lambda x: (order.index(x.name) if x.name in order else 10000, x.obj.name))
    for provider in manager.extensions:
        if active and not provider.obj.is_active:
            continue

        if daily and not (provider.obj.can_daily and provider.obj.daily_enabled):
            continue

        if backlog and not (provider.obj.can_backlog and provider.obj.backlog_enabled):
            continue

        if public and provider.obj.public:
            continue

        if skip and provider.obj.is_skipped:
            continue

        yield provider.obj


def sorted_torrent_provider_list(randomize=False, active=False, daily=False, backlog=False, public=False, skip=False):
    for provider in sorted_provider_list(randomize, active, daily, backlog, public, skip):
        if provider and provider.provider_type == provider.TORRENT:
            yield provider


def sorted_nzb_provider_list(randomize=False, active=False, daily=False, backlog=False, public=False, skip=False, no_newznab=True):
    for provider in sorted_provider_list(randomize, active, daily, backlog, public, skip):
        if provider and provider.provider_type == provider.NZB:
            if no_newznab and provider in settings.newznabProviderList:
                continue
            yield provider


def provider_list():
    for extension in manager.extensions:
        yield extension.obj


def enabled_provider_order():
    return " ".join(provider.get_id(':'+ str(int(provider.is_enabled))) for provider in sorted_provider_list())


def check_enabled_providers():
    if not settings.DEVELOPER:
        def check_attributes_true(extension, attribute_list):
            """
            Method mapped to the extension manager to check if all attributes in attribute_list are true
            @param extension: Stevedore extension instance
            @param attribute_list: list of attributes to check
            @return: Boolean
            """
            return all(getattr(extension.obj, attribute) for attribute in attribute_list)

        daily_enabled = any(manager.map(check_attributes_true, ['is_active', 'can_daily', 'enable_daily']))
        backlog_enabled = any(manager.map(check_attributes_true, ['is_active', 'can_backlog', 'enable_backlog']))
        if not (daily_enabled and backlog_enabled):
            searches = ((_('daily searches and backlog searches'), _('daily searches'))[backlog_enabled],
                        _('backlog searches'))[daily_enabled]
            formatted_msg = _('No NZB/Torrent providers found or enabled for {searches}.<br/>'
                              'Please <a href="{web_root}/config/providers/">check your settings</a>.')
            helpers.add_site_message(formatted_msg.format(searches=searches, web_root=settings.WEB_ROOT),
                                               tag='no_providers_enabled', level='danger')
        else:
            helpers.remove_site_message(tag='no_providers_enabled')
