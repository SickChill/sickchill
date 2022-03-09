import json
import os

from tornado.web import addslash

import sickchill.start
from sickchill import settings
from sickchill.helper import try_int
from sickchill.oldbeard import config, filters, ui
from sickchill.oldbeard.providers import newznab, rsstorrent
from sickchill.providers.GenericProvider import GenericProvider
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

from . import Config


@Route("/config/providers(/?.*)", name="config:providers")
class ConfigProviders(Config):
    @addslash
    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_providers.mako")

        return t.render(
            submenu=self.ConfigMenu(), title=_("Config - Providers"), header=_("Search Providers"), topmenu="config", controller="config", action="providers"
        )

    @staticmethod
    def canAddNewznabProvider(name):

        if not name:
            return json.dumps({"error": "No Provider Name specified"})

        providerDict = {x.get_id(): x for x in settings.newznabProviderList}

        cur_id = GenericProvider.make_id(name)

        if cur_id in providerDict:
            return json.dumps({"error": "Provider Name already exists as " + name})
        else:
            return json.dumps({"success": cur_id})

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
            return json.dumps({"success": False, "error": error})

        # Get newznabprovider obj with provided name
        tempProvider = newznab.NewznabProvider(name, url, key)

        success, tv_categories, error = tempProvider.get_newznab_categories()

        return json.dumps({"success": success, "tv_categories": tv_categories, "error": error})

    @staticmethod
    def deleteNewznabProvider(nnid):

        providerDict = {x.get_id(): x for x in settings.newznabProviderList}
        if nnid not in providerDict or providerDict[nnid].default:
            return "0"

        # delete it from the list
        settings.newznabProviderList.remove(providerDict[nnid])

        if nnid in settings.PROVIDER_ORDER:
            settings.PROVIDER_ORDER.remove(nnid)

        return "1"

    @staticmethod
    def canAddTorrentRssProvider(name, url, cookies, titleTAG):

        if not name:
            return json.dumps({"error": "Invalid name specified"})

        url = config.clean_url(url)
        tempProvider = rsstorrent.TorrentRssProvider(name, url, cookies, titleTAG)

        if tempProvider.get_id() in (x.get_id() for x in settings.torrentRssProviderList):
            return json.dumps({"error": "Exists as " + tempProvider.name})
        else:
            (succ, errMsg) = tempProvider.validateRSS()
            if succ:
                return json.dumps({"success": tempProvider.get_id()})
            else:
                return json.dumps({"error": errMsg})

    @staticmethod
    def deleteTorrentRssProvider(provider_id):

        providerDict = {x.get_id(): x for x in settings.torrentRssProviderList}

        if provider_id not in providerDict:
            return "0"

        # delete it from the list
        settings.torrentRssProviderList.remove(providerDict[provider_id])

        if provider_id in settings.PROVIDER_ORDER:
            settings.PROVIDER_ORDER.remove(provider_id)

        return "1"

    def saveProviders(self, newznab_string="", torrentrss_string="", provider_order=None, **kwargs):
        newznabProviderDict = {x.get_id(): x for x in settings.newznabProviderList}

        finished_names = []

        # add all the newznab info we got into our list
        # if not newznab_string:
        #     logger.debug('No newznab_string passed to saveProviders')

        for curNewznabProviderStr in newznab_string.split("!!!"):
            if not curNewznabProviderStr:
                continue

            cur_name, cur_url, cur_key, cur_cat = curNewznabProviderStr.split("|")
            cur_url = config.clean_url(cur_url)
            cur_id = GenericProvider.make_id(cur_name)

            # if it does not already exist then add it
            if cur_id not in newznabProviderDict:
                new_provider = newznab.NewznabProvider(cur_name, cur_url, key=cur_key, catIDs=cur_cat)
                settings.newznabProviderList.append(new_provider)
                newznabProviderDict[cur_id] = new_provider

            # set all params
            newznabProviderDict[cur_id].name = cur_name
            newznabProviderDict[cur_id].url = cur_url
            newznabProviderDict[cur_id].key = cur_key
            newznabProviderDict[cur_id].catIDs = cur_cat
            # a 0 in the key spot indicates that no key is needed
            newznabProviderDict[cur_id].needs_auth = cur_key and cur_key != "0"
            newznabProviderDict[cur_id].search_mode = str(kwargs.get(cur_id + "_search_mode", "eponly")).strip()
            newznabProviderDict[cur_id].search_fallback = config.checkbox_to_value(kwargs.get(cur_id + "search_fallback", 0), value_on=1, value_off=0)
            newznabProviderDict[cur_id].enable_daily = config.checkbox_to_value(kwargs.get(cur_id + "enable_daily", 0), value_on=1, value_off=0)
            newznabProviderDict[cur_id].enable_backlog = config.checkbox_to_value(kwargs.get(cur_id + "enable_backlog", 0), value_on=1, value_off=0)

            # mark it finished
            finished_names.append(cur_id)

        # delete anything that is in the list that was not processed just now
        if newznab_string:
            for curProvider in settings.newznabProviderList:
                if curProvider.get_id() not in finished_names:
                    settings.newznabProviderList.remove(curProvider)
                    del newznabProviderDict[curProvider.get_id()]

        # if not torrentrss_string:
        #     logger.debug('No torrentrss_string passed to saveProviders')

        torrentRssProviderDict = {x.get_id(): x for x in settings.torrentRssProviderList}

        finished_names = []

        if torrentrss_string:
            for curTorrentRssProviderStr in torrentrss_string.split("!!!"):

                if not curTorrentRssProviderStr:
                    continue

                cur_name, cur_url, cur_cookies, cur_title_tag = curTorrentRssProviderStr.split("|")
                cur_url = config.clean_url(cur_url)
                cur_id = GenericProvider.make_id(cur_name)

                # if it does not already exist then create it
                if cur_id not in torrentRssProviderDict:
                    new_provider = rsstorrent.TorrentRssProvider(cur_name, cur_url, cur_cookies, cur_title_tag)
                    settings.torrentRssProviderList.append(new_provider)
                    torrentRssProviderDict[cur_id] = new_provider

                # update values
                torrentRssProviderDict[cur_id].name = cur_name
                torrentRssProviderDict[cur_id].url = cur_url
                torrentRssProviderDict[cur_id].cookies = cur_cookies
                torrentRssProviderDict[cur_id].cur_title_tag = cur_title_tag

                # mark it finished
                finished_names.append(cur_id)

        # delete anything that is in the list that was not processed just now
        if torrentrss_string:
            for curProvider in settings.torrentRssProviderList:
                if curProvider.get_id() not in finished_names:
                    settings.torrentRssProviderList.remove(curProvider)
                    del torrentRssProviderDict[curProvider.get_id()]

        # do the enable/disable
        enabled_provider_list = []
        disabled_provider_list = []
        for cur_id, cur_enabled in (cur_provider_str.split(":") for cur_provider_str in provider_order.split()):
            cur_enabled = bool(try_int(cur_enabled))

            cur_provider_obj = [x for x in sickchill.oldbeard.providers.sortedProviderList() if x.get_id() == cur_id and hasattr(x, "enabled")]

            if cur_provider_obj:
                cur_provider_obj[0].enabled = cur_enabled

            if cur_enabled:
                enabled_provider_list.append(cur_id)
            else:
                disabled_provider_list.append(cur_id)

            if cur_id in newznabProviderDict:
                newznabProviderDict[cur_id].enabled = cur_enabled
            elif cur_id in torrentRssProviderDict:
                torrentRssProviderDict[cur_id].enabled = cur_enabled

        # dynamically load provider settings
        for curProvider in sickchill.oldbeard.providers.sortedProviderList():
            if hasattr(curProvider, "custom_url"):
                curProvider.custom_url = str(kwargs.get(curProvider.get_id("_custom_url"), "")).strip()

            if hasattr(curProvider, "minseed"):
                curProvider.minseed = int(str(kwargs.get(curProvider.get_id("_minseed"), 0)).strip())

            if hasattr(curProvider, "minleech"):
                curProvider.minleech = int(str(kwargs.get(curProvider.get_id("_minleech"), 0)).strip())

            if hasattr(curProvider, "ratio"):
                if curProvider.get_id("_ratio") in kwargs:
                    ratio = str(kwargs.get(curProvider.get_id("_ratio"))).strip()
                    if ratio in ("None", None, ""):
                        curProvider.ratio = None
                    else:
                        curProvider.ratio = max(float(ratio), -1)
                else:
                    curProvider.ratio = None

            if hasattr(curProvider, "digest"):
                curProvider.digest = str(kwargs.get(curProvider.get_id("_digest"), "")).strip() or None

            if hasattr(curProvider, "hash"):
                curProvider.hash = str(kwargs.get(curProvider.get_id("_hash"), "")).strip() or None

            if hasattr(curProvider, "api_key"):
                curProvider.api_key = str(kwargs.get(curProvider.get_id("_api_key"), "")).strip() or None

            if hasattr(curProvider, "username"):
                curProvider.username = str(kwargs.get(curProvider.get_id("_username"), "")).strip() or None

            if hasattr(curProvider, "password"):
                curProvider.password = filters.unhide(curProvider.password, str(kwargs.get(curProvider.get_id("_password"), "")).strip())

            if hasattr(curProvider, "passkey"):
                curProvider.passkey = filters.unhide(curProvider.passkey, str(kwargs.get(curProvider.get_id("_passkey"), "")).strip())

            if hasattr(curProvider, "pin"):
                curProvider.pin = filters.unhide(curProvider.pin, str(kwargs.get(curProvider.get_id("_pin"), "")).strip())

            if hasattr(curProvider, "confirmed"):
                curProvider.confirmed = config.checkbox_to_value(kwargs.get(curProvider.get_id("_confirmed")))

            if hasattr(curProvider, "ranked"):
                curProvider.ranked = config.checkbox_to_value(kwargs.get(curProvider.get_id("_ranked")))

            if hasattr(curProvider, "engrelease"):
                curProvider.engrelease = config.checkbox_to_value(kwargs.get(curProvider.get_id("_engrelease")))

            if hasattr(curProvider, "onlyspasearch"):
                curProvider.onlyspasearch = config.checkbox_to_value(kwargs.get(curProvider.get_id("_onlyspasearch")))

            if hasattr(curProvider, "sorting"):
                curProvider.sorting = str(kwargs.get(curProvider.get_id("_sorting"), "seeders")).strip()

            if hasattr(curProvider, "freeleech"):
                curProvider.freeleech = config.checkbox_to_value(kwargs.get(curProvider.get_id("_freeleech")))

            if hasattr(curProvider, "search_mode"):
                curProvider.search_mode = str(kwargs.get(curProvider.get_id("_search_mode"), "eponly")).strip()

            if hasattr(curProvider, "search_fallback"):
                curProvider.search_fallback = config.checkbox_to_value(kwargs.get(curProvider.get_id("_search_fallback")))

            if hasattr(curProvider, "enable_daily"):
                curProvider.enable_daily = curProvider.can_daily and config.checkbox_to_value(kwargs.get(curProvider.get_id("_enable_daily")))

            if hasattr(curProvider, "enable_backlog"):
                curProvider.enable_backlog = curProvider.can_backlog and config.checkbox_to_value(kwargs.get(curProvider.get_id("_enable_backlog")))

            if hasattr(curProvider, "cat"):
                curProvider.cat = int(str(kwargs.get(curProvider.get_id("_cat"), 0)).strip())

            if hasattr(curProvider, "subtitle"):
                curProvider.subtitle = config.checkbox_to_value(kwargs.get(curProvider.get_id("_subtitle")))

            if curProvider.enable_cookies:
                curProvider.cookies = str(kwargs.get(curProvider.get_id("_cookies"))).strip()

        settings.NEWZNAB_DATA = "!!!".join([x.configStr() for x in settings.newznabProviderList])
        settings.PROVIDER_ORDER = enabled_provider_list + disabled_provider_list

        sickchill.start.save_config()

        # Add a site_message if no providers are enabled for daily and/or backlog
        sickchill.oldbeard.providers.check_enabled_providers()

        ui.notifications.message(_("Configuration Saved"), os.path.join(settings.CONFIG_FILE))

        return self.redirect("/config/providers/")
