# This file is part of SickRage.
#
# URL: https://www.sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from sickbeard.common import Quality, qualityPresetStrings


def get_quality_string(quality):
    """
    :param quality: The quality to convert into a string
    :return: The string representation of the provided quality
    """

    if quality in qualityPresetStrings:
        return qualityPresetStrings[quality]

    if quality in Quality.qualityStrings:
        return Quality.qualityStrings[quality]

    return 'Custom'
