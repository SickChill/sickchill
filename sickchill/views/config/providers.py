# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.
# Stdlib Imports
import json
import os

# Third Party Imports
from tornado.web import addslash

# First Party Imports
import sickbeard
import sickchill.providers.media.torrent
import sickchill.providers.metadata
from sickbeard import config, filters, ui
from sickchill.helper import try_int
from sickchill.providers.media.GenericProvider import GenericProvider
from sickchill.providers.media.nzb import newznab
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

# Local Folder Imports
from ...providers.media.torrent import rsstorrent
from . import Config


@Route('/config/providers(/?.*)', name='config:providers')
class ConfigProviders(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigProviders, self).__init__(*args, **kwargs)

    @addslash
    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_providers.mako")

        return t.render(submenu=self.ConfigMenu(), title=_('Config - Providers'),
                        header=_('Search Providers'), topmenu='config',
                        controller="config", action="providers")

    @staticmethod
    def canAddNewznabProvider(name):

        if not name:
            return json.dumps({'error': 'No Provider Name specified'})

        providerDict = dict(list(zip((x.get_id() for x in sickbeard.newznabProviderList), sickbeard.newznabProviderList)))

        cur_id = GenericProvider.make_id(name)

        if cur_id in providerDict:
            return json.dumps({'error': 'Provider Name already exists as ' + name})
        else:
            return json.dumps({'success': cur_id})

    @staticmethod
    def getNewznabCategories(name, url, key):
        """
        Retrieves a list of possible categories with category id's
        Using the default url/api?cat
        http://yournewznaburl.com/api?t=caps&apikey=yourapikey
        """
        error = ""

        if not name:
            error += "\n" + _("No Provider Name specified")
        if not url:
            error += "\n" + _("No Provider Url specified")
        if not key:
            error += "\n" + _("No Provider Api key specified")

        if error:
            return json.dumps({'success': False, 'error': error})

        tempProvider = newznab.NewznabProvider(name)
        tempProvider.set_config('url', url)
        tempProvider.set_config('key', key)

        success, tv_categories, error = tempProvider.get_newznab_categories()

        return json.dumps({'success': success, 'tv_categories': tv_categories, 'error': error})

    @staticmethod
    def deleteNewznabProvider(nnid):
        providerDict = dict(list(zip((x.get_id() for x in sickbeard.newznabProviderList), sickbeard.newznabProviderList)))

        if nnid not in providerDict or providerDict[nnid].default:
            return '0'

        if nnid in sickbeard.PROVIDER_ORDER:
            sickbeard.PROVIDER_ORDER.remove(nnid)

        return '1'

    @staticmethod
    def canAddTorrentRssProvider(name, url, cookies, title_tag):

        if not name:
            return json.dumps({'error': 'Invalid name specified'})

        if name in sickbeard.PROVIDER_ORDER:
            return json.dumps({'error': 'Exists as ' + name})

        url = config.clean_url(url)
        tempProvider = rsstorrent.TorrentRssProvider(name)
        tempProvider.set_config('url', config.clean_url(url))
        tempProvider.set_config('cookies', cookies)
        tempProvider.set_config('title_tag', title_tag)

        (succ, errMsg) = tempProvider.validateRSS()
        if succ:
            return json.dumps({'success': tempProvider.get_id()})
        else:
            return json.dumps({'error': errMsg})

    @staticmethod
    def deleteTorrentRssProvider(provider_id):
        if provider_id in sickbeard.PROVIDER_ORDER:
            sickbeard.PROVIDER_ORDER.remove(provider_id)

        return '1'

    def saveProviders(self, newznab_string='', torrentrss_string='', provider_order=None, **kwargs):
        if newznab_string:
            for curNewznabProviderStr in newznab_string.split('!!!'):
                if not curNewznabProviderStr:
                    continue

                cur_name, cur_url, cur_key, cur_cat = curNewznabProviderStr.split('|')
                cur_url = config.clean_url(cur_url)
                cur_id = GenericProvider.make_id(cur_name)

                # if it does not already exist then add it
                provider = newznab.NewznabProvider(cur_name)

                # set all params
                provider.set_config('name', cur_name)
                provider.set_config('url', cur_url)
                provider.set_config('key', cur_key)
                provider.set_config('categories', cur_cat)
                # a 0 in the key spot indicates that no key is needed
                provider.set_config('search_mode', str(kwargs.get(cur_id + '_search_mode', 'eponly')).strip())
                provider.set_config('search_fallback', config.checkbox_to_value(kwargs.get(cur_id + 'search_fallback', 0), value_on=1, value_off=0))
                provider.set_config('daily', config.checkbox_to_value(kwargs.get(cur_id + 'enable_daily', 0), value_on=1, value_off=0))
                provider.set_config('backlog', config.checkbox_to_value(kwargs.get(cur_id + 'enable_backlog', 0), value_on=1, value_off=0))

                # TODO: ADD TO MANAGER

        if torrentrss_string:
            for curTorrentRssProviderStr in torrentrss_string.split('!!!'):
                if not curTorrentRssProviderStr:
                    continue

                cur_name, cur_url, cur_cookies, cur_title_tag = curTorrentRssProviderStr.split('|')
                cur_url = config.clean_url(cur_url)
                provider = rsstorrent.TorrentRssProvider(cur_name)

                # update values
                provider.set_config('name', cur_name)
                provider.set_config('url', cur_url)
                provider.set_config('cookies', cur_cookies)
                provider.set_config('title_tag', cur_title_tag)

                # TODO: ADD TO MANAGER

        # do the enable/disable
        enabled_provider_list = []
        disabled_provider_list = []

        manager = sickchill.providers.media.torrent.providers.extensions
        for cur_id, cur_enabled in (cur_provider_str.split(':') for cur_provider_str in provider_order.split()):
            if cur_id in manager:
                cur_provider_obj = manager[cur_id].plugin()

                cur_enabled = bool(try_int(cur_enabled))

                if cur_provider_obj:
                    cur_provider_obj[0].set_config('enabled', cur_enabled)

                if cur_enabled:
                    enabled_provider_list.append(cur_id)
                else:
                    disabled_provider_list.append(cur_id)

        # dynamically load provider settings
        for curProvider in manager:
            provider = curProvider.plugin()
            provider.set_config('custom_url', str(kwargs.get(provider.get_id('_custom_url'), '')).strip())
            provider.set_config('minseed', int(str(kwargs.get(provider.get_id('_minseed'), 0)).strip()))
            provider.set_config('minleech', int(str(kwargs.get(provider.get_id('_minleech'), 0)).strip()))
            provider.set_config('ratio', str(kwargs.get(provider.get_id('_ratio'))).strip())
            provider.set_config('api_key', str(kwargs.get(provider.get_id('_api_key'), '')).strip() or None)
            provider.set_config('username', str(kwargs.get(provider.get_id('_username'), '')).strip() or None)
            provider.set_config('password', filters.unhide(provider.password, str(kwargs.get(provider.get_id('_password'), '')).strip()))
            provider.set_config('passkey', filters.unhide(provider.passkey, str(kwargs.get(provider.get_id('_passkey'), '')).strip()))
            provider.set_config('pin', filters.unhide(provider.pin, str(kwargs.get(provider.get_id('_pin'), '')).strip()))
            provider.set_config('confirmed', config.checkbox_to_value(kwargs.get(provider.get_id('_confirmed'))))
            provider.set_config('ranked', config.checkbox_to_value(kwargs.get(provider.get_id('_ranked'))))
            provider.set_config('engrelease', config.checkbox_to_value(kwargs.get(provider.get_id('_engrelease'))))
            provider.set_config('onlyspasearch', config.checkbox_to_value(kwargs.get(provider.get_id('_onlyspasearch'))))
            provider.set_config('sorting', str(kwargs.get(provider.get_id('_sorting'), 'seeders')).strip())
            provider.set_config('freeleech', config.checkbox_to_value(kwargs.get(provider.get_id('_freeleech'))))
            provider.set_config('search_mode', str(kwargs.get(provider.get_id('_search_mode'), 'eponly')).strip())
            provider.set_config('search_fallback', config.checkbox_to_value(kwargs.get(provider.get_id('_search_fallback'))))
            provider.set_config('enable_daily', provider.can_daily and config.checkbox_to_value(kwargs.get(provider.get_id('_enable_daily'))))
            provider.set_config('enable_backlog', provider.can_backlog and config.checkbox_to_value(kwargs.get(provider.get_id('_enable_backlog'))))
            provider.set_config('cat', int(str(kwargs.get(provider.get_id('_cat'), 0)).strip()))
            provider.set_config('subtitle', config.checkbox_to_value(kwargs.get(provider.get_id('_subtitle'))))
            provider.set_config('cookies', str(kwargs.get(provider.get_id('_cookies'))).strip())

        sickbeard.PROVIDER_ORDER = enabled_provider_list + disabled_provider_list

        sickbeard.save_config()

        ui.notifications.message(_('Configuration Saved'), os.path.join(sickbeard.CONFIG_FILE))

        return self.redirect("/config/providers/")
