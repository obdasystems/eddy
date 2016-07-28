# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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


import os

from PyQt5.QtWidgets import QApplication
from PyQt5.QtXml import QDomDocument

from eddy.core.datatypes.graphol import Item
from eddy.core.exceptions import ProjectNotFoundError
from eddy.core.exceptions import ProjectNotValidError
from eddy.core.exceptions import DiagramNotFoundError
from eddy.core.exceptions import DiagramNotValidError
from eddy.core.functions.path import expandPath
from eddy.core.functions.fsystem import fread, fexists, isdir
from eddy.core.functions.signals import connect
from eddy.core.loaders.common import AbstractLoader
from eddy.core.loaders.graphol import GrapholLoader
from eddy.core.output import getLogger
from eddy.core.project import Project

LOGGER = getLogger(__name__)


class ProjectLoader(AbstractLoader):
    """
    This class can be used to load projects.

    A graphol project is stored within a directory whose structure is the following:

    - projectname/
    -   .eddy/              # subdirectory which contains project specific information
    -       meta.xml        # contains ontology and predicates meta information
    -       modules.xml     # contains the paths of all the modules of the ontology

    -   module1.graphol
    -   module2.graphol
    -   ...
    -   moduleN.graphol
    """
    def __init__(self, path, session):
        """
        Initialize the project loader.
        :type path: str
        :type session: Session
        """
        super().__init__(session)

        self.project = None
        self.metaDocument = None
        self.modulesDocument = None

        self.projectMainPath = expandPath(path)
        self.projectHomePath = os.path.join(self.projectMainPath, Project.Home)
        self.projectMetaDataPath = os.path.join(self.projectHomePath, Project.MetaXML)
        self.projectModulesDataPath = os.path.join(self.projectHomePath, Project.ModulesXML)

        self.metaFuncForItem = {
            Item.AttributeNode: self.buildAttributeMetadata,
            Item.ConceptNode: self.buildPredicateMetadata,
            Item.IndividualNode: self.buildPredicateMetadata,
            Item.RoleNode: self.buildRoleMetadata,
            Item.ValueDomainNode: self.buildPredicateMetadata,
            Item.ValueRestrictionNode: self.buildPredicateMetadata,
        }

        self.itemFromXml = {
            'attribute': Item.AttributeNode,
            'complement': Item.ComplementNode,
            'concept': Item.ConceptNode,
            'datatype-restriction': Item.DatatypeRestrictionNode,
            'disjoint-union': Item.DisjointUnionNode,
            'domain-restriction': Item.DomainRestrictionNode,
            'enumeration': Item.EnumerationNode,
            'individual': Item.IndividualNode,
            'intersection': Item.IntersectionNode,
            'property-assertion': Item.PropertyAssertionNode,
            'range-restriction': Item.RangeRestrictionNode,
            'role': Item.RoleNode,
            'role-chain': Item.RoleChainNode,
            'role-inverse': Item.RoleInverseNode,
            'union': Item.UnionNode,
            'value-domain': Item.ValueDomainNode,
            'value-restriction': Item.ValueRestrictionNode,
            'inclusion': Item.InclusionEdge,
            'input': Item.InputEdge,
            'instance-of': Item.MembershipEdge,
            'membership': Item.MembershipEdge,
        }

    #############################################
    #   AUXILIARY METHODS
    #################################

    def buildAttributeMetadata(self, element):
        """
        Build role metadata using the given QDomElement.
        :type element: QDomElement
        :rtype: AttributeMetaData
        """
        meta = self.buildPredicateMetadata(element)
        functional = element.firstChildElement('functional')
        meta.functional = bool(int(functional.text()))
        return meta

    def buildPredicateMetadata(self, element):
        """
        Build predicate metadata using the given QDomElement.
        :type element: QDomElement
        :rtype: PredicateMetaData
        """
        item = self.itemFromXml[element.attribute('type')]
        name = element.attribute('name')
        description = element.firstChildElement('description')
        url = element.firstChildElement('url')
        meta = self.project.meta(item, name)
        meta.description = description.text()
        meta.url = url.text()
        return meta

    def buildRoleMetadata(self, element):
        """
        Build role metadata using the given QDomElement.
        :type element: QDomElement
        :rtype: AttributeMetaData
        """
        meta = self.buildPredicateMetadata(element)
        functional = element.firstChildElement('functional')
        inverseFunctional = element.firstChildElement('inverseFunctional')
        asymmetric = element.firstChildElement('asymmetric')
        irreflexive = element.firstChildElement('irreflexive')
        reflexive = element.firstChildElement('reflexive')
        symmetric = element.firstChildElement('symmetric')
        transitive = element.firstChildElement('transitive')
        meta.functional = bool(int(functional.text()))
        meta.inverseFunctional = bool(int(inverseFunctional.text()))
        meta.asymmetric = bool(int(asymmetric.text()))
        meta.irreflexive = bool(int(irreflexive.text()))
        meta.reflexive = bool(int(reflexive.text()))
        meta.symmetric = bool(int(symmetric.text()))
        meta.transitive = bool(int(transitive.text()))
        return meta

    #############################################
    #   IMPORT PROJECT FROM XML
    #################################

    def importProjectFromXML(self):
        """
        Initialize the project instance by reading project metadata from XML file.
        :raise ProjectNotValidError: If the project metadata file is missing or not readable.
        """
        # noinspection PyArgumentList
        QApplication.processEvents()

        LOGGER.info('Loading project metadata from %s', self.projectMetaDataPath)

        if not fexists(self.projectMetaDataPath):
            raise ProjectNotValidError('missing project metadata: {0}'.format(self.projectMetaDataPath))

        self.metaDocument = QDomDocument()
        if not self.metaDocument.setContent(fread(self.projectMetaDataPath)):
            raise ProjectNotValidError('could read project metadata from {0}'.format(self.projectMetaDataPath))

        path = self.projectMainPath
        root = self.metaDocument.documentElement()
        ontology = root.firstChildElement('ontology')
        prefix = ontology.firstChildElement('prefix').text()
        iri = ontology.firstChildElement('iri').text()

        LOGGER.debug('Loaded ontology prefix: %s', prefix)
        LOGGER.debug('Loaded ontology IRI: %s', iri)

        self.project = Project(path, prefix, iri, self.session)

    def importMetaFromXML(self):
        """
        Import predicate metadata from XML file.
        """
        # noinspection PyArgumentList
        QApplication.processEvents()

        #############################################
        # LOAD PREDICATE METADATA
        #################################

        LOGGER.info('Loading ontology predicate metadata from %s', self.projectMetaDataPath)

        root = self.metaDocument.documentElement()
        predicates = root.firstChildElement('predicates')

        predicate = predicates.firstChildElement('predicate')
        while not predicate.isNull():

            # noinspection PyArgumentList
            QApplication.processEvents()

            try:
                item = self.itemFromXml[predicate.attribute('type')]
                func = self.metaFuncForItem[item]
                meta = func(predicate)
                self.project.addMeta(meta.item, meta.predicate, meta)
            except Exception:
                LOGGER.exception('Failed to create metadata for predicate %s', predicate)
                pass
            finally:
                predicate = predicate.nextSiblingElement('predicate')

        #############################################
        # UPDATE LAYOUT ACCORDING TO METADATA
        #################################

        predicates = self.project.predicates()
        LOGGER.info('Refreshing state for %s predicate nodes', len(predicates))
        for node in predicates:
            node.updateNode()
            node.redraw()

    def importModulesFromXML(self):
        """
        Import project modules from XML file.
        :raise ProjectNotValidError: If the project structure file is missing or not readable.
        """
        # noinspection PyArgumentList
        QApplication.processEvents()

        LOGGER.info('Loading project structure from %s', self.projectModulesDataPath)

        if not fexists(self.projectModulesDataPath):
            raise ProjectNotValidError('missing project structure: {0}'.format(self.projectModulesDataPath))

        self.modulesDocument = QDomDocument()
        if not self.modulesDocument.setContent(fread(self.projectModulesDataPath)):
            raise ProjectNotValidError('could read project structure from {0}'.format(self.projectModulesDataPath))

        root = self.modulesDocument.documentElement()
        modules = root.firstChildElement('modules')

        module = modules.firstChildElement('module')
        while not module.isNull():

            # noinspection PyArgumentList
            QApplication.processEvents()

            name = module.text()
            path = os.path.join(self.project.path, name)

            try:
                worker = GrapholLoader(self.project, path, self.session)
            except (DiagramNotFoundError, DiagramNotValidError) as e:
                LOGGER.warning('Failed to load project module %s: %s', name, e)
            except Exception:
                LOGGER.exception('Failed to load project module %s', name)
            else:
                self.project.addDiagram(worker.run())
            finally:
                module = module.nextSiblingElement('module')

    #############################################
    #   PROJECT GENERATION
    #################################

    def run(self):
        """
        Perform project import.
        :raise ProjectNotFoundError: If the given path does not identify a project.
        :raise ProjectNotValidError: If one of the project data file is missing or not readable.
        :rtype: Project
        """
        LOGGER.header('Loading project: %s', os.path.basename(self.projectMainPath))

        #############################################
        # VALIDATE PROJECT
        #################################

        if not isdir(self.projectMainPath):
            raise ProjectNotFoundError('project not found: {0}'.format(self.projectMainPath))

        if not isdir(self.projectHomePath):
            raise ProjectNotValidError('missing project home: {0}'.format(self.projectHomePath))

        #############################################
        # IMPORT PROJECT
        #################################

        self.importProjectFromXML()
        self.importModulesFromXML()
        self.importMetaFromXML()

        #############################################
        # CONFIGURE PROJECT SIGNALS
        #################################

        connect(self.project.undoStack.cleanChanged, self.session.doUpdateState)

        LOGGER.separator('-')

        return self.project