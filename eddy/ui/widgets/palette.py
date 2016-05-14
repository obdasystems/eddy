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


from math import ceil

from PyQt5.QtCore import Qt, QSize, QMimeData, pyqtSlot, pyqtSignal, QEvent, QSettings
from PyQt5.QtGui import QIcon, QPainter, QDrag
from PyQt5.QtWidgets import QWidget, QGridLayout, QToolButton, QMenu, QAction
from PyQt5.QtWidgets import QApplication, QStyleOption, QStyle

from eddy import ORGANIZATION, APPNAME
from eddy.core.datatypes.graphol import Item
from eddy.core.functions.signals import emit, connect
from eddy.core.items.factory import ItemFactory
from eddy.core.qt import Font


class Palette(QWidget):
    """
    This class implements the graphol palette.
    """
    Padding = 6
    Spacing = 0

    sgnButtonClicked = pyqtSignal('QToolButton')

    def __init__(self, *args):
        """
        Initialize the Palette.
        """
        super().__init__(*args)

        self.cols = -1
        self.buttons = {}
        self.display = {}
        self.items = [
            Item.ConceptNode,
            Item.RoleNode,
            Item.AttributeNode,
            Item.ValueDomainNode,
            Item.IndividualNode,
            Item.FacetNode,
            Item.DomainRestrictionNode,
            Item.RangeRestrictionNode,
            Item.IntersectionNode,
            Item.RoleChainNode,
            Item.DatatypeRestrictionNode,
            Item.RoleInverseNode,
            Item.ComplementNode,
            Item.EnumerationNode,
            Item.UnionNode,
            Item.DisjointUnionNode,
            Item.PropertyAssertionNode,
            Item.InclusionEdge,
            Item.InputEdge,
            Item.MembershipEdge,
        ]

        # CREATE BUTTONS
        for item in self.items:
            button = Button(item)
            button.installEventFilter(self)
            connect(button.clicked, self.onButtonClicked)
            self.buttons[item] = button

        # LOAD BUTTONS DISPLAY SETTINGS
        settings = QSettings(ORGANIZATION, APPNAME)
        for item in self.items:
            self.display[item] = settings.value('palette/{0}'.format(item.name), True, bool)

        # CREATE TOGGLE MENU
        self.menu = QMenu()
        for item in self.items:
            action = QAction(item.shortname.title(), self)
            action.setCheckable(True)
            action.setChecked(self.display[item])
            action.setFont(Font('Arial', 11))
            action.setData(item)
            connect(action.triggered, self.onMenuButtonClicked)
            self.menu.addAction(action)

        # CREATE CONTROL WIDGET
        self.btnMenu = QToolButton()
        self.btnMenu.setIcon(QIcon(':/icons/18/settings'))
        self.btnMenu.setMenu(self.menu)
        self.btnMenu.setPopupMode(QToolButton.InstantPopup)

        # SETUP LAYOUT
        self.mainLayout = QGridLayout(self)
        self.mainLayout.setAlignment(Qt.AlignHCenter|Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, Palette.Padding, 0, Palette.Padding)
        self.mainLayout.setSpacing(Palette.Spacing)
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(216)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def onButtonClicked(self):
        """
        Executed when a button is clicked.
        """
        self.reset(self.sender())
        emit(self.sgnButtonClicked, self.sender())

    @pyqtSlot()
    def onMenuButtonClicked(self):
        """
        Executed when a button in the widget menu is clicked.
        """
        # UPDATE THE PALETTE LAYOUT
        item = self.sender().data()
        self.display[item] = not self.display[item]
        self.buttons[item].setVisible(self.display[item])
        self.redraw(True)
        # UPDATE SETTINGS
        settings = QSettings(ORGANIZATION, APPNAME)
        for item in self.items:
            settings.setValue('palette/{0}'.format(item.name), self.display[item])
        settings.sync()
        # FIXME: https://bugreports.qt.io/browse/QTBUG-36862
        self.btnMenu.setAttribute(Qt.WA_UnderMouse, False)

    #############################################
    #   EVENTS
    #################################

    def eventFilter(self, source, event):
        """
        Filters events if this object has been installed as an event filter for the watched object.
        :type source: QObject
        :type event: QEvent
        :rtype: bool
        """
        if event.type() in {QEvent.MouseButtonPress, QEvent.MouseButtonRelease, QEvent.MouseMove}:
            if isinstance(source, Button):
                if not self.isEnabled():
                    return True
        return super().eventFilter(source, event)

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

    #############################################
    #   INTERFACE
    #################################

    def button(self, item):
        """
        Returns the button matching the given item type.
        :type item: Item
        :rtype: Button
        """
        return self.buttons[item]

    def controls(self):
        """
        Returns a set of widgets that can be placed in the docking area title bar to control this widget.
        :rtype: list
        """
        return [self.btnMenu]

    def redraw(self, force=False):
        """
        Redraw the palette.
        :type force: bool
        """
        items = [i for i in self.items if self.display[i]]
        cols = int((self.width() - Palette.Padding * 2) / Button.Width)
        rows = ceil(len(items) / cols)
        if self.cols != cols or force:
            self.cols = cols
            # COMPUTE NEW BUTTONS LOCATION
            zipped = list(zip([x for x in range(rows) for _ in range(cols)], list(range(cols)) * rows))
            zipped = zipped[:len(items)]
            # CLEAR CURRENTY LAYOUT
            for i in reversed(range(self.mainLayout.count())):
                item = self.mainLayout.itemAt(i)
                self.mainLayout.removeItem(item)
            # DISPOSE NEW BUTTONS
            for i in range(len(zipped)):
                self.mainLayout.addWidget(self.button(items[i]), zipped[i][0], zipped[i][1])

    def reset(self, *args):
        """
        Reset the palette selection.
        :type args: Item
        """
        for button in self.buttons.values():
            if button not in args:
                button.setChecked(False)

    def sizeHint(self):
        """
        Returns the recommended size for this widget.
        :rtype: QSize
        """
        return QSize(216, 342)


class Button(QToolButton):
    """
    This class implements a single palette button.
    """
    Height = 44
    Width = 60

    def __init__(self, item, parent=None):
        """
        Initialize the palette button.
        :type item: Item
        :type parent: QWidget
        """
        super().__init__(parent)
        self.item = item
        self.pixmap = ItemFactory.imageForItem(item, Button.Width, Button.Height)
        self.startPos = None
        self.setCheckable(True)
        self.setContentsMargins(0, 0, 0, 0)
        self.setIcon(QIcon(self.pixmap))
        self.setIconSize(QSize(Button.Width, Button.Height))

    #############################################
    #   EVENTS
    #################################

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the button.
        :type mouseEvent: QMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:
            self.startPos = mouseEvent.pos()
        super().mousePressEvent(mouseEvent)

    # noinspection PyArgumentList
    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse if moved while a button is being pressed.
        :type mouseEvent: QMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:

            # Exclude edges from drag & drop.
            if Item.ConceptNode <= self.item < Item.InclusionEdge:
                distance = (mouseEvent.pos() - self.startPos).manhattanLength()
                if distance >= QApplication.startDragDistance():
                    mimeData = QMimeData()
                    mimeData.setText(str(self.item.value))
                    drag = QDrag(self)
                    drag.setMimeData(mimeData)
                    drag.setPixmap(self.pixmap)
                    drag.setHotSpot(self.startPos - self.rect().topLeft())
                    drag.exec_(Qt.CopyAction)

        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when a mouse button is released.
        :type mouseEvent: QMouseEvent
        """
        super().mouseReleaseEvent(mouseEvent)