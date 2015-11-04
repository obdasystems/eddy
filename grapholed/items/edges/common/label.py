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


from math import sin, cos, pi as M_PI
from grapholed.datatypes import Font
from grapholed.functions import midpoint, angleP
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QColor, QPainterPath
from PyQt5.QtWidgets import QGraphicsTextItem


class Label(QGraphicsTextItem):
    """
    This class implements the label to be attached to the graph edges.
    """
    def __init__(self, text='', parent=None):
        """
        Initialize the label.
        :param text: the text to be rendered on the label.
        :param parent: the parent node.
        """
        super().__init__(parent)
        self.setDefaultTextColor(QColor(0, 0, 0, 255))
        self.setFont(Font('Arial', 12, Font.Light))
        self.setText(text)
        self.setTextInteractionFlags(Qt.NoTextInteraction)

    ################################################### GEOMETRY #######################################################

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    ################################################ ITEM INTERFACE ####################################################

    def center(self):
        """
        Returns the point at the center of the shape.
        :rtype: QPointF
        """
        return self.boundingRect().center()

    def height(self):
        """
        Returns the height of the text label.
        :rtype: int
        """
        return self.boundingRect().height()

    def pos(self):
        """
        Returns the position of the label in parent's item coordinates.
        :rtype: QPointF
        """
        return self.mapToParent(self.center())

    def setPos(self, pos):
        """
        Set the item position.
        :param pos: the position in parent's item coordinates.
        """
        super().setPos(pos - QPointF(self.width() / 2, self.height() / 2))

    def setText(self, text):
        """
        Set the given text as plain text.
        :param text: the text value to set.
        """
        self.setPlainText(text)

    def text(self):
        """
        Returns the current shape text (shortcut for self.toPlainText()).
        :return: str
        """
        return self.toPlainText()

    def updatePos(self, points):
        """
        Update the current text position with respect to the shape.
        :param points: a list of points defining the edge of this label.
        """
        if not points:
            return

        if len(points) % 2 == 0:

            # if we have an even number of points, compute the position of the label
            # according to the middle point of the subpath connecting the middle points
            p1 = points[int(len(points) / 2) - 1]
            p2 = points[int(len(points) / 2)]

            mid = midpoint(p1, p2)
            rad = angleP(p1, p2)

            spaceX = -40
            spaceY = -16

            self.setPos(QPointF(mid.x() + spaceX * sin(rad), mid.y() + spaceY * cos(rad)))

        else:

            # if we have an even number of points compute the
            # position of the label according the point in the middle
            mid = points[int(len(points) / 2)]
            rad1 = angleP(points[int(len(points) / 2) - 1], mid)
            rad2 = angleP(mid, points[int(len(points) / 2) + 1])
            diff = rad2 - rad1

            spaceX1 = 0
            spaceX2 = 0
            spaceY = -16

            if 0 < diff < M_PI:
                spaceX1 = -80 * sin(rad1)
                spaceX2 = -80 * sin(rad2)
                spaceY += spaceY * sin(diff) * 1.8

            self.setPos(QPointF(mid.x() + spaceX1 + spaceX2, mid.y() + spaceY))

    def width(self):
        """
        Returns the width of the text label.
        :rtype: int
        """
        return self.boundingRect().width()

    ################################################## ITEM DRAWING ####################################################

    def paint(self, painter, option, widget=None):
        """
        Paint the label in the graphic view.
        :param painter: the active painter.
        :param option: the style option for this item.
        :param widget: the widget that is being painted on.
        """
        parent = self.parentItem()
        if not parent.path.isEmpty():
            super().paint(painter, option, widget)
