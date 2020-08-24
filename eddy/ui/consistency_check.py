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

from eddy.core.common import HasThreadingSystem, HasWidgetSystem
from eddy.core.datatypes.graphol import Special, Item
from eddy.core.datatypes.owl import OWLAxiom, OWLSyntax
from eddy.core.exporters.owl2 import OWLOntologyFetcher
from eddy.core.exporters.owl2_iri import OWLOntologyExporterWorker_v3
from eddy.core.functions.misc import first
from eddy.core.functions.signals import connect
from eddy.core.jvm import getJavaVM
from eddy.core.output import getLogger
from eddy.core.owl import IRI
from eddy.core.worker import AbstractWorker
from eddy.ui.fields import StringField

LOGGER = getLogger()

#############################################
#   CONSISTENCY CHECK
#################################
class OntologyConsistencyCheckDialog(QtWidgets.QDialog, HasThreadingSystem):
    """
    Extends QtWidgets.QDialog with facilities to perform Ontology Consistency check
    """
    sgnWork = QtCore.pyqtSignal()
    sgnErrored = QtCore.pyqtSignal()
    sgnOntologyConsistent = QtCore.pyqtSignal()
    sgnOntologyInconsistent = QtCore.pyqtSignal()
    sgnUnsatisfiableEntities = QtCore.pyqtSignal(int)
    sgnUnsatisfiableClass = QtCore.pyqtSignal(IRI)
    sgnUnsatisfiableObjectProperty = QtCore.pyqtSignal(IRI)
    sgnUnsatisfiableDataProperty = QtCore.pyqtSignal(IRI)

    def __init__(self, project, session, includeImports=True, computeUnsatisfiableEntities=True, computeExplanations=False):
        """
        Initialize the dialog.
        :type project: Project
        :type session: Session
        """
        super().__init__(session)

        self.project = project
        self.workerThread = None
        self.worker = None

        self._includeImports = includeImports
        self._computeUnsatisfiableEntities = computeUnsatisfiableEntities
        self._computeExplanations = computeExplanations

        self.msgbox_busy = QtWidgets.QMessageBox(self)
        self.msgbox_busy.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_busy.setWindowTitle('Please Wait!')
        self.msgbox_busy.setStandardButtons(QtWidgets.QMessageBox.NoButton)
        self.msgbox_busy.setText('Running reasoner  (Please Wait!)')
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
        self.msgbox_done.setWindowTitle('Ontology consistency check done')
        self.msgbox_done.setStandardButtons(QtWidgets.QMessageBox.Close)
        self.msgbox_done.setTextFormat(QtCore.Qt.RichText)

        connect(self.sgnWork, self.doWork)
        self.sgnWork.emit()
        self.session.doResetConsistencyCheck(updateNodes=True, clearReasonerCache=True)

        #TODO DEVI CONNETTERE APPOSITI SEGNALI CON ONTOLOGY EXPLORER: Quando viene modificata l'ontologia (INCLUSI GLI IMPORT)
        connect(self.project.sgnItemAdded, self.project.reset_changes_made_after_reasoning_task)
        connect(self.project.sgnItemRemoved, self.project.reset_changes_made_after_reasoning_task)

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
        self.sgnWork.emit()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def doWork(self):
        """
        Perform on or more advancements step in the validation procedure.
        """
        worker = OntologyReasoningTasksWorker(self.status_bar, self.project, self.session)
        connect(worker.sgnError, self.onErrorInExec)
        connect(worker.sgnConsistent, self.onOntologyConsistent)
        connect(worker.sgnInconsistent, self.onOntologyInconsistent)
        connect(worker.sgnUnsatisfiableEntitiesComputed, self.onUnsatisfiableEntitiesComputed)
        connect(worker.sgnUnsatisfiableClass, self.onUnsatisfiableClass)
        connect(worker.sgnUnsatisfiableObjectProperty, self.onUnsatisfiableObjectProperty)
        connect(worker.sgnUnsatisfiableDataProperty, self.onUnsatisfiableDataProperty)
        self.startThread('OntologyConsistencyCheck', worker)

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

    @QtCore.pyqtSlot()
    def onOntologyConsistent(self):
        """
        Executed when ontology is perfect
        :type message: str
        """
        if not self._computeUnsatisfiableEntities:
            self.msgbox_done = QtWidgets.QMessageBox(self)
            self.msgbox_done.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            self.msgbox_done.setWindowTitle('Ontology consistency check completed')
            self.msgbox_done.setStandardButtons(QtWidgets.QMessageBox.Close)
            self.msgbox_done.setTextFormat(QtCore.Qt.RichText)
            self.msgbox_done.setIconPixmap(QtGui.QIcon(':/icons/48/ic_done_black').pixmap(48))
            self.msgbox_done.setText('Ontology is consistent and  all classes are satisfiable')
            self.close()
            self.msgbox_done.exec_()
        self.sgnOntologyConsistent.emit()

    @QtCore.pyqtSlot()
    def onOntologyInconsistent(self):
        """
        Executed when the ontology is inconsistent.
        """
        self.msgbox_done = QtWidgets.QMessageBox(self)
        self.msgbox_done.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_done.setWindowTitle('Ontology consistency check completed')
        self.msgbox_done.setStandardButtons(QtWidgets.QMessageBox.Close)
        self.msgbox_done.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
        self.msgbox_done.setTextFormat(QtCore.Qt.RichText)
        self.msgbox_done.setText('<p>Ontology is inconsistent.</p>')
        #TODO al momento non calcoliamo explanations
        """ 
        self.msgbox_done.setText('<p>Ontology is inconsistent.</p>'
                                 '<p>You may choose to display one explanation at a time in the Explanation Explorer.</p>'
                                 '<p>To reset the background coloring of the nodes in the diagram, '
                                 'press the Reset button in the toolbar.</p>')
        """
        self.close()
        self.msgbox_done.exec_()
        self.sgnOntologyInconsistent.emit()

    @QtCore.pyqtSlot(int)
    def onUnsatisfiableEntitiesComputed(self, count):
        """
        Executed when the ontology is consistent and the unsatisfiable entities check has been run
        """
        self.msgbox_done = QtWidgets.QMessageBox(self)
        self.msgbox_done.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_done.setWindowTitle('Ontology consistency check complete')
        self.msgbox_done.setStandardButtons(QtWidgets.QMessageBox.Close)
        self.msgbox_done.setTextFormat(QtCore.Qt.RichText)
        if count>0:
            self.msgbox_done.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
            self.msgbox_done.setText('<p>Ontology is consistent however {} entities are unsatisfiable.</p>'
                                     '<p>See highlighted entries in the Ontology Explorer for details.</p>'
                                     '<p>To reset the highlighting press the Reset button in the toolbar.</p>'.format(str(count)))
        else:
            self.msgbox_done.setIconPixmap(QtGui.QIcon(':/icons/48/ic_done_black').pixmap(48))
            self.msgbox_done.setText('Ontology is consistent and all Classes, Object Properties, and Data Properties are satisfiable ')
        # TODO al momento non calcoliamo explanations
        """
        self.msgbox_done.setText('<p>Ontology is consistent however some class(es) are unsatisfiable.</p>'
                                 '<p>See Unsatisfiable Entity Explorer for details.</p>'
                                 '<p>To reset the background coloring of the nodes in the diagram, '
                                 'press the Reset button in the toolbar.</p>')
        """
        self.close()
        self.msgbox_done.exec_()
        self.sgnUnsatisfiableEntities.emit(count)

    @QtCore.pyqtSlot(IRI)
    def onUnsatisfiableClass(self,iri):
        self.sgnUnsatisfiableClass.emit(iri)

    @QtCore.pyqtSlot(IRI)
    def onUnsatisfiableObjectProperty(self, iri):
        self.sgnUnsatisfiableObjectProperty.emit(iri)

    @QtCore.pyqtSlot(IRI)
    def onUnsatisfiableDataProperty(self, iri):
        self.sgnUnsatisfiableDataProperty.emit(iri)

