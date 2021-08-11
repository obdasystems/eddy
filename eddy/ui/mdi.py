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


from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from eddy.core.datatypes.misc import DiagramMode
from eddy.core.functions.signals import connect


class MdiArea(QtWidgets.QMdiArea):
    """
    Extends QtWidgets.QMdiArea providing a widget where to render Graphol diagrams.
    """
    def __init__(self, session, **kwargs):
        """
        Initialize the MDI area.
        :type session: Session
        """
        super().__init__(session, **kwargs)

        self.setContentsMargins(0, 0, 0, 0)
        self.setViewMode(MdiArea.TabbedView)
        self.setTabPosition(QtWidgets.QTabWidget.North)
        self.setTabsClosable(True)
        self.setTabsMovable(True)
        self.tabBar.setExpanding(False)
        connect(self.subWindowActivated, self.onSubWindowActivated)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the active Session (alias for MdiArea.parent()).
        :rtype: Session
        """
        return self.parent()

    @property
    def tabBar(self):
        """
        Returns the reference to the MdiArea's QTabBar.
        :rtype: QTabBar
        """
        return self.findChild(QtWidgets.QTabBar)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(QtWidgets.QGraphicsScene)
    def onDiagramRemoved(self, diagram):
        """
        Executed when a diagram is renamed.
        :type diagram: Diagram
        """
        for subwindow in self.subWindowList():
            if subwindow.diagram is diagram:
                subwindow.close()

    @QtCore.pyqtSlot(QtWidgets.QMdiSubWindow)
    def onSubWindowActivated(self, subwindow):
        """
        Executed when the active subwindow changes.
        :type subwindow: MdiSubWindow
        """
        self.session.sgnUpdateState.emit()
        if subwindow:
            subwindow.diagram.setMode(DiagramMode.Idle)
            self.session.setWindowTitle(self.session.project, subwindow.diagram)
        else:
            if not self.subWindowList():
                self.session.setWindowTitle(self.session.project)

    @QtCore.pyqtSlot()
    def doCloseOtherSubWindows(self):
        """
        Closes all the sub-windows except the one from which the action has been triggered.
        If the triggering action does not correspond to any sub-window, then close
        all sub-windows except the currently active one.
        """
        action = self.sender()
        window = action.parent()
        if window not in self.subWindowList():
            window = self.activeSubWindow()
        for subwindow in self.subWindowList():
            if subwindow is not window:
                subwindow.close()

    #############################################
    #   INTERFACE
    #################################

    def activeDiagram(self):
        """
        Returns the reference to the active diagram, or None if there is no active diagram..
        :rtype: Diagram
        """
        subwindow = self.activeSubWindow()
        if subwindow:
            view = subwindow.widget()
            if view:
                return view.scene()
        return None

    def activeView(self):
        """
        Returns the reference to the active diagram view, or None if there is no active view.
        :rtype: DiagramView
        """
        subwindow = self.activeSubWindow()
        if subwindow:
            return subwindow.widget()
        return None

    def addSubWindow(self, subwindow, flags=0, **kwargs):
        """
        Add a subwindow to the MDI area.
        :type subwindow: MdiSubWindow
        :type flags: int
        """
        menu = subwindow.systemMenu()
        action = menu.actions()[7] # CLOSE ACTION
        action.setShortcut(QtGui.QKeySequence.Close)
        action = QtWidgets.QAction('Close All', subwindow)
        action.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_TitleBarCloseButton))
        connect(action.triggered, self.closeAllSubWindows)
        menu.addAction(action)
        action = QtWidgets.QAction('Close Others', subwindow)
        action.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_TitleBarCloseButton))
        connect(action.triggered, self.doCloseOtherSubWindows)
        menu.addAction(action)
        return super().addSubWindow(subwindow)

    def subWindowForDiagram(self, diagram):
        """
        Returns the subwindow holding the given diagram.
        :type diagram: Diagram
        :rtype: MdiSubWindow
        """
        for subwindow in self.subWindowList():
            if subwindow.diagram == diagram:
                return subwindow
        return None


class MdiSubWindow(QtWidgets.QMdiSubWindow):
    """
    This class implements the MDI area subwindow.
    """
    def __init__(self, view, parent=None):
        """
        Initialize the subwindow
        :type view: DiagramView
        :type parent: QWidget
        """
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWidget(view)
        self.setWindowTitle(self.diagram.name)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def diagram(self):
        """
        Returns the diagram displayed in this subwindow.
        :rtype: Diagram
        """
        view = self.widget()
        if view:
            return view.scene()
        return None

    @property
    def view(self):
        """
        Returns the diagram view used in this subwindow (alias for MdiSubWindow.widget()).
        :rtype: DiagramView
        """
        return self.widget()
