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

from eddy.core.functions.signals import connect, disconnect
from eddy.core.plugin import AbstractPlugin

from eddy.ui.dock import DockWidget


class OverviewPlugin(AbstractPlugin):
    """
    This plugin provides the Overview widget.
    """
    #############################################
    #   EVENTS
    #################################

    def eventFilter(self, source, event):
        """
        Filters events if this object has been installed as an event filter for the watched object.
        :type source: QObject
        :type event: QtCore.QEvent
        :rtype: bool
        """
        if event.type() == QtCore.QEvent.Resize:
            widget = source.widget()
            widget.redraw()
        return super().eventFilter(source, event)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onDiagramSelectionChanged(self):
        """
        Executed whenever the selection of the active diagram changes.
        """
        self.widget('overview').redraw()

    @QtCore.pyqtSlot()
    def onDiagramUpdated(self):
        """
        Executed whenever the active diagram is updated.
        """
        self.widget('overview').redraw()

    @QtCore.pyqtSlot(QtWidgets.QMdiSubWindow)
    def onSubWindowActivated(self, subwindow):
        """
        Executed when the active subwindow changes.
        :type subwindow: MdiSubWindow
        """
        if subwindow:
            # If we have an active subwindow, we change the overview 
            # widget to browse the diagram within such subwindow.
            widget = self.widget('overview')
            if widget.view():
                # If the overview widget is currently inspecting a 
                # diagram, detach signals from the subwindow which 
                # is going out of focus, before connecting new ones.
                self.debug('Disconnecting from diagram: %s', widget.diagram.name)
                disconnect(widget.diagram.selectionChanged, self.onDiagramSelectionChanged)
                disconnect(widget.diagram.sgnUpdated, self.onDiagramUpdated)
            # Attach the new view/diagram to the overview widget.
            self.debug('Connecting to diagram: %s', subwindow.diagram.name)
            connect(subwindow.diagram.selectionChanged, self.onDiagramSelectionChanged)
            connect(subwindow.diagram.sgnUpdated, self.onDiagramUpdated)
            widget.setScene(subwindow.diagram)
            widget.setView(subwindow.view)
            widget.redraw()
        else:
            if not self.session.mdi.subWindowList():
                # If we don't have any active subwindow (which means that
                # they have been all closed and not just out of focus) we
                # detach the widget from the last inspected diagram.
                widget = self.widget('overview')
                if widget.view():
                    self.debug('Disconnecting from diagram: %s', widget.diagram.name)
                    disconnect(widget.diagram.selectionChanged, self.onDiagramSelectionChanged)
                    disconnect(widget.diagram.sgnUpdated, self.onDiagramUpdated)
                widget.setScene(None)
                widget.setView(None)
                widget.redraw()

    #############################################
    #   HOOKS
    #################################

    def dispose(self):
        """
        Executed whenever the plugin is going to be destroyed.
        """
        # DISCONNECT FROM THE ACTIVE DIAGRAM
        widget = self.widget('overview')
        if widget.view():
            self.debug('Disconnecting from diagram: %s', widget.diagram.name)
            disconnect(widget.diagram.selectionChanged, self.onDiagramSelectionChanged)
            disconnect(widget.diagram.sgnUpdated, self.onDiagramUpdated)

        # DISCONNECT FROM ACTIVE SESSION
        self.debug('Disconnecting to active session')
        disconnect(self.session.mdi.subWindowActivated, self.onSubWindowActivated)

        # REMOVE DOCKING AREA WIDGET MENU ENTRY
        self.debug('Removing docking area widget toggle from "view" menu')
        menu = self.session.menu('view')
        menu.removeAction(self.widget('overview_dock').toggleViewAction())

        # UNINSTALL THE PALETTE DOCK WIDGET
        self.debug('Uninstalling docking area widget')
        self.widget('overview_dock').removeEventFilter(self)
        self.session.removeDockWidget(self.widget('overview_dock'))

    def start(self):
        """
        Perform initialization tasks for the plugin.
        """
        # INITIALIZE THE WIDGET
        self.debug('Creating overview widget')
        widget = OverviewWidget(self)
        widget.setObjectName('overview')
        self.addWidget(widget)

        # CREATE DOCKING AREA WIDGET
        self.debug('Creating docking area widget')
        widget = DockWidget('Overview', QtGui.QIcon(':/icons/18/ic_zoom_black'), self.session)
        widget.installEventFilter(self)
        widget.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.BottomDockWidgetArea)
        widget.setObjectName('overview_dock')
        widget.setWidget(self.widget('overview'))
        self.addWidget(widget)

        # CREATE SHORTCUTS
        action = widget.toggleViewAction()
        action.setParent(self.session)
        action.setShortcut(QtGui.QKeySequence('Alt+3'))

        # CREATE ENTRY IN VIEW MENU
        self.debug('Creating docking area widget toggle in "view" menu')
        menu = self.session.menu('view')
        menu.addAction(self.widget('overview_dock').toggleViewAction())

        # CONFIGURE SIGNALS/SLOTS
        self.debug('Connecting to active session')
        connect(self.session.mdi.subWindowActivated, self.onSubWindowActivated)

        # CREATE DOCKING AREA WIDGET
        self.debug('Installing docking area widget')
        self.session.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.widget('overview_dock'))


