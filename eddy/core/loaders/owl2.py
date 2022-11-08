import os
import sys

from PyQt5 import QtCore
from jpype import JImplements, JOverride

from eddy.core.datatypes.system import File
from eddy.core.jvm import getJavaVM
from eddy.core.loaders.common import AbstractProjectLoader
from eddy.core.output import getLogger
from eddy.core.owl import ImportedOntology
from eddy.core.project import Project
from eddy.core.worker import AbstractWorker

LOGGER = getLogger()


class OwlProjectLoader(AbstractProjectLoader):
    """
    Extends AbstractProjectLoader with facilities to create a project from Owl file.
    """
    def __init__(self, path, session):
        """
        Initialize the loader.
        :param path: path to the OWL 2 file
        :param session: session
        """
        super().__init__(path, session)
        self.nproject = None

    def run(self):
        """
        Perform project import.
        """
        self.createProject()
        self.projectLoaded()

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        return File.Owl

    def createProject(self):
        """
        Create the Project by reading data from the parsed Owl File.
        """
        ontologyIRI, ontologyV = self.getOntologyID()
        self.nproject = Project(
            parent=self.session,
            profile=self.session.createProfile('OWL 2'),
            ontologyIRI=ontologyIRI,
            version=ontologyV
        )
        LOGGER.info('Loaded project from ontology: %s...', self.path)

    def projectLoaded(self):
        """
        Initialize the Session Project to be the loaded one.
        """
        self.session.project = self.nproject

    def getOntologyID(self):
        """
        Get Ontology IRI from Owl File.
        """
        vm = getJavaVM()
        if not vm.isRunning():
            vm.initialize()
        vm.attachThreadToJVM()

        OWLManager = vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
        MissingImportHandlingStrategy = vm.getJavaClass('org.semanticweb.owlapi.model.MissingImportHandlingStrategy')
        JavaFileClass = vm.getJavaClass('java.io.File')
        fileInstance = JavaFileClass(self.path)
        manager = OWLManager().createOWLOntologyManager()
        config = manager.getOntologyLoaderConfiguration()
        config = config.setMissingImportHandlingStrategy(MissingImportHandlingStrategy.SILENT)
        manager.setOntologyLoaderConfiguration(config)
        ontology = manager.loadOntologyFromOntologyDocument(fileInstance)
        ontologyID = ontology.getOntologyID()
        if ontologyID.isAnonymous():
            ontologyIRI = None
            ontologyV = None
        else:
            ontologyIRI = ontologyID.getOntologyIRI().get().toString()
            if ontologyID.getVersionIRI().isPresent():
                ontologyV = ontologyID.getVersionIRI().get().toString()
            else:
                ontologyV = None

        return ontologyIRI, ontologyV


