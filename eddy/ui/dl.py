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

import time

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy.core.common import HasThreadingSystem
from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.qt import Font
from eddy.core.functions.signals import connect
from eddy.core.items.nodes.literal import LiteralNode
from eddy.core.owl import OWL2Datatype, OWL2Profiles
from eddy.core.worker import AbstractWorker


class DLSyntaxValidationDialog(QtWidgets.QDialog, HasThreadingSystem):
    """
    Extends QtWidgets.QDialog with facilities to perform manual DL syntax validation.
    """
    sgnWork = QtCore.pyqtSignal(int)

    def __init__(self, project, session):
        """
        Initialize the dialog.
        :type project: Project
        :type session: Session
        """
        super().__init__(session)

        self.project = project
        self.workerThread = None
        self.worker = None
        self.i = 0

        #############################################
        # TOP AREA
        #################################

        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.setAlignment(QtCore.Qt.AlignHCenter)
        self.progressBar.setRange(self.i, 6)
        self.progressBar.setFixedSize(400, 30)
        self.progressBar.setValue(self.i)

        self.progressBox = QtWidgets.QWidget(self)
        self.progressBoxLayout = QtWidgets.QVBoxLayout(self.progressBox)
        self.progressBoxLayout.setContentsMargins(10, 10, 10, 10)
        self.progressBoxLayout.addWidget(self.progressBar)

        #############################################
        # CONTROLS AREA
        #################################

        self.buttonAbort = QtWidgets.QPushButton('Abort', self)
        self.buttonIgnore = QtWidgets.QPushButton('Ignore', self)
        self.buttonShow = QtWidgets.QPushButton('Show', self)

        self.buttonBox = QtWidgets.QWidget(self)
        self.buttonBox.setVisible(False)
        self.buttonBoxLayout = QtWidgets.QHBoxLayout(self.buttonBox)
        self.buttonBoxLayout.setContentsMargins(10, 0, 10, 10)
        self.buttonBoxLayout.addWidget(self.buttonAbort, 0, QtCore.Qt.AlignRight)
        self.buttonBoxLayout.addWidget(self.buttonIgnore, 0, QtCore.Qt.AlignRight)
        self.buttonBoxLayout.addWidget(self.buttonShow, 0, QtCore.Qt.AlignRight)

        #############################################
        # MESSAGE AREA
        #################################

        self.messageField = QtWidgets.QTextEdit(self)
        self.messageField.setAcceptRichText(True)
        self.messageField.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.messageField.setFixedSize(400, 100)
        self.messageField.setReadOnly(True)

        self.messageBox = QtWidgets.QWidget(self)
        self.messageBox.setVisible(False)
        self.messageBoxLayout = QtWidgets.QVBoxLayout(self.messageBox)
        self.messageBoxLayout.setContentsMargins(10, 0, 10, 10)
        self.messageBoxLayout.addWidget(self.messageField)

        #############################################
        # CONFIGURE LAYOUT
        #################################

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.progressBox)
        self.mainLayout.addWidget(self.buttonBox, 0, QtCore.Qt.AlignRight)
        self.mainLayout.addWidget(self.messageBox)

        connect(self.buttonAbort.clicked, self.doAbort)
        connect(self.buttonIgnore.clicked, self.doIgnore)
        connect(self.buttonShow.clicked, self.doShow)
        connect(self.sgnWork, self.doWork)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Running OWL 2 DL syntax validation...')
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))

    #############################################
    #   INTERFACE
    #################################

    def dispose(self):
        """
        Gracefully quits working thread.
        """
        if self.workerThread:
            self.workerThread.quit()
            if not self.workerThread.wait(2000):
                self.workerThread.terminate()
                self.workerThread.wait()

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the active session (alias for SyntaxValidationDialog.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   EVENTS
    #################################

    def closeEvent(self, closeEvent):
        """
        Executed when the dialog is closed.
        :type closeEvent: QCloseEvent
        """
        self.dispose()

    def showEvent(self, showEvent):
        """
        Executed whenever the dialog is shown.
        :type showEvent: QShowEvent
        """
        self.sgnWork.emit(0)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(bool)
    def doAbort(self, _=False):
        """
        Executed when the abort button is pressed.
        :type _: bool
        """
        self.sgnWork.emit(self.i + 1)  #previous dialog pops up if this command is not executed.
        self.close()

    @QtCore.pyqtSlot(bool)
    def doIgnore(self, _=False):
        """
        Executed when the ignore button is pressed.
        :type _: bool
        """
        self.sgnWork.emit(self.i + 1)

    @QtCore.pyqtSlot(bool)
    def doShow(self, _=False):
        """
        Executed when the show button is pressed.
        :type _: bool
        """
        if self.i < len(self.items):
            item = self.items[self.i]
            focus = item
            if item.isEdge():
                try:
                    focus = item.breakpoints[int(len(item.breakpoints) / 2)]
                except IndexError:
                    pass
            self.session.doFocusDiagram(item.diagram)
            self.session.mdi.activeView().centerOn(focus)
            self.session.mdi.activeDiagram().clearSelection()
            item.setSelected(True)
        self.close()

    @QtCore.pyqtSlot(int)
    def doWork(self, i):
        """
        Perform on or more advancements step in the validation procedure.
        :type i: int
        """
        # ADAPT DISPLAY
        self.buttonBox.setVisible(False)
        self.messageBox.setVisible(False)
        self.messageField.setText('')
        self.setFixedSize(self.sizeHint())
        # MAKE SURE WE ARE CLEAR
        self.dispose()
        # RUN THE WORKER
        worker = DLSyntaxWorker(self.project)
        connect(worker.sgnStep, self.onStep)
        connect(worker.sgnCompliant, self.onCompliant)
        connect(worker.sgnNotCompliant, self.onNotCompliant)
        self.startThread('DLSyntaxCheck', worker)

    @QtCore.pyqtSlot(int)
    def onStep(self, step):
        """
        Executed when the syntax validation procedure is completed and the alphabet is not compliant.
        """
        self.progressBar.setValue(step)
        self.progressBar.update()

    @QtCore.pyqtSlot()
    def onCompliant(self):
        """
        Executed when the syntax validation procedure is completed and the alphabet is compliant.
        """
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_done_black').pixmap(48))
        msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        msgbox.setWindowTitle('Done!')
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
        msgbox.setText('The current alphabet can be used to define a valid OWL 2 DL Ontology')
        msgbox.setTextFormat(QtCore.Qt.RichText)
        msgbox.exec_()
        self.close()

    @QtCore.pyqtSlot(int)
    def onNotCompliant(self,issueCount):
        """
        Executed when the syntax validation procedure is completed and the alphabet is not compliant.
        """
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
        msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        msgbox.setWindowTitle('Done!')
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
        msgbox.setText('The current alphabet cannot be used to define a valid OWL 2 DL Ontology ({} violations found)'.format(str(issueCount)))
        msgbox.setTextFormat(QtCore.Qt.RichText)
        msgbox.exec_()
        self.close()


class DLSyntaxWorker(AbstractWorker):
    """
    Extends QtCore.QObject providing a worker thread that will check if the alphabet induced by the diagram can be used to define a OWL 2 DL ontology .
    """
    sgnCompliant = QtCore.pyqtSignal()
    sgnNotCompliant = QtCore.pyqtSignal(int)
    sgnStep = QtCore.pyqtSignal(int)

    def __init__(self,project):
        """
        Initialize the dl validation worker.
        :type project: Project
        """
        super().__init__()
        self.project = project

    @QtCore.pyqtSlot()
    def run(self):
        """
        Main worker.
        """
        issues = []

        classes = self.project.itemIRIs(Item.ConceptIRINode)
        datatypes = self.project.itemIRIs(Item.ValueDomainIRINode)
        objProps = self.project.itemIRIs(Item.RoleIRINode)
        dataProps = self.project.itemIRIs(Item.AttributeIRINode)
        individuals = self.project.itemIRIs(Item.IndividualIRINode)
        defaultDatatypes = OWL2Datatype.forProfile(OWL2Profiles.OWL2)

        for cls in classes:
            if not (cls.isOwlThing or cls.isOwlNothing) and self.project.isFromReservedVocabulary(cls):
                issues.append('The iri <{}> cannot occur as class in a OWL 2 DL ontology (it comes from the reserved vocabulary)'.format(str(cls)))
        self.sgnStep.emit(1)

        for type in datatypes:
            if not (type in defaultDatatypes) and self.project.isFromReservedVocabulary(type):
                issues.append('The iri <{}> cannot occur as datatype in a OWL 2 DL ontology (it comes from the reserved vocabulary and is not in the OWL 2 default datatype map)'.format(str(type)))
            if type in classes:
                issues.append('The iri <{}> cannot occur as both datatype and class in a OWL 2 DL ontology'.format(str(type)))
        self.sgnStep.emit(2)

        for objProp in objProps:
            if not (objProp.isTopObjectProperty or objProp.isBottomObjectProperty) and self.project.isFromReservedVocabulary(objProp):
                issues.append('The iri <{}> cannot occur as object property in a OWL 2 DL ontology (it comes from the reserved vocabulary)'.format(str(objProp)))
        self.sgnStep.emit(3)

        for dataProp in dataProps:
            if not (dataProp.isTopDataProperty or dataProp.isBottomDataProperty) and self.project.isFromReservedVocabulary(dataProp):
                issues.append('The iri <{}> cannot occur as object property in a OWL 2 DL ontology (it comes from the reserved vocabulary)'.format(str(dataProp)))
            if dataProp in objProps:
                issues.append('The iri <{}> cannot occur as both DataProperty and ObjectProperty in a OWL 2 DL ontology'.format(str(dataProp)))
        self.sgnStep.emit(4)

        for ind in individuals:
            if self.project.isFromReservedVocabulary(ind):
                issues.append('The iri <{}> cannot occur as individual in a OWL 2 DL ontology (it comes from the reserved vocabulary)'.format(str(ind)))
        self.sgnStep.emit(5)

        for diagram in self.project.diagrams():
            for node in diagram.nodes():
                if isinstance(node, LiteralNode):
                    type = node.datatype
                    if not type in defaultDatatypes:
                        issues.append(
                            'The datatype <{}> cannot be used to build literals as it has empty lexical space (literal: {})'.format(
                                str(type), str(node.literal)))
        self.sgnStep.emit(6)

        if issues:
            self.sgnNotCompliant.emit(len(issues))
        else:
            self.sgnCompliant.emit()

        self.finished.emit()