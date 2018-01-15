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
class String_1(StringField):
    """
    This class implements the string value of an info field.
    """
    def __init__(self,  *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)
class String_2(StringField):
    """
    This class implements the string value of an info field.
    """
    def __init__(self,  *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)
class String_3(StringField):
    """
    This class implements the string value of an info field.
    """
    def __init__(self,  *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)


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

        #self.tableheader_prefixes = Header('Prefix', self)
        #self.tableheader_iri = Header(' IRI  ', self)

        self.entry_status = QtWidgets.QStatusBar()

        """
        self.entry_button = QtWidgets.QPushButton()
        self.entry_button.setText('+++')
        """
        self.remove_entry_button = QtWidgets.QPushButton()
        self.remove_entry_button.setText('---')
        self.modify_entry_button = QtWidgets.QPushButton()

        self.buttons_layout = QtWidgets.QHBoxLayout(self)
        self.buttons_layout.setAlignment(QtCore.Qt.AlignTop)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(0)
        #self.buttons_layout.addWidget(self.entry_button)
        self.buttons_layout.addWidget(self.remove_entry_button)

        #connect(self.entry_button.pressed, self.button_add)
        connect(self.remove_entry_button.pressed, self.button_remove)

        self.verticalbox = QtWidgets.QVBoxLayout(self)  # to be added to main layout
        self.verticalbox.setAlignment(QtCore.Qt.AlignTop)
        self.verticalbox.setContentsMargins(0, 0, 0, 0)
        self.verticalbox.setSpacing(0)
        self.verticalbox.addLayout(self.buttons_layout)
        self.verticalbox.addWidget(self.entry_status)

        #############

        self.table = QtWidgets.QTableWidget(self)
        self.table.setContentsMargins(0, 0, 0, 0)

        self.horizontalbox_3 = QtWidgets.QHBoxLayout(self)    #to be added to main layout
        self.horizontalbox_3.setAlignment(QtCore.Qt.AlignTop)
        self.horizontalbox_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalbox_3.setSpacing(0)
        self.horizontalbox_3.addLayout(self.table)

        #############

        self.mainLayout.addLayout(self.verticalbox)
        self.mainLayout.addLayout(self.horizontalbox_3)

        #############

        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(QtCore.QSize(216, 120))
        self.setMinimumWidth(350)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setWidgetResizable(True)

        self.setStyleSheet("""
        PrefixWidget {
          background: #FFFFFF;
        }
                
        PrefixWidget String_1{
          background: #bccbff;
          border-top: none;
          border-right: none;
          border-bottom: 1px solid #BBDEFB !important;
          border-left: 1px solid #BBDEFB !important;
          padding: 0 0 0 4px;
          text-align:left;
        }
        
        PrefixWidget String_2{
          background: #ffc1c1;
          border-top: none;
          border-right: none;
          border-bottom: 1px solid #BBDEFB !important;
          border-left: 1px solid #BBDEFB !important;
          padding: 0 0 0 4px;
          text-align:left;
        }
        
        PrefixWidget String_3{
          background: #ffffff;
          border-top: none;
          border-right: none;
          border-bottom: 1px solid #BBDEFB !important;
          border-left: 1px solid #BBDEFB !important;
          padding: 0 0 0 4px;
          text-align:left;
        }
        
        PrefixWidget Header {
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

        self.ADD_OR_REMOVE = None

        self.ITEM_ACTIVATED = None

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

    def button_remove(self):

        for r in range(0,self.table.rowCount()):

            iri=self.table.itemAt(r, QtWidgets.QFormLayout.LabelRole).widget()
            prefixes=self.table.itemAt(r, QtWidgets.QFormLayout.FieldRole).widget()

            disconnect(iri,self.module_for_cell_modified)
            disconnect(prefixes, self.module_for_cell_modified)

            item_to_delete = self.table.takeAt(0)
            self.table.removeItem(item_to_delete)
            del item_to_delete

        del self.table

        self.table = QtWidgets.QFormLayout()
        self.table.setContentsMargins(0, 0, 0, 0)

        self.FillTableWithIRIPrefixNodesDictionaryKeysAndValues()
        self.redraw()

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

        self.clear_table()
        self.FillTableWithIRIPrefixNodesDictionaryKeysAndValues()
        self.redraw()

    @QtCore.pyqtSlot()
    def module_for_cell_modified(self):

        for r in range(1,self.table.rowCount()-1):
            iri_widget=self.table.itemAt(r, QtWidgets.QFormLayout.LabelRole).widget()
            prefixes_widget=self.table.itemAt(r, QtWidgets.QFormLayout.FieldRole).widget()

            prefixes_widget_raw_val = prefixes_widget.value().strip()
            prefixes_widget_processed_str = prefixes_widget_raw_val.replace(' ','')

            #iri is not changed
            if iri_widget.value().strip() in self.project.IRI_prefixes_nodes_dict.keys():
                prefixes_in_backup = self.convert_set_to_text_comma_seperated(\
                    self.project.IRI_prefixes_nodes_dict[iri_widget.value().strip()][0])

                #prefixes_is_changed
                if prefixes_in_backup != prefixes_widget_processed_str:

                    if prefixes_in_backup !='':

                        if prefixes_widget_processed_str == '':
                            #val -> '' (remove prefixes_widget)
                            pass
                        elif prefixes_widget_processed_str != '':
                            #val1 -> val2 (modify prefixes_widget)
                            self.process_entry_from_textboxes_for_task_modify(None,None,\
                                        prefixes_in_backup,prefixes_widget_processed_str)
                            return
                    else:

                        if prefixes_widget_processed_str == '':
                            #nothing to change(case not possible)
                            pass
                        elif prefixes_widget_processed_str != '':
                            #'' -> val (add prefixes_widget)
                            pass
            #iri is changed
            else:
                difference = self.get_list_of_iris_changed_or_removed_in_widget()

                if len(difference) !=1:
                    LOGGER.critical('number of IRIs changed is !=1.')
                prev_iri = difference[0]

                if iri_widget.value().strip() == '':
                    # iri' -> '' and hence remove signal for [iri_widget] has to be emited
                    pass
                else:
                    #(iri.value().strip()) is not in backup data; it also contains a val(!='')
                    # an iri' -> (iri_widget.value().strip())
                    self.process_entry_from_textboxes_for_task_modify(prev_iri,iri_widget.value().strip(),None,None)
                    return

        empty_iri = self.table.itemAt(self.table.rowCount()-1, QtWidgets.QFormLayout.LabelRole).widget()
        empty_prefixes = self.table.itemAt(self.table.rowCount()-1, QtWidgets.QFormLayout.FieldRole).widget()

        # add signal needs to be sent
        if empty_iri !='':
            print('empty_iri !='':')
        if empty_prefixes !='':
            print('empty_prefixes !='':')

    #needs editing
    @QtCore.pyqtSlot(str,str)
    def UpdateTableForIRI(self,iri_inp,nodes_inp):

        print('UpdateTableForIRI    >>> iri_inp-nodes_inp >',iri_inp,' - ',nodes_inp)

        self.clear_table()
        self.FillTableWithIRIPrefixNodesDictionaryKeysAndValues()
        self.redraw()

    def clear_table(self):

        for r in range(0,self.table.rowCount()):

            iri=self.table.itemAt(r, QtWidgets.QFormLayout.LabelRole).widget()
            prefixes=self.table.itemAt(r, QtWidgets.QFormLayout.FieldRole).widget()

            disconnect(iri,self.module_for_cell_modified)
            disconnect(prefixes, self.module_for_cell_modified)
            del iri
            del prefixes
            #item_to_delete = self.table.takeAt(0)
            #self.table.removeItem(item_to_delete)
            #del item_to_delete

        del self.table

        self.table = QtWidgets.QFormLayout()
        self.table.setContentsMargins(0, 0, 0, 0)

    def get_list_of_iris_changed_or_removed_in_widget(self):

        iri_widget_set = []
        difference = []

        for r in range(1,self.table.rowCount()-1):
            iri_widget=self.table.itemAt(r, QtWidgets.QFormLayout.LabelRole).widget()
            iri_widget_set.append(iri_widget.text().strip())

        for iri_backup in self.project.IRI_prefixes_nodes_dict.keys():
            if iri_backup not in iri_widget_set:
                difference.append(iri_backup)

        return difference

    def FillTableWithStandardData(self):

        for iri in self.project.IRI_prefixes_nodes_dict.keys():
            if iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():

                item_iri = String_1(self)
                item_iri.setText(iri)
                connect(item_iri.editingFinished, self.module_for_cell_modified)

                prefixes = self.project.IRI_prefixes_nodes_dict[iri][0]
                item_prefixes = String_1(self)
                item_prefixes.setText(self.convert_set_to_text_comma_seperated(prefixes))
                connect(item_prefixes.editingFinished, self.module_for_cell_modified)

                self.table.addRow(item_iri, item_prefixes)

        iri = self.project.iri
        item_iri = String_2(self)
        item_iri.setText(iri)
        connect(item_iri.editingFinished, self.module_for_cell_modified)

        prefixes = self.project.IRI_prefixes_nodes_dict[self.project.iri][0]
        item_prefixes = String_2(self)
        item_prefixes.setText(self.convert_set_to_text_comma_seperated(prefixes))
        connect(item_prefixes.editingFinished, self.module_for_cell_modified)

        self.table.addRow(item_iri, item_prefixes)

    def FillTableWithIRIPrefixNodesDictionaryKeysAndValues(self):

        # print('>>>  FillTableWithIRIPrefixNodesDictionaryKeysAndValues')
        # first delete all entries from the dictionary id present
        # add standard IRIs
        # add key value pairs from dict

        #self.table.clear()

        header_iri = Header(self)
        header_iri.setText('IRI')
        header_iri.setFont(Font('Roboto', 15, bold=True))

        header_prefixes = Header(self)
        header_prefixes.setText('PREFIXES')
        header_prefixes.setFont(Font('Roboto', 15, bold=True))

        self.table.addRow(header_iri, header_prefixes)
        self.FillTableWithStandardData()

        for iri in sorted(self.project.IRI_prefixes_nodes_dict.keys()):

            if iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():
                continue
            if iri == self.project.iri:
                continue

            item_iri = String_3(self)
            item_iri.setText(iri)

            connect(item_iri.editingFinished, self.module_for_cell_modified)

            prefixes = self.project.IRI_prefixes_nodes_dict[iri][0]
            item_prefixes = String_3(self)
            item_prefixes.setText(self.convert_set_to_text_comma_seperated(prefixes))
            connect(item_prefixes.editingFinished, self.module_for_cell_modified)

            self.table.addRow(item_iri, item_prefixes)

        empty_item_iri = String_3(self)
        empty_item_iri.setText('')
        connect(empty_item_iri.editingFinished, self.module_for_cell_modified)

        empty_item_prefixes = String_3(self)
        empty_item_prefixes.setText('')
        connect(empty_item_prefixes.editingFinished, self.module_for_cell_modified)

        self.table.addRow(empty_item_iri, empty_item_prefixes)

        self.redraw()

    def convert_set_to_text_comma_seperated(self,inp_set):

        return_str = ''

        for p in inp_set:
            return_str = return_str+p+', '

        if len(return_str)>=2:
            if return_str[len(return_str)-2] == ',' and return_str[len(return_str)-1] == ' ':
                return return_str[0:len(return_str)-2]

        return return_str

    def convert_prefixes_in_table_to_set(self,prefixes_str):

        if prefixes_str is None:
            return None

        prefixes_set = set()

        prefixes_str_split = prefixes_str.split(',')

        for prefix_raw in prefixes_str_split:
                prefix = prefix_raw.strip()
                if prefix != '':
                    prefixes_set.add(prefix)

        print('return prefixes_set',prefixes_set)
        return prefixes_set

    #has to be edited
    def process_entry_from_textboxes_for_task_add_or_remove(self):

        self.ENTRY_ADD_OK_var = set()
        self.ENTRY_REMOVE_OK_var = set()
        self.ENTRY_IGNORE_var = set()

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
                    #self.project.removeIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, prefix)
                    self.project.addORremoveIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, prefix, 'remove_entry')
                    if (False in self.ENTRY_REMOVE_OK_var) or (True in self.ENTRY_IGNORE_var):
                        LOGGER.error('transaction was not executed correctly; problem with a prefix/IRI')
                        return
                    else:
                        process = True
                elif self.ADD_OR_REMOVE == 'add':
                    #self.project.addIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, prefix)
                    self.project.addORremoveIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, prefix, 'add_entry')
                    if (False in self.ENTRY_ADD_OK_var) or (True in self.ENTRY_IGNORE_var) :
                        LOGGER.error('transaction was not executed correctly; problem with a prefix/IRI')
                        return
                    else:
                        process = True
                else:
                    pass
        else:
            if self.ADD_OR_REMOVE == 'remove':
                #self.project.removeIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, None)
                self.project.addORremoveIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, None, 'remove_entry')
                if (False in self.ENTRY_REMOVE_OK_var) or (True in self.ENTRY_IGNORE_var):
                    LOGGER.error('transaction was not executed correctly; problem with IRI')
                    return
                else:
                    process = True
            elif self.ADD_OR_REMOVE == 'add':
                #self.project.addIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, None)
                self.project.addORremoveIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, None, 'add_entry')
                if (False in self.ENTRY_ADD_OK_var) or (True in self.ENTRY_IGNORE_var):
                    LOGGER.error('transaction was not executed correctly; problem with IRI')
                    return
                else:
                    process = True
            else:
                pass

        if process is True:
            self.session.undostack.push(CommandProjetSetIRIPrefixesNodesDict(self.project,\
                                        Duplicate_IRI_prefixes_nodes_dict_2,Duplicate_IRI_prefixes_nodes_dict_1, [iri], None))

        self.ENTRY_ADD_OK_var = set()
        self.ENTRY_REMOVE_OK_var = set()
        self.ENTRY_IGNORE_var = set()

    # has to be edited
    def process_entry_from_textboxes_for_task_modify(self,iri_old,iri_new,prefixes_old,prefixes_new):

        print('process_entry_from_textboxes_for_task_modify >>>')
        print('iri_old',iri_old)
        print('iri_new',iri_new)
        print('prefixes_old',prefixes_old)
        print('prefixes_new',prefixes_new)

        self.ENTRY_MODIFY_OK_var = set()
        self.ENTRY_IGNORE_var = set()

        Duplicate_IRI_prefixes_nodes_dict_1 = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict, dict())
        Duplicate_IRI_prefixes_nodes_dict_2 = self.project.copy_IRI_prefixes_nodes_dictionaries(self.project.IRI_prefixes_nodes_dict, dict())

        process = False

        iris_to_be_updated = []

        if (iri_old is not None) and (iri_new is not None):

            # Case1     IRI->IRI'         if iri==iri' no need for a transaction
            if (iri_old == iri_new):
                print('case1')
                self.entry_status.showMessage('IRIs in selected cell and input box are the same. Nothing to change', 10000)
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

            prefixes_old_set = self.convert_prefixes_in_table_to_set(prefixes_old)
            prefixes_new_set = self.convert_prefixes_in_table_to_set(prefixes_new)

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
                Duplicate_IRI_prefixes_nodes_dict_2, Duplicate_IRI_prefixes_nodes_dict_1, iris_to_be_updated, None))

        self.ENTRY_MODIFY_OK_var = set()
        self.ENTRY_IGNORE_var = set()

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

        height_of_other_objects = self.entry_status.height()+20*self.table.rowCount()
        self.setFixedHeight(height_of_other_objects)

        for r in range(0,self.table.rowCount()):

            iri=self.table.itemAt(r, QtWidgets.QFormLayout.LabelRole)
            prefixes=self.table.itemAt(r, QtWidgets.QFormLayout.FieldRole)

            #print('r', r)

            if iri is not None:
                #print('type(iri)',type(iri))
                #print('type(iri.widget())', type(iri.widget()))
                iri.widget().setFixedWidth(7 * self.width() / 10)
                #print('iri', iri.widget().text())

            if prefixes is not None:
                #print('type(prefixes)',type(prefixes))
                #print('type(prefixes.widget())', type(prefixes.widget()))
                #print('prefixes', prefixes.widget().text())
                prefixes.widget().setFixedWidth(3*self.width()/10)


    @QtCore.pyqtSlot()
    def run(self):
        """
        Set the current stacked widget.
        """
        self.FillTableWithIRIPrefixNodesDictionaryKeysAndValues()
        self.redraw()









