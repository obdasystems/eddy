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


from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QWidget, QToolButton, QAction, QMenu

from eddy.datatypes import Font
from eddy.functions import clamp, connect, make_shaded_icon, rangeF


class ZoomControl(QWidget):
    """
    This class implements the Zoom control which is used to scale the diagram scene.
    """
    MinScale = 0.25 # minimum scale value
    MaxScale = 5.00 # maximum scale value
    Step = 0.25     # incremental scale step
    Default = 1.00  # default zoom level

    zoomChanged = pyqtSignal(float)

    def __init__(self, parent=None):
        """
        Inizialize the zoom control widget.
        :param parent: the parent widget.
        """
        super().__init__(parent)

        self.zoomLevel = ZoomControl.Default
        self.zoomLevels = [x for x in rangeF(ZoomControl.MinScale, ZoomControl.MaxScale + ZoomControl.Step, ZoomControl.Step)]

        # zoom level change actions
        self.actionsZoomChange = []
        for i in self.zoomLevels:
            action = QAction('{0}%'.format(int(i * 100)), self)
            action.setCheckable(True)
            action.setChecked(i == self.zoomLevel)
            action.setData(i)
            connect(action.triggered, self.zoomLevelChange)
            self.actionsZoomChange.append(action)

        # zoom level change menu (to be embedded into a QToolButton)
        self.menuZoomLevelChange = QMenu('Zoom Level')
        for action in self.actionsZoomChange:
            self.menuZoomLevelChange.addAction(action)

        # zoom out shortcut
        self.buttonZoomOut = QToolButton()
        self.buttonZoomOut.setIcon(make_shaded_icon(':/icons/zoom-out'))
        connect(self.buttonZoomOut.clicked, self.zoomOut)

        # zoom in shortcut
        self.buttonZoomIn = QToolButton()
        self.buttonZoomIn.setIcon(make_shaded_icon(':/icons/zoom-in'))
        connect(self.buttonZoomIn.clicked, self.zoomIn)

        # zoom level QToolButton (to show a drop down menu)
        self.buttonZoomLevelChange = QToolButton()
        self.buttonZoomLevelChange.setFont(Font('Arial', 12, Font.Light))
        self.buttonZoomLevelChange.setMenu(self.menuZoomLevelChange)
        self.buttonZoomLevelChange.setPopupMode(QToolButton.InstantPopup)
        self.buttonZoomLevelChange.setProperty('class', 'zoom')

        self.setEnabled(False)

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def readableLevel(self):
        """
        Returns the current zoom level in readable format (i.e: 100%, 125%, ...)
        :rtyoe: str
        """
        return '{0}%'.format(int(self.zoomLevel * 100))

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot(float)
    def scaleChanged(self, zoomLevel):
        """
        Executed when the main view changed the zoom value.
        :param zoomLevel: the zoom value.
        """
        self.adjustZoomLevel(zoomLevel)

    @pyqtSlot()
    def zoomOut(self):
        """
        Decrese the main view zoom level.
        """
        self.setZoomLevel(self.zoomLevel - ZoomControl.Step)

    @pyqtSlot()
    def zoomIn(self):
        """
        Increase the main view zoom level.
        """
        self.setZoomLevel(self.zoomLevel + ZoomControl.Step)

    @pyqtSlot()
    def zoomLevelChange(self):
        """
        Change the zoom level using the value stored in the action that triggered the slot.
        """
        self.setZoomLevel(self.sender().data())

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def adjustZoomLevel(self, zoomLevel):
        """
        Adjust the zoom control zoom level using the given value.
        :param zoomLevel: the new zoom level.
        """
        self.zoomLevel = zoomLevel
        self.updateWidget()

    def resetZoomLevel(self):
        """
        Reset the zoom control to the default index.
        """
        self.setZoomLevel(ZoomControl.Default)

    def setZoomLevel(self, zoomLevel):
        """
        Set the zoom level according to the given value.
        :param zoomLevel: the new zoom level.
        """
        if self.isEnabled():
            zoomLevel = clamp(zoomLevel, ZoomControl.MinScale, ZoomControl.MaxScale)
            if zoomLevel != self.zoomLevel:
                self.zoomLevel = zoomLevel
                self.zoomChanged.emit(self.zoomLevel)
                self.updateWidget()

    def updateWidget(self):
        """
        Update current widget status.
        """
        if self.isEnabled():
            self.buttonZoomOut.setEnabled(self.zoomLevel > min(self.zoomLevels))
            self.buttonZoomIn.setEnabled(self.zoomLevel < max(self.zoomLevels))
            self.buttonZoomLevelChange.setText(self.readableLevel)
            self.buttonZoomLevelChange.setEnabled(True)
            for action in self.actionsZoomChange:
                action.setChecked(action.data() == self.zoomLevel)
        else:
            self.buttonZoomOut.setEnabled(False)
            self.buttonZoomIn.setEnabled(False)
            self.buttonZoomLevelChange.setEnabled(False)
            self.buttonZoomLevelChange.setText('{0}%'.format(int(ZoomControl.Default * 100)))
            for action in self.actionsZoomChange:
                action.setChecked(False)

    ####################################################################################################################
    #                                                                                                                  #
    #   OVERRIDES                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def setDisabled(self, disabled):
        """
        Set the widget disabled status.
        :param disabled: the disabled status.
        """
        super().setDisabled(disabled)
        self.updateWidget()

    def setEnabled(self, enabled):
        """
        Set the widget enabled status.
        :param enabled: the enabled status.
        """
        super().setEnabled(enabled)
        self.updateWidget()