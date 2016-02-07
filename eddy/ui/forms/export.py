# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import traceback

from PyQt5.QtCore import Qt, QThread, pyqtSlot, QRegExp
from PyQt5.QtGui import QPixmap, QIcon, QRegExpValidator
from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QProgressBar
from PyQt5.QtWidgets import QMessageBox, QSpacerItem, QSizePolicy

from eddy import BUG_TRACKER
from eddy.core.datatypes import File, OWLSyntax
from eddy.core.exceptions import MalformedDiagramError
from eddy.core.exporters import OWLExporter
from eddy.core.functions import isEmpty, connect, openPath

from eddy.ui.fields import StringEditField, ComboBox
from eddy.ui.view import MainView


class OWLTranslationForm(QDialog):
    """
    This class implements the form used to perform Graphol -> OWL ontology translation.
    """
    def __init__(self, scene, filepath, parent=None):
        """
        Initialize the form dialog.
        :type scene: DiagramScene
        :type filepath: str
        :type parent: QWidget
        """
        super().__init__(parent)

        self.scene = scene
        self.filepath = filepath
        self.worker = None
        self.workerThread = None

        self.iriField = StringEditField(self)
        self.iriField.setFixedWidth(300)
        self.iriField.setValidator(QRegExpValidator(QRegExp('[\w:\/\[\]=?%#~\.\-\+]*'), self))

        self.prefixField = StringEditField(self)
        self.prefixField.setFixedWidth(300)
        self.prefixField.setValidator(QRegExpValidator(QRegExp('[\w]*'), self))

        self.syntaxField = ComboBox(self)
        for syntax in OWLSyntax:
            self.syntaxField.addItem(syntax.value, syntax)
        self.syntaxField.setCurrentIndex(0)

        self.progressBar = QProgressBar(self)
        self.progressBar.setAlignment(Qt.AlignHCenter)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.buttonBox.button(QDialogButtonBox.Ok).setDisabled(True)

        self.mainLayout = QFormLayout(self)
        self.mainLayout.addRow('IRI', self.iriField)
        self.mainLayout.addRow('Prefix', self.prefixField)
        self.mainLayout.addRow('Syntax', self.syntaxField)
        self.mainLayout.addRow(self.progressBar)
        self.mainLayout.addRow(self.buttonBox)

        self.setWindowTitle('OWL Translation')
        self.setWindowIcon(QIcon(':/images/eddy'))
        self.setFixedSize(self.sizeHint())

        connect(self.buttonBox.accepted, self.run)
        connect(self.buttonBox.rejected, self.reject)
        connect(self.iriField.textChanged, self.iriChanged)

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot(Exception)
    def errored(self, exception):
        """
        Executed whenever the translation errors.
        :type exception: Exception
        """
        if isinstance(exception, MalformedDiagramError):

            msgbox = QMessageBox(self)
            msgbox.setIconPixmap(QPixmap(':/icons/warning'))
            msgbox.setWindowIcon(QIcon(':/images/eddy'))
            msgbox.setWindowTitle('Malformed Diagram')
            msgbox.setText('Malformed expression detected on {}: {}'.format(exception.item, exception))
            msgbox.setInformativeText('Do you want to see the error in the diagram?')
            msgbox.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
            S = QSpacerItem(400, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
            L = msgbox.layout()
            L.addItem(S, L.rowCount(), 0, 1, L.columnCount())
            msgbox.exec_()

            if msgbox.result() == QMessageBox.Yes:
                for view in self.scene.views():
                    if isinstance(view, MainView):
                        view.centerOn(exception.item)

        else:

            msgbox = QMessageBox(self)
            msgbox.setIconPixmap(QPixmap(':/icons/error'))
            msgbox.setWindowIcon(QIcon(':/images/eddy'))
            msgbox.setWindowTitle('Unhandled exception!')
            msgbox.setStandardButtons(QMessageBox.Close)
            msgbox.setText('Diagram translation could not be completed!')
            msgbox.setInformativeText('Please <a href="{}">submit a bug report</a> with detailed information.'.format(BUG_TRACKER))
            msgbox.setDetailedText(''.join(traceback.format_exception(type(exception), exception, exception.__traceback__)))
            S = QSpacerItem(400, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
            L = msgbox.layout()
            L.addItem(S, L.rowCount(), 0, 1, L.columnCount())
            msgbox.exec_()

        self.workerThread.quit()
        self.reject()

    @pyqtSlot()
    def completed(self):
        """
        Executed whenever the translation completes.
        """
        self.workerThread.quit()

        file = File(path=self.filepath)
        file.write(string=self.worker.export(syntax=self.syntaxField.currentData()))

        msgbox = QMessageBox(self)
        msgbox.setIconPixmap(QPixmap(':/icons/info'))
        msgbox.setWindowIcon(QIcon(':/images/eddy'))
        msgbox.setText('Translation completed!')
        msgbox.setInformativeText('Do you want to open the OWL ontology?')
        msgbox.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
        S = QSpacerItem(400, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        L = msgbox.layout()
        L.addItem(S, L.rowCount(), 0, 1, L.columnCount())
        msgbox.exec_()

        if msgbox.result() == QMessageBox.Yes:
            openPath(self.filepath)

        self.accept()

    @pyqtSlot(int, int)
    def progress(self, current, total):
        """
        Update the progress bar showing the translation advancement.
        :type current: int
        :type total: int
        """
        self.progressBar.setRange(0, total)
        self.progressBar.setValue(current)

    @pyqtSlot()
    def iriChanged(self):
        """
        Executed whenever the value of the prefix field changes.
        """
        button = self.buttonBox.button(QDialogButtonBox.Ok)
        button.setEnabled(not isEmpty(self.iriField.value()))

    @pyqtSlot()
    def run(self):
        """
        Perform the Graphol -> OWL translation in a separate thread.
        """
        ontoIRI = self.iriField.value()
        ontoPrefix = self.prefixField.value()

        self.buttonBox.setEnabled(False)
        self.syntaxField.setEnabled(False)

        if not ontoIRI.endswith('#'):
            ontoIRI = '{0}#'.format(ontoIRI)

        self.workerThread = QThread()
        self.worker = OWLExporter(scene=self.scene, ontoIRI=ontoIRI, ontoPrefix=ontoPrefix)
        self.worker.moveToThread(self.workerThread)

        connect(self.worker.completed, self.completed)
        connect(self.worker.errored, self.errored)
        connect(self.worker.progress, self.progress)
        connect(self.workerThread.started, self.worker.work)

        self.workerThread.start()