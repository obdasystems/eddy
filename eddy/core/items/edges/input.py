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


from math import sin, cos, radians, pi as M_PI

from PyQt5.QtCore import QPointF, QLineF, Qt
from PyQt5.QtGui import QPainter, QPolygonF
from PyQt5.QtGui import QPixmap, QPainterPath, QIcon

from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.misc import Brush, Pen
from eddy.core.items.edges.common.base import AbstractEdge
from eddy.core.items.edges.common.label import EdgeLabel


class InputEdge(AbstractEdge):
    """
    This class implements the 'Input' edge.
    """
    HeadSize = 10
    Type = Item.InputEdge

    def __init__(self, **kwargs):
        """
        Initialize the edge.
        """
        super().__init__(**kwargs)
        self.label = EdgeLabel('', centered=False, parent=self)

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
        pos2 = pos1 - QPointF(sin(rad + M_PI / 4.0) * size, cos(rad + M_PI / 4.0) * size)
        pos3 = pos2 - QPointF(sin(rad + 3.0 / 4.0 * M_PI) * size, cos(rad + 3.0 / 4.0 * M_PI) * size)
        pos4 = pos3 - QPointF(sin(rad - 3.0 / 4.0 * M_PI) * size, cos(rad - 3.0 / 4.0 * M_PI) * size)
        return QPolygonF([pos1, pos2, pos3, pos4])

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
            p2 = p1 - QPointF(sin(a1 + M_PI / 4.0) * 8, cos(a1 + M_PI / 4.0) * 8)
            p3 = p2 - QPointF(sin(a1 + 3.0 / 4.0 * M_PI) * 8, cos(a1 + 3.0 / 4.0 * M_PI) * 8)
            p4 = p3 - QPointF(sin(a1 - 3.0 / 4.0 * M_PI) * 8, cos(a1 - 3.0 / 4.0 * M_PI) * 8)
            h1 = QPolygonF([p1, p2, p3, p4])
            # DRAW THE EDGE
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Pen.DashedBlack1_1Pt_x3)
            painter.drawLine(l1)
            painter.setPen(Pen.SolidBlack1_1Pt)
            painter.setBrush(Brush.White255A)
            painter.drawPolygon(h1)
            painter.end()
            # ADD THE PIXMAP TO THE ICON
            icon.addPixmap(pixmap)
        return icon

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
        return path

    def redraw(self, selected=None, visible=None, breakpoint=None, anchor=None, **kwargs):
        """
        Schedule this item for redrawing.
        :type selected: bool
        :type visible: bool
        :type breakpoint: int
        :type anchor: AbstractNode
        """
        headBrush = Brush.NoBrush
        headPen = Pen.NoPen
        handleBrush = Brush.NoBrush
        handlePen = Pen.NoPen
        selectionBrush = Brush.NoBrush
        pen = Pen.NoPen

        if visible:
            headBrush = Brush.White255A
            headPen = Pen.SolidBlack1_1Pt
            pen = Pen.DashedBlack1_1Pt_x5
            if selected:
                handleBrush = Brush.Blue255A
                handlePen = Pen.SolidBlack1_1Pt
                if breakpoint is None and anchor is None:
                    selectionBrush = Brush.Yellow255A

        self.selectionBrush = selectionBrush
        self.headBrush = headBrush
        self.headPen = headPen
        self.handleBrush = handleBrush
        self.handlePen = handlePen
        self.pen = pen

        # FORCE CACHE REGENERATION
        self.setCacheMode(AbstractEdge.NoCache)
        self.setCacheMode(AbstractEdge.DeviceCoordinateCache)

        # SCHEDULE REPAINT
        self.update(self.boundingRect())

    def setText(self, text):
        """
        Set the label text.
        :type text: str
        """
        self.label.setText(text)

    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        self.label.setPos(pos)

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

    def text(self):
        """
        Returns the label text.
        :rtype: str
        """
        return self.label.text()

    def textPos(self):
        """
        Returns the current label position.
        :rtype: QPointF
        """
        return self.label.pos()

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

        ##########################################
        # UPDATE EDGE PATH, SELECTION BOX AND HEAD
        #################################

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

        self.updateLabel(points)
        self.redraw(selected=self.isSelected(), visible=self.canDraw())

    def updateLabel(self, points):
        """
        Update the edge label (both text and position).
        :type points: T <= tuple | list
        """
        if self.target and self.target.type() in {Item.PropertyAssertionNode, Item.RoleChainNode}:
            self.label.setVisible(True)
            self.label.setText(str(self.target.inputs.index(self.id) + 1))
            self.label.updatePos(points)
        else:
            self.label.setVisible(False)