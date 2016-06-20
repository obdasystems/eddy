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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtXml import QDomDocument

from eddy.core.datatypes.graphol import Item
from eddy.core.exporters.common import AbstractExporter
from eddy.core.functions.fsystem import fwrite


class GrapholExporter(AbstractExporter):
    """
    This class can be used to export the structure of graphol diagrams to file.
    """
    GrapholVersion = 1

    def __init__(self, diagram, path=None, parent=None):
        """
        Initialize the graphol exporter.
        :type diagram: Diagram
        :type path: str
        :type parent: QObject
        """
        super().__init__(parent)

        self.document = None
        self.diagram = diagram
        self.path = path

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
        element.setAttribute('color', node.brush.color().name())
        geometry = self.document.createElement('geometry')
        geometry.setAttribute('height', node.height())
        geometry.setAttribute('width', node.width())
        geometry.setAttribute('x', node.pos().x())
        geometry.setAttribute('y', node.pos().y())
        element.appendChild(geometry)
        return element

    #############################################
    #   DOCUMENT GENERATION
    #################################

    def run(self):
        """
        Perform graphol document generation.
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
        fwrite(self.document.toString(2), self.path or self.diagram.path)
