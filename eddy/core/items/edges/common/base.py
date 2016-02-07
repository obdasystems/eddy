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
from math import sin, cos, radians

from PyQt5.QtCore import Qt, QPointF, QLineF, QRectF
from PyQt5.QtGui import QPen, QPolygonF, QPainterPath, QBrush, QColor
from PyQt5.QtWidgets import QGraphicsItem

from eddy.core.commands import CommandEdgeBreakpointAdd, CommandEdgeBreakpointMove, CommandEdgeAnchorMove
from eddy.core.datatypes import DiagramMode
from eddy.core.functions import distanceP, distanceL
from eddy.core.items import AbstractItem


class AbstractEdge(AbstractItem):
    """
    Base class for all the diagram edges.
    """
    __metaclass__ = ABCMeta

    headBrushPattern = QBrush(QColor(0, 0, 0))
    headPenPattern = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    handleBrushPattern = QBrush(QColor(168, 168, 168, 255))
    handlePenPattern = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    penPattern = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    selectionBrushPattern = QBrush(QColor(251, 255, 148))

    handleSize = 8
    headSize = 12
    prefix = 'e'
    selectionSize = 8

    def __init__(self, source, target=None, breakpoints=None, **kwargs):
        """
        Initialize the edge.
        :type source: AbstractNode
        :type target: AbstractNode
        :type breakpoints: list
        """
        super().__init__(**kwargs)

        self._source = source
        self._target = target

        self.handleBrush = QBrush(Qt.NoBrush)
        self.handlePen = QPen(Qt.NoPen)
        self.headBrush = QBrush(Qt.NoBrush)
        self.headPen = QPen(Qt.NoPen)
        self.selectionBrush = QBrush(Qt.NoBrush)
        self.selectionPen = QPen(Qt.NoPen)

        self.anchors = {}
        self.breakpoints = breakpoints or []
        self.handles = []
        self.head = QPolygonF()

        self.path = QPainterPath()
        self.selection = QPainterPath()

        self.mousePressAnchorNode = None
        self.mousePressAnchorNodePos = None
        self.mousePressBreakPoint = None
        self.mousePressBreakPointPos = None
        self.mousePressPos = None

        self.setAcceptHoverEvents(True)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def source(self):
        """
        Returns the source node.
        :rtype: Node
        """
        return self._source

    @source.setter
    def source(self, source):
        """
        Set the source of this edge.
        :type source: AbstractNode
        """
        self._source = source

    @property
    def target(self):
        """
        Returns the target node.
        :rtype: Node
        """
        return self._target

    @target.setter
    def target(self, target):
        """
        Set the target of this edge.
        :type target: AbstractNode
        """
        self._target = target

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def anchorAt(self, point):
        """
        Returns the key of the anchor whose handle is being pressed.
        :type point: AbstractNode
        """
        for k, v, in self.anchors.items():
            if v.contains(point):
                return k
        return None

    def anchorMove(self, node, mousePos):
        """
        Move the selected anchor point.
        :type node: AbstractNode
        :type mousePos: QPointF
        """
        scene = self.scene()
        nodePos = node.pos()
        mousePos = scene.snapToGrid(mousePos)
        path = self.mapFromItem(node, node.painterPath())
        if path.contains(mousePos):
            # Mouse is inside the shape => use this position as anchor point.
            pos = nodePos if distanceP(mousePos, nodePos) < 10.0 else mousePos
        else:
            # Mouse is outside the shape => use the intersection point as anchor point.
            pos = node.intersection(QLineF(mousePos, nodePos))
            for e in [pos, pos + QPointF(1, -1), pos + QPointF(1, 0),
                           pos + QPointF(1, 1), pos + QPointF(0, 1),
                           pos + QPointF(-1, 1), pos + QPointF(-1, 0),
                           pos + QPointF(-1, -1), pos + QPointF(0, -1)]:
                if path.contains(e):
                    pos = e
                    break

        node.setAnchor(self, pos)

    def breakpointAdd(self, mousePos):
        """
        Create a new breakpoint from the given mouse position returning its index.
        :type mousePos: QPointF
        :rtype: int
        """
        index = 0
        point = None
        between = None
        shortest = 999

        source = self.source.anchor(self)
        target = self.target.anchor(self)
        points = [source] + self.breakpoints + [target]

        # Estimate between which breakpoints the new one is being added.
        for subpath in (QLineF(points[i], points[i + 1]) for i in range(len(points) - 1)):
            dis, pos = distanceL(subpath, mousePos)
            if dis < shortest:
                point = pos
                shortest = dis
                between = subpath.p1(), subpath.p2()

        # If there is no breakpoint the new one will be appended.
        for i, breakpoint in enumerate(self.breakpoints):

            if breakpoint == between[1]:
                # In case the new breakpoint is being added between
                # the source node of this edge and the last breakpoint.
                index = i
                break

            if breakpoint == between[0]:
                # In case the new breakpoint is being added between
                # the last breakpoint and the target node of this edge.
                index = i + 1
                break

        scene = self.scene()
        scene.undostack.push(CommandEdgeBreakpointAdd(scene, self, index, point))
        return index

    def breakpointAt(self, point):
        """
        Returns the index of the breakpoint whose handle is being pressed.
        :type point: QPointF
        :rtype: int
        """
        for i in range(len(self.handles)):
            if self.handles[i].contains(point):
                return i
        return None

    def breakpointMove(self, breakpoint, mousePos):
        """
        Move the selected breakpoint.
        :type breakpoint: int
        :type mousePos: QPointF
        """
        scene = self.scene()
        self.breakpoints[breakpoint] = scene.snapToGrid(mousePos)

    def canDraw(self):
        """
        Check whether we have to draw the edge or not.
        :rtype: bool
        """
        if not self.scene():
            # No scene => probably the edge is sitting in a CommandEdgeAdd instance in the
            # undo stack of the scene but it is currently detached from it: removing this
            # check will cause an AttributeError being raised in paint() methods.
            return False

        if self.target:
            
            S = self.source
            T = self.target

            SP = self.mapFromItem(S, S.painterPath())
            TP = self.mapFromItem(T, T.painterPath())

            if SP.intersects(TP):

                # Paths are colliding: estimate whether the edge needs to be drawn or not.
                if not self.breakpoints:
                    # If there is no breakpoint then the edge line won't be visible.
                    return False

                for point in self.breakpoints:
                    # Loop through all the breakpoints: if there is at least one breakpoint
                    # which is not inside the connected shapes then draw the edges
                    if not S.contains(self.mapToItem(S, point)) and not T.contains(self.mapToItem(T, point)):
                        return True

                return False

        return True

    @staticmethod
    def createSelectionArea(pos1, pos2, angle, size):
        """
        Constructs the selection polygon between pos1 and pos2 according to the given angle.
        :type pos1: QPointF
        :type pos2: QPointF
        :type angle: float
        :type size: int
        :rtype: QPolygonF
        """
        rad = radians(angle)
        x = size / 2 * sin(rad)
        y = size / 2 * cos(rad)
        a = QPointF(+x, +y)
        b = QPointF(-x, -y)
        return QPolygonF([pos1 + a, pos1 + b, pos2 + b, pos2 + a])

    def computePath(self, source, target, points):
        """
        Returns a list of QLineF instance representing all the visible edge pieces.
        Subpaths which are obscured by the source or target shape are excluded by this method.
        :type source: AbstractNode
        :type target: AbstractNode
        :type points: list
        :rtype: list
        """
        # Get the source node painter path (the source node is always available).
        SP = self.mapFromItem(source, source.painterPath())
        TP = self.mapFromItem(target, target.painterPath()) if target else None
        # Exclude all the "subpaths" which are not visible (obscured by the shapes).
        return [x for x in (QLineF(points[i], points[i + 1]) for i in range(len(points) - 1)) \
                    if (not SP.contains(x.p1()) or not SP.contains(x.p2())) and \
                        (not TP or (not TP.contains(x.p1()) or not TP.contains(x.p2())))]

    def moveBy(self, x, y):
        """
        Move the edge by the given deltas.
        :type x: float
        :type y: float
        """
        move = QPointF(x, y)
        self.breakpoints = [p + move for p in self.breakpoints]

    def other(self, node):
        """
        Returns the opposite endpoint of the given node.
        :raise AttributeError: if the given node is not an endpoint of this edge.
        :type node: AtttributeNode
        :rtype: Node
        """
        if node is self.source:
            return self.target
        elif node is self.target:
            return self.source
        raise AttributeError('node {} is not attached to edge {}'.format(node, self))

    def updateBrush(self, selected=None, visible=None, breakpoint=None, anchor=None, **kwargs):
        """
        Perform updates on pens and brushes needed by the paint() method.
        :type selected: bool
        :type visible: bool
        :type breakpoint: int
        :type anchor: AbstractNode
        """
        noBrush = QBrush(Qt.NoBrush)
        noPen = QPen(Qt.NoPen)

        headBrush = noBrush
        headPen = noPen
        handleBrush = noBrush
        handlePen = noPen
        selectionBrush = noBrush
        pen = noPen

        if visible:
            headBrush = self.headBrushPattern
            headPen = self.headPenPattern
            pen = self.penPattern
            if selected:
                handleBrush = self.handleBrushPattern
                handlePen = self.handlePenPattern
                if breakpoint is None and anchor is None:
                    selectionBrush = self.selectionBrushPattern

        self.headBrush = headBrush
        self.headPen = headPen
        self.handleBrush = handleBrush
        self.handlePen = handlePen
        self.pen = pen
        self.selectionBrush = selectionBrush

        # FORCE CACHE REGENERATION
        self.setCacheMode(QGraphicsItem.NoCache)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

        # SCHEDULE REPAINT
        self.update(self.boundingRect())

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def hoverEnterEvent(self, hoverEvent):
        """
        Executed when the mouse enters the shape (NOT PRESSED).
        :type hoverEvent: QGraphicsSceneHoverEvent
        """
        self.setCursor(Qt.PointingHandCursor)
        super().hoverEnterEvent(hoverEvent)

    def hoverMoveEvent(self, hoverEvent):
        """
        Executed when the mouse moves over the shape (NOT PRESSED).
        :type hoverEvent: QGraphicsSceneHoverEvent
        """
        self.setCursor(Qt.PointingHandCursor)
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
        if change == AbstractEdge.ItemSelectedHasChanged:
            self.updateBrush(selected=value, visible=self.canDraw())
        return super(AbstractEdge, self).itemChange(change, value)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the selection box.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()
        mousePos = mouseEvent.pos()

        if scene.mode is DiagramMode.Idle:
            # Check first if we need to start an anchor point movement: we need to evaluate anchor
            # points first because we may be in the situation where we are trying to select the anchor
            # point, but if the code for breakpoint retrieval is executed first, no breakpoint is found
            # and hence a new one will be added upon mouseMoveEvent (even a small move will cause this).
            anchorNode = self.anchorAt(mousePos)
            if anchorNode is not None:
                scene.clearSelection()
                scene.setMode(DiagramMode.EdgeAnchorPointMove)
                self.setSelected(True)
                self.mousePressAnchorNode = anchorNode
                self.mousePressAnchorNodePos = QPointF(anchorNode.anchor(self))
                self.updateBrush(selected=True, visible=self.canDraw(), anchor=anchorNode)
            else:
                breakPoint = self.breakpointAt(mousePos)
                if breakPoint is not None:
                    scene.clearSelection()
                    scene.setMode(DiagramMode.EdgeBreakPointMove)
                    self.setSelected(True)
                    self.mousePressBreakPoint = breakPoint
                    self.mousePressBreakPointPos = QPointF(self.breakpoints[breakPoint])
                    self.updateBrush(selected=True, visible=self.canDraw(), breakpoint=breakPoint)

        self.mousePressPos = mousePos
        super().mousePressEvent(mouseEvent)

    # noinspection PyTypeChecker
    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is being moved over the item while being pressed.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()
        mousePos = mouseEvent.pos()

        if scene.mode is DiagramMode.EdgeAnchorPointMove:
            self.anchorMove(self.mousePressAnchorNode, mousePos)
            self.updateEdge()
        else:

            if scene.mode is DiagramMode.Idle:

                try:
                    # If we are still idle we didn't succeeded in selecting a breakpoint
                    # so we need to create a new one and switch the operation mode.
                    breakPoint = self.breakpointAdd(self.mousePressPos)
                except:
                    # Sometime an error is raised while creating the breakpoint... still
                    # need to figure out why, but it's not something we need to hurry to fix.
                    pass
                else:
                    scene.clearSelection()
                    scene.setMode(DiagramMode.EdgeBreakPointMove)
                    self.setSelected(True)
                    self.mousePressBreakPoint = breakPoint
                    self.mousePressBreakPointPos = QPointF(self.breakpoints[breakPoint])

            if scene.mode is DiagramMode.EdgeBreakPointMove:
                self.breakpointMove(self.mousePressBreakPoint, mousePos)
                self.updateEdge()

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the selection box.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()

        if scene.mode is DiagramMode.EdgeAnchorPointMove:
            anchorNode = self.mousePressAnchorNode
            anchorNodePos = QPointF(anchorNode.anchor(self))
            if anchorNodePos != self.mousePressAnchorNodePos:
                commandData = {'undo': self.mousePressAnchorNodePos, 'redo': anchorNodePos}
                scene.undostack.push(CommandEdgeAnchorMove(scene, self, anchorNode, commandData))
        elif scene.mode is DiagramMode.EdgeBreakPointMove:
            breakPoint = self.mousePressBreakPoint
            breakPointPos = self.breakpoints[breakPoint]
            if breakPointPos != self.mousePressBreakPointPos:
                commandData = {'undo': self.mousePressBreakPointPos, 'redo': breakPointPos}
                scene.undostack.push(CommandEdgeBreakpointMove(scene, self, breakPoint, commandData))

        scene.setMode(DiagramMode.Idle)

        self.updateEdge()

        self.mousePressAnchorNode = None
        self.mousePressAnchorNodePos = None
        self.mousePressBreakPoint = None
        self.mousePressBreakPointPos = None
        self.mousePressPos = None

        super().mouseReleaseEvent(mouseEvent)

    ####################################################################################################################
    #                                                                                                                  #
    #   GEOMETRY UPDATE                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def updateAnchors(self):
        """
        Update edge anchors (update only the polygon: the real anchor point is in the node).
        """
        source = self.source
        target = self.target
        size = self.handleSize
        if source and target:
            p = source.anchor(self)
            self.anchors[source] = QRectF(p.x() - size / 2, p.y() - size / 2, size, size)
            p = target.anchor(self)
            self.anchors[target] = QRectF(p.x() - size / 2, p.y() - size / 2, size, size)

    def updateBreakPoints(self):
        """
        Update edge breakpoints (update only the polygon: the breakpoint is created by the user).
        """
        size = self.handleSize
        points = self.breakpoints
        self.handles = [QRectF(p.x() - size / 2, p.y() - size / 2, size, size) for p in points]

    def updateZValue(self):
        """
        Update the edge Z value making sure it stays above source and target shapes (and respective labels).
        """
        source = self.source
        zValue = source.zValue() + 0.1
        if hasattr(source, 'label'):
            zValue = max(zValue, source.label.zValue())

        if self.target:
            target = self.target
            zValue = max(zValue, target.zValue())
            if hasattr(target, 'label'):
                zValue = max(zValue, target.label.zValue())

        self.setZValue(zValue)

    @abstractmethod
    def updateEdge(self, target=None):
        """
        Update the edge painter path and the selection polygon.
        :type target: QPointF
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