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

    sgnMissingOntologyImportFound = QtCore.pyqtSignal(str, str)

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
        self.ontologyID = None
        self.ontologyIRI = ''
        self.versionIRI = ''

        self.vm = getJavaVM()
        if not self.vm.isRunning():
            self.vm.initialize()
        self.vm.attachThreadToJVM()

        self.File = self.vm.getJavaClass('java.io.File')
        self.IRI = self.vm.getJavaClass('org.semanticweb.owlapi.model.IRI')
        self.OWLManager = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.ImportListener = self.vm.getJavaClass('com.obdasystems.eddy.ImportListener')
        self.IRIDocumentSource = self.vm.getJavaClass('org.semanticweb.owlapi.io.IRIDocumentSource')
        self.FileDocumentSource = self.vm.getJavaClass(
            'org.semanticweb.owlapi.io.FileDocumentSource')
        self.OWLOntologyLoaderConfiguration = self.vm.getJavaClass(
            'org.semanticweb.owlapi.model.OWLOntologyLoaderConfiguration')
        self.MissingImportHandlingStrategy = self.vm.getJavaClass(
            'org.semanticweb.owlapi.model.MissingImportHandlingStrategy')

    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.sgnStarted.emit()
            self.vm.attachThreadToJVM()
            missImpListener = self.ImportListener()
            self.ontologyManager = self.OWLManager.createOWLOntologyManager()
            self.ontologyManager.addMissingImportListener(missImpListener)
            loadConf = self.OWLOntologyLoaderConfiguration()
            loadConf = loadConf.setMissingImportHandlingStrategy(
                self.MissingImportHandlingStrategy.SILENT)
            if self.isLocalImport:
                fileInstance = self.File(self.location)
                ontDocSrc = self.FileDocumentSource(fileInstance)
            else:
                iriInstance = self.IRI.create(self.location)
                ontDocSrc = self.IRIDocumentSource(iriInstance)

            ontology = self.ontologyManager.loadOntologyFromOntologyDocument(ontDocSrc, loadConf)

            self.ontologyID = ontology.getOntologyID()

            optionalOntologyIRI = self.ontologyID.getOntologyIRI()
            if optionalOntologyIRI.isPresent():
                self.ontologyIRI = optionalOntologyIRI.get().toString()

            optionalVersionIRI = self.ontologyID.getVersionIRI()
            if optionalVersionIRI.isPresent():
                self.versionIRI = optionalVersionIRI.get().toString()

            if self.ontologyIRI == str(self.project.ontologyIRI):
                raise Exception('The selected ontology cannot be imported because '
                                'its IRI "{}" is associated to the working ontology'
                                .format(self.ontologyIRI))
            if not self.isReloadAttempt:
                for ont in self.project.importedOntologies:
                    if self.ontologyIRI == str(ont.ontologyIRI):
                        raise Exception('The selected ontology cannot be added to the project '
                                        'because its IRI "{}" is associated to an ontology that '
                                        'has been previously imported'.format(self.ontologyIRI))

            for missingEvent in missImpListener.getMissingImportEvents():
                self.sgnMissingOntologyImportFound.emit(
                    missingEvent.getImportedOntologyURI().toString(),
                    missingEvent.getCreationException().getMessage())

            self.sgnOntologyDocumentLoaded.emit(
                self.ontologyIRI,
                self.location,
                self.versionIRI,
                self.isLocalImport
            )

            self.sgnStepPerformed.emit(1)

            for cls in ontology.getClassesInSignature():
                if not (cls.isOWLThing() or cls.isOWLNothing()):
                    self.sgnClassFetched.emit(cls.getIRI().toString())
            self.sgnStepPerformed.emit(2)

            for prop in ontology.getObjectPropertiesInSignature():
                if not prop.isOWLTopObjectProperty() and not prop.isOWLBottomObjectProperty():
                    self.sgnObjectPropertyFetched.emit(prop.getIRI().toString())
            self.sgnStepPerformed.emit(3)

            for prop in ontology.getDataPropertiesInSignature():
                if not prop.isOWLTopDataProperty() and not prop.isOWLBottomDataProperty():
                    self.sgnDataPropertyFetched.emit(prop.getIRI().toString())
            self.sgnStepPerformed.emit(4)

            for ind in ontology.getIndividualsInSignature():
                if not ind.isAnonymous():
                    self.sgnIndividualFetched.emit(ind.getIRI().toString())
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

        self.File = self.vm.getJavaClass('java.io.File')
        self.IRI = self.vm.getJavaClass('org.semanticweb.owlapi.model.IRI')
        self.OWLManager = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.ontologyManager = None
        self._owlOntologyImportErrors = set()
        self._loadCount = 0

    @property
    def importSize(self):
        return len(self.imports)

    @property
    def loadCount(self):
        return self._loadCount

    @property
    def owlOntologyImportErrors(self):
        return self._owlOntologyImportErrors

    @QtCore.pyqtSlot(str, Exception)
    def onImportError(self, location, exc):
        self._owlOntologyImportErrors.update([(location, str(exc))])

    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.sgnStarted.emit()
            self.vm.attachThreadToJVM()
            self.ontologyManager = self.OWLManager.createOWLOntologyManager()
            for ont in self.imports:
                if not self.toBeLoaded or ont.ontologyIRI in self.toBeLoaded:
                    try:
                        if ont.isLocalDocument:
                            file = self.File(ont.docLocation)
                            ontology = self.ontologyManager.loadOntologyFromOntologyDocument(file)
                        else:
                            iriInstance = self.IRI.create(ont.docLocation)
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
                            ont.ontologyIRI = ontologyIRI
                        if versionIRI:
                            ont.versionIRI = versionIRI

                        setClasses = ontology.getClassesInSignature()
                        for c in setClasses:
                            if not (c.isOWLThing() or c.isOWLNothing()):
                                iri = self.project.getIRI(c.getIRI().toString(), imported=True)
                                ont.addClass(iri)

                        for prop in ontology.getObjectPropertiesInSignature():
                            if prop.isOWLTopObjectProperty() or prop.isOWLBottomObjectProperty():
                                continue
                            iri = self.project.getIRI(prop.getNamedProperty().getIRI().toString(),
                                                      imported=True)
                            ont.addObjectProperty(iri)

                        for prop in ontology.getDataPropertiesInSignature():
                            if prop.isOWLTopDataProperty() or prop.isOWLBottomDataProperty():
                                continue
                            iri = self.project.getIRI(prop.getIRI().toString(), imported=True)
                            ont.addDataProperty(iri)

                        for ind in ontology.getIndividualsInSignature():
                            if not ind.isAnonymous():
                                iri = self.project.getIRI(ind.getIRI().toString(), imported=True)
                                ont.addIndividual(iri)
                    except Exception as e:
                        LOGGER.exception('The ontology located in {} cannot be correctly '
                                         'loaded'.format(ont.docLocation))
                        ont.correctlyLoaded = False
                        self.sgnErrored.emit(ont, e)
                    else:
                        self._loadCount += 1
                        ont.correctlyLoaded = True
        except Exception as e:
            LOGGER.exception('Fatal exception while resolving ontology imports: %s', e)
        else:
            LOGGER.info('Found %s import declarations, %s loaded',
                        len(self.imports), self._loadCount)
            self.sgnCompleted.emit(self._loadCount, len(self.imports))
        finally:
            self.vm.detachThreadFromJVM()
            self.sgnFinished.emit()
