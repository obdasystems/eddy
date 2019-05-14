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

import pkg_resources

from PyQt5 import QtWidgets

from eddy.core.datatypes.system import File


class EddyProxyStyle(QtWidgets.QProxyStyle):
    """
    Extends QProxyStyle providing Eddy specific style.
    """
    PM = {
        QtWidgets.QStyle.PM_SmallIconSize: 18,
        QtWidgets.QStyle.PM_TabBarIconSize: 14,
        QtWidgets.QStyle.PM_ToolBarIconSize: 24,
    }

    def __init__(self, base):
        """
        Initialize the proxy style.
        :type base: str
        """
        super().__init__(base)
        buffer = ''
        for name in pkg_resources.resource_listdir(__name__, ''):
            if File.forPath(name) is File.Qss:
                buffer += pkg_resources.resource_string(__name__, name).decode('utf-8')
        self._stylesheet = buffer

    def pixelMetric(self, metric, option=None, widget=None):
        """
        Returns the value for the given pixel metric.
        :type metric: int
        :type option: int
        :type widget: QWidget
        :rtype: int
        """
        try:
            return EddyProxyStyle.PM[metric]
        except KeyError:
            return super().pixelMetric(metric, option, widget)

    @property
    def stylesheet(self):
        """
        Returns the stylesheet for this proxystyle.
        :rtype: str
        """
        return self._stylesheet
