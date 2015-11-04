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


from math import sin, cos, radians, pi as M_PI

from grapholed.datatypes import DiagramMode, ItemType
from grapholed.exceptions import ParseError
from grapholed.functions import connect
from grapholed.items.edges.common.base import Edge

from PyQt5.QtCore import QPointF, QLineF, Qt
from PyQt5.QtGui import QPainter, QPen, QPolygonF, QColor, QPixmap, QIcon, QPainterPath
from PyQt5.QtWidgets import QAction, QMenu


class InputEdge(Edge):
    """
    This class implements the Input edge.
    """
    headPen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    headBrush = QColor(252, 252, 252)
    headSize = 10
    itemtype = ItemType.InputEdge
    name = 'input'
    shapePen = QPen(QColor(0, 0, 0), 1.1, Qt.CustomDashLine, Qt.RoundCap, Qt.RoundJoin)
    shapePen.setDashPattern([5, 5])
    xmlname = 'input'

    def __init__(self, functional=False, **kwargs):
        """
        Initialize the Input edge.
        :param functional: whether the edge is functional or not.
        """
        super().__init__(**kwargs)
        self._functional = functional
        self.tail = QLineF()

    ################################################## PROPERTIES ######################################################

    @property
    def functional(self):
        """
        Tells whether this edge is functional.
        :return: True if the edge is functional, False otherwise.
        :rtype: bool
        """
        return self._functional

    @functional.setter
    def functional(self, functional):
        """
        Set the functional attribute for this edge.
        :param functional: the complete value.
        """
        self._functional = bool(functional)

    ################################################# ITEM INTERFACE ###################################################

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
            action = QAction(QIcon(':/icons/delete'), 'Remove breakpoint', scene)
            connect(action.triggered, self.breakpointDel, breakpoint=breakpoint)
            menu.addAction(action)
        else:
            menu.addAction(scene.actionItemDelete)
            menu.addSeparator()
            menu.addAction(scene.actionToggleEdgeFunctional)
            scene.actionToggleEdgeFunctional.setChecked(self.functional)
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
            'functional': self.functional,
        }

        return self.__class__(**kwargs)

    ############################################# ITEM IMPORT / EXPORT #################################################

    @classmethod
    def fromGraphol(cls, scene, E):
        """
        Create a new item instance by parsing a Graphol document item entry.
        :param scene: the scene where the element will be inserted.
        :param E: the Graphol document element entry.
        :raise ParseError: in case it's not possible to generate the node using the given element.
        :rtype: Edge
        """
        try:

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
                'functional': bool(int(E.attribute('functional', '0'))),
            }

            edge = cls(**kwargs)
            edge.source.setAnchor(edge, points[0])
            edge.target.setAnchor(edge, points[-1])
            edge.updateEdge()

            # map the edge over the source and target nodes
            edge.source.edges.append(edge)
            edge.target.edges.append(edge)

        except Exception as e:
            raise ParseError('could not create {0} instance from Graphol node: {1}'.format(cls.__name__, e))
        else:
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
        edge.setAttribute('functional', int(self.functional))

        ## LINE GEOMETRY
        source = self.source.anchor(self)
        target = self.target.anchor(self)

        for p in [source] + self.breakpoints + [target]:
            point = document.createElement('line:point')
            point.setAttribute('x', p.x())
            point.setAttribute('y', p.y())
            edge.appendChild(point)

        return edge

    ##################################################### GEOMETRY #####################################################

    def boundingRect(self):
        """
        Returns the shape bounding rect.
        :rtype: QRectF
        """
        path = QPainterPath()
        path.addPath(self.selection)
        path.addPolygon(self.head)

        if self.functional:
            path.moveTo(self.tail.p1())
            path.lineTo(self.tail.p2())

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

        if self.functional:
            path.moveTo(self.tail.p1())
            path.lineTo(self.tail.p2())

        return path

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPath(self.selection)
        path.addPolygon(self.head)

        if self.functional:
            path.moveTo(self.tail.p1())
            path.lineTo(self.tail.p2())

        if self.isSelected():
            for shape in self.handles.values():
                path.addEllipse(shape)
            for shape in self.anchors.values():
                path.addEllipse(shape)

        return path

    ################################################# GEOMETRY UPDATE ##################################################

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

        ################################ UPDATE EDGE PATH, SELECTION BOX, HEAD AND TAIL ################################

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
            pos2 = pos1 - QPointF(sin(rad + M_PI / 4.0) * size, cos(rad + M_PI / 4.0) * size)
            pos3 = pos2 - QPointF(sin(rad + 3.0 / 4.0 * M_PI) * size, cos(rad + 3.0 / 4.0 * M_PI) * size)
            pos4 = pos3 - QPointF(sin(rad - 3.0 / 4.0 * M_PI) * size, cos(rad - 3.0 / 4.0 * M_PI) * size)
            return QPolygonF([pos1, pos2, pos3, pos4])

        def createTail(pos1, angle, size):
            """
            Create the tail line.
            :param pos1: the intersection point between the edge and the souce shape.
            :param angle: the angle of the line connecting pos1 to the next breakpoint.
            :param size: the size of the tail of the polygon.
            :rtype: QLineF
            """
            rad = radians(angle)
            pos2 = pos1 + QPointF(sin(rad + M_PI / 3.0) * size, cos(rad + M_PI / 3.0) * size)
            pos3 = pos1 + QPointF(sin(rad + M_PI - M_PI / 3.0) * size, cos(rad + M_PI - M_PI / 3.0) * size)
            return QLineF(pos2, pos3)

        self.path = QPainterPath()
        self.selection = QPainterPath()

        if len(collection) == 1:

            subpath = collection[0]
            p1 = sourceNode.intersection(subpath)
            p2 = targetNode.intersection(subpath) if targetNode else subpath.p2()
            if p1 is not None and p2 is not None:
                self.path.moveTo(p1)
                self.path.lineTo(p2)
                self.selection.addPolygon(createSelectionBox(p1, p2, subpath.angle(), boxSize))
                self.head = createHead(p2, subpath.angle(), headSize)
                if self.functional:
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
                if self.functional:
                    self.tail = createTail(p11, subpath1.angle(), headSize)

        self.updateZValue()
        self.update()

    ################################################## ITEM DRAWING ####################################################

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

        angle = radians(line.angle())

        # Calculate head coordinates
        p1 = QPointF(line.p2().x() + (headSpan / 2), line.p2().y())
        p2 = p1 - QPointF(sin(angle + M_PI / 4.0) * headSize, cos(angle + M_PI / 4.0) * headSize)
        p3 = p2 - QPointF(sin(angle + 3.0 / 4.0 * M_PI) * headSize, cos(angle + 3.0 / 4.0 * M_PI) * headSize)
        p4 = p3 - QPointF(sin(angle - 3.0 / 4.0 * M_PI) * headSize, cos(angle - 3.0 / 4.0 * M_PI) * headSize)

        # Initialize edge head
        head = QPolygonF([p1, p2, p3, p4])

        # Initialize dashed pen for the line
        linePen = QPen(QColor(0, 0, 0), 1.1, Qt.CustomDashLine, Qt.RoundCap, Qt.RoundJoin)
        linePen.setDashPattern([3, 3])

        # Draw the polygon
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(linePen)
        painter.drawLine(line)

        # Draw the head
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QColor(252, 252, 252))
        painter.drawPolygon(head)

        return pixmap

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
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

            # Draw the tail line
            if self.functional:
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setPen(self.headPen)
                painter.drawLine(self.tail)

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