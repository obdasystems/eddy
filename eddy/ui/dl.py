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
from eddy.core.datatypes.owl import OWLAxiom
from eddy.core.datatypes.qt import Font
from eddy.core.exporters.owl2 import OWLOntologyExporterWorker
from eddy.core.functions.signals import connect
from eddy.core.items.nodes.literal import LiteralNode
from eddy.core.jvm import getJavaVM
from eddy.core.output import getLogger
from eddy.core.owl import OWL2Datatype, OWL2Profiles
from eddy.core.worker import AbstractWorker

LOGGER = getLogger()

class OWL2DLProfileValidationDialog(QtWidgets.QDialog, HasThreadingSystem):
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

        self.msgbox_busy = QtWidgets.QMessageBox(self)
        self.msgbox_busy.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_busy.setWindowTitle('Please Wait!')
        self.msgbox_busy.setStandardButtons(QtWidgets.QMessageBox.NoButton)
        self.msgbox_busy.setText('Running profile check  (Please Wait!)')
        self.msgbox_busy.setTextFormat(QtCore.Qt.RichText)

        self.status_bar = QtWidgets.QStatusBar()
        self.status_bar.setMinimumWidth(350)

        ####################################################

        self.messageBoxLayout = QtWidgets.QVBoxLayout()
        self.messageBoxLayout.setContentsMargins(0, 6, 0, 0)
        self.messageBoxLayout.setAlignment(QtCore.Qt.AlignCenter)

        self.messageBoxLayout.addWidget(self.msgbox_busy)
        self.messageBoxLayout.addWidget(self.status_bar)

        self.messageBoxArea = QtWidgets.QWidget()
        self.messageBoxArea.setLayout(self.messageBoxLayout)
        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addWidget(self.messageBoxArea)

        self.setLayout(self.mainLayout)

        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Please Wait!')
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.CustomizeWindowHint)
        self.setWindowModality(QtCore.Qt.NonModal)

        self.adjustSize()
        self.setFixedSize(self.width(), self.height())
        self.show()

        ######################################################

        self.msgbox_done = QtWidgets.QMessageBox(self)
        self.msgbox_done.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_done.setWindowTitle('OWL 2 DL profile validation done')
        self.msgbox_done.setStandardButtons(QtWidgets.QMessageBox.Close)
        self.msgbox_done.setTextFormat(QtCore.Qt.RichText)

        connect(self.sgnWork, self.doWork)
        self.sgnWork.emit(0)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Running OWL 2 DL profile validation...')
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
        self.setFixedSize(self.sizeHint())
        # MAKE SURE WE ARE CLEAR
        self.dispose()
        # RUN THE WORKER
        worker = DLSyntaxWorker(self.status_bar, self.project, self.session)
        connect(worker.sgnCompliant, self.onCompliant)
        connect(worker.sgnNotCompliant, self.onNotCompliant)
        connect(worker.sgnError, self.onErrorInExec)
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
        msgbox.setText('The current ontology is in the OWL 2 DL profile')
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
        msgbox.setText('The current ontology is NOT in the OWL 2 DL profile ({} violations found)'.format(str(issueCount)))
        msgbox.setTextFormat(QtCore.Qt.RichText)
        msgbox.exec_()
        self.close()

    @QtCore.pyqtSlot(Exception)
    def onErrorInExec(self, exc):
        self.msgbox_error = QtWidgets.QMessageBox(self)
        self.msgbox_error.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_error.setWindowTitle('Error!')
        self.msgbox_error.setStandardButtons(QtWidgets.QMessageBox.Close)
        self.msgbox_error.setTextFormat(QtCore.Qt.RichText)
        self.msgbox_error.setIconPixmap(QtGui.QIcon(':/icons/48/ic_done_black').pixmap(48))
        self.msgbox_error.setText('An error occured!!\n{}'.format(str(exc)))
        self.close()
        self.msgbox_error.exec_()