class OverviewWidget(QtWidgets.QGraphicsView):
    """
    This class is used to display the active diagram overview.
    """
    def __init__(self, plugin):
        """
        Initialize the Overview.
        :type plugin: Overview
        """
        super().__init__(plugin.parent())
        self.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        self.setMinimumSize(QtCore.QSize(216, 216))
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setOptimizationFlags(QtWidgets.QGraphicsView.DontAdjustForAntialiasing)
        self.setOptimizationFlags(QtWidgets.QGraphicsView.DontSavePainterState)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.NoViewportUpdate)
        self._mousePressed = False
        self._view = None

    #############################################
    #   PROPERTIES
    #################################

    @property
    def diagram(self):
        """
        Returns the reference to the diagram currently being inspected.
        :rtype: Diagram
        """
        if self._view:
            return self._view.scene()
        return None

    #############################################
    #   EVENTS
    #################################

    def mouseDoubleClickEvent(self, mouseEvent):
        """
        Executed when the mouse is double clicked on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        pass

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if mouseEvent.buttons() & QtCore.Qt.LeftButton:
            if self._view:
                self._mousePressed = True
                self._view.centerOn(self.mapToScene(mouseEvent.pos()))

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is moved on the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if mouseEvent.buttons() & QtCore.Qt.LeftButton:
            if self._view and self._mousePressed:
                self._view.centerOn(self.mapToScene(mouseEvent.pos()))

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the view.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if mouseEvent.buttons() & QtCore.Qt.LeftButton:
            if self._view:
                self._mousePressed = False

    def wheelEvent(self, wheelEvent):
        """
        Turn off wheel event since we don't need to scroll anything.
        :type wheelEvent: QGraphicsSceneWheelEvent
        """
        pass

    #############################################
    #   INTERFACE
    #################################

    def redraw(self):
        """
        Redraw the diagram within the overview.
        """
        if self._view:
            polygon = self.diagram.visibleRect(margin=10)
            if polygon:
                self.fitInView(polygon, QtCore.Qt.KeepAspectRatio)
        viewport = self.viewport()
        viewport.update()

    def setView(self, view):
        """
        Sets the widget to inspect the given Diagram view.
        :type: view: DiagramView
        """
        self._view = view

    def sizeHint(self):
        """
        Returns the recommended size for this widget.
        :rtype: QtCore.QSize
        """
        return QtCore.QSize(216, 216)
    
    def view(self):
        """
        Returns the reference to the view currently inspected by this widget.
        :rtype: DiagramView 
        """
        return self._view