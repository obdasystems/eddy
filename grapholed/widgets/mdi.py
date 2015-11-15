# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  GrapholEd: an editor for the Graphol ontology language.               #
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
#  Dipartimento di Informatica e Sistemistica "A.Ruberti" at Sapienza    #
#  University of Rome: http://www.dis.uniroma1.it/~graphol/:             #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Marco Console <console@dis.uniroma1.it>                          #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#                                                                        #
##########################################################################


from PyQt5.QtCore import pyqtSlot, Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QMdiArea, QMdiSubWindow, QMessageBox, QTabWidget


class MdiArea(QMdiArea):
    """
    This class implements the MDI Area where documents are rendered.
    """
    def __init__(self, parent=None):
        """
        Initialize the MDI area.
        :param parent: the parent widget.
        """
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setViewMode(MdiArea.TabbedView)
        self.setTabPosition(QTabWidget.North)
        self.setTabsClosable(True)
        self.setTabsMovable(True)

    ################################################ PROPERTIES ########################################################

    @property
    def activeView(self):
        """
        Returns active MainView.
        :rtype: MainView
        """
        subwindow = self.activeSubWindow()
        if subwindow:
            return subwindow.widget()
        return None


class MdiSubWindow(QMdiSubWindow):
    """
    This class implements the MDI area subwindow.
    """
    closeEventIgnored = pyqtSignal('QMdiSubWindow')

    def __init__(self, view, parent=None):
        """
        Initialize the subwindow
        :param view: the main graphic view.
        :param parent: the parent widget.
        """
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWidget(view)

    ############################################## EVENT HANDLERS ######################################################

    def closeEvent(self, closeEvent):
        """
        Executed when the subwindow is closed.
        :param closeEvent: the close event instance.
        """
        mainview = self.widget()
        scene = mainview.scene()

        if (scene.items() and not scene.document.filepath) or (not scene.undostack.isClean()):
            # ask the user if he wants to save unsaved changes to disk
            box = QMessageBox()
            box.setIconPixmap(QPixmap(':/icons/info'))
            box.setWindowIcon(QIcon(':/images/grapholed'))
            box.setWindowTitle('Save file?')
            box.setText('The document has been modified. Save changes?')
            box.setStandardButtons(QMessageBox.Cancel|QMessageBox.No|QMessageBox.Yes)

            result = box.exec_()

            if result == QMessageBox.Cancel:
                closeEvent.ignore()
                self.closeEventIgnored.emit(self)
            elif result == QMessageBox.Yes:
                if not self.saveScene():
                    closeEvent.ignore()

        if closeEvent.isAccepted():
            # NOTE: it is possible to have some minor memory leak here. Upon closing of a
            # subwindow sys.getrefcount still shows 4 references to the scene being destroyed:
            #
            #   1. inside the Main View
            #   2. inside the MdiSubWindow which holds a reference of the Main View
            #   3. here below
            #   4. extra value which is the temporary argument of sys.getrefcount
            #
            # Setting the Qt.WA_DeleteOnClose attribute on the MdiSubWindow should remove
            # all those references after the close event is processed.
            scene.clear()

    ############################################# SIGNALS HANDLERS #####################################################

    @pyqtSlot('QGraphicsScene')
    def onDocumentSaved(self, scene):
        """
        Executed when a document contained in the scene rendered in this subwindow is saved.
        :param scene: the DiagramScene instance containing the document.
        """
        self.updateSubwindowTitle()

    @pyqtSlot(bool)
    def onUndoStackCleanChanged(self, clean):
        """
        Executed when the clean state of undo stack of the scene displayed in the MDI subwindow changes.
        :param clean: the undo stack clean state.
        """
        self.updateSubwindowTitle(clean)

    ################################################# INTERFACE ########################################################

    def updateSubwindowTitle(self, clean=True):
        """
        Updated the subwindow title.
        :param clean: the undo stack clean state.
        """
        mainview = self.widget()
        scene = mainview.scene()
        if scene.document.filepath:
            self.setWindowTitle(scene.document.name if clean else '{0} *'.format(scene.document.name))