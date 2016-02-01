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


from math import sin, cos, radians, pi as M_PI

from PyQt5.QtCore import QPointF, QLineF, Qt
from PyQt5.QtGui import QPainter, QPen, QPolygonF, QColor, QPixmap, QPainterPath

from eddy.core.datatypes import DiagramMode, Item
from eddy.core.items.edges.common.base import AbstractEdge
from eddy.core.items.edges.common.label import Label


class InputEdge(AbstractEdge):
    """
    This class implements the Input edge.
    """
    headPen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    headBrush = QColor(252, 252, 252)
    headSize = 10
    item = Item.InputEdge
    shapePen = QPen(QColor(0, 0, 0), 1.1, Qt.CustomDashLine, Qt.RoundCap, Qt.RoundJoin)
    shapePen.setDashPattern([5, 5])
    xmlname = 'input'

    def __init__(self, functional=False, **kwargs):
        """
        Initialize the edge.
        :type functional: bool
        """
        super().__init__(**kwargs)

        self._functional = functional

        self.label = Label('', centered=False, parent=self)
        self.tail = QLineF()

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def functional(self):
        """
        Tells whether this edge is functional.
        :rtype: bool
        """
        return self._functional

    @functional.setter
    def functional(self, functional):
        """
        Set the functional attribute for this edge.
        :type functional: bool
        """
        self._functional = bool(functional)

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def copy(self, scene):
        """
        Create a copy of the current edge.
        :type scene: DiagramScene
        """
        kwargs = {
            'id': self.id,
            'source': self.source,
            'target': self.target,
            'breakpoints': self.breakpoints[:],
            'functional': self.functional,
        }
        return scene.itemFactory.create(item=self.item, scene=scene, **kwargs)

    def updateLabel(self, points):
        """
        Update the edge label (both text and position).
        :type points: T <= tuple | list
        """
        if self.target and self.target.isItem(Item.PropertyAssertionNode, Item.RoleChainNode):
            self.label.setVisible(True)
            self.label.setText(str(self.target.inputs.index(self.id) + 1))
            self.label.updatePos(points)
        else:
            self.label.setVisible(False)

    ####################################################################################################################
    #                                                                                                                  #
    #   IMPORT / EXPORT                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    @classmethod
    def fromGraphol(cls, scene, E):
        """
        Create a new item instance by parsing a Graphol document item entry.
        :type scene: DiagramScene
        :type E: QDomElement
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
            'id': E.attribute('id'),
            'source': scene.node(E.attribute('source')),
            'target': scene.node(E.attribute('target')),
            'breakpoints': points[1:-1],
            'functional': bool(int(E.attribute('functional', '0'))),
        }

        edge = scene.itemFactory.create(item=cls.item, scene=scene, **kwargs)

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
        :type document: QDomDocument
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

    ####################################################################################################################
    #                                                                                                                  #
    #   GEOMETRY UPDATE                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def updateEdge(self, target=None):
        """
        Update the edge painter path and the selection polygon.
        :type target: QPointF
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

        def createHead(pos1, angle, size):
            """
            Create the head polygon.
            :type pos1: QPointF
            :type angle: float
            :type size: int
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
            :type pos1: QPointF
            :type angle: float
            :type size: int
            :rtype: QLineF
            """
            rad = radians(angle)
            pos2 = pos1 + QPointF(sin(rad + M_PI / 3.0) * size, cos(rad + M_PI / 3.0) * size)
            pos3 = pos1 + QPointF(sin(rad + M_PI - M_PI / 3.0) * size, cos(rad + M_PI - M_PI / 3.0) * size)
            return QLineF(pos2, pos3)

        self.path = QPainterPath()
        self.selection = QPainterPath()

        points = [] # will store all the points defining the edge not to recompute the path to update the label
        append = points.append  # keep this shortcut and the one below since it saves a lot of computation
        extend = points.extend  # more: http://blog.cdleary.com/2010/04/efficiency-of-list-comprehensions/

        if len(collection) == 0:

            self.head = QPolygonF()
            self.tail = QLineF()

        elif len(collection) == 1:

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
                extend((p1, p2))

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
                extend((p11, p12))

                for subpath in collection[1:-1]:
                    p1 = subpath.p1()
                    p2 = subpath.p2()
                    self.path.moveTo(p1)
                    self.path.lineTo(p2)
                    self.selection.addPolygon(createSelectionBox(p1, p2, subpath.angle(), boxSize))
                    append(p2)

                self.path.moveTo(p21)
                self.path.lineTo(p22)
                self.selection.addPolygon(createSelectionBox(p21, p22, subpathN.angle(), boxSize))
                append(p22)

                self.head = createHead(p22, subpathN.angle(), headSize)
                if self.functional:
                    self.tail = createTail(p11, subpath1.angle(), headSize)

        self.updateZValue()
        self.updateLabel(points)
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
        :type painter: QPainter
        :type option: int
        :type widget: QWidget
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