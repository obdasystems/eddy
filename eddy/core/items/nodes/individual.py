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


import math

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPolygonF, QPainterPath, QPainter, QPen, QColor, QPixmap, QBrush

from eddy.core.datatypes import Font, Identity, Item, XsdDatatype
from eddy.core.functions import snapF
from eddy.core.items.nodes.common.base import AbstractResizableNode
from eddy.core.items.nodes.common.label import Label
from eddy.core.regex import RE_LITERAL


class IndividualNode(AbstractResizableNode):
    """
    This class implements the 'Individual' node.
    """
    indexLT = 0
    indexLB = 1
    indexBL = 2
    indexBR = 3
    indexRB = 4
    indexRT = 5
    indexTR = 6
    indexTL = 7
    indexEE = 8

    identities = {Identity.Individual, Identity.Literal}
    item = Item.IndividualNode
    minheight = 60
    minwidth = 60

    def __init__(self, width=minwidth, height=minheight, brush=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(**kwargs)
        w = max(width, self.minwidth)
        h = max(height, self.minheight)
        s = self.handleSize
        self.brush = brush or QBrush(QColor(252, 252, 252))
        self.pen = QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine)
        self.polygon = self.createPolygon(w, h)
        self.background = self.createBackground(w + s, h + s)
        self.selection = self.createSelection(w + s, h + s)
        self.label = Label('individual', parent=self)
        self.label.updatePos()
        self.updateHandles()

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def datatype(self):
        """
        Returns the datatype associated with this node or None if the node is not a Literal.
        :rtype: XsdDatatype
        """
        match = RE_LITERAL.match(self.text())
        if match:
            return XsdDatatype.forValue(match.group('datatype'))
        return None

    @property
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        match = RE_LITERAL.match(self.text())
        if match:
            return Identity.Literal
        return Identity.Individual

    @property
    def literal(self):
        """
        Returns the literal value associated with this node.
        If the node is not a literal it will return None.
        :rtype: str
        """
        match = RE_LITERAL.match(self.text())
        if match:
            return match.group('literal')
        return None

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def copy(self, scene):
        """
        Create a copy of the current item.
        :type scene: DiagramScene
        """
        kwargs = {
            'id': self.id,
            'brush': self.brush,
            'description': self.description,
            'url': self.url,
            'height': self.height(),
            'width': self.width(),
        }
        node = scene.itemFactory.create(item=self.item, scene=scene, **kwargs)
        node.setPos(self.pos())
        node.setText(self.text())
        node.setTextPos(node.mapFromScene(self.mapToScene(self.textPos())))
        return node

    @staticmethod
    def createBackground(width, height):
        """
        Returns the initialized background polygon according to the given width/height.
        :type width: int
        :type height: int
        :rtype: QPolygonF
        """
        return QPolygonF([
            QPointF(-(width / 2), -((height / (1 + math.sqrt(2))) / 2)), # 0
            QPointF(-(width / 2), +((height / (1 + math.sqrt(2))) / 2)), # 1
            QPointF(-((width / (1 + math.sqrt(2))) / 2), +(height / 2)), # 2
            QPointF(+((width / (1 + math.sqrt(2))) / 2), +(height / 2)), # 3
            QPointF(+(width / 2), +((height / (1 + math.sqrt(2))) / 2)), # 4
            QPointF(+(width / 2), -((height / (1 + math.sqrt(2))) / 2)), # 5
            QPointF(+((width / (1 + math.sqrt(2))) / 2), -(height / 2)), # 6
            QPointF(-((width / (1 + math.sqrt(2))) / 2), -(height / 2)), # 7
            QPointF(-(width / 2), -((height / (1 + math.sqrt(2))) / 2)), # 8
        ])

    @staticmethod
    def createPolygon(width, height):
        """
        Returns the initialized polygon according to the given width/height.
        :type width: int
        :type height: int
        :rtype: QPolygonF
        """
        return QPolygonF([
            QPointF(-(width / 2), -((height / (1 + math.sqrt(2))) / 2)), # 0
            QPointF(-(width / 2), +((height / (1 + math.sqrt(2))) / 2)), # 1
            QPointF(-((width / (1 + math.sqrt(2))) / 2), +(height / 2)), # 2
            QPointF(+((width / (1 + math.sqrt(2))) / 2), +(height / 2)), # 3
            QPointF(+(width / 2), +((height / (1 + math.sqrt(2))) / 2)), # 4
            QPointF(+(width / 2), -((height / (1 + math.sqrt(2))) / 2)), # 5
            QPointF(+((width / (1 + math.sqrt(2))) / 2), -(height / 2)), # 6
            QPointF(-((width / (1 + math.sqrt(2))) / 2), -(height / 2)), # 7
            QPointF(-(width / 2), -((height / (1 + math.sqrt(2))) / 2)), # 8
        ])
    
    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.polygon[self.indexTR].y() - self.polygon[self.indexBR].y()

    def interactiveResize(self, mousePos):
        """
        Handle the interactive resize of the shape.
        :type mousePos: QPointF
        """
        scene = self.scene()
        snap = scene.mainwindow.snapToGrid
        size = scene.GridSize
        offset = self.handleSize + self.handleMove
        moved = self.label.moved
        
        R = QRectF(self.boundingRect())
        D = QPointF(0, 0)

        minBoundW = self.minwidth + offset * 2
        minBoundH = self.minheight + offset * 2

        self.prepareGeometryChange()

        if self.mousePressHandle == self.handleTL:

            fromX = self.mousePressBound.left()
            fromY = self.mousePressBound.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapF(toX, size, -offset, snap)
            toY = snapF(toY, size, -offset, snap)
            D.setX(toX - fromX)
            D.setY(toY - fromY)
            R.setLeft(toX)
            R.setTop(toY)

            ## CLAMP SIZE
            if R.width() < minBoundW:
                D.setX(D.x() - minBoundW + R.width())
                R.setLeft(R.left() - minBoundW + R.width())
            if R.height() < minBoundH:
                D.setY(D.y() - minBoundH + R.height())
                R.setTop(R.top() - minBoundH + R.height())

            newSideY = (R.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (R.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSideY / 2
            newLeftRightTopY = (R.y() + R.height() / 2) - newSideY / 2
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSideX / 2
            newTopBottomRightX = (R.x() + R.width() / 2) + newSideX / 2

            self.selection.setLeft(R.left())
            self.selection.setTop(R.top())
            
            self.background[self.indexLT] = QPointF(R.left(), newLeftRightTopY)
            self.background[self.indexLB] = QPointF(R.left(), newLeftRightBottomY)
            self.background[self.indexRT] = QPointF(R.right(), newLeftRightTopY)
            self.background[self.indexRB] = QPointF(R.right(), newLeftRightBottomY)
            self.background[self.indexTL] = QPointF(newTopBottomLeftX, R.top())
            self.background[self.indexTR] = QPointF(newTopBottomRightX, R.top())
            self.background[self.indexBL] = QPointF(newTopBottomLeftX, R.bottom())
            self.background[self.indexBR] = QPointF(newTopBottomRightX, R.bottom())
            self.background[self.indexEE] = QPointF(R.left(), newLeftRightTopY)

            self.polygon[self.indexLT] = QPointF(R.left() + offset, newLeftRightTopY)
            self.polygon[self.indexLB] = QPointF(R.left() + offset, newLeftRightBottomY)
            self.polygon[self.indexRT] = QPointF(R.right() - offset, newLeftRightTopY)
            self.polygon[self.indexRB] = QPointF(R.right() - offset, newLeftRightBottomY)
            self.polygon[self.indexTL] = QPointF(newTopBottomLeftX, R.top() + offset)
            self.polygon[self.indexTR] = QPointF(newTopBottomRightX, R.top() + offset)
            self.polygon[self.indexBL] = QPointF(newTopBottomLeftX, R.bottom() - offset)
            self.polygon[self.indexBR] = QPointF(newTopBottomRightX, R.bottom() - offset)
            self.polygon[self.indexEE] = QPointF(R.left() + offset, newLeftRightTopY)

        elif self.mousePressHandle == self.handleTM:

            fromY = self.mousePressBound.top()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapF(toY, size, -offset, snap)
            D.setY(toY - fromY)
            R.setTop(toY)

            ## CLAMP SIZE
            if R.height() < minBoundH:
                D.setY(D.y() - minBoundH + R.height())
                R.setTop(R.top() - minBoundH + R.height())

            newSide = (R.height() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSide / 2
            newLeftRightTopY = (R.y() + R.height() / 2) - newSide / 2
            
            self.selection.setTop(R.top())
            
            self.background[self.indexTL] = QPointF(self.background[self.indexTL].x(), R.top())
            self.background[self.indexTR] = QPointF(self.background[self.indexTR].x(), R.top())
            self.background[self.indexLB] = QPointF(self.background[self.indexLB].x(), newLeftRightBottomY)
            self.background[self.indexRB] = QPointF(self.background[self.indexRB].x(), newLeftRightBottomY)
            self.background[self.indexLT] = QPointF(self.background[self.indexLT].x(), newLeftRightTopY)
            self.background[self.indexRT] = QPointF(self.background[self.indexRT].x(), newLeftRightTopY)
            self.background[self.indexEE] = QPointF(self.background[self.indexEE].x(), newLeftRightTopY)
            
            self.polygon[self.indexTL] = QPointF(self.polygon[self.indexTL].x(), R.top() + offset)
            self.polygon[self.indexTR] = QPointF(self.polygon[self.indexTR].x(), R.top() + offset)
            self.polygon[self.indexLB] = QPointF(self.polygon[self.indexLB].x(), newLeftRightBottomY)
            self.polygon[self.indexRB] = QPointF(self.polygon[self.indexRB].x(), newLeftRightBottomY)
            self.polygon[self.indexLT] = QPointF(self.polygon[self.indexLT].x(), newLeftRightTopY)
            self.polygon[self.indexRT] = QPointF(self.polygon[self.indexRT].x(), newLeftRightTopY)
            self.polygon[self.indexEE] = QPointF(self.polygon[self.indexEE].x(), newLeftRightTopY)

        elif self.mousePressHandle == self.handleTR:

            fromX = self.mousePressBound.right()
            fromY = self.mousePressBound.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapF(toX, size, +offset, snap)
            toY = snapF(toY, size, -offset, snap)
            D.setX(toX - fromX)
            D.setY(toY - fromY)
            R.setRight(toX)
            R.setTop(toY)

            ## CLAMP SIZE
            if R.width() < minBoundW:
                D.setX(D.x() + minBoundW - R.width())
                R.setRight(R.right() + minBoundW - R.width())
            if R.height() < minBoundH:
                D.setY(D.y() - minBoundH + R.height())
                R.setTop(R.top() - minBoundH + R.height())

            newSideY = (R.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (R.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSideY / 2
            newLeftRightTopY = (R.y() + R.height() / 2) - newSideY / 2
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSideX / 2
            newTopBottomRightX = (R.x() + R.width() / 2) + newSideX / 2
            
            self.selection.setRight(R.right())
            self.selection.setTop(R.top())
            
            self.background[self.indexLT] = QPointF(R.left(), newLeftRightTopY)
            self.background[self.indexLB] = QPointF(R.left(), newLeftRightBottomY)
            self.background[self.indexRT] = QPointF(R.right(), newLeftRightTopY)
            self.background[self.indexRB] = QPointF(R.right(), newLeftRightBottomY)
            self.background[self.indexTL] = QPointF(newTopBottomLeftX, R.top())
            self.background[self.indexTR] = QPointF(newTopBottomRightX, R.top())
            self.background[self.indexBL] = QPointF(newTopBottomLeftX, R.bottom())
            self.background[self.indexBR] = QPointF(newTopBottomRightX, R.bottom())
            self.background[self.indexEE] = QPointF(R.left(), newLeftRightTopY)
            
            self.polygon[self.indexLT] = QPointF(R.left() + offset, newLeftRightTopY)
            self.polygon[self.indexLB] = QPointF(R.left() + offset, newLeftRightBottomY)
            self.polygon[self.indexRT] = QPointF(R.right() - offset, newLeftRightTopY)
            self.polygon[self.indexRB] = QPointF(R.right() - offset, newLeftRightBottomY)
            self.polygon[self.indexTL] = QPointF(newTopBottomLeftX, R.top() + offset)
            self.polygon[self.indexTR] = QPointF(newTopBottomRightX, R.top() + offset)
            self.polygon[self.indexBL] = QPointF(newTopBottomLeftX, R.bottom() - offset)
            self.polygon[self.indexBR] = QPointF(newTopBottomRightX, R.bottom() - offset)
            self.polygon[self.indexEE] = QPointF(R.left() + offset, newLeftRightTopY)

        elif self.mousePressHandle == self.handleML:

            fromX = self.mousePressBound.left()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapF(toX, size, -offset, snap)
            D.setX(toX - fromX)
            R.setLeft(toX)

            ## CLAMP SIZE
            if R.width() < minBoundW:
                D.setX(D.x() - minBoundW + R.width())
                R.setLeft(R.left() - minBoundW + R.width())

            newSide = (R.width() - offset * 2) / (1 + math.sqrt(2))
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSide / 2
            newTopBottomRightX = (R.x() + R.width() / 2) + newSide / 2

            self.selection.setLeft(R.left())
            
            self.background[self.indexLT] = QPointF(R.left(), self.background[self.indexLT].y())
            self.background[self.indexLB] = QPointF(R.left(), self.background[self.indexLB].y())
            self.background[self.indexEE] = QPointF(R.left(), self.background[self.indexEE].y())
            self.background[self.indexTL] = QPointF(newTopBottomLeftX, self.background[self.indexTL].y())
            self.background[self.indexTR] = QPointF(newTopBottomRightX, self.background[self.indexTR].y())
            self.background[self.indexBL] = QPointF(newTopBottomLeftX, self.background[self.indexBL].y())
            self.background[self.indexBR] = QPointF(newTopBottomRightX, self.background[self.indexBR].y())
            
            self.polygon[self.indexLT] = QPointF(R.left() + offset, self.polygon[self.indexLT].y())
            self.polygon[self.indexLB] = QPointF(R.left() + offset, self.polygon[self.indexLB].y())
            self.polygon[self.indexEE] = QPointF(R.left() + offset, self.polygon[self.indexEE].y())
            self.polygon[self.indexTL] = QPointF(newTopBottomLeftX, self.polygon[self.indexTL].y())
            self.polygon[self.indexTR] = QPointF(newTopBottomRightX, self.polygon[self.indexTR].y())
            self.polygon[self.indexBL] = QPointF(newTopBottomLeftX, self.polygon[self.indexBL].y())
            self.polygon[self.indexBR] = QPointF(newTopBottomRightX, self.polygon[self.indexBR].y())

        elif self.mousePressHandle == self.handleMR:

            fromX = self.mousePressBound.right()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapF(toX, size, +offset, snap)
            D.setX(toX - fromX)
            R.setRight(toX)

            ## CLAMP SIZE
            if R.width() < minBoundW:
                D.setX(D.x() + minBoundW - R.width())
                R.setRight(R.right() + minBoundW - R.width())

            newSide = (R.width() - offset * 2) / (1 + math.sqrt(2))
            newTopBottomRightX = (R.x() + R.width() / 2) + newSide / 2
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSide / 2
            
            self.selection.setRight(R.right())
            
            self.background[self.indexRT] = QPointF(R.right(), self.background[self.indexRT].y())
            self.background[self.indexRB] = QPointF(R.right(), self.background[self.indexRB].y())
            self.background[self.indexTL] = QPointF(newTopBottomLeftX, self.background[self.indexTL].y())
            self.background[self.indexTR] = QPointF(newTopBottomRightX, self.background[self.indexTR].y())
            self.background[self.indexBL] = QPointF(newTopBottomLeftX, self.background[self.indexBL].y())
            self.background[self.indexBR] = QPointF(newTopBottomRightX, self.background[self.indexBR].y())
            
            self.polygon[self.indexRT] = QPointF(R.right() - offset, self.polygon[self.indexRT].y())
            self.polygon[self.indexRB] = QPointF(R.right() - offset, self.polygon[self.indexRB].y())
            self.polygon[self.indexTL] = QPointF(newTopBottomLeftX, self.polygon[self.indexTL].y())
            self.polygon[self.indexTR] = QPointF(newTopBottomRightX, self.polygon[self.indexTR].y())
            self.polygon[self.indexBL] = QPointF(newTopBottomLeftX, self.polygon[self.indexBL].y())
            self.polygon[self.indexBR] = QPointF(newTopBottomRightX, self.polygon[self.indexBR].y())

        elif self.mousePressHandle == self.handleBL:

            fromX = self.mousePressBound.left()
            fromY = self.mousePressBound.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapF(toX, size, -offset, snap)
            toY = snapF(toY, size, +offset, snap)
            D.setX(toX - fromX)
            D.setY(toY - fromY)
            R.setLeft(toX)
            R.setBottom(toY)

            ## CLAMP SIZE
            if R.width() < minBoundW:
                D.setX(D.x() - minBoundW + R.width())
                R.setLeft(R.left() - minBoundW + R.width())
            if R.height() < minBoundH:
                D.setY(D.y() + minBoundH - R.height())
                R.setBottom(R.bottom() + minBoundH - R.height())

            newSideY = (R.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (R.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSideY / 2
            newLeftRightTopY = (R.y() + R.height() / 2) - newSideY / 2
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSideX / 2
            newTopBottomRightX = (R.x() + R.width() / 2) + newSideX / 2
            
            self.selection.setLeft(R.left())
            self.selection.setBottom(R.bottom())
            
            self.background[self.indexLT] = QPointF(R.left(), newLeftRightTopY)
            self.background[self.indexLB] = QPointF(R.left(), newLeftRightBottomY)
            self.background[self.indexRT] = QPointF(R.right(), newLeftRightTopY)
            self.background[self.indexRB] = QPointF(R.right(), newLeftRightBottomY)
            self.background[self.indexTL] = QPointF(newTopBottomLeftX, R.top())
            self.background[self.indexTR] = QPointF(newTopBottomRightX, R.top())
            self.background[self.indexBL] = QPointF(newTopBottomLeftX, R.bottom())
            self.background[self.indexBR] = QPointF(newTopBottomRightX, R.bottom())
            self.background[self.indexEE] = QPointF(R.left(), newLeftRightTopY)
            
            self.polygon[self.indexLT] = QPointF(R.left() + offset, newLeftRightTopY)
            self.polygon[self.indexLB] = QPointF(R.left() + offset, newLeftRightBottomY)
            self.polygon[self.indexRT] = QPointF(R.right() - offset, newLeftRightTopY)
            self.polygon[self.indexRB] = QPointF(R.right() - offset, newLeftRightBottomY)
            self.polygon[self.indexTL] = QPointF(newTopBottomLeftX, R.top() + offset)
            self.polygon[self.indexTR] = QPointF(newTopBottomRightX, R.top() + offset)
            self.polygon[self.indexBL] = QPointF(newTopBottomLeftX, R.bottom() - offset)
            self.polygon[self.indexBR] = QPointF(newTopBottomRightX, R.bottom() - offset)
            self.polygon[self.indexEE] = QPointF(R.left() + offset, newLeftRightTopY)

        elif self.mousePressHandle == self.handleBM:

            fromY = self.mousePressBound.bottom()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapF(toY, size, +offset, snap)
            D.setY(toY - fromY)
            R.setBottom(toY)

            ## CLAMP SIZE
            if R.height() < minBoundH:
                D.setY(D.y() + minBoundH - R.height())
                R.setBottom(R.bottom() + minBoundH - R.height())

            newSide = (R.height() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightTopY = (R.y() + R.height() / 2) - newSide / 2
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSide / 2
            
            self.selection.setBottom(R.bottom())
            
            self.background[self.indexBL] = QPointF(self.background[self.indexBL].x(), R.bottom())
            self.background[self.indexBR] = QPointF(self.background[self.indexBR].x(), R.bottom())
            self.background[self.indexLB] = QPointF(self.background[self.indexLB].x(), newLeftRightBottomY)
            self.background[self.indexRB] = QPointF(self.background[self.indexRB].x(), newLeftRightBottomY)
            self.background[self.indexLT] = QPointF(self.background[self.indexLT].x(), newLeftRightTopY)
            self.background[self.indexRT] = QPointF(self.background[self.indexRT].x(), newLeftRightTopY)
            self.background[self.indexEE] = QPointF(self.background[self.indexEE].x(), newLeftRightTopY)
            
            self.polygon[self.indexBL] = QPointF(self.polygon[self.indexBL].x(), R.bottom() - offset)
            self.polygon[self.indexBR] = QPointF(self.polygon[self.indexBR].x(), R.bottom() - offset)
            self.polygon[self.indexLB] = QPointF(self.polygon[self.indexLB].x(), newLeftRightBottomY)
            self.polygon[self.indexRB] = QPointF(self.polygon[self.indexRB].x(), newLeftRightBottomY)
            self.polygon[self.indexLT] = QPointF(self.polygon[self.indexLT].x(), newLeftRightTopY)
            self.polygon[self.indexRT] = QPointF(self.polygon[self.indexRT].x(), newLeftRightTopY)
            self.polygon[self.indexEE] = QPointF(self.polygon[self.indexEE].x(), newLeftRightTopY)

        elif self.mousePressHandle == self.handleBR:

            fromX = self.mousePressBound.right()
            fromY = self.mousePressBound.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapF(toX, size, +offset, snap)
            toY = snapF(toY, size, +offset, snap)
            D.setX(toX - fromX)
            D.setY(toY - fromY)
            R.setRight(toX)
            R.setBottom(toY)

            ## CLAMP SIZE
            if R.width() < minBoundW:
                D.setX(D.x() + minBoundW - R.width())
                R.setRight(R.right() + minBoundW - R.width())
            if R.height() < minBoundH:
                D.setY(D.y() + minBoundH - R.height())
                R.setBottom(R.bottom() + minBoundH - R.height())

            newSideY = (R.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (R.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (R.y() + R.height() / 2) + newSideY / 2
            newLeftRightTopY = (R.y() + R.height() / 2) - newSideY / 2
            newTopBottomLeftX = (R.x() + R.width() / 2) - newSideX / 2
            newTopBottomRightX = (R.x() + R.width() / 2) + newSideX / 2

            self.selection.setRight(R.right())
            self.selection.setBottom(R.bottom())

            self.background[self.indexLT] = QPointF(R.left(), newLeftRightTopY)
            self.background[self.indexLB] = QPointF(R.left(), newLeftRightBottomY)
            self.background[self.indexRT] = QPointF(R.right(), newLeftRightTopY)
            self.background[self.indexRB] = QPointF(R.right(), newLeftRightBottomY)
            self.background[self.indexTL] = QPointF(newTopBottomLeftX, R.top())
            self.background[self.indexTR] = QPointF(newTopBottomRightX, R.top())
            self.background[self.indexBL] = QPointF(newTopBottomLeftX, R.bottom())
            self.background[self.indexBR] = QPointF(newTopBottomRightX, R.bottom())
            self.background[self.indexEE] = QPointF(R.left(), newLeftRightTopY)
            
            self.polygon[self.indexLT] = QPointF(R.left() + offset, newLeftRightTopY)
            self.polygon[self.indexLB] = QPointF(R.left() + offset, newLeftRightBottomY)
            self.polygon[self.indexRT] = QPointF(R.right() - offset, newLeftRightTopY)
            self.polygon[self.indexRB] = QPointF(R.right() - offset, newLeftRightBottomY)
            self.polygon[self.indexTL] = QPointF(newTopBottomLeftX, R.top() + offset)
            self.polygon[self.indexTR] = QPointF(newTopBottomRightX, R.top() + offset)
            self.polygon[self.indexBL] = QPointF(newTopBottomLeftX, R.bottom() - offset)
            self.polygon[self.indexBR] = QPointF(newTopBottomRightX, R.bottom() - offset)
            self.polygon[self.indexEE] = QPointF(R.left() + offset, newLeftRightTopY)

        self.updateHandles()
        self.updateTextPos(moved=moved)
        self.updateAnchors(self.mousePressData, D)

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.polygon[self.indexRT].x() - self.polygon[self.indexLT].x()

    ####################################################################################################################
    #                                                                                                                  #
    #   GEOMETRY                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QRectF
        """
        return self.selection

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPolygon(self.polygon)
        return path

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addPolygon(self.polygon)
        for shape in self.handleBound:
            path.addEllipse(shape)
        return path

    ####################################################################################################################
    #                                                                                                                  #
    #   LABEL SHORTCUTS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def textPos(self):
        """
        Returns the current label position in item coordinates.
        :rtype: QPointF
        """
        return self.label.pos()

    def text(self):
        """
        Returns the label text.
        :rtype: str
        """
        return self.label.text()

    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        self.label.setPos(pos)

    def setText(self, text):
        """
        Set the label text: will additionally block label editing if a literal is being.
        :type text: str
        """
        self.label.editable = RE_LITERAL.match(text) is None
        self.label.setText(text)

    def updateTextPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        self.label.updatePos(*args, **kwargs)

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
        # INITIALIZATION
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        polygon = cls.createPolygon(40, 40)
        # ITEM SHAPE
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawPolygon(polygon)
        # TEXT WITHIN THE SHAPE
        painter.setFont(Font('Arial', 9, Font.Light))
        painter.drawText(-18, 4, 'individual')
        return pixmap

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the diagram scene.
        :type painter: QPainter
        :type option: QStyleOptionGraphicsItem
        :type widget: QWidget
        """
        # SET THE RECT THAT NEEDS TO BE REPAINTED
        painter.setClipRect(option.exposedRect)
        # SELECTION AREA
        painter.setPen(self.selectionPen)
        painter.setBrush(self.selectionBrush)
        painter.drawRect(self.selection)
        # SYNTAX VALIDATION
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.backgroundPen)
        painter.setBrush(self.backgroundBrush)
        painter.drawPolygon(self.background)
        # ITEM SHAPE
        painter.setPen(self.pen)
        painter.setBrush(self.brush)
        painter.drawPolygon(self.polygon)
        # RESIZE HANDLES
        painter.setRenderHint(QPainter.Antialiasing)
        for i in range(self.handleNum):
            painter.setBrush(self.handleBrush[i])
            painter.setPen(self.handlePen[i])
            painter.drawEllipse(self.handleBound[i])