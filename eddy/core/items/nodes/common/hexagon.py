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


from abc import ABCMeta, abstractmethod

from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath, QPolygonF

from eddy.core.datatypes import DiagramMode
from eddy.core.items.nodes.common.base import AbstractNode


class HexagonNode(AbstractNode):
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

    def __init__(self, width=50, height=30, brush='#fcfcfc', **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: T <= QBrush | QColor | Color | tuple | list | bytes | unicode
        """
        super().__init__(**kwargs)
        self.brush = brush
        self.pen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine)
        self.polygon = self.createPolygon(shape_w=50, shape_h=30, oblique=6)

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    @abstractmethod
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        pass

    @identity.setter
    @abstractmethod
    def identity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def contextMenu(self):
        """
        Returns the basic nodes context menu.
        :rtype: QMenu
        """
        scene = self.scene()
        menu = super().contextMenu()
        menu.insertMenu(scene.mainwindow.actionOpenNodeProperties, scene.mainwindow.menuHexagonNodeSwitch)

        # switch the check matching the current node
        for action in scene.mainwindow.actionsSwitchHexagonNode:
            action.setChecked(isinstance(self, action.data()))
            action.setVisible(True)

        menu.insertSeparator(scene.mainwindow.actionOpenNodeProperties)
        return menu

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.polygon[self.indexBL].y() - self.polygon[self.indexTL].y()

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.polygon[self.indexMR].x() - self.polygon[self.indexML].x()

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    @staticmethod
    def createPolygon(shape_w, shape_h, oblique):
        """
        Returns the initialized polygon according to the given width/height.
        :type shape_w: int
        :type shape_h: int
        :type oblique: int
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
        o = self.selectionOffset
        x = self.polygon[self.indexML].x()
        y = self.polygon[self.indexTL].y()
        w = self.polygon[self.indexMR].x() - x
        h = self.polygon[self.indexBL].y() - y
        return QRectF(x, y, w, h).adjusted(-o, -o, o, o)

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

    ####################################################################################################################
    #                                                                                                                  #
    #   LABEL SHORTCUTS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

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
        :type pos: QPointF
        """
        pass

    def setLabelText(self, text):
        """
        Set the label text.
        :type text: T <= bytes | unicode
        """
        pass

    def updateLabelPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        pass

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

        if self.isSelected():
            painter.setPen(self.selectionPen)
            painter.drawRect(self.boundingRect())

        if scene.mode is DiagramMode.EdgeInsert and scene.mouseOverNode is self:
            edge = scene.command.edge

            brush = self.brushConnectionOk
            if not scene.validator.check(edge.source, edge, scene.mouseOverNode):
                brush = self.brushConnectionBad

            boundingRect = self.boundingRect()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(brush)
            painter.drawPolygon(self.createPolygon(boundingRect.width(), boundingRect.height(), 6))

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        painter.drawPolygon(self.polygon)
