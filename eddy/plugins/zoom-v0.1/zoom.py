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


from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy.core.functions.misc import clamp, rangeF
from eddy.core.functions.signals import connect, disconnect
from eddy.core.plugin import AbstractPlugin

from eddy.ui.view import DiagramView


class ZoomPlugin(AbstractPlugin):
    """
    This plugin provides the Zoom control used to scale the MDI area.
    """
    sgnChanged = QtCore.pyqtSignal(float)

    def __init__(self, spec, session):
        """
        Initialize the plugin.
        :type spec: PluginSpec
        :type session: session
        """
        super().__init__(spec, session)
        self.afwset = set()
        self.level = DiagramView.ZoomDefault
        self.levels = [x for x in rangeF(DiagramView.ZoomMin, DiagramView.ZoomMax + DiagramView.ZoomStep, DiagramView.ZoomStep)]
        self.view = None

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def doUpdateState(self):
        """
        Update the state of the zoom controls according to the active diagram.
        """
        self.refresh(enabled=self.session.mdi.activeDiagram() is not None)

    @QtCore.pyqtSlot(bool)
    def doZoomIn(self, _=False):
        """
        Increase the main view zoom level.
        :type _: bool
        """
        self.setLevel(self.level + DiagramView.ZoomStep)

    @QtCore.pyqtSlot(bool)
    def doZoomOut(self, _=False):
        """
        Decrese the main view zoom level.
        :type _: bool
        """
        self.setLevel(self.level - DiagramView.ZoomStep)

    @QtCore.pyqtSlot(bool)
    def doZoomReset(self, _=False):
        """
        Reset the zoom control to the default index.
        :type _: bool
        """
        self.setLevel(DiagramView.ZoomDefault)

    @QtCore.pyqtSlot(float)
    def onScaleChanged(self, level):
        """
        Executed when the main view changes the zoom value.
        :type level: float
        """
        self.adjust(level)

    @QtCore.pyqtSlot(QtWidgets.QMdiSubWindow)
    def onSubWindowActivated(self, subwindow):
        """
        Executed when the active subwindow changes.
        :type subwindow: MdiSubWindow
        """
        if subwindow:
            if self.view:
                # If the Zoom control widgets are currently controlling a diagram view, 
                # disconnect them from the old view before connecting them to the new one.
                self.debug('Disconnecting from diagram: %s', self.view.diagram.name)
                disconnect(self.sgnChanged, self.view.onZoomChanged)
                disconnect(self.view.sgnScaled, self.onScaleChanged)
            # Attach the new view to the Zoom controls.
            self.debug('Connecting to diagram: %s', subwindow.diagram.name)
            connect(self.sgnChanged, subwindow.view.onZoomChanged)
            connect(subwindow.view.sgnScaled, self.onScaleChanged)
            self.adjust(subwindow.view.zoom)
            self.setView(subwindow.view)
        else:
            if not self.session.mdi.subWindowList():
                if self.view:
                    # If the Zoom control widgets are currently controlling a diagram view,
                    # disconnect them from the old view before connecting them to the new one.
                    self.debug('Disconnecting from diagram: %s', self.view.diagram.name)
                    disconnect(self.sgnChanged, self.view.onZoomChanged)
                    disconnect(self.view.sgnScaled, self.onScaleChanged)
                self.setLevel(DiagramView.ZoomDefault)
                self.setView(None)

    #############################################
    #   INTERFACE
    #################################

    def adjust(self, level):
        """
        Adjust the zoom control zoom level using the given value.
        Will not emit any signal since this is to be executed just to adapt the level value to the view one.
        :type level: float
        """
        self.level = level
        self.refresh(enabled=True)

    def refresh(self, enabled):
        """
        Refresh the status of the Zoom controls
        :type enabled: bool
        """
        self.widget('button_zoom_in').setEnabled(enabled and self.level < max(self.levels))
        self.widget('button_zoom_out').setEnabled(enabled and self.level > min(self.levels))
        self.widget('button_zoom_reset').setEnabled(enabled and self.level != DiagramView.ZoomDefault)

    def setLevel(self, level):
        """
        Set the zoom level according to the given value.
        :type level: float
        """
        level = clamp(level, DiagramView.ZoomMin, DiagramView.ZoomMax)
        if level != self.level:
            self.level = level
            self.refresh(enabled=True)
            self.sgnChanged.emit(self.level)

    def setView(self, view):
        """
        Sets the view currently controlled by the Zoom controls.
        :type view: T <= DiagramView|None
        """
        self.view = view
        self.refresh(enabled=view is not None)

    #############################################
    #   HOOKS
    #################################

    def dispose(self):
        """
        Executed whenever the plugin is going to be destroyed.
        """
        # DISCONNECT FROM THE ACTIVE DIAGRAM
        if self.view:
            self.debug('Disconnecting from diagram: %s', self.view.diagram.name)
            disconnect(self.sgnChanged, self.view.onZoomChanged)
            disconnect(self.view.sgnScaled, self.onScaleChanged)

        # DISCONNECT FROM ACTIVE SESSION
        self.debug('Disconnecting to active session')
        disconnect(self.session.mdi.subWindowActivated, self.onSubWindowActivated)
        disconnect(self.session.sgnUpdateState, self.doUpdateState)

        # UNINSTALL THE PALETTE DOCK WIDGET
        self.debug('Uninstalling zoom controls from "view" toolbar')
        for action in self.afwset:
            self.session.widget('view_toolbar').removeAction(action)

    def start(self):
        """
        Perform initialization tasks for the plugin.
        """
        # INITIALIZE THE WIDGETS
        self.debug('Creating zoom control widgets')

        self.addWidget(QtWidgets.QToolButton(
            icon=QtGui.QIcon(':/icons/24/ic_zoom_in_black'),
            enabled=False, checkable=False, clicked=self.doZoomIn,
            objectName='button_zoom_in'))
        self.addWidget(QtWidgets.QToolButton(
            icon=QtGui.QIcon(':/icons/24/ic_zoom_out_black'),
            enabled=False, checkable=False, clicked=self.doZoomOut,
            objectName='button_zoom_out'))
        self.addWidget(QtWidgets.QToolButton(
            icon=QtGui.QIcon(':/icons/24/ic_zoom_reset_black'),
            enabled=False, checkable=False, clicked=self.doZoomReset,
            objectName='button_zoom_reset'))

        # CONFIGURE SIGNALS/SLOTS
        self.debug('Configuring session and MDI area specific signals/slots')
        connect(self.session.mdi.subWindowActivated, self.onSubWindowActivated)
        connect(self.session.sgnUpdateState, self.doUpdateState)

        # CREATE VIEW TOOLBAR BUTTONS
        self.debug('Installing zoom controls in "view" toolbar')
        self.afwset.add(self.session.widget('view_toolbar').addSeparator())
        self.afwset.add(self.session.widget('view_toolbar').addWidget(self.widget('button_zoom_out')))
        self.afwset.add(self.session.widget('view_toolbar').addWidget(self.widget('button_zoom_in')))
        self.afwset.add(self.session.widget('view_toolbar').addWidget(self.widget('button_zoom_reset')))