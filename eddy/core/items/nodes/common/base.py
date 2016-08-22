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


from abc import ABCMeta, abstractmethod

from PyQt5.QtCore import QPointF, QLineF, Qt, QRectF
from PyQt5.QtGui import QPolygonF, QPen, QBrush, QColor

from eddy.core.commands.nodes import CommandNodeRezize
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.items.common import AbstractItem
from eddy.core.polygon import Polygon


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

        self._identity = Identity.Neutral

        self.anchors = dict()
        self.edges = set()

        self.background = None
        self.selection = None
        self.polygon = None
        self.label = None

        self.setAcceptHoverEvents(True)
        self.setCacheMode(AbstractItem.DeviceCoordinateCache)
        self.setFlag(AbstractItem.ItemIsSelectable, True)

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
        :rtype: set
        """
        f0 = lambda x: True
        f1 = filter_on_edges or f0
        f2 = filter_on_nodes or f0
        return {x for x in [e.other(self) for e in self.edges if f1(e)] if f2(x)}

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

    def brush(self):
        """
        Returns the brush used to paint the shape of this node.
        :rtype: QBrush
        """
        return self.polygon.brush()

    def center(self):
        """
        Returns the point at the center of the shape in item's coordinate.
        :rtype: QPointF
        """
        return self.boundingRect().center()

    @abstractmethod
    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        pass

    def geometry(self):
        """
        Returns the geometry of the shape of this node.
        :rtype: QPolygonF
        """
        return self.polygon.geometry()

    @abstractmethod
    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        pass

    def incomingNodes(self, filter_on_edges=None, filter_on_nodes=None):
        """
        Returns the set of incoming nodes.
        :type filter_on_edges: callable
        :type filter_on_nodes: callable
        :rtype: set
        """
        f0 = lambda x: True
        f1 = filter_on_edges or f0
        f2 = filter_on_nodes or f0
        return {x for x in [e.other(self) for e in self.edges \
                    if (e.target is self or e.type() is Item.InclusionEdge and e.equivalence) \
                        and f1(e)] if f2(x)}

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
        return Item.DomainRestrictionNode <= self.type() <= Item.FacetNode

    def isPredicate(self):
        """
        Returns True if this node is a predicate node, False otherwise.
        :rtype: bool
        """
        return Item.ConceptNode <= self.type() <= Item.IndividualNode

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
        :rtype: set
        """
        f0 = lambda x: True
        f1 = filter_on_edges or f0
        f2 = filter_on_nodes or f0
        return {x for x in [e.other(self) for e in self.edges \
                    if (e.source is self or e.type() is Item.InclusionEdge and e.equivalence) \
                        and f1(e)] if f2(x)}

    @abstractmethod
    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        pass

    def pen(self):
        """
        Returns the pen used to paint the shape of this node.
        :rtype: QPen
        """
        return self.polygon.pen()

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

    def setBrush(self, brush):
        """
        Set the brush used to paint the shape of this node.
        :type brush: QBrush
        """
        self.polygon.setBrush(brush)

    def setGeometry(self, geometry):
        """
        Set the geometry used to paint the shape of this node.
        :type geometry: T <= QRectF|QPolygonF
        """
        self.polygon.setGeometry(geometry)

    def setPen(self, pen):
        """
        Set the pen used to paint the shape of this node.
        :type pen: QPen
        """
        self.polygon.setPen(pen)

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
            raise TypeError('too many arguments; expected {0}, got {1}'.format(2, len(__args)))
        super().setPos(pos + super().pos() - self.pos())

    def redraw(self, selected=None, valid=None, **kwargs):
        """
        Perform the redrawing of this item.
        :type selected: bool
        :type valid: bool
        """
        # ITEM SELECTION
        pen = QPen(Qt.NoPen)
        if selected:
            pen = QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.DashLine)
        self.selection.setPen(pen)

        # SYNTAX VALIDATION
        brush = QBrush(Qt.NoBrush)
        if valid is not None:
            brush = QBrush(QColor(43, 173, 63, 160)) if valid else QBrush(QColor(179, 12, 12, 160))
        self.background.setBrush(brush)

        # FORCE CACHE REGENERATION
        self.setCacheMode(AbstractItem.NoCache)
        self.setCacheMode(AbstractItem.DeviceCoordinateCache)

        # SCHEDULE REPAINT
        self.update(self.boundingRect())

    def updateEdges(self):
        """
        Update all the edges attached to the node.
        """
        for edge in self.edges:
            edge.updateEdge()

    def updateNode(self, *args, **kwargs):
        """
        Update the current node.
        """
        pass

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
        Executed when the mouse is pressed on the item (EXCLUDED).
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        pass

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

    Cursors = [
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

        self.handles = [Polygon(QRectF()) for _ in range(8)]

        self.mp_Background = None
        self.mp_Selection = None
        self.mp_Polygon = None
        self.mp_Bound = None
        self.mp_Data = None
        self.mp_Handle = None
        self.mp_Pos = None

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
            return self.Cursors[index]
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
        for i in range(len(self.handles)):
            if self.handles[i].geometry().intersects(area):
                return i
        return None

    @abstractmethod
    def resize(self, mousePos):
        """
        Perform interactive resize of the node.
        :type mousePos: QPointF
        """
        pass

    def redraw(self, selected=None, valid=None, handle=None, **kwargs):
        """
        Perform the redrawing of this item.
        :type selected: bool
        :type valid: bool
        :type handle: int
        """
        # RESIZE HANDLES
        brush = [QBrush(Qt.NoBrush)] * 8
        pen = [QPen(Qt.NoPen)] * 8
        if selected:
            if handle is None:
                brush = [QBrush(QColor(66, 165, 245, 255))] * 8
                pen = [QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)] * 8
            else:
                for i in range(8):
                    if i == handle:
                        brush[i] = QBrush(QColor(66, 165, 245, 255))
                        pen[i] = QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

        for i in range(8):
            self.handles[i].setBrush(brush[i])
            self.handles[i].setPen(pen[i])

        # ITEM SELECTION
        pen = QPen(Qt.NoPen)
        if selected and handle is None:
            pen = QPen(QBrush(QColor(0, 0, 0, 255)), 1.0, Qt.DashLine)
        self.selection.setPen(pen)

        # SYNTAX VALIDATION
        brush = QBrush(Qt.NoBrush)
        if valid is not None:
            brush = QBrush(QColor(43, 173, 63, 160)) if valid else QBrush(QColor(179, 12, 12, 160))
        self.background.setBrush(brush)

        # FORCE CACHE REGENERATION
        self.setCacheMode(AbstractItem.NoCache)
        self.setCacheMode(AbstractItem.DeviceCoordinateCache)

        # SCHEDULE REPAINT
        self.update(self.boundingRect())

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

    def updateResizeHandles(self):
        """
        Update current resize handles according to the shape size and position.
        """
        b = self.boundingRect()
        self.handles[self.HandleTL].setGeometry(QRectF(b.left(), b.top(), 8, 8))
        self.handles[self.HandleTM].setGeometry(QRectF(b.center().x() - 4, b.top(), 8, 8))
        self.handles[self.HandleTR].setGeometry(QRectF(b.right() - 8, b.top(), 8, 8))
        self.handles[self.HandleML].setGeometry(QRectF(b.left(), b.center().y() - 4, 8, 8))
        self.handles[self.HandleMR].setGeometry(QRectF(b.right() - 8, b.center().y() - 4, 8, 8))
        self.handles[self.HandleBL].setGeometry(QRectF(b.left(), b.bottom() - 8, 8, 8))
        self.handles[self.HandleBM].setGeometry(QRectF(b.center().x() - 4, b.bottom() - 8, 8, 8))
        self.handles[self.HandleBR].setGeometry(QRectF(b.right() - 8, b.bottom() - 8, 8, 8))

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
            if self.diagram.mode is not DiagramMode.NodeResize:
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
                self.diagram.setMode(DiagramMode.NodeResize)
                self.setSelected(True)

                self.mp_Background = self.background.geometry().__class__(self.background.geometry())
                self.mp_Selection = self.selection.geometry().__class__(self.selection.geometry())
                self.mp_Polygon = self.polygon.geometry().__class__(self.polygon.geometry())
                self.mp_Bound = self.boundingRect().__class__(self.boundingRect())
                self.mp_Data = {edge: pos for edge, pos in self.anchors.items()}
                self.mp_Handle = handle
                self.mp_Pos = mousePos

                self.redraw(selected=True, handle=handle)

        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is being moved over the item while being pressed.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if self.diagram.mode is DiagramMode.NodeResize:
            self.resize(mouseEvent.pos())
            self.updateEdges()
        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the item.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if self.diagram.mode is DiagramMode.NodeResize:

            if self.boundingRect().size() != self.mp_Bound.size():

                data = {
                    'undo': {
                        'background': self.mp_Background,
                        'selection': self.mp_Selection,
                        'polygon': self.mp_Polygon,
                        'anchors': self.mp_Data,
                        'moved': self.label is not None and self.label.isMoved(),
                    },
                    'redo': {
                        'background': self.background.geometry().__class__(self.background.geometry()),
                        'selection': self.selection.geometry().__class__(self.selection.geometry()),
                        'polygon': self.polygon.geometry().__class__(self.polygon.geometry()),
                        'anchors': {edge: pos for edge, pos in self.anchors.items()},
                        'moved': self.label is not None and self.label.isMoved(),
                    }
                }

                self.session.undostack.push(CommandNodeRezize(self.diagram, self, data))

            self.diagram.setMode(DiagramMode.Idle)

        self.redraw(selected=self.isSelected())

        self.mp_Background = None
        self.mp_Selection = None
        self.mp_Polygon = None
        self.mp_Bound = None
        self.mp_Data = None
        self.mp_Handle = None
        self.mp_Pos = None

        super().mouseReleaseEvent(mouseEvent)

        self.updateEdges()
        self.update()