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


from abc import ABCMeta, abstractmethod
from functools import partial

from grapholed.commands import CommandEdgeBreakpointAdd, CommandEdgeBreakpointDel, CommandEdgeBreakpointMove
from grapholed.commands import CommandEdgeAnchorMove
from grapholed.functions import distanceP, distanceL
from grapholed.items import Item

from PyQt5.QtCore import Qt, QPointF, QLineF, QRectF
from PyQt5.QtGui import QColor, QPen, QPolygonF, QPainterPath, QIcon
from PyQt5.QtWidgets import QGraphicsItem, QMenu, QAction


class Edge(Item):
    """
    Base class for all the diagram edges.
    """
    __metaclass__ = ABCMeta

    handleBrush = QColor(79, 195, 247, 255)
    handlePen = QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine)
    handleSize = 8
    headPen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    headBrush = QColor(0, 0, 0)
    headSize = 12
    name = 'edge'
    prefix = 'e'
    selectionBrush = QColor(251, 255, 148)
    selectionSize = 6
    shapePen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    xmlname = 'edge'

    def __init__(self, source, target=None, breakpoints=None, **kwargs):
        """
        Initialize the edge.
        :param source: the edge source node.
        :param target: the edge target node (if any).
        :param breakpoints: the breakpoints of this edge.
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

    ################################################### PROPERTIES #####################################################

    @property
    def source(self):
        """
        Returns the source node.
        :rtype: Node
        """
        return self._source

    @source.setter
    def source(self, value):
        """
        Set the source of this edge.
        :param value: the source node
        """
        self._source = value

    @property
    def target(self):
        """
        Returns the target node.
        :rtype: Node
        """
        return self._target

    @source.setter
    def source(self, value):
        """
        Set the target of this edge.
        :param value: the target node
        """
        self._target = value

    ################################################ ITEM INTERFACE ####################################################

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

    def anchorMove(self, node, mousePos):
        """
        Move the selected anchor point.
        :param node: the shape whose anchor point is being moved.
        :param mousePos: the current mouse position.
        """
        scene = self.scene()

        if not self.command:
            scene.clearSelection()
            self.setSelected(True)
            self.command = CommandEdgeAnchorMove(edge=self, node=node)

        pos = None
        path = self.mapFromItem(node, node.painterPath())
        scene = self.scene()
        mousePos = scene.snapToGrid(mousePos)
        if path.contains(mousePos):
            epsilon = 10.0
            magnet = self.mapFromItem(node, node.center())
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
            node.setAnchor(self, pos)
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
        scene.undoStack.push(CommandEdgeBreakpointAdd(edge=self, index=index, point=point))
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
            scene.undoStack.push(CommandEdgeBreakpointDel(self, breakpoint))

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
            self.command = CommandEdgeBreakpointMove(edge=self, index=breakpoint)

        self.breakpoints[breakpoint] = scene.snapToGrid(mousePos)
        self.updateEdge()

    def canDraw(self):
        """
        Check whether we have to draw the edge or not.
        :return: True if we need to draw the edge, False otherwise.
        """
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
        :param source: the source node shape.
        :param target: the target node shape.
        :param points: a list of points composing the edge path.
        :rtype: list
        """
        # get the source node painter path (the source node is always available)
        sourcePP = self.mapFromItem(source, source.painterPath())
        targetPP = self.mapFromItem(target, target.painterPath()) if target else None

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
            scene = self.scene()
            menu.addAction(scene.actionItemDelete)
        return menu

    def copy(self, scene):
        """
        Create a copy of the current edge.
        :param scene: a reference to the scene where this item is being copied.
        """
        return self.__class__(scene=scene,
                              id=self.id,
                              source=self.source,
                              target=self.target,
                              breakpoints=self.breakpoints[:])

    def other(self, node):
        """
        Returns the opposite endpoint of the given node.
        :raise AttributeError: if the given node is not an endpoint of this edge.
        :param node: the node we want to find the opposite endpoint.
        :rtype: Node
        """
        if node == self.source:
            return self.target
        elif node == self.target:
            return self.source
        raise AttributeError('node {0} is not attached to edge {1}'.format(node, self))

    ################################################## ITEM EXPORT #####################################################

    def asGraphol(self, document):
        """
        Export the current item in Graphol format.
        :param document: the XML document where this item will be inserted.
        :rtype: QDomElement
        """
        ## ROOT ELEMENT
        edge = document.createElement('edge')
        edge.setAttribute('source', self.source.id)
        edge.setAttribute('target', self.target.id)
        edge.setAttribute('id', self.id)
        edge.setAttribute('type', self.xmlname)

        ## LINE GEOMETRY
        source = self.source.shape.anchor(self.shape)
        target = self.target.shape.anchor(self.shape)

        for p in [source] + self.breakpoints + [target]:
            point = document.createElement('line:point')
            point.setAttribute('x', p.x())
            point.setAttribute('y', p.y())
            edge.appendChild(point)

        return edge

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

    ################################################# GEOMETRY UPDATE ##################################################

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
        :param target: the endpoint of this edge.
        """
        pass

    ################################################## ITEM DRAWING ####################################################

    @classmethod
    @abstractmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        pass