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
from itertools import permutations

from PyQt5 import QtCore
from PyQt5 import QtGui

from eddy.core.commands.edges import CommandEdgeAnchorMove
from eddy.core.commands.edges import CommandEdgeBreakpointAdd
from eddy.core.commands.edges import CommandEdgeBreakpointMove
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.functions.geometry import distance, projection
from eddy.core.functions.misc import snap
from eddy.core.items.common import AbstractItem
from eddy.core.polygon import Polygon


class AbstractEdge(AbstractItem):
    """
    Base class for all the diagram edges.
    """
    __metaclass__ = ABCMeta

    Prefix = 'e'

    def __init__(self, source, target=None, breakpoints=None, **kwargs):
        """
        Initialize the edge.
        :type source: AbstractNode
        :type target: AbstractNode
        :type breakpoints: list
        """
        super().__init__(**kwargs)

        self.source = source
        self.target = target

        self.anchors = {} # {AbstractNode: Polygon}
        self.breakpoints = breakpoints or [] # [QtCore.QPointF]
        self.handles = [] # [Polygon]
        self.head = Polygon(QtGui.QPolygonF())
        self.path = Polygon(QtGui.QPainterPath())
        self.selection = Polygon(QtGui.QPainterPath())

        self.mp_AnchorNode = None
        self.mp_AnchorNodePos = None
        self.mp_BreakPoint = None
        self.mp_BreakPointPos = None
        self.mp_Pos = None

        self.setAcceptHoverEvents(True)
        self.setCacheMode(AbstractItem.DeviceCoordinateCache)
        self.setFlag(AbstractItem.ItemIsSelectable, True)

    #############################################
    #   INTERFACE
    #################################

    def anchorAt(self, point):
        """
        Returns the key of the anchor whose handle is being pressed.
        :type point: AbstractNode
        """
        size = QtCore.QPointF(3, 3)
        area = QtCore.QRectF(point - size, point + size)
        for k, v, in self.anchors.items():
            if v.geometry().intersects(area):
                return k
        return None

    def anchorMove(self, node, mousePos):
        """
        Move the selected anchor point.
        :type node: AbstractNode
        :type mousePos: QtCore.QPointF
        """
        nodePos = node.pos()
        snapToGrid = self.session.action('toggle_grid').isChecked()
        mousePos = snap(mousePos, self.diagram.GridSize, snapToGrid)
        path = self.mapFromItem(node, node.painterPath())
        if path.contains(mousePos):
            # Mouse is inside the shape => use this position as anchor point.
            pos = nodePos if distance(mousePos, nodePos) < 10.0 else mousePos
        else:
            # Mouse is outside the shape => use the intersection point as anchor point.
            pos = node.intersection(QtCore.QLineF(mousePos, nodePos))
            for pair in set(permutations([-1, -1, 0, 0, 1, 1], 2)):
                p = pos + QtCore.QPointF(*pair)
                if path.contains(p):
                    pos = p
                    break

        node.setAnchor(self, pos)

    def breakPointAdd(self, mousePos):
        """
        Create a new breakpoint from the given mouse position returning its index.
        :type mousePos: QtCore.QPointF
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
        for subpath in (QtCore.QLineF(points[i], points[i + 1]) for i in range(len(points) - 1)):
            dis, pos = projection(subpath, mousePos)
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

        self.session.undostack.push(CommandEdgeBreakpointAdd(self.diagram, self, index, point))
        return index

    def breakPointAt(self, point):
        """
        Returns the index of the breakpoint whose handle is being pressed.
        :type point: QtCore.QPointF
        :rtype: int
        """
        size = QtCore.QPointF(3, 3)
        area = QtCore.QRectF(point - size, point + size)
        for polygon in self.handles:
            if polygon.geometry().intersects(area):
                return self.handles.index(polygon)
        return None

    def breakPointMove(self, breakpoint, mousePos):
        """
        Move the selected breakpoint.
        :type breakpoint: int
        :type mousePos: QtCore.QPointF
        """
        snapToGrid = self.session.action('toggle_grid').isChecked()
        self.breakpoints[breakpoint] = snap(mousePos, self.diagram.GridSize, snapToGrid)

    def canDraw(self):
        """
        Check whether we have to draw the edge or not.
        :rtype: bool
        """
        if not self.diagram:
            return False

        if self.target:
            source = self.source
            target = self.target
            sp = self.mapFromItem(source, source.painterPath())
            tp = self.mapFromItem(target, target.painterPath())
            if sp.intersects(tp):
                for point in self.breakpoints:
                    if not source.contains(self.mapToItem(source, point)):
                        if not target.contains(self.mapToItem(target, point)):
                            return True
                return False
        return True

    @abstractmethod
    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        pass

    def computePath(self, source, target, points):
        """
        Returns a list of QtCore.QLineF instance representing all the visible edge pieces.
        Subpaths which are obscured by the source or target shape are excluded by this method.
        :type source: AbstractNode
        :type target: AbstractNode
        :type points: list
        :rtype: list
        """
        # Get the source node painter path (the source node is always available).
        sp = self.mapFromItem(source, source.painterPath())
        tp = self.mapFromItem(target, target.painterPath()) if target else None
        # Exclude all the "subpaths" which are not visible (obscured by the shapes).
        return [x for x in (QtCore.QLineF(points[i], points[i + 1]) for i in range(len(points) - 1)) \
                    if (not sp.contains(x.p1()) or not sp.contains(x.p2())) and \
                        (not tp or (not tp.contains(x.p1()) or not tp.contains(x.p2())))]

    def isSwapAllowed(self):
        """
        Returns True if this edge can be swapped, False otherwise.
        :rtype: bool
        """
        return self.project.profile.check(self.target, self, self.source).isValid()

    def moveBy(self, x, y):
        """
        Move the edge by the given deltas.
        :type x: float
        :type y: float
        """
        self.breakpoints = [p + QtCore.QPointF(x, y) for p in self.breakpoints]

    def other(self, node):
        """
        Returns the opposite endpoint of the given node.
        :raise AttributeError: if the given node is not an endpoint of this edge.
        :type node: AttributeNode
        :rtype: Node
        """
        if node is self.source:
            return self.target
        elif node is self.target:
            return self.source
        raise AttributeError('node {0} is not attached to edge {1}'.format(node, self))

    def updateEdge(self, selected=None, visible=None, breakpoint=None, anchor=None, **kwargs):
        """
        Update the current edge.
        :type selected: bool
        :type visible: bool
        :type breakpoint: int
        :type anchor: AbstractNode
        """
        if selected is None:
            selected = self.isSelected()
        if visible is None:
            visible = self.canDraw()

        source = self.source
        target = self.target

        # ANCHORS (GEOMETRY) --> NB: THE POINTS ARE IN THE ENDPOINTS
        if source and target:
            p = source.anchor(self)
            self.anchors[source] = Polygon(QtCore.QRectF(p.x() - 4, p.y() - 4, 8, 8))
            p = target.anchor(self)
            self.anchors[target] = Polygon(QtCore.QRectF(p.x() - 4, p.y() - 4, 8, 8))

        # BREAKPOINTS (GEOMETRY)
        self.handles = [Polygon(QtCore.QRectF(p.x() - 4, p.y() - 4, 8, 8)) for p in self.breakpoints]

        # ANCHORS + BREAKPOINTS + SELECTION (BRUSH + PEN)
        anchorBrush = QtGui.QBrush(QtCore.Qt.NoBrush)
        anchorPen = QtGui.QPen(QtCore.Qt.NoPen)
        handleBrush = QtGui.QBrush(QtCore.Qt.NoBrush)
        handlePen = QtGui.QPen(QtCore.Qt.NoPen)
        selectionBrush = QtGui.QBrush(QtCore.Qt.NoBrush)
        if visible and selected:
            anchorBrush = QtGui.QBrush(QtGui.QColor(66, 165, 245, 255))
            anchorPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
            handleBrush = QtGui.QBrush(QtGui.QColor(66, 165, 245, 255))
            handlePen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
            if breakpoint is None and anchor is None:
                selectionBrush = QtGui.QBrush(QtGui.QColor(251, 255, 148, 255))
        for polygon in self.anchors.values():
            polygon.setBrush(anchorBrush)
            polygon.setPen(anchorPen)
        for polygon in self.handles:
            polygon.setBrush(handleBrush)
            polygon.setPen(handlePen)
        self.selection.setBrush(selectionBrush)

        # Z-VALUE (DEPTH)
        zValue = source.zValue() + 0.1
        if source.label:
            zValue = max(zValue, source.label.zValue())
        if target:
            zValue = max(zValue, target.zValue())
            if target.label:
                zValue = max(zValue, target.label.zValue())
        self.setZValue(zValue)

        # FORCE CACHE REGENERATION
        self.setCacheMode(AbstractItem.NoCache)
        self.setCacheMode(AbstractItem.DeviceCoordinateCache)

        # SCHEDULE REPAINT
        self.update(self.boundingRect())

    #############################################
    #   EVENTS
    #################################

    def hoverEnterEvent(self, hoverEvent):
        """
        Executed when the mouse enters the shape (NOT PRESSED).
        :type hoverEvent: QGraphicsSceneHoverEvent
        """
        self.setCursor(QtCore.Qt.PointingHandCursor)
        super().hoverEnterEvent(hoverEvent)

    def hoverMoveEvent(self, hoverEvent):
        """
        Executed when the mouse moves over the shape (NOT PRESSED).
        :type hoverEvent: QGraphicsSceneHoverEvent
        """
        self.setCursor(QtCore.Qt.PointingHandCursor)
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
        if change == AbstractEdge.ItemSelectedHasChanged:
            self.updateEdge(selected=value)
        return super(AbstractEdge, self).itemChange(change, value)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the selection box.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        self.mp_Pos = mouseEvent.pos()

        if self.diagram.mode is DiagramMode.Idle:
            # Check first if we need to start an anchor point movement: we need
            # to evaluate anchor points first because we may be in the situation
            # where we are trying to select the anchor point, but if the code for
            # breakpoint retrieval is executed first, no breakpoint is found
            # and hence a new one will be added upon mouseMoveEvent (even a small
            # move will cause this).
            anchorNode = self.anchorAt(self.mp_Pos)
            if anchorNode is not None:
                self.diagram.clearSelection()
                self.diagram.setMode(DiagramMode.EdgeAnchorMove)
                self.setSelected(True)
                self.mp_AnchorNode = anchorNode
                self.mp_AnchorNodePos = QtCore.QPointF(anchorNode.anchor(self))
                self.updateEdge(selected=True, anchor=anchorNode)
            else:
                breakPoint = self.breakPointAt(self.mp_Pos)
                if breakPoint is not None:
                    self.diagram.clearSelection()
                    self.diagram.setMode(DiagramMode.EdgeBreakPointMove)
                    self.setSelected(True)
                    self.mp_BreakPoint = breakPoint
                    self.mp_BreakPointPos = QtCore.QPointF(self.breakpoints[breakPoint])
                    self.updateEdge(selected=True, breakpoint=breakPoint)

        super().mousePressEvent(mouseEvent)

    # noinspection PyTypeChecker
    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is being moved over the item while being pressed.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        mousePos = mouseEvent.pos()

        if self.diagram.mode is DiagramMode.EdgeAnchorMove:
            self.anchorMove(self.mp_AnchorNode, mousePos)
            self.updateEdge()
        else:

            if self.diagram.mode is DiagramMode.Idle:

                try:
                    # If we are still idle we didn't succeeded in
                    # selecting a breakpoint so we need to create
                    # a new one and switch the operational mode.
                    breakPoint = self.breakPointAdd(self.mp_Pos)
                except:
                    pass
                else:
                    self.diagram.clearSelection()
                    self.diagram.setMode(DiagramMode.EdgeBreakPointMove)
                    self.setSelected(True)
                    self.mp_BreakPoint = breakPoint
                    self.mp_BreakPointPos = QtCore.QPointF(self.breakpoints[breakPoint])

            if self.diagram.mode is DiagramMode.EdgeBreakPointMove:
                self.breakPointMove(self.mp_BreakPoint, mousePos)
                self.updateEdge()

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the selection box.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if self.diagram.mode is DiagramMode.EdgeAnchorMove:
            anchorNode = self.mp_AnchorNode
            anchorNodePos = QtCore.QPointF(anchorNode.anchor(self))
            if anchorNodePos != self.mp_AnchorNodePos:
                data = {'undo': self.mp_AnchorNodePos, 'redo': anchorNodePos}
                self.session.undostack.push(CommandEdgeAnchorMove(self.diagram, self, anchorNode, data))
        elif self.diagram.mode is DiagramMode.EdgeBreakPointMove:
            breakPoint = self.mp_BreakPoint
            breakPointPos = self.breakpoints[breakPoint]
            if breakPointPos != self.mp_BreakPointPos:
                data = {'undo': self.mp_BreakPointPos, 'redo': breakPointPos}
                self.session.undostack.push(CommandEdgeBreakpointMove(self.diagram, self, breakPoint, data))

        self.mp_AnchorNode = None
        self.mp_AnchorNodePos = None
        self.mp_BreakPoint = None
        self.mp_BreakPointPos = None
        self.mp_Pos = None

        self.diagram.setMode(DiagramMode.Idle)
        self.updateEdge()