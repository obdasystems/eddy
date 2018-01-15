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
from eddy.core.output import getLogger

from eddy.ui.dock import DockWidget
from eddy.ui.fields import StringField

import sys

LOGGER = getLogger()


class PrefixExplorerPlugin(AbstractPlugin):
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

        widget = self.widget('Prefix Explorer')

        connect(self.project.sgnIRIPrefixNodeDictionaryUpdated, widget.UpdateTableForIRI)

        connect(self.project.sgnIRIPrefixesEntryModified, widget.entry_MODIFY_ok)
        connect(self.project.sgnIRIPrefixEntryAdded, widget.entry_ADD_ok)
        connect(self.project.sgnIRIPrefixEntryRemoved, widget.entry_REMOVE_OK)
        connect(self.project.sgnIRIPrefixesEntryIgnored, widget.entry_NOT_OK)

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
        menu.removeAction(self.widget('Prefix_dock').toggleViewAction())

        # UNINSTALL THE PALETTE DOCK WIDGET
        self.debug('Uninstalling docking area widget')
        self.session.removeDockWidget(self.widget('Prefix_dock'))


    def start(self):
        """
        Perform initialization tasks for the plugin.
        """
        # INITIALIZE THE WIDGET
        self.debug('Creating Prefix Explorer widget')
        widget = PrefixWidget(self)
        widget.setObjectName('Prefix Explorer')
        self.addWidget(widget)

        # CREATE DOCKING AREA WIDGET
        self.debug('Creating docking area widget')
        widget = DockWidget('Prefix Explorer', QtGui.QIcon(':/icons/18/ic_info_outline_black'), self.session)
        widget.installEventFilter(self)
        #widget.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        widget.setAllowedAreas(QtCore.Qt.NoDockWidgetArea)
        widget.setObjectName('Prefix_dock')
        widget.setWidget(self.widget('Prefix Explorer'))
        self.addWidget(widget)

        # CREATE ENTRY IN VIEW MENU
        self.debug('Creating docking area widget toggle in "view" menu')
        menu = self.session.menu('view')
        menu.addAction(self.widget('Prefix_dock').toggleViewAction())

        # INSTALL DOCKING AREA WIDGET
        self.debug('Installing docking area widget')
        #self.session.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.widget('Prefix_dock'))
        self.session.addDockWidget(QtCore.Qt.NoDockWidgetArea, self.widget('Prefix_dock'))

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


