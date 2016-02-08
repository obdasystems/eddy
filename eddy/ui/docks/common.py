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


from PyQt5.QtCore import Qt, pyqtSlot, QSettings
from PyQt5.QtWidgets import QDockWidget

from eddy.core.functions import connect, expandPath


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

        self.settings = QSettings(expandPath('@home/Eddy.ini'), QSettings.IniFormat)

        connect(self.dockLocationChanged, self.saveArea)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def closeEvent(self, event):
        """
        Executed when the dock widget is closed.
        :param event: QCloseEvent
        """
        self.saveView(False)

    def showEvent(self, event):
        """
        Executed when the dock widget is shown.
        :type event: QShowEvent
        """
        self.saveView(True)

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot(int)
    def saveArea(self, area):
        """
        Executed when the dock widget is moved into a different area.
        :type area: int
        """
        self.settings.setValue('dock/{}/area'.format(self.objectName()), area)

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def saveView(self, view):
        """
        Executed when the dock widget is hidden/displayed.
        :type view: bool
        """
        self.settings.setValue('dock/{}/view'.format(self.objectName()), view)