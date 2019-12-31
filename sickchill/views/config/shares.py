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
from __future__ import absolute_import, print_function, unicode_literals

# Third Party Imports
from tornado.web import addslash

# First Party Imports
import sickbeard
from sickbeard import logger, ui
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

# Local Folder Imports
from . import Config


@Route('/config/shares(/?.*)', name='config:shares')
class ConfigShares(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigShares, self).__init__(*args, **kwargs)

    @addslash
    def index(self):

        t = PageTemplate(rh=self, filename="config_shares.mako")
        return t.render(title=_('Config - Shares'), header=_('Windows Shares Configuration'),
                        topmenu='config', submenu=self.ConfigMenu(),
                        controller="config", action="shares")

    @staticmethod
    def save_shares(shares):
        new_shares = {}
        for index, share in enumerate(shares):
            if share.get('server') and share.get('path') and share.get('name'):
                new_shares[share.get('name')] = {'server': share.get('server'), 'path': share.get('path')}
            elif any([share.get('server'), share.get('path'), share.get('name')]):
                info = []
                if not share.get('name'):
                    info.append('name')
                if not share.get('server'):
                    info.append('server')
                if not share.get('path'):
                    info.append('path')

                info = ' and '.join(info)
                logger.log('Cannot save share #{index}. You must enter name, server and path.'
                           '{info} {copula} missing, got: [name: {name}, server:{server}, path: {path}]'.format(
                                index=index, info=info, copula=('is', 'are')['and' in info],
                                name=share.get('name'), server=share.get('server'), path=share.get('path')))

        sickbeard.WINDOWS_SHARES.clear()
        sickbeard.WINDOWS_SHARES.update(new_shares)

        ui.notifications.message(_('Saved Shares'), _('Your Windows share settings have been saved'))
