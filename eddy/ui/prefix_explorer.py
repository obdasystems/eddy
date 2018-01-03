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

        self.main_header = Header('PREFIX EXPLORER', self)
        self.main_header_layout = VBoxLayout()
        self.main_header_layout.addWidget(self.main_header)

        self.tableheader_prefixes = Header('Prefix(es)', self)
        self.tableheader_prefix = Header('Prefix', self)
        self.tableheader_iri = Header(' IRI  ', self)
        self.tableheader_version = Header('Version', self)

        ###     Standard [Prefix-IRI] pairs    ###

        self.sub_header_std_IRIs = Header('Standard IRIs', self)

        self.horizontalbox_std_IRIs = QtWidgets.QHBoxLayout(self)   #to be added to main layout
        self.horizontalbox_std_IRIs.setAlignment(QtCore.Qt.AlignTop)
        self.horizontalbox_std_IRIs.setContentsMargins(0, 0, 0, 0)
        self.horizontalbox_std_IRIs.setSpacing(0)
        self.horizontalbox_std_IRIs.addWidget(self.tableheader_prefix)
        self.horizontalbox_std_IRIs.addWidget(self.tableheader_iri)
        self.table_std_IRIs = QtWidgets.QTableWidget(self)
        self.table_std_IRIs.setContentsMargins(0, 0, 0, 0)
        self.table_std_IRIs.horizontalHeader().setVisible(False)
        self.table_std_IRIs.verticalHeader().setVisible(False)
        self.table_std_IRIs.setColumnCount(2)
        ###
        #add std [IRI-Prefix] pairs
        ###
        self.std_IRIs_layout = VBoxLayout()
        self.std_IRIs_layout.addWidget(self.sub_header_std_IRIs)
        self.std_IRIs_layout.addLayout(self.horizontalbox_std_IRIs)
        self.std_IRIs_layout.addWidget(self.table_std_IRIs)
        ##################################

        ###     Project [Prefix-IRI] pair    ###

        self.sub_header_pjt_IRI = Header('Ontology IRI', self)

        self.horizontalbox_pjt_IRI = QtWidgets.QHBoxLayout(self)  # to be added to main layout
        self.horizontalbox_pjt_IRI.setAlignment(QtCore.Qt.AlignTop)
        self.horizontalbox_pjt_IRI.setContentsMargins(0, 0, 0, 0)
        self.horizontalbox_pjt_IRI.setSpacing(0)
        self.horizontalbox_pjt_IRI.addWidget(self.tableheader_prefixes)
        self.horizontalbox_pjt_IRI.addWidget(self.tableheader_iri)
        self.horizontalbox_pjt_IRI.addWidget(self.tableheader_version)
        self.table_pjt_IRI = QtWidgets.QTableWidget(self)
        self.table_pjt_IRI.setContentsMargins(0, 0, 0, 0)
        self.table_pjt_IRI.horizontalHeader().setVisible(False)
        self.table_pjt_IRI.verticalHeader().setVisible(False)
        ###
        # add project [IRI-Prefix] pairs
        ###
        self.pjt_IRI_layout = VBoxLayout()
        self.pjt_IRI_layout.addWidget(self.sub_header_pjt_IRI)
        self.pjt_IRI_layout.addLayout(self.horizontalbox_pjt_IRI)
        self.pjt_IRI_layout.addWidget(self.table_pjt_IRI)
        ##########################################

        ###     Foreign [Prefix-IRI] pair

        self.sub_header_foreign_IRIs = Header('IRIs', self)

        self.horizontalbox_foreign_IRIs = QtWidgets.QHBoxLayout(self)  # to be added to main layout
        self.horizontalbox_foreign_IRIs.setAlignment(QtCore.Qt.AlignTop)
        self.horizontalbox_foreign_IRIs.setContentsMargins(0, 0, 0, 0)
        self.horizontalbox_foreign_IRIs.setSpacing(0)
        self.horizontalbox_foreign_IRIs.addWidget(self.tableheader_prefixes)
        self.horizontalbox_foreign_IRIs.addWidget(self.tableheader_iri)
        self.horizontalbox_foreign_IRIs.addWidget(self.tableheader_version)
        self.table_foreign_IRIs = QtWidgets.QTableWidget(self)
        self.table_foreign_IRIs.setContentsMargins(0, 0, 0, 0)
        self.table_foreign_IRIs.horizontalHeader().setVisible(False)
        self.table_foreign_IRIs.verticalHeader().setVisible(False)
        ###
        # add foreign [IRI-Prefix] pairs
        ###
        self.foreign_IRIs_layout = VBoxLayout()
        self.foreign_IRIs_layout.addWidget(self.sub_header_foreign_IRIs)
        self.foreign_IRIs_layout.addLayout(self.horizontalbox_foreign_IRIs)
        self.foreign_IRIs_layout.addWidget(self.table_foreign_IRIs)
        ##############################################

        self.entry_status = QtWidgets.QStatusBar()

        self.add_entry_button = QtWidgets.QPushButton()
        self.add_entry_button.setText('Add entry')
        self.remove_entry_button = QtWidgets.QPushButton()
        self.remove_entry_button.setText('Remove entry')

        #connect(self.add_entry_button.pressed, self.process_entry_from_textboxes_for_button_add)
        #connect(self.remove_entry_button.pressed, self.process_entry_from_textboxes_for_button_remove)

        self.horizontalbox_buttons = QtWidgets.QHBoxLayout(self)    #to be added to vertical_box
        self.horizontalbox_buttons.setAlignment(QtCore.Qt.AlignTop)
        self.horizontalbox_buttons.setContentsMargins(0, 0, 0, 0)
        self.horizontalbox_buttons.setSpacing(0)
        self.horizontalbox_buttons.addWidget(self.add_entry_button)
        self.horizontalbox_buttons.addWidget(self.remove_entry_button)

        self.buttons_and_entry_status_layout = VBoxLayout()
        self.buttons_and_entry_status_layout.addWidget(self.entry_status)
        self.buttons_and_entry_status_layout.addLayout(self.horizontalbox_buttons)
        ##############################################


        self.mainLayout.addLayout(self.main_header_layout)
        self.mainLayout.addLayout(self.std_IRIs_layout)
        self.mainLayout.addLayout(self.pjt_IRI_layout)
        self.mainLayout.addLayout(self.foreign_IRIs_layout)
        self.mainLayout.addLayout(self.buttons_and_entry_status_layout)

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

    def fill_std_IRIs_table(self):

        for std_iri in OWLStandardIRIPrefixPairsDict.keys():
            prefix = OWLStandardIRIPrefixPairsDict[std_iri]

            item_iri = QtWidgets.QTableWidgetItem(std_iri)
            item_iri.setText(std_iri)
            item_iri.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

    def fill_project_IRI_table(self):
        pass

    def fill_foreign_IRIs_table(self):
        pass

    def run(self):
        """
        Perform initialization tasks for the plugin.
        """
        """
        widget = self.widget('developers_iri')

        connect(self.project.sgnIRIPrefixNodeDictionaryUpdated, widget.FillTableWithIRIPrefixNodesDictionaryKeysAndValues)

        connect(self.project.sgnIRIPrefixNodeEntryAdded, widget.entry_ADD_ok)
        connect(self.project.sgnIRIPrefixNodeEntryRemoved, widget.entry_REMOVE_OK)
        connect(self.project.sgnIRIPrefixNodeEntryIgnored, widget.entry_NOT_OK)

        widget.run()
        """



class Header(QtWidgets.QLabel):
    """
    This class implements the header of properties section.
    """
    def __init__(self, *args):
        """
        Initialize the header.
        """
        super().__init__(*args)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setFixedHeight(24)
        self.setFont(Font('Roboto', 12))


class VBoxLayout(QtWidgets.QVBoxLayout):

    def __init__(self):
        super().__init__()
        self.setAlignment(QtCore.Qt.AlignTop)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)