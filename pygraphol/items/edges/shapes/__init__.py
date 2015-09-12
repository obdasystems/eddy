# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  pyGraphol: a python design tool for the Graphol language.             #
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
##########################################################################
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Informatica e Sistemistica "A.Ruberti" at Sapienza    #
#  University of Rome: http://www.dis.uniroma1.it/~graphol/:             #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Marco Console <console@dis.uniroma1.it>                          #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#                                                                        #
##########################################################################


import math

from functools import partial
from pygraphol.commands import CommandEdgeBreakpointAdd, CommandEdgeBreakpointMove, CommandEdgeBreakpointDel
from pygraphol.functions import distance
from PyQt5.QtCore import QPointF, Qt, QLineF, QRectF
from PyQt5.QtGui import QPolygonF, QPainter, QPen, QColor, QPainterPath, QIcon
from PyQt5.QtWidgets import QGraphicsItem, QMenu, QAction


class SubPath(object):
    """
    This class is used to store edge subpath data.
    """
    # selection box size
    size = 6.0

    def __init__(self, source, target):
        """
        Initialize the edge subpath.
        :type source: QPointF
        :type target: QPointF
        :param source: the source point.
        :param target: the end point.
        """
        self.source = source
        self.target = target

        # create the edge subpath line
        self.line = QLineF(self.source, self.target)

        # create the edge subpath selection box
        aa = self.line.angle() * math.pi / 180
        dx = self.size / 2 * math.sin(aa)
        dy = self.size / 2 * math.cos(aa)
        p1 = QPointF(+dx, +dy)
        p2 = QPointF(-dx, -dy)
        self.selection = QPolygonF([self.line.p1() + p1, self.line.p1() + p2, self.line.p2() + p2, self.line.p2() + p1])

    def distance(self, point):
        """
        Returns a tuple containing the distance between the subpath and the given point, and the intersection point.
        :type point: QPointF
        :param point: the point from which to compute the distance/intersection.
        :rtype: tuple
        """
        x1 = self.line.x1()
        y1 = self.line.y1()
        x2 = self.line.x2()
        y2 = self.line.y2()
        x3 = point.x()
        y3 = point.y()

        kk = ((y2 - y1) * (x3 - x1) - (x2 - x1) * (y3 - y1)) / (math.pow(y2 - y1, 2) + math.pow(x2 - x1, 2))
        x4 = x3 - kk * (y2 - y1)
        y4 = y3 + kk * (x2 - x1)

        p1 = QPointF(x3, y3)
        p2 = QPointF(x4, y4)

        return distance(p1, p2), p2