class OntologyReasoningTasksWorker(AbstractWorker):
    """
    Extends QtCore.QObject providing a worker thread that will perform the consistency check over the Project ontology
    """
    sgnBusy = QtCore.pyqtSignal(bool)
    sgnStarted = QtCore.pyqtSignal()
    sgnConsistent = QtCore.pyqtSignal()
    sgnInconsistent = QtCore.pyqtSignal()
    sgnError = QtCore.pyqtSignal(Exception)
    sgnUnsatisfiableEntitiesComputed = QtCore.pyqtSignal(int)
    sgnUnsatisfiableClass = QtCore.pyqtSignal(IRI)
    sgnUnsatisfiableObjectProperty = QtCore.pyqtSignal(IRI)
    sgnUnsatisfiableDataProperty = QtCore.pyqtSignal(IRI)

    def __init__(self, status_bar, project, session, includeImports=True, computeUnsatisfiableEntities=True, computeExplanations=False):
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
        self.ReasonerClass = self.vm.getJavaClass('org.semanticweb.HermiT.Reasoner')
        self.ReasonerFactoryClass = self.vm.getJavaClass('org.semanticweb.HermiT.ReasonerFactory')
        self.ReasonerConfigurationClass = self.vm.getJavaClass('org.semanticweb.HermiT.Configuration')
        self.IRIClass = self.vm.getJavaClass('org.semanticweb.owlapi.model.IRI')
        self.OWLManagerClass = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.JavaFileClass = self.vm.getJavaClass('java.io.File')
        self.URIClass = self.vm.getJavaClass('java.net.URI')
        self.IRIMapperClass = self.vm.getJavaClass('org.semanticweb.owlapi.util.SimpleIRIMapper')
        self.OWLClassClass = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLClass')
        self.OWLImportsEnum = self.vm.getJavaClass('org.semanticweb.owlapi.model.parameters.Imports')
        self.InconsistentOntologyExplanationGeneratorFactory = self.vm.getJavaClass(
            'org.semanticweb.owl.explanation.impl.blackbox.checker.InconsistentOntologyExplanationGeneratorFactory')

        self.reasonerInstance = None
        self._isOntologyConsistent = None
        self.javaBottomClassNode=None
        self.javaBottomObjectPropertyNode = None
        self.javaBottomDataPropertyNode = None
        self._unsatisfiableClasses = set()
        self._unsatisfiableObjectProperties = set()
        self._unsatisfiableDataProperties = set()
        self._includeImports = includeImports
        self._computeUnsatisfiableEntities = computeUnsatisfiableEntities
        self._computeExplanations = computeExplanations
        self.explanations = list()

    @property
    def unsatisfiableClasses(self):
        return self._unsatisfiableClasses

    @property
    def unsatisfiableObjectProperties(self):
        return self._unsatisfiableObjectProperties

    @property
    def unsatisfiableDataProperties(self):
        return self._unsatisfiableDataProperties

    def axioms(self):
        """
        Returns the set of axioms that needs to be exported.
        :rtype: set
        """
        return {axiom for axiom in OWLAxiom}

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

    def initializeOWLManagerAndReasoner(self, ontology):
        self.manager = ontology.getOWLOntologyManager()
        self.df = self.manager.getOWLDataFactory()
        self.loadImportedOntologiesIntoManager()
        self.reasonerInstance = self.ReasonerClass(self.ReasonerConfigurationClass(), ontology)
        #TODO se si usano metodi factory di Hermit, oggetto 'ontology' non viene riconosciuto come istanza di OWLReasoner
        #self.reasonerInstance = self.ReasonerFactoryClass.createReasoner(ontology, self.ReasonerConfigurationClass())
        #self.reasonerInstance = self.ReasonerFactoryClass.createReasoner(ontology)

    def isConsistent(self):
        return self.reasonerInstance.isConsistent()

    def computeUnsatisfiableClasses(self):
        try:
            self.javaBottomClassNode = self.reasonerInstance.getBottomClassNode()
            for owlClass in self.javaBottomClassNode.getEntities():
                if not(owlClass.isTopEntity() or owlClass.isBottomEntity()):
                    projIRI = self.project.getIRI(owlClass.getIRI().toString())
                    self.sgnUnsatisfiableClass.emit(projIRI)
                    self._unsatisfiableClasses.add(projIRI)
            #self._unsatisfiableClasses = {x.getIRI().toString() for x in self.javaBottomClassNode.getEntities()}
        except Exception as e:
            LOGGER.exception('Encountered problems while computing unsatisfiable classes.\nError:{}'.format(str(e)))
        else:
            LOGGER.debug('Unsatisfiable classes computed')

    def computeUnsatisfiableObjectProperties(self):
        try:
            self.javaBottomObjectPropertyNode = self.reasonerInstance.getBottomObjectPropertyNode()
            for owlObjProp in self.javaBottomObjectPropertyNode.getEntities():
                if not (owlObjProp.isTopEntity() or owlObjProp.isBottomEntity()):
                    projIRI = self.project.getIRI(owlObjProp.getIRI().toString())
                    self.sgnUnsatisfiableObjectProperty.emit(projIRI)
                    self._unsatisfiableObjectProperties.add(projIRI)
            #self._unsatisfiableObjectProperties = {x.getIRI().toString() for x in self.javaBottomObjectPropertyNode.getEntities()}
        except Exception as e:
            LOGGER.exception('Encountered problems while computing unsatisfiable object properties.\nError:{}'.format(str(e)))
        else:
            LOGGER.debug('Unsatisfiable object properties computed')

    def computeUnsatisfiableDataProperties(self):
        try:
            self.javaBottomDataPropertyNode = self.reasonerInstance.getBottomDataPropertyNode()
            for owlDataProp in self.javaBottomDataPropertyNode.getEntities():
                if not (owlDataProp.isTopEntity() or owlDataProp.isBottomEntity()):
                    projIRI = self.project.getIRI(owlDataProp.getIRI().toString())
                    self.sgnUnsatisfiableDataProperty.emit(projIRI)
                    self._unsatisfiableDataProperties.add(projIRI)
            #self._unsatisfiableDataProperties = {x.getIRI().toString() for x in self.javaBottomDataPropertyNode.getEntities()}
        except Exception as e:
            LOGGER.exception('Encountered problems while computing unsatisfiable data properties.\nError:{}'.format(str(e)))
        else:
            LOGGER.debug('Unsatisfiable data properties computed')

    def runReasoningTasks(self):
        #TODO VALUTA REINSERIMENTO EXPLANATIONS TRAMITE BOOLEANO self.computeExplanations
        worker = OWLOntologyExporterWorker_v3(self.project,axioms=self.axioms())
        worker.run()
        self.initializeOWLManagerAndReasoner(worker.ontology)
        if not self.isConsistent():
            factory = self.ReasonerFactoryClass()
            ecf = self.InconsistentOntologyExplanationGeneratorFactory(factory, 0)
            generator = ecf.createExplanationGenerator(worker.ontology)

            thingISANothing = self.df.getOWLSubClassOfAxiom(self.df.getOWLThing(),self.df.getOWLNothing())

            self.status_bar.showMessage('Computing explanations')
            explanations = generator.getExplanations(thingISANothing)
            self.status_bar.showMessage('Explanations computed')
            for explanation in explanations:
                axiomList = list()
                for axiom in explanation.getAxioms():
                    axiomList.append(axiom.toString())
                self.explanations.append(axiomList)
            self.session.inconsistentOntologyExplanations = self.explanations

            self.sgnInconsistent.emit()
        else:
            self.sgnConsistent.emit()
            if self._computeUnsatisfiableEntities:
                self.computeUnsatisfiableClasses()
                self.computeUnsatisfiableObjectProperties()
                self.computeUnsatisfiableDataProperties()
                unsatisfiableCount = len(self.unsatisfiableClasses) + len(self.unsatisfiableObjectProperties) + len(self.unsatisfiableDataProperties)
                self.sgnUnsatisfiableEntitiesComputed.emit(unsatisfiableCount)

    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.sgnStarted.emit()
            #self.vm.attachThreadToJVM()
            self.runReasoningTasks()
        except Exception as e:
            LOGGER.exception('Fatal error while executing reasoning tasks.\nError:{}'.format(str(e)))
            self.sgnError.emit(e)
        finally:
            self.vm.detachThreadFromJVM()
            self.finished.emit()

class InconsistentOntologyExplanationDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    This class implements the 'Ontology Manager' dialog.
    """

    noPrefixString = ''
    emptyString = ''

    def __init__(self, session, explanations):
        """
        Initialize the Ontology Manager dialog.
        :type session: Session
        :type explanations: list
        """
        super().__init__(session)
        self.explanations = explanations
        self.project = session.project

        #############################################
        # EXPLANATIONS TAB
        #################################

        explanationWidget = ExplanationExplorerWidget(self.project, self.session, objectName='explanation_widget')
        self.addWidget(explanationWidget)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('explanation_widget'))
        groupbox = QtWidgets.QGroupBox('Explanations', self, objectName='explanation_group')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        #############################################
        # MAIN WIDGET
        #################################

        widget = QtWidgets.QTabWidget(self, objectName='main_widget')
        widget.addTab(self.widget('explanation_group'), 'Explanations')
        self.addWidget(widget)

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self, objectName='confirmation_widget')
        #confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        #confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        doneBtn = QtWidgets.QPushButton('Done', objectName='done_button')
        confirmation.addButton(doneBtn, QtWidgets.QDialogButtonBox.AcceptRole)
        confirmation.setContentsMargins(10, 0, 10, 10)
        self.addWidget(confirmation)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(800, 520)
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Inference explanations')
        self.redraw()

        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)


    #############################################
    #   PROPERTIES
    #################################
    @property
    def session(self):
        """
        Returns the reference to the main session (alias for PreferencesDialog.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot()
    def accept(self):
        """
        Executed when the dialog is accepted.
        """
        ##
        ## TODO: complete validation and settings save
        ##
        #############################################
        # GENERAL TAB
        #################################

        #############################################
        # PREFIXES TAB
        #################################

        #############################################
        # ANNOTATIONS TAB
        #################################

        #############################################
        # SAVE & EXIT
        #################################

        super().accept()

    @QtCore.pyqtSlot()
    def reject(self):
        """
        Executed when the dialog is accepted.
        """
        ##
        ## TODO: complete validation and settings save
        ##
        #############################################
        # GENERAL TAB
        #################################

        #############################################
        # PREFIXES TAB
        #################################

        #############################################
        # ANNOTATIONS TAB
        #################################

        #############################################
        # SAVE & EXIT
        #################################

        super().reject()

    @QtCore.pyqtSlot()
    def redraw(self):
        """
        Redraw the dialog components, reloading their contents.
        """
        explanationWidget = self.widget('explanation_widget')
        explanationWidget.doClear()
        explanationWidget.setExplanations(self.explanations)




#############################################
#   EMPTY ENTITIES
#################################
class EmptyEntityDialog(QtWidgets.QDialog, HasThreadingSystem, HasWidgetSystem):
    """
    Extends QtWidgets.QDialog with facilities to list explanations for empty entities
    """
    sgnWork = QtCore.pyqtSignal()
    sgnErrored = QtCore.pyqtSignal()
    sgnExplanationComputed = QtCore.pyqtSignal()

    def __init__(self, project, session, iri, entityType):
        """
        Initialize the dialog.
        :type project: Project
        :type session: Session
        :type iri : IRI
        :type entityType : Item
        """
        super().__init__(session)

        self.project = project
        self.workerThread = None
        self.worker = None
        self.iri = iri
        self.entityType = entityType
        self.explanations = list()

        self.msgbox_busy = QtWidgets.QMessageBox(self)
        self.msgbox_busy.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_busy.setWindowTitle('Please Wait!')
        self.msgbox_busy.setStandardButtons(QtWidgets.QMessageBox.NoButton)
        self.msgbox_busy.setText('Computing explanations...  (Please Wait!)')
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

        self.explanationWidget = ExplanationExplorerWidget(self.project, self.session, objectName='explanation_widget')

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addWidget(self.messageBoxArea)
        self.mainLayout.addWidget(self.explanationWidget)

        self.closeBtn = QtWidgets.QPushButton('Close', objectName='close_button')
        self.closeBtn.setEnabled(False)
        connect(self.closeBtn.clicked, self.onCloseBtnClicked)
        self.addWidget(self.closeBtn)
        self.mainLayout.addWidget(self.closeBtn)

        self.setLayout(self.mainLayout)

        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Please Wait!')
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.CustomizeWindowHint)
        self.setWindowModality(QtCore.Qt.NonModal)

        self.adjustSize()
        #self.setFixedSize(self.width(), self.height())
        self.show()

        connect(self.sgnWork, self.doWork)
        self.sgnWork.emit()


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
        self.sgnWork.emit()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onCloseBtnClicked(self):
        self.close()

    @QtCore.pyqtSlot()
    def doWork(self):
        """
        Perform on or more advancements step in the validation procedure.
        """
        self.worker = EmptyEntityExplanationWorker(self.status_bar, self.project, self.session, self, self.iri, self.entityType)
        connect(self.worker.sgnError, self.onErrorInExec)
        connect(self.worker.sgnExplanationComputed, self.onExplanationComputed)
        self.startThread('EmptyEntityExplanation', self.worker)

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

    @QtCore.pyqtSlot()
    def onExplanationComputed(self):
        """
        Executed when the ontology is inconsistent.
        """
        self.msgbox_busy.setText('Explanations computed')
        self.status_bar.hide()
        self.explanationWidget.setExplanations(self.explanations)
        self.closeBtn.setEnabled(True)
        self.resize(self.sizeHint())
        self.sgnExplanationComputed.emit()

