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


from grapholed.exceptions import ProgrammingError
from grapholed.functions import shaded, connect

from PyQt5.QtCore import Qt, QEvent, QSize, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QScrollArea, QVBoxLayout, QWidget, QFrame, QScrollBar, QLabel
from PyQt5.QtWidgets import QHBoxLayout, QStyleOption, QStyle, QListWidget, QListWidgetItem


class Pane(QScrollArea):

    MinWidth = 216  # without scrollbars
    MaxWidth = 234  # with scrollbars displayed

    def __init__(self, parent=None):
        """
        Initialize the pane container.
        :param parent: the parent widget.
        """
        super().__init__(parent)

        self.paneList = QListWidget()
        self.paneList.setContentsMargins(0, 0, 0, 0)
        self.paneList.setSpacing(0)

        self.setContentsMargins(0, 0, 0, 0)
        self.setFrameStyle(QFrame.NoFrame)
        self.setFixedWidth(Pane.MinWidth)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.setWidgetResizable(True)
        self.setWidget(self.paneList)
        self.verticalScrollBar().installEventFilter(self)

    ################################################# INTERFACE ########################################################

    def addWidget(self, widget):
        """
        Add a widget to the Pane.
        :param widget: the widget to add.
        """
        if not isinstance(widget, PaneWidget):
            raise ProgrammingError('invalid argument specified ({0}): '
                                   'expecting PaneItem'.format(widget.__class__.__name__))
        item = PaneWidgetItem()
        item.setFlags(item.flags() & ~Qt.ItemIsEditable & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
        item.setSizeHint(widget.sizeHint())

        connect(widget.sizeChanged, item.handleSizeChanged)

        self.paneList.addItem(item)
        self.paneList.setItemWidget(item, widget)

    ############################################## EVENT HANDLERS ######################################################

    def eventFilter(self, source, event):
        """
        Filters events if this object has been installed as an event filter for the watched object.
        :param source: the watched object.
        :param event: the event instance.
        """
        if isinstance(source, QScrollBar):
            if event.type() == QEvent.Show:
                self.setFixedWidth(Pane.MaxWidth)
                print("SETMAX")
            elif event.type() == QEvent.Hide:
                self.setFixedWidth(Pane.MinWidth)
        return super().eventFilter(source, event)

    ################################################### UPDATE #########################################################

    def update(self, *__args):
        """
        Update the widget refreshing all the children.
        """
        for item in (self.paneList.item(i) for i in range(self.paneList.count())):
            self.paneList.itemWidget(item).update()
        super().update(*__args)


class PaneWidget(QWidget):
    """
    This the base class for all the Pane items.
    """
    sizeChanged = pyqtSignal()

    ####################################################################################################################
    #                                                                                                                  #
    #   HEAD                                                                                                           #
    #                                                                                                                  #
    ####################################################################################################################

    class Head(QWidget):

        def __init__(self, title, icon, body, parent=None):
            """
            Initialize the header of the widget.
            :param title: the title of the widget.
            :param icon: the path of the icon to display in the header.
            :param body: the body this header is controlling.
            :param parent: the parent widget
            """
            super().__init__(parent)

            self.body = body
            self.icon = shaded(QPixmap(icon), 0.7)
            self.title = QLabel(title)

            self.iconUp = QPixmap(':/icons/arrow-up')
            self.iconDown = QPixmap(':/icons/arrow-down')

            self.image = QLabel()
            self.image.setPixmap(self.icon)
            self.arrow = QLabel()

            self.mainLayout = QHBoxLayout(self)
            self.mainLayout.addWidget(self.image, 0, Qt.AlignLeft)
            self.mainLayout.addWidget(self.title, 1, Qt.AlignLeft)
            self.mainLayout.addWidget(self.arrow, 0, Qt.AlignRight)
            self.mainLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            self.mainLayout.setContentsMargins(5, 4, 5, 4)

            self.setContentsMargins(0, 0, 0, 0)
            self.setFixedSize(QSize(Pane.MinWidth, 30))

        ############################################## EVENT HANDLERS ##################################################

        def enterEvent(self, event):
            """
            Executed when the mouse enter the widget area.
            :param event: the event instance.
            """
            self.setCursor(Qt.PointingHandCursor)

        def leaveEvent(self, event):
            """
            Executed when the mouse leaves the widget area.
            :param event: the event instance.
            """
            self.setCursor(Qt.ArrowCursor)

        def mousePressEvent(self, mouseEvent):
            """
            Executed when the mouse is pressed on the widget.
            :param mouseEvent: the event instance.
            """
            self.setCollapsed(self.body.isVisible())

        ############################################ AUXILIARY METHODS #################################################

        def setCollapsed(self, collapsed):
            """
            Set the collapsed status (of the attached body).
            :param collapsed: True if the body attached to the header should be collapsed, False otherwise.
            """
            self.body.setVisible(not collapsed)
            self.arrow.setPixmap(self.iconDown if collapsed else self.iconUp)
            self.setProperty('class', 'collapsed' if collapsed else 'normal')

            # emit a signal so other widgets can react on the size change
            parent = self.parent()
            parent.sizeChanged.emit()

            # refresh the widget stylesheet
            style = self.style()
            style.unpolish(self)
            style.polish(self)

            # refresh the label stylesheet
            style = self.title.style()
            style.unpolish(self.title)
            style.polish(self.title)

            self.update()

        ############################################## LAYOUT UPDATE ###################################################

        def update(self, *__args):
            """
            Update the widget refreshing all the children.
            """
            self.title.update()
            self.image.update()
            self.arrow.update()
            super().update(*__args)

        ############################################## ITEM PAINTING ###################################################

        def paintEvent(self, paintEvent):
            """
            This is needed for the widget to pick the stylesheet.
            :param paintEvent: the paint event instance.
            """
            option = QStyleOption()
            option.initFrom(self)
            painter = QPainter(self)
            style = self.style()
            style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    ####################################################################################################################
    #                                                                                                                  #
    #   BODY                                                                                                           #
    #                                                                                                                  #
    ####################################################################################################################

    class Body(QWidget):

        def __init__(self, widget, fixed=True, parent=None):
            """
            Initialize the body of the widget.
            :param widget: the widget to be rendered in the body.
            :param fixed: whether the widget has fixed height.
            :param parent: the parent widget.
            """
            super().__init__(parent)
            self.mainLayout = QVBoxLayout(self)
            self.mainLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            self.mainLayout.setContentsMargins(0, 0, 0, 0)
            self.mainLayout.addWidget(widget)
            self.setContentsMargins(0, 0, 0, 0)

            if fixed:
                self.setFixedSize(QSize(Pane.MinWidth, Pane.MinWidth))
            else:
                self.setFixedWidth(Pane.MinWidth)

        ############################################# ITEM PAINTING ####################################################

        def paintEvent(self, paintEvent):
            """
            This is needed for the widget to pick the stylesheet.
            :param paintEvent: the paint event instance.
            """
            option = QStyleOption()
            option.initFrom(self)
            painter = QPainter(self)
            style = self.style()
            style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    def __init__(self, title, icon, widget, collapsed=False, fixed=True):
        """
        Initialize the Pane item.
        :param title: the title of the widget.
        :param icon: the path of the icon to display as widget icon.
        :param widget: the widget to be rendered inside the body of the Pane widget.
        :param collapsed: whether the widget should be collapsed by default.
        :param fixed: whether the widget has fixed height.
        """
        super().__init__()

        self._widget = widget

        self.body = PaneWidget.Body(widget, fixed, self)
        self.head = PaneWidget.Head(title, icon, self.body, self)
        self.head.setCollapsed(collapsed)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 4)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.head)
        self.mainLayout.addWidget(self.body)

        self.setFixedWidth(Pane.MinWidth)

    @property
    def widget(self):
        """
        Returns the widget displayed inside this Pane widget.
        """
        return self._widget

    ################################################ LAYOUT UPDATE #####################################################

    def update(self, *__args):
        """
        Update the widget refreshing all the children.
        """
        self.head.update()
        self.body.update()
        super().update(*__args)


class PaneWidgetItem(QListWidgetItem):
    """
    This class is used to store widgets inside the QListWidget.
    """
    @pyqtSlot(bool)
    def handleSizeChanged(self):
        """
        Executed when size of the widget atached to this item changes.
        """
        self.setSizeHint(self.listWidget().itemWidget(self).sizeHint())