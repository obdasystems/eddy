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


import os
import sys

from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import QGraphicsScene, QUndoStack

from eddy.core.commands.edges import CommandEdgeAdd
from eddy.core.commands.nodes import CommandNodeAdd, CommandNodeMove
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.functions.graph import bfs
from eddy.core.functions.misc import snap, snapF, partition, first
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect
from eddy.core.utils.clipboard import Clipboard


class Diagram(QGraphicsScene):
    """
    This class implements a graphol diagram.
    """
    GridPen = QPen(QColor(80, 80, 80), 0, Qt.SolidLine)
    GridSize = 20
    MinSize = 2000
    MaxSize = 1000000

    sgnActionCompleted = pyqtSignal('QGraphicsItem', int)
    sgnItemAdded = pyqtSignal('QGraphicsScene', 'QGraphicsItem')
    sgnItemRemoved = pyqtSignal('QGraphicsScene', 'QGraphicsItem')
    sgnModeChanged = pyqtSignal(DiagramMode)
    sgnUpdated = pyqtSignal()

    def __init__(self, path, parent):
        """
        Initialize the diagram.
        :type path: str
        :type parent: Project
        """
        super().__init__(parent)

        self.mode = DiagramMode.Idle
        self.modeParam = Item.Undefined
        self.path = expandPath(path)
        self.pasteX = Clipboard.PasteOffsetX
        self.pasteY = Clipboard.PasteOffsetY
        self.undoStack = QUndoStack(self)
        self.undoStack.setUndoLimit(100)

        self.mouseOverNode = None
        self.mousePressEdge = None
        self.mousePressPos = None
        self.mousePressNode = None
        self.mousePressNodePos = None
        self.mousePressData = {}

        connect(self.sgnItemAdded, self.onConnectionChanged)
        connect(self.sgnItemRemoved, self.onConnectionChanged)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def id(self):
        """
        Returns the pseudo unique id of this diagram (alias for Diagram.path).
        :rtype: str
        """
        return self.path

    @property
    def name(self):
        """
        Returns the name of the file where this diagram is stored.
        :rtype: str
        """
        return os.path.basename(os.path.normpath(self.path))

    @property
    def project(self):
        """
        Returns the project this diagram belongs to (alias for Diagram.parent()).
        :rtype: Project
        """
        return self.parent()

    #############################################
    #   EVENTS
    #################################

    def dragEnterEvent(self, dragEvent):
        """
        Executed when a dragged element enters the scene area.
        :type dragEvent: QGraphicsSceneDragDropEvent
        """
        super().dragEnterEvent(dragEvent)
        if dragEvent.mimeData().hasFormat('text/plain'):
            dragEvent.setDropAction(Qt.CopyAction)
            dragEvent.accept()
        else:
            dragEvent.ignore()

    def dragMoveEvent(self, dragEvent):
        """
        Executed when an element is dragged over the scene.
        :type dragEvent: QGraphicsSceneDragDropEvent
        """
        super().dragMoveEvent(dragEvent)
        if dragEvent.mimeData().hasFormat('text/plain'):
            dragEvent.setDropAction(Qt.CopyAction)
            dragEvent.accept()
        else:
            dragEvent.ignore()

    def dropEvent(self, dropEvent):
        """
        Executed when a dragged element is dropped on the diagram.
        :type dropEvent: QGraphicsSceneDragDropEvent
        """
        super().dropEvent(dropEvent)
        if dropEvent.mimeData().hasFormat('text/plain'):
            mainwindow = self.project.parent()
            snapToGrid = mainwindow.actionSnapToGrid.isChecked()
            node = self.project.itemFactory.create(Item.forValue(dropEvent.mimeData().text()))
            node.setPos(snap(dropEvent.scenePos(), Diagram.GridSize, snapToGrid))
            self.undoStack.push(CommandNodeAdd(self, node))
            self.sgnActionCompleted.emit(node, dropEvent.modifiers())
            dropEvent.setDropAction(Qt.CopyAction)
            dropEvent.accept()
        else:
            dropEvent.ignore()

    def mousePressEvent(self, mouseEvent):
        """
        Executed when a mouse button is clicked on the scene.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        mouseButtons = mouseEvent.buttons()
        mousePos = mouseEvent.scenePos()

        if mouseButtons & Qt.LeftButton:

            if self.mode is DiagramMode.InsertNode:

                #############################################
                # NODE INSERTION
                #################################

                mainwindow = self.project.parent()
                snapToGrid = mainwindow.actionSnapToGrid.isChecked()
                node = self.project.itemFactory.create(Item.forValue(self.modeParam))
                node.setPos(snap(mousePos, Diagram.GridSize, snapToGrid))
                self.undoStack.push(CommandNodeAdd(self, node))
                self.sgnActionCompleted.emit(node, mouseEvent.modifiers())

                super().mousePressEvent(mouseEvent)

            elif self.mode is DiagramMode.InsertEdge:

                #############################################
                # EDGE INSERTION
                #################################

                node = self.itemOnTopOf(mousePos, edges=False)
                if node:
                    edge = self.project.itemFactory.create(Item.forValue(self.modeParam), source=node)
                    edge.updateEdge(mousePos)
                    self.mousePressEdge = edge
                    self.addItem(edge)

                super().mousePressEvent(mouseEvent)

            else:

                super().mousePressEvent(mouseEvent)

                if self.mode is DiagramMode.Idle:

                    #############################################
                    # ITEM SELECTION
                    #################################

                    # See if we have some nodes selected in the scene: this is needed because itemOnTopOf
                    # will discard labels, so if we have a node whose label is overlapping the node shape,
                    # clicking on the label will make itemOnTopOf return the node item instead of the label.
                    selected = self.selectedNodes()
                    if selected:
                        # We have some nodes selected in the scene so we probably are going to do a
                        # move operation, prepare data for mouse move event => select a node that will act
                        # as mouse grabber to compute delta movements for each componenet in the selection.
                        self.mousePressNode = self.itemOnTopOf(mousePos, edges=False)
                        if self.mousePressNode:
                            self.mousePressNodePos = self.mousePressNode.pos()
                            self.mousePressPos = mousePos
                            self.mousePressData = {
                                'nodes': {
                                    node: {
                                        'anchors': {k: v for k, v in node.anchors.items()},
                                        'pos': node.pos(),
                                    } for node in selected},
                                'edges': {}
                            }

                            # Figure out if the nodes we are moving are sharing edges: if so, move the edge
                            # together with the nodes (which actually means moving the edge breakpoints).
                            for node in self.mousePressData['nodes']:
                                for edge in node.edges:
                                    if edge not in self.mousePressData['edges']:
                                        if edge.other(node).isSelected():
                                            self.mousePressData['edges'][edge] = edge.breakpoints[:]

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when then mouse is moved on the scene.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        mouseButtons = mouseEvent.buttons()
        mousePos = mouseEvent.scenePos()

        if mouseButtons & Qt.LeftButton:

            if self.mode is DiagramMode.InsertEdge:

                #############################################
                # EDGE INSERTION
                #################################

                if self.mousePressEdge:

                    mainwindow = self.project.parent()
                    statusBar = mainwindow.statusBar()
                    edge = self.mousePressEdge
                    edge.updateEdge(mousePos)

                    currentNode = self.itemOnTopOf(mousePos, edges=False, skip={edge.source})
                    previousNode = self.mouseOverNode

                    if previousNode:
                        previousNode.redraw(selected=False)

                    if currentNode:
                        self.mouseOverNode = currentNode
                        result = self.project.validator.validate(edge.source, edge, currentNode)
                        currentNode.redraw(selected=False, valid=result.valid)
                        if not result.valid:
                            statusBar.showMessage(result.message)
                        else:
                            statusBar.clearMessage()

                    else:
                        statusBar.clearMessage()
                        self.mouseOverNode = None
                        self.project.validator.clear()

            else:

                if self.mode is DiagramMode.Idle:
                    if self.mousePressNode:
                        self.setMode(DiagramMode.MoveNode)

                if self.mode is DiagramMode.MoveNode:

                    #############################################
                    # ITEM MOVEMENT
                    #################################

                    mainwindow = self.project.parent()
                    snapToGrid = mainwindow.actionSnapToGrid.isChecked()
                    point = self.mousePressNodePos + mousePos - self.mousePressPos
                    point = snap(point, Diagram.GridSize, snapToGrid)
                    delta = point - self.mousePressNodePos
                    edges = set()

                    # Update all the breakpoint positions.
                    for edge, breakpoints in self.mousePressData['edges'].items():
                        for i in range(len(breakpoints)):
                            edge.breakpoints[i] = breakpoints[i] + delta

                    # Move all the selected nodes.
                    for node, data in self.mousePressData['nodes'].items():
                        edges |= set(node.edges)
                        node.setPos(data['pos'] + delta)
                        for edge, pos in data['anchors'].items():
                            node.setAnchor(edge, pos + delta)

                    # Update edges.
                    for edge in edges:
                        edge.updateEdge()

        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the scene.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        mouseButton = mouseEvent.button()
        mousePos = mouseEvent.scenePos()

        if mouseButton == Qt.LeftButton:

            if self.mode is DiagramMode.InsertEdge:

                #############################################
                # EDGE INSERTION
                #################################

                if self.mousePressEdge:

                    edge = self.mousePressEdge
                    edge.source.redraw(selected=False)
                    currentNode = self.itemOnTopOf(mousePos, edges=False, skip={edge.source})
                    insertEdge = False

                    if currentNode:
                        currentNode.redraw(selected=False)
                        result = self.project.validator.validate(edge.source, edge, currentNode)
                        if result.valid:
                            edge.target = currentNode
                            insertEdge = True

                    # We temporarily remove the item from the diagram and we perform the
                    # insertion using the undo command that will also emit the sgnItemAdded
                    # signal hence all the widgets will be notified of the edge insertion.
                    # We do this because while creating the edge we need to display it so the
                    # user knows what is he connecting, but we don't want to truly insert
                    # it till it's necessary (when the mouse is released and the validator
                    # confirms that the generated expression is a valid graphol expression).
                    self.removeItem(edge)

                    if insertEdge:
                        self.undoStack.push(CommandEdgeAdd(self, edge))
                        edge.updateEdge()

                    self.clearSelection()
                    self.project.validator.clear()
                    self.mouseOverNode = None
                    self.mousePressEdge = None
                    mainwindow = self.project.parent()
                    statusBar = mainwindow.statusBar()
                    statusBar.clearMessage()

                    self.sgnActionCompleted.emit(edge, mouseEvent.modifiers())

            elif self.mode is DiagramMode.MoveNode:

                #############################################
                # ITEM MOVEMENT
                #################################

                data = {
                    'undo': self.mousePressData,
                    'redo': {
                        'nodes': {
                            node: {
                                'anchors': {k: v for k, v in node.anchors.items()},
                                'pos': node.pos(),
                            } for node in self.mousePressData['nodes']},
                        'edges': {x: x.breakpoints[:] for x in self.mousePressData['edges']}
                    }
                }

                self.undoStack.push(CommandNodeMove(self, data))
                self.setMode(DiagramMode.Idle)

        elif mouseButton == Qt.RightButton:

            if self.mode is not DiagramMode.SceneDrag:

                #############################################
                # CONTEXTUAL MENU
                #################################

                item = self.itemOnTopOf(mousePos)
                if item:
                    self.clearSelection()
                    item.setSelected(True)

                self.mousePressPos = mousePos
                mainwindow = self.project.parent()
                menu = mainwindow.menuFactory.create(mainwindow, self, item, mousePos)
                menu.exec_(mouseEvent.screenPos())

        super().mouseReleaseEvent(mouseEvent)

        self.mousePressPos = None
        self.mousePressNode = None
        self.mousePressNodePos = None
        self.mousePressData = None

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def onConnectionChanged(self, _, item):
        """
        Executed whenever a connection is created/removed.
        :type _: Diagram
        :type item: AbstractItem
        """
        if item.isEdge():
            for node in (item.source, item.target):
                if Identity.Neutral in node.Identities:
                    self.identify(node)

    #############################################
    #   INTERFACE
    #################################

    def edge(self, eid):
        """
        Returns the edge matching the given id or None if no edge is found.
        :type eid: str
        :rtype: AbstractEdge
        """
        return self.project.edge(self, eid)

    def edges(self):
        """
        Returns a collection with all the edges in the diagram.
        :rtype: set
        """
        return self.project.edges(self)

    def height(self):
        """
        Returns the height of the diagram.
        :rtype: int
        """
        return self.sceneRect().height()

    @staticmethod
    def identify(node):
        """
        Perform node identification.
        :type node: AbstractNode
        """
        predicate = lambda x: Identity.Neutral in x.Identities
        collection = bfs(source=node, filter_on_visit=predicate)
        generators = partition(predicate, collection)
        excluded = set()
        strong = set(generators[1])
        weak = set(generators[0])

        #############################################
        #   SPECIAL CASES
        #################################

        for node in weak:

            if node.type() is Item.EnumerationNode:

                # ENUMERATION:
                #
                #   - If it has INSTANCE as inputs => Identity is CONCEPT
                #   - If it has VALUE as inputs => Identity is VALUE-DOMAIN
                #
                # After establishing the identity for this node, we discard all the
                # nodes we used to compute such identity and also move the enumeration
                # node from the WEAK set to the STRONG set, so it will contribute to the
                # computation of the final identity for all the remaining WEAK nodes.

                f1 = lambda x: x.type() is Item.InputEdge
                f2 = lambda x: x.type() is Item.IndividualNode
                f3 = lambda x: Identity.Concept if x is Identity.Instance else Identity.ValueDomain

                individuals = node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)
                identities = {f3(x.identity) for x in individuals}
                computed = Identity.Neutral

                if identities:
                    computed = first(identities)
                    if len(identities) > 1:
                        computed = Identity.Unknown

                node.identity = computed

                if node.identity is not Identity.Neutral:
                    strong.add(node)

                for k in individuals:
                    strong.discard(k)

            elif node.type() is Item.RangeRestrictionNode:

                # RANGE RESTRICTION:
                #
                #   - If it has ATTRIBUTE|VALUE-DOMAIN as inputs => Identity is VALUE-DOMAIN
                #   - If it has ROLE|CONCEPT as inputs => Identity is CONCEPT
                #
                # After establishing the identity for this node, we discard all the
                # nodes we used to compute such identity and also moVe the range restriction
                # node from the WEAK set to the STRONG set, so it will contribute to the
                # computation of the final identity for all the remaining WEAK nodes.

                admissible = {Identity.Role, Identity.Attribute, Identity.Concept, Identity.ValueDomain}

                f1 = lambda x: x.type() is Item.InputEdge
                f2 = lambda x: x.type() in admissible and Identity.Neutral not in x.Identities
                f3 = lambda x: Identity.Concept if x in {Identity.Role, Identity.Concept} else Identity.ValueDomain

                collection = node.incomingNodes(filter_on_edges=f1, filter_on_nodes=f2)
                identities = {f3(x.identity) for x in collection}
                computed = Identity.Neutral

                if identities:
                    computed = first(identities)
                    if len(identities) > 1:
                        computed = Identity.Unknown

                node.identity = computed

                if node.identity is not Identity.Neutral:
                    strong.add(node)

                for k in collection:
                    strong.discard(k)

            elif node.type() is Item.PropertyAssertionNode:

                # PROPERTY ASSERTION:
                #
                #   - If it is targeting a ROLE using a Membership edge => Identity is ROLE INSTANCE
                #   - If it is targeting an ATTRIBUTE using a Membership edge => Identity is ATTRIBUTE INSTANCE
                #
                #   OR
                #
                #   - If it has 2 INSTANCE as inputs => Identity is ROLE INSTANCE
                #   - If it has 1 INSTANCE and 1 VALUE as inputs => Identity is ATTRIBUTE INSTANCE
                #
                # In both the cases, whether we establish or not an idendity for this node,
                # we exclude it from both the WEAK and the STRONG sets. This is due to the fact
                # that the PropertyAssertion node is used to perform assertions at ABox level
                # while every other node in the graph is used at TBox level. Additionally we
                # discard the inputs of the node from the STRONG set since they are either INSTANCE
                # or VALUE nodes since they are not needed to compute the final identity for
                # the remaining nodes in the WEAK set (see Enumeration node).

                f1 = lambda x: x.type() is Item.MembershipEdge
                f2 = lambda x: x.type() in {Item.RoleNode, Item.RoleInverseNode, Item.AttributeNode}
                f3 = lambda x: x.type() is Item.InputEdge
                f4 = lambda x: x.type() is Item.IndividualNode
                f5 = lambda x: Identity.RoleInstance if x is Identity.Role else Identity.AttributeInstance
                f6 = lambda x: x.identity is Identity.Value

                outgoing = node.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2)
                incoming = node.incomingNodes(filter_on_edges=f3, filter_on_nodes=f4)

                computed = Identity.Neutral

                # 1) USE MEMBERSHIP EDGE
                identities = {f5(x.identity) for x in outgoing}
                if identities:
                    computed = first(identities)
                    if len(identities) > 1:
                        computed = Identity.Unknown

                # 2) USE INPUT EDGES
                if computed is Identity.Neutral and len(incoming) >= 2:
                    computed = Identity.RoleInstance
                    if sum(map(f6, incoming)):
                        computed = Identity.AttributeInstance

                node.identity = computed

                excluded.add(node)

                for k in incoming:
                    strong.discard(k)

        #############################################
        #   FINAL COMPUTATION
        #################################

        computed = Identity.Neutral
        identities = {x.identity for x in strong}
        if identities:
            computed = first(identities)
            if len(identities) > 1:
                computed = Identity.Unknown

        for node in weak - strong - excluded:
            node.identity = computed

    def itemOnTopOf(self, point, nodes=True, edges=True, skip=None):
        """
        Returns the shape which is on top of the given point.
        :type point: QPointF
        :type nodes: bool
        :type edges: bool
        :type skip: iterable
        :rtype: Item
        """
        skip = skip or {}
        data = [x for x in self.items(point) if (nodes and x.isNode() or edges and x.isEdge()) and x not in skip]
        if data:
            return max(data, key=lambda x: x.zValue())
        return None

    def nodes(self):
        """
        Returns a collection with all the nodes in the diagram.
        :rtype: set
        """
        return self.project.nodes(self)

    def node(self, nid):
        """
        Returns the node matching the given id or None if no node is found.
        :type nid: str
        :rtype: AbstractNode
        """
        return self.project.node(self, nid)

    def propertyComposition(self, source, item):
        """
        Returns a collection of items to be added to the given source node to compose a property expression.
        :type source: AbstractNode
        :type item: Item
        :rtype: set
        """
        restriction = self.project.itemFactory.create(item)
        edge = self.project.itemFactory.create(Item.InputEdge, source=source, target=restriction)
        size = Diagram.GridSize

        offsets = (
            QPointF(snapF(+source.width() / 2 + 70, size), 0),
            QPointF(snapF(-source.width() / 2 - 70, size), 0),
            QPointF(0, snapF(-source.height() / 2 - 70, size)),
            QPointF(0, snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(+source.width() / 2 + 70, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(-source.width() / 2 - 70, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(+source.width() / 2 + 70, size), snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(-source.width() / 2 - 70, size), snapF(+source.height() / 2 + 70, size)),
        )

        pos = None
        num = sys.maxsize
        rad = QPointF(restriction.width() / 2, restriction.height() / 2)

        for o in offsets:
            count = len(self.items(QRectF(source.pos() + o - rad, source.pos() + o + rad)))
            if count < num:
                num = count
                pos = source.pos() + o

        restriction.setPos(pos)
        return {restriction, edge}

    def selectedEdges(self):
        """
        Returns the edges selected in the diagram.
        :rtype: list
        """
        return [x for x in super(Diagram, self).selectedItems() if x.isEdge()]

    def selectedItems(self):
        """
        Returns the items selected in the diagram.
        :rtype: list
        """
        return [x for x in super(Diagram, self).selectedItems() if x.isNode() or x.isEdge()]

    def selectedNodes(self):
        """
        Returns the nodes selected in the diagram.
        :rtype: list
        """
        return [x for x in super(Diagram, self).selectedItems() if x.isNode()]

    def setMode(self, mode, param=None):
        """
        Set the operational mode.
        :type mode: DiagramMode
        :type param: Item
        """
        if self.mode != mode or self.modeParam != param:
            self.mode = mode
            self.modeParam = param
            self.sgnModeChanged.emit(mode)

    def visibleRect(self, margin=0):
        """
        Returns a rectangle matching the area of visible items.
        :type margin: float
        :rtype: QRectF
        """
        bound = self.itemsBoundingRect()
        topLeft = QPointF(bound.left() - margin, bound.top() - margin)
        bottomRight = QPointF(bound.right() + margin, bound.bottom() + margin)
        return QRectF(topLeft, bottomRight)

    def width(self):
        """
        Returns the width of the diagram.
        :rtype: int
        """
        return self.sceneRect().width()