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


from PyQt5.QtCore import pyqtSlot, Qt
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


class MdiSubWindow(QMdiSubWindow):
    """
    This class implements the MDI area subwindow.
    """
    #closeAborted = pyqtSignal('QMdiSubWindow')
    #closed = pyqtSignal('QMdiSubWindow')

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
        connect(self.diagram.undoStack.cleanChanged, self.doSetWindowTitle)
    
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
    
    #############################################
    #   EVENTS
    #################################
    #
    # def closeEvent(self, closeEvent):
    #     """
    #     Executed when the subwindow is closed.
    #     :type closeEvent: QCloseEvent
    #     """
    #     mainview = self.widget()
    #     scene = mainview.scene()
    #
    #     if (scene.items() and not scene.document.path) or (not scene.undoStack.isClean()):
    #         # ask the user if he wants to save unsaved changes to disk
    #         box = QMessageBox()
    #         box.setIconPixmap(QPixmap(':/icons/info'))
    #         box.setWindowIcon(QIcon(':/images/eddy'))
    #         box.setWindowTitle('Save file?')
    #         box.setText('The document has been modified. Save changes?')
    #         box.setStandardButtons(QMessageBox.Cancel|QMessageBox.No|QMessageBox.Yes)
    #
    #         result = box.exec_()
    #
    #         if result == QMessageBox.Cancel:
    #             closeEvent.ignore()
    #             self.closeAborted.emit(self)
    #         elif result == QMessageBox.Yes:
    #             if not self.saveScene():
    #                 closeEvent.ignore()
    #                 self.closeAborted.emit(self)
    #
    #     if closeEvent.isAccepted():
    #         self.closed.emit(self)
    #         scene.clear()

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot(bool)
    def doSetWindowTitle(self, clean):
        """
        Executed when the clean state of the undoStack held by the displayed diagram is updated.
        :type clean: bool
        """
        self.setWindowTitle(self.diagram.name if clean else '{0} *'.format(self.diagram.name))