# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Grapholed: a diagramming software for the Graphol language.           #
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


import os
import traceback

from grapholed.datatypes import FileType
from grapholed.dialogs import SaveFileDialog
from grapholed.functions import getPath, connect

from PyQt5.QtCore import pyqtSlot, Qt, QFile, QTextStream, QIODevice, pyqtSignal, QSizeF
from PyQt5.QtGui import QPainter, QPageSize, QPixmap
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWidgets import QMdiArea, QMdiSubWindow, QMessageBox, QDialog, QTabWidget



class MdiArea(QMdiArea):
    """
    This class implements the MDI Area where documents are rendered.
    """

    def __init__(self, *args, parent=None):
        """
        Initialize the MDI area.
        :param args: widgets that needs to be updated whenever the main active view changes.
        :param parent: the parent widget.
        """
        super().__init__(parent)
        self.setViewMode(MdiArea.TabbedView)
        self.setTabPosition(QTabWidget.North)
        self.setTabsClosable(True)
        self.setTabsMovable(True)
        self.setContentsMargins(0, 0, 0, 0)
        self.inspectors = args
        connect(self.subWindowActivated, self.handleSubWindowActivated)

    ################################################ PROPERTIES ########################################################

    @property
    def activeView(self):
        """
        Returns active MainView.
        :rtype: MainView
        """
        activeSubWindow = self.activeSubWindow()
        if activeSubWindow:
            return activeSubWindow.widget()
        return None

    ############################################# SIGNALS HANDLERS #####################################################

    @pyqtSlot('QMdiSubWindow')
    def handleSubWindowActivated(self, subwindow):
        """
        Executed when the active subwindow changes.
        :param subwindow: the subwindow which got the focus (0 if there is no subwindow).
        """
        if subwindow:
            # change the active undo stack
            mainview = subwindow.widget()
            scene = mainview.scene()
            scene.undoStack.setActive()
            # switch inspectors to show the new mainview
            for widget in self.inspectors:
                widget.setView(subwindow.widget())
        else:
            # clear inspectors
            for widget in self.inspectors:
                widget.clearView()


