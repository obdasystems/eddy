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


from abc import ABCMeta, abstractmethod

from PyQt5 import QtCore
from PyQt5 import QtGui

from eddy.core.datatypes.qt import Font
from eddy.core.functions.signals import connect, disconnect

from eddy.core.commands.nodes import CommandNodeRezize
from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.items.common import AbstractItem, Polygon
from eddy.core.items.nodes.common.label import PredicateLabel
from eddy.core.owl import IRIRender


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

        self.background = None # BACKGROUND POLYGON
        self.selection = None # SELECTION POLYGON
        self.polygon = None # MAIN POLYGON
        self.label = None # ATTACHED LABEL

        self.setAcceptHoverEvents(True)
        self.setCacheMode(AbstractItem.DeviceCoordinateCache)
        self.setFlag(AbstractItem.ItemIsSelectable, True)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def identityName(self):
        """
        Returns the name of the identity of this item (i.e: Concept, Role, ...).
        :rtype: str
        """
        identity = self.identity()
        return identity.value

    @property
    def fontSize(self):
        if self.label:
            return self.label.font().pixelSize()
        return 12

    #############################################
    #   INTERFACE
    #################################

    def addEdge(self, edge):
        """
        Add the given edge to the current node.
        :type edge: AbstractEdge
        """
        self.edges.add(edge)

    def adjacentNodes(self, filter_on_edges=lambda x: True, filter_on_nodes=lambda x: True):
        """
        Returns the set of adjacent nodes.
        :type filter_on_edges: callable
        :type filter_on_nodes: callable
        :rtype: set
        """
        return {x for x in [e.other(self) for e in self.edges if filter_on_edges(e)] if filter_on_nodes(x)}

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
        :rtype: QtGui.QBrush
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

    def definition(self):
        """
        Returns the list of nodes which contribute to the definition of this very node.
        :rtype: set
        """
        return set()

    def geometry(self):
        """
        Returns the geometry of the shape of this node.
        :rtype: QtGui.QPolygonF
        """
        return self.polygon.geometry()

    @abstractmethod
    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        pass

    @classmethod
    def identities(cls):
        """
        Returns the set of identities supported by this node.
        :rtype: set
        """
        return cls.Identities

    def identify(self):
        """
        Perform the node identification step for the current node.
        Nodes who compute their identity without inheriting it from a direct connection,
        MUST provide an implementation of this method, which MUST be invoked only during
        the process which aims to identify a set of connected nodes.
        Any attempt to call this method from outside this process may cause inconsistencies.
        This method will compute the identity of the node according to it's configuration,
        and will return a tuple composed of 3 elements, whose purpose is to dynamically adapt
        the node identification algorithm behaviour according to the specific diagram configuration:

        * 1) A set of nodes to be added to the STRONG set (usually the node itself, when identified correctly).
        * 2) A set of nodes to be removed from the STRONG set (nodes that contribute only to the identity of this node)
        * 3) A set of nodes to be added to the EXCLUDED set (nodes that to not partecipate with inheritance in the identification step)

        If no identification is performed, the method MUST return None.
        :rtype: tuple
        """
        return None

    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return self._identity

    def incomingNodes(self, filter_on_edges=lambda x: True, filter_on_nodes=lambda x: True):
        """
        Returns the set of incoming nodes.
        :type filter_on_edges: callable
        :type filter_on_nodes: callable
        :rtype: set
        """
        return {x for x in [e.other(self) for e in self.edges \
                    if (e.target is self or e.type() is Item.EquivalenceEdge) \
                        and filter_on_edges(e)] if filter_on_nodes(x)}

    def intersection(self, line):
        """
        Returns the intersection of the shape with the given line (in scene coordinates).
        :type line: QtCore.QLineF
        :rtype: QPointF
        """
        intersection = QtCore.QPointF()
        path = self.painterPath()
        polygon = self.mapToScene(path.toFillPolygon(self.transform()))
        for i in range(0, polygon.size() - 1):
            polyline = QtCore.QLineF(polygon[i], polygon[i + 1])
            if polyline.intersect(line, intersection) == QtCore.QLineF.BoundedIntersection:
                return intersection
        return None

    def intersections(self, line):
        """
        Returns the list of intersections of the shape with the given line (in scene coordinates).
        :type line: QtCore.QLineF
        :rtype: list
        """
        intersections = []
        path = self.painterPath()
        polygon = self.mapToScene(path.toFillPolygon(self.transform()))
        for i in range(0, polygon.size() - 1):
            intersection = QtCore.QPointF()
            polyline = QtCore.QLineF(polygon[i], polygon[i + 1])
            if polyline.intersect(line, intersection) == QtCore.QLineF.BoundedIntersection:
                intersections.append(intersection)
        return intersections

    def isConstructor(self):
        """
        Returns True if this node is a contructor node, False otherwise.
        :rtype: bool
        """
        return Item.DomainRestrictionNode <= self.type() <= Item.HasKeyNode

    def isMeta(self):
        """
        Returns True iff we should memorize metadata for this item, False otherwise.
        :rtype: bool
        """
        item = self.type()
        identity = self.identity()
        return item is Item.ConceptNode or \
           item is Item.RoleNode or \
           item is Item.AttributeNode or \
           item is Item.IndividualNode and identity is not Identity.Value

    def isPredicate(self):
        """
        Returns True if this node is a predicate node, False otherwise.
        :rtype: bool
        """
        return  Item.ConceptNode <= self.type() <= Item.IndividualNode

    def moveBy(self, x, y):
        """
        Move the node by the given deltas.
        :type x: T <= float | int
        :type y: T <= float | int
        """
        move = QtCore.QPointF(x, y)
        self.setPos(self.pos() + move)
        self.anchors = {edge: pos + move for edge, pos in self.anchors.items()}

    def outgoingNodes(self, filter_on_edges=lambda x: True, filter_on_nodes=lambda x: True):
        """
        Returns the set of outgoing nodes.
        :type filter_on_edges: callable
        :type filter_on_nodes: callable
        :rtype: set
        """
        return {x for x in [e.other(self) for e in self.edges \
                    if (e.source is self or e.type() is Item.EquivalenceEdge) \
                        and filter_on_edges(e)] if filter_on_nodes(x)}

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
        :rtype: QtGui.QPen
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
        :type geometry: T <= QtCore.QRectF|QtGui.QPolygonF
        """
        self.polygon.setGeometry(geometry)

    def setIdentity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        if identity not in self.identities():
            identity = Identity.Unknown
        self._identity = identity

    def setPen(self, pen):
        """
        Set the pen used to paint the shape of this node.
        :type pen: QtGui.QPen
        """
        self.polygon.setPen(pen)

    def setPos(self, *__args):
        """
        Set the item position.
        QGraphicsItem.setPos(QtCore.QPointF)
        QGraphicsItem.setPos(float, float)
        """
        if len(__args) == 1:
            pos = __args[0]
        elif len(__args) == 2:
            pos = QtCore.QPointF(__args[0], __args[1])
        else:
            raise TypeError('too many arguments; expected {0}, got {1}'.format(2, len(__args)))
        super().setPos(pos + super().pos() - self.pos())

    def updateEdges(self):
        """
        Update all the edges attached to the node.
        """
        for edge in self.edges:
            edge.updateEdge()

    def updateNode(self, selected=None, valid=None, **kwargs):
        """
        Update the current node.
        :type selected: bool
        :type valid: bool
        """
        # ITEM SELECTION (BRUSH)
        brush = QtGui.QBrush(QtCore.Qt.NoBrush)
        if selected:
            brush = QtGui.QBrush(QtGui.QColor(248, 255, 72, 255))
        self.selection.setBrush(brush)

        # SYNTAX VALIDATION (BACKGROUND BRUSH)
        brush = QtGui.QBrush(QtCore.Qt.NoBrush)
        if valid is not None:
            brush = QtGui.QBrush(QtGui.QColor(179, 12, 12, 160))
            if valid:
                brush = QtGui.QBrush(QtGui.QColor(43, 173, 63, 160))
        self.background.setBrush(brush)

        # FORCE CACHE REGENERATION
        self.setCacheMode(AbstractItem.NoCache)
        self.setCacheMode(AbstractItem.DeviceCoordinateCache)

        # SCHEDULE REPAINT
        self.update(self.boundingRect())

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

    def setFontSize(self, size):
        if self.label:
            baseFont = self.diagram.font() if self.diagram else None
            self.label.setCustomFont(Font(font=baseFont, pixelSize=size, weight=Font.Light))

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
            self.updateNode(selected=value)
        return super().itemChange(change, value)

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
        QtCore.Qt.SizeFDiagCursor,
        QtCore.Qt.SizeVerCursor,
        QtCore.Qt.SizeBDiagCursor,
        QtCore.Qt.SizeHorCursor,
        QtCore.Qt.SizeHorCursor,
        QtCore.Qt.SizeBDiagCursor,
        QtCore.Qt.SizeVerCursor,
        QtCore.Qt.SizeFDiagCursor,
    ]

    def __init__(self, **kwargs):
        """
        Initialize the node.
        """
        super().__init__(**kwargs)

        self.handles = [Polygon(QtCore.QRectF()) for _ in range(8)]

        self.mp_Background = None
        self.mp_Selection = None
        self.mp_Polygon = None
        self.mp_Bound = None
        self.mp_Data = None
        self.mp_Handle = None
        self.mp_Pos = None

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
            return QtCore.Qt.ArrowCursor

    def handleAt(self, point):
        """
        Returns the index of the resize handle below the given point.
        :type point: QtCore.QPointF
        :rtype: int
        """
        size = QtCore.QPointF(3, 3)
        area = QtCore.QRectF(point - size, point + size)
        for i in range(len(self.handles)):
            if self.handles[i].geometry().intersects(area):
                return i
        return None

    @abstractmethod
    def resize(self, mousePos):
        """
        Perform interactive resize of the node.
        :type mousePos: QtCore.QPointF
        """
        pass

    def updateNode(self, selected=None, valid=None, handle=None, anchors=None, **kwargs):
        """
        Update the current node.
        :type selected: bool
        :type valid: bool
        :type handle: int
        :type anchors: T <= list|tuple
        """
        # RESIZE HANDLES (GEOMETRY)
        b = self.boundingRect()
        self.handles[self.HandleTL].setGeometry(QtCore.QRectF(b.left(), b.top(), 8, 8))
        self.handles[self.HandleTM].setGeometry(QtCore.QRectF(b.center().x() - 4, b.top(), 8, 8))
        self.handles[self.HandleTR].setGeometry(QtCore.QRectF(b.right() - 8, b.top(), 8, 8))
        self.handles[self.HandleML].setGeometry(QtCore.QRectF(b.left(), b.center().y() - 4, 8, 8))
        self.handles[self.HandleMR].setGeometry(QtCore.QRectF(b.right() - 8, b.center().y() - 4, 8, 8))
        self.handles[self.HandleBL].setGeometry(QtCore.QRectF(b.left(), b.bottom() - 8, 8, 8))
        self.handles[self.HandleBM].setGeometry(QtCore.QRectF(b.center().x() - 4, b.bottom() - 8, 8, 8))
        self.handles[self.HandleBR].setGeometry(QtCore.QRectF(b.right() - 8, b.bottom() - 8, 8, 8))

        # RESIZE HANDLES (PEN + BRUSH)
        brush = [QtGui.QBrush(QtCore.Qt.NoBrush)] * 8
        pen = [QtGui.QPen(QtCore.Qt.NoPen)] * 8
        if selected:
            if handle is None:
                brush = [QtGui.QBrush(QtGui.QColor(66, 165, 245, 255))] * 8
                pen = [QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)] * 8
            else:
                for i in range(8):
                    if i == handle:
                        brush[i] = QtGui.QBrush(QtGui.QColor(66, 165, 245, 255))
                        pen[i] = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        for i in range(8):
            self.handles[i].setBrush(brush[i])
            self.handles[i].setPen(pen[i])

        # ITEM SELECTION (BRUSH)
        brush = QtGui.QBrush(QtCore.Qt.NoBrush)
        if selected and handle is None:
            brush = QtGui.QBrush(QtGui.QColor(248, 255, 72, 255))
        self.selection.setBrush(brush)

        # SYNTAX VALIDATION (BACKGROUND BRUSH)
        brush = QtGui.QBrush(QtCore.Qt.NoBrush)
        if valid is not None:
            brush = QtGui.QBrush(QtGui.QColor(43, 173, 63, 160)) if valid else QtGui.QBrush(QtGui.QColor(179, 12, 12, 160))
        self.background.setBrush(brush)

        # ANCHOR POINTS (POSITION) -> NB: SHAPE IS IN THE EDGES
        if anchors is not None:
            mp_Data = anchors[0]
            diff = anchors[1]
            for edge, pos in mp_Data.items():
                newPos = pos + diff * 0.5
                painterPath = self.painterPath()
                if not painterPath.contains(self.mapFromScene(newPos)):
                    newPos = self.intersection(QtCore.QLineF(newPos, self.pos()))
                self.setAnchor(edge, newPos)

        # FORCE CACHE REGENERATION
        self.setCacheMode(AbstractItem.NoCache)
        self.setCacheMode(AbstractItem.DeviceCoordinateCache)

        # SCHEDULE REPAINT
        self.update(self.boundingRect())

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
        self.setCursor(QtCore.Qt.ArrowCursor)
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
                self.updateNode(selected=value)
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

                self.updateNode(selected=True, handle=handle)

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

        self.updateNode(selected=self.isSelected())

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


class PredicateNodeMixin:
    """
    Mixin for nodes representing ontology elements (i.e. nodes having an associated IRI).
    """
    sgnIRISwitched = QtCore.pyqtSignal()

    def __init__(self, iri=None, **kwargs):
        super().__init__(**kwargs)
        self._iri = iri
        self.labelString = None
        self.label = None

    @property
    def iri(self):
        """
        :rtype: IRI
        """
        return self._iri

    @iri.setter
    def iri(self, iriObj):
        """
        :type iriObj:IRI
        """
        switch = False
        if self.iri:
            switch = True
            self.disconnectIRISignals()
        self._iri = iriObj
        self.connectIRISignals()
        if switch:
            self.sgnIRISwitched.emit()
        self.doUpdateNodeLabel()
        if self.diagram:
            self.diagram.project.sgnUpdated.emit()

    @abstractmethod
    def initialLabelPosition(self):
        pass

    #############################################
    #   INTERFACE
    #################################

    def mouseDoubleClickEvent(self, mouseEvent):
        """
        Executed when the mouse is double clicked on the text item.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        self.session.doOpenIRIDialog(self)
        mouseEvent.accept()

    def connectSignals(self):
        if self.diagram:
            connect(self.project.sgnPrefixAdded, self.onPrefixAdded)
            connect(self.project.sgnPrefixRemoved, self.onPrefixRemoved)
            connect(self.project.sgnPrefixModified, self.onPrefixModified)
            #connect(self.session.sgnRenderingModified, self.onRenderingModified)
            self.connectIRISignals()

    def disconnectSignals(self):
        if self.diagram:
            disconnect(self.project.sgnPrefixAdded, self.onPrefixAdded)
            disconnect(self.project.sgnPrefixRemoved, self.onPrefixRemoved)
            disconnect(self.project.sgnPrefixModified, self.onPrefixModified)
            #disconnect(self.session.sgnRenderingModified, self.onRenderingModified)
            self.disconnectIRISignals()

    def connectIRISignals(self):
        connect(self.iri.sgnIRIModified, self.onIRIModified)
        connect(self.iri.sgnIRIPropModified, self.onIRIPropModified)
        connect(self.iri.sgnAnnotationAdded, self.onAnnotationAdded)
        connect(self.iri.sgnAnnotationRemoved, self.onAnnotationRemoved)
        connect(self.iri.sgnAnnotationModified, self.onAnnotationModified)
        self.connectIRIMetaSignals()

    def disconnectIRISignals(self):
        disconnect(self.iri.sgnIRIModified, self.onIRIModified)
        disconnect(self.iri.sgnIRIPropModified, self.onIRIPropModified)
        disconnect(self.iri.sgnAnnotationAdded, self.onAnnotationAdded)
        disconnect(self.iri.sgnAnnotationRemoved, self.onAnnotationRemoved)
        disconnect(self.iri.sgnAnnotationModified, self.onAnnotationModified)
        self.disconnectIRIMetaSignals()

    def connectIRIMetaSignals(self):
        pass

    def disconnectIRIMetaSignals(self):
        pass

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onIRIPropModified(self):
        if self.diagram:
            self.diagram.project.sgnUpdated.emit()

    @QtCore.pyqtSlot()
    def doUpdateNodeLabel(self):
        newLabelString = IRIRender.iriLabelString(self._iri)
        if self.label and not self.labelString == newLabelString:
            self.labelString = newLabelString
            labelPos = lambda:self.label.pos()
            try:
                if self.label.diagram:
                    self.label.diagram.removeItem(self.label)
            except AttributeError:
                print("label.diagram is not defined!!")
            self.label = PredicateLabel(template=self.labelString, pos=labelPos, parent=self)
            #self.diagram.sgnUpdated.emit()self.label
        elif not self.label:
            self.labelString = newLabelString
            self.label = PredicateLabel(template=self.labelString, pos=self.initialLabelPosition, parent=self)
            #self.diagram.sgnUpdated.emit()

    #@QtCore.pyqtSlot(AnnotationAssertion)
    def onAnnotationAdded(self, annotation):
        """
        :type annotation: AnnotationAssertion
        """
        settings = QtCore.QSettings()
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value)
        if rendering == IRIRender.LABEL.value:
            self.doUpdateNodeLabel()
        if self.diagram:
            self.diagram.project.sgnUpdated.emit()

    #@QtCore.pyqtSlot(AnnotationAssertion)
    def onAnnotationRemoved(self, annotation):
        """
        :type annotation: AnnotationAssertion
        """
        settings = QtCore.QSettings()
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, )
        if rendering == IRIRender.LABEL.value:
            self.doUpdateNodeLabel()
        if self.diagram:
            self.diagram.project.sgnUpdated.emit()

    #@QtCore.pyqtSlot(AnnotationAssertion)
    def onAnnotationModified(self, annotation):
        """
        :type annotation: AnnotationAssertion
        """
        settings = QtCore.QSettings()
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering == IRIRender.LABEL.value:
            self.doUpdateNodeLabel()
        if self.diagram:
            self.diagram.project.sgnUpdated.emit()

    #@QtCore.pyqtSlot()
    def onIRIModified(self):
        self.doUpdateNodeLabel()
        if self.diagram:
            self.diagram.project.sgnUpdated.emit()

    #@QtCore.pyqtSlot('QString','QString')
    def onPrefixAdded(self,pref,ns):
        settings = QtCore.QSettings()
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering==IRIRender.PREFIX.value or rendering==IRIRender.LABEL.value:
            self.doUpdateNodeLabel()

    #@QtCore.pyqtSlot(str)
    def onPrefixRemoved(self,pref):
        settings = QtCore.QSettings()
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering==IRIRender.PREFIX.value or rendering==IRIRender.LABEL.value:
            self.doUpdateNodeLabel()

    #@QtCore.pyqtSlot(str)
    def onPrefixModified(self,pref):
        settings = QtCore.QSettings()
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering==IRIRender.PREFIX.value or rendering==IRIRender.LABEL.value:
            self.doUpdateNodeLabel()

    #############################################
    #   EVENTS
    #################################
    def hoverEnterEvent(self, hoverEvent):
        """
        Executed when the mouse enters the shape (NOT PRESSED).
        :type hoverEvent: QGraphicsSceneHoverEvent
        """
        self.session.statusBar().showMessage('Hold Shift ⇧ and drag the label to move it')
        super().hoverEnterEvent(hoverEvent)

    def hoverLeaveEvent(self, hoverEvent):
        """
        Executed when the mouse leaves the shape (NOT PRESSED).
        :type hoverEvent: QGraphicsSceneHoverEvent
        """
        self.session.statusBar().clearMessage()
        super().hoverLeaveEvent(hoverEvent)
