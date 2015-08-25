# Author: Paul Wollaston
#
# This client script allows connection to Deluge Daemon directly, completely
# circumventing the requirement to use the WebUI.

import json
from base64 import b64encode

import sickbeard
from sickbeard import logger
from .generic import GenericClient
from synchronousdeluge import DelugeClient

class DelugeDAPI(GenericClient):

    drpc = None

    def __init__(self, host=None, username=None, password=None):
        super(DelugeDAPI, self).__init__('DelugeD', host, username, password)

    def _get_auth(self):
        if not self.connect():
            return None

        return True

    def connect(self, reconnect = False):
        hostname = self.host.replace("/", "").split(':')

        if not self.drpc or reconnect:
            self.drpc = DelugeRPC(hostname[1], port = hostname[2], username = self.username, password = self.password)

        return self.drpc

    def _add_torrent_uri(self, result):
        label = sickbeard.TORRENT_LABEL
        if result.show.is_anime:
            label = sickbeard.TORRENT_LABEL_ANIME

        options = {
            'add_paused': sickbeard.TORRENT_PAUSED
        }

        remote_torrent = self.drpc.add_torrent_magnet(result.url, options)

        if not remote_torrent:
            return None

        result.hash = remote_torrent

        return remote_torrent

    def _add_torrent_file(self, result):
        label = sickbeard.TORRENT_LABEL
        if result.show.is_anime:
            label = sickbeard.TORRENT_LABEL_ANIME

        if not result.content: result.content = {}

        if not result.content:
            return None

        options = {
            'add_paused': sickbeard.TORRENT_PAUSED
        }

        remote_torrent = self.drpc.add_torrent_file(result.name + '.torrent', result.content, options)

        if not remote_torrent:
            return None

        result.hash = remote_torrent

        return remote_torrent

    def _set_torrent_label(self, result):

        label = sickbeard.TORRENT_LABEL
        if result.show.is_anime:
            label = sickbeard.TORRENT_LABEL_ANIME
        if ' ' in label:
            logger.log(self.name + u': Invalid label. Label must not contain a space', logger.ERROR)
            return False

        if label:
            if self.drpc.set_torrent_label(result.hash, label):
                return True

        return False

    def _set_torrent_ratio(self, result):

        return True

    def _set_torrent_path(self, result):

        path = sickbeard.TORRENT_PATH
        if path:
            if self.drpc.set_torrent_path(result.hash, path):
                return True
        return False

    def _set_torrent_pause(self, result):

        if sickbeard.TORRENT_PAUSED:
            return self.drpc.pause_torrent(result.hash)
        return True

    def testAuthentication(self):
        print "Test Auth"
        if self.connect(True) and self.drpc.test():
            return True, 'Success: Connected and Authenticated'
        else:
            return False, 'Error: Unable to Authenticate!  Please check your config!'

class DelugeRPC(object):

    host = 'localhost'
    port = 58846
    username = None
    password = None
    client = None

    def __init__(self, host = 'localhost', port = 58846, username = None, password = None):
        super(DelugeRPC, self).__init__()

        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def connect(self):
        self.client = DelugeClient()
        self.client.connect(self.host, int(self.port), self.username, self.password)

    def test(self):
        try:
            self.connect()
        except:
            return False
        return True

    def add_torrent_magnet(self, torrent, options):
        torrent_id = False
        try:
            self.connect()
            torrent_id = self.client.core.add_torrent_magnet(torrent, options).get()
            if not torrent_id:
                torrent_id = self._check_torrent(True, torrent)
        except Exception as err:
            print "ERRERR: %s" % err
            return False
        finally:
            if self.client:
                self.disconnect()

        return torrent_id

    def add_torrent_file(self, filename, torrent, options):
        torrent_id = False
        try:
            self.connect()
            torrent_id = self.client.core.add_torrent_file(filename, b64encode(torrent), options).get()
            if not torrent_id:
                torrent_id = self._check_torrent(False, torrent)
        except Exception as err:
            return False
        finally:
            if self.client:
                self.disconnect()

        return torrent_id

    def set_torrent_label(self, torrent_id, label):
        try:
            self.connect()
            self.client.label.set_torrent(torrent_id, label).get()
        except Exception as err:
            logger.log('DelugeD: Failed to set label for torrent: ' + err + ' ' + traceback.format_exc(), logger.ERROR)
            return False
        finally:
            if self.client:
                self.disconnect()
        return True

    def set_torrent_path(self, torrent_id, path):
        try:
            self.connect()
            self.client.core.set_torrent_move_completed_path(torrent_id, path).get()
            self.client.core.set_torrent_move_completed(torrent_id, 1).get()
        except Exception as err:
            logger.log('DelugeD: Failed to set path for torrent: ' + err + ' ' + traceback.format_exc(), logger.ERROR)
            return False
        finally:
            if self.client:
                self.disconnect()
        return True

    def pause_torrent(self, torrent_ids):
        try:
            self.connect()
            self.client.core.pause_torrent(torrent_ids).get()
        except Exception as err:
            logger.log('DelugeD: Failed to pause torrent: ' + err + ' ' + traceback.format_exc(), logger.ERROR)
            return False
        finally:
            if self.client:
                self.disconnect()
        return True

    def disconnect(self):
        self.client.disconnect()

    def _check_torrent(self, magnet, torrent):
        # Torrent not added, check if it already existed.
        if magnet:
            torrent_hash = re.findall('urn:btih:([\w]{32,40})', torrent)[0]
        else:
            info = bdecode(torrent)["info"]
            torrent_hash = sha1(benc(info)).hexdigest()

        # Convert base 32 to hex
        if len(torrent_hash) == 32:
            torrent_hash = b16encode(b32decode(torrent_hash))

        torrent_hash = torrent_hash.lower()
        torrent_check = self.client.core.get_torrent_status(torrent_hash, {}).get()
        if torrent_check['hash']:
            return torrent_hash

        return False

api = DelugeDAPI()
