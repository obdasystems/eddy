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


from math import sin, cos, radians, pi as M_PI
from pygraphol.items.edges.shapes import EdgeShape
from pygraphol.items.edges.shapes.common import Label
from PyQt5.QtCore import QPointF, Qt, QLineF
from PyQt5.QtGui import QPolygonF, QPixmap, QPainter, QPen, QColor, QFont


class NamedArrow(EdgeShape):
    """
    This class implements a arrow which is used to render the instanceOf edge.
    """
    def __init__(self, item, name, **kwargs):
        """
        Initialize the arrow shape.
        :param item: the edge attached to this shape.
        """
        super().__init__(item, **kwargs)
        self.label = Label(name, parent=self)

    ################################################ AUXILIARY METHODS #################################################

    def updateHead(self):
        """
        Update the Edge head polygon.
        """
        if not self.edge.target:
            ending = self.path[0].line
            head = ending.p2()
        else:
            intersection = self.getIntersectionWithShape(self.edge.target.shape)
            if intersection:
                ending = self.path[intersection[0]].line
                head = intersection[1]
            else:
                ending = self.path[-1].line
                head = ending.p2()

        angle = radians(ending.angle())

        p1 = head - QPointF(sin(angle + M_PI / 3.0) * self.size, cos(angle + M_PI / 3.0) * self.size)
        p2 = head - QPointF(sin(angle + M_PI - M_PI / 3.0) * self.size, cos(angle + M_PI - M_PI / 3.0) * self.size)

        self.head = QPolygonF([head, p1, p2])

    def updateLabelPos(self):
        """
        Update the label text position (shortcut for self.label.updatePos).
        """
        self.label.updatePos()

    def updateEdge(self, target=None):
        """
        Update the Edge line.
        :type target: QPointF
        :param target: the Edge new end point (when there is no endNode attached yet).
        """
        self.updateHandles()
        self.updatePath(target)
        self.updateZValue()
        self.updateHead()
        self.updateLabelPos()
        self.update()

    ################################################### ITEM DRAWING ###################################################

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        line_w = 54
        head_size = 8  # length of the head side
        head_span = 4  # offset between line end and head end (this is needed
                       # to prevent artifacts to be visible on low res screens)

        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Initialize the line
        line_p1 = QPointF(((kwargs['w'] - line_w) / 2), kwargs['h'] / 2)
        line_p2 = QPointF(((kwargs['w'] - line_w) / 2) + line_w - (head_span / 2), kwargs['h'] / 2)
        line = QLineF(line_p1, line_p2)

        angle = radians(line.angle())

        # Calculate head coordinates
        p1 = QPointF(line.p2().x() + (head_span / 2), line.p2().y())
        p2 = p1 - QPointF(sin(angle + M_PI / 3.0) * head_size, cos(angle + M_PI / 3.0) * head_size)
        p3 = p1 - QPointF(sin(angle + M_PI - M_PI / 3.0) * head_size, cos(angle + M_PI - M_PI / 3.0) * head_size)

        # Initialize edge head
        head = QPolygonF([p1, p2, p3])

        # Draw the polygon
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(line)

        # Draw the head
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QColor(0, 0, 0))
        painter.drawPolygon(head)

        # Draw the text within the rectangle
        painter.setFont(QFont('Arial', 9, QFont.Light))
        painter.drawText(line_p1.x() + 2,  (kwargs['h'] / 2) - 4, kwargs['name'])

        return pixmap

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        :param painter: the active painter.
        :param option: the style option for this item.
        :param widget: the widget that is being painted on.
        """
        if self.canDraw():
            super().paint(painter, option, widget)