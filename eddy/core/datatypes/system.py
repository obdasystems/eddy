# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import os
import sys

from enum import unique, Enum
from types import DynamicClassAttribute

from eddy.core.functions.system import expandPath


class File(object):
    """
    This class is used to manage Files.
    """
    def __init__(self, path=None):
        """
        Initialize the File.
        :type path: str
        """
        self._path = expandPath(path) if path else None

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def edited(self):
        """
        Returns the timestamp when the file has been last modified.
        :rtype: int
        """
        if self.exists():
            return os.path.getmtime(self.path)
        return 0

    @property
    def path(self):
        """
        Returns the path of the File.
        :rtype: str
        """
        return self._path

    @path.setter
    def path(self, path):
        """
        Set the path of the File.
        :type path: str.
        """
        self._path = expandPath(path)

    @property
    def name(self):
        """
        Returns the name of the File.
        :rtype: str
        """
        if not self.path:
            return 'Untitled'
        return os.path.basename(os.path.normpath(self.path))

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def exists(self):
        """
        Tells whether the file exists.
        :rtype: bool
        """
        return self.path and os.path.isfile(self.path)

    def write(self, string, path=None):
        """
        Write the content of 'string' in 'path'.
        :type string: str
        :type path: str
        """
        path = path or self.path
        temp = expandPath('@home/.{}'.format(os.path.basename(os.path.normpath(path))))

        with open(temp, mode='wb') as file:
            file.write(string.encode(encoding='UTF-8'))
            if os.path.isfile(path):
                os.remove(path)
            os.rename(temp, path)
            self.path = path

@unique
class Filetype(Enum):
    """
    This class defines all the available file types supported for graphol document export.
    """
    __order__ = 'Graphol Owl Pdf'

    Graphol = 'Graphol (*.graphol)'
    Owl = 'Owl (*.owl)'
    Pdf = 'PDF (*.pdf)'

    @classmethod
    def forValue(cls, value):
        """
        Returns the filetype matching the given value.
        :type value: str
        :rtype: Filetype
        """
        for x in cls:
            if x.value == value:
                return x
        return None

    @DynamicClassAttribute
    def suffix(self):
        """
        The suffix associated with the Enum member.
        :rtype: str
        """
        return {
            Filetype.Graphol: '.graphol',
            Filetype.Owl: '.owl',
            Filetype.Pdf: '.pdf'
        }[self]


@unique
class Platform(Enum):
    """
    This class defines supported platforms.
    """
    __order__ = 'Darwin Linux Windows'

    Darwin = 'Darwin'
    Linux = 'Linux'
    Windows = 'Windows'
    Unknown = 'Unknown'

    @classmethod
    def identify(cls):
        """
        Returns the current platform identifier.
        :rtype: Platform
        """
        return Platform.forValue(sys.platform)

    @classmethod
    def forValue(cls, value):
        """
        Returns the platform identified by the the given value.
        :type value: str
        :rtype: Platform
        """
        if value.startswith('darwin'):
            return Platform.Darwin
        if value.startswith('linux'):
            return Platform.Linux
        if value.startswith('win') or value.startswith('cygwin'):
            return Platform.Windows
        return Platform.Unknown