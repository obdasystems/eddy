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


from abc import ABCMeta
from collections import OrderedDict

from grapholed.commands import CommandNodeHexagonSwitchTo
from grapholed.functions import connect
from grapholed.items.nodes.common.base import Node

from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath, QIcon, QPolygonF
from PyQt5.QtWidgets import QAction


class HexagonNode(Node):
    """
    This is the base class for all the Hexagon shaped nodes.
    """
    __metaclass__ = ABCMeta

    indexML = 0
    indexBL = 1
    indexBR = 2
    indexMR = 3
    indexTR = 4
    indexTL = 5
    indexEE = 6

    diagonalSize = 6
    minHeight = 30
    minWidth = 50
    shapePen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine)

    def __init__(self, width=minWidth, height=minHeight, brush=(252, 252, 252), **kwargs):
        """
        Initialize the Hexagon shaped node.
        :param width: the shape width (unused in current implementation).
        :param height: the shape height (unused in current implementation).
        :param brush: the brush to use as shape background
        """
        super().__init__(**kwargs)
        self.shapeBrush = QColor(*brush)
        self.polygon = self.createPolygon(self.minWidth, self.minHeight, self.diagonalSize)

    ################################################ ITEM INTERFACE ####################################################

    def contextMenu(self):
        """
        Returns the basic nodes context menu.
        :rtype: QMenu
        """
        menu = super().contextMenu()
        menu.addSeparator()

        data = OrderedDict()

        from grapholed.items.nodes import UnionNode, DisjointUnionNode
        from grapholed.items.nodes import EnumerationNode, RoleChainNode, RoleInverseNode
        from grapholed.items.nodes import ComplementNode, IntersectionNode, DatatypeRestrictionNode

        data[ComplementNode] = 'Complement'
        data[DisjointUnionNode] = 'Disjoint union'
        data[DatatypeRestrictionNode] = 'Datatype restriction'
        data[EnumerationNode] = 'Enumeration'
        data[IntersectionNode] = 'Intersection'
        data[RoleChainNode] = 'Role chain'
        data[RoleInverseNode] = 'Role inverse'
        data[UnionNode] = 'Union'

        subMenu = menu.addMenu('Switch to')
        subMenu.setIcon(QIcon(':/icons/refresh'))

        scene = self.scene()

        for k, v in data.items():
            if not isinstance(self, k):
                action = QAction(v, scene)
                connect(action.triggered, self.switchTo, clazz=k)
                subMenu.addAction(action)
                
        return menu

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.polygon[self.indexBL].y() - self.polygon[self.indexTL].y()

    def switchTo(self, clazz):
        """
        Switch the current node to a different type.
        :param clazz: the class implementing the new node type.
        """
        scene = self.scene()
        xnode = clazz(scene=scene)
        xnode.setPos(self.pos())
        scene.undoStack.push(CommandNodeHexagonSwitchTo(scene, self, xnode))

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.polygon[self.indexMR].x() - self.polygon[self.indexML].x()

    ############################################### AUXILIARY METHODS ##################################################

    @staticmethod
    def createPolygon(shape_w, shape_h, oblique):
        """
        Returns the initialized polygon according to the given width/height.
        :param shape_w: the shape width.
        :param shape_h: the shape height.
        :param oblique: the width of the oblique side.
        :rtype: QPolygonF
        """
        return QPolygonF([
            QPointF(-shape_w / 2, 0),                       # 0
            QPointF(-shape_w / 2 + oblique, +shape_h / 2),  # 1
            QPointF(+shape_w / 2 - oblique, +shape_h / 2),  # 2
            QPointF(+shape_w / 2, 0),                       # 3
            QPointF(+shape_w / 2 - oblique, -shape_h / 2),  # 4
            QPointF(-shape_w / 2 + oblique, -shape_h / 2),  # 5
            QPointF(-shape_w / 2, 0)                        # 6
        ])

    #################################################### GEOMETRY ######################################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QRectF
        """
        x = self.polygon[self.indexML].x()
        y = self.polygon[self.indexTL].y()
        w = self.polygon[self.indexMR].x() - x
        h = self.polygon[self.indexBL].y() - y
        return QRectF(x, y, w, h)

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
        return path

    ################################################# LABEL SHORTCUTS ##################################################

    def labelPos(self):
        """
        Returns the current label position in item coordinates.
        :rtype: QPointF
        """
        pass

    def labelText(self):
        """
        Returns the label text.
        :rtype: str
        """
        pass

    def setLabelPos(self, pos):
        """
        Set the label position.
        :param pos: the node position in item coordinates.
        """
        pass

    def setLabelText(self, text):
        """
        Set the label text.
        :param text: the text value to set.
        """
        pass

    def updateLabelPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        pass

    ################################################## ITEM DRAWING ####################################################

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        :param painter: the active painter.
        :param option: the style option for this item.
        :param widget: the widget that is being painted on.
        """
        shapeBrush = self.shapeBrushSelected if self.isSelected() else self.shapeBrush

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(shapeBrush)
        painter.setPen(self.shapePen)
        painter.drawPolygon(self.polygon)
