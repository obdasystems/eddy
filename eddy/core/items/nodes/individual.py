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
from PyQt5.QtGui import QPolygonF, QPainterPath, QPainter, QPen, QColor, QPixmap

from eddy.core.datatypes import DiagramMode, Font, Identity, Item, XsdDatatype
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
    xmlname = 'individual'

    def __init__(self, width=minwidth, height=minheight, brush='#fcfcfc', **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: T <= QBrush | QColor | Color | tuple | list | bytes | unicode
        """
        super().__init__(**kwargs)
        self.brush = brush
        self.pen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine)
        self.polygon = self.createPolygon(max(width, self.minwidth), max(height, self.minheight))
        self.label = Label('individual', parent=self)
        self.label.updatePos()
        self.updateHandlesPos()

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
            'scene': scene,
            'id': self.id,
            'description': self.description,
            'url': self.url,
            'width': self.width(),
            'height': self.height(),
        }

        node = self.__class__(**kwargs)
        node.setPos(self.pos())
        node.setText(self.text())
        node.setTextPos(node.mapFromScene(self.mapToScene(self.textPos())))
        return node

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.boundingRect().height() - 2 * (self.handleSize + self.handleSpace)

    # noinspection PyTypeChecker
    def interactiveResize(self, mousePos):
        """
        Handle the interactive resize of the shape.
        :type mousePos: QPointF
        """
        offset = self.handleSize + self.handleSpace
        moved = self.label.moved
        scene = self.scene()
        snap = scene.settings.value('scene/snap_to_grid', False, bool)
        rect = self.boundingRect()
        diff = QPointF(0, 0)

        minBoundingRectW = self.minwidth + offset * 2
        minBoundingRectH = self.minheight + offset * 2

        self.prepareGeometryChange()

        if self.handleSelected == self.handleTL:

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapF(toX, scene.GridSize, -offset, snap)
            toY = snapF(toY, scene.GridSize, -offset, snap)
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            rect.setLeft(toX)
            rect.setTop(toY)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectW:
                diff.setX(diff.x() - minBoundingRectW + rect.width())
                rect.setLeft(rect.left() - minBoundingRectW + rect.width())
            if rect.height() < minBoundingRectH:
                diff.setY(diff.y() - minBoundingRectH + rect.height())
                rect.setTop(rect.top() - minBoundingRectH + rect.height())

            newSideY = (rect.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (rect.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (rect.y() + rect.height() / 2) + newSideY / 2
            newLeftRightTopY = (rect.y() + rect.height() / 2) - newSideY / 2
            newTopBottomLeftX = (rect.x() + rect.width() / 2) - newSideX / 2
            newTopBottomRightX = (rect.x() + rect.width() / 2) + newSideX / 2

            self.polygon[self.indexLT] = QPointF(rect.left() + offset, newLeftRightTopY)
            self.polygon[self.indexLB] = QPointF(rect.left() + offset, newLeftRightBottomY)
            self.polygon[self.indexRT] = QPointF(rect.right() - offset, newLeftRightTopY)
            self.polygon[self.indexRB] = QPointF(rect.right() - offset, newLeftRightBottomY)
            self.polygon[self.indexTL] = QPointF(newTopBottomLeftX, rect.top() + offset)
            self.polygon[self.indexTR] = QPointF(newTopBottomRightX, rect.top() + offset)
            self.polygon[self.indexBL] = QPointF(newTopBottomLeftX, rect.bottom() - offset)
            self.polygon[self.indexBR] = QPointF(newTopBottomRightX, rect.bottom() - offset)
            self.polygon[self.indexEE] = QPointF(rect.left() + offset, newLeftRightTopY)

        elif self.handleSelected == self.handleTM:

            fromY = self.mousePressRect.top()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapF(toY, scene.GridSize, -offset, snap)
            diff.setY(toY - fromY)
            rect.setTop(toY)

            ## CLAMP SIZE
            if rect.height() < minBoundingRectH:
                diff.setY(diff.y() - minBoundingRectH + rect.height())
                rect.setTop(rect.top() - minBoundingRectH + rect.height())

            newSide = (rect.height() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (rect.y() + rect.height() / 2) + newSide / 2
            newLeftRightTopY = (rect.y() + rect.height() / 2) - newSide / 2

            self.polygon[self.indexTL] = QPointF(self.polygon[self.indexTL].x(), rect.top() + offset)
            self.polygon[self.indexTR] = QPointF(self.polygon[self.indexTR].x(), rect.top() + offset)
            self.polygon[self.indexLB] = QPointF(self.polygon[self.indexLB].x(), newLeftRightBottomY)
            self.polygon[self.indexRB] = QPointF(self.polygon[self.indexRB].x(), newLeftRightBottomY)
            self.polygon[self.indexLT] = QPointF(self.polygon[self.indexLT].x(), newLeftRightTopY)
            self.polygon[self.indexRT] = QPointF(self.polygon[self.indexRT].x(), newLeftRightTopY)
            self.polygon[self.indexEE] = QPointF(self.polygon[self.indexEE].x(), newLeftRightTopY)

        elif self.handleSelected == self.handleTR:

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapF(toX, scene.GridSize, +offset, snap)
            toY = snapF(toY, scene.GridSize, -offset, snap)
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            rect.setRight(toX)
            rect.setTop(toY)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectW:
                diff.setX(diff.x() + minBoundingRectW - rect.width())
                rect.setRight(rect.right() + minBoundingRectW - rect.width())
            if rect.height() < minBoundingRectH:
                diff.setY(diff.y() - minBoundingRectH + rect.height())
                rect.setTop(rect.top() - minBoundingRectH + rect.height())

            newSideY = (rect.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (rect.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (rect.y() + rect.height() / 2) + newSideY / 2
            newLeftRightTopY = (rect.y() + rect.height() / 2) - newSideY / 2
            newTopBottomLeftX = (rect.x() + rect.width() / 2) - newSideX / 2
            newTopBottomRightX = (rect.x() + rect.width() / 2) + newSideX / 2

            self.polygon[self.indexLT] = QPointF(rect.left() + offset, newLeftRightTopY)
            self.polygon[self.indexLB] = QPointF(rect.left() + offset, newLeftRightBottomY)
            self.polygon[self.indexRT] = QPointF(rect.right() - offset, newLeftRightTopY)
            self.polygon[self.indexRB] = QPointF(rect.right() - offset, newLeftRightBottomY)
            self.polygon[self.indexTL] = QPointF(newTopBottomLeftX, rect.top() + offset)
            self.polygon[self.indexTR] = QPointF(newTopBottomRightX, rect.top() + offset)
            self.polygon[self.indexBL] = QPointF(newTopBottomLeftX, rect.bottom() - offset)
            self.polygon[self.indexBR] = QPointF(newTopBottomRightX, rect.bottom() - offset)
            self.polygon[self.indexEE] = QPointF(rect.left() + offset, newLeftRightTopY)

        elif self.handleSelected == self.handleML:

            fromX = self.mousePressRect.left()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapF(toX, scene.GridSize, -offset, snap)
            diff.setX(toX - fromX)
            rect.setLeft(toX)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectW:
                diff.setX(diff.x() - minBoundingRectW + rect.width())
                rect.setLeft(rect.left() - minBoundingRectW + rect.width())

            newSide = (rect.width() - offset * 2) / (1 + math.sqrt(2))
            newTopBottomLeftX = (rect.x() + rect.width() / 2) - newSide / 2
            newTopBottomRightX = (rect.x() + rect.width() / 2) + newSide / 2

            self.polygon[self.indexLT] = QPointF(rect.left() + offset, self.polygon[self.indexLT].y())
            self.polygon[self.indexLB] = QPointF(rect.left() + offset, self.polygon[self.indexLB].y())
            self.polygon[self.indexEE] = QPointF(rect.left() + offset, self.polygon[self.indexEE].y())
            self.polygon[self.indexTL] = QPointF(newTopBottomLeftX, self.polygon[self.indexTL].y())
            self.polygon[self.indexTR] = QPointF(newTopBottomRightX, self.polygon[self.indexTR].y())
            self.polygon[self.indexBL] = QPointF(newTopBottomLeftX, self.polygon[self.indexBL].y())
            self.polygon[self.indexBR] = QPointF(newTopBottomRightX, self.polygon[self.indexBR].y())

        elif self.handleSelected == self.handleMR:

            fromX = self.mousePressRect.right()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toX = snapF(toX, scene.GridSize, +offset, snap)
            diff.setX(toX - fromX)
            rect.setRight(toX)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectW:
                diff.setX(diff.x() + minBoundingRectW - rect.width())
                rect.setRight(rect.right() + minBoundingRectW - rect.width())

            newSide = (rect.width() - offset * 2) / (1 + math.sqrt(2))
            newTopBottomRightX = (rect.x() + rect.width() / 2) + newSide / 2
            newTopBottomLeftX = (rect.x() + rect.width() / 2) - newSide / 2

            self.polygon[self.indexRT] = QPointF(rect.right() - offset, self.polygon[self.indexRT].y())
            self.polygon[self.indexRB] = QPointF(rect.right() - offset, self.polygon[self.indexRB].y())
            self.polygon[self.indexTL] = QPointF(newTopBottomLeftX, self.polygon[self.indexTL].y())
            self.polygon[self.indexTR] = QPointF(newTopBottomRightX, self.polygon[self.indexTR].y())
            self.polygon[self.indexBL] = QPointF(newTopBottomLeftX, self.polygon[self.indexBL].y())
            self.polygon[self.indexBR] = QPointF(newTopBottomRightX, self.polygon[self.indexBR].y())

        elif self.handleSelected == self.handleBL:

            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapF(toX, scene.GridSize, -offset, snap)
            toY = snapF(toY, scene.GridSize, +offset, snap)
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            rect.setLeft(toX)
            rect.setBottom(toY)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectW:
                diff.setX(diff.x() - minBoundingRectW + rect.width())
                rect.setLeft(rect.left() - minBoundingRectW + rect.width())
            if rect.height() < minBoundingRectH:
                diff.setY(diff.y() + minBoundingRectH - rect.height())
                rect.setBottom(rect.bottom() + minBoundingRectH - rect.height())

            newSideY = (rect.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (rect.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (rect.y() + rect.height() / 2) + newSideY / 2
            newLeftRightTopY = (rect.y() + rect.height() / 2) - newSideY / 2
            newTopBottomLeftX = (rect.x() + rect.width() / 2) - newSideX / 2
            newTopBottomRightX = (rect.x() + rect.width() / 2) + newSideX / 2

            self.polygon[self.indexLT] = QPointF(rect.left() + offset, newLeftRightTopY)
            self.polygon[self.indexLB] = QPointF(rect.left() + offset, newLeftRightBottomY)
            self.polygon[self.indexRT] = QPointF(rect.right() - offset, newLeftRightTopY)
            self.polygon[self.indexRB] = QPointF(rect.right() - offset, newLeftRightBottomY)
            self.polygon[self.indexTL] = QPointF(newTopBottomLeftX, rect.top() + offset)
            self.polygon[self.indexTR] = QPointF(newTopBottomRightX, rect.top() + offset)
            self.polygon[self.indexBL] = QPointF(newTopBottomLeftX, rect.bottom() - offset)
            self.polygon[self.indexBR] = QPointF(newTopBottomRightX, rect.bottom() - offset)
            self.polygon[self.indexEE] = QPointF(rect.left() + offset, newLeftRightTopY)

        elif self.handleSelected == self.handleBM:

            fromY = self.mousePressRect.bottom()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toY = snapF(toY, scene.GridSize, +offset, snap)
            diff.setY(toY - fromY)
            rect.setBottom(toY)

            ## CLAMP SIZE
            if rect.height() < minBoundingRectH:
                diff.setY(diff.y() + minBoundingRectH - rect.height())
                rect.setBottom(rect.bottom() + minBoundingRectH - rect.height())

            newSide = (rect.height() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightTopY = (rect.y() + rect.height() / 2) - newSide / 2
            newLeftRightBottomY = (rect.y() + rect.height() / 2) + newSide / 2

            self.polygon[self.indexBL] = QPointF(self.polygon[self.indexBL].x(), rect.bottom() - offset)
            self.polygon[self.indexBR] = QPointF(self.polygon[self.indexBR].x(), rect.bottom() - offset)
            self.polygon[self.indexLB] = QPointF(self.polygon[self.indexLB].x(), newLeftRightBottomY)
            self.polygon[self.indexRB] = QPointF(self.polygon[self.indexRB].x(), newLeftRightBottomY)
            self.polygon[self.indexLT] = QPointF(self.polygon[self.indexLT].x(), newLeftRightTopY)
            self.polygon[self.indexRT] = QPointF(self.polygon[self.indexRT].x(), newLeftRightTopY)
            self.polygon[self.indexEE] = QPointF(self.polygon[self.indexEE].x(), newLeftRightTopY)

        elif self.handleSelected == self.handleBR:

            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            toX = snapF(toX, scene.GridSize, +offset, snap)
            toY = snapF(toY, scene.GridSize, +offset, snap)
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            rect.setRight(toX)
            rect.setBottom(toY)

            ## CLAMP SIZE
            if rect.width() < minBoundingRectW:
                diff.setX(diff.x() + minBoundingRectW - rect.width())
                rect.setRight(rect.right() + minBoundingRectW - rect.width())
            if rect.height() < minBoundingRectH:
                diff.setY(diff.y() + minBoundingRectH - rect.height())
                rect.setBottom(rect.bottom() + minBoundingRectH - rect.height())

            newSideY = (rect.height() - offset * 2) / (1 + math.sqrt(2))
            newSideX = (rect.width() - offset * 2) / (1 + math.sqrt(2))
            newLeftRightBottomY = (rect.y() + rect.height() / 2) + newSideY / 2
            newLeftRightTopY = (rect.y() + rect.height() / 2) - newSideY / 2
            newTopBottomLeftX = (rect.x() + rect.width() / 2) - newSideX / 2
            newTopBottomRightX = (rect.x() + rect.width() / 2) + newSideX / 2

            self.polygon[self.indexLT] = QPointF(rect.left() + offset, newLeftRightTopY)
            self.polygon[self.indexLB] = QPointF(rect.left() + offset, newLeftRightBottomY)
            self.polygon[self.indexRT] = QPointF(rect.right() - offset, newLeftRightTopY)
            self.polygon[self.indexRB] = QPointF(rect.right() - offset, newLeftRightBottomY)
            self.polygon[self.indexTL] = QPointF(newTopBottomLeftX, rect.top() + offset)
            self.polygon[self.indexTR] = QPointF(newTopBottomRightX, rect.top() + offset)
            self.polygon[self.indexBL] = QPointF(newTopBottomLeftX, rect.bottom() - offset)
            self.polygon[self.indexBR] = QPointF(newTopBottomRightX, rect.bottom() - offset)
            self.polygon[self.indexEE] = QPointF(rect.left() + offset, newLeftRightTopY)

        self.updateHandlesPos()
        self.updateTextPos(moved=moved)
        self.updateAnchors(self.mousePressData, diff)

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.boundingRect().width() - 2 * (self.handleSize + self.handleSpace)

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    @staticmethod
    def createPolygon(shape_w, shape_h):
        """
        Returns the initialized polygon according to the given width/height.
        :type shape_w: int
        :type shape_h: int
        :rtype: QPolygonF
        """
        return QPolygonF([
            QPointF(-(shape_w / 2), -((shape_h / (1 + math.sqrt(2))) / 2)), # 0
            QPointF(-(shape_w / 2), +((shape_h / (1 + math.sqrt(2))) / 2)), # 1
            QPointF(-((shape_w / (1 + math.sqrt(2))) / 2), +(shape_h / 2)), # 2
            QPointF(+((shape_w / (1 + math.sqrt(2))) / 2), +(shape_h / 2)), # 3
            QPointF(+(shape_w / 2), +((shape_h / (1 + math.sqrt(2))) / 2)), # 4
            QPointF(+(shape_w / 2), -((shape_h / (1 + math.sqrt(2))) / 2)), # 5
            QPointF(+((shape_w / (1 + math.sqrt(2))) / 2), -(shape_h / 2)), # 6
            QPointF(-((shape_w / (1 + math.sqrt(2))) / 2), -(shape_h / 2)), # 7
            QPointF(-(shape_w / 2), -((shape_h / (1 + math.sqrt(2))) / 2)), # 8
        ])

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
        :rtype: Node
        """
        U = E.elementsByTagName('data:url').at(0).toElement()
        D = E.elementsByTagName('data:description').at(0).toElement()
        G = E.elementsByTagName('shape:geometry').at(0).toElement()
        L = E.elementsByTagName('shape:label').at(0).toElement()

        kwargs = {
            'brush': E.attribute('color', '#fcfcfc'),
            'description': D.text(),
            'height': int(G.attribute('height')),
            'id': E.attribute('id'),
            'scene': scene,
            'url': U.text(),
            'width': int(G.attribute('width')),
        }

        node = cls(**kwargs)
        node.setPos(QPointF(int(G.attribute('x')), int(G.attribute('y'))))
        node.setText(L.text())
        node.setTextPos(node.mapFromScene(QPointF(int(L.attribute('x')), int(L.attribute('y')))))
        return node

    def toGraphol(self, document):
        """
        Export the current item in Graphol format.
        :type document: QDomDocument
        :rtype: QDomElement
        """
        pos1 = self.pos()
        pos2 = self.mapToScene(self.textPos())

        # create the root element for this node
        node = document.createElement('node')
        node.setAttribute('id', self.id)
        node.setAttribute('type', self.xmlname)
        node.setAttribute('color', self.brush.color().name())

        # add node attributes
        url = document.createElement('data:url')
        url.appendChild(document.createTextNode(self.url))
        description = document.createElement('data:description')
        description.appendChild(document.createTextNode(self.description))

        # add the shape geometry
        geometry = document.createElement('shape:geometry')
        geometry.setAttribute('height', self.height())
        geometry.setAttribute('width', self.width())
        geometry.setAttribute('x', pos1.x())
        geometry.setAttribute('y', pos1.y())

        # add the shape label
        label = document.createElement('shape:label')
        label.setAttribute('height', self.label.height())
        label.setAttribute('width', self.label.width())
        label.setAttribute('x', pos2.x())
        label.setAttribute('y', pos2.y())
        label.appendChild(document.createTextNode(self.label.text()))

        node.appendChild(url)
        node.appendChild(description)
        node.appendChild(geometry)
        node.appendChild(label)

        return node

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
        o = self.handleSize + self.handleSpace
        x = self.polygon[self.indexLT].x()
        y = self.polygon[self.indexTL].y()
        w = self.polygon[self.indexRT].x() - x
        h = self.polygon[self.indexBL].y() - y
        return QRectF(x - o, y - o, w + o * 2, h + o * 2)

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

        if self.isSelected():
            for shape in self.handles.values():
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

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        :type painter: QPainter
        :type option: int
        :type widget: QWidget
        """
        scene = self.scene()

        if scene.mode is not DiagramMode.NodeResize and self.isSelected():
            painter.setPen(self.selectionPen)
            painter.drawRect(self.boundingRect())

        if scene.mode is DiagramMode.EdgeInsert and scene.mouseOverNode is self:

            edge = scene.command.edge
            brush = self.brushConnectionOk
            if not scene.validator.valid(edge.source, edge, scene.mouseOverNode):
                brush = self.brushConnectionBad

            boundingRect = self.boundingRect()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(brush)
            painter.drawPolygon(self.createPolygon(boundingRect.width(), boundingRect.height()))

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        painter.drawPolygon(self.polygon)
        self.paintHandles(painter)

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Initialize the shape
        polygon = cls.createPolygon(40, 40)

        # Draw the polygon
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawPolygon(polygon)

        # Draw the text within the rectangle
        painter.setFont(Font('Arial', 9, Font.Light))
        painter.drawText(-18, 4, 'individual')

        return pixmap