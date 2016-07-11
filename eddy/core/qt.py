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


from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPainterPath
from PyQt5.QtGui import QColor, QBrush, QPen, QFont
from PyQt5.QtWidgets import QPushButton, QToolButton

from eddy.core.datatypes.system import Platform


class Font(QFont):
    """
    This class extends QFont providing better font rendering on different platforms.
    """
    def __init__(self, family, size=12, weight=-1, italic=False):
        """
        Contruct a new Font instance using the given parameters.
        :type family: str
        :type size: float
        :type weight: float
        :type italic: bool
        """
        if Platform.identify() is not Platform.Darwin:
            size = int(round(size * 0.75))
        super().__init__(family, size, weight, italic)


class BrushIcon(QIcon):
    """
    This class extends QIcon and automatically creates an icon filled with the given color.
    """
    def __init__(self, width, height, color, border=None):
        """
        Initialize the icon.
        :type width: T <= int | float
        :type height: T <= int | float
        :type color: str
        :type border: str
        """
        pixmap = QPixmap(width, height)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRect(QRectF(QPointF(0, 0), QPointF(width, height)))
        painter.fillPath(path, QBrush(QColor(color)))
        if border:
            painter.setPen(QPen(QColor(border), 0, Qt.SolidLine))
            painter.drawPath(path)
        painter.end()
        super().__init__(pixmap)


class PHCQPushButton(QPushButton):
    """
    This class extends QPushButton providing mouse cursor change then the mour pointer hover the button area.
    """
    def __init__(self, parent=None):
        """
        Initialize the button.
        """
        super().__init__(parent)

    #############################################
    #   EVENTS
    #################################

    def enterEvent(self, event):
        """
        Executed when the mouse enter the widget.
        :type event: QEvent
        """
        self.setCursor(Qt.PointingHandCursor)

    def leaveEvent(self, event):
        """
        Executed when the mouse leave the widget.
        :type event: QEvent
        """
        self.unsetCursor()


class PHCQToolButton(QToolButton):
    """
    This class extends QToolButton providing mouse cursor change then the mour pointer hover the button area.
    """
    def __init__(self, parent=None):
        """
        Initialize the button.
        """
        super().__init__(parent)

    #############################################
    #   EVENTS
    #################################

    def enterEvent(self, event):
        """
        Executed when the mouse enter the widget.
        :type event: QEvent
        """
        self.setCursor(Qt.PointingHandCursor)

    def leaveEvent(self, event):
        """
        Executed when the mouse leave the widget.
        :type event: QEvent
        """
        self.unsetCursor()