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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtXml import QDomDocument

from eddy.core.datatypes import Item
from eddy.core.exporters.common import AbstractExporter


class GrapholExporter(AbstractExporter):
    """
    This class can be used to export Graphol diagrams to file.
    """
    def __init__(self, scene):
        """
        Initialize the Graphol exporter.
        :type scene: DiagramScene
        """
        super().__init__(scene)
        self.document = None
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
            Item.ValueRestrictionNode: 'value-restriction',
            Item.InclusionEdge: 'inclusion',
            Item.InputEdge: 'input',
            Item.InstanceOfEdge: 'instance-of',
        }

    ####################################################################################################################
    #                                                                                                                  #
    #   NODES                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

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

    def exportValueRestrictionNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: ValueRestrictionNode
        :rtype: QDomElement
        """
        return self.exportLabelNode(node)

    ####################################################################################################################
    #                                                                                                                  #
    #   EDGES                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    def exportInclusionEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: InclusionEdge
        :rtype: QDomElement
        """
        element = self.exportGenericEdge(edge)
        element.setAttribute('complete', int(edge.complete))
        return element

    def exportInputEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: InputEdge
        :rtype: QDomElement
        """
        return self.exportGenericEdge(edge)

    def exportInstanceOfEdge(self, edge):
        """
        Export the given edge into a QDomElement.
        :type edge: InstanceOf
        :rtype: QDomElement
        """
        return self.exportGenericEdge(edge)

    ####################################################################################################################
    #                                                                                                                  #
    #   METADATA                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def exportPredicateMetadata(self, item, predicate):
        """
        Export given predicate metadata.
        :type item: Item
        :type predicate: str
        :rtype: QDomElement
        """
        meta = self.scene.meta.metaFor(item, predicate)
        if meta:
            element = self.document.createElement('meta')
            element.setAttribute('type', self.itemToXml[item])
            element.setAttribute('predicate', predicate)
            url = self.document.createElement('data:url')
            url.appendChild(self.document.createTextNode(meta.url))
            description = self.document.createElement('data:description')
            description.appendChild(self.document.createTextNode(meta.description))
            element.appendChild(url)
            element.appendChild(description)
            return element
        return None

    def exportAttributeMetadata(self, item, predicate):
        """
        Export given attribute metadata.
        :type item: Item
        :type predicate: str
        :rtype: QDomElement
        """
        element = self.exportPredicateMetadata(item, predicate)
        if element:
            meta = self.scene.meta.metaFor(item, predicate)
            if meta:
                functionality = self.document.createElement('data:functionality')
                functionality.appendChild(self.document.createTextNode(str(int(meta.functionality))))
                element.appendChild(functionality)
                return element
        return None

    def exportRoleMetadata(self, item, predicate):
        """
        Export given role metadata
        :type item: Item
        :type predicate: str
        :rtype: QDomElement
        """
        element = self.exportPredicateMetadata(item, predicate)
        if element:
            meta = self.scene.meta.metaFor(item, predicate)
            if meta:
                functionality = self.document.createElement('data:functionality')
                functionality.appendChild(self.document.createTextNode(str(int(meta.functionality))))
                inverseFunctionality = self.document.createElement('data:inverseFunctionality')
                inverseFunctionality.appendChild(self.document.createTextNode(str(int(meta.inverseFunctionality))))
                asymmetry = self.document.createElement('data:asymmetry')
                asymmetry.appendChild(self.document.createTextNode(str(int(meta.asymmetry))))
                irreflexivity = self.document.createElement('data:irreflexivity')
                irreflexivity.appendChild(self.document.createTextNode(str(int(meta.irreflexivity))))
                reflexivity = self.document.createElement('data:reflexivity')
                reflexivity.appendChild(self.document.createTextNode(str(int(meta.reflexivity))))
                symmetry = self.document.createElement('data:symmetry')
                symmetry.appendChild(self.document.createTextNode(str(int(meta.symmetry))))
                transitivity = self.document.createElement('data:transitivity')
                transitivity.appendChild(self.document.createTextNode(str(int(meta.transitivity))))
                element.appendChild(functionality)
                element.appendChild(inverseFunctionality)
                element.appendChild(asymmetry)
                element.appendChild(irreflexivity)
                element.appendChild(reflexivity)
                element.appendChild(symmetry)
                element.appendChild(transitivity)
                return element
        return None

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def exportLabelNode(self, node):
        """
        Export the given node into a QDomElement.
        :type node: AbstractNode
        :rtype: QDomElement
        """
        position = node.mapToScene(node.textPos())
        label = self.document.createElement('shape:label')
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
        element.setAttribute('type', self.itemToXml[edge.item])

        for p in [edge.source.anchor(edge)] + edge.breakpoints + [edge.target.anchor(edge)]:
            point = self.document.createElement('line:point')
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
        element.setAttribute('type', self.itemToXml[node.item])
        element.setAttribute('color', node.brush.color().name())
        geometry = self.document.createElement('shape:geometry')
        geometry.setAttribute('height', node.height())
        geometry.setAttribute('width', node.width())
        geometry.setAttribute('x', node.pos().x())
        geometry.setAttribute('y', node.pos().y())
        element.appendChild(geometry)
        return element

    ####################################################################################################################
    #                                                                                                                  #
    #   DOCUMENT EXPORT                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def export(self, indent=4):
        """
        Export the coverted ontology.
        :type indent: int
        :rtype: str
        """
        return self.document.toString(indent)

    ####################################################################################################################
    #                                                                                                                  #
    #   DOCUMENT GENERATION                                                                                            #
    #                                                                                                                  #
    ####################################################################################################################

    def run(self):
        """
        Perform Graphol ontology generation.
        """
        # 1) CREATE THE DOCUMENT
        self.document = QDomDocument()
        self.document.appendChild(self.document.createProcessingInstruction('xml', 'version="1.0" '
                                                                                   'encoding="UTF-8" '
                                                                                   'standalone="no"'))
        
        # 2) CREATE ROOT ELEMENT
        root = self.document.createElement('graphol')
        root.setAttribute('xmlns', 'http://www.dis.uniroma1.it/~graphol/schema')
        root.setAttribute('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.setAttribute('xmlns:data', 'http://www.dis.uniroma1.it/~graphol/schema/data')
        root.setAttribute('xmlns:line', 'http://www.dis.uniroma1.it/~graphol/schema/line')
        root.setAttribute('xmlns:shape', 'http://www.dis.uniroma1.it/~graphol/schema/shape')
        root.setAttribute('xsi:schemaLocation', 'http://www.dis.uniroma1.it/~graphol/schema '
                                                'http://www.dis.uniroma1.it/~graphol/schema/graphol.xsd')
        
        self.document.appendChild(root)
        
        # 3) CREATE THE GRAPH NODE
        graph = self.document.createElement('graph')
        graph.setAttribute('width', self.scene.sceneRect().width())
        graph.setAttribute('height', self.scene.sceneRect().height())
        
        # 4) GENERATE NODES
        for node in self.scene.nodes():
        
            element = None

            if node.item is Item.AttributeNode:
                element = self.exportAttributeNode(node)
            elif node.item is Item.ComplementNode:
                element = self.exportComplementNode(node)
            elif node.item is Item.ConceptNode:
                element = self.exportConceptNode(node)
            elif node.item is Item.DatatypeRestrictionNode:
                element = self.exportDatatypeRestrictionNode(node)
            elif node.item is Item.DisjointUnionNode:
                element = self.exportDisjointUnionNode(node)
            elif node.item is Item.DomainRestrictionNode:
                element = self.exportDomainRestrictionNode(node)
            elif node.item is Item.EnumerationNode:
                element = self.exportEnumerationNode(node)
            elif node.item is Item.IndividualNode:
                element = self.exportIndividualNode(node)
            elif node.item is Item.IntersectionNode:
                element = self.exportIntersectionNode(node)
            elif node.item is Item.PropertyAssertionNode:
                element = self.exportPropertyAssertionNode(node)
            elif node.item is Item.RangeRestrictionNode:
                element = self.exportRangeRestrictionNode(node)
            elif node.item is Item.RoleNode:
                element = self.exportRoleNode(node)
            elif node.item is Item.RoleChainNode:
                element = self.exportRoleChainNode(node)
            elif node.item is Item.RoleInverseNode:
                element = self.exportRoleInverseNode(node)
            elif node.item is Item.UnionNode:
                element = self.exportUnionNode(node)
            elif node.item is Item.ValueDomainNode:
                element = self.exportValueDomainNode(node)
            elif node.item is Item.ValueRestrictionNode:
                element = self.exportValueRestrictionNode(node)

            if not element:
                raise ValueError('unknown node: {}'.format(node))

            graph.appendChild(element)

        # 5) GENERATE EDGES
        for edge in self.scene.edges():

            element = None

            if edge.item is Item.InclusionEdge:
                element = self.exportInclusionEdge(edge)
            elif edge.item is Item.InputEdge:
                element = self.exportInputEdge(edge)
            elif edge.item is Item.InstanceOfEdge:
                element = self.exportInstanceOfEdge(edge)

            if not element:
                raise ValueError('unknown edge: {}'.format(edge))

            graph.appendChild(element)

        # 6) APPEND THE GRAPH TO THE DOCUMENT
        root.appendChild(graph)

        # 7) GENERATE NODES META DATA
        collection = []
        for item, predicate in self.scene.meta.entries():

            if item is Item.RoleNode:
                element = self.exportRoleMetadata(item, predicate)
            elif item is Item.AttributeNode:
                element = self.exportAttributeMetadata(item, predicate)
            else:
                element = self.exportPredicateMetadata(item, predicate)

            if element:
                collection.append(element)

        if collection:
            metadata = self.document.createElement('metadata')
            for element in collection:
                metadata.appendChild(element)
            root.appendChild(metadata)