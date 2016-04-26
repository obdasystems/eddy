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


from abc import ABCMeta, abstractmethod

from PyQt5.QtCore import QPointF, QLineF, Qt, QRectF
from PyQt5.QtGui import QColor, QPen, QBrush, QPolygonF
from PyQt5.QtWidgets import QGraphicsItem

from eddy.core.commands.nodes import CommandNodeRezize
from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.items.common import AbstractItem


class AbstractNode(AbstractItem):
    """
    Base class for all the diagram nodes.
    """
    __metaclass__ = ABCMeta

    Identities = {}
    Prefix = 'n'

    def __init__(self, **kwargs):
        """
        Initialize the node.
        """
        super().__init__(**kwargs)

        self.anchors = dict()
        self.edges = set()

        self.backgroundBrush = QBrush(Qt.NoBrush)
        self.backgroundPen = QPen(Qt.NoPen)
        self.background = None
        self.selection = None
        self.polygon = None

        self.setAcceptHoverEvents(True)
        self.setCacheMode(AbstractItem.DeviceCoordinateCache)
        self.setFlag(AbstractItem.ItemIsSelectable, True) # TODO: remove

    #############################################
    #   PROPERTIES
    #################################

    @property
    @abstractmethod
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        pass

    @identity.setter
    @abstractmethod
    def identity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

    #############################################
    #   INTERFACE
    #################################

    def addEdge(self, edge):
        """
        Add the given edge to the current node.
        :type edge: AbstractEdge
        """
        self.edges.add(edge)

    def adjacentNodes(self, filter_on_edges=None, filter_on_nodes=None):
        """
        Returns the set of adjacent nodes.
        :type filter_on_edges: callable
        :type filter_on_nodes: callable
        :rtype: list
        """
        f0 = lambda x: True
        f1 = filter_on_edges or f0
        f2 = filter_on_nodes or f0
        return [x for x in [e.other(self) for e in self.edges if f1(e)] if f2(x)]

    def anchor(self, edge):
        """
        Returns the anchor point of the given edge in scene coordinates.
        :type edge: AbstractEdge
        :rtype: QPointF
        """
        try:
            return self.anchors[edge]
        except KeyError:
            self.anchors[edge] = self.mapToScene(self.center())
            return self.anchors[edge]

    def center(self):
        """
        Returns the point at the center of the shape in item's coordinate.
        :rtype: QPointF
        """
        return self.boundingRect().center()

    @abstractmethod
    def copy(self, project):
        """
        Create a copy of the current item.
        :type project: Project
        """
        pass

    @staticmethod
    @abstractmethod
    def createBackground(width, height):
        """
        Returns the initialized background polygon according to the given width/height.
        :type width: int
        :type height: int
        :rtype: T <= QRectF | QPolygonF
        """
        pass

    @staticmethod
    @abstractmethod
    def createPolygon(width, height):
        """
        Returns the initialized polygon according to the given width/height.
        :type width: int
        :type height: int
        :rtype: T <= QRectF | QPolygonF
        """
        pass

    @staticmethod
    def createSelection(width, height):
        """
        Returns the initialized selection polygon according to the given width/height.
        :type width: int
        :type height: int
        :rtype: QRectF
        """
        return QRectF(-width / 2, -height / 2, width, height)

    @abstractmethod
    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        pass

    @classmethod
    @abstractmethod
    def image(cls, **kwargs):
        """
        Returns a snapshot of this item suitable for the palette.
        :rtype: QPixmap
        """
        pass

    def incomingNodes(self, filter_on_edges=None, filter_on_nodes=None):
        """
        Returns the set of incoming nodes.
        :type filter_on_edges: callable
        :type filter_on_nodes: callable
        :rtype: list
        """
        f0 = lambda x: True
        f1 = filter_on_edges or f0
        f2 = filter_on_nodes or f0
        return [x for x in [e.other(self) for e in self.edges \
                    if (e.target is self or e.type() is Item.InclusionEdge and e.complete) \
                        and f1(e)] if f2(x)]

    def intersection(self, line):
        """
        Returns the intersection of the shape with the given line (in scene coordinates).
        :type line: QLineF
        :rtype: QPointF
        """
        intersection = QPointF()
        path = self.painterPath()
        polygon = self.mapToScene(path.toFillPolygon(self.transform()))
        for i in range(0, polygon.size() - 1):
            polyline = QLineF(polygon[i], polygon[i + 1])
            if polyline.intersect(line, intersection) == QLineF.BoundedIntersection:
                return intersection
        return None

    def isConstructor(self):
        """
        Returns True if this node is a contructor node, False otherwise.
        :rtype: bool
        """
        return Item.DomainRestrictionNode <= self.type() <= Item.PropertyAssertionNode

    def isPredicate(self):
        """
        Returns True if this node is a predicate node, False otherwise.
        :rtype: bool
        """
        return Item.ConceptNode <= self.type() <= Item.ValueRestrictionNode

    def moveBy(self, x, y):
        """
        Move the node by the given deltas.
        :type x: T <= float | int
        :type y: T <= float | int
        """
        move = QPointF(x, y)
        self.setPos(self.pos() + move)
        self.anchors = {edge: pos + move for edge, pos in self.anchors.items()}

    def outgoingNodes(self, filter_on_edges=None, filter_on_nodes=None):
        """
        Returns the set of outgoing nodes.
        :type filter_on_edges: callable
        :type filter_on_nodes: callable
        :rtype: list
        """
        f0 = lambda x: True
        f1 = filter_on_edges or f0
        f2 = filter_on_nodes or f0
        return [x for x in [e.other(self) for e in self.edges \
                    if (e.source is self or e.type() is Item.InclusionEdge and e.complete) \
                        and f1(e)] if f2(x)]

    @abstractmethod
    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        pass

    def pos(self):
        """
        Returns the position of this node in scene coordinates.
        :rtype: QPointF
        """
        return self.mapToScene(self.center())

    def removeEdge(self, edge):
        """
        Remove the given edge from the current node.
        :type edge: AbstractEdge
        """
        self.edges.discard(edge)

    def setAnchor(self, edge, pos):
        """
        Set the given position as anchor for the given edge.
        :type edge: AbstractEdge
        :type pos: QPointF
        """
        self.anchors[edge] = pos

    def setPos(self, *__args):
        """
        Set the item position.
        QGraphicsItem.setPos(QPointF)
        QGraphicsItem.setPos(float, float)
        """
        if len(__args) == 1:
            pos = __args[0]
        elif len(__args) == 2:
            pos = QPointF(__args[0], __args[1])
        else:
            raise TypeError('too many arguments; expected {}, got {}'.format(2, len(__args)))
        super().setPos(pos + super().pos() - self.pos())

    def redraw(self, selected=None, valid=None, **kwargs):
        """
        Schedule this item for redrawing.
        :type selected: bool
        :type valid: bool
        """
        brush0 = QBrush(Qt.NoBrush)
        brush1 = QBrush(QColor(43, 173, 63, 160))
        brush2 = QBrush(QColor(179, 12, 12, 160))

        pen0 = QPen(Qt.NoPen)
        pen1 = QPen(QColor(0, 0, 0), 1.0, Qt.DashLine)

        backgroundBrush = brush0
        selectionPen = pen0

        # ITEM SELECTION
        if selected:
            selectionPen = pen1
        self.selectionPen = selectionPen

        # SYNTAX VALIDATION
        if valid is not None:
            backgroundBrush = brush1 if valid else brush2
        self.backgroundBrush = backgroundBrush

        # FORCE CACHE REGENERATION
        self.setCacheMode(QGraphicsItem.NoCache)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

        # SCHEDULE REPAINT
        self.update(self.boundingRect())

    @abstractmethod
    def setText(self, text):
        """
        Set the label text.
        :type text: str
        """
        pass

    @abstractmethod
    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        pass

    @abstractmethod
    def text(self):
        """
        Returns the label text.
        :rtype: str
        """
        pass

    @abstractmethod
    def textPos(self):
        """
        Returns the current label position.
        :rtype: QPointF
        """
        pass

    def updateEdges(self):
        """
        Update all the edges attached to the node.
        """
        for edge in self.edges:
            edge.updateEdge()

    @abstractmethod
    def updateTextPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        pass

    @abstractmethod
    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        pass

    #############################################
    #   EVENTS
    #################################

    def itemChange(self, change, value):
        """
        Executed whenever the item change state.
        :type change: int
        :type value: QVariant
        :rtype: QVariant
        """
        if change == AbstractNode.ItemSelectedHasChanged:
            self.redraw(selected=value)
        return super(AbstractNode, self).itemChange(change, value)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the item.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        # Allow node selection only if we are in DiagramMode.Idle state: resizable
        # nodes may have changed the diagram mode to DiagramMode.ResizeNode if a resize
        # handle is selected, thus we don't need to perform (multi)selection.
        if self.diagram.mode is DiagramMode.Idle:
            # Here is a slightly modified version of the default behavior
            # which improves the interaction with multiple selected nodes.
            if mouseEvent.modifiers() & Qt.ControlModifier:
                # If the control modifier is being held switch the selection flag.
                self.setSelected(not self.isSelected())
            else:
                if self.diagram.selectedItems():
                    # Some elements are already selected (previoust mouse press event).
                    if not self.isSelected():
                        # There are some items selected but we clicked on a node
                        # which is not currently selected, so select only this one.
                        self.diagram.clearSelection()
                        self.setSelected(True)
                else:
                    # No node is selected and we just clicked on one so select it
                    # since we filter out the Label, clear the diagram selection in
                    # any case to avoid strange bugs.
                    self.diagram.clearSelection()
                    self.setSelected(True)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is being moved over the item while being pressed (EXCLUDED).
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        pass

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the item (EXCLUDED).
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        pass


