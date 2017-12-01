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

import math

from abc import ABCMeta, abstractmethod
from operator import attrgetter

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy.core.datatypes.owl import OWLStandardIRIPrefixPairsDict
from eddy.core.datatypes.qt import BrushIcon, Font
from eddy.core.functions.misc import first, clamp, isEmpty
from eddy.core.functions.signals import connect, disconnect
from eddy.core.plugin import AbstractPlugin
from eddy.core.project import K_FUNCTIONAL, K_INVERSE_FUNCTIONAL
from eddy.core.project import K_ASYMMETRIC, K_IRREFLEXIVE, K_REFLEXIVE
from eddy.core.project import K_SYMMETRIC, K_TRANSITIVE
from eddy.core.regex import RE_CAMEL_SPACE

from eddy.ui.dock import DockWidget
from eddy.ui.fields import IntegerField, StringField
from eddy.ui.fields import CheckBox, ComboBox

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

        self.widget('iri').run()

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
        widget.setObjectName('iri')
        self.addWidget(widget)

        # CREATE DOCKING AREA WIDGET
        self.debug('Creating docking area widget')
        widget = DockWidget('Iri', QtGui.QIcon(':/icons/18/ic_info_outline_black'), self.session)
        widget.installEventFilter(self)
        widget.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        widget.setObjectName('iri_dock')
        widget.setWidget(self.widget('iri'))
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

        self.tableheader_prefix = Header('Prefix', self)
        self.tableheader_iri = Header('IRI', self)

        self.horizontalbox = QtWidgets.QHBoxLayout(self)   #to be added to main layout
        self.horizontalbox.setAlignment(QtCore.Qt.AlignTop)
        self.horizontalbox.setContentsMargins(0, 0, 0, 0)
        self.horizontalbox.setSpacing(0)
        self.horizontalbox.addWidget(self.tableheader_iri)
        self.horizontalbox.addWidget(self.tableheader_prefix)

        #############

        self.entry_status = QtWidgets.QStatusBar()

        self.entry_button = QtWidgets.QPushButton()
        self.entry_button.setText('Add entry to the table')
        self.remove_entry_button = QtWidgets.QPushButton()
        self.remove_entry_button.setText('Remove entry from table')

        connect(self.entry_button.pressed, self.process_entry_from_textbox_for_button_add)
        connect(self.remove_entry_button.pressed, self.process_entry_from_textbox_for_button_remove)

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
        self.verticalbox.addWidget(self.entry_status)

        #############

        self.table = QtWidgets.QTableWidget(self)
        self.table.setContentsMargins(0, 0, 0, 0)
        self.table.horizontalHeader().setVisible(False)

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

    def update_table_data(self):

        print('*************            update_table_data           ************')

        self.table.clear()
        self.table.setRowCount(0)

        prefix_iri_dict = dict()
        """
        for prefix,iri in self.project.prefix_IRI_dictionary.items():

            if iri in prefix_iri_dict.keys():
                corr_prefixes = prefix_iri_dict.get(iri)
                corr_prefixes.add(prefix)
                prefix_iri_dict[iri] = corr_prefixes
            else:
                new_set = set()
                new_set.add(prefix)
                prefix_iri_dict[iri] = new_set
        """
        for iri_to_add_table,prefixes_to_add_table in prefix_iri_dict.items():

            print('iri_to_add_table', iri_to_add_table)
            print('prefixes_to_add_table',prefixes_to_add_table)


            item_iri = QtWidgets.QTableWidgetItem()
            item_iri.setText(iri_to_add_table)
            item_iri.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)


            prefix_str_widget = QtWidgets.QTextEdit()

            prefixes_str = ''
            for count,i in enumerate(list(prefixes_to_add_table)):
                if count == 0:
                    prefixes_str = prefixes_str + i
                else:
                    prefixes_str = prefixes_str+'\n'+i

            print('prefixes_str',prefixes_str)

            item_prefixes = QtWidgets.QTableWidgetItem()
            item_prefixes.setText(prefixes_str)
            item_prefixes.setFlags(QtCore.Qt.ItemIsEnabled)

            print('item_iri',item_iri)
            print('item_prefixes', item_prefixes)
            print('self.table.rowCount()', self.table.rowCount())

            self.table.setRowCount(self.table.rowCount() + 1)
            self.table.setItem(self.table.rowCount() - 1, 0, item_iri)
            self.table.setItem(self.table.rowCount() - 1, 1, item_prefixes)
            self.table.resizeRowToContents(self.table.rowCount() - 1)


        print('*************            update_table_data  END         ************')

    def process_entry_from_textbox_for_button_remove(self):

        """
        nodes = self.project.nodes()
        for n in nodes:
            if n.id == 'n6':
                print('self.project.node(test,n6).iri',n.iri)
                return
        """

        prefix = self.prefix_input_box.text()
        iri = self.iri_input_box.text()
        
        if (iri is '') and (prefix is ''):
            self.entry_status.showMessage('IRI & prefix fields are blank', 5000)
            return

        if iri in self.standard_IRIs:
            self.entry_status.showMessage('Cannot modify standard IRI(s)', 5000)
            return

        if iri is self.project.iri:
            self.entry_status.showMessage('Please use Info Widget to modify project IRI', 5000)
            return

        self.project.removeIRIPrefixEntry(iri, prefix)

        """
        for r in self.table.rowCount():

            iri_entry = self.table.item(r,0)
            prefix_entries = self.table.item(r,1)

            if prefix is '':
                self.table.removeRow(r)
                r=r-1
            else:
                #delete[IRI-Prefix] pair
                if len(list(prefix_entries)) == 1:
                    self.table.removeRow(r)
                    r = r - 1
                elif len(list(prefix_entries)) > 1:
                    prefix_entries = prefix_entries.replace(prefix+'\n','')
                    self.table.setItem(r,1,prefix_entries)
        """

    def process_entry_from_textbox_for_button_add(self):

        prefix = self.prefix_input_box.text()
        iri = self.iri_input_box.text()
        """
        nodes = self.project.nodes()

        for n in nodes:
            if n.id == prefix:
                n.iri = iri
        return
        """

        if iri is '':
            self.entry_status.showMessage('IRI field is blank', 5000)
            return

        if iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.items()[1]:
            self.entry_status.showMessage('Cannot modify standard IRI(s)', 5000)
            return

        if iri is self.project.iri:
            self.entry_status.showMessage('Please use Info Widget to modify project IRI', 5000)
            return

        if prefix is OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.items()[0]:
            self.entry_status.showMessage('Cannot modify standard prefix(es)', 5000)
            return

        if prefix is self.project.prefix:
            self.entry_status.showMessage('Please use Info Widget to modify project prefix', 5000)
            return

        self.project.addIRIPrefixEntry(iri, prefix)

        #self.update_table_data()

        """
        print('dict')

        for key_prefix,value_iri in self.project.prefix_IRI_dictionary.items():
            print('key_prefix',key_prefix)
            print('value_iri',value_iri)

        print('dict END')
        """

        """
        self.prefix_input_box.clear()
        self.iri_input_box.clear()


        item_prefix = QtWidgets.QTableWidgetItem()
        item_prefix.setText(prefix)
        item_prefix.setFlags(QtCore.Qt.ItemIsEnabled)

        item_iri = QtWidgets.QTableWidgetItem()
        item_iri.setText(iri)
        item_iri.setFlags(QtCore.Qt.ItemIsEnabled)

        print('self.table.rowCount()',self.table.rowCount())

        self.table.setRowCount(self.table.rowCount() + 1)


        self.table.setItem(self.table.rowCount()-1,0,item_prefix)
        self.table.setItem(self.table.rowCount()-1,1,item_iri)
        
        #self.redraw()

        print('self.table.rowCount()', self.table.rowCount())
        
        self.entry_status.showMessage('Entry added to the table', 5000)
        """
    #############################################
    #   INTERFACE
    #################################

    def redraw(self):
        """
        Redraw the content of the widget.
        """
        print('IriWidget >>> def redraw(self):')

        width = self.width()
        scrollbar = self.verticalScrollBar()
        if scrollbar.isVisible():
            width -= scrollbar.width()
        #widget = self.table
        #widget.setFixedWidth(width)
        #sizeHint = widget.sizeHint()
        #height = sizeHint.height()
        sizeHint = self.table.sizeHint()
        height = sizeHint.height()
        print('width - ',width)
        print('height - ', height)
        self.table.setFixedWidth(width)
        self.table.setFixedHeight(clamp(height, 0))
        self.table.setColumnWidth(0,math.floor(width/2)-6)
        self.table.setColumnWidth(1,math.floor(width/2)-6)
        print('IriWidget >>> def redraw(self): END')

    def run(self):
        """
        Set the current stacked widget.
        """

        self.table.setRowCount(0)
        self.table.setColumnCount(2)

        ##########   +[std_IRI-std-Prefix]  ###############

        for std_prefix,std_iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.items():

            item_std_iri = QtWidgets.QTableWidgetItem()
            item_std_iri.setText(std_iri)
            item_std_iri.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

            item_std_prefix = QtWidgets.QTableWidgetItem()
            item_std_prefix.setText(std_prefix)
            item_std_prefix.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

            self.table.setRowCount(self.table.rowCount() + 1)

            self.table.setItem(self.table.rowCount() - 1, 0, item_std_iri)
            self.table.setItem(self.table.rowCount() - 1, 1, item_std_prefix)
            self.table.resizeRowToContents(self.table.rowCount() - 1)

        ################     +[project_IRI-project_prefix]          ################

        item_project_iri = QtWidgets.QTableWidgetItem()
        item_project_iri.setText(self.project.iri)
        item_project_iri.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

        item_std_prefix = QtWidgets.QTableWidgetItem()
        item_std_prefix.setText(self.project.prefix)
        item_std_prefix.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

        self.table.setRowCount(self.table.rowCount() + 1)

        self.table.setItem(self.table.rowCount() - 1, 0, item_project_iri)
        self.table.setItem(self.table.rowCount() - 1, 1, item_std_prefix)
        self.table.resizeRowToContents(self.table.rowCount() - 1)

        ###############       +[IRI-Set(prefix)] from self.project.IRI_prefixes_dict        ##############

        for iri,prefixes in self.project.IRI_prefixes_dict:

            item_iri = QtWidgets.QTableWidgetItem(iri)
            item_iri.setText(iri)
            item_iri.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

            item_prefix = QtWidgets.QTableWidgetItem()
            item_prefix.setText(str(prefixes))
            item_prefix.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)

            self.table.setRowCount(self.table.rowCount() + 1)

            self.table.setItem(self.table.rowCount() - 1, 0, item_iri)
            self.table.setItem(self.table.rowCount() - 1, 1, item_prefix)
            self.table.resizeRowToContents(self.table.rowCount() - 1)

        ##############################################################################

        #self.redraw()







