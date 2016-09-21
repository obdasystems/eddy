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

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtXml

from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.system import File
from eddy.core.diagram import Diagram
from eddy.core.diagram import DiagramNotFoundError
from eddy.core.diagram import DiagramNotValidError
from eddy.core.diagram import DiagramParseError
from eddy.core.functions.fsystem import fexists
from eddy.core.functions.fsystem import fread
from eddy.core.functions.misc import snapF, isEmpty, rstrip, snap
from eddy.core.functions.path import uniquePath
from eddy.core.functions.signals import connect
from eddy.core.loaders.common import AbstractDiagramLoader
from eddy.core.output import getLogger


LOGGER = getLogger(__name__)


class GraphMLDiagramLoader(AbstractDiagramLoader):
    """
    Extends AbstractDiagramLoader with facilities to load diagrams from GraphML file format.
    """
    def __init__(self, path, project, session):
        """
        Initialize the GraphML importer.
        :type path: str
        :type project: Project
        :type session: Session
        """
        super(GraphMLDiagramLoader, self).__init__(path, project, session)

        self.diagram = None
        self.keys = dict()
        self.edges = dict()
        self.nodes = dict()
        
        self.importFuncForItem = {
            Item.AttributeNode: self.buildAttributeNode,
            Item.ComplementNode: self.buildComplementNode,
            Item.ConceptNode: self.buildConceptNode,
            Item.DatatypeRestrictionNode: self.buildDatatypeRestrictionNode,
            Item.DisjointUnionNode: self.buildDisjointUnionNode,
            Item.DomainRestrictionNode: self.buildDomainRestrictionNode,
            Item.EnumerationNode: self.buildEnumerationNode,
            Item.FacetNode: self.buildFacetNode,
            Item.IndividualNode: self.buildIndividualNode,
            Item.IntersectionNode: self.buildIntersectionNode,
            Item.RangeRestrictionNode: self.buildRangeRestrictionNode,
            Item.RoleNode: self.buildRoleNode,
            Item.RoleChainNode: self.buildRoleChainNode,
            Item.RoleInverseNode: self.buildRoleInverseNode,
            Item.UnionNode: self.buildUnionNode,
            Item.ValueDomainNode: self.buildValueDomainNode,
            Item.InclusionEdge: self.buildInclusionEdge,
            Item.EquivalenceEdge: self.buildEquivalenceEdge,
            Item.InputEdge: self.buildInputEdge,
            Item.MembershipEdge: self.buildMembershipEdge,
        }

    #############################################
    #   NODES
    #################################

    def buildAttributeNode(self, element):
        """
        Build an Attribute node using the given QDomElement.
        :type element: QDomElement
        :rtype: AttributeNode
        """
        return self.buildNodeFromGenericNode(Item.AttributeNode, element)

    def buildComplementNode(self, element):
        """
        Build a Complement node using the given QDomElement.
        :type element: QDomElement
        :rtype: ComplementNode
        """
        return self.buildNodeFromShapeNode(Item.ComplementNode, element)

    def buildConceptNode(self, element):
        """
        Build a Concept node using the given QDomElement.
        :type element: QDomElement
        :rtype: ConceptNode
        """
        return self.buildNodeFromGenericNode(Item.ConceptNode, element)

    def buildDatatypeRestrictionNode(self, element):
        """
        Build a DatatypeRestriction node using the given QDomElement.
        :type element: QDomElement
        :rtype: DatatypeRestrictionNode
        """
        return self.buildNodeFromShapeNode(Item.DatatypeRestrictionNode, element)

    def buildDisjointUnionNode(self, element):
        """
        Build a DisjointUnion node using the given QDomElement.
        :type element: QDomElement
        :rtype: DisjointUnionNode
        """
        return self.buildNodeFromShapeNode(Item.DisjointUnionNode, element)

    def buildDomainRestrictionNode(self, element):
        """
        Build a DomainRestriction node using the given QDomElement.
        :type element: QDomElement
        :rtype: DomainRestrictionNode
        """
        return self.buildNodeFromShapeNode(Item.DomainRestrictionNode, element)

    def buildEnumerationNode(self, element):
        """
        Build an Enumeration node using the given QDomElement.
        :type element: QDomElement
        :rtype: EnumerationNode
        """
        return self.buildNodeFromShapeNode(Item.EnumerationNode, element)

    def buildFacetNode(self, element):
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

    def buildIndividualNode(self, element):
        """
        Build an Individual node using the given QDomElement.
        :type element: QDomElement
        :rtype: IndividualNode
        """
        return self.buildNodeFromShapeNode(Item.IndividualNode, element)

    def buildIntersectionNode(self, element):
        """
        Build an Intersection node using the given QDomElement.
        :type element: QDomElement
        :rtype: IntersectionNode
        """
        return self.buildNodeFromShapeNode(Item.IntersectionNode, element)

    def buildRangeRestrictionNode(self, element):
        """
        Build a RangeRestriction node using the given QDomElement.
        :type element: QDomElement
        :rtype: RangeRestrictionNode
        """
        return self.buildNodeFromShapeNode(Item.RangeRestrictionNode, element)

    def buildRoleNode(self, element):
        """
        Build a Role node using the given QDomElement.
        :type element: QDomElement
        :rtype: RoleNode
        """
        return self.buildNodeFromGenericNode(Item.RoleNode, element)

    def buildRoleChainNode(self, element):
        """
        Build a RoleChain node using the given QDomElement.
        :type element: QDomElement
        :rtype: RoleChainNode
        """
        return self.buildNodeFromShapeNode(Item.RoleChainNode, element)

    def buildRoleInverseNode(self, element):
        """
        Build a RoleInverse node using the given QDomElement.
        :type element: QDomElement
        :rtype: RoleInverseNode
        """
        return self.buildNodeFromShapeNode(Item.RoleInverseNode, element)

    def buildValueDomainNode(self, element):
        """
        Build a Value-Domain node using the given QDomElement.
        :type element: QDomElement
        :rtype: ValueDomainNode
        """
        return self.buildNodeFromShapeNode(Item.ValueDomainNode, element)

    def buildUnionNode(self, element):
        """
        Build a Union node using the given QDomElement.
        :type element: QDomElement
        :rtype: UnionNode
        """
        return self.buildNodeFromShapeNode(Item.UnionNode, element)

    #############################################
    #   NODES
    #################################

    def buildEquivalenceEdge(self, element):
        """
        Build an Equivalence edge using the given QDomElement.
        :type element: QDomElement
        :rtype: EquivalenceEdge
        """
        edge = self.buildEdgeFromGenericEdge(Item.EquivalenceEdge, element)
        if edge:
            edge.updateEdge()
        return edge

    def buildInclusionEdge(self, element):
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
                    return self.buildEquivalenceEdge(element)
        edge = self.buildEdgeFromGenericEdge(Item.InclusionEdge, element)
        if edge:
            edge.updateEdge()
        return edge

    def buildInputEdge(self, element):
        """
        Build an Input edge using the given QDomElement.
        :type element: QDomElement
        :rtype: InputEdge
        """
        edge = self.buildEdgeFromGenericEdge(Item.InputEdge, element)
        if edge:
            edge.updateEdge()
        return edge

    def buildMembershipEdge(self, element):
        """
        Build a Membership edge using the given QDomElement.
        :type element: QDomElement
        :rtype: InputEdge
        """
        edge = self.buildEdgeFromGenericEdge(Item.MembershipEdge, element)
        if edge:
            edge.updateEdge()
        return edge

    #############################################
    #   AUXILIARY METHODS
    #################################

    def buildEdgeFromGenericEdge(self, item, element):
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
                    raise DiagramParseError('missing source node ({0})'.format(element.attribute('source')))
                if not element.attribute('target') in self.nodes:
                    raise DiagramParseError('missing target node ({0})'.format(element.attribute('target')))

                points = []
                polyLineEdge = data.firstChildElement('y:PolyLineEdge')
                path = polyLineEdge.firstChildElement('y:Path')
                collection = path.elementsByTagName('y:Point')
                for i in range(0, collection.count()):
                    point = collection.at(i).toElement()
                    pos = QtCore.QPointF(float(point.attribute('x')), float(point.attribute('y')))
                    pos = QtCore.QPointF(snapF(pos.x(), Diagram.GridSize), snapF(pos.y(), Diagram.GridSize))
                    points.append(pos)

                source = self.nodes[element.attribute('source')]
                target = self.nodes[element.attribute('target')]
                kwargs = {'id': element.attribute('id'), 'source': source, 'target': target, 'breakpoints': points}
                edge = self.diagram.factory.create(item, **kwargs)
                edge.source.setAnchor(edge, self.parseAnchorPos(edge, edge.source, path.attribute('sx'), path.attribute('sy')))
                edge.target.setAnchor(edge, self.parseAnchorPos(edge, edge.target, path.attribute('tx'), path.attribute('ty')))
                edge.source.addEdge(edge)
                edge.target.addEdge(edge)
                return edge

            data = data.nextSiblingElement('data')

        return None

    def buildNodeFromGenericNode(self, item, element):
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

    def buildNodeFromShapeNode(self, item, element):
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
                nodeNode = data.firstChildElement('y:UMLNoteNode')
                if not nodeNode.isNull():
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
                                if  edgeText == 'instanceOf':
                                    return Item.MembershipEdge
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
    def parseLabelPos(geometry, nodeLabel):
        """
        Parse the node label position properly translating it from yEd coordinate system.
        :type geometry: QDomElement
        :type nodeLabel: QDomElement
        :rtype: QtCore.QPointF
        """
        return QtCore.QPointF(float(nodeLabel.attribute('x')), float(nodeLabel.attribute('y'))) - \
               QtCore.QPointF(float(geometry.attribute('width')) / 2, float(geometry.attribute('height')) / 2) + \
               QtCore.QPointF(float(nodeLabel.attribute('width')) / 2, float(nodeLabel.attribute('height')) / 2)

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
        return snap(QtCore.QPointF(float(geometry.attribute('x')), float(geometry.attribute('y'))) + \
                    QtCore.QPointF(float(geometry.attribute('width')) / 2, float(geometry.attribute('height')) / 2), Diagram.GridSize)

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

    def load(self):
        """
        Perform diagram import from .graphml file format.
        :raise DiagramNotFoundError: If the given path does not identify a .graphml module.
        :raise DiagramNotValidError: If the given path identifies an invalid .graphml module.
        """
        LOGGER.info('Loading diagram: %s', self.path)

        if not fexists(self.path):
            raise DiagramNotFoundError('diagram not found: {0}'.format(self.path))

        document = QtXml.QDomDocument()
        if not document.setContent(fread(self.path)):
            raise DiagramNotValidError('could not parse diagram from {0}'.format(self.path))

        root = document.documentElement()
        graph = root.firstChildElement('graph')

        #############################################
        # READ NECESSARY DATA FROM DOCUMENT HEADER
        #################################

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

        LOGGER.debug('Using node_key: %s', self.keys['node_key'])
        LOGGER.debug('Using edge_key: %s', self.keys['edge_key'])

        #############################################
        # CREATE AN EMPTY DIAGRAM
        #################################

        name = rstrip(os.path.basename(self.path), File.GraphML.extension)
        path = uniquePath(self.project.path, name, File.GraphML.extension)
        self.diagram = Diagram(path, self.project)
        self.diagram.setSceneRect(QtCore.QRectF(-Diagram.MaxSize / 2, -Diagram.MaxSize / 2, Diagram.MaxSize, Diagram.MaxSize))
        self.diagram.setItemIndexMethod(Diagram.NoIndex)

        LOGGER.debug('Initialzing empty diagram with size: %s', Diagram.MaxSize)

        #############################################
        # LOAD NODES
        #################################

        element = graph.firstChildElement('node')
        while not element.isNull():

            QtWidgets.QApplication.processEvents()

            try:
                item = self.itemFromXmlNode(element)
                if not item:
                    raise DiagramParseError('could not identify item for XML node')
                func = self.importFuncForItem[item]
                node = func(element)
                if not node:
                    raise DiagramParseError('could not generate item for XML node')
            except DiagramParseError as e:
                LOGGER.warning('Failed to create node %s: %s', element.attribute('id'), e)
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

            QtWidgets.QApplication.processEvents()

            try:
                item = self.itemFromXmlNode(element)
                if not item:
                    raise DiagramParseError('could not identify item for XML node')
                func = self.importFuncForItem[item]
                edge = func(element)
                if not edge:
                    raise DiagramParseError('could not generate item for XML node')
            except DiagramParseError as e:
                LOGGER.warning('Failed to create edge %s: %s', element.attribute('id'), e)
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
        # CENTER THE DIAGRAM
        #################################

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
                if item.isEdge():
                    item.updateEdge()

        #############################################
        # RESIZE THE DIAGRAM
        #################################

        R3 = self.diagram.visibleRect(margin=20)
        size = int(max(R3.width(), R3.height(), Diagram.MinSize))
        self.diagram.setSceneRect(QtCore.QRectF(-size / 2, -size / 2, size, size))

        LOGGER.debug('Diagram resized: %s -> %s', Diagram.MaxSize, size)

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

        return self.diagram