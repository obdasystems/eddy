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

from PyQt5.QtCore import Qt, QPointF, QLineF, QRectF
from PyQt5.QtGui import QColor, QPen, QPolygonF, QPainterPath
from PyQt5.QtWidgets import QGraphicsItem, QMenu

from eddy.core.commands import CommandEdgeBreakpointAdd, CommandEdgeBreakpointMove, CommandEdgeAnchorMove
from eddy.core.datatypes import DiagramMode
from eddy.core.functions import distanceP, distanceL
from eddy.core.items import AbstractItem


class AbstractEdge(AbstractItem):
    """
    Base class for all the diagram edges.
    """
    __metaclass__ = ABCMeta

    handleBrush = QColor(168, 168, 168, 255)
    handlePen = QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine)
    handleSize = 8
    headPen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    headBrush = QColor(0, 0, 0)
    headSize = 12
    prefix = 'e'
    selectionBrush = QColor(251, 255, 148)
    selectionSize = 6
    shapePen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    xmlname = 'edge'

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

        self.anchors = {}
        self.breakpoints = breakpoints or []
        self.handles = {}
        self.head = QPolygonF()

        self.path = QPainterPath()
        self.selection = QPainterPath()

        self.command = None
        self.mousePressPos = None
        self.selectedAP = None
        self.selectedBP = None

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

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
        Will return None if the mouse is not being pressed on an anchor.
        :type point: QPointF
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

        if not self.command:
            scene.clearSelection()
            self.setSelected(True)
            self.command = CommandEdgeAnchorMove(scene=scene, edge=self, node=node)

        scene = self.scene()
        nodePos = node.pos()
        mousePos = scene.snapToGrid(mousePos)

        path = self.mapFromItem(node, node.painterPath())
        if path.contains(mousePos):
            # mouse is inside the shape => use this position as anchor point
            pos = nodePos if distanceP(mousePos, nodePos) < 10.0 else mousePos
        else:
            # FIXME: intersection point doesn't seem to be the best we can do here
            pos = node.intersection(QLineF(mousePos, nodePos))
            # make sure the point is actually inside the shape since
            for bound in [pos, pos + QPointF(1, -1), pos + QPointF(1, 0),
                               pos + QPointF(1, 1), pos + QPointF(0, 1),
                               pos + QPointF(-1, 1), pos + QPointF(-1, 0),
                               pos + QPointF(-1, -1), pos + QPointF(0, -1)]:
                if path.contains(bound):
                    pos = bound
                    break

        if pos:
            node.setAnchor(self, pos)
            self.mousePressPos = pos
            self.updateEdge()

    def breakpointAdd(self, mousePos):
        """
        Create a new breakpoint from the given mouse position returning its index.
        :type mousePos: QPointF
        :rtype: int
        """
        index = 0
        point = None
        between = None
        shortest = self.selectionSize

        source = self.source.anchor(self)
        target = self.target.anchor(self)
        points = [source] + self.breakpoints + [target]

        # estimate between which breakpoints the new one is being added
        for subpath in (QLineF(points[i], points[i + 1]) for i in range(len(points) - 1)):
            dis, pos = distanceL(subpath, mousePos)
            if dis < shortest:
                point = pos
                shortest = dis
                between = subpath.p1(), subpath.p2()

        # if there is no breakpoint the new one will be appended
        for i, breakpoint in enumerate(self.breakpoints):

            if breakpoint == between[1]:
                # in case the new breakpoint is being added between
                # the source node of this edge and the last breakpoint
                index = i
                break

            if breakpoint == between[0]:
                # in case the new breakpoint is being added between
                # the last breakpoint and the target node of this edge
                index = i + 1
                break

        scene = self.scene()
        scene.undostack.push(CommandEdgeBreakpointAdd(scene, self, index, point))
        return index

    def breakpointAt(self, point):
        """
        Returns the index of the breakpoint whose handle is being pressed.
        Will return None if the mouse is not being pressed on a handle.
        :type point: QPointF
        :rtype: int
        """
        for k, v, in self.handles.items():
            if v.contains(point):
                return k
        return None

    def breakpointMove(self, breakpoint, mousePos):
        """
        Move the selected breakpoint.
        :type breakpoint: int
        :type mousePos: QPointF
        """
        scene = self.scene()

        if not self.command:
            scene.clearSelection()
            self.setSelected(True)
            self.command = CommandEdgeBreakpointMove(scene=scene, edge=self, index=breakpoint)

        self.breakpoints[breakpoint] = scene.snapToGrid(mousePos)
        self.updateEdge()

    def canDraw(self):
        """
        Check whether we have to draw the edge or not.
        :rtype: bool
        """
        if not self.scene():
            # no scene => probably the edge is sitting in a CommandEdgeAdd instance in the
            # undo stack of the scene but it is currently detached from it: removing this
            # check will cause an AttributeError being raised in paint() methods.
            return False

        if self.target:

            sourcePath = self.mapFromItem(self.source, self.source.painterPath())
            targetPath = self.mapFromItem(self.target, self.target.painterPath())

            if sourcePath.intersects(targetPath):

                # shapes are colliding: estimate whether the edge needs to be drawn or not
                if not self.breakpoints:
                    # if there is no breakpoint then the edge
                    # line won't be visible so skip the drawing
                    return False

                for point in self.breakpoints:
                    # loop through all the breakpoints: if there is at least one breakpoint
                    # which is not inside the connected shapes then draw the edges
                    if not self.source.contains(self.mapToItem(self.source, point)) and \
                       not self.target.contains(self.mapToItem(self.target, point)):
                        return True

                return False

        return True

    def computePath(self, source, target, points):
        """
        Returns a list of QLineF instance representing all the visible edge pieces.
        Subpaths which are obscured by the source or target shape are excluded by this method.
        :type source: AbstractNode
        :type target: AbstractNode
        :type points: list
        :rtype: list
        """
        # get the source node painter path (the source node is always available)
        sourcePP = self.mapFromItem(source, source.painterPath())
        targetPP = self.mapFromItem(target, target.painterPath()) if target else None

        # exclude all the "subpaths" which are not visible (obscured by the shapes)
        return [x for x in (QLineF(points[i], points[i + 1]) for i in range(len(points) - 1)) \
                    if (not sourcePP.contains(x.p1()) or not sourcePP.contains(x.p2())) and \
                        (not targetPP or (not targetPP.contains(x.p1()) or not targetPP.contains(x.p2())))]

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

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the selection box.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()

        if scene.mode is DiagramMode.Idle:
            # check first if we need to start an anchor point movement: we need to evaluate anchor
            # points first because we may be in the situation where we are trying to select the anchor
            # point, but if the code for breakpoint retrieval is executed first, no breakpoint is found
            # and hence a new one will be added upon mouseMoveEvent (even a small move will cause this)
            self.selectedAP = self.anchorAt(mouseEvent.pos())
            if self.selectedAP is not None:
                scene.setMode(DiagramMode.EdgeAnchorPointMove)
            else:
                # if no anchor point is selected then check for a breakpoint
                self.selectedBP = self.breakpointAt(mouseEvent.pos())
                if self.selectedBP is not None:
                    scene.setMode(DiagramMode.EdgeBreakPointMove)

        # always track the press position since it's need by other events to compute deltas
        self.mousePressPos = mouseEvent.pos()
        super().mousePressEvent(mouseEvent)

    # noinspection PyTypeChecker
    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is being moved over the item while being pressed.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()

        if scene.mode is DiagramMode.EdgeAnchorPointMove:
            self.anchorMove(self.selectedAP, mouseEvent.pos())
        else:

            if scene.mode is DiagramMode.Idle:

                try:
                    # if we are still idle we didn't succeeded in selecting a breakpoint
                    # so we need to create a new one and switch the operation mode
                    self.selectedBP = self.breakpointAdd(self.mousePressPos)
                except TypeError:
                    # FIXME: sometime TypeError is raised when computing the breakpoint position:
                    # if self.breakpoints[i] == between[1]:
                    #   TypeError: 'NoneType' object is not subscriptable
                    pass
                else:
                    scene.setMode(DiagramMode.EdgeBreakPointMove)

            if scene.mode is DiagramMode.EdgeBreakPointMove:
                self.breakpointMove(self.selectedBP, mouseEvent.pos())

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the selection box.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()

        if scene.mode is DiagramMode.EdgeAnchorPointMove:
            if self.command:
                self.command.end()
                scene.undostack.push(self.command)
        elif scene.mode is DiagramMode.EdgeBreakPointMove:
            if self.command:
                self.command.end(scene.snapToGrid(mouseEvent.pos()))
                scene.undostack.push(self.command)

        scene.setMode(DiagramMode.Idle)

        self.selectedAP = None
        self.selectedBP = None
        self.mousePressPos = None
        self.command = None
        self.command = None
        self.updateEdge()

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
        size = self.handleSize
        if self.source and self.target:
            p = self.source.anchor(self)
            self.anchors[self.source] = QRectF(p.x() - size / 2, p.y() - size / 2, size, size)
            p = self.target.anchor(self)
            self.anchors[self.target] = QRectF(p.x() - size / 2, p.y() - size / 2, size, size)

    def updateHandles(self):
        """
        Update edge handles.
        """
        size = self.handleSize
        points = self.breakpoints
        self.handles = {points.index(p): QRectF(p.x() - size / 2, p.y() - size / 2, size, size) for p in points}

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