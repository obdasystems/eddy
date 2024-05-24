# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <danielepantaleone@me.com>      #
#                                                                        #
#  This program is free software: you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation, either version 3 of the License, or     #
#  (at your option) any later version.                                   #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
#  GNU General Public License for more details.                          #
#                                                                        #
#  You should have received a copy of the GNU General Public License     #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#                                                                        #
#  #####################                          #####################  #
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import sys
from enum import unique

from eddy.core.datatypes.common import Enum_
from eddy.core.regex import RE_FILE_EXTENSION

IS_FREEBSD = sys.platform.startswith('freebsd')
IS_LINUX = sys.platform.startswith('linux')
IS_MACOS = sys.platform.startswith('darwin')
IS_WIN = sys.platform.startswith('win') or sys.platform.startswith('cygwin')
IS_XDG = IS_LINUX or IS_FREEBSD

IS_FROZEN = hasattr(sys, 'frozen')

@unique
class Channel(Enum_):
    """
    Update channel enum type definition
    """
    Beta = 'Beta'
    Stable = 'Stable'


@unique
class File(Enum_):
    """
    Enum implementation to deal with file types.
    """
    Bmp = 'Bitmap (*.bmp)'
    Csv = 'Comma-separated values (*.csv)'
    GraphML = 'GraphML (*.graphml)'
    Graphol = 'Graphol (*.graphol)'
    GraphReferences = 'Graph References (*.xml)'
    Html = 'Hyper-Text Markup Language (*.html)'
    Jar = 'Java Archive (*.jar)'
    Jpeg = 'JPEG (*.jpg)'
    Owl = 'Web Ontology Language (*.owl *.ofn *.owx *.omn *.ttl)'
    Pdf = 'Portable Document Format (*.pdf)'
    Png = 'PNG (*.png)'
    Qss = 'Qt Style Sheet (*.qss)'
    Spec = 'Plugin SPEC (*.spec)'
    Zip = 'ZIP (*.zip)'
    Xlsx = 'Excel Spreadsheet (*.xlsx)'
    Xml = 'XML (*.xml)'
    Any = 'All Files (*)'

    @classmethod
    def forPath(cls, path):
        """
        Returns the File matching the given path.
        :type path: str
        :rtype: File
        """
        for x in cls:
            if x.extension and path.endswith(x.extension):
                return x
        return None

    @classmethod
    def forValue(cls, value):
        """
        Returns the File matching the given value.
        :type value: str
        :rtype: File
        """
        for x in cls:
            if x.value == value:
                return x
        return None

    @property
    def extension(self):
        """
        The extension associated with the Enum member,
        or `None` if there is no associated extension.
        If there is more than one associated extension,
        the first one specified is returned.
        :rtype: str
        """
        match = RE_FILE_EXTENSION.search(self.value)
        if match:
            return match.group('extension')
        return None

    @property
    def extensions(self):
        """
        The list of extensions associated with the Enum member.
        :rtype: list
        """
        return RE_FILE_EXTENSION.findall(self.value)

    def __lt__(self, other):
        """
        Returns True if the current File is "lower" than the given other one.
        :type other: File
        :rtype: bool
        """
        return self.value < other.value

    def __gt__(self, other):
        """
        Returns True if the current File is "greater" than the given other one.
        :type other: File
        :rtype: bool
        """
        return self.value > other.value
