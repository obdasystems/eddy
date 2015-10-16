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


from grapholed.widgets import PaneWidget, Pane

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QWidget, QGridLayout, QStyleOption, QStyle


class Palette(PaneWidget):
    """
    This class implements a single palette section.
    """
    padding = 6
    spacing = 4

    class Widget(QWidget):
        """
        This class is used to dispose palette elements withing the Palette block.
        """
        def __init__(self, parent=None):
            """
            Initialize the palette block inner widget.
            :param parent: the parent widget.
            """
            super().__init__(parent)
            self.mainLayout = QGridLayout(self)
            self.mainLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            self.mainLayout.setContentsMargins(0, Palette.padding, 0, Palette.padding)
            self.mainLayout.setSpacing(Palette.spacing)
            self.setContentsMargins(0, 0, 0, 0)
            self.setFixedWidth(Pane.MinWidth)
            self.numcol = 3
            self.indexC = 0
            self.indexR = 0

        ############################################### INTERFACE ######################################################

        def addButton(self, button):
            """
            Appened the given button to the palette.
            :param button: the button to add.
            """
            self.mainLayout.addWidget(button, self.indexR, self.indexC)
            self.indexC += 1
            if self.indexC >= self.numcol:
                self.indexC = 0
                self.indexR += 1

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

    def __init__(self, title, icon, collapsed=False):
        """
        Initialize the palette block.
        :param title: the title of the widget.
        :param icon: the path of the icon to display as widget icon.
        :param collapsed: whether the widget should be collapsed by default.
        """
        super().__init__(title, icon, Palette.Widget(), collapsed, fixed=False)

    ################################################# INTERFACE ########################################################

    def addButton(self, button):
        """
        Appened the given button to the palette.
        :param button: the button to add.
        """
        self.widget.addButton(button)
        # IMPORTANT: do not remove this otherwise the palette won't be
        # rendered properly due to the fact that it doesn't specify a
        # fixed height in the constructor (because we don't know the
        # exact height) so we need to continuously recalculate it
        sizeHint = self.widget.mainLayout.sizeHint()
        self.body.setFixedHeight(sizeHint.height() - 2 * self.widget.mainLayout.rowCount())