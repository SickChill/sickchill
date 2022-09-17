import socket

import gntp.core

from sickchill import logger, settings
from sickchill.oldbeard import common


class Notifier(object):
    def test_notify(self, host, password):
        self._sendRegistration(host, password, "Test")
        return self._sendGrowl("Test Growl", "Testing Growl settings from SickChill", "Test", host, password, force=True)

    def notify_snatch(self, ep_name):
        if settings.GROWL_NOTIFY_ONSNATCH:
            self._sendGrowl(common.notifyStrings[common.NOTIFY_SNATCH], ep_name)

    def notify_download(self, ep_name):
        if settings.GROWL_NOTIFY_ONDOWNLOAD:
            self._sendGrowl(common.notifyStrings[common.NOTIFY_DOWNLOAD], ep_name)

    def notify_subtitle_download(self, ep_name, lang):
        if settings.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._sendGrowl(common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD], ep_name + ": " + lang)

    def notify_update(self, new_version="??"):
        update_text = common.notifyStrings[common.NOTIFY_UPDATE_TEXT]
        title = common.notifyStrings[common.NOTIFY_UPDATE]
        self._sendGrowl(title, update_text + new_version)

    def notify_login(self, ipaddress=""):
        update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
        title = common.notifyStrings[common.NOTIFY_LOGIN]
        self._sendGrowl(title, update_text.format(ipaddress))

    def _send_growl(self, options, message=None):

        # Send Notification
        notice = gntp.core.GNTPNotice()

        # Required
        notice.add_header("Application-Name", options["app"])
        notice.add_header("Notification-Name", options["name"])
        notice.add_header("Notification-Title", options["title"])

        if options["password"]:
            notice.set_password(options["password"])

        # Optional
        if options["sticky"]:
            notice.add_header("Notification-Sticky", options["sticky"])
        if options["priority"]:
            notice.add_header("Notification-Priority", options["priority"])
        if options["icon"]:
            notice.add_header("Notification-Icon", settings.LOGO_URL)

        if message:
            notice.add_header("Notification-Text", message)

        response = self._send(options["host"], options["port"], notice.encode(), options["debug"])
        return True if isinstance(response, gntp.core.GNTPOK) else False

    @staticmethod
    def _send(host, port, data, debug=False):
        if debug:
            print("<Sending>\n", data, "\n</Sending>")

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.send(data)
        response = gntp.core.parse_gntp(s.recv(1024).decode())
        s.close()

        if debug:
            print("<Received>\n", response, "\n</Received>")

        return response

    def _sendGrowl(self, title="SickChill Notification", message=None, name=None, host=None, password=None, force=False):
        if not settings.USE_GROWL and not force:
            return False

        if name is None:
            name = title

        if host is None:
            hostParts = settings.GROWL_HOST.split(":")
        else:
            hostParts = host.split(":")

        if len(hostParts) != 2 or hostParts[1] == "":
            port = 23053
        else:
            port = int(hostParts[1])

        growlHosts = [(hostParts[0], port)]

        opts = {"name": name, "title": title, "app": "SickChill", "sticky": None, "priority": None, "debug": False}

        if password is None:
            opts["password"] = settings.GROWL_PASSWORD
        else:
            opts["password"] = password

        opts["icon"] = True

        for pc in growlHosts:
            opts["host"] = pc[0]
            opts["port"] = pc[1]
            logger.debug("GROWL: Sending message '" + message + "' to " + opts["host"] + ":" + str(opts["port"]))
            try:
                if self._send_growl(opts, message):
                    return True
                else:
                    if self._sendRegistration(host, password, "SickChill"):
                        return self._send_growl(opts, message)
                    else:
                        return False
            except Exception as error:
                logger.warning(f"GROWL: Unable to send growl to {opts['host']}:{opts['port']} - {error}")
                return False

    def _sendRegistration(self, host=None, password=None, name="SickChill Notification"):
        opts = {}

        if host is None:
            hostParts = settings.GROWL_HOST.split(":")
        else:
            hostParts = host.split(":")

        if len(hostParts) != 2 or hostParts[1] == "":
            port = 23053
        else:
            port = int(hostParts[1])

        opts["host"] = hostParts[0]
        opts["port"] = port

        if password is None:
            opts["password"] = settings.GROWL_PASSWORD
        else:
            opts["password"] = password

        opts["app"] = "SickChill"
        opts["debug"] = False

        # Send Registration
        register = gntp.core.GNTPRegister()
        register.add_header("Application-Name", opts["app"])
        register.add_header("Application-Icon", settings.LOGO_URL)

        register.add_notification("Test", True)
        register.add_notification(common.notifyStrings[common.NOTIFY_SNATCH], True)
        register.add_notification(common.notifyStrings[common.NOTIFY_DOWNLOAD], True)
        register.add_notification(common.notifyStrings[common.NOTIFY_UPDATE], True)

        if opts["password"]:
            register.set_password(opts["password"])

        try:
            return self._send(opts["host"], opts["port"], register.encode(), opts["debug"])
        except Exception as error:
            logger.warning(f"GROWL: Unable to send growl to {opts['host']}:{opts['port']} - {error}")
            return False
