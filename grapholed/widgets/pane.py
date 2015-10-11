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

from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QScrollArea, QVBoxLayout, QSizePolicy, QWidget, QFrame, QScrollBar


class Pane(QScrollArea):

    MinWidth = 216
    MaxWidth = 234

    def __init__(self, alignment=0, parent=None):
        """
        Initialize the pain container.
        :param alignment: the alignment of the child widget.
        :param parent: the parent widget.
        """
        super().__init__(parent)
        self.mainWidget = QWidget(self)
        self.mainLayout = QVBoxLayout(self.mainWidget)
        self.mainLayout.setAlignment(alignment)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFrameStyle(QFrame.NoFrame)
        self.setFixedWidth(Pane.MinWidth)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Ignored)
        self.setWidgetResizable(True)
        self.setWidget(self.mainWidget)
        self.verticalScrollBar().installEventFilter(self)

    ################################################# SHORTCUTS ########################################################

    def addWidget(self, widget):
        """
        Add a widget to the pane.
        :param widget: the widget to add.
        """
        self.mainLayout.addWidget(widget)

    def removeWidget(self, widget):
        """
        Remove a widget from the pane.
        :param widget: the widget to remove.
        """
        self.mainLayout.removeWidget(widget)

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
            elif event.type() == QEvent.Hide:
                self.setFixedWidth(Pane.MinWidth)
        return super().eventFilter(source, event)

    ################################################### UPDATE #########################################################

    def update(self, *__args):
        """
        Update the widget refreshing all the children.
        """
        for item in (self.mainLayout.itemAt(i) for i in range(self.mainLayout.count())):
            item.widget().update()
        super().update(*__args)