class OwlOntologyImportWorker(AbstractWorker):
    """
    Expose facilities to load an OWL ontology starting from the given parameters
    """
    sgnCompleted = QtCore.pyqtSignal()
    sgnErrored = QtCore.pyqtSignal(str, Exception)
    sgnStarted = QtCore.pyqtSignal()
    sgnFinished = QtCore.pyqtSignal()
    sgnStepPerformed = QtCore.pyqtSignal(int)

    sgnOntologyDocumentLoaded = QtCore.pyqtSignal(str, str, str, bool)
    sgnClassFetched = QtCore.pyqtSignal(str)
    sgnObjectPropertyFetched = QtCore.pyqtSignal(str)
    sgnDataPropertyFetched = QtCore.pyqtSignal(str)
    sgnIndividualFetched = QtCore.pyqtSignal(str)

    sgnMissingOntologyImportFound = QtCore.pyqtSignal(str,str)

    TOTAL_STEP_COUNT = 5

    def __init__(self, location, session, isLocalImport=True, isReloadAttempt=False):
        """
        Initialize the OwlOntologyImportChecker worker.
        :type location: str
        :type isLocalImport: bool
        """
        super().__init__()
        self.location = location
        self.isLocalImport = isLocalImport
        self.project = session.project
        self.isReloadAttempt = isReloadAttempt

        self.vm = getJavaVM()
        if not self.vm.isRunning():
            self.vm.initialize()
        self.vm.attachThreadToJVM()

        self.IRIClass = self.vm.getJavaClass('org.semanticweb.owlapi.model.IRI')
        self.OWLManagerClass = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.JavaFileClass = self.vm.getJavaClass('java.io.File')
        self.iriDocumentSourceClass = self.vm.getJavaClass(
            'org.semanticweb.owlapi.io.IRIDocumentSource')
        self.fileDocumentSourceClass = self.vm.getJavaClass(
            'org.semanticweb.owlapi.io.FileDocumentSource')
        self.ontologyLoaderConfigurationClass = self.vm.getJavaClass(
            'org.semanticweb.owlapi.model.OWLOntologyLoaderConfiguration')
        self.missingImportHandlingStrategyClass = self.vm.getJavaClass(
            'org.semanticweb.owlapi.model.MissingImportHandlingStrategy')

    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.sgnStarted.emit()
            self.vm.attachThreadToJVM()
            missImpListener = PythonMissingImportListener()
            self.ontologyManager = self.OWLManagerClass.createOWLOntologyManager()
            self.ontologyManager.addMissingImportListener(missImpListener)
            loadConf = self.ontologyLoaderConfigurationClass()
            loadConf = loadConf.setMissingImportHandlingStrategy(
                self.missingImportHandlingStrategyClass.SILENT)
            ontDocSrc = None
            if self.isLocalImport:
                fileInstance = self.JavaFileClass(self.location)
                ontDocSrc = self.fileDocumentSourceClass(fileInstance)
            else:
                iriInstance = self.IRIClass.create(self.location)
                ontDocSrc = self.iriDocumentSourceClass(iriInstance)

            ontology = self.ontologyManager.loadOntologyFromOntologyDocument(ontDocSrc, loadConf)

            self.ontologyId = ontology.getOntologyID()
            self.ontologyIRI = ''
            self.optionalOntologyIRI = self.ontologyId.getOntologyIRI()
            if self.optionalOntologyIRI.isPresent():
                self.ontologyIRI = self.optionalOntologyIRI.get().toString()
            self.versionIRI = ''
            self.optionalVersionIRI = self.ontologyId.getVersionIRI()
            if self.optionalVersionIRI.isPresent():
                self.versionIRI = self.optionalOntologyIRI.get().toString()

            if self.ontologyIRI == str(self.project.ontologyIRI):
                raise Exception(
                    'The selected ontology cannot be imported because its IRI "{}" is associated to the working ontology'.format(
                        self.ontologyIRI))
            if not self.isReloadAttempt:
                for impOnt in self.project.importedOntologies:
                    if self.ontologyIRI == str(impOnt.ontologyIRI):
                        raise Exception(
                            'The selected ontology cannot be added to the project because its IRI "{}" is associated to an ontology that has been previously imported'.format(
                                self.ontologyIRI))

            for missingEvent in missImpListener.missingImportEvents:
                self.sgnMissingOntologyImportFound.emit(missingEvent.getImportedOntologyURI().toString(), missingEvent.getCreationException().getMessage())

            self.sgnOntologyDocumentLoaded.emit(self.ontologyIRI, self.location, self.versionIRI,
                                                self.isLocalImport)
            # importedOntology = ImportedOntology(self.ontologyIRI, self.location, self.versionIRI, self.isLocalImport, self.project)

            self.sgnStepPerformed.emit(1)

            setClasses = ontology.getClassesInSignature()
            for c in setClasses:
                if not (c.isOWLThing() or c.isOWLNothing()):
                    self.sgnClassFetched.emit(c.getIRI().toString())
                    # iri = self.project.getIRI(c.getIRI().toString(),imported=True)
                    # importedOntology.addClass(iri)
            self.sgnStepPerformed.emit(2)

            setObjProps = ontology.getObjectPropertiesInSignature()
            for objProp in setObjProps:
                if not (objProp.isOWLTopObjectProperty() or objProp.isOWLBottomObjectProperty()):
                    self.sgnObjectPropertyFetched.emit(objProp.getIRI().toString())
                    # iri = self.project.getIRI(objProp.getNamedProperty().getIRI().toString(), imported=True)
                    # importedOntology.addObjectProperty(iri)
            self.sgnStepPerformed.emit(3)

            setDataProps = ontology.getDataPropertiesInSignature()
            for dataProp in setDataProps:
                if not (dataProp.isOWLTopDataProperty() or dataProp.isOWLBottomDataProperty()):
                    self.sgnDataPropertyFetched.emit(dataProp.getIRI().toString())
                    # iri = self.project.getIRI(dataProp.getIRI().toString(), imported=True)
                    # importedOntology.addDataProperty(iri)
            self.sgnStepPerformed.emit(4)

            setIndividuals = ontology.getIndividualsInSignature()
            for ind in setIndividuals:
                if not ind.isAnonymous():
                    self.sgnIndividualFetched.emit(ind.getIRI().toString())
                    # iri = self.project.getIRI(ind.getIRI().toString(), imported=True)
                    # importedOntology.addIndividual(iri)
            self.sgnStepPerformed.emit(5)

        except Exception as e:
            LOGGER.exception('OWL 2 import could not be completed')
            self.sgnErrored.emit(self.location, e)
        else:
            self.sgnCompleted.emit()
        finally:
            self.vm.detachThreadFromJVM()
            self.sgnFinished.emit()