class EmptyEntityExplanationWorker(AbstractWorker):
    """
    Extends AbstractWorker providing a worker thread that will compute explanations for empty entities
    """
    sgnBusy = QtCore.pyqtSignal(bool)
    sgnStarted = QtCore.pyqtSignal()
    sgnError = QtCore.pyqtSignal(Exception)
    sgnExplanationComputed = QtCore.pyqtSignal()

    def __init__(self, status_bar, project, session, dialog, iri, entityType):
        """
        Initialize the syntax validation worker.
        :type current: int
        :type items: list
        :type project: Project
        :type iri : IRI
        :type entityType : Item
        """
        super().__init__()
        self.explanations = list()
        self.project = project
        self.session = session
        self.status_bar = status_bar
        self.dialog = dialog
        self.iri = iri
        self.entityType = entityType
        self.vm = getJavaVM()
        if not self.vm.isRunning():
            self.vm.initialize()
        self.vm.attachThreadToJVM()
        self.ReasonerClass = self.vm.getJavaClass('org.semanticweb.HermiT.Reasoner')
        self.ReasonerFactoryClass = self.vm.getJavaClass('org.semanticweb.HermiT.ReasonerFactory')
        self.ReasonerConfigurationClass = self.vm.getJavaClass('org.semanticweb.HermiT.Configuration')
        self.IRIClass = self.vm.getJavaClass('org.semanticweb.owlapi.model.IRI')
        self.OWLManagerClass = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.JavaFileClass = self.vm.getJavaClass('java.io.File')
        self.URIClass = self.vm.getJavaClass('java.net.URI')
        self.IRIMapperClass = self.vm.getJavaClass('org.semanticweb.owlapi.util.SimpleIRIMapper')
        self.OWLClassClass = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLClass')
        self.OWLImportsEnum = self.vm.getJavaClass('org.semanticweb.owlapi.model.parameters.Imports')
        self.SilentExplanationProgressMonitor = self.vm.getJavaClass(
            'com.clarkparsia.owlapi.explanation.util.SilentExplanationProgressMonitor')
        self.DefaultExplanationGenerator = self.vm.getJavaClass('com.clarkparsia.owlapi.explanation.DefaultExplanationGenerator')
        self.df = None


    def loadImportedOntologiesIntoManager(self):
        LOGGER.debug('Loading declared imports into the OWL 2 Manager')
        self.status_bar.showMessage('Loading declared imports into the OWL 2 Manager')
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
                self.status_bar.showMessage('Ontology ({}) correctly loaded.'.format(impOnt))

    def initializeOWLManagerAndReasoner(self, ontology):
        self.status_bar.showMessage('Initializing the OWL 2 Manager')
        self.manager = ontology.getOWLOntologyManager()
        self.df = self.manager.getOWLDataFactory()
        self.loadImportedOntologiesIntoManager()
        self.status_bar.showMessage('OWL 2 Manager initialized')
        self.status_bar.showMessage('Initializing the OWL 2 reasoner')
        self.reasonerInstance = self.ReasonerClass(self.ReasonerConfigurationClass(), ontology)
        self.status_bar.showMessage('OWL 2 reasoner initialized')
        
    def initializeOWLOntology(self):
        self.status_bar.showMessage('Fetching the OWL 2 ontology')
        worker = OWLOntologyExporterWorker_v3(self.project, axioms={axiom for axiom in OWLAxiom})
        worker.run()
        self.status_bar.showMessage('OWL 2 ontology fetched')
        self.ontology = worker.ontology
        self.initializeOWLManagerAndReasoner(self.ontology)
    
    def getEmptyExpression(self):
        if self.entityType is Item.ConceptIRINode:
            return self.df.getOWLClass(self.IRIClass.create(str(self.iri)))
        elif self.entityType is Item.RoleIRINode:
            objProp = self.df.getOWLObjectProperty(self.IRIClass.create(str(self.iri)))
            return self.df.getOWLObjectSomeValuesFrom(objProp, self.df.getOWLThing())
        else:
            dataProp = self.df.getOWLDataProperty(self.IRIClass.create(str(self.iri)))
            return self.df.getOWLDataSomeValuesFrom(dataProp, self.df.getTopDatatype())

    def computeExplanationAxioms(self):
        progressMonitor = self.SilentExplanationProgressMonitor()
        factory = self.ReasonerFactoryClass()
        explanationGenerator = self.DefaultExplanationGenerator(self.manager, factory, self.ontology, self.reasonerInstance, progressMonitor)
        emptyExpression = self.getEmptyExpression()
        self.status_bar.showMessage('Computing explanations')
        explanations = explanationGenerator.getExplanations(emptyExpression)
        self.status_bar.showMessage('Explanations computed')
        for explanation in explanations:
            axiomList = list()
            for axiom in explanation:
                axiomList.append(axiom.toString())
            self.explanations.append(axiomList)
        self.dialog.explanations = self.explanations
        self.sgnExplanationComputed.emit()

    def getExplanations(self):
        return self.explanations

    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.sgnStarted.emit()
            #self.vm.attachThreadToJVM()
            self.initializeOWLOntology()
            self.computeExplanationAxioms()
        except Exception as e:
            LOGGER.exception('Fatal error while computing explanations.\nError:{}'.format(str(e)))
            self.sgnError.emit(e)
        finally:
            self.vm.detachThreadFromJVM()
            self.finished.emit()


