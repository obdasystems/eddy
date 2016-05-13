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


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMdiArea, QMdiSubWindow
from PyQt5.QtWidgets import QTabWidget, QAction, QTabBar

from eddy.core.functions.signals import connect


class MdiArea(QMdiArea):
    """
    This class implements the MDI area where diagrams are rendered.
    """
    def __init__(self, parent=None):
        """
        Initialize the MDI area.
        :type parent: QWidget
        """
        super().__init__(parent)

        self.setContentsMargins(0, 0, 0, 0)
        self.setViewMode(MdiArea.TabbedView)
        self.setTabPosition(QTabWidget.North)
        self.setTabsClosable(True)
        self.setTabsMovable(True)

        for child in self.children():
            if isinstance(child, QTabBar):
                child.setExpanding(False)
                break

    #############################################
    #   PROPERTIES
    #################################

    @property
    def activeDiagram(self):
        """
        Returns active diagram.
        :rtype: Diagram
        """
        subwindow = self.activeSubWindow()
        if subwindow:
            view = subwindow.widget()
            if view:
                return view.scene()
        return None

    @property
    def activeView(self):
        """
        Returns active diagram view.
        :rtype: DiagramView
        """
        subwindow = self.activeSubWindow()
        if subwindow:
            return subwindow.widget()
        return None

    #############################################
    #   INTERFACE
    #################################

    def addSubWindow(self, subwindow, flags=0):
        """
        Add a subwindow to the MDI area.
        :type subwindow: MdiSubWindow
        :type flags: int
        """
        menu = subwindow.systemMenu()
        action = QAction('Close All', menu)
        action.setIcon(menu.actions()[7].icon())
        connect(action.triggered, self.closeAllSubWindows)
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


class MdiSubWindow(QMdiSubWindow):
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
        self.setAttribute(Qt.WA_DeleteOnClose)
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