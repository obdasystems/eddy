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


from typing import Any

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from eddy.core.datatypes.system import File
from eddy.core.functions.signals import connect


class FileDialog(QtWidgets.QFileDialog):
    """
    Extends `QtWidgets.QFileDialog` to provide a file dialog that remembers
    its state and geometry between sessions.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initializes the file dialog.
        """
        super().__init__(*args, **kwargs)
        # RESTORE STATE AND GEOMETRY
        settings = QtCore.QSettings()
        self.restoreGeometry(settings.value('filedialog/geometry', QtCore.QByteArray()))
        self.restoreState(settings.value('filedialog/state', QtCore.QByteArray()))
        self.setDirectoryUrl(settings.value('filedialog/lastVisited', self.directoryUrl()))
        connect(self.filterSelected, self.onFilterSelected)

    #############################################
    #   EVENTS
    #################################

    def hideEvent(self, hideEvent: QtGui.QHideEvent) -> None:
        """
        Executed when the dialog is hidden.
        """
        if not hideEvent.spontaneous():
            # SAVE STATE AND GEOMETRY
            settings = QtCore.QSettings()
            settings.setValue('filedialog/geometry', self.saveGeometry())
            settings.setValue('filedialog/state', self.saveState())
            settings.setValue('filedialog/lastVisited', self.directoryUrl())
            settings.sync()
        super().hideEvent(hideEvent)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(str)
    def onFilterSelected(self, filter: str) -> None:
        """
        Executed when the current file filter changes.
        """
        filetype = File.forValue(filter)
        self.setDefaultSuffix(filetype.extension if filetype else '')
