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


import os
import textwrap
from time import time

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
    QtXml,
)

from eddy import APPNAME
from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.graphol import (
    Item,
    Identity,
)
from eddy.core.datatypes.system import File
from eddy.core.diagram import (
    Diagram,
    DiagramNotFoundError,
    DiagramNotValidError,
)
from eddy.core.exporters.graphol import GrapholProjectExporter
from eddy.core.functions.fsystem import (
    fread,
    fexists,
    isdir,
    rmdir,
    make_archive,
)
from eddy.core.functions.misc import (
    rstrip,
    postfix,
)
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect
from eddy.core.loaders.common import (
    AbstractDiagramLoader,
    AbstractOntologyLoader,
    AbstractProjectLoader,
)
from eddy.core.output import getLogger
from eddy.core.project import (
    K_FUNCTIONAL,
    K_INVERSE_FUNCTIONAL,
    K_ASYMMETRIC,
    K_IRREFLEXIVE,
    K_REFLEXIVE,
    K_SYMMETRIC,
    K_TRANSITIVE,
    Project,
    ProjectNotFoundError,
    ProjectNotValidError,
    ProjectStopLoadingError,
    ProjectVersionError,
)

LOGGER = getLogger()


class GrapholDiagramLoader_v1(AbstractDiagramLoader):
    """
    Extends AbstractDiagramLoader with facilities to load diagrams from Graphol file format.
    """

    def __init__(self, path, project, session):
        """
        Initialize the Graphol diagram loader.
        :type path: str
        :type project: Project
        :type session: Session
        """
        super().__init__(path, project, session)

        self.diagram = None
        self.edges = dict()
        self.nodes = dict()

        self.importFuncForItem = {
            Item.AttributeNode: self.importAttributeNode,
            Item.ComplementNode: self.importComplementNode,
            Item.ConceptNode: self.importConceptNode,
            Item.DatatypeRestrictionNode: self.importDatatypeRestrictionNode,
            Item.DisjointUnionNode: self.importDisjointUnionNode,
            Item.DomainRestrictionNode: self.importDomainRestrictionNode,
            Item.EnumerationNode: self.importEnumerationNode,
            Item.FacetNode: self.importFacetNode,
            Item.IndividualNode: self.importIndividualNode,
            Item.IntersectionNode: self.importIntersectionNode,
            Item.PropertyAssertionNode: self.importPropertyAssertionNode,
            Item.RangeRestrictionNode: self.importRangeRestrictionNode,
            Item.RoleNode: self.importRoleNode,
            Item.RoleChainNode: self.importRoleChainNode,
            Item.RoleInverseNode: self.importRoleInverseNode,
            Item.UnionNode: self.importUnionNode,
            Item.ValueDomainNode: self.importValueDomainNode,
            Item.InclusionEdge: self.importInclusionEdge,
            Item.EquivalenceEdge: self.importEquivalenceEdge,
            Item.InputEdge: self.importInputEdge,
            Item.MembershipEdge: self.importMembershipEdge,
        }

        self.itemFromXml = {
            'attribute': Item.AttributeNode,
            'complement': Item.ComplementNode,
            'concept': Item.ConceptNode,
            'datatype-restriction': Item.DatatypeRestrictionNode,
            'disjoint-union': Item.DisjointUnionNode,
            'domain-restriction': Item.DomainRestrictionNode,
            'enumeration': Item.EnumerationNode,
            'facet': Item.FacetNode,
            'individual': Item.IndividualNode,
            'intersection': Item.IntersectionNode,
            'property-assertion': Item.PropertyAssertionNode,
            'range-restriction': Item.RangeRestrictionNode,
            'role': Item.RoleNode,
            'role-chain': Item.RoleChainNode,
            'role-inverse': Item.RoleInverseNode,
            'union': Item.UnionNode,
            'value-domain': Item.ValueDomainNode,
            'value-restriction': Item.FacetNode,
            'inclusion': Item.InclusionEdge,
            'equivalence': Item.EquivalenceEdge,
            'input': Item.InputEdge,
            'instance-of': Item.MembershipEdge,
            'membership': Item.MembershipEdge,
        }

    #############################################
    #   NODES
    #################################

    def importAttributeNode(self, e):
        """
        Build an Attribute node using the given QDomElement.
        :type e: QDomElement
        :rtype: AttributeNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.AttributeNode, e)
        node.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importComplementNode(self, e):
        """
        Build a Complement node using the given QDomElement.
        :type e: QDomElement
        :rtype: ComplementNode
        """
        return self.importGenericNode(Item.ComplementNode, e)

    def importConceptNode(self, e):
        """
        Build a Concept node using the given QDomElement.
        :type e: QDomElement
        :rtype: ConceptNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.ConceptNode, e)
        node.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importDatatypeRestrictionNode(self, e):
        """
        Build a DatatypeRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: DatatypeRestrictionNode
        """
        return self.importGenericNode(Item.DatatypeRestrictionNode, e)

    def importDisjointUnionNode(self, e):
        """
        Build a DisjointUnion node using the given QDomElement.
        :type e: QDomElement
        :rtype: DisjointUnionNode
        """
        return self.importGenericNode(Item.DisjointUnionNode, e)

    def importDomainRestrictionNode(self, e):
        """
        Build a DomainRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: DomainRestrictionNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.DomainRestrictionNode, e)
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importEnumerationNode(self, e):
        """
        Build an Enumeration node using the given QDomElement.
        :type e: QDomElement
        :rtype: EnumerationNode
        """
        return self.importGenericNode(Item.EnumerationNode, e)

    def importFacetNode(self, e):
        """
        Build a FacetNode node using the given QDomElement.
        :type e: QDomElement
        :rtype: FacetNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.FacetNode, e)
        node.setText(label.text())
        return node

    def importIndividualNode(self, e):
        """
        Build an Individual node using the given QDomElement.
        :type e: QDomElement
        :rtype: IndividualNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.IndividualNode, e)
        node.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importIntersectionNode(self, e):
        """
        Build an Intersection node using the given QDomElement.
        :type e: QDomElement
        :rtype: IntersectionNode
        """
        return self.importGenericNode(Item.IntersectionNode, e)

    def importPropertyAssertionNode(self, e):
        """
        Build a PropertyAssertion node using the given QDomElement.
        :type e: QDomElement
        :rtype: PropertyAssertionNode
        """
        inputs = e.attribute('inputs', '').strip()
        node = self.importGenericNode(Item.PropertyAssertionNode, e)
        node.inputs = DistinctList(inputs.split(',') if inputs else [])
        return node

    def importRangeRestrictionNode(self, e):
        """
        Build a RangeRestriction node using the given QDomElement.
        :type e: QDomElement
        :rtype: RangeRestrictionNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.RangeRestrictionNode, e)
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importRoleNode(self, e):
        """
        Build a Role node using the given QDomElement.
        :type e: QDomElement
        :rtype: RoleNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.RoleNode, e)
        node.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importRoleChainNode(self, e):
        """
        Build a RoleChain node using the given QDomElement.
        :type e: QDomElement
        :rtype: RoleChainNode
        """
        inputs = e.attribute('inputs', '').strip()
        node = self.importGenericNode(Item.RoleChainNode, e)
        node.inputs = DistinctList(inputs.split(',') if inputs else [])
        return node

    def importRoleInverseNode(self, e):
        """
        Build a RoleInverse node using the given QDomElement.
        :type e: QDomElement
        :rtype: RoleInverseNode
        """
        return self.importGenericNode(Item.RoleInverseNode, e)

    def importValueDomainNode(self, e):
        """
        Build a Value-Domain node using the given QDomElement.
        :type e: QDomElement
        :rtype: ValueDomainNode
        """
        label = self.getLabelFromElement(e)
        node = self.importGenericNode(Item.ValueDomainNode, e)
        node.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        node.setText(label.text())
        node.setTextPos(node.mapFromScene(QtCore.QPointF(int(label.attribute('x')), int(label.attribute('y')))))
        return node

    def importUnionNode(self, e):
        """
        Build a Union node using the given QDomElement.
        :type e: QDomElement
        :rtype: UnionNode
        """
        return self.importGenericNode(Item.UnionNode, e)

    #############################################
    #   EDGES
    #################################

    def importEquivalenceEdge(self, e):
        """
        Build an Equivalence edge using the given QDomElement.
        :type e: QDomElement
        :rtype: EquivalenceEdge
        """
        return self.importGenericEdge(Item.EquivalenceEdge, e)

    def importInclusionEdge(self, e):
        """
        Build an Inclusion edge using the given QDomElement.
        :type e: QDomElement
        :rtype: InclusionEdge
        """
        if self.getEdgeEquivalenceFromElement(e):
            return self.importEquivalenceEdge(e)
        return self.importGenericEdge(Item.InclusionEdge, e)

    def importInputEdge(self, e):
        """
        Build an Input edge using the given QDomElement.
        :type e: QDomElement
        :rtype: InputEdge
        """
        return self.importGenericEdge(Item.InputEdge, e)

    def importMembershipEdge(self, e):
        """
        Build a Membership edge using the given QDomElement.
        :type e: QDomElement
        :rtype: MembershipEdge
        """
        return self.importGenericEdge(Item.MembershipEdge, e)

    #############################################
    #   AUXILIARY METHODS
    #################################

    def importGenericEdge(self, item, e):
        """
        Build an edge using the given item type and QDomElement.
        :type item: Item
        :type e: QDomElement
        :rtype: AbstractEdge
        """
        points = []
        point = self.getPointInsideElement(e)
        while not point.isNull():
            points.append(QtCore.QPointF(int(point.attribute('x')), int(point.attribute('y'))))
            point = self.getPointBesideElement(point)

        source = self.nodes[e.attribute('source')]
        target = self.nodes[e.attribute('target')]
        edge = self.diagram.factory.create(item, **{
            'id': e.attribute('id'),
            'source': source,
            'target': target,
            'breakpoints': [p for p in points[1:-1] \
                            if not (source.painterPath().contains(p) or target.painterPath().contains(p))]
        })

        path = edge.source.painterPath()
        if path.contains(edge.source.mapFromScene(points[0])):
            edge.source.setAnchor(edge, points[0])

        path = edge.target.painterPath()
        if path.contains(edge.target.mapFromScene(points[-1])):
            edge.target.setAnchor(edge, points[-1])

        edge.source.addEdge(edge)
        edge.target.addEdge(edge)
        return edge

    def importGenericNode(self, item, e):
        """
        Build a node using the given item type and QDomElement.
        :type item: Item
        :type e: QDomElement
        :rtype: AbstractNode
        """
        geometry = self.getGeometryFromElement(e)
        node = self.diagram.factory.create(item, **{
            'id': e.attribute('id'),
            'height': int(geometry.attribute('height')),
            'width': int(geometry.attribute('width'))
        })
        node.setPos(QtCore.QPointF(int(geometry.attribute('x')), int(geometry.attribute('y'))))
        return node

    @staticmethod
    def getEdgeEquivalenceFromElement(e):
        """
        Returns the value of the 'equivalence' attribute from the given element.
        :type e: QDomElement
        :rtype: bool
        """
        if e.hasAttribute('equivalence'):
            return bool(int(e.attribute('equivalence', '0')))
        return bool(int(e.attribute('complete', '0')))

    @staticmethod
    def getGeometryFromElement(e):
        """
        Returns the geometry element inside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.firstChildElement('geometry')
        if search.isNull():
            search = e.firstChildElement('shape:geometry')
        return search

    @staticmethod
    def getLabelFromElement(e):
        """
        Returns the label element inside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.firstChildElement('label')
        if search.isNull():
            search = e.firstChildElement('shape:label')
        return search

    @staticmethod
    def getPointBesideElement(e):
        """
        Returns the point element beside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.nextSiblingElement('point')
        if search.isNull():
            search = e.nextSiblingElement('line:point')
        return search

    @staticmethod
    def getPointInsideElement(e):
        """
        Returns the point element inside the given one.
        :type e: QDomElement
        :rtype: QDomElement
        """
        search = e.firstChildElement('point')
        if search.isNull():
            search = e.firstChildElement('line:point')
        return search

    def itemFromGrapholNode(self, e):
        """
        Returns the item matching the given graphol node.
        :type e: QDomElement
        :rtype: Item
        """
        try:
            return self.itemFromXml[e.attribute('type').lower().strip()]
        except KeyError:
            return None

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        return File.Graphol

    def run(self):
        """
        Perform diagram import from Graphol file format and add it to the project.
        """
        LOGGER.info('Loading diagram: %s', self.path)

        if not fexists(self.path):
            raise DiagramNotFoundError('diagram not found: {0}'.format(self.path))

        document = QtXml.QDomDocument()
        if not document.setContent(fread(self.path)):
            raise DiagramNotValidError('could not parse diagram from {0}'.format(self.path))

        root = document.documentElement()
        graph = root.firstChildElement('graph')
        size = max(int(graph.attribute('width', '10000')), int(graph.attribute('height', '10000')))

        #############################################
        # CREATE AN EMPTY DIAGRAM
        #################################

        LOGGER.debug('Initialzing empty diagram with size: %s', size)

        name = os.path.basename(self.path)
        name = rstrip(name, File.Graphol.extension)
        self.diagram = Diagram.create(name, size, self.project)

        #############################################
        # LOAD NODES
        #################################

        element = graph.firstChildElement('node')
        while not element.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromGrapholNode(element)
                func = self.importFuncForItem[item]
                node = func(element)
            except Exception:
                LOGGER.exception('Failed to create node %s', element.attribute('id'))
            else:
                self.diagram.addItem(node)
                self.diagram.guid.update(node.id)
                self.nodes[node.id] = node
            finally:
                element = element.nextSiblingElement('node')

        LOGGER.debug('Loaded nodes: %s', len(self.nodes))

        #############################################
        # LOAD EDGES
        #################################

        element = graph.firstChildElement('edge')
        while not element.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromGrapholNode(element)
                func = self.importFuncForItem[item]
                edge = func(element)
            except Exception:
                LOGGER.exception('Failed to create edge %s', element.attribute('id'))
            else:
                self.diagram.addItem(edge)
                self.diagram.guid.update(edge.id)
                self.edges[edge.id] = edge
                edge.updateEdge()
            finally:
                element = element.nextSiblingElement('edge')

        LOGGER.debug('Loaded edges: %s', len(self.edges))

        #############################################
        # IDENTIFY NODES
        #################################

        nodes = [n for n in self.nodes.values() if Identity.Neutral in n.identities()]
        if nodes:
            LOGGER.debug('Running identification algorithm for %s nodes', len(nodes))
            for node in nodes:
                self.diagram.sgnNodeIdentification.emit(node)

        #############################################
        # CONFIGURE DIAGRAM SIGNALS
        #################################

        connect(self.diagram.sgnItemAdded, self.project.doAddItem)
        connect(self.diagram.sgnItemRemoved, self.project.doRemoveItem)
        connect(self.diagram.selectionChanged, self.session.doUpdateState)

        LOGGER.debug('Diagram created: %s', self.diagram.name)

        #############################################
        # ADD THE DIAGRAM TO THE PROJECT
        #################################

        self.project.addDiagram(self.diagram)

        LOGGER.debug('Diagram "%s" added to project "%s"', self.diagram.name, self.project.name)