class PrefixWidget(QtWidgets.QScrollArea):
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


        connect(self.table.cellPressed, self.cell_edited)

        #############
        self.verticalbox.addWidget(self.table)

        self.mainLayout.addLayout(self.verticalbox)

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

        self.ITEM_EDITED = None
        self.ITEM_CHANGED = None
        self.old_text = None
        self.new_text = None
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
    @QtCore.pyqtSlot(str, str, str, str)
    def entry_MODIFY_ok(self,iri_from,prefix_from,iri_to,prefix_to):

        self.ENTRY_MODIFY_OK_var.add(True)

        self.entry_status.showMessage('Successfully modified',10000)
        print('entry_ADD_ok(self): ',iri_from,',',prefix_from,',',iri_to,',',prefix_to)

    @QtCore.pyqtSlot(str, str, str)
    def entry_ADD_ok(self,iri,prefix,message):

        self.ENTRY_ADD_OK_var.add(True)
        self.entry_status.showMessage(message,10000)
        print('entry_ADD_ok(self): ',iri,',',prefix,',',message)

    @QtCore.pyqtSlot(str, str, str)
    def entry_REMOVE_OK(self,iri,prefix,message):

        self.ENTRY_REMOVE_OK_var.add(True)
        self.entry_status.showMessage(message, 10000)
        print('entry_REMOVE_ok(self): ',iri,',',prefix,',',message)

    @QtCore.pyqtSlot(str, str, str)
    def entry_NOT_OK(self,iri,prefixes,message):

        self.ENTRY_IGNORE_var.add(True)
        self.entry_status.showMessage(message, 10000)
        print('entry_NOT_OK(self): ',iri,',',prefixes,',',message)

        disconnect(self.table.cellChanged, self.cell_changed)

        self.FillTableWithIRIPrefixNodesDictionaryKeysAndValues()

        connect(self.table.cellChanged, self.cell_changed)

    @QtCore.pyqtSlot(int, int)
    def cell_changed(self, r, c):

        item_changed = self.table.item(r, c)
        self.new_text = item_changed.text().strip()
        self.ITEM_CHANGED = [r, c]

        self.add_remove_or_modify_task()

    @QtCore.pyqtSlot(int,int)
    def cell_edited(self, r, c):

        item_to_edit = self.table.item(r, c)
        self.old_text = item_to_edit.text().strip()
        self.ITEM_EDITED = [r, c]

    @QtCore.pyqtSlot(str, str)
    def UpdateTableForIRI(self,iri_inp,nodes_inp):

        disconnect(self.table.cellChanged, self.cell_changed)

        self.FillTableWithIRIPrefixNodesDictionaryKeysAndValues()

        connect(self.table.cellChanged, self.cell_changed)

    def add_remove_or_modify_task(self):

        print('self.ITEM_CHANGED',self.ITEM_CHANGED)
        print('self.ITEM_EDITED',self.ITEM_EDITED)

        if self.ITEM_CHANGED is None or self.ITEM_EDITED is None:
            return

        if (self.ITEM_CHANGED[0] == self.ITEM_EDITED[0]) and (self.ITEM_CHANGED[1] == self.ITEM_EDITED[1]):
            column = self.ITEM_CHANGED[1]
            if column == 0:
                # add/remove/modify IRI
                if self.old_text == '' and self.new_text != '':

                    # Add IRI
                    self.process_entry_from_textboxes_for_button_add_or_remove(self.new_text, None, 'add')

                elif self.old_text != '' and self.new_text != '':

                    # Modify IRI
                    self.process_entry_from_textboxes_for_task_modify(self.old_text, self.new_text, None, None)

                elif self.old_text != '' and self.new_text == '':

                    # Remove IRI
                    self.process_entry_from_textboxes_for_button_add_or_remove(self.old_text, None, 'remove')

                else:
                    pass
            else:
                # add/remove/modify prefixes

                iri_row = self.ITEM_CHANGED[0]
                iri_column = 0
                iri_inp = self.table.item(iri_row,iri_column).text()

                if self.old_text == '' and self.new_text != '':

                    # Add Prefixes
                    self.process_entry_from_textboxes_for_button_add_or_remove(iri_inp, self.new_text, 'add')

                elif self.old_text != '' and self.new_text != '':

                    # Modify Prefixes
                    self.process_entry_from_textboxes_for_task_modify(None, None, self.old_text, self.new_text)

                elif self.old_text != '' and self.new_text == '':

                    # Remove Prefixes
                    self.process_entry_from_textboxes_for_button_add_or_remove(iri_inp, self.old_text, 'remove')

                else:
                    pass

        self.old_text = None
        self.new_text = None
        self.ITEM_CHANGED = None
        self.ITEM_EDITED = None

    def FillTableWithStandardData(self):

        for iri in self.project.IRI_prefixes_nodes_dict.keys():
            if iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():
                item_iri = QtWidgets.QTableWidgetItem()
                item_iri.setText(iri)
                item_iri.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                item_iri.setBackground(QtGui.QBrush(QtGui.QColor(50,50,205,50)))
                self.table.setItem(self.table.rowCount() - 1, 0, item_iri)

                prefixes = self.project.IRI_prefixes_nodes_dict[iri][0]
                item_prefixes = QtWidgets.QTableWidgetItem()
                #item_prefixes.setText(str(prefixes))
                item_prefixes.setText(self.convert_set_to_comma_seperated_text(prefixes))
                item_prefixes.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                item_prefixes.setBackground(QtGui.QBrush(QtGui.QColor(50,50,205,50)))
                self.table.setItem(self.table.rowCount() - 1, 1, item_prefixes)

                self.table.setRowCount(self.table.rowCount() + 1)

        iri = self.project.iri
        item_iri = QtWidgets.QTableWidgetItem()
        item_iri.setText(iri)
        item_iri.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable)
        item_iri.setBackground(QtGui.QBrush(QtGui.QColor(205, 50, 50, 50)))
        self.table.setItem(self.table.rowCount() - 1, 0, item_iri)

        prefixes = self.project.IRI_prefixes_nodes_dict[self.project.iri][0]
        item_prefixes = QtWidgets.QTableWidgetItem()
        #item_prefixes.setText(str(prefixes))
        item_prefixes.setText(self.convert_set_to_comma_seperated_text(prefixes))
        item_prefixes.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable)
        item_prefixes.setBackground(QtGui.QBrush(QtGui.QColor(205, 50, 50, 50)))
        self.table.setItem(self.table.rowCount() - 1, 1, item_prefixes)

        self.table.setRowCount(self.table.rowCount() + 1)

    def FillTableWithIRIPrefixNodesDictionaryKeysAndValues(self):

        #if (iri_to_update is None) and (nodes_to_update is None):
        # print('>>>  FillTableWithIRIPrefixNodesDictionaryKeysAndValues')
        # first delete all entries from the dictionary id present
        # add standard IRIs
        # add key value pairs from dict
        self.table.clear()
        self.table.setRowCount(1)
        self.table.setColumnCount(2)

        header_iri = QtWidgets.QTableWidgetItem()
        header_iri.setText('IRI')
        header_iri.setFont(Font('Roboto', 15, bold=True))
        header_iri.setTextAlignment(QtCore.Qt.AlignCenter)
        header_iri.setBackground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        header_iri.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_iri.setFlags(QtCore.Qt.NoItemFlags)
        self.table.setItem(self.table.rowCount() - 1, 0, header_iri)

        header_prefixes = QtWidgets.QTableWidgetItem()
        header_prefixes.setText('PREFIXES')
        header_prefixes.setFont(Font('Roboto', 15, bold=True))
        header_prefixes.setTextAlignment(QtCore.Qt.AlignCenter)
        header_prefixes.setBackground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        header_prefixes.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_prefixes.setFlags(QtCore.Qt.NoItemFlags)
        self.table.setItem(self.table.rowCount() - 1, 1, header_prefixes)

        self.table.setRowCount(self.table.rowCount() + 1)

        self.FillTableWithStandardData()

        for iri in sorted(self.project.IRI_prefixes_nodes_dict.keys()):

            if iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():
                continue
            if iri == self.project.iri:
                continue

            item_iri = QtWidgets.QTableWidgetItem()
            item_iri.setText(iri)
            item_iri.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable)
            self.table.setItem(self.table.rowCount() - 1, 0, item_iri)

            prefixes = self.project.IRI_prefixes_nodes_dict[iri][0]
            item_prefixes = QtWidgets.QTableWidgetItem()
            #item_prefixes.setText(str(prefixes))
            item_prefixes.setText(self.convert_set_to_comma_seperated_text(prefixes))
            item_prefixes.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable)
            self.table.setItem(self.table.rowCount() - 1, 1, item_prefixes)

            self.table.setRowCount(self.table.rowCount() + 1)

        item_iri = QtWidgets.QTableWidgetItem()
        item_iri.setText('')
        item_iri.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable)
        self.table.setItem(self.table.rowCount() - 1, 0, item_iri)

        item_prefixes = QtWidgets.QTableWidgetItem()
        # item_prefixes.setText(str(prefixes))
        item_prefixes.setText('')
        item_prefixes.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable)
        self.table.setItem(self.table.rowCount() - 1, 1, item_prefixes)

        #self.table.setRowCount(self.table.rowCount() + 1)
        #self.table.setRowCount(self.table.rowCount() - 1)

        self.redraw()

    def convert_set_to_comma_seperated_text(self,inp_set):

        return_str = ''

        for p in inp_set:
            return_str = return_str+p+', '

        if len(return_str)>=2:
            if return_str[len(return_str)-2] == ',' and return_str[len(return_str)-1] == ' ':
                return return_str[0:len(return_str)-2]

        return return_str

    def convert_str_prefixes_in_table_to_set(self,prefixes_str):

        if prefixes_str is None:
            return None

        prefixes_set = set()

        prefixes_str_split = prefixes_str.split(',')

        for prefix_raw in prefixes_str_split:
            prefix = prefix_raw.strip()
            if prefix != '':
                prefixes_set.add(prefix)

        return prefixes_set

    def process_entry_from_textboxes_for_button_add_or_remove(self,iri_inp,prefixes_inp,inp_task):

        self.ENTRY_ADD_OK_var = set()
        self.ENTRY_REMOVE_OK_var = set()
        self.ENTRY_IGNORE_var = set()

        prefixes = self.convert_str_prefixes_in_table_to_set(prefixes_inp)

        if iri_inp == '':
            print('iri field is empty')
            self.entry_status.showMessage('iri field is empty', 10000)
            return

        Duplicate_IRI_prefixes_nodes_dict_1 = self.project.copy_IRI_prefixes_nodes_dictionaries(
            self.project.IRI_prefixes_nodes_dict, dict())

        Duplicate_IRI_prefixes_nodes_dict_2 = self.project.copy_IRI_prefixes_nodes_dictionaries(
            self.project.IRI_prefixes_nodes_dict, dict())

        process = False

        if (prefixes is not None) and (len(prefixes) > 0):
            for prefix in prefixes:
                if inp_task == 'remove':
                    #self.project.removeIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, prefix)
                    self.project.addORremoveIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri_inp, prefix, 'remove_entry')
                    if (False in self.ENTRY_REMOVE_OK_var) or (True in self.ENTRY_IGNORE_var):
                        LOGGER.error('transaction was not executed correctly; problem with a prefix/IRI')
                        return
                    else:
                        process = True
                elif inp_task == 'add':
                    #self.project.addIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, prefix)
                    self.project.addORremoveIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri_inp, prefix, 'add_entry')
                    if (False in self.ENTRY_ADD_OK_var) or (True in self.ENTRY_IGNORE_var) :
                        LOGGER.error('transaction was not executed correctly; problem with a prefix/IRI')
                        return
                    else:
                        process = True
                else:
                    pass
        else:
            if inp_task == 'remove':
                #self.project.removeIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, None)
                self.project.addORremoveIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri_inp, None, 'remove_entry')
                if (False in self.ENTRY_REMOVE_OK_var) or (True in self.ENTRY_IGNORE_var):
                    LOGGER.error('transaction was not executed correctly; problem with IRI')
                    return
                else:
                    process = True
            elif inp_task == 'add':
                #self.project.addIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, None)
                self.project.addORremoveIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri_inp, None, 'add_entry')
                if (False in self.ENTRY_ADD_OK_var) or (True in self.ENTRY_IGNORE_var):
                    LOGGER.error('transaction was not executed correctly; problem with IRI')
                    return
                else:
                    process = True
            else:
                pass

        if process is True:
            self.session.undostack.push(CommandProjetSetIRIPrefixesNodesDict(self.project,\
                                        Duplicate_IRI_prefixes_nodes_dict_2,Duplicate_IRI_prefixes_nodes_dict_1, [iri_inp], None))

        self.ENTRY_ADD_OK_var = set()
        self.ENTRY_REMOVE_OK_var = set()
        self.ENTRY_IGNORE_var = set()

    # has to be edited
    def process_entry_from_textboxes_for_task_modify(self, iri_old, iri_new, prefixes_old, prefixes_new):

        print('process_entry_from_textboxes_for_task_modify >>>')
        print('iri_old', iri_old)
        print('iri_new', iri_new)
        print('prefixes_old', prefixes_old)
        print('prefixes_new', prefixes_new)

        self.ENTRY_MODIFY_OK_var = set()
        self.ENTRY_IGNORE_var = set()

        Duplicate_IRI_prefixes_nodes_dict_1 = self.project.copy_IRI_prefixes_nodes_dictionaries(
            self.project.IRI_prefixes_nodes_dict, dict())
        Duplicate_IRI_prefixes_nodes_dict_2 = self.project.copy_IRI_prefixes_nodes_dictionaries(
            self.project.IRI_prefixes_nodes_dict, dict())

        process = False

        iris_to_be_updated = []

        if (iri_old is not None) and (iri_new is not None):

            # Case1     IRI->IRI'         if iri==iri' no need for a transaction
            if (iri_old == iri_new):
                print('case1')
                self.entry_status.showMessage('IRIs in selected cell and input box are the same. Nothing to change',
                                              10000)
                return

            self.project.modifyIRIPrefixesEntry(iri_old, None, iri_new, None, Duplicate_IRI_prefixes_nodes_dict_1)
            iris_to_be_updated.append(iri_old)
            iris_to_be_updated.append(iri_new)

            if (False in self.ENTRY_MODIFY_OK_var) or (True in self.ENTRY_IGNORE_var):
                LOGGER.error('transaction was not executed correctly; problem with a prefix/IRI')
                return
            else:
                process = True

        if (prefixes_old is not None) and (prefixes_new is not None):

            prefixes_old_set = self.convert_str_prefixes_in_table_to_set(prefixes_old)
            prefixes_new_set = self.convert_str_prefixes_in_table_to_set(prefixes_new)

            # case2     prefix(es)->prefix(es)'          if prefix(es)==prefix(es)' no need for a transaction
            if (prefixes_old_set.issubset(prefixes_new_set) and prefixes_new_set.issubset(
                    prefixes_old_set)):
                self.entry_status.showMessage(
                    'prefix(es) in selected cell and input box are the same. Nothing to change', 10000)
                return

            self.project.modifyIRIPrefixesEntry(None, prefixes_old_set, None, prefixes_new_set,
                                                Duplicate_IRI_prefixes_nodes_dict_1)

            for iri_key in Duplicate_IRI_prefixes_nodes_dict_1.keys():
                prefixes_for_iri_key = Duplicate_IRI_prefixes_nodes_dict_1[iri_key][0]
                C1 = prefixes_for_iri_key.issubset(prefixes_old_set) and prefixes_old_set.issubset(
                    prefixes_for_iri_key)
                C2 = prefixes_for_iri_key.issubset(prefixes_new_set) and prefixes_new_set.issubset(
                    prefixes_for_iri_key)
                if C1 or C2:
                    iris_to_be_updated.append(iri_key)

            if (False in self.ENTRY_MODIFY_OK_var) or (True in self.ENTRY_IGNORE_var):
                LOGGER.error('transaction was not executed correctly; problem with a prefix/IRI')
                return
            else:
                process = True

        if process is True:
            self.session.undostack.push(CommandProjetSetIRIPrefixesNodesDict(self.project, \
                                                                             Duplicate_IRI_prefixes_nodes_dict_2,
                                                                             Duplicate_IRI_prefixes_nodes_dict_1,
                                                                             iris_to_be_updated, None))

        self.ENTRY_MODIFY_OK_var = set()
        self.ENTRY_IGNORE_var = set()

    #############################################
    #   INTERFACE
    #################################

    def redraw(self):
        """
        Redraw the content of the widget.
        """

        self.table.setColumnCount(2)

        width = self.width()
        scrollbar = self.verticalScrollBar()
        if scrollbar.isVisible():
            width -= scrollbar.width()

        height_of_other_objects = self.entry_status.height()
        #self.setMinimumHeight(height_of_other_objects+30*self.table.rowCount())
        height = (self.height()) - (height_of_other_objects)

        self.table.setFixedWidth(width)
        #self.table.setFixedHeight(clamp(height, 0))
        self.table.setFixedHeight(height)

        scrollbar_width = 0
        if scrollbar.isVisible():
            scrollbar_width = scrollbar.width()
            scrollbar_width = scrollbar_width+20

        self.table.setColumnWidth(0, (7*self.width() / 10)-(scrollbar_width/2))
        self.table.setColumnWidth(1, (3*self.width() / 10)-(scrollbar_width/2))

        for r in range(0,self.table.rowCount()):
            self.table.setRowHeight(r,30)
            #self.table.resizeRowToContents(r)

    @QtCore.pyqtSlot()
    def run(self):
        """
        Set the current stacked widget.
        """
        self.FillTableWithIRIPrefixNodesDictionaryKeysAndValues()
        self.redraw()

        connect(self.table.cellChanged, self.cell_changed)