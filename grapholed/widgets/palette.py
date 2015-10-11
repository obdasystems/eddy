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
from grapholed.functions import shaded
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QStyleOption, QStyle, QHBoxLayout


class Palette(QWidget):
    """
    This class implements the Graphol palette.
    """
    class Item(QWidget):
        """
        This class implements a palette section.
        """
        ################################################################################################################
        #                                                                                                              #
        #   HEAD                                                                                                       #
        #                                                                                                              #
        ################################################################################################################

        class Head(QWidget):

            def __init__(self, title, body, parent=None):
                """
                Initialize the header of the palette item.
                :param title: the title to display as header.
                :param body: the body this header is controlling.
                :param parent: the parent widget.
                """
                super().__init__(parent)
                self.body = body
                self.iconUp = QPixmap(':/icons/arrow-up')
                self.iconDown = QPixmap(':/icons/arrow-down')
                self.iconAdd = shaded(QPixmap(':/icons/add'), 0.7)
                self.headText = QLabel(title)
                self.headImg1 = QLabel()
                self.headImg1.setPixmap(self.iconAdd)
                self.headImg2 = QLabel()

                self.headLayout = QHBoxLayout(self)
                self.headLayout.addWidget(self.headImg1, 0, Qt.AlignLeft)
                self.headLayout.addWidget(self.headText, 1, Qt.AlignLeft)
                self.headLayout.addWidget(self.headImg2, 0, Qt.AlignRight)
                self.headLayout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.headLayout.setContentsMargins(5, 4, 5, 4)

                self.setContentsMargins(0, 0, 0, 0)
                self.setFixedSize(216, 30)

            ########################################## EVENT HANDLERS ##################################################

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

            ######################################### AUXILIARY METHODS ################################################

            def setCollapsed(self, collapsed):
                """
                Set the collapsed status (of the attached body).
                :param collapsed: True if the body attached to the header should be collapsed, False otherwise.
                """
                self.body.setVisible(not collapsed)
                self.headImg2.setPixmap(self.iconDown if collapsed else self.iconUp)
                self.setProperty('class', 'collapsed' if collapsed else 'normal')
                # refresh the widget stylesheet
                self.style().unpolish(self)
                self.style().polish(self)
                # refresh the label stylesheet
                self.headText.style().unpolish(self.headText)
                self.headText.style().polish(self.headText)
                self.update()

            ############################################## LAYOUT UPDATE ###################################################

            def update(self, *__args):
                """
                Update the widget refreshing all the children.
                """
                self.headText.update()
                self.headImg2.update()
                super().update(*__args)

            ########################################### ITEM PAINTING ##################################################

            def paintEvent(self, paintEvent):
                """
                This is needed for the widget to pick the stylesheet.
                :param paintEvent: the paint event instance.
                """
                option = QStyleOption()
                option.initFrom(self)
                painter = QPainter(self)
                self.style().drawPrimitive(QStyle.PE_Widget, option, painter, self)

        ################################################################################################################
        #                                                                                                              #
        #   BODY                                                                                                       #
        #                                                                                                              #
        ################################################################################################################

        class Body(QWidget):

            def __init__(self, span=2, parent=None):
                """
                Initialize the body of the widget.
                :param span: the amount of widgets to display per line.
                :param parent: the parent widget.
                """
                super().__init__(parent)
                self.bodyLayout = QGridLayout(self)
                self.bodyLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
                self.bodyLayout.setContentsMargins(0, 6, 0, 6)
                self.bodyLayout.setSpacing(4)
                self.setContentsMargins(0, 0, 0, 0)
                self.setFixedWidth(216)
                self.colNum = span
                self.colIdx = 0
                self.rowIdx = 0

            def addWidget(self, widget):
                """
                Appened the given widget to the body of the Palette.Item
                :type widget: QWidget
                :param widget: the widget to add.
                """
                self.bodyLayout.addWidget(widget, self.rowIdx, self.colIdx)
                self.colIdx += 1
                if self.colIdx >= self.colNum:
                    self.colIdx = 0
                    self.rowIdx += 1

            def removeWidget(self, widget):
                """
                Removes the given widget from the body of the Palette.Item.
                :type widget: QWidget
                :param widget: the widget to remove.
                """
                self.bodyLayout.removeWidget(widget)

            ########################################### ITEM PAINTING ##################################################

            def paintEvent(self, paintEvent):
                """
                This is needed for the widget to pick the stylesheet.
                :param paintEvent: the paint event instance.
                """
                option = QStyleOption()
                option.initFrom(self)
                painter = QPainter(self)
                self.style().drawPrimitive(QStyle.PE_Widget, option, painter, self)

        def __init__(self, title, span=3, collapsed=False, parent=None):
            """
            Initialize the Palette item.
            :type title: str
            :type span: int
            :type collapsed: bool
            :type parent: QWidget
            :param title: the title to display as Palette.Item header.
            :param span: the amount of widgets to display per line in the Palette.Item body.
            :param collapsed: whether this item should be collapsed or not by default.
            :param parent: the parent widget.
            """
            super().__init__(parent)
            self.body = Palette.Item.Body(span=span, parent=self)
            self.head = Palette.Item.Head(title=title, body=self.body, parent=self)
            self.head.setCollapsed(collapsed)

            self.mainLayout = QVBoxLayout(self)
            self.mainLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            self.mainLayout.setContentsMargins(0, 0, 0, 4)
            self.mainLayout.setSpacing(0)
            self.mainLayout.addWidget(self.head)
            self.mainLayout.addWidget(self.body)

            self.setFixedWidth(216)

        ################################################# SHORTCUTS ########################################################

        def addWidget(self, widget):
            """
            Appened the given widget to the body of the Palette.Item.
            :type widget: QWidget
            :param widget: the widget to add.
            """
            self.body.addWidget(widget)

        def removeWidget(self, widget):
            """
            Removes the given widget from the body of the Palette item.
            :type widget: QWidget
            :param widget: the widget to remove.
            """
            self.body.removeWidget(widget)

        ################################################ LAYOUT UPDATE #####################################################

        def update(self, *__args):
            """
            Update the widget refreshing all the children.
            """
            self.head.update()
            self.body.update()
            super().update(*__args)

    def __init__(self, parent=None):
        """
        Initialize the palette.
        :type parent: QWidget
        :param parent: the parent widget.
        """
        super().__init__(parent)
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.setFixedWidth(216)
        self.setProperty('class', 'palette')

    ################################################# SHORTCUTS ########################################################

    def addItem(self, item):
        """
        Add the current item to the Palette.
        :type item: Palette.Item.
        :param item: the item to add to the Palette.
        """
        if not isinstance(item, Palette.Item):
            raise ProgrammingError('invalid argument specified (%s): expecting Palette.Item' % item.__class__.__name__)
        self.mainLayout.addWidget(item)

    def removeItem(self, item):
        """
        Remove the current item from the Palette.
        :type item: Palette.item
        :param item: the item to remove from the Palette.
        """
        if not isinstance(item, Palette.Item):
            raise ProgrammingError('invalid argument specified (%s): expecting Palette.Item' % item.__class__.__name__)
        self.mainLayout.removeWidget(item)

    ################################################ LAYOUT UPDATE #####################################################

    def update(self, *__args):
        """
        Update the widget refreshing all the children.
        """
        for item in (self.mainLayout.itemAt(i) for i in range(self.mainLayout.count())):
            item.widget().update()
        super().update(*__args)