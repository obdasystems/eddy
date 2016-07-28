# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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


from PyQt5.QtCore import Qt, QThread, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox
from PyQt5.QtWidgets import QProgressBar, QFrame, QWidget, QVBoxLayout
from PyQt5.QtWidgets import QMessageBox

from eddy import BUG_TRACKER
from eddy.core.datatypes.owl import OWLSyntax
from eddy.core.datatypes.qt import Font
from eddy.core.exceptions import MalformedDiagramError
from eddy.core.exporters.owl import OWLExporter
from eddy.core.functions.misc import format_exception
from eddy.core.functions.path import openPath, expandPath
from eddy.core.functions.signals import connect

from eddy.ui.fields import ComboBox


class OWLExportDialog(QDialog):
    """
    This class implements the form used to perform Graphol -> OWL ontology translation.
    """
    def __init__(self, project, path, session):
        """
        Initialize the form dialog.
        :type project: Project
        :type path: str
        :type session: Session
        """
        super().__init__(session)

        arial12r = Font('Arial', 12)

        self.path = expandPath(path)
        self.project = project
        self.worker = None
        self.workerThread = None

        #############################################
        # FORM AREA
        #################################

        self.syntaxField = ComboBox(self)
        for syntax in OWLSyntax:
            self.syntaxField.addItem(syntax.value, syntax)
        self.syntaxField.setCurrentIndex(0)
        self.syntaxField.setFixedWidth(300)
        self.syntaxField.setFont(arial12r)

        spacer = QFrame()
        spacer.setFrameShape(QFrame.HLine)
        spacer.setFrameShadow(QFrame.Sunken)

        self.progressBar = QProgressBar(self)
        self.progressBar.setAlignment(Qt.AlignHCenter)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)

        self.formWidget = QWidget(self)
        self.formLayout = QFormLayout(self.formWidget)
        self.formLayout.addRow('Syntax', self.syntaxField)
        self.formLayout.addRow(spacer)
        self.formLayout.addRow(self.progressBar)

        #############################################
        # CONFIRMATION AREA
        #################################

        self.confirmationBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.setFont(arial12r)

        #############################################
        # CONFIGURE LAYOUT
        #################################

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.formWidget)
        self.mainLayout.addWidget(self.confirmationBox, 0, Qt.AlignRight)

        self.setWindowTitle('OWL Export')
        self.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
        self.setFixedSize(self.sizeHint())

        connect(self.confirmationBox.accepted, self.run)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the active session (aloas for OWLExportDialog.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot(Exception)
    def onErrored(self, exception):
        """
        Executed whenever the translation errors.
        :type exception: Exception
        """
        self.workerThread.quit()

        if isinstance(exception, MalformedDiagramError):
            msgbox = QMessageBox(self)
            msgbox.setIconPixmap(QIcon(':/icons/48/ic_warning_black').pixmap(48))
            msgbox.setInformativeText('Do you want to see the error in the diagram?')
            msgbox.setText('Malformed expression detected on {0}: {1}'.format(exception.item, exception))
            msgbox.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
            msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Malformed expression')
            msgbox.exec_()
            if msgbox.result() == QMessageBox.Yes:
                self.session.doFocusItem(exception.item)
        else:
            msgbox = QMessageBox(self)
            msgbox.setDetailedText(format_exception(exception))
            msgbox.setIconPixmap(QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
            msgbox.setInformativeText('Please <a href="{0}">submit a bug report</a>.'.format(BUG_TRACKER))
            msgbox.setStandardButtons(QMessageBox.Close)
            msgbox.setText('Diagram translation could not be completed!')
            msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Unhandled exception!')
            msgbox.exec_()

        self.reject()

    @pyqtSlot()
    def onCompleted(self):
        """
        Executed whenever the translation completes.
        """
        self.workerThread.quit()

        msgbox = QMessageBox(self)
        msgbox.setIconPixmap(QIcon(':/icons/24/ic_info_outline_black').pixmap(48))
        msgbox.setInformativeText('Do you want to open the OWL ontology?')
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgbox.setText('Translation completed!')
        msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
        msgbox.exec_()
        if msgbox.result() == QMessageBox.Yes:
            openPath(self.path)

        self.accept()

    @pyqtSlot(int, int)
    def onProgress(self, current, total):
        """
        Update the progress bar showing the translation advancement.
        :type current: int
        :type total: int
        """
        self.progressBar.setRange(0, total)
        self.progressBar.setValue(current)

    @pyqtSlot()
    def onStarted(self):
        """
        Executed whenever the translation starts.
        """
        self.confirmationBox.setEnabled(False)

    @pyqtSlot()
    def run(self):
        """
        Perform the Graphol -> OWL translation in a separate thread.
        """
        self.workerThread = QThread()
        self.worker = OWLExporter(self.project, self.path, self.syntaxField.currentData())
        self.worker.moveToThread(self.workerThread)
        connect(self.worker.sgnStarted, self.onStarted)
        connect(self.worker.sgnCompleted, self.onCompleted)
        connect(self.worker.sgnErrored, self.onErrored)
        connect(self.worker.sgnProgress, self.onProgress)
        connect(self.workerThread.started, self.worker.run)
        self.workerThread.start()