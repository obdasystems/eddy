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


from pygraphol.items.nodes.shapes.mixins import ShapeMixin
from PyQt5.QtCore import QRectF, Qt, QPointF, QLineF
from PyQt5.QtGui import QPainter, QPainterPath, QPixmap, QColor, QPen, QPolygonF
from PyQt5.QtWidgets import QGraphicsRectItem


class Oval(QGraphicsRectItem, ShapeMixin):
    """
    This class implements an oval which is used to render the 'PropertyAssertion' node.
    """
    BorderRadius = 20
    MinWidth = 80
    MinHeight = 40

    def __init__(self, **kwargs):
        """
        Initialize the rounded rectangle shape.
        """
        super().__init__(**kwargs)
        self.setRect(Oval.getRect(Oval.MinWidth, Oval.MinHeight))

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
        contextMenu.exec_(menuEvent.screenPos())

    ###################################################### GEOMETRY ####################################################

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRoundedRect(self.rect(), self.BorderRadius, self.BorderRadius)
        return path

    ################################################## AUXILIARY METHODS ###############################################

    @staticmethod
    def getRect(shape_w, shape_h):
        """
        Returns the initialized rect according to the given width/height.
        :param shape_w: the shape width
        :param shape_h: the shape height
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
        path.addRoundedRect(self.rect(), self.BorderRadius, self.BorderRadius)
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
        shape_w = 50
        shape_h = 30
        radius = 14

        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)

        # Initialize the shape
        rect = Oval.getRect(shape_w, shape_h)

        # Draw the rectangle
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawRoundedRect(rect, radius, radius)

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
        painter.drawRoundedRect(self.rect(), self.BorderRadius, self.BorderRadius)