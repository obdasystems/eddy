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

from eddy.core.common import HasThreadingSystem
from eddy.core.datatypes.graphol import Special
from eddy.core.datatypes.owl import OWLAxiom, OWLSyntax
from eddy.core.datatypes.qt import Font
from eddy.core.exporters.owl2 import OWLOntologyFetcher
from eddy.core.exporters.owl2_iri import OWLOntologyExporterWorker
from eddy.core.functions.signals import connect
from eddy.core.jvm import getJavaVM
from eddy.core.output import getLogger
from eddy.core.owl import IRI
from eddy.core.worker import AbstractWorker

LOGGER = getLogger()


class OntologyConsistencyCheckDialog(QtWidgets.QDialog, HasThreadingSystem):
    """
    Extends QtWidgets.QDialog with facilities to perform Ontology Consistency check
    """
    sgnWork = QtCore.pyqtSignal()
    sgnErrored = QtCore.pyqtSignal()
    sgnOntologyConsistent = QtCore.pyqtSignal()
    sgnOntologyInconsistent = QtCore.pyqtSignal()
    sgnUnsatisfiableEntities = QtCore.pyqtSignal(int)

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
            self.msgbox_done.setWindowTitle('Ontology consistency check complete')
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
        self.msgbox_done.setWindowTitle('Ontology consistency check complete')
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

class OntologyReasoningTasksWorker(AbstractWorker):
    """
    Extends QtCore.QObject providing a worker thread that will perform the consistency check over the Project ontology
    """
    sgnBusy = QtCore.pyqtSignal(bool)
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
        #self.ReasonerClass = self.vm.getJavaClass('org.semanticweb.HermiT.Reasoner')
        self.ReasonerFactoryClass = self.vm.getJavaClass('org.semanticweb.HermiT.ReasonerFactory')
        self.ReasonerConfigurationClass = self.vm.getJavaClass('org.semanticweb.HermiT.Configuration')
        self.IRIClass = self.vm.getJavaClass('org.semanticweb.owlapi.model.IRI')
        self.OWLManagerClass = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.JavaFileClass = self.vm.getJavaClass('java.io.File')
        self.URIClass = self.vm.getJavaClass('java.net.URI')

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
                docLocationIRI = self.IRI.create(docObj)
                impOntIRI = self.IRI.create(impOnt.ontologyIRI)
                iriMapper = self.IRIMapperClass(impOntIRI, docLocationIRI)
                self.manager.getIRIMappers().add(iriMapper)
                self.manager.loadOntology(impOntIRI)
            except Exception as e:
                LOGGER.exception('The imported ontology <{}> cannot be loaded.\nError:{}'.format(impOnt, str(e)))
            else:
                LOGGER.debug('Ontology ({}) correctly loaded.'.format(impOnt))

    def initializeOWLManagerAndReasoner(self, ontology):
        self.manager = self.OWLManager.createOWLOntologyManager()
        self.loadImportedOntologiesIntoManager()
        self.reasonerInstance = self.ReasonerFactoryClass.createReasoner(ontology, self.ReasonerConfigurationClass())

    def isConsistent(self):
        return self.reasonerInstance.isConsistent()

    def computeUnsatisfiableClasses(self):
        try:
            self.javaBottomClassNode = self.reasonerInstance.getBottomClassNode()
            for owlClass in self.javaBottomClassNode.getEntities:
                projIRI = self.project.getIRI(owlClass.getIRI().toString())
                self.sgnUnsatisfiableClass.emit(projIRI)
                self._unsatisfiableClasses.add(projIRI)
            #self._unsatisfiableClasses = {x.getIRI().toString() for x in self.javaBottomClassNode.getEntities}
        except Exception as e:
            LOGGER.exception('Encountered problems while computing unsatisfiable classes.\nError:{}'.format(str(e)))
        else:
            LOGGER.debug('Unsatisfiable classes computed')

    def computeUnsatisfiableObjectProperties(self):
        try:
            self.javaBottomObjectPropertyNode = self.reasonerInstance.getBottomObjectPropertyNode()
            for owlObjProp in self.javaBottomObjectPropertyNode.getEntities:
                projIRI = self.project.getIRI(owlObjProp.getIRI().toString())
                self.sgnUnsatisfiableObjectProperty.emit(projIRI)
                self._unsatisfiableObjectProperties.add()
            #self._unsatisfiableObjectProperties = {x.getIRI().toString() for x in self.javaBottomObjectPropertyNode.getEntities}
        except Exception as e:
            LOGGER.exception('Encountered problems while computing unsatisfiable object properties.\nError:{}'.format(str(e)))
        else:
            LOGGER.debug('Unsatisfiable object properties computed')

    def computeUnsatisfiableDataProperties(self):
        try:
            self.javaBottomDataPropertyNode = self.reasonerInstance.getBottomDataPropertyNode()
            for owlDataProp in self.javaBottomDataPropertyNode.getEntities:
                projIRI = self.project.getIRI(owlDataProp.getIRI().toString())
                self.sgnUnsatisfiableDataProperty.emit(projIRI)
                self._unsatisfiableDataProperties.add(projIRI)
            #self._unsatisfiableDataProperties = {x.getIRI().toString() for x in self.javaBottomDataPropertyNode.getEntities}
        except Exception as e:
            LOGGER.exception('Encountered problems while computing unsatisfiable data properties.\nError:{}'.format(str(e)))
        else:
            LOGGER.debug('Unsatisfiable data properties computed')

    def runReasoningTasks(self):
        #TODO VALUTA REINSERIMENTO EXPLANATIONS TRAMITE BOOLEANO self.computeExplanations
        worker = OWLOntologyExporterWorker(self.project)
        worker.run()
        self.initializeOWLManagerAndReasoner(worker.ontology)
        if not self.isConsistent():
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
            self.vm.attachThreadToJVM()
            self.runReasoningTasks()
        except Exception as e:
            LOGGER.exception('Fatal error while executing reasoning tasks.\nError:{}'.format(str(e)))
            self.sgnError.emit(e)
        finally:
            self.vm.detachThreadFromJVM()
            self.finished.emit()



