# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  pyGraphol: a python design tool for the Graphol language.             #
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


import math

from pygraphol.functions import distance, midpoint
from pygraphol.items.nodes.shapes.common import Label
from pygraphol.items.nodes.shapes.mixins import ShapeMixin
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF
from PyQt5.QtGui import QColor, QPen, QPainter, QPixmap, QFont, QPainterPath, QPolygonF, QBrush
from PyQt5.QtWidgets import QGraphicsEllipseItem


class Ring(QGraphicsEllipseItem, ShapeMixin):
    """
    This class implements a ring which is used to render the 'Attribute' node.
    """
    shapeRadius = 10.0
    shapePen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine)

    def __init__(self, **kwargs):
        """
        Initialize the ring shape.
        """
        super().__init__(**kwargs)
        self.setRect(Ring.getRect(self.shapeRadius * 2, self.shapeRadius * 2))
        self.label = Label(self.node.name, centered=False, parent=self)
        self.label.updatePos()

    ################################################## EVENT HANDLERS ##################################################

    def contextMenuEvent(self, menuEvent):
        """
        Bring up the context menu for the given node.
        :param menuEvent: the context menu event instance.
        """
        scene = self.scene()
        scene.clearSelection()

        self.setSelected(True)

        contextMenu = self.contextMenu()

        collection = self.label.contextMenuAdd()
        if collection:
            contextMenu.addSeparator()
            for action in collection:
                contextMenu.addAction(action)

        contextMenu.exec_(menuEvent.screenPos())

    ################################################ AUXILIARY METHODS #################################################

    @staticmethod
    def getRect(shape_w, shape_h):
        """
        Returns the initialized rect according to the given width/height.
        :param shape_w: the shape width.
        :param shape_h: the shape height.
        :rtype: QRectF
        """
        return QRectF(-shape_w / 2, -shape_h / 2, shape_w, shape_h)

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.rect().height()

    def intersection(self, line):
        """
        Returns the intersection of the shape with the given line (in scene coordinates).
        :param line: the line whose intersection needs to be calculated (in scene coordinates).
        :rtype: QPointF
        """
        path = QPainterPath()
        path.addEllipse(self.center(), self.width() / 2, self.height() / 2)
        polygon = self.mapToScene(path.toFillPolygon(self.transform()))

        intersection = QPointF()

        for i in range(0, polygon.size() - 1):
            polyline = QLineF(polygon[i], polygon[i + 1])
            if polyline.intersect(line, intersection) == QLineF.BoundedIntersection:
                return intersection

        return None

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.rect().width()

    ################################################### ITEM DRAWING ###################################################

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        shape_w = 18
        shape_h = 18

        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Draw the rectangle
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawEllipse(QRectF(-shape_w / 2, -shape_h / 2 + 8, shape_w, shape_h))

        # Draw the text within the rectangle
        painter.setFont(QFont('Arial', 10, QFont.Light))
        painter.drawText(-18, -6, 'attribute')

        return pixmap

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        :param painter: the active painter.
        :param option: the style option for this item.
        :param widget: the widget that is being painted on.
        """
        shapeBrush = self.shapeSelectedBrush if self.isSelected() else self.shapeBrush

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(shapeBrush)
        painter.setPen(self.shapePen)
        painter.drawEllipse(self.rect())

        self.paintAnchors(painter, option, widget)