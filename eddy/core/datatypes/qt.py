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


import sys

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets


LINUX = sys.platform.startswith('linux')
MACOS = sys.platform.startswith('darwin')
WIN32 = sys.platform.startswith('win32')


class Font(QtGui.QFont):
    """
    This class extends QtGui.QFont providing better font rendering on different platforms.
    """
    def __init__(self, family, size=12, weight=-1, **kwargs):
        """
        Contruct a new Font instance using the given parameters.
        :type family: str
        :type size: float
        :type weight: float
        """
        if not MACOS:
            size = int(round(size * 0.75))
        super(Font, self).__init__(family, size, weight)
        self.setBold(kwargs.get('bold', False))
        self.setItalic(kwargs.get('italic', False))
        self.setCapitalization(kwargs.get('capitalization', QtGui.QFont.MixedCase))
        self.setStyleHint(kwargs.get('style', QtGui.QFont.AnyStyle))


class BrushIcon(QtGui.QIcon):
    """
    This class extends QtGui.QIcon and automatically creates an icon filled with the given color.
    """
    def __init__(self, width, height, color, border=None):
        """
        Initialize the icon.
        :type width: T <= int | float
        :type height: T <= int | float
        :type color: str
        :type border: str
        """
        pixmap = QtGui.QPixmap(width, height)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        path = QtGui.QPainterPath()
        path.addRect(QtCore.QRectF(QtCore.QPointF(0, 0), QtCore.QPointF(width, height)))
        painter.fillPath(path, QtGui.QBrush(QtGui.QColor(color)))
        if border:
            painter.setPen(QtGui.QPen(QtGui.QColor(border), 0, QtCore.Qt.SolidLine))
            painter.drawPath(path)
        painter.end()
        super().__init__(pixmap)


class PHCQPushButton(QtWidgets.QPushButton):
    """
    This class extends QtWidgets.QPushButton providing mouse cursor change then the mour pointer hover the button area.
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
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def leaveEvent(self, event):
        """
        Executed when the mouse leave the widget.
        :type event: QEvent
        """
        self.unsetCursor()


class PHCQToolButton(QtWidgets.QToolButton):
    """
    This class extends QtWidgets.QToolButton providing mouse cursor change then the mour pointer hover the button area.
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
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def leaveEvent(self, event):
        """
        Executed when the mouse leave the widget.
        :type event: QEvent
        """
        self.unsetCursor()