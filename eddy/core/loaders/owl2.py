from PyQt5 import QtCore

from eddy.core.common import HasThreadingSystem
from eddy.core.datatypes.system import File
from eddy.core.jvm import getJavaVM
from eddy.core.loaders.common import AbstractOntologyLoader
from eddy.core.output import getLogger
from eddy.core.owl import ImportedOntology
from eddy.core.worker import AbstractWorker

LOGGER = getLogger()

class OwlOntologyImportWorker(AbstractWorker):
    """
    Expose facilities to verify if an OWL ontology can be correctly imported starting from the given parameters
    """
    sgnCompleted = QtCore.pyqtSignal(ImportedOntology)
    sgnErrored = QtCore.pyqtSignal(str,Exception)
    sgnStarted = QtCore.pyqtSignal()
    sgnFinished = QtCore.pyqtSignal()
    sgnStepPerformed = QtCore.pyqtSignal(int)

    TOTAL_STEP_COUNT = 5

    def __init__(self, location, session, isLocalImport=True):
        """
        Initialize the OwlOntologyImportChecker worker.
        :type location: str
        :type isLocalImport: bool
        """
        super().__init__()
        self.location = location
        self.isLocalImport = isLocalImport
        self.project = session.project


        self.vm = getJavaVM()
        if not self.vm.isRunning():
            self.vm.initialize()
        self.vm.attachThreadToJVM()

        self.IRIClass = self.vm.getJavaClass('org.semanticweb.owlapi.model.IRI')
        self.OWLManagerClass = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.JavaFileClass = self.vm.getJavaClass('java.io.File')

    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.sgnStarted.emit()
            self.vm.attachThreadToJVM()
            self.ontology = None
            self.ontologyManager = self.OWLManagerClass.createOWLOntologyManager()
            if self.isLocalImport:
                self.fileInstance = self.JavaFileClass(self.location)
                self.ontology = self.ontologyManager.loadOntologyFromOntologyDocument(self.fileInstance)
            else:
                self.iriInstance = self.IRIClass.create(self.location)
                self.ontology = self.ontologyManager.loadOntology(self.iriInstance)
            self.ontologyId = self.ontology.getOntologyID()
            self.ontologyIRI = ''
            self.optionalOntologyIRI = self.ontologyId.getOntologyIRI()
            if self.optionalOntologyIRI.isPresent():
                self.ontologyIRI = self.optionalOntologyIRI.get().toString()
            self.versionIRI = ''
            self.optionalVersionIRI = self.ontologyId.getVersionIRI()
            if self.optionalVersionIRI.isPresent():
                self.versionIRI = self.optionalOntologyIRI.get().toString()

            importedOntology = ImportedOntology(self.ontologyIRI, self.location, self.versionIRI, self.isLocalImport, self.project)

            self.sgnStepPerformed.emit(1)

            setClasses = self.ontology.getClassesInSignature()
            for c in setClasses:
                if not (c.isOWLThing() or c.isOWLNothing()):
                    iri = self.project.getIRI(c.getIRI().toString(),imported=True)
                    importedOntology.addClass(iri)
            self.sgnStepPerformed.emit(2)

            setObjProps = self.ontology.getObjectPropertiesInSignature()
            for objProp in setObjProps:
                if not (objProp.isOWLTopObjectProperty() or objProp.isOWLBottomObjectProperty()):
                    iri = self.project.getIRI(objProp.getNamedProperty().getIRI().toString(), imported=True)
                    importedOntology.addObjectProperty(iri)
            self.sgnStepPerformed.emit(3)

            setDataProps = self.ontology.getDataPropertiesInSignature()
            for dataProp in setDataProps:
                if not (dataProp.isOWLTopDataProperty() or dataProp.isOWLBottomDataProperty()):
                    iri = self.project.getIRI(dataProp.getIRI().toString(), imported=True)
                    importedOntology.addDataProperty(iri)
            self.sgnStepPerformed.emit(4)

            setIndividuals = self.ontology.getIndividualsInSignature()
            for ind in setIndividuals:
                if not ind.isAnonymous():
                    iri = self.project.getIRI(ind.getIRI().toString(), imported=True)
                    importedOntology.addIndividual(iri)
            self.sgnStepPerformed.emit(5)

        except Exception as e:
            LOGGER.exception('OWL 2 export could not be completed')
            self.sgnErrored.emit(self.location,e)
        else:
            self.sgnCompleted.emit(importedOntology)
        finally:
            self.vm.detachThreadFromJVM()
            self.sgnFinished.emit()


#NOT USED
class OwlOntologyLoader(AbstractOntologyLoader):
    """
    Extends AbstractOntologyLoader with facilities to load ontologies from OWL file format as ImportedOntology into the current project
    """

    def __init__(self, location, project, session, isLocalImport=True):
        super().__init__(location, project, session)
        self.isLocalImport = isLocalImport


    #############################################
    #   INTERFACE
    #################################
    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        return File.Owl

    def run(self):
        """
        Perform ontology import from Graphol file format and merge the loaded ontology with the current project.
        """
        self.createDomDocument()
        self.createProject()
        self.createDiagrams()
        self.projectRender()
        self.projectMerge()

#NOT USED
class OwlOntologyLoaderWorker(AbstractWorker):
    """
    Extends AbstractWorker providing a worker thread that will perform the OWL 2 ontology loading.
    """
    sgnCompleted = QtCore.pyqtSignal()
    sgnErrored = QtCore.pyqtSignal(Exception)
    sgnProgress = QtCore.pyqtSignal(int, int)
    sgnStarted = QtCore.pyqtSignal()

    def __init__(self, project, path, **kwargs):
        """
        Initialize the OWL 2 Exporter worker.
        :type project: Project
        :type path: str
        """
        super().__init__()