class DLSyntaxWorker(AbstractWorker):
    """
    Extends QtCore.QObject providing a worker thread that will check if the alphabet induced by the diagram can be used to define a OWL 2 DL ontology .
    """
    sgnCompliant = QtCore.pyqtSignal()
    sgnNotCompliant = QtCore.pyqtSignal(int)
    sgnStarted = QtCore.pyqtSignal()
    sgnError = QtCore.pyqtSignal(Exception)

    def __init__(self, status_bar, project, session, includeImports=True, computeExplanations=False):
        """
        Initialize the syntax validation worker.
        :type current: int
        :type items: list
        :type project: Project
        """
        super().__init__()
        self.project = project
        self.session = session
        self.status_bar = status_bar
        self.vm = getJavaVM()
        if not self.vm.isRunning():
            self.vm.initialize()
        self.vm.attachThreadToJVM()
        self.ProfileClass = self.vm.getJavaClass('org.semanticweb.owlapi.profiles.OWL2DLProfile')
        self.IRIClass = self.vm.getJavaClass('org.semanticweb.owlapi.model.IRI')
        self.OWLManagerClass = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.JavaFileClass = self.vm.getJavaClass('java.io.File')
        self.URIClass = self.vm.getJavaClass('java.net.URI')
        self.IRIMapperClass = self.vm.getJavaClass('org.semanticweb.owlapi.util.SimpleIRIMapper')
        self.OWLProfileReport = self.vm.getJavaClass('org.semanticweb.owlapi.profiles.OWLProfileReport')
        self.reasonerInstance = None
        self._isOntologyConsistent = None
        self.javaBottomClassNode=None
        self.javaBottomObjectPropertyNode = None
        self.javaBottomDataPropertyNode = None
        self._unsatisfiableClasses = set()
        self._unsatisfiableObjectProperties = set()
        self._unsatisfiableDataProperties = set()
        self._includeImports = includeImports
        self._computeExplanations = computeExplanations

    def loadImportedOntologiesIntoManager(self):
        LOGGER.debug('Loading declared imports into the OWL 2 Manager')
        for impOnt in self.project.importedOntologies:
            try:
                docObj = None
                if impOnt.isLocalDocument:
                    docObj = self.JavaFileClass(impOnt.docLocation)
                else:
                    docObj = self.URIClass(impOnt.docLocation)
                docLocationIRI = self.IRIClass.create(docObj)
                impOntIRI = self.IRIClass.create(impOnt.ontologyIRI)
                iriMapper = self.IRIMapperClass(impOntIRI, docLocationIRI)
                self.manager.getIRIMappers().add(iriMapper)
                loaded = self.manager.loadOntology(impOntIRI)
            except Exception as e:
                LOGGER.exception('The imported ontology <{}> cannot be loaded.\nError:{}'.format(impOnt, str(e)))
            else:
                LOGGER.debug('Ontology ({}) correctly loaded.'.format(impOnt))

    def initializeOWLManager(self, ontology):
        self.manager = ontology.getOWLOntologyManager()
        self.loadImportedOntologiesIntoManager()

    def axioms(self):
        """
        Returns the set of axioms that needs to be exported.
        :rtype: set
        """
        return {axiom for axiom in OWLAxiom}


    def runProfileCheck(self):
        worker = OWLOntologyExporterWorker(self.project,axioms=self.axioms())
        worker.run()
        self.initializeOWLManager(worker.ontology)


        self.dlProfile = self.ProfileClass()
        self.profileReport = self.dlProfile.checkOntology(worker.ontology)

        if not self.profileReport.isInProfile() :
            self.sgnNotCompliant.emit(self.profileReport.getViolations().size())
            for violation in self.profileReport.getViolations():
                print()
                print('######### Class= {} '.format(violation.getClass().toString()))
                print('######### Axiom= {} '.format(violation.getAxiom().toString()))
                for change in violation.repair():
                    print('Change= {} '.format(change.toString()))
        else:
            self.sgnCompliant.emit()

    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.sgnStarted.emit()
            self.vm.attachThreadToJVM()
            self.runProfileCheck()
        except Exception as e:
            LOGGER.exception('Fatal error while executing reasoning tasks.\nError:{}'.format(str(e)))
            self.sgnError.emit(e)
        finally:
            self.vm.detachThreadFromJVM()
            self.finished.emit()
