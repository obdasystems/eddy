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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QWidget, QToolButton

from eddy.core.functions.misc import clamp, rangeF
from eddy.core.functions.signals import connect
from eddy.core.qt import Icon


class Zoom(QWidget):
    """
    This class implements the Zoom control which is used to scale the diagram scene.
    """
    Default = 1.00
    Min = 0.10
    Max = 5.00
    Step = 0.10

    sgnChanged = pyqtSignal(float)

    def __init__(self, parent=None):
        """
        Inizialize the zoom widget.
        :type parent: QWidget
        """
        super().__init__(parent)

        self.level = Zoom.Default
        self.levels = [x for x in rangeF(Zoom.Min, Zoom.Max + Zoom.Step, Zoom.Step)]

        self.buttonZoomIn = QToolButton()
        self.buttonZoomIn.setIcon(Icon(':/icons/zoom-in'))
        self.buttonZoomOut = QToolButton()
        self.buttonZoomOut.setIcon(Icon(':/icons/zoom-out'))
        self.buttonZoomReset = QToolButton()
        self.buttonZoomReset.setIcon(Icon(':/icons/zoom-reset'))

        connect(self.buttonZoomIn.clicked, self.zoomIn)
        connect(self.buttonZoomOut.clicked, self.zoomOut)
        connect(self.buttonZoomReset.clicked, self.zoomReset)

        self.setEnabled(False)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot(float)
    def scaleChanged(self, level):
        """
        Executed when the main view changes the zoom value.
        :type level: float
        """
        self.adjust(level)

    @pyqtSlot()
    def zoomIn(self):
        """
        Increase the main view zoom level.
        """
        self.setLevel(self.level + Zoom.Step)

    @pyqtSlot()
    def zoomOut(self):
        """
        Decrese the main view zoom level.
        """
        self.setLevel(self.level - Zoom.Step)

    @pyqtSlot()
    def zoomReset(self):
        """
        Reset the zoom control to the default index.
        """
        self.setLevel(Zoom.Default)

    #############################################
    #   INTERFACE
    #################################

    def adjust(self, level):
        """
        Adjust the zoom control zoom level using the given value.
        :type level: float
        """
        self.level = level
        self.refresh()
    
    def refresh(self):
        """
        Reload current widget status.
        """
        self.buttonZoomIn.setEnabled(self.isEnabled() and self.level < max(self.levels))
        self.buttonZoomOut.setEnabled(self.isEnabled() and self.level > min(self.levels))
        self.buttonZoomReset.setEnabled(self.isEnabled() and self.level != Zoom.Default)

    def setDisabled(self, disabled):
        """
        Set the widget disabled status.
        :type disabled: bool
        """
        super().setDisabled(disabled)
        self.refresh()

    def setEnabled(self, enabled):
        """
        Set the widget enabled status.
        :type enabled: bool
        """
        super().setEnabled(enabled)
        self.refresh()

    def setLevel(self, level):
        """
        Set the zoom level according to the given value.
        :type level: float
        """
        if self.isEnabled():
            level = clamp(level, Zoom.Min, Zoom.Max)
            if level != self.level:
                self.level = level
                self.refresh()
                self.sgnChanged.emit(self.level)