class EdgeShape(QGraphicsItem):
    """
    Base class for all the Edge shapes.
    """
    size = 12.0

    handleSize = +8.0
    handleBrush = QColor(79, 195, 247, 255)
    handlePen = QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine)

    headPen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    headBrush = QColor(0, 0, 0)

    linePen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

    selectionPen = QPen(QColor(251, 255, 148), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    selectionBrush = QColor(251, 255, 148)

    tailPen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    tailBrush = QColor(0, 0, 0)

    def __init__(self, item, **kwargs):
        """
        Initialize the arrow shape.
        :param item: the edge attached to this shape.
        """
        self.item = item
        self.head = QPolygonF()
        self.tail = None
        self.breakpoints = kwargs.pop('breakpoints', [])
        self.handles = {}
        self.anchors = {}
        self.path = []

        self.command = None
        self.mousePressPos = None
        self.selectedBreakpointIndex = None

        kwargs.pop('id', None)
        kwargs.pop('source', None)
        kwargs.pop('target', None)

        super().__init__(**kwargs)

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

    ################################################### PROPERTIES #####################################################

    @property
    def edge(self):
        """
        Returns the edge this shape is attached to.
        :rtype: Edge
        """
        return self.item

    ################################################## EVENT HANDLERS ##################################################

    def contextMenuEvent(self, menuEvent):
        """
        Bring up the context menu for the given node.
        :param menuEvent: the context menu event instance.
        """
        self.scene().clearSelection()
        self.setSelected(True)
        contextMenu = self.contextMenu(menuEvent.pos())
        contextMenu.exec_(menuEvent.screenPos())

    def hoverEnterEvent(self, moveEvent):
        """
        Executed when the mouse enters the shape (NOT PRESSED).
        :param moveEvent: the move event.
        """
        self.setCursor(Qt.PointingHandCursor)
        super().hoverEnterEvent(moveEvent)

    def hoverMoveEvent(self, moveEvent):
        """
        Executed when the mouse moves over the shape (NOT PRESSED).
        :param moveEvent: the move event.
        """
        self.setCursor(Qt.PointingHandCursor)
        super().hoverMoveEvent(moveEvent)

    def hoverLeaveEvent(self, moveEvent):
        """
        Executed when the mouse leaves the shape (NOT PRESSED).
        :param moveEvent: the move event.
        """
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the selection box.
        :param mouseEvent: the mouse event instance.
        """
        self.selectedBreakpointIndex = self.breakpointIndex(mouseEvent.pos())
        self.mousePressPos = mouseEvent.pos()
        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is being moved over the item while being pressed.
        :param mouseEvent: the mouse move event instance.
        """
        scene = self.scene()
        index = self.selectedBreakpointIndex

        if scene.mode == scene.MoveItem:

            if index is None:
                index = self.breakpointAdd(self.mousePressPos)
                self.selectedBreakpointIndex = index
                self.mousePressPos = None

            if not self.command:
                scene.clearSelection()
                self.setSelected(True)
                self.command = CommandEdgeBreakpointMove(edge=self.edge, index=index)

            # show the visual move
            self.breakpoints[index] = scene.snapToGrid(mouseEvent.pos())
            self.updateEdge()

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the selection box.
        :param mouseEvent: the mouse event instance.
        """
        scene = self.scene()
        if scene.mode == scene.MoveItem:
            if self.command:
                self.command.end(scene.snapToGrid(mouseEvent.pos()))
                scene.undoStack.push(self.command)

        self.selectedBreakpointIndex = None
        self.mousePressPos = None
        self.command = None
        self.updateEdge()

        super().mouseReleaseEvent(mouseEvent)

    ################################################ AUXILIARY METHODS #################################################

    def breakpointAdd(self, mousePos):
        """
        Create a new breakpoint from the given mouse position.
        :param mousePos: the position from where to create the breakpoint.
        :return: the index of the new breakpoint
        """
        index = 0
        point = None
        between = None
        shortest = SubPath.size

        # calculate the shortest distance between the click point
        # and all the subpaths od the edge in order to estimate
        # which subpath needs to be splitted by the new breakpoint
        for subpath in self.path:
            dis, pos = subpath.distance(mousePos)
            if dis < shortest:
                point = pos
                shortest = dis
                between = subpath.source, subpath.target

        # if there is no breakpoint the new one will be appended
        for i in range(len(self.breakpoints)):

            if self.breakpoints[i] == between[1]:
                # in case the new breakpoint is being added between
                # the source node of this edge and the last breakpoint
                index = i
                break

            if self.breakpoints[i] == between[0]:
                # in case the new breakpoint is being added between
                # the last breakpoint and the target node of this edge
                index = i + 1
                break

        scene = self.scene()
        scene.undoStack.push(CommandEdgeBreakpointAdd(edge=self.edge, index=index, point=point))
        return index

    def breakpointDel(self, breakpoint):
        """
        Remove the given breakpoint from the edge.
        :param breakpoint: the breakpoint index.
        """
        if 0 <= breakpoint < len(self.breakpoints):
            scene = self.scene()
            scene.undoStack.push(CommandEdgeBreakpointDel(self.edge, breakpoint))

    def breakpointIndex(self, point):
        """
        Returns the index of the breakpoint whose handle is being pressed.
        Will return None if the mouse is not being pressed on a handle.
        :type point: QPointF
        :param point: the point where to look for a handle.
        :rtype: int
        """
        for k, v, in self.handles.items():
            if v.contains(point):
                return k
        return None

    def canDraw(self):
        """
        Check whether we have to draw the edge or not.
        :return: True if we need to draw the edge, False otherwise.
        """
        if self.edge.target:

            sourcePath = self.mapFromItem(self.edge.source.shape, self.edge.source.shape.painterPath())
            targetPath = self.mapFromItem(self.edge.target.shape, self.edge.target.shape.painterPath())

            if sourcePath.intersects(targetPath):

                # shapes are colliding: estimate whether the edge needs to be drawn or not
                if not self.breakpoints:
                    # if there is no breakpoint then the edge
                    # line won't be visible so skip the drawing
                    return False

                for point in self.breakpoints:
                    # loop through all the breakpoints: if there is at least one breakpoint
                    # which is not inside the connected shapes then draw the edges
                    if not self.edge.source.shape.contains(self.mapToItem(self.edge.source.shape, point)) and \
                       not self.edge.target.shape.contains(self.mapToItem(self.edge.target.shape, point)):
                        return True

                return False

        return True

    def contextMenu(self, pos):
        """
        Returns the basic edge context menu.
        :rtype: QMenu
        """
        menu = QMenu()
        breakpoint = self.breakpointIndex(pos)
        if breakpoint is not None:
            action = QAction(QIcon(':/icons/delete'), 'Remove breakpoint', self.scene())
            action.triggered.connect(partial(self.breakpointDel, breakpoint=breakpoint))
            menu.addAction(action)
        else:
            menu.addAction(self.scene().actionItemDelete)
        return menu

    def intersections(self, shape):
        """
        Returns the intersections with the given shape: the return value is a list of tuples where
        the first element of each tuple represents the index of the subpath where the intersection
        happened and the second point is the intersected point in scene coordinates.
        :param shape: the shape whose intersection needs to be calculated.
        :rtype: list
        """
        collection = []
        for i in range(len(self.path)):
            subpath = self.path[i]
            subline = subpath.line
            intersections = shape.intersections(subline)
            for pos in intersections:
                collection.append((i, pos))
        return collection

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used to detect the collision between items in the graphics scene).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        if self.path:
            subpath = self.path[0]
            path.moveTo(subpath.line.p1())
            for subpath in self.path:
                path.lineTo(subpath.line.p2())
        path.addPolygon(self.head)
        return path

    ##################################################### GEOMETRY #####################################################

    def shape(self):
        """
        Return the shape of the Edge.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        for subpath in self.path:
            path.addPolygon(subpath.selection)
        path.addPolygon(self.head)
        return path

    def boundingRect(self):
        """
        Returns the shape bounding rect.
        :rtype: QRectF
        """
        listX = [point.x() for subpath in self.path for point in subpath.selection]
        listY = [point.y() for subpath in self.path for point in subpath.selection]
        x1, x2 = min(listX), max(listX)
        y1, y2 = min(listY), max(listY)
        return QRectF(QPointF(x1, y1), QPointF(x2, y2))

    ################################################# GEOMETRY UPDATE ##################################################

    def updateEdge(self, target=None):
        """
        Update the Edge line.
        :type target: QPointF
        :param target: the Edge new end point (when there is no endNode attached yet).
        """
        raise NotImplementedError('method `updateEdge` must be implemented in inherited class')

    def updateAnchors(self):
        """
        Update edge anchors (update only the polygon: the real anchor point is in the node).
        """
        size = self.handleSize
        if self.edge.source and self.edge.target:
            p = self.edge.source.shape.anchor(self)
            self.anchors[self.edge.source.shape] = QRectF(p.x() - size / 2, p.y() - size / 2, size, size)
            p = self.edge.target.shape.anchor(self)
            self.anchors[self.edge.target.shape] = QRectF(p.x() - size / 2, p.y() - size / 2, size, size)

    def updateHandles(self):
        """
        Update edge handles.
        """
        size = self.handleSize
        points = self.breakpoints
        self.handles = {points.index(p): QRectF(p.x() - size / 2, p.y() - size / 2, size, size) for p in points}

    def updateHead(self):
        """
        Update the Edge head polygon.
        """
        raise NotImplementedError('method `updateHead` must be implemented in inherited class')

    def updatePath(self, target=None):
        """
        Update edge path according to the source/target nodes and breakpoints.
        :type target: QPointF
        :param target: the endpoint of this edge.
        """
        source = self.edge.source.shape.anchor(self)
        target = target or self.edge.target.shape.anchor(self)
        points = [source] + self.breakpoints + [target]
        self.path = [SubPath(points[i], points[i + 1]) for i in range(len(points) - 1)]

    def updateZValue(self):
        """
        Update the edge Z value making sure it stays above source and target shapes (and respective labels).
        """
        source = self.edge.source.shape
        zValue = source.zValue() + 0.1
        if source.label:
            zValue = max(zValue, source.label.zValue())

        if self.edge.target:
            target = self.edge.target.shape
            zValue = max(zValue, target.zValue())
            if target.label:
                zValue = max(zValue, target.label.zValue())

        self.setZValue(zValue)

    ################################################### ITEM DRAWING ###################################################

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        :param painter: the active painter.
        :param option: the style option for this item.
        :param widget: the widget that is being painted on.
        """
        scene = self.scene()

        # Draw the line
        for subpath in self.path:

            # Draw the selection polygon if needed
            if scene.mode == scene.MoveItem and self.isSelected():
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(self.selectionPen)
                painter.setBrush(self.selectionBrush)
                painter.drawPolygon(subpath.selection)

            # Draw the edge line
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(self.linePen)
            painter.drawLine(subpath.line)

        # Draw the head polygon
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.headPen)
        painter.setBrush(self.headBrush)
        painter.drawPolygon(self.head)

        # Draw breakpoint handles
        if self.isSelected():
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(self.handlePen)
            painter.setBrush(self.handleBrush)
            for rect in self.handles.values():
                painter.drawEllipse(rect)


from pygraphol.items.edges.shapes.arrow import Arrow
from pygraphol.items.edges.shapes.squared_arrow import SquaredArrow
from pygraphol.items.edges.shapes.named_arrow import NamedArrow


__all__ = [
    'Arrow',
    'SquaredArrow',
    'NamedArrow'
]