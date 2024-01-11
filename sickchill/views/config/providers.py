import json
import os

from tornado.web import addslash

import sickchill.start
from sickchill import settings
from sickchill.helper import try_int
from sickchill.helper.common import try_float
from sickchill.oldbeard import config, ui
from sickchill.oldbeard.providers.newznab import NewznabProvider
from sickchill.oldbeard.providers.rsstorrent import TorrentRssProvider
from sickchill.providers.GenericProvider import GenericProvider
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

from . import Config


@Route("/config/providers(/?.*)", name="config:providers")
class ConfigProviders(Config):
    @addslash
    def index(self):
        t = PageTemplate(rh=self, filename="config_providers.mako")

        return t.render(
            submenu=self.ConfigMenu(), title=_("Config - Providers"), header=_("Search Providers"), topmenu="config", controller="config", action="providers"
        )

    @staticmethod
    def canAddNewznabProvider(name):
        if not name:
            return json.dumps({"error": "No Provider Name specified"})

        provider_dict = {x.get_id(): x for x in settings.newznab_provider_list}

        provider_id = GenericProvider.make_id(name)

        if provider_id in provider_dict:
            return json.dumps({"error": "Provider Name already exists as " + name})
        else:
            return json.dumps({"success": provider_id})

    @staticmethod
    def getNewznabCategories(name, url, key):
        """
        Retrieves a list of possible categories with category id's
        Using the default url/api?cat
        https://yournewznaburl.com/api?t=caps&apikey=yourapikey
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
        temp_provider = NewznabProvider(name, url, key)

        success, tv_categories, error = temp_provider.get_newznab_categories()

        return json.dumps({"success": success, "tv_categories": tv_categories, "error": error})

    @staticmethod
    def deleteNewznabProvider(nnid):
        provider_dict = {x.get_id(): x for x in settings.newznab_provider_list}
        if nnid not in provider_dict or provider_dict[nnid].default:
            return "0"

        # delete it from the list
        settings.newznab_provider_list.remove(provider_dict[nnid])

        if nnid in settings.PROVIDER_ORDER:
            settings.PROVIDER_ORDER.remove(nnid)

        return "1"

    @staticmethod
    def canAddTorrentRssProvider(name, url, cookies, titleTAG):
        if not name:
            return json.dumps({"error": "Invalid name specified"})

        url = config.clean_url(url)
        temp_provider = TorrentRssProvider(name, url, cookies, titleTAG)

        if temp_provider.get_id() in (x.get_id() for x in settings.torrent_rss_provider_list):
            return json.dumps({"error": "Exists as " + temp_provider.name})
        else:
            (succ, errMsg) = temp_provider.validateRSS()
            if succ:
                return json.dumps({"success": temp_provider.get_id()})
            else:
                return json.dumps({"error": errMsg})

    @staticmethod
    def deleteTorrentRssProvider(provider_id):
        provider_dict = {x.get_id(): x for x in settings.torrent_rss_provider_list}

        if provider_id not in provider_dict:
            return "0"

        # delete it from the list
        settings.torrent_rss_provider_list.remove(provider_dict[provider_id])

        if provider_id in settings.PROVIDER_ORDER:
            settings.PROVIDER_ORDER.remove(provider_id)

        return "1"

    def saveProviders(self):
        newznab_provider_dict = {x.get_id(): x for x in settings.newznab_provider_list}

        finished_names = []

        newznab_string = self.get_body_argument("newznab_string", default="")
        torrent_rss_string = self.get_body_argument("torrent_rss_string", default="")
        provider_order = self.get_body_argument("provider_order", default="")

        print(provider_order)

        for current_newznab_string in newznab_string.split("!!!"):
            if not current_newznab_string:
                continue

            name, url, key, categories = current_newznab_string.split("|")
            url = config.clean_url(url)
            provider_id = GenericProvider.make_id(name)

            # if it does not already exist then add it
            if provider_id not in newznab_provider_dict:
                new_provider = NewznabProvider(name, url, key=key, categories=categories)
                settings.newznab_provider_list.append(new_provider)
                newznab_provider_dict[provider_id] = new_provider

            # set all params
            newznab_provider_dict[provider_id].name = name
            newznab_provider_dict[provider_id].url = url
            newznab_provider_dict[provider_id].key = key
            newznab_provider_dict[provider_id].categories = categories
            # a 0 in the key spot indicates that no key is needed
            newznab_provider_dict[provider_id].needs_auth = key and key != "0"
            newznab_provider_dict[provider_id].search_mode = self.get_body_argument(provider_id + "_search_mode", "episode")
            newznab_provider_dict[provider_id].search_fallback = config.checkbox_to_value(
                self.get_body_argument(provider_id + "search_fallback", 0), value_on=1, value_off=0
            )
            newznab_provider_dict[provider_id].enable_daily = config.checkbox_to_value(
                self.get_body_argument(provider_id + "enable_daily", 0), value_on=1, value_off=0
            )
            newznab_provider_dict[provider_id].enable_backlog = config.checkbox_to_value(
                self.get_body_argument(provider_id + "enable_backlog", 0), value_on=1, value_off=0
            )

            # mark it finished
            finished_names.append(provider_id)

        # delete anything that is in the list that was not processed just now
        if newznab_string:
            for provider in settings.newznab_provider_list:
                if provider.get_id() not in finished_names:
                    settings.newznab_provider_list.remove(provider)
                    del newznab_provider_dict[provider.get_id()]

        torrent_rss_provider_dict = {x.get_id(): x for x in settings.torrent_rss_provider_list}

        finished_names = []

        if torrent_rss_string:
            for current_torrent_rss_provider_string in torrent_rss_string.split("!!!"):
                if not current_torrent_rss_provider_string:
                    continue

                name, url, current_cookies, current_title_tag = current_torrent_rss_provider_string.split("|")
                url = config.clean_url(url)
                provider_id = GenericProvider.make_id(name)

                # if it does not already exist then create it
                if provider_id not in torrent_rss_provider_dict:
                    new_provider = TorrentRssProvider(name, url, current_cookies, current_title_tag)
                    settings.torrent_rss_provider_list.append(new_provider)
                    torrent_rss_provider_dict[provider_id] = new_provider

                # update values
                torrent_rss_provider_dict[provider_id].name = name
                torrent_rss_provider_dict[provider_id].url = url
                torrent_rss_provider_dict[provider_id].cookies = current_cookies
                torrent_rss_provider_dict[provider_id].current_title_tag = current_title_tag

                # mark it finished
                finished_names.append(provider_id)

        # delete anything that is in the list that was not processed just now
        if torrent_rss_string:
            for provider in settings.torrent_rss_provider_list:
                if provider.get_id() not in finished_names:
                    settings.torrent_rss_provider_list.remove(provider)
                    del torrent_rss_provider_dict[provider.get_id()]

        # do the enable/disable
        enabled_provider_list = []
        disabled_provider_list = []

        for provider_id, enabled in (provider.split(":") for provider in provider_order.split()):
            enabled = bool(try_int(enabled))

            current_provider_object = [x for x in sickchill.oldbeard.providers.sorted_provider_list() if x.get_id() == provider_id and hasattr(x, "enabled")]

            if current_provider_object:
                current_provider_object[0].enabled = enabled

            if enabled:
                enabled_provider_list.append(provider_id)
            else:
                disabled_provider_list.append(provider_id)

            if provider_id in newznab_provider_dict:
                newznab_provider_dict[provider_id].enabled = enabled
            elif provider_id in torrent_rss_provider_dict:
                torrent_rss_provider_dict[provider_id].enabled = enabled

        # dynamically load provider settings
        for provider in sickchill.oldbeard.providers.sorted_provider_list():
            provider.check_set_option(self, "custom_url")
            provider.check_set_option(self, "cookies")

            provider.check_set_option(self, "minseed", 0, int)
            provider.check_set_option(self, "minleech", 0, int)
            provider.check_set_option(self, "cat", 0, int)
            provider.check_set_option(self, "digest", None)
            provider.check_set_option(self, "hash", None)
            provider.check_set_option(self, "api_key", None, unhide=True)
            provider.check_set_option(self, "username", None, unhide=True)
            provider.check_set_option(self, "password", None, unhide=True)
            provider.check_set_option(self, "passkey", None, unhide=True)
            provider.check_set_option(self, "pin", None, unhide=True)

            provider.check_set_option(self, "confirmed", False, cast=config.checkbox_to_value)
            provider.check_set_option(self, "ranked", False, cast=config.checkbox_to_value)
            provider.check_set_option(self, "engrelease", False, cast=config.checkbox_to_value)
            provider.check_set_option(self, "onlyspasearch", False, cast=config.checkbox_to_value)
            provider.check_set_option(self, "freeleech", False, cast=config.checkbox_to_value)
            provider.check_set_option(self, "search_fallback", False, cast=config.checkbox_to_value)
            provider.check_set_option(self, "enable_daily", False, cast=config.checkbox_to_value)  # fix can_daily
            provider.check_set_option(self, "enable_backlog", False, cast=config.checkbox_to_value)  # fix can_backlog
            provider.check_set_option(self, "subtitle", False, cast=config.checkbox_to_value)

            provider.check_set_option(self, "sorting", "seeders")
            provider.check_set_option(self, "search_mode", "episode")

            provider.check_set_option(self, "ratio", 0, cast=lambda x: max(try_float(x), -1))

        settings.NEWZNAB_DATA = "!!!".join([x.config_string() for x in settings.newznab_provider_list])
        settings.PROVIDER_ORDER = enabled_provider_list + disabled_provider_list

        sickchill.start.save_config()

        # Add a site_message if no providers are enabled for daily and/or backlog
        sickchill.oldbeard.providers.check_enabled_providers()

        ui.notifications.message(_("Configuration Saved"), os.path.join(settings.CONFIG_FILE))

        return self.redirect("/config/providers/")
