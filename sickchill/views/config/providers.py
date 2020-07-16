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
from sickbeard import config, filters, ui
from sickbeard.providers import newznab, rsstorrent
from sickchill.helper import try_int
from sickchill.providers.GenericProvider import GenericProvider
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

# Local Folder Imports
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

        # Get newznabprovider obj with provided name
        tempProvider = newznab.NewznabProvider(name, url, key)

        success, tv_categories, error = tempProvider.get_newznab_categories()

        return json.dumps({'success': success, 'tv_categories': tv_categories, 'error': error})

    @staticmethod
    def deleteNewznabProvider(nnid):

        providerDict = dict(list(zip((x.get_id() for x in sickbeard.newznabProviderList), sickbeard.newznabProviderList)))

        if nnid not in providerDict or providerDict[nnid].default:
            return '0'

        # delete it from the list
        sickbeard.newznabProviderList.remove(providerDict[nnid])

        if nnid in sickbeard.PROVIDER_ORDER:
            sickbeard.PROVIDER_ORDER.remove(nnid)

        return '1'

    @staticmethod
    def canAddTorrentRssProvider(name, url, cookies, title_tag):

        if not name:
            return json.dumps({'error': 'Invalid name specified'})

        url = config.clean_url(url)
        tempProvider = rsstorrent.TorrentRssProvider(name)

        if tempProvider.get_id() in (x.get_id() for x in sickbeard.torrentRssProviderList):
            return json.dumps({'error': 'Exists as ' + tempProvider.name})

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

        providerDict = dict(
            list(zip((x.get_id() for x in sickbeard.torrentRssProviderList), sickbeard.torrentRssProviderList)))

        if provider_id not in providerDict:
            return '0'

        # delete it from the list
        sickbeard.torrentRssProviderList.remove(providerDict[provider_id])

        if provider_id in sickbeard.PROVIDER_ORDER:
            sickbeard.PROVIDER_ORDER.remove(provider_id)

        return '1'

    def saveProviders(self, newznab_string='', torrentrss_string='', provider_order=None, **kwargs):
        newznabProviderDict = dict(
            list(zip((x.get_id() for x in sickbeard.newznabProviderList), sickbeard.newznabProviderList)))

        finished_names = []

        # add all the newznab info we got into our list
        # if not newznab_string:
        #     logger.debug('No newznab_string passed to saveProviders')

        for curNewznabProviderStr in newznab_string.split('!!!'):
            if not curNewznabProviderStr:
                continue

            cur_name, cur_url, cur_key, cur_cat = curNewznabProviderStr.split('|')
            cur_url = config.clean_url(cur_url)
            cur_id = GenericProvider.make_id(cur_name)

            # if it does not already exist then add it
            if cur_id not in newznabProviderDict:
                new_provider = newznab.NewznabProvider(cur_name, cur_url)
                sickbeard.newznabProviderList.append(new_provider)
                newznabProviderDict[cur_id] = new_provider

            # set all params
            newznabProviderDict[cur_id].config.set_config('name', cur_name)
            newznabProviderDict[cur_id].config.set_config('url', cur_url)
            newznabProviderDict[cur_id].config.set_config('key', cur_key)
            newznabProviderDict[cur_id].config.set_config('catIDs', cur_cat)
            # a 0 in the key spot indicates that no key is needed
            newznabProviderDict[cur_id].config.set_config('needs_auth', cur_key and cur_key != '0')
            newznabProviderDict[cur_id].config.set_config('search_mode', str(kwargs.get(cur_id + '_search_mode', 'eponly')).strip())
            newznabProviderDict[cur_id].config.set_config('search_fallback', config.checkbox_to_value(kwargs.get(cur_id + 'search_fallback', 0), value_on=1, value_off=0))
            newznabProviderDict[cur_id].config.set_config('enable_daily', config.checkbox_to_value(kwargs.get(cur_id + 'enable_daily', 0), value_on=1, value_off=0))
            newznabProviderDict[cur_id].config.set_config('enable_backlog', config.checkbox_to_value(kwargs.get(cur_id + 'enable_backlog', 0), value_on=1, value_off=0))

            # mark it finished
            finished_names.append(cur_id)

        # delete anything that is in the list that was not processed just now
        if newznab_string:
            for curProvider in sickbeard.newznabProviderList:
                if curProvider.get_id() not in finished_names:
                    sickbeard.newznabProviderList.remove(curProvider)
                    del newznabProviderDict[curProvider.get_id()]

        # if not torrentrss_string:
        #     logger.debug('No torrentrss_string passed to saveProviders')

        torrentRssProviderDict = dict(
            list(zip((x.get_id() for x in sickbeard.torrentRssProviderList), sickbeard.torrentRssProviderList)))

        finished_names = []

        if torrentrss_string:
            for curTorrentRssProviderStr in torrentrss_string.split('!!!'):

                if not curTorrentRssProviderStr:
                    continue

                cur_name, cur_url, cur_cookies, cur_title_tag = curTorrentRssProviderStr.split('|')
                cur_url = config.clean_url(cur_url)
                cur_id = GenericProvider.make_id(cur_name)

                # if it does not already exist then create it
                if cur_id not in torrentRssProviderDict:
                    new_provider = rsstorrent.TorrentRssProvider(cur_name, cur_url)
                    sickbeard.torrentRssProviderList.append(new_provider)
                    torrentRssProviderDict[cur_id] = new_provider

                # update values
                torrentRssProviderDict[cur_id].set_config('name', cur_name)
                torrentRssProviderDict[cur_id].set_config('url', cur_url)
                torrentRssProviderDict[cur_id].set_config('cookies', cur_cookies)
                torrentRssProviderDict[cur_id].set_config('cur_title_tag', cur_title_tag)

                # mark it finished
                finished_names.append(cur_id)

        # delete anything that is in the list that was not processed just now
        if torrentrss_string:
            for curProvider in sickbeard.torrentRssProviderList:
                if curProvider.get_id() not in finished_names:
                    sickbeard.torrentRssProviderList.remove(curProvider)
                    del torrentRssProviderDict[curProvider.get_id()]

        # do the enable/disable
        enabled_provider_list = []
        disabled_provider_list = []
        for cur_id, cur_enabled in (cur_provider_str.split(':') for cur_provider_str in provider_order.split()):
            cur_enabled = bool(try_int(cur_enabled))

            cur_provider_obj = [x for x in sickbeard.providers.sortedProviderList() if x.get_id() == cur_id and x.options('enabled')]

            if cur_provider_obj:
                cur_provider_obj[0].set_config('enabled', cur_enabled)

            if cur_enabled:
                enabled_provider_list.append(cur_id)
            else:
                disabled_provider_list.append(cur_id)

            if cur_id in newznabProviderDict:
                newznabProviderDict[cur_id].set_config('enabled', cur_enabled)
            elif cur_id in torrentRssProviderDict:
                torrentRssProviderDict[cur_id].set_config('enabled', cur_enabled)

        # dynamically load provider settings
        for curProvider in sickbeard.providers.sortedProviderList():
            curProvider.set_config('custom_url', str(kwargs.get(curProvider.get_id('_custom_url'), '')).strip())
            curProvider.set_config('minseed', int(str(kwargs.get(curProvider.get_id('_minseed'), 0)).strip()))
            curProvider.set_config('minleech', int(str(kwargs.get(curProvider.get_id('_minleech'), 0)).strip()))
            curProvider.set_config('ratio', str(kwargs.get(curProvider.get_id('_ratio'))).strip())
            curProvider.set_config('api_key', str(kwargs.get(curProvider.get_id('_api_key'), '')).strip() or None)
            curProvider.set_config('username', str(kwargs.get(curProvider.get_id('_username'), '')).strip() or None)
            curProvider.set_config('password', filters.unhide(curProvider.password, str(kwargs.get(curProvider.get_id('_password'), '')).strip()))
            curProvider.set_config('passkey', filters.unhide(curProvider.passkey, str(kwargs.get(curProvider.get_id('_passkey'), '')).strip()))
            curProvider.set_config('pin', filters.unhide(curProvider.pin, str(kwargs.get(curProvider.get_id('_pin'), '')).strip()))
            curProvider.set_config('confirmed', config.checkbox_to_value(kwargs.get(curProvider.get_id('_confirmed'))))
            curProvider.set_config('ranked', config.checkbox_to_value(kwargs.get(curProvider.get_id('_ranked'))))
            curProvider.set_config('engrelease', config.checkbox_to_value(kwargs.get(curProvider.get_id('_engrelease'))))
            curProvider.set_config('onlyspasearch', config.checkbox_to_value(kwargs.get(curProvider.get_id('_onlyspasearch'))))
            curProvider.set_config('sorting', str(kwargs.get(curProvider.get_id('_sorting'), 'seeders')).strip())
            curProvider.set_config('freeleech', config.checkbox_to_value(kwargs.get(curProvider.get_id('_freeleech'))))
            curProvider.set_config('search_mode', str(kwargs.get(curProvider.get_id('_search_mode'), 'eponly')).strip())
            curProvider.set_config('search_fallback', config.checkbox_to_value(kwargs.get(curProvider.get_id('_search_fallback'))))
            curProvider.set_config('enable_daily', curProvider.can_daily and config.checkbox_to_value(kwargs.get(curProvider.get_id('_enable_daily'))))
            curProvider.set_config('enable_backlog', curProvider.can_backlog and config.checkbox_to_value(kwargs.get(curProvider.get_id('_enable_backlog'))))
            curProvider.set_config('cat', int(str(kwargs.get(curProvider.get_id('_cat'), 0)).strip()))
            curProvider.set_config('subtitle', config.checkbox_to_value(kwargs.get(curProvider.get_id('_subtitle'))))
            curProvider.set_config('cookies', str(kwargs.get(curProvider.get_id('_cookies'))).strip())

        sickbeard.PROVIDER_ORDER = enabled_provider_list + disabled_provider_list

        sickbeard.save_config()

        # Add a site_message if no providers are enabled for daily and/or backlog
        sickbeard.providers.check_enabled_providers()

        ui.notifications.message(_('Configuration Saved'), os.path.join(sickbeard.CONFIG_FILE))

        return self.redirect("/config/providers/")