#TODO NOT TO BE USED ANYMORE BECAUSOF THE EXPLANATION COMPUTATION
class OntologyExplanationsWorker(AbstractWorker):
    """
    Extends QtCore.QObject providing a worker thread that will perform all reasoning tasks (unsatisfiable entities, consistency)
    over the Ontology induced by the diagrams (NO OWL IMPORT TAKEN INTO ACCOUNT) and will compute all the possible explanations
    """
    sgnBusy = QtCore.pyqtSignal(bool)
    sgnAllOK = QtCore.pyqtSignal()
    sgnOntologyInconsistency = QtCore.pyqtSignal()
    sgnUnsatisfiableEntities = QtCore.pyqtSignal()
    sgnError = QtCore.pyqtSignal()

    def __init__(self, status_bar, project, session):
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
        self.Iterator = self.vm.getJavaClass('java.util.Iterator')
        self.String = self.vm.getJavaClass('java.lang.String')
        self.Object = self.vm.getJavaClass('java.lang.Object')
        self.Configuration = self.vm.getJavaClass('org.semanticweb.HermiT.Configuration')
        self.Reasoner = self.vm.getJavaClass('org.semanticweb.HermiT.Reasoner')
        self.ReasonerFactory = self.vm.getJavaClass('org.semanticweb.HermiT.ReasonerFactory')
        self.Explanation = self.vm.getJavaClass('org.semanticweb.owl.explanation.api.Explanation')
        self.ExplanationGenerator = self.vm.getJavaClass('org.semanticweb.owl.explanation.api.ExplanationGenerator')
        self.InconsistentOntologyExplanationGeneratorFactory = self.vm.getJavaClass(
            'org.semanticweb.owl.explanation.impl.blackbox.checker.InconsistentOntologyExplanationGeneratorFactory')
        # self.BlackBoxExplanation = self.vm.getJavaClass('com.clarkparsia.owlapi.explanation.BlackBoxExplanation')
        self.SilentExplanationProgressMonitor = self.vm.getJavaClass(
            'com.clarkparsia.owlapi.explanation.util.SilentExplanationProgressMonitor')
        self.DefaultExplanationGenerator = self.vm.getJavaClass(
            'com.clarkparsia.owlapi.explanation.DefaultExplanationGenerator')
        self.OWLFunctionalSyntaxFactory = self.vm.getJavaClass(
            'org.semanticweb.owlapi.apibinding.OWLFunctionalSyntaxFactory')
        self.OWLManager = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.IRI = self.vm.getJavaClass('org.semanticweb.owlapi.model.IRI')
        self.OWLAxiom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLAxiom')
        self.OWLClass = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLClass')
        self.OWLClassExpression = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLClassExpression')
        self.OWLDataProperty = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLDataProperty')
        self.OWLDatatype = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLDatatype')
        self.OWLEntity = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLEntity')
        self.OWLNamedIndividual = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLNamedIndividual')
        self.OWLObjectProperty = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLObjectProperty')
        self.OWLObjectPropertyExpression = self.vm.getJavaClass(
            'org.semanticweb.owlapi.model.OWLObjectPropertyExpression')
        self.OWLOntology = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLOntology')
        self.OWLOntologyCreationException = self.vm.getJavaClass(
            'org.semanticweb.owlapi.model.OWLOntologyCreationException')
        self.OWLOntologyManager = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLOntologyManager')
        # self.OWLSubClassOfAxiom = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLSubClassOfAxiom')
        self.InconsistentOntologyException = self.vm.getJavaClass(
            'org.semanticweb.owlapi.reasoner.InconsistentOntologyException')
        self.Node = self.vm.getJavaClass('org.semanticweb.owlapi.reasoner.Node')
        self.InconsistentOntologyException_string = 'JVM exception occurred: Inconsistent ontology'

    def axioms(self):
        """
        Returns the set of axioms that needs to be exported.
        :rtype: set
        """
        return {axiom for axiom in OWLAxiom}

    @QtCore.pyqtSlot()
    def onCompleted(self):
        self.accept()

    def fetch_axioms_and_set_variables(self, bottom_entity_node, java_class):
        self.status_bar.showMessage('Ontology is inconsistent; Fetching explanations for the same')

        if java_class == self.OWLClass:
            self.status_bar.showMessage('Fetching explanations for unsatisfiable class(es)')
        elif java_class == self.OWLDataProperty:
            self.status_bar.showMessage('Fetching explanations for unsatisfiable attribute(s)')
        elif java_class == self.OWLObjectPropertyExpression:
            self.status_bar.showMessage('Fetching explanations for unsatisfiable role(s)')
        else:
            self.status_bar.showMessage('')

        entities_of_bottom_entity_node = bottom_entity_node.getEntities()
        entities_of_bottom_entity_node_itr = entities_of_bottom_entity_node.iterator()
        unsatisfiable_entities_string = []
        explanations_for_all_unsatisfiable_entities = []

        while entities_of_bottom_entity_node_itr.hasNext():
            unsatisfiable_entity = entities_of_bottom_entity_node_itr.next()

            if unsatisfiable_entity.toString() in Special.BottomEntities.value.values():
                continue

            unsatisfiable_entities_string.append(unsatisfiable_entity.toString())
            explanations_for_unsatisfiable_entity = []
            axioms_of_explanations = []

            if java_class == self.OWLClass:
                axiom_err = self.manager.getOWLDataFactory().getOWLSubClassOfAxiom(
                    unsatisfiable_entity, self.OWLFunctionalSyntaxFactory.OWLNothing())
            elif java_class == self.OWLDataProperty:
                exists_for_some_values = self.OWLFunctionalSyntaxFactory.DataSomeValuesFrom(
                    unsatisfiable_entity, self.OWLFunctionalSyntaxFactory.TopDatatype())
                axiom_err = self.manager.getOWLDataFactory().getOWLSubClassOfAxiom(
                    exists_for_some_values, self.OWLFunctionalSyntaxFactory.OWLNothing())
            elif java_class == self.OWLObjectPropertyExpression:
                exists_for_some_objects = self.OWLFunctionalSyntaxFactory.ObjectSomeValuesFrom(
                    unsatisfiable_entity, self.OWLFunctionalSyntaxFactory.OWLThing())
                axiom_err = self.manager.getOWLDataFactory().getOWLSubClassOfAxiom(
                    exists_for_some_objects, self.OWLFunctionalSyntaxFactory.OWLNothing())
            else:
                raise RuntimeError('Invalid unsatisfiable entity {0}'.format(java_class))

            axiom_err_sc = axiom_err.getSubClass()
            explanations_raw = self.generator_unsatisfiable_entities.getExplanations(axiom_err_sc)
            explanations_raw_itr = explanations_raw.iterator()

            while explanations_raw_itr.hasNext():
                expl_raw = explanations_raw_itr.next()
                explanations_for_unsatisfiable_entity.append(expl_raw)
                axioms_of_expl = []
                axioms_itr = expl_raw.iterator()

                # get axioms for the explanation
                while axioms_itr.hasNext():
                    axiom_raw = axioms_itr.next()
                    axioms_of_expl.append(axiom_raw.toString())
                axioms_of_explanations.append(axioms_of_expl)
            explanations_for_all_unsatisfiable_entities.append(explanations_for_unsatisfiable_entity)

        if java_class == self.OWLClass:
            self.project.unsatisfiable_classes = unsatisfiable_entities_string
            self.project.explanations_for_unsatisfiable_classes = explanations_for_all_unsatisfiable_entities
        elif java_class == self.OWLDataProperty:
            self.project.unsatisfiable_attributes = unsatisfiable_entities_string
            self.project.explanations_for_unsatisfiable_attributes = explanations_for_all_unsatisfiable_entities
        elif java_class == self.OWLObjectPropertyExpression:
            self.project.unsatisfiable_roles = unsatisfiable_entities_string
            self.project.explanations_for_unsatisfiable_roles = explanations_for_all_unsatisfiable_entities
        else:
            raise RuntimeError('invalid unsatisfiable entity {0}'.format(java_class))

    def reason_over_ontology(self):
        self.status_bar.showMessage('Fetching ontology')

        worker = OWLOntologyFetcher(self.project, axioms=self.axioms(), normalize=False, syntax=OWLSyntax.Functional)
        worker.run()

        self.vm.attachThreadToJVM()
        errored_message = worker.errored_message
        if errored_message is not None:
            self.status_bar.showMessage(errored_message)
            self.project.inconsistent_ontology = None
            LOGGER.error(errored_message)
            return

        dict = worker.refined_axiom_to_node_or_edge
        ontology = worker.ontology

        if ontology is None:
            LOGGER.warning('ontology is None')
        else:
            LOGGER.info('ontology is not None')

        self.project.axioms_to_nodes_edges_mapping = dict
        self.project.ontology_OWL = ontology

        self.manager = self.OWLManager.createOWLOntologyManager()
        configuration = self.Configuration()

        try:
            hermit = self.Reasoner(configuration, ontology)
        except Exception as e0:
            self.project.inconsistent_ontology = None
            LOGGER.error(str(e0))
            return

        progressMonitor = self.SilentExplanationProgressMonitor()
        self.status_bar.showMessage('Running reasoner over ontology')

        try:
            hermit.precomputeInferences()

            if hermit.isConsistent() is True:
                self.project.inconsistent_ontology = False
            else:
                raise RuntimeError('ontology is inconsistent however exception was not thrown')

            factory = self.ReasonerFactory()

            self.generator_unsatisfiable_entities = self.DefaultExplanationGenerator(
                self.manager, factory, ontology, hermit, progressMonitor)

            # BottomClass
            bottom_class_node = hermit.getBottomClassNode()
            bottom_data_property_node = hermit.getBottomDataPropertyNode()
            bottom_object_property_node = hermit.getBottomObjectPropertyNode()
            self.fetch_axioms_and_set_variables(bottom_class_node, self.OWLClass)
            self.fetch_axioms_and_set_variables(bottom_data_property_node, self.OWLDataProperty)
            self.fetch_axioms_and_set_variables(bottom_object_property_node, self.OWLObjectPropertyExpression)
        except Exception as e:
            if not hermit.isConsistent():
                self.status_bar.showMessage('Ontology is inconsistent; Fetching explanations for the same')
                self.project.inconsistent_ontology = True
                factory = self.ReasonerFactory()
                ecf = self.InconsistentOntologyExplanationGeneratorFactory(factory, 0)
                generator = ecf.createExplanationGenerator(ontology)
                axiom = self.manager.getOWLDataFactory().getOWLSubClassOfAxiom(
                    self.OWLFunctionalSyntaxFactory.OWLThing(), self.OWLFunctionalSyntaxFactory.OWLNothing())

                try:
                    explanations = generator.getExplanations(axiom)
                    explanations_itr = explanations.iterator()

                    while explanations_itr.hasNext():
                        explanation = explanations_itr.next()
                        self.project.explanations_for_inconsistent_ontology.append(explanation)

                except Exception as ex:
                    ex.printStackTrace()
            else:
                self.project.inconsistent_ontology = None
                LOGGER.error(str(e))
        finally:
            hermit.flush()
            hermit.dispose()

    @QtCore.pyqtSlot()
    def run(self):
        """
        Main worker.
        """
        self.reason_over_ontology()

        if self.project.inconsistent_ontology is not None:
            if self.project.inconsistent_ontology is True:
                self.sgnOntologyInconsistency.emit()
            else:
                if len(self.project.unsatisfiable_classes) or len(self.project.unsatisfiable_attributes) or len(
                        self.project.unsatisfiable_roles):
                    self.sgnUnsatisfiableEntities.emit()
                else:
                    self.sgnAllOK.emit()
            self.finished.emit()
        else:
            self.sgnError.emit()
