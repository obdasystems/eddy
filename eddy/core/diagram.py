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


from __future__ import annotations

from typing import (
    cast,
    Dict,
    Optional,
    Set,
    TYPE_CHECKING,
)

from PyQt5 import (
    QtCore,
    QtWidgets,
)

from eddy.core.clipboard import Clipboard
from eddy.core.commands.edges import CommandEdgeAdd
from eddy.core.commands.labels import CommandLabelMove
from eddy.core.commands.nodes import (
    CommandNodeAdd,
    CommandNodeMove,
)
from eddy.core.datatypes.graphol import (
    Identity,
    Item,
)
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.datatypes.qt import Font
from eddy.core.functions.graph import bfs
from eddy.core.functions.misc import (
    first,
    partition,
    snap,
)
from eddy.core.functions.signals import connect
from eddy.core.generators import GUID
from eddy.core.items.common import AbstractItem
from eddy.core.items.edges.common.base import AbstractEdge
from eddy.core.items.factory import ItemFactory
from eddy.core.items.nodes.common.base import (
    AbstractNode,
    PredicateNodeMixin,
)
from eddy.core.items.nodes.facet import FacetNode
from eddy.core.items.nodes.literal import LiteralNode
from eddy.core.output import getLogger

if TYPE_CHECKING:
    from eddy.core.project import Project
    from eddy.ui.session import Session

#############################################
#   GLOBALS
#################################

LOGGER = getLogger()


