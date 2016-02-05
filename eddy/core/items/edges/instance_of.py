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

from eddy.core.datatypes import Font, Item, Platform
from eddy.core.items.edges.common.base import AbstractEdge
from eddy.core.items.edges.common.label import Label


class InstanceOfEdge(AbstractEdge):
    """
    This class implements the InstanceOf edge.
    """
    item = Item.InstanceOfEdge

    def __init__(self, **kwargs):
        """
        Initialize the InstanceOf edge.
        """
        super().__init__(**kwargs)
        self.label = Label('instanceOf', centered=True, parent=self)

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
        }
        return scene.itemFactory.create(item=self.item, scene=scene, **kwargs)

    @staticmethod
    def createHead(pos1, angle, size):
        """
        Create the head polygon.
        :type pos1: QPointF
        :type angle: float
        :type size: int
        :rtype: QPolygonF
        """
        rad = radians(angle)
        pos2 = pos1 - QPointF(sin(rad + M_PI / 3.0) * size, cos(rad + M_PI / 3.0) * size)
        pos3 = pos1 - QPointF(sin(rad + M_PI - M_PI / 3.0) * size, cos(rad + M_PI - M_PI / 3.0) * size)
        return QPolygonF([pos1, pos2, pos3])

    def updateLabel(self, points):
        """
        Update the label text position.
        :type points: T <= tuple | list
        """
        self.label.updatePos(points)

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

        for shape in self.handles:
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

        return path

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPath(self.selection)
        path.addPolygon(self.head)

        if self.isSelected():
            for shape in self.handles:
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
        self.updateBreakPoints()
        self.updateZValue()

        createSelectionArea = self.createSelectionArea
        createHead = self.createHead

        ################################################################################################################
        #                                                                                                              #
        #   UPDATE EDGE PATH, SELECTION BOX AND HEAD                                                                   #
        #                                                                                                              #
        ################################################################################################################

        # get the list of visible subpaths for this edge
        collection = self.computePath(sourceNode, targetNode, [sourcePos] + self.breakpoints + [targetPos])

        self.path = QPainterPath()
        self.selection = QPainterPath()
        self.head = QPolygonF()

        points = [] # will store all the points defining the edge not to recompute the path to update the label
        append = points.append  # keep this shortcut and the one below since it saves a lot of computation
        extend = points.extend  # more: http://blog.cdleary.com/2010/04/efficiency-of-list-comprehensions/

        if len(collection) == 1:

            subpath = collection[0]
            p1 = sourceNode.intersection(subpath)
            p2 = targetNode.intersection(subpath) if targetNode else subpath.p2()
            if p1 is not None and p2 is not None:
                self.path.moveTo(p1)
                self.path.lineTo(p2)
                self.selection.addPolygon(createSelectionArea(p1, p2, subpath.angle(), boxSize))
                self.head = createHead(p2, subpath.angle(), headSize)
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
                self.selection.addPolygon(createSelectionArea(p11, p12, subpath1.angle(), boxSize))
                extend((p11, p12))

                for subpath in collection[1:-1]:
                    p1 = subpath.p1()
                    p2 = subpath.p2()
                    self.path.moveTo(p1)
                    self.path.lineTo(p2)
                    self.selection.addPolygon(createSelectionArea(p1, p2, subpath.angle(), boxSize))
                    append(p2)

                self.path.moveTo(p21)
                self.path.lineTo(p22)
                self.selection.addPolygon(createSelectionArea(p21, p22, subpathN.angle(), boxSize))
                append(p22)

                self.head = createHead(p22, subpathN.angle(), headSize)

        self.updatePenAndBrush(selected=self.isSelected(), visible=self.canDraw())
        self.updateLabel(points)
        self.update()

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def paint(self, painter, option, widget=None):
        """
        Paint the edge in the diagram scene.
        :type painter: QPainter
        :type option: int
        :type widget: QWidget
        """
        # SELECTION AREA
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillPath(self.selection, self.selectionBrush())
        # EDGE LINE
        painter.setPen(self.pen())
        painter.drawPath(self.path)
        # HEAD POLYGON
        painter.setPen(self.headPen())
        painter.setBrush(self.headBrush())
        painter.drawPolygon(self.head)
        # BREAKPOINTS AND ANCHOR POINTS
        painter.setPen(self.handlePen())
        painter.setBrush(self.handleBrush())
        for shape in self.handles:
            painter.drawEllipse(shape)
        for shape in self.anchors.values():
            painter.drawEllipse(shape)

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        # INITIALIZATION
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        # INITIALIZE EDGE LINE
        pp1 = QPointF(((kwargs['w'] - 52) / 2), kwargs['h'] / 2)
        pp2 = QPointF(((kwargs['w'] - 52) / 2) + 52 - 2, kwargs['h'] / 2)
        line = QLineF(pp1, pp2)
        # CALCULATE HEAD COORDINATES
        angle = radians(line.angle())
        p1 = QPointF(line.p2().x() + 2, line.p2().y())
        p2 = p1 - QPointF(sin(angle + M_PI / 3.0) * 8, cos(angle + M_PI / 3.0) * 8)
        p3 = p1 - QPointF(sin(angle + M_PI - M_PI / 3.0) * 8, cos(angle + M_PI - M_PI / 3.0) * 8)
        # INITIALIZE EDGE HEAD
        head = QPolygonF([p1, p2, p3])
        # DRAW THE POLYGON
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(line)
        # DRAW HEAD
        painter.setPen(QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QColor(0, 0, 0))
        painter.drawPolygon(head)
        # DRAW THE TEXT ON TOP OF THE EDGE
        space = 2 if Platform.identify() is Platform.Darwin else 0
        painter.setFont(Font('Arial', 9, Font.Light))
        painter.drawText(pp1.x() + space, (kwargs['h'] / 2) - 4, 'instanceOf')

        return pixmap