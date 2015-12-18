# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: an editor for the Graphol ontology language.                    #
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
##########################################################################
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


from abc import ABCMeta, abstractmethod

from PyQt5.QtWidgets import QProxyStyle


class Style(QProxyStyle):

    __metaclass__ = ABCMeta

    def __init__(self, *args):
        """
        Initialize the Light style (using Fusion as base).
        """
        super().__init__(*args)

    @abstractmethod
    def qss(self):
        """
        Returns the stylesheet associated with this style.
        :rtype: unicode
        """
        pass

    @classmethod
    def forName(cls, name):
        """
        Returns an initialized style matching the given name. If the given name is not
        a valid style name will return the default one (currently set on Light style).
        :type name: T <= bytes | unicode
        :rtype: Style
        """
        return __mapping__.get(name, LightStyle)()


from eddy.styles.light import LightStyle


__mapping__ = {
    'light': LightStyle,
}