class AbstractResizableNode(AbstractNode):
    """
    Base class for all the diagram resizable nodes.
    """
    __metaclass__ = ABCMeta

    HandleTL = 0
    HandleTM = 1
    HandleTR = 2
    HandleML = 3
    HandleMR = 4
    HandleBL = 5
    HandleBM = 6
    HandleBR = 7

    HandleNum = 8
    HandleMove = -4
    HandleSize = 8

    HandleCursors = [
        Qt.SizeFDiagCursor,
        Qt.SizeVerCursor,
        Qt.SizeBDiagCursor,
        Qt.SizeHorCursor,
        Qt.SizeHorCursor,
        Qt.SizeBDiagCursor,
        Qt.SizeVerCursor,
        Qt.SizeFDiagCursor,
    ]

    def __init__(self, **kwargs):
        """
        Initialize the node.
        """
        super().__init__(**kwargs)

        self.handleBound = [QRectF()] * self.HandleNum
        self.handleBrush = [QBrush(Qt.NoBrush)] * self.HandleNum
        self.handlePen = [QPen(Qt.NoPen)] * self.HandleNum

        self.mousePressBackground = None
        self.mousePressSelection = None
        self.mousePressPolygon = None
        self.mousePressBound = None
        self.mousePressData = None
        self.mousePressHandle = None
        self.mousePressPos = None

    #############################################
    #   PROPERTIES
    #################################

    @property
    @abstractmethod
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        pass

    @identity.setter
    @abstractmethod
    def identity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

    #############################################
    #   INTERFACE
    #################################

    def cursorAt(self, index):
        """
        Returns the appropriate mouse cursor for the given handle index.
        :type index: index
        :rtype: int
        """
        try:
            return self.HandleCursors[index]
        except (TypeError, IndexError):
            return Qt.ArrowCursor

    def handleAt(self, point):
        """
        Returns the index of the resize handle below the given point.
        :type point: QPointF
        :rtype: int
        """
        size = QPointF(3, 3)
        area = QRectF(point - size, point + size)
        for i in range(len(self.handleBound)):
            if self.handleBound[i].intersects(area):
                return i
        return None

    def redraw(self, selected=None, valid=None, handle=None, **kwargs):
        """
        Schedule this item for redrawing.
        :type selected: bool
        :type valid: bool
        :type handle: int
        """
        num = self.HandleNum

        brush0 = QBrush(Qt.NoBrush)
        brush1 = QBrush(QColor(43, 173, 63, 160))
        brush2 = QBrush(QColor(179, 12, 12, 160))
        brush3 = QBrush(QColor(132, 255, 0, 255))

        pen0 = QPen(Qt.NoPen)
        pen1 = QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        pen2 = QPen(QColor(0, 0, 0), 1.0, Qt.DashLine)

        backgroundBrush = brush0
        handleBrush = [brush0] * num
        handlePen = [pen0] * num
        selectionPen = pen0

        # ITEM SELECTION & RESIZE HANDLES
        if selected:
            if handle is None:
                handleBrush = [brush3] * num
                handlePen = [pen1] * num
                selectionPen = pen2
            else:
                for i in range(num):
                    if i == handle:
                        handleBrush[i] = brush3
                        handlePen[i] = pen1

        for i in range(num):
            self.handleBrush[i] = handleBrush[i]
            self.handlePen[i] = handlePen[i]

        self.selectionPen = selectionPen

        # SYNTAX VALIDATION
        if valid is not None:
            backgroundBrush = brush1 if valid else brush2
        self.backgroundBrush = backgroundBrush

        # FORCE CACHE REGENERATION
        self.setCacheMode(QGraphicsItem.NoCache)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

        # SCHEDULE REPAINT
        self.update(self.boundingRect())

    @abstractmethod
    def resize(self, mousePos):
        """
        Perform interactive resize of the node.
        :type mousePos: QPointF
        """
        pass

    def updateAnchors(self, data, diff):
        """
        Update anchor points.
        :type data: dict
        :type diff: QPointF
        """
        if data:
            for edge, pos in data.items():
                newPos = pos + diff * 0.5
                painterPath = self.painterPath()
                if not painterPath.contains(self.mapFromScene(newPos)):
                    newPos = self.intersection(QLineF(newPos, self.pos()))
                self.setAnchor(edge, newPos)

    def updateHandles(self):
        """
        Update current resize handles according to the shape size and position.
        """
        s = self.HandleSize
        b = self.boundingRect()
        self.handleBound[self.HandleTL] = QRectF(b.left(), b.top(), s, s)
        self.handleBound[self.HandleTM] = QRectF(b.center().x() - s / 2, b.top(), s, s)
        self.handleBound[self.HandleTR] = QRectF(b.right() - s, b.top(), s, s)
        self.handleBound[self.HandleML] = QRectF(b.left(), b.center().y() - s / 2, s, s)
        self.handleBound[self.HandleMR] = QRectF(b.right() - s, b.center().y() - s / 2, s, s)
        self.handleBound[self.HandleBL] = QRectF(b.left(), b.bottom() - s, s, s)
        self.handleBound[self.HandleBM] = QRectF(b.center().x() - s / 2, b.bottom() - s, s, s)
        self.handleBound[self.HandleBR] = QRectF(b.right() - s, b.bottom() - s, s, s)

    #############################################
    #   EVENTS
    #################################

    def hoverMoveEvent(self, hoverEvent):
        """
        Executed when the mouse moves over the shape (NOT PRESSED).
        :type hoverEvent: QGraphicsSceneHoverEvent
        """
        if self.diagram.mode is DiagramMode.Idle:
            if self.isSelected():
                self.setCursor(self.cursorAt(self.handleAt(hoverEvent.pos())))
        super().hoverMoveEvent(hoverEvent)

    def hoverLeaveEvent(self, hoverEvent):
        """
        Executed when the mouse leaves the shape (NOT PRESSED).
        :type hoverEvent: QGraphicsSceneHoverEvent
        """
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(hoverEvent)

    def itemChange(self, change, value):
        """
        Executed whenever the item change state.
        :type change: GraphicsItemChange
        :type value: QVariant
        :rtype: QVariant
        """
        if change == AbstractNode.ItemSelectedHasChanged:
            if self.diagram.mode is not DiagramMode.ResizeNode:
                self.redraw(selected=value)
        return super(AbstractNode, self).itemChange(change, value)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the item.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if self.diagram.mode is DiagramMode.Idle:

            mousePos = mouseEvent.pos()
            handle = self.handleAt(mousePos)
            if handle is not None:

                self.diagram.clearSelection()
                self.diagram.setMode(DiagramMode.ResizeNode)
                self.setSelected(True)

                BC = QRectF if isinstance(self.background, QRectF) else QPolygonF
                SC = QRectF if isinstance(self.selection, QRectF) else QPolygonF
                PC = QRectF if isinstance(self.polygon, QRectF) else QPolygonF

                self.mousePressBackground = BC(self.background)
                self.mousePressSelection = SC(self.selection)
                self.mousePressPolygon = PC(self.polygon)
                self.mousePressBound = SC(self.selection)
                self.mousePressData = {edge: pos for edge, pos in self.anchors.items()}
                self.mousePressHandle = handle
                self.mousePressPos = mousePos

                self.redraw(selected=True, handle=handle)

        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is being moved over the item while being pressed.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if self.diagram.mode is DiagramMode.ResizeNode:
            self.resize(mouseEvent.pos())
            self.updateEdges()
        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the item.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if self.diagram.mode is DiagramMode.ResizeNode:

            bound = self.boundingRect()

            if bound.size() != self.mousePressBound.size():

                BC = QRectF if isinstance(self.background, QRectF) else QPolygonF
                SC = QRectF if isinstance(self.selection, QRectF) else QPolygonF
                PC = QRectF if isinstance(self.polygon, QRectF) else QPolygonF

                background = BC(self.background)
                selection = SC(self.selection)
                polygon = PC(self.polygon)

                data = {
                    'undo': {
                        'background': self.mousePressBackground,
                        'selection': self.mousePressSelection,
                        'polygon': self.mousePressPolygon,
                        'anchors': self.mousePressData,
                        'moved': hasattr(self, 'label') and self.label.moved,
                    },
                    'redo': {
                        'background': background,
                        'selection': selection,
                        'polygon': polygon,
                        'anchors': {edge: pos for edge, pos in self.anchors.items()},
                        'moved': hasattr(self, 'label') and self.label.moved,
                    }
                }

                self.diagram.undoStack.push(CommandNodeRezize(self.diagram, self, data))

            self.diagram.setMode(DiagramMode.Idle)

        self.redraw(selected=self.isSelected())

        super().mouseReleaseEvent(mouseEvent)

        self.mousePressBackground = None
        self.mousePressSelection = None
        self.mousePressPolygon = None
        self.mousePressBound = None
        self.mousePressData = None
        self.mousePressHandle = None
        self.mousePressPos = None
        self.updateEdges()
        self.update()