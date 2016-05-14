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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it  #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPixmap, QIcon
from PyQt5.QtWidgets import QWidget, QStyleOption, QStyle, QHBoxLayout, QLabel, QDockWidget, QPushButton

from eddy.core.functions.signals import connect
from eddy.core.qt import Font


class DockWidget(QDockWidget):
    """
    This class implements the container for docking area widgets.
    """
    def __init__(self, title, icon, parent=None):
        """
        Initialize the dock widget.
        :type title: str
        :type icon: str
        :type parent: QWidget
        """
        super().__init__(title, parent, Qt.Widget)
        self.setTitleBarWidget(DockTitleWidget(title, icon, self))

    def addTitleBarButton(self, button):
        """
        Add a button to the right side of the titlebar of this widget.
        :type button: T <= QPushButton|QToolButton
        """
        widget = self.titleBarWidget()
        widget.addButton(button)
        widget.updateLayout()


class DockTitleWidget(QWidget):
    """
    This class implements the title widget of docking area widgets.
    """
    def __init__(self, title, icon, parent=None):
        """
        Initialize the widget.
        :type title: str
        :type icon: icon
        :type parent: QDockWidget
        """
        super().__init__(parent)
        # CREATE TITLEBAR ICON AND TITLE
        self.imageLabel = QLabel(self)
        self.imageLabel.setPixmap(QPixmap(icon))
        self.imageLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.imageLabel.setContentsMargins(0, 0, 0, 0)
        self.imageLabel.setFixedSize(18, 18)
        self.titleLabel = QLabel(title, self)
        self.titleLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.titleLabel.setContentsMargins(4, 0, 0, 0)
        self.titleLabel.setFont(Font('Arial', 13))
        # CREATE STANDARD BUTTONS
        close = QPushButton(self)
        close.setIcon(QIcon(':/icons/18/close'))
        close.setFixedSize(18, 18)
        connect(close.clicked, parent.close)
        self.buttons = [close]
        # CONFIGURE LAYOUT
        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.setContentsMargins(6, 4, 6, 4)
        self.setContextMenuPolicy(Qt.PreventContextMenu)
        self.setFont(Font('Arial', 13))
        self.updateLayout()

    #############################################
    #   INTERFACE
    #################################

    def addButton(self, button):
        """
        Add a button to the right side of the titlebar, before the close button..
        :type button: T <= QPushButton|QToolButton
        """
        self.buttons.insert(0, button)

    def updateLayout(self):
        """
        Redraw the widget by updating its layout.
        """
        # CLEAR CURRENTY LAYOUT
        for i in reversed(range(self.mainLayout.count())):
            item = self.mainLayout.itemAt(i)
            self.mainLayout.removeItem(item)
        # DISPOSE NEW ELEMENTS
        self.mainLayout.addWidget(self.imageLabel, 0, Qt.AlignLeft|Qt.AlignVCenter)
        self.mainLayout.addWidget(self.titleLabel, 1, Qt.AlignLeft|Qt.AlignVCenter)
        for button in self.buttons:
            self.mainLayout.addWidget(button, 0, Qt.AlignRight|Qt.AlignVCenter)

    #############################################
    #   EVENTS
    #################################

    def paintEvent(self, paintEvent):
        """
        This is needed for the widget to pick the stylesheet.
        :type paintEvent: QPaintEvent
        """
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)