class GrapholProjectLoader_v1(AbstractProjectLoader):
    """
    Extends AbstractProjectLoader with facilities to load Graphol projects.
    This class can be used to load projects.

    A Graphol project is stored within a directory whose structure is the following:

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
        super().__init__(path, session)

        self.project = None
        self.metaDocument = None
        self.modulesDocument = None

        self.projectMainPath = expandPath(self.path)
        self.projectHomePath = os.path.join(self.projectMainPath, '.eddy')
        self.projectMetaDataPath = os.path.join(self.projectHomePath, 'meta.xml')
        self.projectModulesDataPath = os.path.join(self.projectHomePath, 'modules.xml')

        self.metaFuncForItem = {
            Item.AttributeNode: self.importAttributeMetadata,
            Item.ConceptNode: self.importPredicateMetadata,
            Item.RoleNode: self.importRoleMetadata,
        }

        self.itemFromXml = {
            'attribute': Item.AttributeNode,
            'complement': Item.ComplementNode,
            'concept': Item.ConceptNode,
            'datatype-restriction': Item.DatatypeRestrictionNode,
            'disjoint-union': Item.DisjointUnionNode,
            'domain-restriction': Item.DomainRestrictionNode,
            'enumeration': Item.EnumerationNode,
            'facet': Item.FacetNode,
            'individual': Item.IndividualNode,
            'intersection': Item.IntersectionNode,
            'property-assertion': Item.PropertyAssertionNode,
            'range-restriction': Item.RangeRestrictionNode,
            'role': Item.RoleNode,
            'role-chain': Item.RoleChainNode,
            'role-inverse': Item.RoleInverseNode,
            'union': Item.UnionNode,
            'value-domain': Item.ValueDomainNode,
            'inclusion': Item.InclusionEdge,
            'input': Item.InputEdge,
            'instance-of': Item.MembershipEdge,
            'membership': Item.MembershipEdge,
        }

    #############################################
    #   AUXILIARY METHODS
    #################################

    def importAttributeMetadata(self, element):
        """
        Build role metadata using the given QDomElement.
        :type element: QDomElement
        :rtype: dict
        """
        meta = self.importPredicateMetadata(element)
        meta[K_FUNCTIONAL] = bool(int(element.firstChildElement(K_FUNCTIONAL).text()))
        return meta

    def importPredicateMetadata(self, element):
        """
        Build predicate metadata using the given QDomElement.
        :type element: QDomElement
        :rtype: PredicateMetaData
        """
        item = self.itemFromXml[element.attribute('type')]
        name = element.attribute('name')
        meta = self.project.meta(item, name)
        return meta

    def importRoleMetadata(self, element):
        """
        Build role metadata using the given QDomElement.
        :type element: QDomElement
        :rtype: dict
        """
        meta = self.importPredicateMetadata(element)
        meta[K_FUNCTIONAL] = bool(int(element.firstChildElement(K_FUNCTIONAL).text()))
        meta[K_INVERSE_FUNCTIONAL] = bool(int(element.firstChildElement(K_INVERSE_FUNCTIONAL).text()))
        meta[K_ASYMMETRIC] = bool(int(element.firstChildElement(K_ASYMMETRIC).text()))
        meta[K_IRREFLEXIVE] = bool(int(element.firstChildElement(K_IRREFLEXIVE).text()))
        meta[K_REFLEXIVE] = bool(int(element.firstChildElement(K_REFLEXIVE).text()))
        meta[K_SYMMETRIC] = bool(int(element.firstChildElement(K_SYMMETRIC).text()))
        meta[K_TRANSITIVE] = bool(int(element.firstChildElement(K_TRANSITIVE).text()))
        return meta

    #############################################
    #   IMPORT PROJECT FROM XML
    #################################

    def importProjectFromXML(self):
        """
        Initialize the project instance by reading project metadata from XML file.
        :raise ProjectNotValidError: If the project metadata file is missing or not readable.
        """
        QtWidgets.QApplication.processEvents()

        LOGGER.info('Loading ontology metadata from %s', self.projectMetaDataPath)

        if not fexists(self.projectMetaDataPath):
            raise ProjectNotValidError('missing project metadata: {0}'.format(self.projectMetaDataPath))

        self.metaDocument = QtXml.QDomDocument()
        if not self.metaDocument.setContent(fread(self.projectMetaDataPath)):
            raise ProjectNotValidError('could read project metadata from {0}'.format(self.projectMetaDataPath))

        path = self.projectMainPath
        root = self.metaDocument.documentElement()
        ontology = root.firstChildElement('ontology')
        prefix = ontology.firstChildElement('prefix').text()
        LOGGER.debug('Loaded ontology prefix: %s', prefix)
        iri = ontology.firstChildElement('iri').text()
        LOGGER.debug('Loaded ontology IRI: %s', iri)
        profileName = ontology.firstChildElement('profile').text()
        if not profileName:
            profileName = 'OWL 2'
            LOGGER.warning('Missing ontology profile, using default: %s', profileName)
        profile = self.session.createProfile(profileName)
        LOGGER.debug('Loaded ontology profile: %s', profile.name())
        self.project = Project(
            name=os.path.basename(path),
            path=path,
            profile=profile, session=self.session)

    def importMetaFromXML(self):
        """
        Import predicate metadata from XML file.
        """
        QtWidgets.QApplication.processEvents()

        #############################################
        # LOAD PREDICATE METADATA
        #################################

        LOGGER.info('Loading ontology predicate metadata from %s', self.projectMetaDataPath)

        root = self.metaDocument.documentElement()
        predicates = root.firstChildElement('predicates')
        predicate = predicates.firstChildElement('predicate')
        while not predicate.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromXml[predicate.attribute('type')]
                func = self.metaFuncForItem[item]
                meta = func(predicate)
                self.project.setMeta(item, predicate.attribute('name'), meta)
            except Exception:
                LOGGER.exception('Failed to create metadata for predicate %s', predicate.attribute('name'))
            finally:
                predicate = predicate.nextSiblingElement('predicate')

        #############################################
        # UPDATE LAYOUT ACCORDING TO METADATA
        #################################

        predicates = self.project.predicates()
        LOGGER.info('Refreshing state for %s predicate nodes', len(predicates))
        for node in predicates:
            node.updateNode()

    def importModulesFromXML(self):
        """
        Import project modules from XML file.
        :raise ProjectNotValidError: If the project structure file is missing or not readable.
        """
        QtWidgets.QApplication.processEvents()

        LOGGER.info('Loading ontology structure from %s', self.projectModulesDataPath)

        if not fexists(self.projectModulesDataPath):
            raise ProjectNotValidError('missing project structure: {0}'.format(self.projectModulesDataPath))

        self.modulesDocument = QtXml.QDomDocument()
        if not self.modulesDocument.setContent(fread(self.projectModulesDataPath)):
            raise ProjectNotValidError('could read project structure from {0}'.format(self.projectModulesDataPath))

        root = self.modulesDocument.documentElement()
        modules = root.firstChildElement('modules')
        mod = modules.firstChildElement('module')
        while not mod.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                name = mod.text()
                path = os.path.join(self.project.path, name)
                worker = GrapholDiagramLoader_v1(path, self.project, self.session)
                worker.run()
            except (DiagramNotFoundError, DiagramNotValidError) as e:
                LOGGER.warning('Failed to load project diagram %s: %s', name, e)
            except Exception:
                LOGGER.exception('Failed to load diagram module %s', name)
            finally:
                mod = mod.nextSiblingElement('module')

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        return File.Graphol

    def run(self):
        """
        Perform project import (LEGACY MODE).
        """
        #############################################
        # VALIDATE PROJECT
        #################################

        if not isdir(self.projectMainPath):
            raise ProjectNotFoundError('project not found: {0}'.format(self.projectMainPath))

        if not isdir(self.projectHomePath):
            raise ProjectNotValidError('missing project home: {0}'.format(self.projectHomePath))

        #############################################
        # LEGACY LOADING CHECK
        #################################

        msgbox = QtWidgets.QMessageBox()
        msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
        msgbox.setTextFormat(QtCore.Qt.RichText)
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        msgbox.setWindowTitle('Legacy mode')
        msgbox.setText(textwrap.dedent("""
        You have selected an {EDDY} version <b>1</b> project.<br/>
        If you continue with the loading procedure the project will be automatically
        converted to the most recent project version.<br/><br/>
        Do you want to continue?
        """.format(EDDY=APPNAME)))
        msgbox.exec_()

        if msgbox.result() == QtWidgets.QMessageBox.No:
            raise ProjectStopLoadingError

        #############################################
        # IMPORT PROJECT
        #################################

        LOGGER.info('Loading ontology: %s (LEGACY MODE)...', os.path.basename(self.projectMainPath))

        self.importProjectFromXML()
        self.importModulesFromXML()
        self.importMetaFromXML()

        #############################################
        # BACKUP PROJECT DIRECTORY
        #################################

        projectName = os.path.basename(self.projectMainPath)
        archivePath = os.path.join(self.projectMainPath, os.path.pardir)
        archiveName = '{}-{}'.format(projectName, int(round(time() * 1000)))
        archiveFullName = os.path.join(archivePath, archiveName)
        LOGGER.info('Archiving legacy project to: {}'.format(archiveFullName))
        make_archive(archivePath, expandPath(archiveFullName), projectName)

        #############################################
        # CLEANUP PROJECT DIRECTORY
        #################################

        rmdir(self.projectMainPath)

        #############################################
        # SET THE LOADED PROJECT IN THE CURRENT SESSION
        #################################

        self.session.project = self.project


class GrapholLoaderMixin_v2(object):
    """
    Mixin which adds the ability to create a project out of a Graphol file.
    """

    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        """
        super().__init__(**kwargs)

        self.buffer = dict()
        self.document = None
        self.nproject = None

        self.itemFromXml = {
            'attribute': Item.AttributeNode,
            'complement': Item.ComplementNode,
            'concept': Item.ConceptNode,
            'datatype-restriction': Item.DatatypeRestrictionNode,
            'disjoint-union': Item.DisjointUnionNode,
            'domain-restriction': Item.DomainRestrictionNode,
            'enumeration': Item.EnumerationNode,
            'facet': Item.FacetNode,
            'individual': Item.IndividualNode,
            'intersection': Item.IntersectionNode,
            'property-assertion': Item.PropertyAssertionNode,
            'range-restriction': Item.RangeRestrictionNode,
            'role': Item.RoleNode,
            'role-chain': Item.RoleChainNode,
            'role-inverse': Item.RoleInverseNode,
            'union': Item.UnionNode,
            'value-domain': Item.ValueDomainNode,
            'inclusion': Item.InclusionEdge,
            'equivalence': Item.EquivalenceEdge,
            'input': Item.InputEdge,
            'membership': Item.MembershipEdge,
            'same': Item.SameEdge,
            'different': Item.DifferentEdge,
        }

        self.importFuncForItem = {
            Item.AttributeNode: self.importAttributeNode,
            Item.ComplementNode: self.importComplementNode,
            Item.ConceptNode: self.importConceptNode,
            Item.DatatypeRestrictionNode: self.importDatatypeRestrictionNode,
            Item.DisjointUnionNode: self.importDisjointUnionNode,
            Item.DomainRestrictionNode: self.importDomainRestrictionNode,
            Item.EnumerationNode: self.importEnumerationNode,
            Item.FacetNode: self.importFacetNode,
            Item.IndividualNode: self.importIndividualNode,
            Item.IntersectionNode: self.importIntersectionNode,
            Item.PropertyAssertionNode: self.importPropertyAssertionNode,
            Item.RangeRestrictionNode: self.importRangeRestrictionNode,
            Item.RoleNode: self.importRoleNode,
            Item.RoleChainNode: self.importRoleChainNode,
            Item.RoleInverseNode: self.importRoleInverseNode,
            Item.UnionNode: self.importUnionNode,
            Item.ValueDomainNode: self.importValueDomainNode,
            Item.InclusionEdge: self.importInclusionEdge,
            Item.EquivalenceEdge: self.importEquivalenceEdge,
            Item.InputEdge: self.importInputEdge,
            Item.MembershipEdge: self.importMembershipEdge,
            Item.SameEdge: self.importSameEdge,
            Item.DifferentEdge: self.importDifferentEdge,
        }

        self.importMetaFuncForItem = {
            Item.AttributeNode: self.importAttributeMeta,
            Item.ConceptNode: self.importPredicateMeta,
            Item.IndividualNode: self.importPredicateMeta,
            Item.RoleNode: self.importRoleMeta,
        }

    #############################################
    #   ONTOLOGY PREDICATES IMPORT
    #################################

    def importAttributeMeta(self, e):
        """
        Build role metadata using the given QDomElement.
        :type e: QDomElement
        :rtype: dict
        """
        meta = self.importPredicateMeta(e)
        meta[K_FUNCTIONAL] = bool(int(e.firstChildElement(K_FUNCTIONAL).text()))
        return meta

    def importPredicateMeta(self, e):
        """
        Build predicate metadata using the given QDomElement.
        :type e: QDomElement
        :rtype: dict
        """
        item = self.itemFromXml[e.attribute('type')]
        name = e.attribute('name')
        meta = self.nproject.meta(item, name)
        return meta

    def importRoleMeta(self, e):
        """
        Build role metadata using the given QDomElement.
        :type e: QDomElement
        :rtype: dict
        """
        meta = self.importPredicateMeta(e)
        meta[K_FUNCTIONAL] = bool(int(e.firstChildElement(K_FUNCTIONAL).text()))
        meta[K_INVERSE_FUNCTIONAL] = bool(int(e.firstChildElement(K_INVERSE_FUNCTIONAL).text()))
        meta[K_ASYMMETRIC] = bool(int(e.firstChildElement(K_ASYMMETRIC).text()))
        meta[K_IRREFLEXIVE] = bool(int(e.firstChildElement(K_IRREFLEXIVE).text()))
        meta[K_REFLEXIVE] = bool(int(e.firstChildElement(K_REFLEXIVE).text()))
        meta[K_SYMMETRIC] = bool(int(e.firstChildElement(K_SYMMETRIC).text()))
        meta[K_TRANSITIVE] = bool(int(e.firstChildElement(K_TRANSITIVE).text()))
        return meta

    #############################################
    #   ONTOLOGY DIAGRAMS IMPORT : NODES
    #################################

    def importAttributeNode(self, d, e):
        """
        Build an Attribute node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: AttributeNode
        """
        x = e.firstChildElement('label')
        n = self.importGenericNode(d, Item.AttributeNode, e)
        n.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        n.setText(x.text())
        n.setTextPos(n.mapFromScene(QtCore.QPointF(int(x.attribute('x')), int(x.attribute('y')))))
        return n

    def importComplementNode(self, d, e):
        """
        Build a Complement node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: ComplementNode
        """
        return self.importGenericNode(d, Item.ComplementNode, e)

    def importConceptNode(self, d, e):
        """
        Build a Concept node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: ConceptNode
        """
        x = e.firstChildElement('label')
        n = self.importGenericNode(d, Item.ConceptNode, e)
        n.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        n.setText(x.text())
        n.setTextPos(n.mapFromScene(QtCore.QPointF(int(x.attribute('x')), int(x.attribute('y')))))
        return n

    def importDatatypeRestrictionNode(self, d, e):
        """
        Build a DatatypeRestriction node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: DatatypeRestrictionNode
        """
        return self.importGenericNode(d, Item.DatatypeRestrictionNode, e)

    def importDisjointUnionNode(self, d, e):
        """
        Build a DisjointUnion node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: DisjointUnionNode
        """
        return self.importGenericNode(d, Item.DisjointUnionNode, e)

    def importDomainRestrictionNode(self, d, e):
        """
        Build a DomainRestriction node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: DomainRestrictionNode
        """
        x = e.firstChildElement('label')
        n = self.importGenericNode(d, Item.DomainRestrictionNode, e)
        n.setText(x.text())
        n.setTextPos(n.mapFromScene(QtCore.QPointF(int(x.attribute('x')), int(x.attribute('y')))))
        return n

    def importEnumerationNode(self, d, e):
        """
        Build an Enumeration node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: EnumerationNode
        """
        return self.importGenericNode(d, Item.EnumerationNode, e)

    def importFacetNode(self, d, e):
        """
        Build a FacetNode node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: FacetNode
        """
        x = e.firstChildElement('label')
        n = self.importGenericNode(d, Item.FacetNode, e)
        n.setText(x.text())
        return n

    def importIndividualNode(self, d, e):
        """
        Build an Individual node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: IndividualNode
        """
        x = e.firstChildElement('label')
        n = self.importGenericNode(d, Item.IndividualNode, e)
        n.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        n.setText(x.text())
        n.setTextPos(n.mapFromScene(QtCore.QPointF(int(x.attribute('x')), int(x.attribute('y')))))
        return n

    def importIntersectionNode(self, d, e):
        """
        Build an Intersection node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: IntersectionNode
        """
        return self.importGenericNode(d, Item.IntersectionNode, e)

    def importPropertyAssertionNode(self, d, e):
        """
        Build a PropertyAssertion node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: PropertyAssertionNode
        """
        inputs = e.attribute('inputs', '').strip()
        n = self.importGenericNode(d, Item.PropertyAssertionNode, e)
        n.inputs = DistinctList(inputs.split(',') if inputs else [])
        return n

    def importRangeRestrictionNode(self, d, e):
        """
        Build a RangeRestriction node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: RangeRestrictionNode
        """
        x = e.firstChildElement('label')
        n = self.importGenericNode(d, Item.RangeRestrictionNode, e)
        n.setText(x.text())
        n.setTextPos(n.mapFromScene(QtCore.QPointF(int(x.attribute('x')), int(x.attribute('y')))))
        return n

    def importRoleNode(self, d, e):
        """
        Build a Role node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: RoleNode
        """
        x = e.firstChildElement('label')
        n = self.importGenericNode(d, Item.RoleNode, e)
        n.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        n.setText(x.text())
        n.setTextPos(n.mapFromScene(QtCore.QPointF(int(x.attribute('x')), int(x.attribute('y')))))
        return n

    def importRoleChainNode(self, d, e):
        """
        Build a RoleChain node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: RoleChainNode
        """
        inputs = e.attribute('inputs', '').strip()
        n = self.importGenericNode(d, Item.RoleChainNode, e)
        n.inputs = DistinctList(inputs.split(',') if inputs else [])
        return n

    def importRoleInverseNode(self, d, e):
        """
        Build a RoleInverse node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: RoleInverseNode
        """
        return self.importGenericNode(d, Item.RoleInverseNode, e)

    def importValueDomainNode(self, d, e):
        """
        Build a Value-Domain node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: ValueDomainNode
        """
        x = e.firstChildElement('label')
        n = self.importGenericNode(d, Item.ValueDomainNode, e)
        n.setBrush(QtGui.QBrush(QtGui.QColor(e.attribute('color', '#fcfcfc'))))
        n.setText(x.text())
        n.setTextPos(n.mapFromScene(QtCore.QPointF(int(x.attribute('x')), int(x.attribute('y')))))
        return n

    def importUnionNode(self, d, e):
        """
        Build a Union node using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: UnionNode
        """
        return self.importGenericNode(d, Item.UnionNode, e)

    #############################################
    #   ONTOLOGY DIAGRAMS IMPORT : EDGES
    #################################

    def importEquivalenceEdge(self, d, e):
        """
        Build an Equivalence edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: EquivalenceEdge
        """
        return self.importGenericEdge(d, Item.EquivalenceEdge, e)

    def importInclusionEdge(self, d, e):
        """
        Build an Inclusion edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: InclusionEdge
        """
        return self.importGenericEdge(d, Item.InclusionEdge, e)

    def importInputEdge(self, d, e):
        """
        Build an Input edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: InputEdge
        """
        return self.importGenericEdge(d, Item.InputEdge, e)

    def importMembershipEdge(self, d, e):
        """
        Build a Membership edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: MembershipEdge
        """
        return self.importGenericEdge(d, Item.MembershipEdge, e)

    def importSameEdge(self, d, e):
        """
        Build a Same edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: SameEdge
        """
        return self.importGenericEdge(d, Item.SameEdge, e)

    def importDifferentEdge(self, d, e):
        """
        Build a Different edge using the given QDomElement.
        :type d: Diagram
        :type e: QDomElement
        :rtype: DifferentEdge
        """
        return self.importGenericEdge(d, Item.DifferentEdge, e)

    #############################################
    #   ONTOLOGY DIAGRAMS IMPORT : GENERICS
    #################################

    def importGenericEdge(self, d, i, e):
        """
        Build an edge using the given item type and QDomElement.
        :type d: Diagram
        :type i: Item
        :type e: QDomElement
        :rtype: AbstractEdge
        """
        points = []
        point = e.firstChildElement('point')
        while not point.isNull():
            points.append(QtCore.QPointF(int(point.attribute('x')), int(point.attribute('y'))))
            point = point.nextSiblingElement('point')

        source = self.buffer[d.name][e.attribute('source')]
        target = self.buffer[d.name][e.attribute('target')]
        edge = d.factory.create(i, **{
            'id': e.attribute('id'),
            'source': source,
            'target': target,
            'breakpoints': [p for p in points[1:-1]
                            if not (source.painterPath().contains(source.mapFromScene(p)) or
                                    target.painterPath().contains(target.mapFromScene(p)))]
        })

        path = edge.source.painterPath()
        if path.contains(edge.source.mapFromScene(points[0])):
            edge.source.setAnchor(edge, points[0])

        path = edge.target.painterPath()
        if path.contains(edge.target.mapFromScene(points[-1])):
            edge.target.setAnchor(edge, points[-1])

        edge.source.addEdge(edge)
        edge.target.addEdge(edge)
        return edge

    @staticmethod
    def importGenericNode(d, i, e):
        """
        Build a node using the given item type and QDomElement.
        :type d: Diagram
        :type i: Item
        :type e: QDomElement
        :rtype: AbstractNode
        """
        geometry = e.firstChildElement('geometry')
        node = d.factory.create(i, **{
            'id': e.attribute('id'),
            'height': int(geometry.attribute('height')),
            'width': int(geometry.attribute('width'))
        })
        node.setPos(QtCore.QPointF(int(geometry.attribute('x')), int(geometry.attribute('y'))))
        return node

    #############################################
    #   ONTOLOGY DIAGRAMS : MAIN IMPORT
    #################################

    def importDiagram(self, e, i):
        """
        Create a diagram from the given QDomElement.
        :type e: QDomElement
        :type i: int
        :rtype: Diagram
        """
        QtWidgets.QApplication.processEvents()
        ## PARSE DIAGRAM INFORMATION
        name = e.attribute('name', 'diagram_{0}'.format(i))
        size = max(int(e.attribute('width', '10000')), int(e.attribute('height', '10000')))
        ## CREATE NEW DIAGRAM
        LOGGER.info('Loading diagram: %s', name)
        diagram = Diagram.create(name, size, self.nproject)
        self.buffer[diagram.name] = dict()
        ## LOAD DIAGRAM NODES
        sube = e.firstChildElement('node')
        while not sube.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromXmlNode(sube)
                func = self.importFuncForItem[item]
                node = func(diagram, sube)
            except Exception:
                LOGGER.exception('Failed to create node %s', sube.attribute('id'))
            else:
                diagram.addItem(node)
                diagram.guid.update(node.id)
                self.buffer[diagram.name][node.id] = node
            finally:
                sube = sube.nextSiblingElement('node')
        ## LOAD DIAGRAM EDGES
        sube = e.firstChildElement('edge')
        while not sube.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromXmlNode(sube)
                func = self.importFuncForItem[item]
                edge = func(diagram, sube)
            except Exception:
                LOGGER.exception('Failed to create edge %s', sube.attribute('id'))
            else:
                diagram.addItem(edge)
                diagram.guid.update(edge.id)
                self.buffer[diagram.name][edge.id] = edge
            finally:
                sube = sube.nextSiblingElement('edge')
        ## IDENTIFY NEUTRAL NODES
        nodes = [x for x in diagram.items(edges=False) if Identity.Neutral in x.identities()]
        if nodes:
            LOGGER.debug('Running identification algorithm for %s nodes', len(nodes))
            for node in nodes:
                diagram.sgnNodeIdentification.emit(node)
        ## CONFIGURE DIAGRAM SIGNALS
        connect(diagram.sgnItemAdded, self.nproject.doAddItem)
        connect(diagram.sgnItemRemoved, self.nproject.doRemoveItem)
        connect(diagram.selectionChanged, self.session.doUpdateState)
        ## RETURN GENERATED DIAGRAM
        return diagram

    def importMeta(self, e):
        """
        Create predicate metadata from the given QDomElement.
        :type e: QDomElement
        :rtype: tuple
        """
        try:
            QtWidgets.QApplication.processEvents()
            item = self.itemFromXml[e.attribute('type')]
            func = self.importMetaFuncForItem[item]
            meta = func(e)
        except Exception:
            LOGGER.exception('Failed to create meta for predicate %s', e.attribute('name'))
            return None
        else:
            return item, e.attribute('name'), meta

    #############################################
    #   AUXILIARY METHODS
    #################################

    def itemFromXmlNode(self, e):
        """
        Returns the item matching the given Graphol XML node.
        :type e: QDomElement
        :rtype: Item
        """
        try:
            return self.itemFromXml[e.attribute('type').lower().strip()]
        except KeyError:
            return None

    #############################################
    #   MAIN IMPORT
    #################################

    def createDiagrams(self):
        """
        Create ontology diagrams by parsing the 'diagrams' section of the QDomDocument.
        """
        counter = 1
        section = self.document.documentElement().firstChildElement('diagrams')
        element = section.firstChildElement('diagram')
        while not element.isNull():
            self.nproject.addDiagram(self.importDiagram(element, counter))
            element = element.nextSiblingElement('diagram')
            counter += 1

    def createDomDocument(self):
        """
        Create the QDomDocument from where to parse Project information.
        """
        if not fexists(self.path):
            raise ProjectNotFoundError('missing project ontology: %s' % self.path)
        self.document = QtXml.QDomDocument()
        if File.forPath(self.path) is not File.Graphol or not self.document.setContent(fread(self.path)):
            raise ProjectNotValidError('invalid project ontology supplied: %s' % self.path)
        e = self.document.documentElement()
        version = int(e.attribute('version', '2'))
        if version != 2:
            raise ProjectVersionError('project version mismatch: %s != 2' % version)

    def createPredicatesMeta(self):
        """
        Create ontology predicate metadata by parsing the 'predicates' section of the QDomDocument.
        """
        section = self.document.documentElement().firstChildElement('predicates')
        element = section.firstChildElement('predicate')
        while not element.isNull():
            QtWidgets.QApplication.processEvents()
            meta = self.importMeta(element)
            if meta:
                self.nproject.setMeta(meta[0], meta[1], meta[2])
            element = element.nextSiblingElement('predicate')

    def createProject(self):
        """
        Create the Project by reading data from the parsed QDomDocument.
        """
        section = self.document.documentElement().firstChildElement('ontology')

        def parse(tag, default='NULL'):
            """
            Read an element from the given tag.
            :type tag: str
            :type default: str
            :rtype: str
            """
            QtWidgets.QApplication.processEvents()
            subelement = section.firstChildElement(tag)
            if subelement.isNull():
                LOGGER.warning('Missing tag <%s> in ontology section, using default: %s', tag, default)
                return default
            content = subelement.text()
            if not content:
                LOGGER.warning('Empty tag <%s> in ontology section, using default: %s', tag, default)
                return default
            LOGGER.debug('Loaded ontology %s: %s', tag, content)
            return content

        self.nproject = Project(
            name=parse(tag='name', default=rstrip(os.path.basename(self.path), File.Graphol.extension)),
            path=os.path.dirname(self.path),
            # prefix=parse(tag='prefix', default=None),
            # iri=parse(tag='iri', default=None),
            version=parse(tag='version', default='1.0'),
            profile=self.session.createProfile(parse('profile', 'OWL 2')),
            session=self.session)

        LOGGER.info('Loaded ontology: %s...', self.nproject.name)

    def projectRender(self):
        """
        Render all the elements in the Project ontology.
        """
        for item in self.nproject.items():
            QtWidgets.QApplication.processEvents()
            item.updateEdgeOrNode()


