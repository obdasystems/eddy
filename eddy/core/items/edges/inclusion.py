# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from math import sin, cos, radians, pi as M_PI

from PyQt5.QtCore import QPointF, QLineF, Qt
from PyQt5.QtGui import QPainter, QPolygonF
from PyQt5.QtGui import QPixmap, QPainterPath, QIcon

from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.misc import Brush, Pen
from eddy.core.items.edges.common.base import AbstractEdge


class InclusionEdge(AbstractEdge):
    """
    This class implements the 'Inclusion' edge.
    """
    Type = Item.InclusionEdge

    def __init__(self, equivalence=False, **kwargs):
        """
        Initialize the edge.
        :type equivalence: bool
        """
        super().__init__(**kwargs)
        self.equivalence = equivalence
        self.tail = QPolygonF()

    #############################################
    #   INTERFACE
    #################################

    def boundingRect(self):
        """
        Returns the shape bounding rect.
        :rtype: QRectF
        """
        path = QPainterPath()
        path.addPath(self.selection)
        path.addPolygon(self.head)
        path.addPolygon(self.tail)

        for shape in self.handles:
            path.addEllipse(shape)
        for shape in self.anchors.values():
            path.addEllipse(shape)

        return path.controlPointRect()

    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        kwargs = {
            'id': self.id,
            'source': self.source,
            'target': self.target,
            'breakpoints': self.breakpoints[:],
            'equivalence': self.equivalence,
        }
        return diagram.factory.create(self.type(), **kwargs)

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

    @staticmethod
    def createTail(pos1, angle, size):
        """
        Create the tail polygon.
        :type pos1: QPointF
        :type angle: float
        :type size: int
        :rtype: QPolygonF
        """
        rad = radians(angle)
        pos2 = pos1 + QPointF(sin(rad + M_PI / 3.0) * size, cos(rad + M_PI / 3.0) * size)
        pos3 = pos1 + QPointF(sin(rad + M_PI - M_PI / 3.0) * size, cos(rad + M_PI - M_PI / 3.0) * size)
        return QPolygonF([pos1, pos2, pos3])

    @classmethod
    def icon(cls, width, height, **kwargs):
        """
        Returns an icon of this item suitable for the palette.
        :type width: int
        :type height: int
        :rtype: QIcon
        """
        icon = QIcon()
        for i in (1.0, 2.0):
            # CREATE THE PIXMAP
            pixmap = QPixmap(width * i, height * i)
            pixmap.setDevicePixelRatio(i)
            pixmap.fill(Qt.transparent)
            # CREATE THE LINE
            p1 = QPointF(((width - 54) / 2), height / 2)
            p2 = QPointF(((width - 54) / 2) + 54 - 2, height / 2)
            l1 = QLineF(p1, p2)
            # CREATE THE HEAD
            a1 = l1.angle()
            p1 = QPointF(l1.p2().x() + 2, l1.p2().y())
            p2 = p1 - QPointF(sin(a1 + M_PI / 3.0) * 8, cos(a1 + M_PI / 3.0) * 8)
            p3 = p1 - QPointF(sin(a1 + M_PI - M_PI / 3.0) * 8, cos(a1 + M_PI - M_PI / 3.0) * 8)
            h1 = QPolygonF([p1, p2, p3])
            # DRAW THE EDGE
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Pen.SolidBlack1_1Pt)
            painter.drawLine(l1)
            painter.setPen(Pen.SolidBlack1_1Pt)
            painter.setBrush(Brush.Black255A)
            painter.drawPolygon(h1)
            painter.end()
            # ADD THE PIXMAP TO THE ICON
            icon.addPixmap(pixmap)
        return icon

    def isEquivalenceAllowed(self):
        """
        Returns True if this Inclusion edge can express equivalence, False otherwise.
        :rtype: bool
        """
        if self.source.identity in {Identity.Attribute, Identity.Role}:
            if self.target.type() is Item.ComplementNode:
                return False
        return True

    def paint(self, painter, option, widget=None):
        """
        Paint the edge in the diagram scene.
        :type painter: QPainter
        :type option: QStyleOptionGraphicsItem
        :type widget: QWidget
        """
        # SET THE RECT THAT NEEDS TO BE REPAINTED
        painter.setClipRect(option.exposedRect)
        # SELECTION AREA
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillPath(self.selection, self.selectionBrush)
        # EDGE LINE
        painter.setPen(self.pen)
        painter.drawPath(self.path)
        # HEAD/TAIL POLYGON
        painter.setPen(self.headPen)
        painter.setBrush(self.headBrush)
        painter.drawPolygon(self.head)
        painter.drawPolygon(self.tail)
        # BREAKPOINTS AND ANCHOR POINTS
        painter.setPen(self.handlePen)
        painter.setBrush(self.handleBrush)
        for shape in self.handles:
            painter.drawEllipse(shape)
        for shape in self.anchors.values():
            painter.drawEllipse(shape)

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPath(self.path)
        path.addPolygon(self.head)
        path.addPolygon(self.tail)
        return path

    def setText(self, text):
        """
        Set the label text.
        :type text: str
        """
        pass

    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        pass

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPath(self.selection)
        path.addPolygon(self.head)
        path.addPolygon(self.tail)

        if self.isSelected():
            for shape in self.handles:
                path.addEllipse(shape)
            for shape in self.anchors.values():
                path.addEllipse(shape)

        return path

    def text(self):
        """
        Returns the label text.
        :rtype: str
        """
        pass

    def textPos(self):
        """
        Returns the current label position.
        :rtype: QPointF
        """
        pass

    def updateEdge(self, target=None):
        """
        Update the edge painter path and the selection polygon.
        :type target: QPointF
        """
        boxSize = self.SelectionSize
        headSize = self.HeadSize
        sourceNode = self.source
        targetNode = self.target
        sourcePos = sourceNode.anchor(self)
        targetPos = target or targetNode.anchor(self)

        self.prepareGeometryChange()

        self.updateAnchors()
        self.updateBreakPoints()
        self.updateZValue()

        createSelectionArea = self.createSelectionArea
        createHead = self.createHead
        createTail = self.createTail

        ################################################
        # UPDATE EDGE PATH, SELECTION BOX, HEAD AND TAIL
        #################################

        collection = self.computePath(sourceNode, targetNode, [sourcePos] + self.breakpoints + [targetPos])

        self.path = QPainterPath()
        self.selection = QPainterPath()
        self.head = QPolygonF()
        self.tail = QPolygonF()

        if len(collection) == 1:

            subpath = collection[0]
            p1 = sourceNode.intersection(subpath)
            p2 = targetNode.intersection(subpath) if targetNode else subpath.p2()
            if p1 is not None and p2 is not None:
                self.path.moveTo(p1)
                self.path.lineTo(p2)
                self.selection.addPolygon(createSelectionArea(p1, p2, subpath.angle(), boxSize))
                self.head = createHead(p2, subpath.angle(), headSize)
                if self.equivalence:
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
                self.selection.addPolygon(createSelectionArea(p11, p12, subpath1.angle(), boxSize))

                for subpath in collection[1:-1]:
                    p1 = subpath.p1()
                    p2 = subpath.p2()
                    self.path.moveTo(p1)
                    self.path.lineTo(p2)
                    self.selection.addPolygon(createSelectionArea(p1, p2, subpath.angle(), boxSize))

                self.path.moveTo(p21)
                self.path.lineTo(p22)
                self.selection.addPolygon(createSelectionArea(p21, p22, subpathN.angle(), boxSize))

                self.head = createHead(p22, subpathN.angle(), headSize)
                if self.equivalence:
                    self.tail = createTail(p11, subpath1.angle(), headSize)

        self.redraw(selected=self.isSelected(), visible=self.canDraw())