#############################################
#   EXPLANATIONS (INCONSISTENT AND EMPTY) WIDGET
#################################

class ExplanationExplorerWidget(QtWidgets.QWidget):
    """
    This class implements the Explanation explorer used to list Explanation predicates.
    """
    sgnItemClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnItemDoubleClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnItemRightClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnFakeItemAdded = QtCore.pyqtSignal('QGraphicsScene', 'QGraphicsItem')
    sgnColourItem = QtCore.pyqtSignal('QStandardItem')

    def __init__(self, project, session, **kwargs):
        """
        Initialize the Explanation explorer widget.
        """
        super().__init__(session,objectName=kwargs.get('objectName'))

        self.project = project
        self.explanations = None

        self.iconAttribute = QtGui.QIcon(':/icons/18/ic_treeview_attribute')
        self.iconConcept = QtGui.QIcon(':/icons/18/ic_treeview_concept')
        self.iconInstance = QtGui.QIcon(':/icons/18/ic_treeview_instance')
        self.iconRole = QtGui.QIcon(':/icons/18/ic_treeview_role')
        self.iconValue = QtGui.QIcon(':/icons/18/ic_treeview_value')

        self.search = StringField(self)
        self.search.setAcceptDrops(False)
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText('Search...')
        self.search.setFixedHeight(30)
        self.model = QtGui.QStandardItemModel(self)
        self.proxy = QtCore.QSortFilterProxyModel(self)
        self.proxy.setDynamicSortFilter(False)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setSortCaseSensitivity(QtCore.Qt.CaseSensitive)
        self.proxy.setSourceModel(self.model)
        self.ontoview = ExplanationExplorerView(self)
        self.ontoview.setModel(self.proxy)
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.search)
        self.mainLayout.addWidget(self.ontoview)

        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(216)

        self.setStyleSheet("""
            QLineEdit,
            QLineEdit:editable,
            QLineEdit:hover,
            QLineEdit:pressed,
            QLineEdit:focus {
              border: none;
              border-radius: 0;
              background: #FFFFFF;
              color: #000000;
              padding: 4px 4px 4px 4px;
            }
        """)

        header = self.ontoview.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        '''
        connect(self.ontoview.doubleClicked, self.onItemDoubleClicked)
        connect(self.ontoview.pressed, self.onItemPressed)
        connect(self.search.textChanged, self.doFilterItem)
        connect(self.sgnItemDoubleClicked, self.session.doFocusItem)
        connect(self.sgnItemRightClicked, self.session.doFocusItem)

        connect(self.sgnColourItem, self.doColorItems)
        '''

    #############################################
    #   PROPERTIES
    #################################


    @property
    def session(self):
        """
        Returns the reference to the active session.
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   EVENTS
    #################################

    def paintEvent(self, paintEvent):
        """
        This is needed for the widget to pick the stylesheet.
        :type paintEvent: QPaintEvent
        """
        option = QtWidgets.QStyleOption()
        option.initFrom(self)
        painter = QtGui.QPainter(self)
        style = self.style()
        style.drawPrimitive(QtWidgets.QStyle.PE_Widget, option, painter, self)

    #############################################
    #   SLOTS
    #################################
    '''
    @QtCore.pyqtSlot('QStandardItem')
    def doColorItems(self, item):
        row_count = item.rowCount()
        self.session.doResetConsistencyCheck(updateNodes=False, clearReasonerCache=False)
        self.project.nodes_or_edges_of_axioms_to_display_in_widget = []
        self.project.nodes_or_edges_of_explanations_to_display_in_widget = []

        for r in range(row_count):
            child = item.child(r, 0)
            node_or_edge_or_axiom = child.data()

            if 'eddy.core.items' in str(type(node_or_edge_or_axiom)):
                # item is an axiom
                # child is a node or an edge
                explanation_item = item.parent()
                explanation_item_row_count = explanation_item.rowCount()

                for r2 in range(0, explanation_item_row_count):
                    child_of_explanation_item = explanation_item.child(r2, 0)
                    child_of_explanation_item_row_count = child_of_explanation_item.rowCount()

                    for r3 in range(0, child_of_explanation_item_row_count):
                        nephew_or_child = child_of_explanation_item.child(r3, 0)
                        nephew_or_child_data = nephew_or_child.data()

                        if 'eddy.core.items' in str(type(nephew_or_child_data)):
                            if nephew_or_child_data.id == node_or_edge_or_axiom.id:
                                # if (nephew_or_child_data.text() == nephew_or_child_data.text()):
                                # print('nephew_or_child_data not coloured - ',nephew_or_child_data)
                                pass
                            else:
                                self.project.nodes_or_edges_of_explanations_to_display_in_widget.append(
                                    nephew_or_child_data)

                self.project.nodes_or_edges_of_axioms_to_display_in_widget.append(node_or_edge_or_axiom)

            if (str(type(node_or_edge_or_axiom)) == '<class \'str\'>') or (str(type(node_or_edge_or_axiom)) == 'str'):
                # item is an explanation
                # child is an axiom
                # colour all the nodes and edges involved in the axiom
                row_count_2 = child.rowCount()

                for r2 in range(0, row_count_2):
                    grand_child = child.child(r2, 0)
                    node_or_edge = grand_child.data()

                    if 'eddy.core.items' in str(type(node_or_edge)):
                        self.project.nodes_or_edges_of_explanations_to_display_in_widget.append(node_or_edge)

        self.project.colour_items_in_case_of_unsatisfiability_or_inconsistent_ontology()
    '''

    @QtCore.pyqtSlot(str)
    def doAddExplanation(self, explanation_number):
        explanation_number_to_add = QtGui.QStandardItem('Explanation nr {}'.format(explanation_number))
        explanation_number_to_add.setData(explanation_number)
        self.model.appendRow(explanation_number_to_add)
        self.proxy.sort(0, QtCore.Qt.AscendingOrder)
        return explanation_number_to_add

    @QtCore.pyqtSlot('QStandardItem', str)
    def doAddAxiom(self, q_item, axiom):
        axiom_to_add = QtGui.QStandardItem(axiom)
        axiom_to_add.setData(axiom)
        q_item.appendRow(axiom_to_add)
        self.proxy.sort(0, QtCore.Qt.AscendingOrder)

    '''
    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem', 'QStandardItem')
    def doAddNodeOREdge(self, diagram, node_or_edge, q_item):
        icon = None

        if 'eddy.core.items.nodes' in str(type(node_or_edge)):
            button_name = str(node_or_edge.id) + ':' + str(node_or_edge.text())
            icon = self.iconFor(node_or_edge)
        elif 'eddy.core.items.edges' in str(type(node_or_edge)):
            button_name = str(node_or_edge.id) + ':' + str(node_or_edge.type()).replace('Item.', '')

        node_or_edge_to_append = QtGui.QStandardItem(button_name)

        if icon is not None:
            node_or_edge_to_append.setIcon(icon)

        node_or_edge_to_append.setData(node_or_edge)
        q_item.appendRow(node_or_edge_to_append)
    '''

    '''
    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def doAddNode(self, diagram, node):
        """
        Add a node in the tree view.
        :type diagram: QGraphicsScene
        :type node: AbstractItem
        """
        if node.type() in {Item.ConceptNode, Item.RoleNode, Item.AttributeNode, Item.IndividualNode}:
            parent = self.parentFor(node)
            if not parent:
                parent = QtGui.QStandardItem(self.parentKey(node))
                parent.setIcon(self.iconFor(node))
                self.model.appendRow(parent)
                self.proxy.sort(0, QtCore.Qt.AscendingOrder)
            child = QtGui.QStandardItem(self.childKey(diagram, node))
            child.setData(node)
            parent.appendRow(child)
            self.proxy.sort(0, QtCore.Qt.AscendingOrder)
    '''

    @QtCore.pyqtSlot()
    def doClear(self):
        """
        Clear all the nodes in the tree view.
        """
        self.search.clear()
        self.model.clear()
        self.ontoview.update()

    @QtCore.pyqtSlot(str)
    def doFilterItem(self, key):
        """
        Executed when the search box is filled with data.
        :type key: str
        """
        self.proxy.setFilterFixedString(key)
        self.proxy.sort(QtCore.Qt.AscendingOrder)

    '''
    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def doRemoveNode(self, diagram, node):
        """
        Remove a node from the tree view.
        :type diagram: QGraphicsScene
        :type node: AbstractItem
        """
        if node.type() in {Item.ConceptNode, Item.RoleNode, Item.AttributeNode, Item.IndividualNode}:
            parent = self.parentFor(node)
            if parent:
                child = self.childFor(parent, diagram, node)
                if child:
                    parent.removeRow(child.index().row())
                if not parent.rowCount():
                    self.model.removeRow(parent.index().row())
    '''

    '''
    @QtCore.pyqtSlot('QModelIndex')
    def onItemDoubleClicked(self, index):
        """
        Executed when an item in the treeview is double clicked.
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QtWidgets.QApplication.mouseButtons() & QtCore.Qt.LeftButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item and item.data():
                if (str(type(item.data())) == '<class \'str\'>') or (str(type(item.data())) == 'str'):
                    # item is an explanation or an axiom
                    self.sgnColourItem.emit(item)
                else:
                    self.sgnItemDoubleClicked.emit(item.data())
    '''

    '''
    @QtCore.pyqtSlot('QModelIndex')
    def onItemPressed(self, index):
        """
        Executed when an item in the treeview is clicked.
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QtWidgets.QApplication.mouseButtons() & QtCore.Qt.LeftButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item and item.data():
                if (str(type(item.data())) == '<class \'str\'>') or (str(type(item.data())) == 'str'):
                    # item is an explanation or an axiom
                    self.sgnColourItem.emit(item)
                else:
                    self.sgnItemClicked.emit(item.data())
    '''

    #############################################
    #   INTERFACE
    #################################
    def setExplanations(self,explanations):
        self.explanations = explanations
        for index, explanation in enumerate(self.explanations):
            explanationItem = self.doAddExplanation(index+1)
            for axiom in explanation:
                self.doAddAxiom(explanationItem, axiom)
        self.proxy.invalidateFilter()
        self.proxy.sort(0, QtCore.Qt.AscendingOrder)

    '''
    def childFor(self, parent, diagram, node):
        """
        Search the item representing this node among parent children.
        :type parent: QtGui.QStandardItem
        :type diagram: Diagram
        :type node: AbstractNode
        """
        key = self.childKey(diagram, node)
        for i in range(parent.rowCount()):
            child = parent.child(i)
            if child.text() == key:
                return child
        return None
    '''

    '''
    @staticmethod
    def childKey(diagram, node):
        """
        Returns the child key (text) used to place the given node in the treeview.
        :type diagram: Diagram
        :type node: AbstractNode
        :rtype: str
        """
        predicate = node.text().replace('\n', '')
        diagram = rstrip(diagram.name, File.Graphol.extension)
        return '{0} ({1} - {2})'.format(predicate, diagram, node.id)
    '''

    '''
    def iconFor(self, node):
        """
        Returns the icon for the given node.
        :type node:
        """
        if node.type() is Item.AttributeNode:
            return self.iconAttribute
        if node.type() is Item.ConceptNode:
            return self.iconConcept
        if node.type() is Item.IndividualNode:
            if node.identity() is Identity.Individual:
                return self.iconInstance
            if node.identity() is Identity.Value:
                return self.iconValue
        if node.type() is Item.RoleNode:
            return self.iconRole
    '''

    '''
    def parentFor(self, node):
        """
        Search the parent element of the given node.
        :type node: AbstractNode
        :rtype: QtGui.QStandardItem
        """
        for i in self.model.findItems(self.parentKey(node), QtCore.Qt.MatchExactly):
            n = i.child(0).data()
            if node.type() is n.type():
                return i
        return None
    '''

    '''
    @staticmethod
    def parentKey(node):
        """
        Returns the parent key (text) used to place the given node in the treeview.
        :type node: AbstractNode
        :rtype: str
        """
        return node.text().replace('\n', '')
    '''

    def sizeHint(self):
        """
        Returns the recommended size for this widget.
        :rtype: QtCore.QSize
        """
        return QtCore.QSize(216, 266)

class ExplanationExplorerView(QtWidgets.QTreeView):
    """
    This class implements the Explanation explorer tree view.
    """

    def __init__(self, widget):
        """
        Initialize the Explanation explorer view.
        :type widget: ExplanationExplorerWidget
        """
        super().__init__(widget)
        self.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        self.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setHeaderHidden(True)
        self.setHorizontalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setSelectionMode(QtWidgets.QTreeView.SingleSelection)
        self.setSortingEnabled(True)
        self.setWordWrap(True)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the Session holding the ExplanationExplorer widget.
        :rtype: Session
        """
        return self.widget.session

    @property
    def widget(self):
        """
        Returns the reference to the ExplanationExplorer widget.
        :rtype: ExplanationExplorerWidget
        """
        return self.parent()

    #############################################
    #   EVENTS
    #################################

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the treeview.
        :type mouseEvent: QMouseEvent
        """
        self.clearSelection()
        super().mousePressEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the tree view.
        :type mouseEvent: QMouseEvent
        """
        if mouseEvent.button() == QtCore.Qt.RightButton:
            index = first(self.selectedIndexes())
            if index:
                model = self.model().sourceModel()
                index = self.model().mapToSource(index)
                item = model.itemFromIndex(index)
                node_edge_or_axiom = item.data()

                if 'eddy.core.items.nodes' in str(type(item.data())):
                    self.widget.sgnItemRightClicked.emit(node_edge_or_axiom)
                    menu = self.session.mf.create(node_edge_or_axiom.diagram, [node_edge_or_axiom])
                    menu.exec_(mouseEvent.screenPos().toPoint())

        super().mouseReleaseEvent(mouseEvent)

    #############################################
    #   INTERFACE
    #################################

    '''
    def sizeHintForColumn(self, column):
        """
        Returns the size hint for the given column.
        This will make the column of the treeview as wide as the widget that contains the view.
        :type column: int
        :rtype: int
        """
        return max(super().sizeHintForColumn(column), self.viewport().width())
    '''

