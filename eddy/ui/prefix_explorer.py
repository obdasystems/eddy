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
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy.core.common import HasThreadingSystem
from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.owl import OWLStandardIRIPrefixPairsDict
from eddy.core.datatypes.qt import Font
from eddy.core.functions.signals import connect, disconnect
from eddy.core.output import getLogger
from eddy.ui.fields import IntegerField, StringField



class PrefixExplorerDialog(QtWidgets.QDialog, HasThreadingSystem):

    def __init__(self, project, session):
        """
        Initialize the dialog.
        :type project: Project
        :type session: Session
        """
        super().__init__(session)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        #############

        self.entry_status = QtWidgets.QStatusBar()
        self.entry_status.setFixedHeight(30)

        self.verticalbox = QtWidgets.QVBoxLayout(self)  # to be added to main layout
        self.verticalbox.setAlignment(QtCore.Qt.AlignTop)
        self.verticalbox.setContentsMargins(0, 0, 0, 0)
        self.verticalbox.setSpacing(0)
        self.verticalbox.addWidget(self.entry_status)

        #############

        self.table = QtWidgets.QTableWidget(self)
        self.table.setContentsMargins(0, 0, 0, 0)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumWidth(self.width())
        self.table.setMinimumHeight(self.height())

        connect(self.table.cellPressed, self.cell_pressed)

        #############
        self.verticalbox.addWidget(self.table)

        self.mainLayout.addLayout(self.verticalbox)
        # self.mainLayout.addLayout(self.buttons_layout)
        #############

        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(QtCore.QSize(216, 120))
        self.setMinimumWidth(400)
        self.setMaximumHeight(600)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setWidgetResizable(True)

        self.setStyleSheet("""
                IriWidget {
                  background: #FFFFFF;
                }
                IriWidget Header {
                  background: #5A5050;
                  padding-left: 4px;
                  color: #FFFFFF;
                }
                """)

        scrollbar = self.verticalScrollBar()
        scrollbar.installEventFilter(self)

        self.ENTRY_MODIFY_OK_var = set()
        self.ENTRY_REMOVE_OK_var = set()
        self.ENTRY_ADD_OK_var = set()
        self.ENTRY_IGNORE_var = set()

        self.ITEM_PRESSED = None
        self.ITEM_CHANGED = None

        self.old_text = None
        self.new_text = None

        self.iri_old_text = None
        self.iri_new_text = None
        self.prefix_old_text = None
        self.prefix_new_text = None

    def eventFilter(self, source, event):
        """
        Filters events if this object has been installed as an event filter for the watched object.
        :type source: QObject
        :type event: QtCore.QEvent
        :rtype: bool
        """
        if event.type() == QtCore.QEvent.Resize:
            self.redraw()
        return super().eventFilter(source, event)

    def run(self):

        pass