class GrapholOntologyLoader_v2(AbstractOntologyLoader, GrapholLoaderMixin_v2):
    """
    Extends AbstractOntologyLoader with facilities to load ontologies from Graphol file format.
    """

    def __init__(self, path, project, session):
        """
        Initialize the Graphol importer.
        :type path: str
        :type project: Project
        :type session: Session
        """
        super().__init__(expandPath(path), project, session)

    def projectMerge(self):
        """
        Merge the loaded project with the one currently loaded in Eddy session.
        """
        # worker = ProjectMergeWorker(self.project, self.nproject, self.session)
        # worker.run()
        pass

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        return File.Graphol

    def run(self):
        """
        Perform ontology import from Graphol file format and merge the loaded ontology with the current project.
        """
        self.createDomDocument()
        self.createProject()
        self.createDiagrams()
        self.createPredicatesMeta()
        self.projectRender()
        self.projectMerge()


class GrapholProjectLoader_v2(AbstractProjectLoader, GrapholLoaderMixin_v2):
    """
    Extends AbstractProjectLoader with facilities to load Graphol projects.
    """

    def __init__(self, path, session):
        """
        Initialize the Project loader.
        :type path: str
        :type session: Session
        """
        path = expandPath(path)
        path = os.path.join(path, os.path.basename(path))
        path = postfix(path, File.Graphol.extension)
        super().__init__(path, session)

    def createLegacyProject(self):
        """
        Create a Project using the @deprecated Graphol project loader (v1).
        """
        worker = GrapholProjectLoader_v1(os.path.dirname(self.path), self.session)
        worker.run()
        worker = GrapholProjectExporter(self.session.project)
        worker.run()

    def projectLoaded(self):
        """
        Initialize the Session Project to be the loaded one.
        """
        self.session.project = self.nproject

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        return File.Graphol

    def run(self):
        """
        Perform project import.
        """
        try:
            self.createDomDocument()
        except (ProjectNotFoundError, ProjectVersionError):
            self.createLegacyProject()
        else:
            self.createProject()
            self.createDiagrams()
            self.createPredicatesMeta()
            self.projectRender()
            self.projectLoaded()
