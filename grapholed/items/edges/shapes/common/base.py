# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Grapholed: a diagramming software for the Graphol language.           #
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


from functools import partial
from grapholed.commands import CommandEdgeAnchorMove
from grapholed.commands import CommandEdgeBreakpointAdd, CommandEdgeBreakpointMove, CommandEdgeBreakpointDel
from grapholed.functions import distanceP, distanceL
from PyQt5.QtCore import QPointF, Qt, QLineF, QRectF
from PyQt5.QtGui import QPolygonF, QPen, QColor, QIcon, QPainterPath
from PyQt5.QtWidgets import QGraphicsItem, QMenu, QAction


class AbstractEdgeShape(QGraphicsItem):
    """
    This is the base class for all the edge shapes.
    """
    handleBrush = QColor(79, 195, 247, 255)
    handlePen = QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine)
    handleSize = 8

    edgePen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

    selectionBrush = QColor(251, 255, 148)
    selectionSize = 6

    def __init__(self, item, breakpoints=None, **kwargs):
        """
        Initialize the shape.
        :param item: the edge attached to this shape.
        :param breakpoints: the breakpoints of this edge.
        """
        self.item = item
        self.head = QPolygonF()
        self.breakpoints = breakpoints or []
        self.handles = {}
        self.anchors = {}

        self.path = QPainterPath()
        self.selection = QPainterPath()

        self.command = None
        self.mousePressPos = None
        self.selectedAP = None
        self.selectedBP = None

        kwargs.pop('id', None)

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
        scene = self.scene()
        scene.clearSelection()

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
        self.selectedAP = self.anchorAt(mouseEvent.pos())
        self.selectedBP = self.breakpointAt(mouseEvent.pos())
        self.mousePressPos = mouseEvent.pos()
        super().mousePressEvent(mouseEvent)

    # noinspection PyTypeChecker
    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is being moved over the item while being pressed.
        :param mouseEvent: the mouse move event instance.
        """
        scene = self.scene()

        if scene.mode == scene.MoveItem:

            if self.selectedAP is not None:
                self.anchorMove(self.selectedAP, mouseEvent.pos())
            else:
                if self.selectedBP is None:
                    self.selectedBP = self.breakpointAdd(self.mousePressPos)
                self.breakpointMove(self.selectedBP, mouseEvent.pos())

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the selection box.
        :param mouseEvent: the mouse event instance.
        """
        scene = self.scene()
        if scene.mode == scene.MoveItem:

            if self.selectedAP is not None:
                if self.command:
                    self.command.end()
                    scene.undoStack.push(self.command)

            if self.selectedBP is not None:
                if self.command:
                    self.command.end(scene.snapToGrid(mouseEvent.pos()))
                    scene.undoStack.push(self.command)

        self.selectedAP = None
        self.selectedBP = None
        self.mousePressPos = None
        self.command = None
        self.command = None
        self.updateEdge()

        super().mouseReleaseEvent(mouseEvent)

    ################################################ AUXILIARY METHODS #################################################

    def anchorAt(self, point):
        """
        Returns the key of the anchor whose handle is being pressed.
        Will return None if the mouse is not being pressed on an anchor.
        :param point: the point where to look for an anchor.
        """
        for k, v, in self.anchors.items():
            if v.contains(point):
                return k
        return None

    def anchorMove(self, shape, mousePos):
        """
        Move the selected anchor point.
        :param shape: the shape whose anchor point is being moved.
        :param mousePos: the current mouse position.
        """
        scene = self.scene()

        if not self.command:
            scene.clearSelection()
            self.setSelected(True)
            self.command = CommandEdgeAnchorMove(edge=self.edge, shape=shape)
        
        pos = None
        path = self.mapFromItem(shape, shape.painterPath())
        scene = self.scene()
        mousePos = scene.snapToGrid(mousePos)
        if path.contains(mousePos):
            epsilon = 10.0
            magnet = self.mapFromItem(shape, shape.center())
            pos = magnet if distanceP(mousePos, magnet) < epsilon else mousePos
        else:
            # still move the anchor but make sure it stays on the border of the shape
            p1 = QPointF(mousePos.x(), self.mousePressPos.y())
            p2 = QPointF(self.mousePressPos.x(), mousePos.y())
            p3 = QPointF(self.mousePressPos)

            for p in (p1, p2, p3):
                if path.contains(p):
                    pos = p
                    break

        if pos:
            shape.setAnchor(self, pos)
            self.mousePressPos = pos
            self.updateEdge()

    def breakpointAdd(self, mousePos):
        """
        Create a new breakpoint from the given mouse position.
        :param mousePos: the position where to create the breakpoint.
        :return: the index of the new breakpoint.
        :rtype: int
        """
        index = 0
        point = None
        between = None
        shortest = self.selectionSize

        source = self.edge.source.shape.anchor(self)
        target = self.edge.target.shape.anchor(self)
        points = [source] + self.breakpoints + [target]

        # estimate between which breakpoints the new one is being added
        for subpath in (QLineF(points[i], points[i + 1]) for i in range(len(points) - 1)):
            dis, pos = distanceL(subpath, mousePos)
            if dis < shortest:
                point = pos
                shortest = dis
                between = subpath.p1(), subpath.p2()

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

    def breakpointAt(self, point):
        """
        Returns the index of the breakpoint whose handle is being pressed.
        Will return None if the mouse is not being pressed on a handle.
        :param point: the point where to look for a handle.
        :rtype: int
        """
        for k, v, in self.handles.items():
            if v.contains(point):
                return k
        return None

    def breakpointDel(self, breakpoint):
        """
        Remove the given breakpoint from the edge.
        :param breakpoint: the breakpoint index.
        """
        if 0 <= breakpoint < len(self.breakpoints):
            scene = self.scene()
            scene.undoStack.push(CommandEdgeBreakpointDel(self.edge, breakpoint))

    def breakpointMove(self, breakpoint, mousePos):
        """
        Move the selected breakpoint.
        :param breakpoint: the index of the breakpoint to move.
        :param mousePos: the current mouse position.
        """
        scene = self.scene()

        if not self.command:
            scene.clearSelection()
            self.setSelected(True)
            self.command = CommandEdgeBreakpointMove(edge=self.edge, index=breakpoint)

        self.breakpoints[breakpoint] = scene.snapToGrid(mousePos)
        self.updateEdge()

    def canDraw(self):
        """
        Check whether we have to draw the edge or not.
        :return: True if we need to draw the edge, False otherwise.
        """
        if self.edge.target:

            sourceNode = self.edge.source.shape
            sourcePath = self.mapFromItem(sourceNode, sourceNode.painterPath())
            targetNode = self.edge.target.shape
            targetPath = self.mapFromItem(targetNode, targetNode.painterPath())

            if sourcePath.intersects(targetPath):

                # shapes are colliding: estimate whether the edge needs to be drawn or not
                if not self.breakpoints:
                    # if there is no breakpoint then the edge
                    # line won't be visible so skip the drawing
                    return False

                for point in self.breakpoints:
                    # loop through all the breakpoints: if there is at least one breakpoint
                    # which is not inside the connected shapes then draw the edges
                    if not sourceNode.contains(self.mapToItem(sourceNode, point)) and \
                       not targetNode.contains(self.mapToItem(targetNode, point)):
                        return True

                return False

        return True

    def computePath(self, sourceNode, targetNode, points):
        """
        Returns a list of QLineF instance representing all the visible edge pieces.
        Subpaths which are obscured by the source or target shape are excluded by this method.
        :param sourceNode: the source node shape.
        :param targetNode: the target node shape.
        :param points: a list of points composing the edge path.
        :rtype: list
        """
        # get the source node painter path (the source node is always available)
        sourcePP = self.mapFromItem(sourceNode, sourceNode.painterPath())
        targetPP = self.mapFromItem(targetNode, targetNode.painterPath()) if targetNode else None

        # exclude all the "subpaths" which are not visible (obscured by the shapes)
        return [x for x in (QLineF(points[i], points[i + 1]) for i in range(len(points) - 1)) \
                    if (not sourcePP.contains(x.p1()) or not sourcePP.contains(x.p2())) and \
                       (not targetPP or (not targetPP.contains(x.p1()) or not targetPP.contains(x.p2())))]

    def contextMenu(self, pos):
        """
        Returns the basic edge context menu.
        :rtype: QMenu
        """
        menu = QMenu()
        breakpoint = self.breakpointAt(pos)
        if breakpoint is not None:
            action = QAction(QIcon(':/icons/delete'), 'Remove breakpoint', self.scene())
            action.triggered.connect(partial(self.breakpointDel, breakpoint=breakpoint))
            menu.addAction(action)
        else:
            menu.addAction(self.scene().actionItemDelete)
        return menu

    ################################################# GEOMETRY UPDATE ##################################################

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

    def updateZValue(self):
        """
        Update the edge Z value making sure it stays above source and target shapes (and respective labels).
        """
        source = self.edge.source.shape
        zValue = source.zValue() + 0.1
        if hasattr(source, 'label'):
            zValue = max(zValue, source.label.zValue())

        if self.edge.target:
            target = self.edge.target.shape
            zValue = max(zValue, target.zValue())
            if hasattr(target, 'label'):
                zValue = max(zValue, target.label.zValue())

        self.setZValue(zValue)

    def updateEdge(self, target=None):
        """
        Update the edge painter path and the selection polygon.
        :param target: the endpoint of this edge.
        """
        raise NotImplementedError('method `updateEdge` must be implemented in inherited class')