class OwlOntologyImportSetWorker(AbstractWorker):
    """
    Expose facilities to load a set of OWL ontologies starting from import declarations
    """
    sgnCompleted = QtCore.pyqtSignal(int, int)
    sgnErrored = QtCore.pyqtSignal(ImportedOntology, Exception)
    sgnStarted = QtCore.pyqtSignal()
    sgnFinished = QtCore.pyqtSignal()

    def __init__(self, project, toBeLoaded=None):
        """
        Initialize the OwlOntologyImportChecker worker.
        :type project: Project
        """
        super().__init__()
        self.imports = project.importedOntologies
        self.project = project
        self.toBeLoaded = toBeLoaded

        self.vm = getJavaVM()
        if not self.vm.isRunning():
            self.vm.initialize()
        self.vm.attachThreadToJVM()

        self.IRIClass = self.vm.getJavaClass('org.semanticweb.owlapi.model.IRI')
        self.OWLManagerClass = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.JavaFileClass = self.vm.getJavaClass('java.io.File')
        self._owlOtologyImportErrors = set()
        self._loadCount = 0

    @property
    def importSize(self):
        return len(self.imports)

    @property
    def loadCount(self):
        return self._loadCount

    @property
    def owlOntologyImportErrors(self):
        return self._owlOtologyImportErrors

    @QtCore.pyqtSlot(str, Exception)
    def onImportError(self, location, exc):
        self._owlOtologyImportErrors.update([(location, str(exc))])

    @QtCore.pyqtSlot()
    def run(self):

        try:
            self.sgnStarted.emit()
            self.vm.attachThreadToJVM()
            self.ontologyManager = self.OWLManagerClass.createOWLOntologyManager()
            for impOnt in self.imports:
                if not self.toBeLoaded or impOnt.ontologyIRI in self.toBeLoaded:
                    try:
                        ontology = None
                        if impOnt.isLocalDocument:
                            fileInstance = self.JavaFileClass(impOnt.docLocation)
                            ontology = self.ontologyManager.loadOntologyFromOntologyDocument(
                                fileInstance)
                        else:
                            iriInstance = self.IRIClass.create(impOnt.docLocation)
                            ontology = self.ontologyManager.loadOntology(iriInstance)
                        ontologyId = ontology.getOntologyID()
                        ontologyIRI = None
                        optionalOntologyIRI = ontologyId.getOntologyIRI()
                        if optionalOntologyIRI.isPresent():
                            ontologyIRI = optionalOntologyIRI.get().toString()
                        versionIRI = None
                        optionalVersionIRI = ontologyId.getVersionIRI()
                        if optionalVersionIRI.isPresent():
                            versionIRI = optionalOntologyIRI.get().toString()

                        if ontologyIRI:
                            impOnt.ontologyIRI = ontologyIRI
                        if versionIRI:
                            impOnt.versionIRI = versionIRI

                        setClasses = ontology.getClassesInSignature()
                        for c in setClasses:
                            if not (c.isOWLThing() or c.isOWLNothing()):
                                iri = self.project.getIRI(c.getIRI().toString(), imported=True)
                                impOnt.addClass(iri)

                        setObjProps = ontology.getObjectPropertiesInSignature()
                        for objProp in setObjProps:
                            if not (
                                objProp.isOWLTopObjectProperty() or objProp.isOWLBottomObjectProperty()):
                                iri = self.project.getIRI(
                                    objProp.getNamedProperty().getIRI().toString(), imported=True)
                                impOnt.addObjectProperty(iri)

                        setDataProps = ontology.getDataPropertiesInSignature()
                        for dataProp in setDataProps:
                            if not (
                                dataProp.isOWLTopDataProperty() or dataProp.isOWLBottomDataProperty()):
                                iri = self.project.getIRI(dataProp.getIRI().toString(),
                                                          imported=True)
                                impOnt.addDataProperty(iri)

                        setIndividuals = ontology.getIndividualsInSignature()
                        for ind in setIndividuals:
                            if not ind.isAnonymous():
                                iri = self.project.getIRI(ind.getIRI().toString(), imported=True)
                                impOnt.addIndividual(iri)
                    except Exception as e:
                        LOGGER.exception(
                            'The ontology located in {} cannot be correctly loaded'.format(
                                impOnt.docLocation))
                        impOnt.correctlyLoaded = False
                        self.sgnErrored.emit(impOnt, e)
                    else:
                        self._loadCount += 1
                        impOnt.correctlyLoaded = True
                        self.project.sgnImportedOntologyLoaded.emit(impOnt)
        except Exception as e:
            LOGGER.exception('Fatal exception while resolving ontology imports: {}'.format(str(e)))
        else:
            LOGGER.info('Found {} import declarations, {} loaded'.format(len(self.imports),
                                                                         self._loadCount))
            self.sgnCompleted.emit(self._loadCount, len(self.imports))
        finally:
            self.vm.detachThreadFromJVM()
            self.sgnFinished.emit()


@JImplements("org.semanticweb.owlapi.model.MissingImportListener", deferred=True)
class PythonMissingImportListener:

    def __init__(self):
        self.missingImportEvents = list()

    @JOverride
    def importMissing(self, missingImportEvent):
        self.missingImportEvents.append(missingImportEvent)
