# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: an editor for the Graphol ontology language.                    #
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
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from math import sin, cos, radians, pi as M_PI

from PyQt5.QtCore import QPointF, QLineF, Qt
from PyQt5.QtGui import QPainter, QPen, QPolygonF, QColor, QPixmap, QPainterPath
from PyQt5.QtWidgets import QMenu

from eddy.datatypes import DiagramMode, Item, Identity
from eddy.items.edges.common.base import AbstractEdge


class InclusionEdge(AbstractEdge):
    """
    This class implements the Inclusion edge.
    """
    item = Item.InclusionEdge
    name = 'inclusion'
    xmlname = 'inclusion'

    def __init__(self, complete=False, **kwargs):
        """
        Initialize the Inclusion edge.
        :param complete: whether the edge is complete or not.
        """
        super().__init__(**kwargs)
        self._complete = complete
        self.tail = QPolygonF()

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def complete(self):
        """
        Tells whether this edge is complete.
        :return: True if the edge is complete, False otherwise.
        :rtype: bool
        """
        return self._complete

    @complete.setter
    def complete(self, complete):
        """
        Set the complete attribute for this edge.
        :param complete: the complete value.
        """
        self._complete = bool(complete)

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def contextMenu(self, pos):
        """
        Returns the basic edge context menu.
        :param pos: the position where the context menu has been requested.
        :rtype: QMenu
        """
        menu = QMenu()
        scene = self.scene()
        breakpoint = self.breakpointAt(pos)
        if breakpoint is not None:
            action = scene.mainwindow.actionRemoveEdgeBreakpoint
            action.setData((self, breakpoint))
            menu.addAction(action)
        else:
            menu.addAction(scene.mainwindow.actionDelete)
            menu.addAction(scene.mainwindow.actionSwapEdge)
            menu.addSeparator()
            menu.addAction(scene.mainwindow.actionToggleEdgeComplete)
            scene.mainwindow.actionSwapEdge.setVisible(self.isValid(self.target, self.source))
            scene.mainwindow.actionToggleEdgeComplete.setChecked(self.complete)
        return menu

    def copy(self, scene):
        """
        Create a copy of the current edge.
        :param scene: a reference to the scene where this item is being copied.
        """
        kwargs = {
            'scene': scene,
            'id': self.id,
            'source': self.source,
            'target': self.target,
            'breakpoints': self.breakpoints[:],
            'complete': self.complete,
        }

        return self.__class__(**kwargs)

    def isValid(self, source, target):
        """
        Tells whether this edge is valid when being added between the given source and target nodes.
        :type source: Node.
        :type target: Node.
        :rtype: bool
        """
        if source is target:
            # Self connection is not valid.
            return False

        if source.identity is not Identity.Neutral and \
            target.identity is not Identity.Neutral and \
                source.identity is not target.identity:
            # If neither of the endpoints is NEUTRAL and the two nodes are specifying
            # a different identity, then we can't create an ISA between the nodes.
            return False

        return True

    ####################################################################################################################
    #                                                                                                                  #
    #   IMPORT / EXPORT                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    @classmethod
    def fromGraphol(cls, scene, E):
        """
        Create a new item instance by parsing a Graphol document item entry.
        :param scene: the scene where the element will be inserted.
        :param E: the Graphol document element entry.
        :rtype: AbstractEdge
        """
        points = []

        # extract all the breakpoints from the edge children
        children = E.elementsByTagName('line:point')
        for i in range(0, children.count()):
            P = children.at(i).toElement()
            point = QPointF(int(P.attribute('x')), int(P.attribute('y')))
            points.append(point)

        kwargs = {
            'scene': scene,
            'id': E.attribute('id'),
            'source': scene.node(E.attribute('source')),
            'target': scene.node(E.attribute('target')),
            'breakpoints': points[1:-1],
            'complete': bool(int(E.attribute('complete', '0'))),
        }

        edge = cls(**kwargs)

        # set the anchor points only if they are inside the endpoint shape: users can modify the .graphol file manually,
        # changing anchor points coordinates, which will result in an edge floating in the scene without being bounded
        # by endpoint shapes. Not setting the anchor point will make the edge use the default one (node center point)

        path = edge.source.painterPath()
        if path.contains(edge.source.mapFromScene(points[0])):
            edge.source.setAnchor(edge, points[0])

        path = edge.target.painterPath()
        if path.contains(edge.target.mapFromScene(points[-1])):
            edge.target.setAnchor(edge, points[-1])

        # map the edge over the source and target nodes
        edge.source.addEdge(edge)
        edge.target.addEdge(edge)
        edge.updateEdge()
        return edge

    def toGraphol(self, document):
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
        edge.setAttribute('complete', int(self.complete))

        ## LINE GEOMETRY
        source = self.source.anchor(self)
        target = self.target.anchor(self)

        for p in [source] + self.breakpoints + [target]:
            point = document.createElement('line:point')
            point.setAttribute('x', p.x())
            point.setAttribute('y', p.y())
            edge.appendChild(point)

        return edge

    ####################################################################################################################
    #                                                                                                                  #
    #   GEOMETRY                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def boundingRect(self):
        """
        Returns the shape bounding rect.
        :rtype: QRectF
        """
        path = QPainterPath()
        path.addPath(self.selection)
        path.addPolygon(self.head)

        if self.complete:
            path.addPolygon(self.tail)

        for shape in self.handles.values():
            path.addEllipse(shape)
        for shape in self.anchors.values():
            path.addEllipse(shape)

        return path.controlPointRect()

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPath(self.path)
        path.addPolygon(self.head)

        if self.complete:
            path.addPolygon(self.tail)

        return path

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPath(self.selection)
        path.addPolygon(self.head)

        if self.complete:
            path.addPolygon(self.tail)

        if self.isSelected():
            for shape in self.handles.values():
                path.addEllipse(shape)
            for shape in self.anchors.values():
                path.addEllipse(shape)

        return path

    ####################################################################################################################
    #                                                                                                                  #
    #   GEOMETRY UPDATE                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def updateEdge(self, target=None):
        """
        Update the edge painter path and the selection polygon.
        :param target: the endpoint of this edge.
        """
        boxSize = self.selectionSize
        headSize = self.headSize
        sourceNode = self.source
        targetNode = self.target
        sourcePos = self.source.anchor(self)
        targetPos = target or self.target.anchor(self)

        self.updateAnchors()
        self.updateHandles()

        ################################################################################################################
        #                                                                                                              #
        #   UPDATE EDGE PATH, SELECTION BOX, HEAD AND TAIL                                                             #
        #                                                                                                              #
        ################################################################################################################

        # get the list of visible subpaths for this edge
        collection = self.computePath(sourceNode, targetNode, [sourcePos] + self.breakpoints + [targetPos])

        def createSelectionBox(pos1, pos2, angle, size):
            """
            Constructs the selection polygon between pos1 and pos2 according to the given angle.
            :param pos1: the start point.
            :param pos2: the end point:
            :param angle: the angle of the line connecting pos1 and pos2.
            :param size: the size of the selection polygon.
            :rtype: QPolygonF
            """
            rad = radians(angle)
            x = size / 2 * sin(rad)
            y = size / 2 * cos(rad)
            a = QPointF(+x, +y)
            b = QPointF(-x, -y)
            return QPolygonF([pos1 + a, pos1 + b, pos2 + b, pos2 + a])

        def createHead(pos1, angle, size):
            """
            Create the head polygon.
            :param pos1: the head point of the polygon.
            :param angle: the angle of the line connecting pos1 to the previous breakpoint.
            :param size: the size of the tail of the polygon.
            :rtype: QPolygonF
            """
            rad = radians(angle)
            pos2 = pos1 - QPointF(sin(rad + M_PI / 3.0) * size, cos(rad + M_PI / 3.0) * size)
            pos3 = pos1 - QPointF(sin(rad + M_PI - M_PI / 3.0) * size, cos(rad + M_PI - M_PI / 3.0) * size)
            return QPolygonF([pos1, pos2, pos3])

        def createTail(pos1, angle, size):
            """
            Create the tail polygon.
            :param pos1: the tail point of the polygon.
            :param angle: the angle of the line connecting pos1 to the next breakpoint.
            :param size: the size of the tail of the polygon.
            :rtype: QPolygonF
            """
            rad = radians(angle)
            pos2 = pos1 + QPointF(sin(rad + M_PI / 3.0) * size, cos(rad + M_PI / 3.0) * size)
            pos3 = pos1 + QPointF(sin(rad + M_PI - M_PI / 3.0) * size, cos(rad + M_PI - M_PI / 3.0) * size)
            return QPolygonF([pos1, pos2, pos3])

        self.path = QPainterPath()
        self.selection = QPainterPath()

        if len(collection) == 0:

            self.head = QPolygonF()
            self.tail = QPolygonF()

        elif len(collection) == 1:

            subpath = collection[0]
            p1 = sourceNode.intersection(subpath)
            p2 = targetNode.intersection(subpath) if targetNode else subpath.p2()
            if p1 is not None and p2 is not None:
                self.path.moveTo(p1)
                self.path.lineTo(p2)
                self.selection.addPolygon(createSelectionBox(p1, p2, subpath.angle(), boxSize))
                self.head = createHead(p2, subpath.angle(), headSize)
                if self.complete:
                    self.tail = createTail(p1, subpath.angle(), headSize)

        elif len(collection) > 1:

            subpath1 = collection[0]
            subpathN = collection[-1]
            p11 = sourceNode.intersection(subpath1)
            p22 = targetNode.intersection(subpathN)

            if p11 and p22:

                p12 = subpath1.p2()
                p21 = subpathN.p1()

                self.path.moveTo(p11)
                self.path.lineTo(p12)
                self.selection.addPolygon(createSelectionBox(p11, p12, subpath1.angle(), boxSize))

                for subpath in collection[1:-1]:
                    p1 = subpath.p1()
                    p2 = subpath.p2()
                    self.path.moveTo(p1)
                    self.path.lineTo(p2)
                    self.selection.addPolygon(createSelectionBox(p1, p2, subpath.angle(), boxSize))

                self.path.moveTo(p21)
                self.path.lineTo(p22)
                self.selection.addPolygon(createSelectionBox(p21, p22, subpathN.angle(), boxSize))

                self.head = createHead(p22, subpathN.angle(), headSize)
                if self.complete:
                    self.tail = createTail(p11, subpath1.angle(), headSize)

        self.updateZValue()
        self.update()

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        lineWidth = 54
        headSize = 8  # length of the head side
        headSpan = 4  # offset between line end and head end (this is needed
                      # to prevent artifacts to be visible on low res screens)

        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Initialize the line
        line_p1 = QPointF(((kwargs['w'] - lineWidth) / 2), kwargs['h'] / 2)
        line_p2 = QPointF(((kwargs['w'] - lineWidth) / 2) + lineWidth - (headSpan / 2), kwargs['h'] / 2)
        line = QLineF(line_p1, line_p2)

        angle = line.angle()

        # Calculate head coordinates
        p1 = QPointF(line.p2().x() + (headSpan / 2), line.p2().y())
        p2 = p1 - QPointF(sin(angle + M_PI / 3.0) * headSize, cos(angle + M_PI / 3.0) * headSize)
        p3 = p1 - QPointF(sin(angle + M_PI - M_PI / 3.0) * headSize, cos(angle + M_PI - M_PI / 3.0) * headSize)

        # Initialize edge head
        head = QPolygonF([p1, p2, p3])

        # Draw the polygon
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(line)

        # Draw the head
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QColor(0, 0, 0))
        painter.drawPolygon(head)

        return pixmap

    def paint(self, painter, option, widget=None):
        """
        Paint the edge in the graphic view.
        :param painter: the active painter.
        :param option: the style option for this item.
        :param widget: the widget that is being painted on.
        """
        if self.canDraw():

            scene = self.scene()

            # Draw the selection path if needed
            if scene.mode in (DiagramMode.Idle, DiagramMode.NodeMove) and self.isSelected():
                painter.setRenderHint(QPainter.Antialiasing)
                painter.fillPath(self.selection, self.selectionBrush)

            # Draw the edge path
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(self.shapePen)
            painter.drawPath(self.path)

            # Draw the head polygon
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(self.headPen)
            painter.setBrush(self.headBrush)
            painter.drawPolygon(self.head)

            # Draw the tail polygon
            if self.complete:
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(self.headPen)
                painter.setBrush(self.headBrush)
                painter.drawPolygon(self.tail)

            if self.isSelected():

                # Draw breakpoint handles
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(self.handlePen)
                painter.setBrush(self.handleBrush)
                for rect in self.handles.values():
                    painter.drawEllipse(rect)

                # Draw anchor points
                if self.target:
                    painter.setRenderHint(QPainter.Antialiasing)
                    painter.setPen(self.handlePen)
                    painter.setBrush(self.handleBrush)
                    for rect in self.anchors.values():
                        painter.drawEllipse(rect)