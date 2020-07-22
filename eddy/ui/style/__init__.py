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


import os
import pkgutil

from PyQt5 import QtWidgets

from eddy.core.datatypes.system import IS_FROZEN
from eddy.core.functions.fsystem import (
    isdir,
    fread,
)
from eddy.core.functions.path import expandPath


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
        self._stylesheet = None

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
        if not self._stylesheet:
            if IS_FROZEN:
                resources = expandPath('@resources/styles/')
                if isdir(resources):
                    self._stylesheet = fread(os.path.join(resources, 'default.qss'))
            else:
                self._stylesheet = pkgutil.get_data(__name__, 'default.qss').decode('utf-8')
        return self._stylesheet
