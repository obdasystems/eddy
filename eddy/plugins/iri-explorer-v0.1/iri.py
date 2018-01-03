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

from eddy.core.commands.nodes_2 import CommandProjetSetIRIPrefixesNodesDict
from eddy.core.datatypes.owl import OWLStandardIRIPrefixPairsDict
from eddy.core.datatypes.qt import BrushIcon, Font
from eddy.core.functions.misc import first, clamp, isEmpty
from eddy.core.functions.signals import connect, disconnect
from eddy.core.plugin import AbstractPlugin
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.core.output import getLogger

from eddy.ui.dock import DockWidget
from eddy.ui.fields import IntegerField, StringField
from eddy.ui.fields import CheckBox, ComboBox


LOGGER = getLogger()


class IriPlugin(AbstractPlugin):
    """
    This plugin provides the Prefix-IRI widget.
    """
    #############################################
    #   EVENTS
    #################################

    def eventFilter(self, source, event):
        """
        Filters events if this object has been installed as an event filter for the watched object.
        :type source: QObject
        :type event: QtCore.QEvent
        :rtype: bool
        """
        if event.type() == QtCore.QEvent.Resize:
            widget = source.widget()
            widget.redraw()
        return super().eventFilter(source, event)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onSessionReady(self):

        widget = self.widget('developers_iri')

        connect(self.project.sgnIRIPrefixNodeDictionaryUpdated, widget.FillTableWithIRIPrefixNodesDictionaryKeysAndValues)

        connect(self.project.sgnIRIPrefixEntryAdded, widget.entry_ADD_ok)
        connect(self.project.sgnIRIPrefixEntryRemoved, widget.entry_REMOVE_OK)
        connect(self.project.sgnIRIPrefixEntryIgnored, widget.entry_NOT_OK)

        widget.run()

    @QtCore.pyqtSlot(QtWidgets.QMdiSubWindow)
    def onSubWindowActivated(self, subwindow):
        """
        Executed when the active subwindow changes.
        :type subwindow: MdiSubWindow
        """
        pass

    #############################################
    #   HOOKS
    #################################

    def dispose(self):
        """
        Executed whenever the plugin is going to be destroyed.
        """
        # DISCONNECT FROM ACTIVE SESSION
        self.debug('Disconnecting from active session')
        disconnect(self.session.sgnReady, self.onSessionReady)
        disconnect(self.session.mdi.subWindowActivated, self.onSubWindowActivated)


        # REMOVE DOCKING AREA WIDGET MENU ENTRY
        self.debug('Removing docking area widget toggle from "view" menu')
        menu = self.session.menu('view')
        menu.removeAction(self.widget('iri_dock').toggleViewAction())

        # UNINSTALL THE PALETTE DOCK WIDGET
        self.debug('Uninstalling docking area widget')
        self.session.removeDockWidget(self.widget('iri_dock'))


    def start(self):
        """
        Perform initialization tasks for the plugin.
        """
        # INITIALIZE THE WIDGET
        self.debug('Creating iri widget')
        widget = IriWidget(self)
        widget.setObjectName('developers_iri')
        self.addWidget(widget)

        # CREATE DOCKING AREA WIDGET
        self.debug('Creating docking area widget')
        widget = DockWidget('developers_Prefix-Iri Explorer', QtGui.QIcon(':/icons/18/ic_info_outline_black'), self.session)
        widget.installEventFilter(self)
        widget.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        widget.setObjectName('iri_dock')
        widget.setWidget(self.widget('developers_iri'))
        self.addWidget(widget)

        # CREATE ENTRY IN VIEW MENU
        self.debug('Creating docking area widget toggle in "view" menu')
        menu = self.session.menu('view')
        menu.addAction(self.widget('iri_dock').toggleViewAction())

        # INSTALL DOCKING AREA WIDGET
        self.debug('Installing docking area widget')
        self.session.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.widget('iri_dock'))

        # CONFIGURE SIGNAL/SLOTS
        self.debug('Connecting to active session')
        connect(self.session.sgnReady, self.onSessionReady)
        connect(self.session.mdi.subWindowActivated, self.onSubWindowActivated)


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


