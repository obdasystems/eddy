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
from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.owl import OWLAxiom
from eddy.core.exporters.owl2 import OWLOntologyExporterWorker
from eddy.core.functions.signals import connect
from eddy.core.jvm import getJavaVM
from eddy.core.output import getLogger
from eddy.core.owl import IRI
from eddy.core.worker import AbstractWorker

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
        #self.setWindowModality(QtCore.Qt.NonModal)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

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
        self.session.doResetConsistencyCheck()

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
        self.msgbox_done.setText('<p>Ontology is inconsistent.</p>'
                                 '<p>You may choose to display Explanations by pressing the "?" button in the toolbar</p>'
                                 '<p>To reset the reasoner '
                                 'press the Reset button in the toolbar.</p>')
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
                                     '<p>See highlighted entries in the Ontology Explorer for details: '
                                     'you may choose to display Explanations by right-clicking on them.</p>'
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
        worker = OWLOntologyExporterWorker(self.project,axioms=self.axioms())
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

#############################################
#   EMPTY ENTITIES
#################################
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
        worker = OWLOntologyExporterWorker(self.project, axioms={axiom for axiom in OWLAxiom})
        worker.run()
        self.status_bar.showMessage('OWL 2 ontology fetched')
        self.ontology = worker.ontology
        self.initializeOWLManagerAndReasoner(self.ontology)

    def getEmptyExpression(self):
        if self.entityType is Item.ConceptNode:
            return self.df.getOWLClass(self.IRIClass.create(str(self.iri)))
        elif self.entityType is Item.RoleNode:
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
        self.session.currentEmptyEntityExplanations = self.explanations
        key = '{}-{}'.format(str(self.iri), self.entityType)
        self.session.emptyEntityExplanations[key] = self.explanations
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


