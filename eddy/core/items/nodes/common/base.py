# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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


from abc import ABCMeta, abstractmethod

from PyQt5.QtCore import QPointF, QLineF, Qt, QRectF
from PyQt5.QtGui import QColor, QPen, QBrush, QPolygonF
from PyQt5.QtWidgets import QGraphicsItem

from eddy.core.commands import CommandNodeRezize
from eddy.core.datatypes import DistinctList, DiagramMode, Identity, Item
from eddy.core.items import AbstractItem


class AbstractNode(AbstractItem):
    """
    Base class for all the diagram nodes.
    """
    __metaclass__ = ABCMeta

    identities = {}
    prefix = 'n'

    def __init__(self, **kwargs):
        """
        Initialize the node.
        """
        super().__init__(**kwargs)

        self._backgroundBrush = Qt.NoBrush
        self._backgroundPen = Qt.NoPen

        self.anchors = {}
        self.edges = DistinctList()

        self.polygon = None
        self.backgroundArea = None
        self.selectionArea = None

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def constructor(self):
        """
        Tells whether this node is a constructor node.
        :rtype: bool
        """
        return Item.DomainRestrictionNode <= self.item <= Item.PropertyAssertionNode

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

    @property
    def predicate(self):
        """
        Tells whether this node is a predicate node.
        :rtype: bool
        """
        return Item.ConceptNode <= self.item <= Item.ValueRestrictionNode

    @property
    def resizable(self):
        """
        Tells whether the shape can be resized or not.
        :rtype: bool
        """
        return False

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def addEdge(self, edge):
        """
        Add the given edge to the current node.
        :type edge: AbstractEdge
        """
        self.edges.append(edge)

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

    def backgroundBrush(self):
        """
        Returns the brush used to draw the background of the item.
        :rtype: QBrush
        """
        return self._backgroundBrush

    def backgroundPen(self):
        """
        Returns the pen used to draw the background of the item.
        :rtype: QPen
        """
        return self._backgroundPen

    def center(self):
        """
        Returns the point at the center of the shape in item's coordinate.
        :rtype: QPointF
        """
        return self.boundingRect().center()

    @abstractmethod
    def copy(self, scene):
        """
        Create a copy of the current item.
        :type scene: DiagramScene
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
        :rtype: list
        """
        f0 = lambda x: True
        f1 = filter_on_edges or f0
        f2 = filter_on_nodes or f0
        return [x for x in [e.other(self) for e in self.edges \
                    if (e.target is self or e.isItem(Item.InclusionEdge) and e.complete) \
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
                    if (e.source is self or e.isItem(Item.InclusionEdge) and e.complete) \
                        and f1(e)] if f2(x)]

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
        self.edges.remove(edge)

    def setAnchor(self, edge, pos):
        """
        Set the given position as anchor for the given edge.
        :type edge: AbstractEdge
        :type pos: QPointF
        """
        self.anchors[edge] = pos

    def setBackgroundBrush(self, brush):
        """
        Sets the brush used to draw the background of the item.
        :type brush: QBrush
        """
        self._backgroundBrush = brush

    def setBackgroundPen(self, pen):
        """
        Sets the pen used to draw the background of the item.
        :type pen: QPen
        """
        self._backgroundPen = pen

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

    def updateEdges(self):
        """
        Update all the edges attached to the node.
        """
        for edge in self.edges:
            edge.updateEdge()

    def updatePenAndBrush(self, selected=None, valid=None, **kwargs):
        """
        Perform updates on pens and brushes needed by the paint() method.
        :type selected: bool
        :type valid: bool
        """
        backgroundBrushOkPattern = QBrush(QColor(43, 173, 63, 160))
        backgroundBrushBadPattern = QBrush(QColor(179, 12, 12, 160))
        selectionPenPattern = QPen(QColor(0, 0, 0), 1.0, Qt.DashLine)
        noBrush = QBrush(Qt.NoBrush)
        noPen = QPen(Qt.NoPen)

        backgroundBrush = noBrush
        selectionPen = noPen

        # ITEM SELECTION
        if selected:
            selectionPen = selectionPenPattern
        self.setSelectionPen(selectionPen)

        # SYNTAX VALIDATION
        if valid is not None:
            backgroundBrush = backgroundBrushOkPattern if valid else backgroundBrushBadPattern
        self.setBackgroundBrush(backgroundBrush)

    @abstractmethod
    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def itemChange(self, change, value):
        """
        Executed whenever the item change state.
        :type change: GraphicsItemChange
        :type value: QVariant
        :rtype: QVariant
        """
        if change == AbstractNode.ItemSelectedHasChanged:
            self.updatePenAndBrush(selected=value)
        return super(AbstractNode, self).itemChange(change, value)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the item.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()

        # Allow node selection only if we are in DiagramMode.Idle state: resizable
        # nodes may have changed the scene mode to DiagramMode.NodeResize if a resize
        # handle is selected, thus we don't need to perform (multi)selection.
        if scene.mode is DiagramMode.Idle:

            # Here is a slightly modified version of the default behavior
            # which improves the interaction with multiple selected nodes.
            if mouseEvent.modifiers() & Qt.ControlModifier:
                # If the control modifier is being held switch the selection flag.
                self.setSelected(not self.isSelected())
            else:
                if scene.selectedItems():
                    # Some elements are already selected (previoust mouse press event).
                    if not self.isSelected():
                        # There are some items selected but we clicked on a node
                        # which is not currently selected, so select only this one.
                        scene.clearSelection()
                        self.setSelected(True)
                else:
                    # No node is selected and we just clicked on one so select it
                    # since we filter out the Label, clear the scene selection in
                    # any case to avoid strange bugs.
                    scene.clearSelection()
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

    ####################################################################################################################
    #                                                                                                                  #
    #   GEOMETRY                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    @abstractmethod
    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   LABEL SHORTCUTS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    @abstractmethod
    def textPos(self):
        """
        Returns the current label position.
        :rtype: QPointF
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
    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        pass

    @abstractmethod
    def setText(self, text):
        """
        Set the label text.
        :type text: str
        """
        pass

    @abstractmethod
    def updateTextPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    @classmethod
    @abstractmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        pass


class AbstractResizableNode(AbstractNode):
    """
    Base class for all the diagram resizable nodes.
    """
    __metaclass__ = ABCMeta

    handleTL = 0
    handleTM = 1
    handleTR = 2
    handleML = 3
    handleMR = 4
    handleBL = 5
    handleBM = 6
    handleBR = 7

    handleNum = 8
    handleMove = -4
    handleSize = 8

    handleCursors = [
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

        self._handleBrush = [Qt.NoBrush] * self.handleNum
        self._handlePen = [Qt.NoPen] * self.handleNum
        self._handleRect = [None] * self.handleNum

        self.mousePressBackgroundArea = None
        self.mousePressSelectionArea = None
        self.mousePressPolygon = None
        self.mousePressBound = None
        self.mousePressData = None
        self.mousePressHandle = None
        self.mousePressPos = None

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

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

    @property
    def resizable(self):
        """
        Tells whether the shape can be resized or not.
        :rtype: bool
        """
        return True

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def cursorAt(self, index):
        """
        Returns the appropriate mouse cursor for the given handle index.
        :type index: index
        :rtype: int
        """
        try:
            return self.handleCursors[index]
        except (TypeError, IndexError):
            return Qt.ArrowCursor

    def handleAt(self, point):
        """
        Returns the index of the resize handle below the given point.
        :type point: QPointF
        :rtype: int
        """
        for i in range(len(self._handleRect)):
            if self._handleRect[i].contains(point):
                return i
        return None

    def handleBrush(self, index):
        """
        Returns the brush used to draw the given resizing handle.
        :type index: int
        :rtype: QBrush
        """
        return self._handleBrush[index]

    def handlePen(self, index):
        """
        Returns the pen used to draw the given resizing handle.
        :type index: int
        :rtype: QPen
        """
        return self._handlePen[index]

    @abstractmethod
    def interactiveResize(self, mousePos):
        """
        Handle the interactive resize of the node.
        :type mousePos: QPointF
        """
        pass

    def setHandleBrush(self, index, brush):
        """
        Sets the brush used to draw the given resizing handle.
        :type index: int
        :type brush: QBrush
        """
        self._handleBrush[index] = brush

    def setHandlePen(self, index, pen):
        """
        Sets the pen used to draw the given resizing handle.
        :type index: int
        :type pen: QPen
        """
        self._handlePen[index] = pen

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

    def updatePenAndBrush(self, selected=None, valid=None, handle=None, **kwargs):
        """
        Perform updates on pens and brushes needed by the paint() method.
        :type selected: bool
        :type valid: bool
        :type handle: int
        """
        num = self.handleNum

        backgroundBrushOkPattern = QBrush(QColor(43, 173, 63, 160))
        backgroundBrushBadPattern = QBrush(QColor(179, 12, 12, 160))
        handleBrushPattern = QBrush(QColor(168, 168, 168, 255))
        handlePenPattern = QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        selectionPenPattern = QPen(QColor(0, 0, 0), 1.0, Qt.DashLine)
        noBrush = QBrush(Qt.NoBrush)
        noPen = QPen(Qt.NoPen)

        handleBrush = [noBrush] * num
        handlePen = [noPen] * num
        selectionPen = noPen

        # ITEM SELECTION & RESIZE HANDLES
        if selected:
            if handle is None:
                handleBrush = [handleBrushPattern] * num
                handlePen = [handlePenPattern] * num
                selectionPen = selectionPenPattern
            else:
                for i in range(num):
                    if i == handle:
                        handleBrush[i] = handleBrushPattern
                        handlePen[i] = handlePenPattern

        for i in range(num):
            self.setHandleBrush(i, handleBrush[i])
            self.setHandlePen(i, handlePen[i])

        self.setSelectionPen(selectionPen)

        # SYNTAX VALIDATION
        brush = noBrush
        if valid is not None:
            brush = backgroundBrushOkPattern if valid else backgroundBrushBadPattern
        self.setBackgroundBrush(brush)

    def updateHandles(self):
        """
        Update current resize handles according to the shape size and position.
        """
        s = self.handleSize
        b = self.boundingRect()
        self._handleRect[self.handleTL] = QRectF(b.left(), b.top(), s, s)
        self._handleRect[self.handleTM] = QRectF(b.center().x() - s / 2, b.top(), s, s)
        self._handleRect[self.handleTR] = QRectF(b.right() - s, b.top(), s, s)
        self._handleRect[self.handleML] = QRectF(b.left(), b.center().y() - s / 2, s, s)
        self._handleRect[self.handleMR] = QRectF(b.right() - s, b.center().y() - s / 2, s, s)
        self._handleRect[self.handleBL] = QRectF(b.left(), b.bottom() - s, s, s)
        self._handleRect[self.handleBM] = QRectF(b.center().x() - s / 2, b.bottom() - s, s, s)
        self._handleRect[self.handleBR] = QRectF(b.right() - s, b.bottom() - s, s, s)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def hoverMoveEvent(self, hoverEvent):
        """
        Executed when the mouse moves over the shape (NOT PRESSED).
        :type hoverEvent: QGraphicsSceneHoverEvent
        """
        scene = self.scene()
        if scene.mode is DiagramMode.Idle:
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
            scene = self.scene()
            if scene.mode is not DiagramMode.NodeResize:
                self.updatePenAndBrush(selected=value)
        return super(AbstractNode, self).itemChange(change, value)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the item.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()

        if scene.mode is DiagramMode.Idle:
            mousePos = mouseEvent.pos()
            handle = self.handleAt(mousePos)
            if handle is not None:

                scene.clearSelection()
                scene.setMode(DiagramMode.NodeResize)
                self.setSelected(True)

                BC = QRectF if isinstance(self.backgroundArea, QRectF) else QPolygonF
                SC = QRectF if isinstance(self.selectionArea, QRectF) else QPolygonF
                PC = QRectF if isinstance(self.polygon, QRectF) else QPolygonF

                self.mousePressBackgroundArea = BC(self.backgroundArea)
                self.mousePressSelectionArea = SC(self.selectionArea)
                self.mousePressPolygon = PC(self.polygon)
                self.mousePressBound = self.boundingRect()
                self.mousePressData = {edge: pos for edge, pos in self.anchors.items()}
                self.mousePressHandle = handle
                self.mousePressPos = mousePos

                self.updatePenAndBrush(selected=True, handle=handle)

        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is being moved over the item while being pressed.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()

        if scene.mode is DiagramMode.NodeResize:
            self.interactiveResize(mouseEvent.pos())
            self.updateEdges()

        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the item.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()

        if scene.mode is DiagramMode.NodeResize:

            bound = self.boundingRect()

            if bound.size() != self.mousePressBound.size():

                BC = QRectF if isinstance(self.backgroundArea, QRectF) else QPolygonF
                SC = QRectF if isinstance(self.selectionArea, QRectF) else QPolygonF
                PC = QRectF if isinstance(self.polygon, QRectF) else QPolygonF

                backgroundArea = BC(self.backgroundArea)
                selectionArea = SC(self.selectionArea)
                polygon = PC(self.polygon)

                commandData = {
                    'undo': {
                        'backgroundArea': self.mousePressBackgroundArea,
                        'selectionArea': self.mousePressSelectionArea,
                        'polygon': self.mousePressPolygon,
                        'anchors': self.mousePressData,
                        'moved': hasattr(self, 'label') and self.label.moved,
                    },
                    'redo': {
                        'backgroundArea': backgroundArea,
                        'selectionArea': selectionArea,
                        'polygon': polygon,
                        'anchors': {edge: pos for edge, pos in self.anchors.items()},
                        'moved': hasattr(self, 'label') and self.label.moved,
                    }
                }

                scene.undostack.push(CommandNodeRezize(scene=scene, node=self, data=commandData))

            scene.setMode(DiagramMode.Idle)

        self.updatePenAndBrush(selected=self.isSelected())

        super().mouseReleaseEvent(mouseEvent)

        self.mousePressBackgroundArea = None
        self.mousePressSelectionArea = None
        self.mousePressPolygon = None
        self.mousePressBound = None
        self.mousePressData = None
        self.mousePressHandle = None
        self.mousePressPos = None
        self.updateEdges()
        self.update()