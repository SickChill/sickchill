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

providers = RegistrableExtensionManager('sickbeard.providers', [
    'hdspace = sickbeard.providers.hdspace:HDSpaceProvider',
    'ncore = sickbeard.providers.ncore:NcoreProvider',
    'tntvillage = sickbeard.providers.tntvillage:TNTVillageProvider',
    'rarbg = sickbeard.providers.rarbg:RarbgProvider',
    'elitetorrent = sickbeard.providers.elitetorrent:EliteTorrentProvider',
    'hd4free = sickbeard.providers.hd4free:HD4FreeProvider',
    'horriblesubs = sickbeard.providers.horriblesubs:HorribleSubsProvider',
    'limetorrents = sickbeard.providers.limetorrents:LimeTorrentsProvider',
    'cpasbien = sickbeard.providers.cpasbien:CpasbienProvider',
    'bjshare = sickbeard.providers.bjshare:BJShareProvider',
    'tvchaosuk = sickbeard.providers.tvchaosuk:TVChaosUKProvider',
    'eztv = sickbeard.providers.eztv:EZTVProvider',
    'shazbat = sickbeard.providers.shazbat:ShazbatProvider',
    'scc = sickbeard.providers.scc:SCCProvider',
    'thepiratebay = sickbeard.providers.thepiratebay:ThePirateBayProvider',
    'nyaa = sickbeard.providers.nyaa:NyaaProvider',
    'bitcannon = sickbeard.providers.bitcannon:BitCannonProvider',
    'magnetdl = sickbeard.providers.magnetdl:MagnetDLProvider',
    'hdtorrents_it = sickbeard.providers.hdtorrents_it:HDTorrentsProvider_IT',
    'skytorrents = sickbeard.providers.skytorrents:SkyTorrents',
    'xthor = sickbeard.providers.xthor:XThorProvider',
    'norbits = sickbeard.providers.norbits:NorbitsProvider',
    'yggtorrent = sickbeard.providers.yggtorrent:YggTorrentProvider',
    'torrentbytes = sickbeard.providers.torrentbytes:TorrentBytesProvider',
    'btn = sickbeard.providers.btn:BTNProvider',
    'demonoid = sickbeard.providers.demonoid:DemonoidProvider',
    'tokyotoshokan = sickbeard.providers.tokyotoshokan:TokyoToshokanProvider',
    'speedcd = sickbeard.providers.speedcd:SpeedCDProvider',
    'kat = sickbeard.providers.kat:KatProvider',
    'scenetime = sickbeard.providers.scenetime:SceneTimeProvider',
    'alpharatio = sickbeard.providers.alpharatio:AlphaRatioProvider',
    'hounddawgs = sickbeard.providers.hounddawgs:HoundDawgsProvider',
    'hdbits = sickbeard.providers.hdbits:HDBitsProvider',
    'pretome = sickbeard.providers.pretome:PretomeProvider',
    'morethantv = sickbeard.providers.morethantv:MoreThanTVProvider',
    'torrentz = sickbeard.providers.torrentz:TorrentzProvider',
    'archetorrent = sickbeard.providers.archetorrent:ArcheTorrentProvider',
    'hdtorrents = sickbeard.providers.hdtorrents:HDTorrentsProvider',
    'immortalseed = sickbeard.providers.immortalseed:ImmortalseedProvider',
    'ilcorsaronero = sickbeard.providers.ilcorsaronero:ilCorsaroNeroProvider',
    'iptorrents = sickbeard.providers.iptorrents:IPTorrentsProvider',
    'torrent9 = sickbeard.providers.torrent9:Torrent9Provider',
    'newpct = sickbeard.providers.newpct:newpctProvider',
    'gftracker = sickbeard.providers.gftracker:GFTrackerProvider',
    'filelist = sickbeard.providers.filelist:FileListProvider',
    'abnormal = sickbeard.providers.abnormal:ABNormalProvider',
    'torrentproject = sickbeard.providers.torrentproject:TorrentProjectProvider',
    'danishbits = sickbeard.providers.danishbits:DanishbitsProvider',
    'omgwtfnzbs = sickbeard.providers.omgwtfnzbs:OmgwtfnzbsProvider',
    'gimmepeers = sickbeard.providers.gimmepeers:GimmePeersProvider',
    'nebulance = sickbeard.providers.nebulance:NebulanceProvider',
    'torrentday = sickbeard.providers.torrentday:TorrentDayProvider',
    'torrentleech = sickbeard.providers.torrentleech:TorrentLeechProvider',
])
