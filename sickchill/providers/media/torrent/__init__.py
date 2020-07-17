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
    'hdspace = sickchill.providers.torrent.hdspace:HDSpaceProvider',
    'ncore = sickchill.providers.torrent.ncore:NcoreProvider',
    'tntvillage = sickchill.providers.torrent.tntvillage:TNTVillageProvider',
    'rarbg = sickchill.providers.torrent.rarbg:RarbgProvider',
    'elitetorrent = sickchill.providers.torrent.elitetorrent:EliteTorrentProvider',
    'hd4free = sickchill.providers.torrent.hd4free:HD4FreeProvider',
    'horriblesubs = sickchill.providers.torrent.horriblesubs:HorribleSubsProvider',
    'limetorrents = sickchill.providers.torrent.limetorrents:LimeTorrentsProvider',
    'cpasbien = sickchill.providers.torrent.cpasbien:CpasbienProvider',
    'bjshare = sickchill.providers.torrent.bjshare:BJShareProvider',
    'tvchaosuk = sickchill.providers.torrent.tvchaosuk:TVChaosUKProvider',
    'eztv = sickchill.providers.torrent.eztv:EZTVProvider',
    'shazbat = sickchill.providers.torrent.shazbat:ShazbatProvider',
    'scc = sickchill.providers.torrent.scc:SCCProvider',
    'thepiratebay = sickchill.providers.torrent.thepiratebay:ThePirateBayProvider',
    'nyaa = sickchill.providers.torrent.nyaa:NyaaProvider',
    'bitcannon = sickchill.providers.torrent.bitcannon:BitCannonProvider',
    'magnetdl = sickchill.providers.torrent.magnetdl:MagnetDLProvider',
    'hdtorrents_it = sickchill.providers.torrent.hdtorrents_it:HDTorrentsProvider_IT',
    'skytorrents = sickchill.providers.torrent.skytorrents:SkyTorrents',
    'xthor = sickchill.providers.torrent.xthor:XThorProvider',
    'norbits = sickchill.providers.torrent.norbits:NorbitsProvider',
    'yggtorrent = sickchill.providers.torrent.yggtorrent:YggTorrentProvider',
    'torrentbytes = sickchill.providers.torrent.torrentbytes:TorrentBytesProvider',
    'btn = sickchill.providers.torrent.btn:BTNProvider',
    'demonoid = sickchill.providers.torrent.demonoid:DemonoidProvider',
    'tokyotoshokan = sickchill.providers.torrent.tokyotoshokan:TokyoToshokanProvider',
    'speedcd = sickchill.providers.torrent.speedcd:SpeedCDProvider',
    'kat = sickchill.providers.torrent.kat:KatProvider',
    'scenetime = sickchill.providers.torrent.scenetime:SceneTimeProvider',
    'alpharatio = sickchill.providers.torrent.alpharatio:AlphaRatioProvider',
    'hounddawgs = sickchill.providers.torrent.hounddawgs:HoundDawgsProvider',
    'hdbits = sickchill.providers.torrent.hdbits:HDBitsProvider',
    'pretome = sickchill.providers.torrent.pretome:PretomeProvider',
    'morethantv = sickchill.providers.torrent.morethantv:MoreThanTVProvider',
    'torrentz = sickchill.providers.torrent.torrentz:TorrentzProvider',
    'archetorrent = sickchill.providers.torrent.archetorrent:ArcheTorrentProvider',
    'hdtorrents = sickchill.providers.torrent.hdtorrents:HDTorrentsProvider',
    'immortalseed = sickchill.providers.torrent.immortalseed:ImmortalseedProvider',
    'ilcorsaronero = sickchill.providers.torrent.ilcorsaronero:ilCorsaroNeroProvider',
    'iptorrents = sickchill.providers.torrent.iptorrents:IPTorrentsProvider',
    'torrent9 = sickchill.providers.torrent.torrent9:Torrent9Provider',
    'newpct = sickchill.providers.torrent.newpct:newpctProvider',
    'gftracker = sickchill.providers.torrent.gftracker:GFTrackerProvider',
    'filelist = sickchill.providers.torrent.filelist:FileListProvider',
    'abnormal = sickchill.providers.torrent.abnormal:ABNormalProvider',
    'torrentproject = sickchill.providers.torrent.torrentproject:TorrentProjectProvider',
    'danishbits = sickchill.providers.torrent.danishbits:DanishbitsProvider',
    'omgwtfnzbs = sickchill.providers.nzb.omgwtfnzbs:OmgwtfnzbsProvider',
    'gimmepeers = sickchill.providers.torrent.gimmepeers:GimmePeersProvider',
    'nebulance = sickchill.providers.torrent.nebulance:NebulanceProvider',
    'torrentday = sickchill.providers.torrent.torrentday:TorrentDayProvider',
    'torrentleech = sickchill.providers.torrent.torrentleech:TorrentLeechProvider',
])
