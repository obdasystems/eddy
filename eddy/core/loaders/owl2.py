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
    Expose facilities to load an OWL ontology starting from the given parameters
    """
    sgnCompleted = QtCore.pyqtSignal()
    sgnErrored = QtCore.pyqtSignal(str,Exception)
    sgnStarted = QtCore.pyqtSignal()
    sgnFinished = QtCore.pyqtSignal()
    sgnStepPerformed = QtCore.pyqtSignal(int)

    sgnOntologyDocumentLoaded = QtCore.pyqtSignal(str,str,str,bool)
    sgnClassFetched = QtCore.pyqtSignal(str)
    sgnObjectPropertyFetched= QtCore.pyqtSignal(str)
    sgnDataPropertyFetched = QtCore.pyqtSignal(str)
    sgnIndividualFetched = QtCore.pyqtSignal(str)

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

    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.sgnStarted.emit()
            self.vm.attachThreadToJVM()
            ontology = None
            self.ontologyManager = self.OWLManagerClass.createOWLOntologyManager()
            if self.isLocalImport:
                fileInstance = self.JavaFileClass(self.location)
                ontology = self.ontologyManager.loadOntologyFromOntologyDocument(fileInstance)
            else:
                iriInstance = self.IRIClass.create(self.location)
                ontology = self.ontologyManager.loadOntology(iriInstance)
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
                raise Exception('The selected ontology cannot be imported because its IRI "{}" is associated to the working ontology'.format(self.ontologyIRI))
            if not self.isReloadAttempt:
                for impOnt in self.project.importedOntologies:
                    if self.ontologyIRI == str(impOnt.ontologyIRI):
                        raise Exception(
                            'The selected ontology cannot be added to the project because its IRI "{}" is associated to an ontology that has been previously imported'.format(
                                self.ontologyIRI))

            self.sgnOntologyDocumentLoaded.emit(self.ontologyIRI, self.location, self.versionIRI, self.isLocalImport)
            #importedOntology = ImportedOntology(self.ontologyIRI, self.location, self.versionIRI, self.isLocalImport, self.project)

            self.sgnStepPerformed.emit(1)

            setClasses = ontology.getClassesInSignature()
            for c in setClasses:
                if not (c.isOWLThing() or c.isOWLNothing()):
                    self.sgnClassFetched.emit(c.getIRI().toString())
                    #iri = self.project.getIRI(c.getIRI().toString(),imported=True)
                    #importedOntology.addClass(iri)
            self.sgnStepPerformed.emit(2)

            setObjProps = ontology.getObjectPropertiesInSignature()
            for objProp in setObjProps:
                if not (objProp.isOWLTopObjectProperty() or objProp.isOWLBottomObjectProperty()):
                    self.sgnObjectPropertyFetched.emit(c.getIRI().toString())
                    #iri = self.project.getIRI(objProp.getNamedProperty().getIRI().toString(), imported=True)
                    #importedOntology.addObjectProperty(iri)
            self.sgnStepPerformed.emit(3)

            setDataProps = ontology.getDataPropertiesInSignature()
            for dataProp in setDataProps:
                if not (dataProp.isOWLTopDataProperty() or dataProp.isOWLBottomDataProperty()):
                    self.sgnDataPropertyFetched.emit(c.getIRI().toString())
                    #iri = self.project.getIRI(dataProp.getIRI().toString(), imported=True)
                    #importedOntology.addDataProperty(iri)
            self.sgnStepPerformed.emit(4)

            setIndividuals = ontology.getIndividualsInSignature()
            for ind in setIndividuals:
                if not ind.isAnonymous():
                    self.sgnIndividualFetched.emit(c.getIRI().toString())
                    #iri = self.project.getIRI(ind.getIRI().toString(), imported=True)
                    #importedOntology.addIndividual(iri)
            self.sgnStepPerformed.emit(5)

        except Exception as e:
            LOGGER.exception('OWL 2 import could not be completed')
            self.sgnErrored.emit(self.location,e)
        else:
            self.sgnCompleted.emit()
        finally:
            self.vm.detachThreadFromJVM()
            self.sgnFinished.emit()


class OwlOntologyImportSetWorker(AbstractWorker):
    """
    Expose facilities to load a set of OWL ontologies starting from import declarations
    """
    sgnCompleted = QtCore.pyqtSignal(int,int)
    sgnErrored = QtCore.pyqtSignal(ImportedOntology,Exception)
    sgnStarted = QtCore.pyqtSignal()
    sgnFinished = QtCore.pyqtSignal()

    def __init__(self,project):
        """
        Initialize the OwlOntologyImportChecker worker.
        :type project: Project
        """
        super().__init__()
        self.imports = project.importedOntologies
        self.project = project

        self.vm = getJavaVM()
        if not self.vm.isRunning():
            self.vm.initialize()
        self.vm.attachThreadToJVM()

        self.IRIClass = self.vm.getJavaClass('org.semanticweb.owlapi.model.IRI')
        self.OWLManagerClass = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.JavaFileClass = self.vm.getJavaClass('java.io.File')

    @QtCore.pyqtSlot()
    def run(self):
        loadCount = 0
        try:
            self.sgnStarted.emit()
            self.vm.attachThreadToJVM()
            self.ontologyManager = self.OWLManagerClass.createOWLOntologyManager()
            for impOnt in self.imports:
                try:
                    ontology = None
                    if impOnt.isLocalDocument:
                        fileInstance = self.JavaFileClass(impOnt.docLocation)
                        ontology = self.ontologyManager.loadOntologyFromOntologyDocument(fileInstance)
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
                            iri = self.project.getIRI(c.getIRI().toString(),imported=True)
                            impOnt.addClass(iri)

                    setObjProps = ontology.getObjectPropertiesInSignature()
                    for objProp in setObjProps:
                        if not (objProp.isOWLTopObjectProperty() or objProp.isOWLBottomObjectProperty()):
                            iri = self.project.getIRI(objProp.getNamedProperty().getIRI().toString(), imported=True)
                            impOnt.addObjectProperty(iri)

                    setDataProps = ontology.getDataPropertiesInSignature()
                    for dataProp in setDataProps:
                        if not (dataProp.isOWLTopDataProperty() or dataProp.isOWLBottomDataProperty()):
                            iri = self.project.getIRI(dataProp.getIRI().toString(), imported=True)
                            impOnt.addDataProperty(iri)

                    setIndividuals = ontology.getIndividualsInSignature()
                    for ind in setIndividuals:
                        if not ind.isAnonymous():
                            iri = self.project.getIRI(ind.getIRI().toString(), imported=True)
                            impOnt.addIndividual(iri)
                    loadCount+=1
                except Exception as e:
                    LOGGER.exception('The ontology located in {} cannot be correctly loaded'.format(impOnt.docLocation))
                    impOnt.correctlyLoaded = False
                    self.sgnErrored.emit(impOnt, e)
                else:
                    loadCount += 1
                    impOnt.correctlyLoaded = True
        except Exception as e:
            LOGGER.exception('Fatal exception while resolving ontology imports: {}'.format(str(e)))
        else:
            LOGGER.info('Found {} import declarations, {} loaded'.format(len(self.imports),loadCount))
            self.sgnCompleted.emit(loadCount, len(self.imports))
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
