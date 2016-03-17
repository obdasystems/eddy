# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
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


from PyQt5.QtCore import pyqtSlot, QRectF, QPointF, Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QPainterPath, QColor, QBrush, QPen
from PyQt5.QtWidgets import QStackedWidget, QSizePolicy

from eddy.core.datatypes.system import Platform
from eddy.core.functions import connect, shaded


class Font(QFont):
    """
    This class extends PyQt5.QtGui.QFont providing better font rendering on different platforms.
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


class ColoredIcon(QIcon):
    """
    This class extends PyQt5.QtGui.QIcon and automatically creates an icon filled with the given color..
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


class Icon(QIcon):
    """
    This class extends PyQt5.QtGui.QIcon providing automatic generation of shaded icon for disabled status.
    """
    def __init__(self, path, opacity=0.25):
        """
        Initialize the icon.
        :type path: str
        :type opacity: float
        """
        super().__init__()
        self.addPixmap(QPixmap(path), QIcon.Normal)
        self.addPixmap(shaded(QPixmap(path), opacity), QIcon.Disabled)


class StackedWidget(QStackedWidget):
    """
    This class implements a stacked widget with variable page size.
    """
    def __init__(self, parent=None):
        """
        Initialize the stacked widget.
        :type parent: QWidget
        """
        super().__init__(parent)
        connect(self.currentChanged, self.currentIndexChanged)

    def addWidget(self, widget):
        """
        Add a widget in the stack.
        :type widget: QWidget
        """
        widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        super().addWidget(widget)

    @pyqtSlot(int)
    def currentIndexChanged(self, index):
        """
        Executed whenever the currently displayed widget changes.
        :type index: int
        """
        widget = self.widget(index)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        widget.adjustSize()