class IriWidget(QtWidgets.QScrollArea):
    """
    This class implements the information box widget.
    """

    def __init__(self, plugin):
        """
        Initialize the info box.
        :type plugin: Info
        """
        super().__init__(plugin.session)

        self.plugin = plugin

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        #############

        self.tableheader_prefixes = Header('Prefix', self)
        self.tableheader_iri = Header(' IRI  ', self)
        self.tableheader_nodes = Header('Nodes ', self)

        self.horizontalbox = QtWidgets.QHBoxLayout(self)   #to be added to main layout
        self.horizontalbox.setAlignment(QtCore.Qt.AlignTop)
        self.horizontalbox.setContentsMargins(0, 0, 0, 0)
        self.horizontalbox.setSpacing(0)
        self.horizontalbox.addWidget(self.tableheader_iri)
        self.horizontalbox.addWidget(self.tableheader_prefixes)
        self.horizontalbox.addWidget(self.tableheader_nodes)

        #############

        self.entry_status = QtWidgets.QStatusBar()

        self.entry_button = QtWidgets.QPushButton()
        self.entry_button.setText('Add entry to the table')
        self.remove_entry_button = QtWidgets.QPushButton()
        self.remove_entry_button.setText('Remove entry from table')
        self.dictionary_display_button = QtWidgets.QPushButton()
        self.dictionary_display_button.setText('Display dictionary')

        connect(self.entry_button.pressed, self.button_add)
        connect(self.remove_entry_button.pressed, self.button_remove)
        connect(self.dictionary_display_button.pressed, self.display_IRIPrefixesNodesDict)

        self.prefix_input_box = StringField(self)
        self.prefix_input_box.setPlaceholderText('Enter Prefix')
        self.prefix_input_box.setAcceptDrops(False)
        self.prefix_input_box.setClearButtonEnabled(True)
        self.prefix_input_box.setFixedHeight(30)

        self.iri_input_box = StringField(self)
        self.iri_input_box.setPlaceholderText('Enter IRI')
        self.iri_input_box.setAcceptDrops(False)
        self.iri_input_box.setClearButtonEnabled(True)
        self.iri_input_box.setFixedHeight(30)

        self.verticalbox = QtWidgets.QVBoxLayout(self)  # to be added to main layout
        self.verticalbox.setAlignment(QtCore.Qt.AlignTop)
        self.verticalbox.setContentsMargins(0, 0, 0, 0)
        self.verticalbox.setSpacing(0)
        self.verticalbox.addWidget(self.iri_input_box)
        self.verticalbox.addWidget(self.prefix_input_box)
        self.verticalbox.addWidget(self.entry_button)
        self.verticalbox.addWidget(self.remove_entry_button)
        self.verticalbox.addWidget(self.dictionary_display_button)
        self.verticalbox.addWidget(self.entry_status)

        #############

        self.table = QtWidgets.QTableWidget(self)
        self.table.setContentsMargins(0, 0, 0, 0)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumWidth(self.width())
        self.table.setMinimumHeight(self.height()-self.dictionary_display_button.height())



        self.horizontalbox_3 = QtWidgets.QHBoxLayout(self)    #to be added to main layout
        self.horizontalbox_3.setAlignment(QtCore.Qt.AlignTop)
        self.horizontalbox_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalbox_3.setSpacing(0)
        self.horizontalbox_3.addWidget(self.table)

        #############

        self.mainLayout.addLayout(self.verticalbox)
        self.mainLayout.addLayout(self.horizontalbox)
        self.mainLayout.addLayout(self.horizontalbox_3)

        #############

        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(QtCore.QSize(216, 120))
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

        self.ENTRY_REMOVE_OK_var = False
        self.ENTRY_ADD_OK_var = False
        self.ENTRY_IGNORE_var = False

        self.ADD_OR_REMOVE = None

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self):
        """
        Returns the reference to the active project.
        :rtype: Session
        """
        return self.session.project

    @property
    def session(self):
        """
        Returns the reference to the active session.
        :rtype: Session
        """
        return self.plugin.parent()

    #############################################
    #   EVENTS
    #################################

    def eventFilter(self, source, event):
        """
        Filter incoming events.
        :type source: QObject
        :type event: QtCore.QEvent
        """
        if source is self.verticalScrollBar():
            if event.type() in {QtCore.QEvent.Show, QtCore.QEvent.Hide}:
                self.redraw()
        return super().eventFilter(source, event)

    ###############################
    #
    ###############################

    @QtCore.pyqtSlot(str, str, str)
    def entry_ADD_ok(self,iri,prefix,message):

        self.ENTRY_ADD_OK_var = True

        self.entry_status.showMessage(message,10000)
        print('entry_ADD_ok(self): ',iri,',',prefix,',',message)

    @QtCore.pyqtSlot(str, str, str)
    def entry_REMOVE_OK(self,iri,prefix,message):

        self.ENTRY_REMOVE_OK_var = True
        self.entry_status.showMessage(message, 10000)
        print('entry_REMOVE_ok(self): ',iri,',',prefix,',',message)

    @QtCore.pyqtSlot(str, str, str)
    def entry_NOT_OK(self,iri,prefix,message):

        self.ENTRY_IGNORE_var = True
        self.entry_status.showMessage(message, 10000)
        print('entry_NOT_OK(self): ',iri,',',prefix,',',message)

    def display_IRIPrefixesNodesDict(self):

        self.project.print_dictionary(self.project.IRI_prefixes_nodes_dict)

    #not used
    def FillTableWithStandardIRIsAndStandardPrefixes(self):

        #print('>>>  fill_table_with_standard_iris_and_standard_prefixes')

        for std_iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():

            item_std_iri = QtWidgets.QTableWidgetItem()
            item_std_iri.setText(std_iri)
            item_std_iri.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

            std_prefix = OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict[std_iri]

            item_std_prefix = QtWidgets.QTableWidgetItem()
            item_std_prefix.setText(std_prefix)
            item_std_prefix.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

            self.table.setRowCount(self.table.rowCount() + 1)

            self.table.setItem(self.table.rowCount() - 1, 0, item_std_iri)
            self.table.setItem(self.table.rowCount() - 1, 1, item_std_prefix)
            #self.table.resizeRowToContents(self.table.rowCount() - 1)

        #print('>>>  fill_table_with_standard_iris_and_standard_prefixes     END')

    def FillTableWithIRIPrefixNodesDictionaryKeysAndValues(self):

        #print('>>>  FillTableWithIRIPrefixNodesDictionaryKeysAndValues')
        # first delete all entries from the dictionary id present
        # add standard IRIs
        # add key value pairs from dict
        self.table.clear()
        self.table.setRowCount(0)

        #print('self.project.IRI_prefixes_nodes_dict.keys()',self.project.IRI_prefixes_nodes_dict.keys())

        for iri in self.project.IRI_prefixes_nodes_dict.keys():

            item_iri = QtWidgets.QTableWidgetItem(iri)
            item_iri.setText(iri)
            item_iri.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

            prefixes = self.project.IRI_prefixes_nodes_dict[iri][0]
            item_prefixes = QtWidgets.QTableWidgetItem()
            item_prefixes.setText(str(prefixes))
            item_prefixes.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

            nodes = self.project.IRI_prefixes_nodes_dict[iri][1]
            item_nodes = QtWidgets.QTableWidgetItem()
            nds_ids = set()
            for n in nodes:
                nds_ids.add(n.id)
            item_nodes.setText(str(nds_ids))
            item_nodes.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

            self.table.setRowCount(self.table.rowCount() + 1)

            self.table.setItem(self.table.rowCount()-1, 0, item_iri)
            self.table.setItem(self.table.rowCount()-1, 1, item_prefixes)
            self.table.setItem(self.table.rowCount()-1, 2, item_nodes)
            self.table.resizeRowToContents(self.table.rowCount() - 1)

        #print('>>>  FillTableWithIRIPrefixNodesDictionaryKeysAndValues      END')

    def button_add(self):

        self.ADD_OR_REMOVE = 'add'
        self.process_entry_from_textboxes_for_button_add_or_remove()
        self.ADD_OR_REMOVE = None

    def button_remove(self):

        self.ADD_OR_REMOVE = 'remove'
        self.process_entry_from_textboxes_for_button_add_or_remove()
        self.ADD_OR_REMOVE = None

    def process_entry_from_textboxes_for_button_add_or_remove(self):

        prefixes = set()
        prefixes_inp = self.prefix_input_box.text().strip()
        prefixes_raw = prefixes_inp.split(',')
        for p in prefixes_raw:
            if p.strip() != '':
                prefixes.add(p.strip())

        iri = self.iri_input_box.text().strip()

        self.iri_input_box.clear()
        self.prefix_input_box.clear()

        if iri == '':
            print('iri field is empty')
            self.entry_status.showMessage('iri field is empty', 10000)
            return

        Duplicate_IRI_prefixes_nodes_dict_1 = self.project.copy_IRI_prefixes_nodes_dictionaries(
            self.project.IRI_prefixes_nodes_dict, dict())

        Duplicate_IRI_prefixes_nodes_dict_2 = self.project.copy_IRI_prefixes_nodes_dictionaries(
            self.project.IRI_prefixes_nodes_dict, dict())

        process = False

        if len(prefixes) > 0:
            for prefix in prefixes:

                if self.ADD_OR_REMOVE == 'remove':
                    self.project.removeIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, prefix)
                    if self.ENTRY_REMOVE_OK_var is True:
                        self.ENTRY_REMOVE_OK_var = False
                        process = True
                    else:
                        LOGGER.error('transaction was not executed correctly; problem with a prefix/IRI')
                        return
                elif self.ADD_OR_REMOVE == 'add':
                    self.project.addIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, prefix)
                    if self.ENTRY_ADD_OK_var is True:
                        self.ENTRY_ADD_OK_var = False
                        process = True
                    else:
                        LOGGER.error('transaction was not executed correctly; problem with a prefix/IRI')
                        return
                else:
                    pass
        else:

            if self.ADD_OR_REMOVE == 'remove':
                self.project.removeIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, None)

                if self.ENTRY_REMOVE_OK_var is True:
                    self.ENTRY_REMOVE_OK_var = False
                    process = True
            elif self.ADD_OR_REMOVE == 'add':
                self.project.addIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, None)

                if self.ENTRY_ADD_OK_var is True:
                    self.ENTRY_ADD_OK_var = False
                    process = True
            else:
                pass

        if process is True:
            self.session.undostack.push(CommandProjetSetIRIPrefixesNodesDict(self.project,\
                                        Duplicate_IRI_prefixes_nodes_dict_2,Duplicate_IRI_prefixes_nodes_dict_1))

    #############################################
    #   INTERFACE
    #################################

    def redraw(self):
        """
        Redraw the content of the widget.
        """
        width = self.width()
        scrollbar = self.verticalScrollBar()
        if scrollbar.isVisible():
            width -= scrollbar.width()
        #sizeHint = self.table.sizeHint()
        #height = sizeHint.height()
        height_of_other_objects = self.dictionary_display_button.height() + self.entry_status.height()+\
                                  self.entry_button.height() + self.remove_entry_button.height() +\
                                  self.iri_input_box.height() + self.prefix_input_box.height() + self.tableheader_nodes.height()
        height = (self.height()) - (height_of_other_objects)
        self.table.setFixedWidth(width)
        self.table.setFixedHeight(clamp(height, 0))

        self.table.setColumnWidth(0,self.width()/3)
        self.table.setColumnWidth(1,self.width()/3)
        self.table.setColumnWidth(2,self.width()/3)

    @QtCore.pyqtSlot()
    def run(self):
        """
        Set the current stacked widget.
        """

        self.table.setRowCount(0)
        self.table.setColumnCount(3)

        ###############       END     ##############

        #print('self.table.rowCount()',self.table.rowCount())

        self.FillTableWithIRIPrefixNodesDictionaryKeysAndValues()

        ##############################################################################
        self.redraw()








