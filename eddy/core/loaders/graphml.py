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


import itertools
import os

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtXml

from eddy.core.datatypes.graphol import Item, Identity, Restriction
from eddy.core.datatypes.system import File
from eddy.core.diagram import Diagram
from eddy.core.diagram import DiagramNotFoundError
from eddy.core.diagram import DiagramNotValidError
from eddy.core.diagram import DiagramParseError
from eddy.core.functions.fsystem import fexists
from eddy.core.functions.fsystem import fread
from eddy.core.functions.misc import snapF, isEmpty, rstrip, snap
from eddy.core.functions.signals import connect
from eddy.core.loaders.common import AbstractOntologyLoader
from eddy.core.output import getLogger
from eddy.core.project import Project


LOGGER = getLogger()


class GraphMLOntologyLoader(AbstractOntologyLoader):
    """
    Extends AbstractOntologyLoader with facilities to load ontologies from GraphML file format.
    """
    def __init__(self, path, project, session):
        """
        Initialize the GraphML importer.
        :type path: str
        :type project: Project
        :type session: Session
        """
        super().__init__(path, project, session)

        self.keys = dict()
        self.edges = dict()
        self.nodes = dict()
        self.diagram = None
        self.document = None
        self.nproject = None

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

    #############################################
    #   NODES
    #################################

    def importAttributeNode(self, element):
        """
        Build an Attribute node using the given QDomElement.
        :type element: QDomElement
        :rtype: AttributeNode
        """
        imported_item =  self.importNodeFromGenericNode(Item.AttributeNode, element)
        imported_item.remaining_characters = element.attribute('remaining_characters','')

        return imported_item

    def importComplementNode(self, element):
        """
        Build a Complement node using the given QDomElement.
        :type element: QDomElement
        :rtype: ComplementNode
        """
        return self.importNodeFromShapeNode(Item.ComplementNode, element)

    def importConceptNode(self, element):
        """
        Build a Concept node using the given QDomElement.
        :type element: QDomElement
        :rtype: ConceptNode
        """
        imported_item =  self.importNodeFromGenericNode(Item.ConceptNode, element)
        imported_item.remaining_characters = element.attribute('remaining_characters','')

        return imported_item

    def importDatatypeRestrictionNode(self, element):
        """
        Build a DatatypeRestriction node using the given QDomElement.
        :type element: QDomElement
        :rtype: DatatypeRestrictionNode
        """
        return self.importNodeFromShapeNode(Item.DatatypeRestrictionNode, element)

    def importDisjointUnionNode(self, element):
        """
        Build a DisjointUnion node using the given QDomElement.
        :type element: QDomElement
        :rtype: DisjointUnionNode
        """
        return self.importNodeFromShapeNode(Item.DisjointUnionNode, element)

    def importDomainRestrictionNode(self, element):
        """
        Build a DomainRestriction node using the given QDomElement.
        :type element: QDomElement
        :rtype: DomainRestrictionNode
        """
        return self.importNodeFromShapeNode(Item.DomainRestrictionNode, element)

    def importEnumerationNode(self, element):
        """
        Build an Enumeration node using the given QDomElement.
        :type element: QDomElement
        :rtype: EnumerationNode
        """
        return self.importNodeFromShapeNode(Item.EnumerationNode, element)

    def importFacetNode(self, element):
        """
        Build a FacetNode node using the given QDomElement.
        :type element: QDomElement
        :rtype: FacetNode
        """
        data = element.firstChildElement('data')
        while not data.isNull():
            if data.attribute('key', '') == self.keys['node_key']:
                noteNode = data.firstChildElement('y:UMLNoteNode')
                geometry = noteNode.firstChildElement('y:Geometry')
                nodeLabel = noteNode.firstChildElement('y:NodeLabel')
                h = float(geometry.attribute('height'))
                w = float(geometry.attribute('width'))
                kwargs = {'id': element.attribute('id'), 'height': h, 'width': w}
                node = self.diagram.factory.create(Item.FacetNode, **kwargs)
                node.setPos(self.parsePos(geometry))
                node.setText(nodeLabel.text())
                return node
            data = data.nextSiblingElement('data')
        return None

    def importIndividualNode(self, element):
        """
        Build an Individual node using the given QDomElement.
        :type element: QDomElement
        :rtype: IndividualNode
        """
        imported_item =  self.importNodeFromShapeNode(Item.IndividualNode, element)
        imported_item.remaining_characters = element.attribute('remaining_characters','')

        return imported_item

    def importIntersectionNode(self, element):
        """
        Build an Intersection node using the given QDomElement.
        :type element: QDomElement
        :rtype: IntersectionNode
        """
        return self.importNodeFromShapeNode(Item.IntersectionNode, element)

    def importRangeRestrictionNode(self, element):
        """
        Build a RangeRestriction node using the given QDomElement.
        :type element: QDomElement
        :rtype: RangeRestrictionNode
        """
        return self.importNodeFromShapeNode(Item.RangeRestrictionNode, element)

    def importRoleNode(self, element):
        """
        Build a Role node using the given QDomElement.
        :type element: QDomElement
        :rtype: RoleNode
        """
        imported_item = self.importNodeFromGenericNode(Item.RoleNode, element)
        imported_item.remaining_characters = element.attribute('remaining_characters','')

        return imported_item

    def importRoleChainNode(self, element):
        """
        Build a RoleChain node using the given QDomElement.
        :type element: QDomElement
        :rtype: RoleChainNode
        """
        return self.importNodeFromShapeNode(Item.RoleChainNode, element)

    def importRoleInverseNode(self, element):
        """
        Build a RoleInverse node using the given QDomElement.
        :type element: QDomElement
        :rtype: RoleInverseNode
        """
        return self.importNodeFromShapeNode(Item.RoleInverseNode, element)

    def importValueDomainNode(self, element):
        """
        Build a Value-Domain node using the given QDomElement.
        :type element: QDomElement
        :rtype: ValueDomainNode
        """
        return self.importNodeFromShapeNode(Item.ValueDomainNode, element)

    def importUnionNode(self, element):
        """
        Build a Union node using the given QDomElement.
        :type element: QDomElement
        :rtype: UnionNode
        """
        return self.importNodeFromShapeNode(Item.UnionNode, element)

    #############################################
    #   EDGES
    #################################

    def importEquivalenceEdge(self, element):
        """
        Build an Equivalence edge using the given QDomElement.
        :type element: QDomElement
        :rtype: EquivalenceEdge
        """
        edge = self.importEdgeFromGenericEdge(Item.EquivalenceEdge, element)
        if edge:
            edge.updateEdge()
        return edge

    def importInclusionEdge(self, element):
        """
        Build an Inclusion edge using the given QDomElement.
        :type element: QDomElement
        :rtype: InclusionEdge
        """
        data = element.firstChildElement('data')
        while not data.isNull():
            if data.attribute('key', '') == self.keys['edge_key']:
                polyLineEdge = data.firstChildElement('y:PolyLineEdge')
                arrows = polyLineEdge.firstChildElement('y:Arrows')
                if arrows.attribute('source', '') == 'standard' and arrows.attribute('target', '') == 'standard':
                    return self.importEquivalenceEdge(element)
            data = data.nextSiblingElement('data')
        edge = self.importEdgeFromGenericEdge(Item.InclusionEdge, element)
        if edge:
            edge.updateEdge()
        return edge

    def importInputEdge(self, element):
        """
        Build an Input edge using the given QDomElement.
        :type element: QDomElement
        :rtype: InputEdge
        """
        edge = self.importEdgeFromGenericEdge(Item.InputEdge, element)
        if edge:
            edge.updateEdge()
        return edge

    def importMembershipEdge(self, element):
        """
        Build a Membership edge using the given QDomElement.
        :type element: QDomElement
        :rtype: MembershipEdge
        """
        edge = self.importEdgeFromGenericEdge(Item.MembershipEdge, element)
        if edge:
            edge.updateEdge()
        return edge

    def importSameEdge(self, element):
        """
        Build a Same edge using the given QDomElement.
        :type element: QDomElement
        :rtype: SameEdge
        """
        edge = self.importEdgeFromGenericEdge(Item.SameEdge, element)
        if edge:
            edge.updateEdge()
        return edge

    def importDifferentEdge(self, element):
        """
        Build a Different edge using the given QDomElement.
        :type element: QDomElement
        :rtype: DifferentEdge
        """
        edge = self.importEdgeFromGenericEdge(Item.DifferentEdge, element)
        if edge:
            edge.updateEdge()
        return edge

    #############################################
    #   AUXILIARY METHODS
    #################################

    def importEdgeFromGenericEdge(self, item, element):
        """
        Build an edge using the given item type and QDomElement.
        :type item: Item
        :type element: QDomElement
        raise DiagramParseError: If one of the endpoints of the edge is not available.
        :rtype: AbstractEdge
        """
        data = element.firstChildElement('data')
        while not data.isNull():

            if data.attribute('key', '') == self.keys['edge_key']:

                if not element.attribute('source') in self.nodes:
                    raise DiagramParseError('missing source node (%s)' % element.attribute('source'))
                if not element.attribute('target') in self.nodes:
                    raise DiagramParseError('missing target node (%s)' % element.attribute('target'))

                source = self.nodes[element.attribute('source')]
                target = self.nodes[element.attribute('target')]

                if source is target:
                    raise DiagramParseError('detected loop between nodes %s and %s' % (source.id, target.id))

                points = []
                polyLineEdge = data.firstChildElement('y:PolyLineEdge')
                path = polyLineEdge.firstChildElement('y:Path')
                collection = path.elementsByTagName('y:Point')
                for i in range(0, collection.count()):
                    point = collection.at(i).toElement()
                    pos = QtCore.QPointF(float(point.attribute('x')), float(point.attribute('y')))
                    pos = QtCore.QPointF(snapF(pos.x(), Diagram.GridSize), snapF(pos.y(), Diagram.GridSize))
                    points.append(pos)

                kwargs = {'id': element.attribute('id'), 'source': source, 'target': target, 'breakpoints': points}
                edge = self.diagram.factory.create(item, **kwargs)
                edge.source.setAnchor(edge, self.parseAnchorPos(edge, edge.source, path.attribute('sx'), path.attribute('sy')))
                edge.target.setAnchor(edge, self.parseAnchorPos(edge, edge.target, path.attribute('tx'), path.attribute('ty')))
                edge.source.addEdge(edge)
                edge.target.addEdge(edge)
                return edge

            data = data.nextSiblingElement('data')

        return None

    def importNodeFromGenericNode(self, item, element):
        """
        Build a node using the given item type and QDomElement.
        :type item: Item
        :type element: QDomElement
        :rtype: AbstractNode
        """
        data = element.firstChildElement('data')
        while not data.isNull():
            if data.attribute('key', '') == self.keys['node_key']:
                genericNode = data.firstChildElement('y:GenericNode')
                geometry = genericNode.firstChildElement('y:Geometry')
                nodeLabel = genericNode.firstChildElement('y:NodeLabel')
                h = float(geometry.attribute('height'))
                w = float(geometry.attribute('width'))
                kwargs = {'id': element.attribute('id'), 'height': h, 'width': w}
                node = self.diagram.factory.create(item, **kwargs)
                node.setPos(self.parsePos(geometry))
                node.setText(nodeLabel.text())
                node.setTextPos(self.parseLabelPos(geometry, nodeLabel))
                return node
            data = data.nextSiblingElement('data')
        return None

    def importNodeFromShapeNode(self, item, element):
        """
        Build a node using the given item type and QDomElement.
        :type item: Item
        :type element: QDomElement
        :rtype: AbstractNode
        """
        data = element.firstChildElement('data')
        while not data.isNull():
            if data.attribute('key', '') == self.keys['node_key']:
                shapeNode = data.firstChildElement('y:ShapeNode')
                geometry = shapeNode.firstChildElement('y:Geometry')
                h = float(geometry.attribute('height'))
                w = float(geometry.attribute('width'))
                kwargs = {'id': element.attribute('id'), 'height': h, 'width': w}
                node = self.diagram.factory.create(item, **kwargs)
                node.setPos(self.parsePos(geometry))
                # For the following items we also import the label.
                # Other operator nodes have fixed label so it's pointless.
                if item in {Item.DomainRestrictionNode, Item.RangeRestrictionNode, Item.ValueDomainNode, Item.IndividualNode}:
                    nodeLabel = shapeNode.firstChildElement('y:NodeLabel')
                    node.setText(nodeLabel.text())
                    if not isEmpty(nodeLabel.text()):
                        # If the node label is empty do not set the position.
                        # This is needed because domain restriction and range restriction nodes
                        # usually do not have any label in gephol documents built with yEd.
                        node.setTextPos(self.parseLabelPos(geometry, nodeLabel))
                return node
            data = data.nextSiblingElement('data')
        return None

    def importPredicateMetaFromElement(self, element):
        """
        Import predicate metadata from the given element.
        :type element: QDomElement
        """
        if self.itemFromXmlNode(element) is Item.InputEdge:

            try:
                edge = self.edges[element.attribute('id')]
            except KeyError:
                LOGGER.warning('Failed to import [inverse]Functionality due to missing edge: %s', element.attribute('id'))
            else:
                data = element.firstChildElement('data')
                while not data.isNull():
                    if data.attribute('key', '') == self.keys['edge_key']:
                        polyLineEdge = data.firstChildElement('y:PolyLineEdge')
                        arrows = polyLineEdge.firstChildElement('y:Arrows')
                        if 't_shape' in {arrows.attribute('source', ''), arrows.attribute('target', '')}:
                            # When we detect a t_shape source or target arrow on an input edge
                            # we set the functionality on the connected predicate node. We should
                            # be setting the functionality only on the predicate identified in the
                            # source node, however in the graphol palette for yEd there is a bugged
                            # functionality edge, in which the target arrow is a t_shape, a and the
                            # source is a white_diamond. Because the input edge on one of the endpoints
                            # has a domain/range restriction node, we can easily establish on which
                            # endpoint we have to check the functionality attribute, since only one of the
                            # endpoints can be a predicate node (because inputs target only constructors).
                            if edge.source.type() in {Item.AttributeNode, Item.RoleNode}:
                                pnode = edge.source
                                cnode = edge.target
                            else:
                                pnode = edge.target
                                cnode = edge.source
                            # Functionality is for both Role and Attribute nodes.
                            if cnode.type() is Item.DomainRestrictionNode:
                                pnode.setFunctional(True)
                            # Inverse functionality is just for Role nodes.
                            if pnode.type() is Item.RoleNode:
                                if cnode.type() is Item.RangeRestrictionNode:
                                    pnode.setInverseFunctional(True)
                    data = data.nextSiblingElement('data')

    def itemFromXmlNode(self, element):
        """
        Returns the item matching the given Graphml node.
        :type element: QDomElement
        :rtype: Item
        """
        data = element.firstChildElement('data')
        while not data.isNull():

            # NODE
            if data.attribute('key', '') == self.keys['node_key']:
                # GENERIC NODE
                genericNode = data.firstChildElement('y:GenericNode')
                if not genericNode.isNull():
                    configuration = genericNode.attribute('configuration', '')
                    if configuration == 'com.yworks.entityRelationship.small_entity':
                        return Item.ConceptNode
                    if configuration == 'com.yworks.entityRelationship.attribute':
                        return Item.AttributeNode
                    if configuration == 'com.yworks.entityRelationship.relationship':
                        return Item.RoleNode

                # SHAPE NODE
                shapeNode = data.firstChildElement('y:ShapeNode')
                if not shapeNode.isNull():
                    shape = shapeNode.firstChildElement('y:Shape')
                    if not shape.isNull():
                        shapeType = shape.attribute('type', '')
                        if shapeType == 'octagon':
                            return Item.IndividualNode
                        if shapeType == 'roundrectangle':
                            return Item.ValueDomainNode
                        if shapeType == 'hexagon':
                            # We need to identify DisjointUnion from the color and not by
                            # checking the empty label because in some ontologies created
                            # under yEd another operator node has been copied over and the
                            # background color has been changed while keeping the label.
                            fill = shapeNode.firstChildElement('y:Fill')
                            if not fill.isNull():
                                color = fill.attribute('color', '')
                                if color == '#000000':
                                    return Item.DisjointUnionNode
                            nodeLabel = shapeNode.firstChildElement('y:NodeLabel')
                            if not nodeLabel.isNull():
                                nodeText = nodeLabel.text().strip()
                                if nodeText == 'and':
                                    return Item.IntersectionNode
                                if nodeText == 'or':
                                    return Item.UnionNode
                                if nodeText == 'not':
                                    return Item.ComplementNode
                                if nodeText == 'oneOf':
                                    return Item.EnumerationNode
                                if nodeText == 'chain':
                                    return Item.RoleChainNode
                                if nodeText == 'inv':
                                    return Item.RoleInverseNode
                                if nodeText == 'data':
                                    return Item.DatatypeRestrictionNode

                        if shapeType == 'rectangle':
                            fill = shapeNode.firstChildElement('y:Fill')
                            if not fill.isNull():
                                color = fill.attribute('color', '')
                                if color == '#000000':
                                    return Item.RangeRestrictionNode
                                return Item.DomainRestrictionNode

                # UML NOTE NODE
                noteNode = data.firstChildElement('y:UMLNoteNode')
                if not noteNode.isNull():
                    return Item.FacetNode

            # EDGE
            if data.attribute('key', '') == self.keys['edge_key']:
                polyLineEdge = data.firstChildElement('y:PolyLineEdge')
                if not polyLineEdge.isNull():
                    lineStyle = polyLineEdge.firstChildElement('y:LineStyle')
                    if not lineStyle.isNull():
                        lineType = lineStyle.attribute('type', '')
                        if lineType == 'line':
                            edgeLabel = polyLineEdge.firstChildElement('y:EdgeLabel')
                            if not edgeLabel.isNull():
                                edgeText = edgeLabel.text().strip()
                                if edgeText == 'instanceOf':
                                    return Item.MembershipEdge
                                elif edgeText == 'same':
                                    return Item.SameEdge
                                elif edgeText == 'different':
                                    return Item.DifferentEdge
                            return Item.InclusionEdge
                        if lineType == 'dashed':
                            return Item.InputEdge

            data = data.nextSiblingElement('data')

        return None

    @staticmethod
    def parseAnchorPos(edge, node, x, y):
        """
        Parse the given edge
        :type edge: AbstractEdge
        :type node: AbstractNode
        :type x: str
        :type y: str
        :rtype: QtCore.QPointF
        """
        path = node.painterPath()
        pos = QtCore.QPointF(float(x), float(y))
        if path.contains(pos):
            return snap(node.mapToScene(pos), Diagram.GridSize)
        return node.anchor(edge)

    @staticmethod
    def parseLabelPos(geometry, label):
        """
        Parse the node label position properly translating it from yEd coordinate system.
        :type geometry: QDomElement
        :type label: QDomElement
        :rtype: QtCore.QPointF
        """
        x1 = float(label.attribute('x'))
        y1 = float(label.attribute('y'))
        w1 = float(label.attribute('width'))
        h1 = float(label.attribute('height'))
        w2 = float(geometry.attribute('width'))
        h2 = float(geometry.attribute('height'))
        return QtCore.QPointF(x1, y1) - QtCore.QPointF(w2 / 2, h2 / 2) + QtCore.QPointF(w1 / 2, h1 / 2)

    @staticmethod
    def parsePos(geometry):
        """
        Parse the position of the node properly translating it from yEd coordinate system.
        :type geometry: QDomElement
        :rtype: QtCore.QPointF
        """
        # yEd uses the TOP-LEFT corner as (0,0) coordinate => we need to translate our
        # position (0,0), which is instead at the center of the shape, so that the TOP-LEFT
        # corner of the shape in yEd matches the TOP-LEFT corner of the shape in Eddy.
        # We additionally snap the position to the grid so that items stay perfectly aligned.
        x = float(geometry.attribute('x'))
        y = float(geometry.attribute('y'))
        w = float(geometry.attribute('width'))
        h = float(geometry.attribute('height'))
        return snap(QtCore.QPointF(x, y) + QtCore.QPointF(w / 2, h / 2), Diagram.GridSize)

    @staticmethod
    def optimizeLabelPos(node):
        """
        Perform updates on the position of the label of the given Domain o Range restriction node.
        This is due to yEd not using the label to denote the 'exists' restriction and because Eddy
        adds the label automatically, it may overlap some other elements hence we try to give it
        some more visibility by moving it around the node till it overlaps less stuff.
        :type node: T <= DomainRestrictionNode|RangeRestrictionNode
        """
        if node.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}:
            if node.restriction() is Restriction.Exists:
                if not node.label.isMoved() and node.label.collidingItems():
                    x = [-30, -15, 0, 15, 30]
                    y = [0, 12, 22, 32, 44]
                    pos = node.label.pos()
                    for offset_x, offset_y in itertools.product(x, y):
                        node.label.setPos(pos + QtCore.QPointF(offset_x, offset_y))
                        if not node.label.collidingItems():
                            break
                    else:
                        node.label.setPos(pos)

    #############################################
    #   MAIN IMPORT
    #################################

    def createDomDocument(self):
        """
        Create the QDomDocument from where to parse information.
        """
        QtWidgets.QApplication.processEvents()

        LOGGER.info('Loading diagram: %s', self.path)

        if not fexists(self.path):
            raise DiagramNotFoundError('diagram not found: {0}'.format(self.path))

        self.document = QtXml.QDomDocument()
        if not self.document.setContent(fread(self.path)):
            raise DiagramNotValidError('could not parse diagram from {0}'.format(self.path))

    def createDiagram(self):
        """
        Creates a diagram and reverse the content of the GraphML document in it.
        """
        LOGGER.debug('Initializing empty diagram with size: %s', Diagram.MaxSize)
        name = os.path.basename(self.path)
        name = rstrip(name, File.GraphML.extension)
        self.diagram = Diagram.create(name, Diagram.MaxSize, self.nproject)

        root = self.document.documentElement()
        graph = root.firstChildElement('graph')
        e = graph.firstChildElement('node')
        while not e.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromXmlNode(e)
                if not item:
                    raise DiagramParseError('could not identify item for XML node')
                func = self.importFuncForItem[item]
                node = func(e)
                if not node:
                    raise DiagramParseError('could not generate item for XML node')
            except DiagramParseError as err:
                LOGGER.warning('Failed to create node %s: %s', e.attribute('id'), err)
            except Exception:
                LOGGER.exception('Failed to create node %s', e.attribute('id'))
            else:
                self.diagram.addItem(node)
                self.diagram.guid.update(node.id)
                self.nodes[node.id] = node
            finally:
                e = e.nextSiblingElement('node')

        LOGGER.debug('Loaded nodes: %s', len(self.nodes))

        e = graph.firstChildElement('edge')
        while not e.isNull():
            try:
                QtWidgets.QApplication.processEvents()
                item = self.itemFromXmlNode(e)
                if not item:
                    raise DiagramParseError('could not identify item for XML node')
                func = self.importFuncForItem[item]
                edge = func(e)
                if not edge:
                    raise DiagramParseError('could not generate item for XML node')
            except DiagramParseError as err:
                LOGGER.warning('Failed to create edge %s: %s', e.attribute('id'), err)
            except Exception:
                LOGGER.exception('Failed to create edge %s', e.attribute('id'))
            else:
                self.diagram.addItem(edge)
                self.diagram.guid.update(edge.id)
                self.edges[edge.id] = edge
            finally:
                e = e.nextSiblingElement('edge')

        LOGGER.debug('Loaded edges: %s', len(self.edges))

        nodes = [n for n in self.nodes.values() if Identity.Neutral in n.identities()]
        if nodes:
            LOGGER.debug('Running identification algorithm for %s nodes', len(nodes))
            for node in nodes:
                QtWidgets.QApplication.processEvents()
                self.diagram.sgnNodeIdentification.emit(node)

        LOGGER.debug('Diagram created: %s', self.diagram.name)

        connect(self.diagram.sgnItemAdded, self.nproject.doAddItem)
        connect(self.diagram.sgnItemRemoved, self.nproject.doRemoveItem)
        connect(self.diagram.selectionChanged, self.session.doUpdateState)

        self.nproject.addDiagram(self.diagram)

        LOGGER.debug('Diagram "%s" added to project "%s"', self.diagram.name, self.nproject.name)

    def createProject(self):
        """
        Create a new project.
        """
        self.nproject = Project(
            name=rstrip(os.path.basename(self.path), File.GraphML.extension),
            path=os.path.dirname(self.path),
            profile=self.session.createProfile('OWL 2'),
            parent=self.session,
        )

        LOGGER.debug('Created project: %s', self.nproject.name)

    def importPredicateMeta(self):
        """
        Import predicate metadata into the new project.
        """
        r = self.document.documentElement()
        g = r.firstChildElement('graph')
        e = g.firstChildElement('edge')
        while not e.isNull():
            QtWidgets.QApplication.processEvents()
            self.importPredicateMetaFromElement(e)
            e = e.nextSiblingElement('edge')

        LOGGER.debug('Loaded predicate metadata from original diagram: %s', self.path)

    def optimizeDiagram(self):
        """
        Perform geometrical optimizations on the loaded diagram.
        """
        ## CENTER THE DIAGRAM
        R1 = self.diagram.sceneRect()
        R2 = self.diagram.visibleRect(margin=0)
        moveX = snapF(((R1.right() - R2.right()) - (R2.left() - R1.left())) / 2, Diagram.GridSize)
        moveY = snapF(((R1.bottom() - R2.bottom()) - (R2.top() - R1.top())) / 2, Diagram.GridSize)
        if moveX or moveY:
            collection = [x for x in self.diagram.items() if x.isNode() or x.isEdge()]
            for item in collection:
                QtWidgets.QApplication.processEvents()
                item.moveBy(moveX, moveY)
            for item in collection:
                QtWidgets.QApplication.processEvents()
                item.updateEdgeOrNode()
        ## RESIZE THE DIAGRAM
        R3 = self.diagram.visibleRect(margin=20)
        size = int(max(R3.width(), R3.height(), Diagram.MinSize))
        self.diagram.setSceneRect(QtCore.QRectF(-size / 2, -size / 2, size, size))
        LOGGER.debug('Diagram resized: %s -> %s', Diagram.MaxSize, size)
        ## OPTIMIZE NODE LABEL POSITIONS
        for node in self.diagram.nodes():
            QtWidgets.QApplication.processEvents()
            self.optimizeLabelPos(node)
        LOGGER.debug('Performed geometrical optimization on %s nodes', len(self.diagram.nodes()))

    def parseDocumentMeta(self):
        """
        Read metadata from the open QDomDocument, necessary to parse the GraphML diagram structure.
        """
        QtWidgets.QApplication.processEvents()

        root = self.document.documentElement()
        key = root.firstChildElement('key')
        while not key.isNull():
            if key.attribute('yfiles.type', '') == 'nodegraphics':
                self.keys['node_key'] = key.attribute('id')
            if key.attribute('yfiles.type', '') == 'edgegraphics':
                self.keys['edge_key'] = key.attribute('id')
            key = key.nextSiblingElement('key')

        if not 'node_key' in self.keys:
            raise DiagramNotValidError('could not parse node keys from {0}'.format(self.path))
        if not 'edge_key' in self.keys:
            raise DiagramNotValidError('could not parse edge keys from {0}'.format(self.path))

        LOGGER.debug('Using node key: %s', self.keys['node_key'])
        LOGGER.debug('Using edge key: %s', self.keys['edge_key'])

    def projectMerge(self):
        """
        Merge the loaded project with the one currently loaded in Eddy session.
        """
        return
        '''
        worker = ProjectMergeWorker(self.project, self.nproject, self.session)
        worker = ProjectMergeWorker(self.project, self.nproject, self.session, diagrams=self.nproject.diagrams())
        worker.run()
        '''

    def projectRender(self):
        """
        Render all the elements in the new project ontology.
        """
        LOGGER.debug('Refreshing project "%s" elements state', self.nproject.name)
        for item in self.nproject.items():
            QtWidgets.QApplication.processEvents()
            item.updateEdgeOrNode()

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        return File.GraphML

    def run(self):
        """
        Perform ontology import from GraphML file format and merge it with the current project.
        """
        self.createDomDocument()
        self.parseDocumentMeta()
        self.createProject()
        self.createDiagram()
        self.optimizeDiagram()
        self.importPredicateMeta()
        self.projectRender()
        self.projectMerge()
