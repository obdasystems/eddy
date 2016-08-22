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

from PyQt5.QtXml import QDomDocument

from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.system import File
from eddy.core.exporters.common import AbstractDiagramExporter
from eddy.core.exporters.common import AbstractProjectExporter
from eddy.core.functions.fsystem import fwrite, mkdir
from eddy.core.project import Project


class GrapholDiagramExporter(AbstractDiagramExporter):
    """
    Extends AbstractDiagramExporter with facilities to export the structure of Graphol diagrams.
    """
    GrapholVersion = 1

    def __init__(self, diagram, session=None):
        """
        Initialize the Graphol diagram exporter.
        :type diagram: Diagram
        :type session: Session
        """
        super(GrapholDiagramExporter, self).__init__(diagram, session)

        self.document = None

        self.exportFuncForItem = {
            Item.AttributeNode: self.exportAttributeNode,
            Item.ComplementNode: self.exportComplementNode,
            Item.ConceptNode: self.exportConceptNode,
            Item.DatatypeRestrictionNode: self.exportDatatypeRestrictionNode,
            Item.DisjointUnionNode: self.exportDisjointUnionNode,
            Item.DomainRestrictionNode: self.exportDomainRestrictionNode,
            Item.EnumerationNode: self.exportEnumerationNode,
            Item.FacetNode: self.exportFacetNode,
            Item.IndividualNode: self.exportIndividualNode,
            Item.IntersectionNode: self.exportIntersectionNode,
            Item.PropertyAssertionNode: self.exportPropertyAssertionNode,
            Item.RangeRestrictionNode: self.exportRangeRestrictionNode,
            Item.RoleNode: self.exportRoleNode,
            Item.RoleChainNode: self.exportRoleChainNode,
            Item.RoleInverseNode: self.exportRoleInverseNode,
            Item.UnionNode: self.exportUnionNode,
            Item.ValueDomainNode: self.exportValueDomainNode,
            Item.InclusionEdge: self.exportInclusionEdge,
            Item.InputEdge: self.exportInputEdge,
            Item.MembershipEdge: self.exportMembershipEdge,
        }

        self.itemToXml = {
            Item.AttributeNode: 'attribute',
            Item.ComplementNode: 'complement',
            Item.ConceptNode: 'concept',
            Item.DatatypeRestrictionNode: 'datatype-restriction',
            Item.DisjointUnionNode: 'disjoint-union',
            Item.DomainRestrictionNode: 'domain-restriction',
            Item.EnumerationNode: 'enumeration',
            Item.FacetNode: 'facet',
            Item.IndividualNode: 'individual',
            Item.IntersectionNode: 'intersection',
            Item.PropertyAssertionNode: 'property-assertion',
            Item.RangeRestrictionNode: 'range-restriction',
            Item.RoleNode: 'role',
            Item.RoleChainNode: 'role-chain',
            Item.RoleInverseNode: 'role-inverse',
            Item.UnionNode: 'union',
            Item.ValueDomainNode: 'value-domain',
            Item.InclusionEdge: 'inclusion',
            Item.InputEdge: 'input',
            Item.MembershipEdge: 'membership',
        }

    #############################################
    #   NODES
    #################################

    def exportAttributeNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: AttributeNode
        :rtype: QDomElement
        """
        return self.exportLabelNode(node)

    def exportComplementNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: ComplementNode
        :rtype: QDomElement
        """
        return self.exportLabelNode(node)

    def exportConceptNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: ConceptNode
        :rtype: QDomElement
        """
        return self.exportLabelNode(node)

    def exportDatatypeRestrictionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: DatatypeRestrictionNode
        :rtype: QDomElement
        """
        return self.exportLabelNode(node)

    def exportDisjointUnionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: DisjointUnionNode
        :rtype: QDomElement
        """
        return self.exportGenericNode(node)

    def exportDomainRestrictionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: DomainRestrictionNode
        :rtype: QDomElement
        """
        return self.exportLabelNode(node)

    def exportEnumerationNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: EnumerationNode
        :rtype: QDomElement
        """
        return self.exportLabelNode(node)

    def exportFacetNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: FacetNode
        :rtype: QDomElement
        """
        position = node.mapToScene(node.textPos())
        label = self.document.createElement('label')
        label.setAttribute('height', node.labelA.height())
        label.setAttribute('width', node.labelA.width() + node.labelB.width())
        label.setAttribute('x', position.x())
        label.setAttribute('y', position.y())
        label.appendChild(self.document.createTextNode(node.text()))
        element = self.exportGenericNode(node)
        element.appendChild(label)
        return element

    def exportIndividualNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: IndividualNode
        :rtype: QDomElement
        """
        return self.exportLabelNode(node)

    def exportIntersectionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: IntersectionNode
        :rtype: QDomElement
        """
        return self.exportLabelNode(node)

    def exportPropertyAssertionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: PropertyAssertionNode
        :rtype: QDomElement
        """
        element = self.exportGenericNode(node)
        element.setAttribute('inputs', ','.join(node.inputs))
        return element

    def exportRangeRestrictionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: RangeRestrictionNode
        :rtype: QDomElement
        """
        return self.exportLabelNode(node)

    def exportRoleNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: RoleNode
        :rtype: QDomElement
        """
        return self.exportLabelNode(node)

    def exportRoleChainNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: RoleChainNode
        :rtype: QDomElement
        """
        element = self.exportLabelNode(node)
        element.setAttribute('inputs', ','.join(node.inputs))
        return element

    def exportRoleInverseNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: RoleInverseNode
        :rtype: QDomElement
        """
        return self.exportLabelNode(node)

    def exportValueDomainNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: ValueDomainNode
        :rtype: QDomElement
        """
        return self.exportLabelNode(node)

    def exportUnionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: UnionNode
        :rtype: QDomElement
        """
        return self.exportLabelNode(node)

    #############################################
    #   EDGES
    #################################

    def exportInclusionEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: InclusionEdge
        :rtype: QDomElement
        """
        element = self.exportGenericEdge(edge)
        element.setAttribute('equivalence', int(edge.equivalence))
        return element

    def exportInputEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: InputEdge
        :rtype: QDomElement
        """
        return self.exportGenericEdge(edge)

    def exportMembershipEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: MembershipEdge
        :rtype: QDomElement
        """
        return self.exportGenericEdge(edge)

    #############################################
    #   AUXILIARY METHODS
    #################################

    def exportLabelNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: AbstractNode
        :rtype: QDomElement
        """
        position = node.mapToScene(node.textPos())
        label = self.document.createElement('label')
        label.setAttribute('height', node.label.height())
        label.setAttribute('width', node.label.width())
        label.setAttribute('x', position.x())
        label.setAttribute('y', position.y())
        label.appendChild(self.document.createTextNode(node.text()))
        element = self.exportGenericNode(node)
        element.appendChild(label)
        return element

    def exportGenericEdge(self, edge):
        """
        Export the given node into a QDomElement.
        :type edge: AbstractEdge
        :rtype: QDomElement
        """
        element = self.document.createElement('edge')
        element.setAttribute('source', edge.source.id)
        element.setAttribute('target', edge.target.id)
        element.setAttribute('id', edge.id)
        element.setAttribute('type', self.itemToXml[edge.type()])

        for p in [edge.source.anchor(edge)] + edge.breakpoints + [edge.target.anchor(edge)]:
            point = self.document.createElement('point')
            point.setAttribute('x', p.x())
            point.setAttribute('y', p.y())
            element.appendChild(point)

        return element

    def exportGenericNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: AbstractNode
        :rtype: QDomElement
        """
        element = self.document.createElement('node')
        element.setAttribute('id', node.id)
        element.setAttribute('type', self.itemToXml[node.type()])
        element.setAttribute('color', node.brush().color().name())
        geometry = self.document.createElement('geometry')
        geometry.setAttribute('height', node.height())
        geometry.setAttribute('width', node.width())
        geometry.setAttribute('x', node.pos().x())
        geometry.setAttribute('y', node.pos().y())
        element.appendChild(geometry)
        return element

    #############################################
    #   INTERFACE
    #################################

    def export(self, path=None):
        """
        Perform Graphol document generation.
        :type path: str
        """
        # 1) CREATE THE DOCUMENT
        self.document = QDomDocument()
        instruction = self.document.createProcessingInstruction('xml', 'version="1.0" encoding="UTF-8"')
        self.document.appendChild(instruction)
        
        # 2) CREATE ROOT ELEMENT
        root = self.document.createElement('graphol')
        root.setAttribute('version', str(self.GrapholVersion))
        
        self.document.appendChild(root)
        
        # 3) CREATE THE GRAPH NODE
        graph = self.document.createElement('graph')
        graph.setAttribute('width', self.diagram.width())
        graph.setAttribute('height', self.diagram.height())
        
        # 4) GENERATE NODES
        for node in self.diagram.nodes():
            func = self.exportFuncForItem[node.type()]
            graph.appendChild(func(node))

        # 5) GENERATE EDGES
        for edge in self.diagram.edges():
            func = self.exportFuncForItem[edge.type()]
            graph.appendChild(func(edge))

        # 6) APPEND THE GRAPH TO THE DOCUMENT
        root.appendChild(graph)

        # 7) GENERATE THE FILE
        fwrite(self.document.toString(2), path or self.diagram.path)

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        :return: File
        """
        return File.Graphol


class GrapholProjectExporter(AbstractProjectExporter):
    """
    Extends AbstractProjectExporter with facilities to export the structure of a Graphol project.

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

    def __init__(self, project, session=None):
        """
        Initialize the project exporter.
        :type project: Project
        :type session: Session
        """
        super(GrapholProjectExporter, self).__init__(project, session)

        self.projectMainPath = project.path
        self.projectDataPath = os.path.join(self.projectMainPath, Project.Home)
        self.projectMetaDataPath = os.path.join(self.projectDataPath, Project.MetaXML)
        self.projectModulesDataPath = os.path.join(self.projectDataPath, Project.ModulesXML)

        self.metaDocument = None
        self.modulesDocument = None

        self.metaFuncForItem = {
            Item.AttributeNode: self.exportAttributeMetadata,
            Item.ConceptNode: self.exportPredicateMeta,
            Item.RoleNode: self.exportRoleMetadata,
        }

        self.itemToXml = {
            Item.AttributeNode: 'attribute',
            Item.ComplementNode: 'complement',
            Item.ConceptNode: 'concept',
            Item.DatatypeRestrictionNode: 'datatype-restriction',
            Item.DisjointUnionNode: 'disjoint-union',
            Item.DomainRestrictionNode: 'domain-restriction',
            Item.EnumerationNode: 'enumeration',
            Item.IndividualNode: 'individual',
            Item.IntersectionNode: 'intersection',
            Item.PropertyAssertionNode: 'property-assertion',
            Item.RangeRestrictionNode: 'range-restriction',
            Item.RoleNode: 'role',
            Item.RoleChainNode: 'role-chain',
            Item.RoleInverseNode: 'role-inverse',
            Item.UnionNode: 'union',
            Item.ValueDomainNode: 'value-domain',
            Item.InclusionEdge: 'inclusion',
            Item.InputEdge: 'input',
            Item.MembershipEdge: 'membership',
        }

    #############################################
    #   AUXILIARY METHODS
    #################################

    def exportPredicateMeta(self, item, name):
        """
        Export predicate metadata.
        :type item: Item
        :type name: str
        :rtype: QDomElement
        """
        meta = self.project.meta(item, name)
        element = self.metaDocument.createElement('predicate')
        element.setAttribute('type', self.itemToXml[item])
        element.setAttribute('name', name)
        description = self.metaDocument.createElement('description')
        description.appendChild(self.metaDocument.createTextNode(meta.description))
        url = self.metaDocument.createElement('url')
        url.appendChild(self.metaDocument.createTextNode(meta.url))
        element.appendChild(url)
        element.appendChild(description)
        return element

    def exportAttributeMetadata(self, item, name):
        """
        Export attribute metadata.
        :type item: Item
        :type name: str
        :rtype: QDomElement
        """
        element = self.exportPredicateMeta(item, name)
        meta = self.project.meta(item, name)
        functional = self.metaDocument.createElement('functional')
        functional.appendChild(self.metaDocument.createTextNode(str(int(meta.functional))))
        element.appendChild(functional)
        return element

    def exportRoleMetadata(self, item, name):
        """
        Export role metadata.
        :type item: Item
        :type name: str
        :rtype: QDomElement
        """
        element = self.exportPredicateMeta(item, name)
        meta = self.project.meta(item, name)
        functional = self.metaDocument.createElement('functional')
        functional.appendChild(self.metaDocument.createTextNode(str(int(meta.functional))))
        inverseFunctional = self.metaDocument.createElement('inverseFunctional')
        inverseFunctional.appendChild(self.metaDocument.createTextNode(str(int(meta.inverseFunctional))))
        asymmetric = self.metaDocument.createElement('asymmetric')
        asymmetric.appendChild(self.metaDocument.createTextNode(str(int(meta.asymmetric))))
        irreflexive = self.metaDocument.createElement('irreflexive')
        irreflexive.appendChild(self.metaDocument.createTextNode(str(int(meta.irreflexive))))
        reflexive = self.metaDocument.createElement('reflexive')
        reflexive.appendChild(self.metaDocument.createTextNode(str(int(meta.reflexive))))
        symmetric = self.metaDocument.createElement('symmetric')
        symmetric.appendChild(self.metaDocument.createTextNode(str(int(meta.symmetric))))
        transitive = self.metaDocument.createElement('transitive')
        transitive.appendChild(self.metaDocument.createTextNode(str(int(meta.transitive))))
        element.appendChild(functional)
        element.appendChild(inverseFunctional)
        element.appendChild(asymmetric)
        element.appendChild(irreflexive)
        element.appendChild(reflexive)
        element.appendChild(symmetric)
        element.appendChild(transitive)
        return element

    #############################################
    #   EXPORT PROJECT SPECIFIC DATA
    #################################

    def exportMetaToXML(self):
        """
        Export project items' matadata to XML file.
        """
        # 1) CREATE DOCUMENT
        self.metaDocument = QDomDocument()
        instruction = self.metaDocument.createProcessingInstruction('xml', 'version="1.0" encoding="UTF-8"')
        self.metaDocument.appendChild(instruction)

        # 2) CREATE ROOT ELEMENT
        root = self.metaDocument.createElement('project')
        root.setAttribute('version', str(Project.Version))
        self.metaDocument.appendChild(root)

        # 3) EXPORT PROJECT METADATA
        iri = self.metaDocument.createElement('iri')
        iri.appendChild(self.metaDocument.createTextNode(self.project.iri))
        prefix = self.metaDocument.createElement('prefix')
        prefix.appendChild(self.metaDocument.createTextNode(self.project.prefix))
        ontology = self.metaDocument.createElement('ontology')
        ontology.appendChild(prefix)
        ontology.appendChild(iri)
        root.appendChild(ontology)

        # 4) APPEND PREDICATE METADATA
        metadata = self.metaDocument.createElement('predicates')
        for item, predicate in self.project.metas():
            func = self.metaFuncForItem[item]
            meta = func(item, predicate)
            metadata.appendChild(meta)
        root.appendChild(metadata)

        # 5) WRITE CONTENT TO DISK
        fwrite(self.metaDocument.toString(2), self.projectMetaDataPath)

    def exportModulesToXML(self):
        """
        Export the list of diagrams in this project to XML file.
        """
        # 1) CREATE DOCUMENT
        self.modulesDocument = QDomDocument()
        instruction = self.modulesDocument.createProcessingInstruction('xml', 'version="1.0" encoding="UTF-8"')
        self.modulesDocument.appendChild(instruction)

        # 2) CREATE ROOT ELEMENT
        root = self.modulesDocument.createElement('project')
        root.setAttribute('version', str(Project.Version))
        self.modulesDocument.appendChild(root)

        # 3) APPEND ALL THE DIAGRAM NAMES
        modules = self.modulesDocument.createElement('modules')
        for diagram in self.project.diagrams():
            module = self.modulesDocument.createElement('module')
            module.appendChild(self.modulesDocument.createTextNode(diagram.name))
            modules.appendChild(module)
        root.appendChild(modules)

        # 4) WRITE CONTENT TO DISK
        fwrite(self.modulesDocument.toString(2), self.projectModulesDataPath)

    #############################################
    #   INTERFACE
    #################################

    def export(self, *args, **kwargs):
        """
        Perform Project export to disk.
        """
        # 1) CREATE PROJECT STRUCTURE
        mkdir(self.projectMainPath)
        mkdir(self.projectDataPath)

        # 2) EXPORT GRAPHOL DIAGRAMS
        for diagram in self.project.diagrams():
            worker = GrapholDiagramExporter(diagram)
            worker.export()

        # 3) EXPORT PROJECT SPECIFIC DATA
        self.exportMetaToXML()
        self.exportModulesToXML()

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        :return: File
        """
        return File.Graphol