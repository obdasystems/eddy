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


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDockWidget


class DockWidget(QDockWidget):
    """
    This class can be used to add widgets to the docking area of the main window.
    """
    def __init__(self, name, parent=None):
        """
        Initialize the Dock widget.
        :type name: str
        :type parent: QWidget
        """
        super().__init__(name, parent, Qt.Widget)

        name = name.lower()
        name = name.replace(' ', '_')
        self.setObjectName(name)

        self._defaultArea = Qt.LeftDockWidgetArea
        self._defaultVisible = True

    def defaultArea(self):
        """
        Returns the default area for this dock widget.
        :rtype: int
        """
        return self._defaultArea

    def defaultVisible(self):
        """
        Returns the default visibility for this dock widget.
        :rtype: bool
        """
        return self._defaultVisible

    def setDefaultArea(self, area):
        """
        Set the default area for this dock widget.
        :type area: int
        """
        self._defaultArea = area

    def setDefaultVisible(self, visible):
        """
        Set the default visibility for this dock widget.
        :type visible: bool
        """
        self._defaultVisible = visible