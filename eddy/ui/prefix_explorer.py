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


from eddy.core.datatypes.qt import Font

from eddy.core.commands.nodes_2 import CommandProjetSetIRIPrefixesNodesDict
from eddy.core.datatypes.owl import OWLStandardIRIPrefixPairsDict
from eddy.core.output import getLogger
from eddy.core.common import HasThreadingSystem, HasWidgetSystem
from eddy.core.functions.signals import connect, disconnect
from eddy.core.exporters.owl2 import OWLOntologyFetcher
from eddy.core.datatypes.owl import OWLAxiom,OWLSyntax
from eddy.core.worker import AbstractWorker
from jnius import autoclass, cast, detach
from eddy.core.datatypes.graphol import Special
import sys,math, threading


LOGGER = getLogger()


class PrefixExplorerDialog(QtWidgets.QDialog, HasThreadingSystem):
    """
    Extends QtWidgets.QDialog with facilities to perform Ontology Consistency check
    """
    sgnWork = QtCore.pyqtSignal()

    def __init__(self, project, session):
        """
        Initialize the dialog.
        :type project: Project
        :type session: Session
        """
        super().__init__(session)

        self.project = project
        self.session = session
        self.workerThread = None
        self.worker = None

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.verticalbox = QtWidgets.QVBoxLayout(self)  # to be added to main layout
        self.verticalbox.setAlignment(QtCore.Qt.AlignTop)
        self.verticalbox.setContentsMargins(0, 0, 0, 0)
        self.verticalbox.setSpacing(0)


        #############

        self.table = QtWidgets.QTableWidget(self)
        self.table.setContentsMargins(0, 0, 0, 0)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumWidth(self.width())
        self.table.setMinimumHeight(self.height())

        connect(self.table.cellPressed, self.cell_pressed)

        connect(self.project.sgnIRIPrefixNodeDictionaryUpdated, self.UpdateTableForIRI)

        connect(self.project.sgnIRIPrefixesEntryModified, self.entry_MODIFY_ok)
        connect(self.project.sgnIRIPrefixEntryAdded, self.entry_ADD_ok)
        connect(self.project.sgnIRIPrefixEntryRemoved, self.entry_REMOVE_OK)
        connect(self.project.sgnIRIPrefixesEntryIgnored, self.entry_NOT_OK)

        #############
        self.verticalbox.addWidget(self.table)

        self.mainLayout.addLayout(self.verticalbox)
        #############

        self.setLayout(self.mainLayout)
        self.hide()
        self.setWindowModality(QtCore.Qt.NonModal)
        self.show()
        self.setWindowTitle('Prefix explorer')

        self.setContentsMargins(20, 20, 20, 20)
        self.setMinimumSize(QtCore.QSize(600, 400))
        #self.setFixedWidth(600)
        #self.setFixedHeight(400)
        #self.setMinimumWidth(200)
        #self.setMaximumHeight(600)


        self.table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        #self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        #self.setWidgetResizable(True)

        #scrollbar = self.verticalScrollBar()
        #scrollbar.installEventFilter(self)

        #self.setStyleSheet("""
                #IriWidget {background: #FFFFFF;}
                #IriWidget Header {background: #5A5050; padding-left: 4px; color: #FFFFFF;} """)

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

        self.run()

    def resizeEvent(self, QResizeEvent):

        self.redraw()

    @QtCore.pyqtSlot(str, str, str, str)
    def entry_MODIFY_ok(self,iri_from,prefix_from,iri_to,prefix_to):

        self.ENTRY_MODIFY_OK_var.add(True)

        self.session.statusBar().showMessage('Successfully modified',10000)
        print('entry_ADD_ok(self): ',iri_from,',',prefix_from,',',iri_to,',',prefix_to)

    @QtCore.pyqtSlot(str, str, str)
    def entry_ADD_ok(self,iri,prefix,message):

        self.ENTRY_ADD_OK_var.add(True)
        self.session.statusBar().showMessage(message,10000)
        print('entry_ADD_ok(self): ',iri,',',prefix,',',message)

    @QtCore.pyqtSlot(str, str, str)
    def entry_REMOVE_OK(self,iri,prefix,message):

        self.ENTRY_REMOVE_OK_var.add(True)
        self.session.statusBar().showMessage(message, 10000)
        print('entry_REMOVE_ok(self): ',iri,',',prefix,',',message)

    @QtCore.pyqtSlot(str, str, str)
    def entry_NOT_OK(self,iri,prefixes,message):

        self.ENTRY_IGNORE_var.add(True)
        self.session.statusBar().showMessage(message, 10000)
        print('entry_NOT_OK(self): ',iri,',',prefixes,',',message)

        disconnect(self.table.cellChanged, self.cell_changed)

        self.FillTableWithIRIPrefixNodesDictionaryKeysAndValues()

        connect(self.table.cellChanged, self.cell_changed)

    @QtCore.pyqtSlot(int, int)
    def cell_changed(self, r, c):

        item_changed = self.table.item(r, c)

        self.new_text = item_changed.text().strip()
        """
        if c == 0:
            self.iri_new_text = item_changed.text().strip()
        elif c==1:
            self.prefix_new_text = item_changed.text().strip()
        else:
            pass
        """

        self.ITEM_CHANGED = [r, c]
        self.add_remove_or_modify_task()

    @QtCore.pyqtSlot(int,int)
    def cell_pressed(self, r, c):

        item_to_edit = self.table.item(r, c)

        self.old_text = item_to_edit.text().strip()
        """
        if c == 0:
            self.iri_old_text = item_to_edit.text().strip()
        elif c==1:
            self.prefix_old_text = item_to_edit.text().strip()
        else:
            pass
        """

        self.ITEM_PRESSED = [r, c]

    @QtCore.pyqtSlot(str, str)
    def UpdateTableForIRI(self,iri_inp,nodes_inp):

        disconnect(self.table.cellChanged, self.cell_changed)

        self.FillTableWithIRIPrefixNodesDictionaryKeysAndValues()

        connect(self.table.cellChanged, self.cell_changed)

    def add_remove_or_modify_task(self):

        print('self.ITEM_CHANGED',self.ITEM_CHANGED)
        print('self.ITEM_PRESSED',self.ITEM_PRESSED)
        print('self.table.rowCount()',self.table.rowCount())

        if self.ITEM_CHANGED is None or self.ITEM_PRESSED is None:
            return

        if (self.ITEM_CHANGED[0] == self.ITEM_PRESSED[0]) and (self.ITEM_CHANGED[1] == self.ITEM_PRESSED[1]):

            row = self.ITEM_CHANGED[0]
            column = self.ITEM_CHANGED[1]

            if column == 0:
                # add/remove/modify IRI
                IRI_valid = self.project.check_validity_of_IRI(self.new_text)

                if IRI_valid is False:
                    self.session.statusBar().showMessage('Invalid IRI.', 15000)
                    self.table.item(row, column).setText(self.old_text)
                else:

                    if (self.old_text == '' and self.new_text != '') or \
                            (self.old_text != '' and self.new_text != '' and row == self.table.rowCount()-1) :

                        # Add IRI
                        prefix_inp = self.table.item(row, 1).text().strip()

                        if (prefix_inp == ''):
                            if self.new_text in self.project.IRI_prefixes_nodes_dict.keys():
                                pass
                            else:
                                self.process_entry_from_textboxes_for_button_add_or_remove(self.new_text, None, 'add')
                        else:
                            self.process_entry_from_textboxes_for_button_add_or_remove(self.new_text, prefix_inp, 'add')


                    elif self.old_text != '' and self.new_text != '':

                        # Modify IRI
                        if row == self.table.rowCount()-1:
                            pass
                        else:
                            self.process_entry_from_textboxes_for_task_modify(self.old_text, self.new_text, None, None)

                    elif self.old_text != '' and self.new_text == '':

                        # Remove IRI
                        if row == self.table.rowCount()-1:
                            pass
                        else:
                            prefix_inp = self.table.item(row, 1).text().strip()
                            if (prefix_inp == ''):
                                self.process_entry_from_textboxes_for_button_add_or_remove(self.old_text, None, 'remove')
                            else:
                                self.process_entry_from_textboxes_for_button_add_or_remove(self.old_text, prefix_inp, 'remove')
                    else:
                        pass
            else:
                # add/remove/modify prefixes

                iri_row = self.ITEM_CHANGED[0]
                iri_column = 0
                iri_inp = self.table.item(iri_row,iri_column).text().strip()

                flag = False

                for c in self.new_text:
                    if c == '':
                        pass
                    elif (not c.isalnum()):
                        flag = True
                        break
                    else:
                        pass

                if flag is True:
                    self.session.statusBar().showMessage('Spaces and special characters are not allowed in a prefix.',15000)
                    self.table.item(row,column).setText(self.old_text)
                else:

                    if self.old_text == '' and self.new_text != '':

                        # Add Prefixes
                        if iri_inp == '':
                            pass
                        else:
                            self.process_entry_from_textboxes_for_button_add_or_remove(iri_inp, self.new_text, 'add')

                    elif self.old_text != '' and self.new_text != '':

                        # Modify Prefixes
                        if row == self.table.rowCount()-1:
                            pass
                        else:
                            self.process_entry_from_textboxes_for_task_modify(None, None, self.old_text, self.new_text)

                    elif self.old_text != '' and self.new_text == '':

                        # Remove Prefixes
                        if row == self.table.rowCount()-1:
                            pass
                        else:
                            self.process_entry_from_textboxes_for_button_add_or_remove(iri_inp, self.old_text, 'remove')

                    else:
                        pass

        self.old_text = None
        self.new_text = None
        self.ITEM_CHANGED = None
        self.ITEM_EDITED = None

    def append_row_and_column_to_table(self,iri,prefix,editable,brush):

        item_iri = QtWidgets.QTableWidgetItem()
        item_iri.setText(iri)
        if editable is True:
            item_iri.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable)
        else:
            item_iri.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        if brush is not None:
            item_iri.setBackground(brush)

        item_prefix = QtWidgets.QTableWidgetItem()
        item_prefix.setText(prefix)
        if editable is True:
            item_prefix.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable)
        else:
            item_prefix.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        if brush is not None:
            item_prefix.setBackground(brush)

        self.table.setItem(self.table.rowCount() - 1, 0, item_iri)
        self.table.setItem(self.table.rowCount() - 1, 1, item_prefix)
        self.table.setRowCount(self.table.rowCount() + 1)

    def FillTableWithIRIPrefixNodesDictionaryKeysAndValues(self):

        #if (iri_to_update is None) and (nodes_to_update is None):
        print('>>>  FillTableWithIRIPrefixNodesDictionaryKeysAndValues')
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

        header_prefixes = QtWidgets.QTableWidgetItem()
        header_prefixes.setText('PREFIXES')
        header_prefixes.setFont(Font('Roboto', 15, bold=True))
        header_prefixes.setTextAlignment(QtCore.Qt.AlignCenter)
        header_prefixes.setBackground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        header_prefixes.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_prefixes.setFlags(QtCore.Qt.NoItemFlags)

        self.table.setItem(self.table.rowCount() - 1, 0, header_iri)
        self.table.setItem(self.table.rowCount() - 1, 1, header_prefixes)

        self.table.setRowCount(self.table.rowCount() + 1)

        for iri in self.project.IRI_prefixes_nodes_dict.keys():
            if iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():
                standard_prefixes = self.project.IRI_prefixes_nodes_dict[iri][0]
                standard_prefix = standard_prefixes[0]
                self.append_row_and_column_to_table(iri, standard_prefix, False, None)
                                                    #QtGui.QBrush(QtGui.QColor(50, 50, 205, 50)))

        iri = self.project.iri
        prefixes = self.project.IRI_prefixes_nodes_dict[self.project.iri][0]

        if len(prefixes) > 0:
            for p in prefixes:
                #self.append_row_and_column_to_table(iri, p, True, QtGui.QBrush(QtGui.QColor(205, 50, 50, 50)))
                self.append_row_and_column_to_table(iri, p, True, None)
        else:
            #self.append_row_and_column_to_table(iri, '', True, QtGui.QBrush(QtGui.QColor(205, 50, 50, 50)))
            self.append_row_and_column_to_table(iri, '', True, None)


        for iri in sorted(self.project.IRI_prefixes_nodes_dict.keys()):

            if iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():
                continue
            if iri == self.project.iri:
                continue

            prefixes = self.project.IRI_prefixes_nodes_dict[iri][0]

            if len(prefixes) > 0:
                for p in prefixes:
                    self.append_row_and_column_to_table(iri, p, True, None)
            else:
                self.append_row_and_column_to_table(iri, '', True, None)

        self.append_row_and_column_to_table('','',True,None)

        self.table.setRowCount(self.table.rowCount() - 1)

        self.redraw()

    def process_entry_from_textboxes_for_button_add_or_remove(self,iri_inp,prefix_inp,inp_task):

        self.ENTRY_ADD_OK_var = set()
        self.ENTRY_REMOVE_OK_var = set()
        self.ENTRY_IGNORE_var = set()

        if iri_inp == '':
            print('iri field is empty')
            self.session.statusBar().showMessage('iri field is empty', 10000)
            return

        Duplicate_IRI_prefixes_nodes_dict_1 = self.project.copy_IRI_prefixes_nodes_dictionaries(
            self.project.IRI_prefixes_nodes_dict, dict())

        Duplicate_IRI_prefixes_nodes_dict_2 = self.project.copy_IRI_prefixes_nodes_dictionaries(
            self.project.IRI_prefixes_nodes_dict, dict())

        process = False

        if (prefix_inp is not None):
            if inp_task == 'remove':
                # self.project.removeIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, prefix)
                self.project.addORremoveIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri_inp, prefix_inp,
                                                       'remove_entry')
                if (False in self.ENTRY_REMOVE_OK_var) or (True in self.ENTRY_IGNORE_var):
                    LOGGER.error('transaction was not executed correctly; problem with a prefix/IRI')
                    return
                else:
                    process = True
            elif inp_task == 'add':
                # self.project.addIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, prefix)
                self.project.addORremoveIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri_inp, prefix_inp,
                                                       'add_entry')
                if (False in self.ENTRY_ADD_OK_var) or (True in self.ENTRY_IGNORE_var):
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
    def process_entry_from_textboxes_for_task_modify(self, iri_old, iri_new, prefix_old, prefix_new):

        print('process_entry_from_textboxes_for_task_modify >>>')
        print('iri_old', iri_old)
        print('iri_new', iri_new)
        print('prefixes_old', prefix_old)
        print('prefixes_new', prefix_new)

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
                self.session.statusBar().showMessage('IRIs in selected cell and input box are the same. Nothing to change',
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

        if (prefix_old is not None) and (prefix_new is not None):

            #prefixes_old_list = self.convert_str_prefixes_in_table_to_list(prefixes_old)
            #prefixes_new_list = self.convert_str_prefixes_in_table_to_list(prefixes_new)

            # case2     prefix->prefix'          if prefix==prefix' no need for a transaction
            if (prefix_old == prefix_new):
                self.session.statusBar().showMessage(
                    'prefix(es) in selected cell and input box are the same. Nothing to change', 10000)
                return

            self.project.modifyIRIPrefixesEntry(None, [prefix_old], None, [prefix_new],
                                                Duplicate_IRI_prefixes_nodes_dict_1)

            for iri_key in Duplicate_IRI_prefixes_nodes_dict_1.keys():
                prefixes_for_iri_key = Duplicate_IRI_prefixes_nodes_dict_1[iri_key][0]
                if (prefix_old in prefixes_for_iri_key) or (prefix_new in prefixes_for_iri_key):
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

    def redraw(self):
        """
        Redraw the content of the widget.
        """
        self.table.setColumnCount(2)

        width = self.width()
        height = self.height()

        print('dialog_width',width)

        total_height_of_all_rows = 0
        for r in range(0,self.table.rowCount()+1):
            total_height_of_all_rows = total_height_of_all_rows+self.table.rowHeight(r)


        #scrollbar = self.table.verticalScrollBar()
        #if scrollbar.isVisible():
            #width -= scrollbar.width()+1



        self.table.setFixedWidth(width-40)
        self.table.setFixedHeight(height-40)

        print('self.table.height()',self.table.height())
        print('total_height_of_all_rows',total_height_of_all_rows)

        if total_height_of_all_rows >= (self.table.height()):
            scrollbar_width = 15
        else:
            scrollbar_width = 0

        self.table.setColumnWidth(0, (7*(self.table.width() - scrollbar_width)/ 10))
        self.table.setColumnWidth(1, (3*(self.table.width() - scrollbar_width)/ 10))

        print('self.table.columnWidth(0)',self.table.columnWidth(0))
        print('self.table.columnWidth(1)', self.table.columnWidth(1))
        print('self.table.verticalScrollBar().isVisible()',self.table.verticalScrollBar().isVisible())
        print('self.table.width()',self.table.width())
        print('scrollbar_width',scrollbar_width)

        for r in range(0,self.table.rowCount()):
            #self.table.setRowHeight(r,30)
            self.table.resizeRowToContents(r)

        print('self.table.height()',self.table.height())
        print('self.table.rowCount()',self.table.rowCount())

        self.setMaximumHeight(total_height_of_all_rows+3+40)

    @QtCore.pyqtSlot()
    def run(self):
        """
        Set the current stacked widget.
        """
        self.FillTableWithIRIPrefixNodesDictionaryKeysAndValues()
        self.redraw()

        connect(self.table.cellChanged, self.cell_changed)


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