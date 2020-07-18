# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
#
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
# Third Party Imports
from subliminal.extensions import RegistrableExtensionManager

manager = RegistrableExtensionManager('sickbeard.providers', [
    'hdspace = sickchill.providers.media.torrent.hdspace:HDSpaceProvider',
    'ncore = sickchill.providers.media.torrent.ncore:NcoreProvider',
    'tntvillage = sickchill.providers.media.torrent.tntvillage:TNTVillageProvider',
    'rarbg = sickchill.providers.media.torrent.rarbg:RarbgProvider',
    'elitetorrent = sickchill.providers.media.torrent.elitetorrent:EliteTorrentProvider',
    'hd4free = sickchill.providers.media.torrent.hd4free:HD4FreeProvider',
    'horriblesubs = sickchill.providers.media.torrent.horriblesubs:HorribleSubsProvider',
    'limetorrents = sickchill.providers.media.torrent.limetorrents:LimeTorrentsProvider',
    'cpasbien = sickchill.providers.media.torrent.cpasbien:CpasbienProvider',
    'bjshare = sickchill.providers.media.torrent.bjshare:BJShareProvider',
    'tvchaosuk = sickchill.providers.media.torrent.tvchaosuk:TVChaosUKProvider',
    'eztv = sickchill.providers.media.torrent.eztv:EZTVProvider',
    'shazbat = sickchill.providers.media.torrent.shazbat:ShazbatProvider',
    'scc = sickchill.providers.media.torrent.scc:SCCProvider',
    'thepiratebay = sickchill.providers.media.torrent.thepiratebay:ThePirateBayProvider',
    'nyaa = sickchill.providers.media.torrent.nyaa:NyaaProvider',
    'bitcannon = sickchill.providers.media.torrent.bitcannon:BitCannonProvider',
    'magnetdl = sickchill.providers.media.torrent.magnetdl:MagnetDLProvider',
    'hdtorrents_it = sickchill.providers.media.torrent.hdtorrents_it:HDTorrentsProvider_IT',
    'skytorrents = sickchill.providers.media.torrent.skytorrents:SkyTorrents',
    'xthor = sickchill.providers.media.torrent.xthor:XThorProvider',
    'norbits = sickchill.providers.media.torrent.norbits:NorbitsProvider',
    'yggtorrent = sickchill.providers.media.torrent.yggtorrent:YggTorrentProvider',
    'torrentbytes = sickchill.providers.media.torrent.torrentbytes:TorrentBytesProvider',
    'btn = sickchill.providers.media.torrent.btn:BTNProvider',
    'demonoid = sickchill.providers.media.torrent.demonoid:DemonoidProvider',
    'tokyotoshokan = sickchill.providers.media.torrent.tokyotoshokan:TokyoToshokanProvider',
    'speedcd = sickchill.providers.media.torrent.speedcd:SpeedCDProvider',
    'kat = sickchill.providers.media.torrent.kat:KatProvider',
    'scenetime = sickchill.providers.media.torrent.scenetime:SceneTimeProvider',
    'alpharatio = sickchill.providers.media.torrent.alpharatio:AlphaRatioProvider',
    'hounddawgs = sickchill.providers.media.torrent.hounddawgs:HoundDawgsProvider',
    'hdbits = sickchill.providers.media.torrent.hdbits:HDBitsProvider',
    'pretome = sickchill.providers.media.torrent.pretome:PretomeProvider',
    'morethantv = sickchill.providers.media.torrent.morethantv:MoreThanTVProvider',
    'torrentz = sickchill.providers.media.torrent.torrentz:TorrentzProvider',
    'archetorrent = sickchill.providers.media.torrent.archetorrent:ArcheTorrentProvider',
    'hdtorrents = sickchill.providers.media.torrent.hdtorrents:HDTorrentsProvider',
    'immortalseed = sickchill.providers.media.torrent.immortalseed:ImmortalseedProvider',
    'ilcorsaronero = sickchill.providers.media.torrent.ilcorsaronero:ilCorsaroNeroProvider',
    'iptorrents = sickchill.providers.media.torrent.iptorrents:IPTorrentsProvider',
    'torrent9 = sickchill.providers.media.torrent.torrent9:Torrent9Provider',
    'newpct = sickchill.providers.media.torrent.newpct:newpctProvider',
    'gftracker = sickchill.providers.media.torrent.gftracker:GFTrackerProvider',
    'filelist = sickchill.providers.media.torrent.filelist:FileListProvider',
    'abnormal = sickchill.providers.media.torrent.abnormal:ABNormalProvider',
    'torrentproject = sickchill.providers.media.torrent.torrentproject:TorrentProjectProvider',
    'danishbits = sickchill.providers.media.torrent.danishbits:DanishbitsProvider',
    'omgwtfnzbs = sickchill.providers.media.nzb.omgwtfnzbs:OmgwtfnzbsProvider',
    'gimmepeers = sickchill.providers.media.torrent.gimmepeers:GimmePeersProvider',
    'nebulance = sickchill.providers.media.torrent.nebulance:NebulanceProvider',
    'torrentday = sickchill.providers.media.torrent.torrentday:TorrentDayProvider',
    'torrentleech = sickchill.providers.media.torrent.torrentleech:TorrentLeechProvider',
])


def get_config(provider: str, key: str = ''):
    result = manager[provider].plugin().__config
    if key:
        result = result[key]
    return result


def set_config(provider: str, key: str, value):
    get_config(provider)[key] = value