class Diagram(QtWidgets.QGraphicsScene):
    """
    Extension of QtWidgets.QGraphicsScene which implements a single Graphol diagram.
    Additionally to built-in signals, this class emits:

    * sgnItemAdded: whenever an element is added to the Diagram.
    * sgnItemInsertionCompleted: whenever an item 'MANUAL' insertion process is completed.
    * sgnItemRemoved: whenever an element is removed from the Diagram.
    * sgnModeChanged: whenever the Diagram operational mode (or its parameter) changes.
    * sgnUpdated: whenever the Diagram has been updated in any of its parts.
    """
    GridSize = 10
    KeyMoveFactor = 10
    MinSize = 2000
    MaxSize = 1000000
    MinFontSize = 8
    MaxFontSize = 40
    SelectionRadius = 4

    sgnItemAdded = QtCore.pyqtSignal(QtWidgets.QGraphicsScene, QtWidgets.QGraphicsItem)
    sgnItemInsertionCompleted = QtCore.pyqtSignal(QtWidgets.QGraphicsItem, int)
    sgnItemRemoved = QtCore.pyqtSignal(QtWidgets.QGraphicsScene, QtWidgets.QGraphicsItem)
    sgnModeChanged = QtCore.pyqtSignal(DiagramMode)
    sgnNodeIdentification = QtCore.pyqtSignal(QtWidgets.QGraphicsItem)
    sgnUpdated = QtCore.pyqtSignal()

    # noinspection PyUnresolvedReferences
    def __init__(self, name: str, parent: Project) -> None:
        """
        Initialize the diagram.
        """
        super().__init__(parent)

        self.factory = ItemFactory(self)
        self.guid = GUID(self)
        self.mode = DiagramMode.Idle
        self.modeParam = Item.Undefined
        self.name = name
        self.pasteX = Clipboard.PasteOffsetX
        self.pasteY = Clipboard.PasteOffsetY

        self.mo_Node = None
        self.mp_Data = None
        self.mp_Edge = None
        self.mp_Label = None
        self.mp_LabelPos = None
        self.mp_Node = None
        self.mp_NodePos = None
        self.mp_Pos = None

        settings = QtCore.QSettings()
        self.setFont(
            Font(
                font=self.font(),
                pixelSize=settings.value('diagram/fontsize', self.font().pixelSize(), int)
            )
        )

        connect(self.sgnItemAdded, self.onItemAdded)
        connect(self.sgnItemRemoved, self.onItemRemoved)
        connect(self.sgnNodeIdentification, self.doNodeIdentification)

    #############################################
    #   FACTORY
    #################################

    # noinspection PyUnresolvedReferences
    @classmethod
    def create(cls, name: str, size: int, project: Project) -> Diagram:
        """
        Build and returns a new Diagram instance, using the given parameters.
        """
        diagram = Diagram(name, project)
        diagram.setBackgroundBrush(QtCore.Qt.white)
        diagram.setSceneRect(QtCore.QRectF(-size / 2, -size / 2, size, size))
        diagram.setItemIndexMethod(Diagram.BspTreeIndex)
        return diagram

    #############################################
    #   PROPERTIES
    #################################

    # noinspection PyUnresolvedReferences
    @property
    def project(self) -> Project:
        """
        Returns the project this diagram belongs to.
        """
        return cast('Project', self.parent())

    # noinspection PyUnresolvedReferences
    @property
    def session(self) -> Session:
        """
        Returns the session this diagram belongs to.
        """
        return cast('Session', self.project.parent())

    #############################################
    #   EVENTS
    #################################

    def event(self, event: QtCore.QEvent) -> bool:
        """
        Executed when an event happens in the scene, before any specialized handler executes.
        """
        # This event is sent to itself by the scene every time the scene font property changes,
        # either directly (via setFont()) or indirectly (via QApplication::setFont()).
        # Here we cascade the event to all top-level widget items in the scene to have
        # them notified about the font change.
        if event.type() == QtCore.QEvent.FontChange:
            # CASCADE THE EVENT TO ALL TOP LEVEL ITEMS IN THE SCENE
            for item in self.items():
                self.sendEvent(item, event)
        return super().event(event)

    def dragEnterEvent(self, dragEvent: QtWidgets.QGraphicsSceneDragDropEvent) -> None:
        """
        Executed when a dragged element enters the scene area.
        """
        super().dragEnterEvent(dragEvent)
        if dragEvent.mimeData().hasFormat('text/plain'):
            dragEvent.setDropAction(QtCore.Qt.CopyAction)
            dragEvent.accept()
        else:
            dragEvent.ignore()

    def dragMoveEvent(self, dragEvent: QtWidgets.QGraphicsSceneDragDropEvent) -> None:
        """
        Executed when an element is dragged over the scene.
        """
        super().dragMoveEvent(dragEvent)
        if dragEvent.mimeData().hasFormat('text/plain'):
            dragEvent.setDropAction(QtCore.Qt.CopyAction)
            dragEvent.accept()
        else:
            dragEvent.ignore()

    # noinspection PyTypeChecker
    def dropEvent(self, dropEvent: QtWidgets.QGraphicsSceneDragDropEvent) -> None:
        """
        Executed when a dragged element is dropped on the diagram.
        """
        super().dropEvent(dropEvent)
        if dropEvent.mimeData().hasFormat('text/plain') and Item.valueOf(dropEvent.mimeData().text()):
            snapToGrid = self.session.action('toggle_grid').isChecked()
            node = self.factory.create(Item.valueOf(dropEvent.mimeData().text()))
            node.setPos(snap(dropEvent.scenePos(), Diagram.GridSize, snapToGrid))
            data = dropEvent.mimeData().data(dropEvent.mimeData().text())
            if int(dropEvent.mimeData().text()) in {Item.ConceptNode, Item.AttributeNode,
                                                    Item.RoleNode, Item.IndividualNode,
                                                    Item.ValueDomainNode, Item.LiteralNode,
                                                    Item.FacetNode}:
                if not data:
                    # For new nodes (e.g. drag and drop from palette)
                    if isinstance(node, FacetNode):
                        self.session.doOpenConstrainingFacetBuilder(node)
                    elif isinstance(node, PredicateNodeMixin):
                        self.session.doOpenIRIBuilder(node)
                    elif isinstance(node, LiteralNode):
                        self.session.doOpenLiteralBuilder(node)
                else:
                    # Copy of existing element (e.g. drag and drop from ontology explorer)
                    data_str = str(data, encoding='utf-8')
                    iri = self.project.getIRI(data_str)
                    node.iri = iri
                    self.session.undostack.push(CommandNodeAdd(self, node))
                    node.doUpdateNodeLabel()
            else:
                self.session.undostack.push(CommandNodeAdd(self, node))
            self.sgnItemInsertionCompleted.emit(node, dropEvent.modifiers())
            dropEvent.setDropAction(QtCore.Qt.CopyAction)
            dropEvent.accept()
        else:
            dropEvent.ignore()

    # noinspection PyTypeChecker
    def mousePressEvent(self, mouseEvent: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """
        Executed when a mouse button is clicked on the scene.
        """
        mouseModifiers = mouseEvent.modifiers()
        mouseButtons = mouseEvent.buttons()
        mousePos = mouseEvent.scenePos()

        if mouseButtons & QtCore.Qt.LeftButton:

            if self.mode is DiagramMode.NodeAdd:

                #############################################
                # NODE INSERTION
                #################################

                snapToGrid = self.session.action('toggle_grid').isChecked()
                node = self.factory.create(Item.valueOf(self.modeParam))
                node.setPos(snap(mousePos, Diagram.GridSize, snapToGrid))
                if isinstance(node, PredicateNodeMixin):
                    self.session.doOpenIRIBuilder(node)
                elif isinstance(node, FacetNode):
                    self.session.doOpenConstrainingFacetBuilder(node)
                elif isinstance(node, LiteralNode):
                    self.session.doOpenLiteralBuilder(node)
                else:
                    self.session.undostack.push(CommandNodeAdd(self, node))
                self.sgnItemInsertionCompleted.emit(node, mouseEvent.modifiers())

            elif self.mode is DiagramMode.EdgeAdd:

                #############################################
                # EDGE INSERTION
                #################################

                node = first(self.items(mousePos, edges=False))
                if node:
                    edge = self.factory.create(Item.valueOf(self.modeParam), source=node)
                    edge.updateEdge(target=mousePos)
                    self.mp_Edge = edge
                    self.addItem(edge)

            else:

                # Execute super at first since this may change the diagram
                # mode: some actions are directly handle by graphics items
                # (i.e: edge breakpoint move, edge anchor move, node shape
                # resize) and we need to check whether any of them is being
                # performed before handling the even locally.
                super().mousePressEvent(mouseEvent)

                if self.mode is DiagramMode.Idle:

                    if mouseModifiers & QtCore.Qt.ShiftModifier:

                        #############################################
                        # LABEL MOVE
                        #################################

                        item = first(self.items(mousePos, nodes=False, edges=False, labels=True))
                        if item and item.isMovable():
                            self.clearSelection()
                            self.mp_Label = item
                            self.mp_LabelPos = item.pos()
                            self.mp_Pos = mousePos
                            self.setMode(DiagramMode.LabelMove)

                    else:

                        #############################################
                        # ITEM SELECTION
                        #################################

                        item = first(self.items(mousePos, labels=True))
                        if item:

                            if item.isLabel():
                                # If we are hitting a label, check whether the label
                                # is overlapping it's parent item and such item is
                                # also intersecting the current mouse position: if so,
                                # use the parent item as placeholder for the selection.
                                parent = item.parentItem()
                                items = self.items(mousePos)
                                item = parent if parent in items else None

                            if item:

                                if mouseModifiers & QtCore.Qt.ControlModifier:
                                    # CTRL => support item multi selection.
                                    item.setSelected(not item.isSelected())
                                else:
                                    if self.selectedItems():
                                        # Some elements have been already selected in the
                                        # diagram, during a previous mouse press event.
                                        if not item.isSelected():
                                            # There are some items selected but we clicked
                                            # on a node which is not currently selected, so
                                            # make this node the only selected one.
                                            self.clearSelection()
                                            item.setSelected(True)
                                    else:
                                        # No item (nodes or edges) is selected and we just
                                        # clicked on one so make sure to select this item and
                                        # because selectedItems() filters out item Label's,
                                        # clear out the selection on the diagram.
                                        self.clearSelection()
                                        item.setSelected(True)

                                # If we have some nodes selected we need to prepare data for a
                                # possible item move operation: we need to make sure to retrieve
                                # the node below the mouse cursor that will act as as mouse grabber
                                # to compute delta  movements for each component in the selection.
                                selected = self.selectedNodes()
                                if selected:
                                    self.mp_Node = first(self.items(mousePos, edges=False))
                                    if self.mp_Node:
                                        self.mp_NodePos = self.mp_Node.pos()
                                        self.mp_Pos = mousePos
                                        self.mp_Data = self.setupMove(selected)

    def mouseMoveEvent(self, mouseEvent: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """
        Executed when then mouse is moved on the scene.
        """
        mouseButtons = mouseEvent.buttons()
        mousePos = mouseEvent.scenePos()

        if mouseButtons & QtCore.Qt.LeftButton:

            if self.mode is DiagramMode.EdgeAdd:

                #############################################
                # EDGE INSERTION
                #################################

                if self.isEdgeAdd():

                    statusBar = self.session.statusBar()
                    edge = self.mp_Edge
                    edge.updateEdge(target=mousePos)

                    previousNode = self.mo_Node
                    if previousNode:
                        previousNode.updateNode(selected=False)

                    currentNode = first(self.items(mousePos, edges=False, skip={edge.source}))
                    if currentNode:
                        self.mo_Node = currentNode
                        pvr = self.project.profile.checkEdge(edge.source, edge, currentNode)
                        currentNode.updateNode(selected=False, valid=pvr.isValid())
                        if not pvr.isValid():
                            statusBar.showMessage(pvr.message())
                        else:
                            statusBar.clearMessage()
                    else:
                        statusBar.clearMessage()
                        self.mo_Node = None
                        self.project.profile.reset()

            elif self.mode is DiagramMode.LabelMove:

                #############################################
                # LABEL MOVE
                #################################

                if self.isLabelMove():

                    snapToGrid = self.session.action('toggle_grid').isChecked()
                    point = self.mp_LabelPos + mousePos - self.mp_Pos
                    point = snap(point, Diagram.GridSize / 2, snapToGrid)
                    delta = point - self.mp_LabelPos
                    self.mp_Label.setPos(self.mp_LabelPos + delta)

            else:

                if self.mode is DiagramMode.Idle:
                    if self.mp_Node:
                        self.setMode(DiagramMode.NodeMove)

                if self.mode is DiagramMode.NodeMove:

                    #############################################
                    # ITEM MOVEMENT
                    #################################

                    if self.isNodeMove():

                        snapToGrid = self.session.action('toggle_grid').isChecked()
                        point = self.mp_NodePos + mousePos - self.mp_Pos
                        point = snap(point, Diagram.GridSize, snapToGrid)
                        delta = point - self.mp_NodePos
                        edges = set()

                        for edge, breakpoints in self.mp_Data['edges'].items():
                            for i in range(len(breakpoints)):
                                edge.breakpoints[i] = breakpoints[i] + delta

                        for node, data in self.mp_Data['nodes'].items():
                            edges |= set(node.edges)
                            node.setPos(data['pos'] + delta)
                            for edge, pos in data['anchors'].items():
                                node.setAnchor(edge, pos + delta)

                        for edge in edges:
                            edge.updateEdge()

        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """
        Executed when the mouse is released from the scene.
        """
        mouseModifiers = mouseEvent.modifiers()
        mouseButton = mouseEvent.button()
        mousePos = mouseEvent.scenePos()

        if mouseButton == QtCore.Qt.LeftButton:

            if self.mode is DiagramMode.EdgeAdd:

                #############################################
                # EDGE INSERTION
                #################################

                if self.isEdgeAdd():

                    edge = self.mp_Edge
                    edge.source.updateNode(selected=False)
                    currentNode = first(self.items(mousePos, edges=False, skip={edge.source}))
                    insertEdge = False

                    if currentNode:
                        currentNode.updateNode(selected=False)
                        pvr = self.project.profile.checkEdge(edge.source, edge, currentNode)
                        if pvr.isValid():
                            edge.target = currentNode
                            insertEdge = True

                    # We temporarily remove the item from the diagram and we perform the
                    # insertion using the undo command that will also emit the sgnItemAdded
                    # signal hence all the widgets will be notified of the edge insertion.
                    # We do this because while creating the edge we need to display it so the
                    # user knows what he is connecting, but we don't want to truly insert
                    # it till it's necessary (when the mouse is released and the validation
                    # confirms that the generated expression is a valid graphol expression).
                    self.removeItem(edge)

                    if insertEdge:
                        self.session.undostack.push(CommandEdgeAdd(self, edge))
                        edge.updateEdge()

                    self.clearSelection()
                    self.project.profile.reset()
                    statusBar = self.session.statusBar()
                    statusBar.clearMessage()

                    self.sgnItemInsertionCompleted.emit(edge, mouseModifiers)

            elif self.mode is DiagramMode.LabelMove:

                #############################################
                # LABEL MOVE
                #################################

                if self.isLabelMove():
                    pos = self.mp_Label.pos()
                    if self.mp_LabelPos != pos:
                        item = self.mp_Label.parentItem()
                        command = CommandLabelMove(self, item, self.mp_LabelPos, pos)
                        self.session.undostack.push(command)
                    self.setMode(DiagramMode.Idle)

            elif self.mode is DiagramMode.NodeMove:

                #############################################
                # ITEM MOVEMENT
                #################################

                if self.isNodeMove():
                    pos = self.mp_Node.pos()
                    if self.mp_NodePos != pos:
                        moveData = self.completeMove(self.mp_Data)
                        self.session.undostack.push(CommandNodeMove(self, self.mp_Data, moveData))
                    self.setMode(DiagramMode.Idle)

        elif mouseButton == QtCore.Qt.RightButton:

            if self.mode is not DiagramMode.SceneDrag:

                #############################################
                # CONTEXTUAL MENU
                #################################

                item = first(self.items(mousePos))
                if not item:
                    self.clearSelection()
                    items = []
                else:
                    items = self.selectedItems()
                    if item not in items:
                        self.clearSelection()
                        item.setSelected(True)
                        items = [item]

                self.mp_Pos = mousePos
                menu = self.session.mf.create(self, items, mousePos)
                menu.exec_(mouseEvent.screenPos())

        super().mouseReleaseEvent(mouseEvent)

        self.mo_Node = None
        self.mp_Data = None
        self.mp_Edge = None
        self.mp_Label = None
        self.mp_LabelPos = None
        self.mp_Node = None
        self.mp_NodePos = None
        self.mp_Pos = None

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(QtWidgets.QGraphicsItem)
    def doNodeIdentification(self, node: AbstractNode) -> None:
        """
        Perform node identification.
        """
        if Identity.Neutral in node.identities():

            func = lambda x: Identity.Neutral in x.identities()
            collection = bfs(source=node, filter_on_visit=func)
            generators = partition(func, collection)
            excluded = set()
            strong = set(generators[1])
            weak = set(generators[0])

            for node in weak:
                identification = node.identify()
                if identification:
                    strong = set.union(strong, identification[0])
                    strong = set.difference(strong, identification[1])
                    excluded = set.union(excluded, identification[2])

            computed = Identity.Neutral
            identities = set(x.identity() for x in strong)
            if identities:
                computed = first(identities)
                if len(identities) > 1:
                    computed = Identity.Unknown

            for node in weak - strong - excluded:
                node.setIdentity(computed)

    @QtCore.pyqtSlot(QtWidgets.QGraphicsScene, QtWidgets.QGraphicsItem)
    def onItemAdded(self, _: Diagram, item: AbstractItem) -> None:
        """
        Executed whenever a connection is created/removed.
        """
        # Send a font change event to the item to update its font
        self.sendEvent(item, QtCore.QEvent(QtCore.QEvent.FontChange))
        if item.isEdge():
            # Execute the node identification procedure only if one of the
            # endpoints we are connecting is currently identified as NEUTRAL.
            if (item.source.identity() is Identity.Neutral) ^ (item.target.identity() is Identity.Neutral):
                for node in (item.source, item.target):
                    self.sgnNodeIdentification.emit(node)

    @QtCore.pyqtSlot(QtWidgets.QGraphicsScene, QtWidgets.QGraphicsItem)
    def onItemRemoved(self, _: Diagram, item: AbstractItem) -> None:
        """
        Executed whenever a connection is created/removed.
        """
        if item.isEdge():
            # When an edge is removed we may be in the case where
            # the ontology is split into 2 subgraphs, hence we need
            # to run the identification procedure on the 2 subgraphs.
            for node in (item.source, item.target):
                self.sgnNodeIdentification.emit(node)

    #############################################
    #   INTERFACE
    #################################

    def addItem(self, item: AbstractItem) -> None:
        """
        Add an item to the Diagram (will redraw the item to reflect its status).
        """
        super().addItem(item)
        if item.isNode():
            if item.isPredicate():
                item.connectSignals()
            item.updateNode()

    @staticmethod
    def completeMove(
        moveData: Dict,
        offset: QtCore.QPointF = QtCore.QPointF(0, 0)
    ) -> Dict:
        """
        Complete item movement, given initialized data for a collection of selected nodes.
        """
        return {
            'nodes': {
                node: {
                    'anchors': {k: v + offset for k, v in node.anchors.items()},
                    'pos': node.pos() + offset,
                } for node in moveData['nodes']},
            'edges': {x: [p + offset for p in x.breakpoints[:]] for x in moveData['edges']}
        }

    def edge(self, eid: str) -> Optional[AbstractEdge]:
        """
        Returns the edge matching the given id or None if no edge is found.
        """
        return self.project.edge(self, eid)

    def edges(self) -> Set[AbstractEdge]:
        """
        Returns a collection with all the edges in the diagram.
        """
        return self.project.edges(self)

    def isEdgeAdd(self) ->  bool:
        """
        Returns `True` if an edge insertion is currently in progress, `False` otherwise.
        """
        return self.mode is DiagramMode.EdgeAdd and self.mp_Edge is not None

    def isLabelMove(self) -> bool:
        """
        Returns `True` if a label is currently being moved, `False` otherwise.
        """
        return self.mode is DiagramMode.LabelMove and \
           self.mp_Label is not None and \
           self.mp_LabelPos is not None and \
           self.mp_Pos is not None

    def isNodeMove(self) -> bool:
        """
        Returns `True` if a node(s) is currently being moved, `False` otherwise.
        """
        return self.mode is DiagramMode.NodeMove and \
           self.mp_Data is not None and \
           self.mp_Node is not None and \
           self.mp_NodePos is not None and \
           self.mp_Pos is not None

    def isEmpty(self) -> bool:
        """
        Returns `True` if this diagram contains no element, `False` otherwise.
        """
        return len(self.project.items(self)) == 0

    def items(self, mixed=None, mode=QtCore.Qt.IntersectsItemShape, **kwargs):
        """
        Returns a collection of items ordered from TOP to BOTTOM.
        If no argument is supplied, an unordered list containing all the elements in the diagram is returned.
        """
        if mixed is None:
            items = super().items()
        elif isinstance(mixed, QtCore.QPointF):
            x = mixed.x() - (Diagram.SelectionRadius / 2)
            y = mixed.y() - (Diagram.SelectionRadius / 2)
            w = Diagram.SelectionRadius
            h = Diagram.SelectionRadius
            items = super().items(QtCore.QRectF(x, y, w, h), mode)
        else:
            items = super().items(mixed, mode)
        return sorted([
            x for x in items
                if (kwargs.get('nodes', True) and x.isNode() or
                    kwargs.get('edges', True) and x.isEdge() or
                    kwargs.get('labels', False) and x.isLabel()) and
                    x not in kwargs.get('skip', set())
        ], key=lambda i: i.zValue(), reverse=True)

    def nodes(self) -> Set[AbstractNode]:
        """
        Returns a collection with all the nodes in the diagram.
        """
        return self.project.nodes(self)

    def node(self, nid: str) -> Optional[AbstractNode]:
        """
        Returns the node matching the given id or None if no node is found.
        """
        return self.project.node(self, nid)

    def selectedEdges(self, filter_on_edges=lambda x: True):
        """
        Returns the edges selected in the diagram.
        :type filter_on_edges: callable
        :rtype: list
        """
        return [x for x in super().selectedItems() if x.isEdge() and filter_on_edges(x)]

    def selectedItems(self, filter_on_items=lambda x: True):
        """
        Returns the items selected in the diagram.
        :type filter_on_items: callable
        :rtype: list
        """
        return [x for x in super().selectedItems() if (x.isNode() or x.isEdge()) and filter_on_items(x)]

    def selectedNodes(self, filter_on_nodes=lambda x: True):
        """
        Returns the nodes selected in the diagram.
        :type filter_on_nodes: callable
        :rtype: list
        """
        return [x for x in super().selectedItems() if x.isNode() and filter_on_nodes(x)]

    def setMode(self, mode: DiagramMode, param: Item = None) -> None:
        """
        Set the operational mode.
        """
        if self.mode != mode or self.modeParam != param:
            #LOGGER.debug('Diagram mode changed: mode=%s, param=%s', mode, param)
            self.mode = mode
            self.modeParam = param
            self.sgnModeChanged.emit(mode)

    @staticmethod
    def setupMove(selected):
        """
        Compute necessary data to initialize item movement, given a collection of selected nodes.
        :type selected: T <= list | tuple
        :rtype: dict
        """
        # Initialize movement data considering only
        # nodes which are involved in the selection.
        moveData = {
            'nodes': {
                node: {
                    'anchors': {k: v for k, v in node.anchors.items()},
                    'pos': node.pos(),
                } for node in selected},
            'edges': {}
        }
        # Figure out if the nodes we are moving are sharing edges:
        # if that's the case, move the edge together with the nodes
        # (which actually means moving the edge breakpoints).
        for node in moveData['nodes']:
            for edge in node.edges:
                if edge not in moveData['edges']:
                    if edge.other(node).isSelected():
                        moveData['edges'][edge] = edge.breakpoints[:]
        return moveData

    def visibleRect(self, margin: float = 0) -> QtCore.QRectF:
        """
        Returns a rectangle matching the area of visible items.
        """
        items = self.items()
        if items:
            x = set()
            y = set()
            for item in items:
                b = item.mapRectToScene(item.boundingRect())
                x.update({b.left(), b.right()})
                y.update({b.top(), b.bottom()})
            return QtCore.QRectF(
                QtCore.QPointF(min(x) - margin, min(y) - margin),
                QtCore.QPointF(max(x) + margin, max(y) + margin)
            )
        return QtCore.QRectF()

    def __str__(self):
        return 'Diagram {}'.format(self.name)


class DiagramMalformedError(RuntimeError):
    """
    Raised whenever a given diagram is detected as malformed.
    This is not meant to be used as Syntax Error, but more to
    detect malformation problems like operator nodes with no input, etc.
    """
    def __init__(self, item, *args, **kwargs):
        """
        Initialize the exception.
        :type item: AbstractItem
        :type args: iterable
        :type kwargs: dict
        """
        super().__init__(*args, **kwargs)
        self.item = item


class DiagramNotFoundError(RuntimeError):
    """
    Raised whenever we are not able to find a diagram given its path.
    """
    pass


class DiagramNotValidError(RuntimeError):
    """
    Raised whenever a diagram appear to have an invalid structure.
    """
    pass


class DiagramParseError(RuntimeError):
    """
    Raised whenever it's not possible parse a Diagram out of a document.
    """
    pass