class MdiSubWindow(QMdiSubWindow):
    """
    This class implements the MDI area subwindow.
    """
    signalDocumentSaved = pyqtSignal('QMdiSubWindow')

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
        scene = self.widget().scene()

        if (scene.items() and not scene.document.filepath) or (not scene.undoStack.isClean()):
            # ask the user if he wants to save unsaved changes to disk
            box = QMessageBox()
            box.setIconPixmap(QPixmap(':/icons/info'))
            box.setWindowTitle('Save file?')
            box.setText('The document has been modified. Save changes?')
            box.setStandardButtons(QMessageBox.Cancel|QMessageBox.No|QMessageBox.Yes)

            result = box.exec_()

            if result == QMessageBox.Cancel:
                closeEvent.ignore()
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

    @pyqtSlot(bool)
    def handleUndoStackCleanChanged(self, clean):
        """
        Executed when the clean state of undoStack of the scene displayed in the MDI subwindow changes.
        :param clean: the clean state.
        """
        mainview = self.widget()
        scene = mainview.scene()
        if scene.document.filepath:
            windowtitle = scene.document.name if clean else '{0} *'.format(scene.document.name)
            self.setWindowTitle(windowtitle)

    ############################################ AUXILIARY METHODS #####################################################

    @staticmethod
    def getExportFilePath(path=None, name=None):
        """
        Bring up the 'Export' file dialog and returns the selected filepath.
        Will return None in case the user hit the 'Cancel' button to abort the operation.
        :param path: the start path of the file dialog.
        :param name: the default name of the file.
        :rtype: str
        """
        exportdialog = SaveFileDialog(path)
        exportdialog.setWindowTitle('Export')
        exportdialog.setNameFilters([x.value for x in FileType if x is not FileType.graphol])
        exportdialog.selectFile(name or 'Untitled')
        if exportdialog.exec_():
            return exportdialog.selectedFiles()[0], exportdialog.selectedNameFilter()
        return None

    @staticmethod
    def getSaveFilePath(path=None, name=None):
        """
        Bring up the 'Save' file dialog and returns the selected filepath.
        Will return None in case the user hit the 'Cancel' button to abort the operation.
        :param path: the start path of the file dialog.
        :param name: the default name of the file.
        :rtype: str
        """
        savedialog = SaveFileDialog(path)
        savedialog.setNameFilters([FileType.graphol.value])
        savedialog.selectFile(name or 'Untitled')
        if savedialog.exec_():
            return savedialog.selectedFiles()[0]
        return None

    def exportScene(self):
        """
        Export the current scene in a different format than Graphol.
        :return: True if the export has been performed, False otherwise.
        """
        mainview = self.widget()
        scene = mainview.scene()
        value = self.getExportFilePath(name=scene.document.name)
        if value:
            filepath = value[0]
            filetype = FileType.getFromValue(value[1])
            if filetype is FileType.pdf:
                return self.exportSceneToPdfFile(scene, filepath)
        return False

    @staticmethod
    def exportSceneToPdfFile(scene, filepath):
        """
        Export the given scene as PDF saving it in the given filepath.
        :param scene: the scene to be exported.
        :param filepath: the filepath where to export the scene.
        :return: True if the export has been performed, False otherwise.
        """
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filepath)
        printer.setPaperSize(QPrinter.Custom)
        printer.setPageSize(QPageSize(QSizeF(scene.width(), scene.height()), QPageSize.Point))

        painter = QPainter()
        if not painter.begin(printer):
            return False

        scene.render(painter)
        painter.end()
        return True

    def printScene(self):
        """
        Print the current scene.
        :return: True if the print has been performed, False otherwise.
        """
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.NativeFormat)
        printdialog = QPrintDialog(printer)

        if printdialog.exec_() == QDialog.Accepted:
            painter = QPainter()
            if not painter.begin(printer):
                return False

            mainview = self.widget()
            scene = mainview.scene()
            scene.render(painter)
            painter.end()
            return True

    def saveScene(self):
        """
        Save the current scene to disk.
        :return: True if the save has been performed, False otherwise.
        """
        mainview = self.widget()
        scene = mainview.scene()
        filepath = scene.document.filepath or self.getSaveFilePath(name=scene.document.name)
        if filepath:
            saved = self.saveSceneToGrapholFile(scene, filepath)
            if saved:
                scene.document.filepath = filepath
                scene.document.edited = os.path.getmtime(filepath)
                scene.undoStack.setClean()
                # emit a signal so the main window can update the title
                self.signalDocumentSaved.emit(self)
            return saved
        return False

    def saveSceneAs(self):
        """
        Save the current scene to disk.
        :return: True if the save has been performed, False otherwise.
        """
        mainview = self.widget()
        scene = mainview.scene()
        filepath = self.getSaveFilePath(name=scene.document.name)
        if filepath:
            saved = self.saveSceneToGrapholFile(scene, filepath)
            if saved:
                scene.document.filepath = filepath
                scene.undoStack.setClean()
                # emit a signal so the main window can update the title
                self.signalDocumentSaved.emit(self)
            return saved
        return False

    @staticmethod
    def saveSceneToGrapholFile(scene, filepath):
        """
        Save the given scene to the corresponding given filepath.
        :param scene: the scene to be saved.
        :param filepath: the filepath where to save the scene.
        :return: True if the save has been performed, False otherwise.
        """
        # save the file in a hidden file inside the grapholed home: if the save successfully
        # complete, move the file on the given filepath (in this way if an exception is raised
        # while exporting the scene, we won't lose previously saved data)
        tmpPath = getPath('@home/.{0}'.format(os.path.basename(os.path.normpath(filepath))))
        tmpFile = QFile(tmpPath)

        if not tmpFile.open(QIODevice.WriteOnly|QIODevice.Truncate|QIODevice.Text):
            box = QMessageBox()
            box.setIconPixmap(QPixmap(':/icons/warning'))
            box.setWindowTitle('Save FAILED')
            box.setText('Could not export diagram!')
            box.setDetailedText(tmpFile.errorString())
            box.setStandardButtons(QMessageBox.Ok)
            box.exec_()
            return False

        try:
            stream = QTextStream(tmpFile)
            document = scene.asGraphol()
            document.save(stream, 2)
            tmpFile.close()
            if os.path.isfile(filepath):
                os.remove(filepath)
            os.rename(tmpPath, filepath)
        except Exception:
            box = QMessageBox()
            box.setIconPixmap(QPixmap(':/icons/warning'))
            box.setWindowTitle('Save FAILED')
            box.setText('Could not export diagram!')
            box.setDetailedText(traceback.format_exc())
            box.setStandardButtons(QMessageBox.Ok)
            box.exec_()
            return False
        else:
            return True
        finally:
            if tmpFile.isOpen():
                tmpFile.close()