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
from eddy.core.commands.project import CommandProjectDisconnectSpecificSignals, CommandProjectConnectSpecificSignals
from eddy.core.commands.project import CommandProjectSetVersion
from eddy.core.common import HasThreadingSystem
from eddy.core.datatypes.owl import Namespace
from eddy.core.datatypes.qt import Font
from eddy.core.functions.signals import connect, disconnect
from eddy.core.output import getLogger
from eddy.ui.fields import StringField

LOGGER = getLogger()


class OntologyExplorerDialog(QtWidgets.QDialog, HasThreadingSystem):
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

        self.versionKey = Key('Version', self)
        self.versionKey.setFont(Font('Roboto', 12))
        self.versionKey.setFixedWidth(60)
        self.versionField = String(self)
        self.versionField.setFont(Font('Roboto', 12))
        self.versionField.setValue(self.project.version)
        connect(self.versionField.editingFinished, self.versionEditingFinished)
        connect(self.project.sgnUpdated, self.redraw)

        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout.setAlignment(QtCore.Qt.AlignLeft)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)

        self.horizontalLayout.addWidget(self.versionKey)
        self.horizontalLayout.addWidget(self.versionField)

        self.verticalbox = QtWidgets.QVBoxLayout(self)  # to be added to main layout
        self.verticalbox.setAlignment(QtCore.Qt.AlignTop)
        self.verticalbox.setContentsMargins(0, 0, 0, 0)
        self.verticalbox.setSpacing(0)

        self.prefixmanagerheader = Key('Prefix Manager', self)
        self.prefixmanagerheader.setFont(Font('Roboto', 12))

        # self.checkbox_layout = QtWidgets.QHBoxLayout(self)
        # self.checkbox_layout.setAlignment(QtCore.Qt.AlignHCenter)

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
        self.verticalbox.addWidget(self.prefixmanagerheader)
        self.verticalbox.addSpacing(10)
        self.verticalbox.addWidget(self.table)

        self.mainLayout.addLayout(self.horizontalLayout)
        self.mainLayout.addSpacing(20)

        self.mainLayout.addLayout(self.verticalbox)
        self.mainLayout.addSpacing(20)
        #############

        self.setLayout(self.mainLayout)
        self.setWindowModality(QtCore.Qt.NonModal)
        self.setWindowTitle('Ontology Manager')

        self.setContentsMargins(20, 20, 20, 20)
        self.setMinimumSize(QtCore.QSize(700, 400))
        # self.setFixedWidth(600)
        # self.setFixedHeight(400)
        # self.setMinimumWidth(200)
        # self.setMaximumHeight(600)

        self.clearFocus()

        self.table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

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

        self.show()
        self.run()

    def closeEvent(self, QCloseEvent):

        disconnect(self.table.cellPressed, self.cell_pressed)
        disconnect(self.table.cellChanged, self.cell_changed)

        disconnect(self.project.sgnIRIPrefixNodeDictionaryUpdated, self.UpdateTableForIRI)

        disconnect(self.project.sgnIRIPrefixesEntryModified, self.entry_MODIFY_ok)
        disconnect(self.project.sgnIRIPrefixEntryAdded, self.entry_ADD_ok)
        disconnect(self.project.sgnIRIPrefixEntryRemoved, self.entry_REMOVE_OK)
        disconnect(self.project.sgnIRIPrefixesEntryIgnored, self.entry_NOT_OK)

        self.close()

    def resizeEvent(self, QResizeEvent):
        self.redraw()

    @QtCore.pyqtSlot()
    def versionEditingFinished(self):
        """
        Executed whenever we finish to edit the ontology prefix
        """
        version = self.versionField.value()
        if self.project.version != version:
            self.session.undostack.push(CommandProjectSetVersion(self.project, self.project.version, version))
        self.versionField.clearFocus()
        # self.versionField.deselect()

    @QtCore.pyqtSlot(str, str, str, str)
    def entry_MODIFY_ok(self, iri_from, prefix_from, iri_to, prefix_to):
        self.ENTRY_MODIFY_OK_var.add(True)
        self.session.statusBar().showMessage('Successfully modified', 10000)

    @QtCore.pyqtSlot(str, str, str)
    def entry_ADD_ok(self, iri, prefix, message):
        self.ENTRY_ADD_OK_var.add(True)
        self.session.statusBar().showMessage(message, 10000)

    @QtCore.pyqtSlot(str, str, str)
    def entry_REMOVE_OK(self, iri, prefix, message):
        self.ENTRY_REMOVE_OK_var.add(True)
        self.session.statusBar().showMessage(message, 10000)

    @QtCore.pyqtSlot(str, str, str)
    def entry_NOT_OK(self, iri, prefixes, message):
        self.ENTRY_IGNORE_var.add(True)
        self.session.statusBar().showMessage(message, 10000)

        disconnect(self.table.cellChanged, self.cell_changed)

        self.FillTableWithIRIPrefixNodesDictionaryKeysAndValues()

        connect(self.table.cellChanged, self.cell_changed)

    @QtCore.pyqtSlot(int, int)
    def cell_changed(self, r, c):
        item_changed = self.table.item(r, c)
        self.new_text = item_changed.text().strip()
        self.ITEM_CHANGED = [r, c]
        self.add_remove_or_modify_task()

    @QtCore.pyqtSlot(int, int)
    def cell_pressed(self, r, c):
        item_to_edit = self.table.item(r, c)
        if item_to_edit is not None:
            self.old_text = item_to_edit.text().strip()
        self.ITEM_PRESSED = [r, c]

    @QtCore.pyqtSlot(str, str, str)
    def UpdateTableForIRI(self, iri_inp, nodes_inp, diag_name):
        disconnect(self.table.cellChanged, self.cell_changed)
        self.FillTableWithIRIPrefixNodesDictionaryKeysAndValues()
        connect(self.table.cellChanged, self.cell_changed)

    def add_remove_or_modify_task(self):
        if self.ITEM_CHANGED is None or self.ITEM_PRESSED is None:
            return

        if self.ITEM_CHANGED[0] == self.ITEM_PRESSED[0] and self.ITEM_CHANGED[1] == self.ITEM_PRESSED[1]:
            row = self.ITEM_CHANGED[0]
            column = self.ITEM_CHANGED[1]

            if column == 0:
                # add/remove/modify IRI
                if self.old_text == '' and self.new_text != '' or \
                        self.old_text != '' and self.new_text != '' and row == self.table.rowCount() - 1:
                    IRI_valid = self.project.check_validity_of_IRI(self.new_text)

                    if IRI_valid is False:
                        self.session.statusBar().showMessage('Invalid IRI.', 15000)
                        self.table.item(row, column).setText(self.old_text)
                    else:
                        # Add IRI
                        prefix_inp = self.table.item(row, 1).text().strip()

                        if prefix_inp == '':
                            if self.new_text in self.project.IRI_prefixes_nodes_dict.keys():
                                # generate new prefix and add it to the widget
                                new_generated_prefix = self.project.generate_new_prefix(
                                    self.project.IRI_prefixes_nodes_dict)
                                self.process_entry_from_textboxes_for_button_add_or_remove(self.new_text,
                                                                                           new_generated_prefix, 'add')
                            else:
                                self.process_entry_from_textboxes_for_button_add_or_remove(self.new_text, None, 'add',
                                                                                           display_in_widget=True)
                        else:
                            self.process_entry_from_textboxes_for_button_add_or_remove(self.new_text, prefix_inp, 'add',
                                                                                       display_in_widget=True)

                elif self.old_text != '' and self.new_text != '':
                    IRI_valid = self.project.check_validity_of_IRI(self.new_text)

                    if IRI_valid is False:
                        self.session.statusBar().showMessage('Invalid IRI.', 15000)
                        self.table.item(row, column).setText(self.old_text)
                    else:
                        # Modify IRI
                        if row == self.table.rowCount() - 1:
                            pass
                        else:
                            self.process_entry_from_textboxes_for_task_modify(self.old_text, self.new_text, None, None)

                elif self.old_text != '' and self.new_text == '':
                    # Remove IRI
                    if row == self.table.rowCount() - 1:
                        pass
                    else:
                        prefix_inp = self.table.item(row, 1).text().strip()
                        if prefix_inp == '':
                            if 'display_in_widget' in self.project.IRI_prefixes_nodes_dict[self.old_text][2]:
                                self.process_entry_from_textboxes_for_button_add_or_remove(self.old_text, None,
                                                                                           'remove',
                                                                                           display_in_widget=True)
                            else:
                                self.process_entry_from_textboxes_for_button_add_or_remove(self.old_text, None,
                                                                                           'remove')
                        else:
                            if len(self.project.IRI_prefixes_nodes_dict[self.old_text][0]) == 1:
                                self.process_entry_from_textboxes_for_button_add_or_remove(self.old_text, None,
                                                                                           'remove',
                                                                                           display_in_widget=True)
                            elif len(self.project.IRI_prefixes_nodes_dict[self.old_text][0]) > 1:
                                self.process_entry_from_textboxes_for_button_add_or_remove(self.old_text, prefix_inp,
                                                                                           'remove',
                                                                                           display_in_widget=True)
            else:
                # add/remove/modify prefixes
                iri_row = self.ITEM_CHANGED[0]
                iri_column = 0
                iri_inp = self.table.item(iri_row, iri_column).text().strip()
                flag = False

                for c in self.new_text:
                    if c == '':
                        pass
                    elif not c.isalnum():
                        flag = True
                        break
                    else:
                        pass

                if flag is True:
                    self.session.statusBar().showMessage('Spaces and special characters are not allowed in a prefix.',
                                                         15000)
                    self.table.item(row, column).setText(self.old_text)
                else:
                    if self.old_text == '' and self.new_text != '':
                        # Add Prefixes
                        if iri_inp == '':
                            pass
                        else:
                            self.process_entry_from_textboxes_for_button_add_or_remove(iri_inp, self.new_text, 'add',
                                                                                       display_in_widget=True)

                    elif self.old_text != '' and self.new_text != '':
                        # Modify Prefixes
                        if row == self.table.rowCount() - 1:
                            pass
                        else:
                            prefixes_old = self.project.IRI_prefixes_nodes_dict[iri_inp][0]
                            self.process_entry_from_textboxes_for_task_modify(None, None, self.old_text, self.new_text,
                                                                              prefixes_old=prefixes_old)

                    elif self.old_text != '' and self.new_text == '':
                        # Remove Prefixes
                        if row == self.table.rowCount() - 1:
                            pass
                        else:
                            self.process_entry_from_textboxes_for_button_add_or_remove(iri_inp, self.old_text, 'remove',
                                                                                       display_in_widget=True)

        self.old_text = None
        self.new_text = None
        self.ITEM_CHANGED = None
        self.ITEM_EDITED = None

    def append_row_and_column_to_table(self, iri, prefix, editable, brush, checkbox_value):
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

        if checkbox_value != 0:
            checkbox = QtWidgets.QRadioButton()

            if checkbox_value == 0:
                checkbox.setEnabled(False)
            elif checkbox_value == 1:
                connect(checkbox.toggled, self.set_project_IRI)
            elif checkbox_value == 2:
                checkbox.setChecked(True)
                connect(checkbox.toggled, self.set_project_IRI)
            else:
                pass

            checkbox.setObjectName(str(self.table.rowCount() - 1))
        else:
            null_item = QtWidgets.QTableWidgetItem()
            null_item.setFlags(QtCore.Qt.NoItemFlags)

        self.table.setItem(self.table.rowCount() - 1, 0, item_iri)
        self.table.setItem(self.table.rowCount() - 1, 1, item_prefix)
        if checkbox_value != 0:
            self.table.setCellWidget(self.table.rowCount() - 1, 2, checkbox)
        else:
            self.table.setItem(self.table.rowCount() - 1, 2, null_item)

        self.table.setRowCount(self.table.rowCount() + 1)

    def FillTableWithIRIPrefixNodesDictionaryKeysAndValues(self):
        # if (iri_to_update is None) and (nodes_to_update is None):
        # print('>>>  FillTableWithIRIPrefixNodesDictionaryKeysAndValues')
        # first delete all entries from the dictionary id present
        # add standard IRIs
        # add key value pairs from dict

        for r in range(0, self.table.rowCount() + 1):
            iri_item_to_el = self.table.item(r, 0)
            del iri_item_to_el
            prefix_item_to_del = self.table.item(r, 1)
            del prefix_item_to_del
            cw = self.table.cellWidget(r, 2)
            if cw is not None:
                disconnect(cw.toggled, self.set_project_IRI)
                self.table.removeCellWidget(r, 2)
                cw.destroy()

        self.table.clear()
        self.table.setRowCount(1)
        self.table.setColumnCount(3)

        header_iri = QtWidgets.QTableWidgetItem()
        header_iri.setText('IRI')
        header_iri.setFont(Font('Roboto', 15, bold=True))
        header_iri.setTextAlignment(QtCore.Qt.AlignCenter)
        # header_iri.setBackground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        # header_iri.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_iri.setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_iri.setForeground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        header_iri.setFlags(QtCore.Qt.NoItemFlags)

        header_prefix = QtWidgets.QTableWidgetItem()
        header_prefix.setText('PREFIX')
        header_prefix.setFont(Font('Roboto', 15, bold=True))
        header_prefix.setTextAlignment(QtCore.Qt.AlignCenter)
        # header_prefix.setBackground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        # header_prefix.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_prefix.setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_prefix.setForeground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        header_prefix.setFlags(QtCore.Qt.NoItemFlags)

        header_project_prefix = QtWidgets.QTableWidgetItem()
        header_project_prefix.setText('DEFAULT')
        header_project_prefix.setFont(Font('Roboto', 15, bold=True))
        header_project_prefix.setTextAlignment(QtCore.Qt.AlignCenter)
        # header_project_prefix.setBackground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        # header_project_prefix.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_project_prefix.setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_project_prefix.setForeground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        header_project_prefix.setFlags(QtCore.Qt.NoItemFlags)

        self.table.setItem(self.table.rowCount() - 1, 0, header_iri)
        self.table.setItem(self.table.rowCount() - 1, 1, header_prefix)
        self.table.setItem(self.table.rowCount() - 1, 2, header_project_prefix)
        self.table.setRowCount(self.table.rowCount() + 1)

        for iri in sorted(self.project.IRI_prefixes_nodes_dict.keys()):
            if Namespace.forValue(iri):
                standard_prefixes = self.project.IRI_prefixes_nodes_dict[iri][0]
                standard_prefix = standard_prefixes[0]
                self.append_row_and_column_to_table(iri, standard_prefix, False, None, 0)
            else:
                prefixes = self.project.IRI_prefixes_nodes_dict[iri][0]

                if len(prefixes) > 0:
                    for p in prefixes:
                        if iri == self.project.ontologyIRIString:
                            self.append_row_and_column_to_table(iri, p, True, None, 2)
                        else:
                            self.append_row_and_column_to_table(iri, p, True, None, 1)
                else:
                    if 'display_in_widget' in self.project.IRI_prefixes_nodes_dict[iri][2]:
                        if iri == self.project.ontologyIRIString:
                            self.append_row_and_column_to_table(iri, '', True, None, 2)
                        else:
                            self.append_row_and_column_to_table(iri, '', True, None, 1)

        self.append_row_and_column_to_table('', '', True, None, 0)
        self.table.setRowCount(self.table.rowCount() - 1)
        self.redraw()

    def process_entry_from_textboxes_for_button_add_or_remove(self, iri_inp, prefix_inp, inp_task, **kwargs):
        display_in_widget = kwargs.get('display_in_widget', False)

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

        if prefix_inp is not None:
            if inp_task == 'remove':
                # self.project.removeIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, prefix)
                self.project.addORremoveIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri_inp, prefix_inp,
                                                       'remove_entry', display_in_widget=display_in_widget)
                if (False in self.ENTRY_REMOVE_OK_var) or (True in self.ENTRY_IGNORE_var):
                    LOGGER.error('transaction was not executed correctly; problem with a prefix/IRI')
                    return
                else:
                    process = True
            elif inp_task == 'add':
                # self.project.addIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, prefix)
                self.project.addORremoveIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri_inp, prefix_inp,
                                                       'add_entry', display_in_widget=display_in_widget)
                if (False in self.ENTRY_ADD_OK_var) or (True in self.ENTRY_IGNORE_var):
                    LOGGER.error('transaction was not executed correctly; problem with a prefix/IRI')
                    return
                else:
                    process = True
            else:
                pass
        else:
            if inp_task == 'remove':
                # self.project.removeIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri, None)
                self.project.addORremoveIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri_inp, None,
                                                       'remove_entry', display_in_widget=display_in_widget)
                if (False in self.ENTRY_REMOVE_OK_var) or (True in self.ENTRY_IGNORE_var):
                    LOGGER.error('transaction was not executed correctly; problem with IRI')
                    return
                else:
                    process = True
            elif inp_task == 'add':
                self.project.addORremoveIRIPrefixEntry(Duplicate_IRI_prefixes_nodes_dict_1, iri_inp, None,
                                                       'add_entry', display_in_widget=display_in_widget)
                if False in self.ENTRY_ADD_OK_var or True in self.ENTRY_IGNORE_var:
                    LOGGER.error('transaction was not executed correctly; problem with IRI')
                    return
                else:
                    process = True

        if process is True:
            commands = [CommandProjectDisconnectSpecificSignals(self.project, regenerate_label_of_nodes_for_iri=False),
                        CommandProjetSetIRIPrefixesNodesDict(self.project,
                                                             Duplicate_IRI_prefixes_nodes_dict_2,
                                                             Duplicate_IRI_prefixes_nodes_dict_1, [iri_inp], None),
                        CommandProjectConnectSpecificSignals(self.project, regenerate_label_of_nodes_for_iri=False)]

            if any(commands):
                self.session.undostack.beginMacro('add/remove IRI')
                for command in commands:
                    if command:
                        self.session.undostack.push(command)
                self.session.undostack.endMacro()

        self.ENTRY_ADD_OK_var = set()
        self.ENTRY_REMOVE_OK_var = set()
        self.ENTRY_IGNORE_var = set()

    def process_entry_from_textboxes_for_task_modify(self, iri_old, iri_new, prefix_old, prefix_new, prefixes_old=None):
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
            if iri_old == iri_new:
                self.session.statusBar().showMessage(
                    'IRIs in selected cell and input box are the same. Nothing to change',
                    10000)
                return

            self.project.modifyIRIPrefixesEntry(iri_old, None, iri_new, None, Duplicate_IRI_prefixes_nodes_dict_1)
            iris_to_be_updated.append(iri_old)
            iris_to_be_updated.append(iri_new)

            if False in self.ENTRY_MODIFY_OK_var or True in self.ENTRY_IGNORE_var:
                LOGGER.error('transaction was not executed correctly; problem with a prefix/IRI')
                return
            else:
                process = True

        if prefix_old is not None and prefix_new is not None:
            prefixes_old_list = []
            prefixes_old_list.extend(prefixes_old)
            ind = prefixes_old_list.index(prefix_old)
            prefixes_old_list.remove(prefix_old)

            prefixes_new_list = []
            prefixes_new_list.extend(prefixes_old_list)
            prefixes_new_list.insert(ind, prefix_new)

            # case2     prefix->prefix'          if prefix==prefix' no need for a transaction
            if prefix_old == prefix_new:
                self.session.statusBar().showMessage(
                    'prefix(es) in selected cell and input box are the same. Nothing to change', 10000)
                return

            self.project.modifyIRIPrefixesEntry(None, prefixes_old, None, prefixes_new_list,
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
            commands = [CommandProjectDisconnectSpecificSignals(self.project, regenerate_label_of_nodes_for_iri=False),
                        CommandProjetSetIRIPrefixesNodesDict(self.project,
                                                             Duplicate_IRI_prefixes_nodes_dict_2,
                                                             Duplicate_IRI_prefixes_nodes_dict_1,
                                                             iris_to_be_updated, None),
                        CommandProjectConnectSpecificSignals(self.project, regenerate_label_of_nodes_for_iri=False)]

            if any(commands):
                self.session.undostack.beginMacro('modify IRI')
                for command in commands:
                    if command:
                        self.session.undostack.push(command)
                self.session.undostack.endMacro()

        self.ENTRY_MODIFY_OK_var = set()
        self.ENTRY_IGNORE_var = set()

    @QtCore.pyqtSlot(bool)
    def set_project_IRI(self, toggled):
        if toggled:
            row = int(self.sender().objectName())
            new_project_iri = self.table.item(row, 0).text()

            if new_project_iri != self.project.ontologyIRIString:
                Duplicate_dict_1 = self.project.copy_IRI_prefixes_nodes_dictionaries(
                    self.project.IRI_prefixes_nodes_dict, dict())
                Duplicate_dict_2 = self.project.copy_IRI_prefixes_nodes_dictionaries(
                    self.project.IRI_prefixes_nodes_dict, dict())

                Duplicate_dict_1[self.project.ontologyIRIString][2].remove('Project_IRI')
                Duplicate_dict_1[new_project_iri][2].add('Project_IRI')

                commands = [CommandProjectDisconnectSpecificSignals(self.project),
                            CommandProjetSetIRIPrefixesNodesDict(self.project, Duplicate_dict_2, Duplicate_dict_1, [],
                                                                 []),
                            CommandProjectConnectSpecificSignals(self.project)]

                self.session.undostack.beginMacro('chenge ontology IRI')
                for command in commands:
                    if command:
                        self.session.undostack.push(command)
                self.session.undostack.endMacro()

    def redraw(self):
        """
        Redraw the content of the widget.
        """
        self.versionField.setValue(self.project.version)
        self.versionField.home(True)
        self.versionField.clearFocus()
        self.versionField.deselect()
        self.table.setColumnCount(3)

        width = self.width()
        height = self.height()

        self.prefixmanagerheader.setFixedWidth(width - 40)
        self.prefixmanagerheader.setAlignment(QtCore.Qt.AlignCenter)

        for r in range(0, self.table.rowCount()):
            self.table.setRowHeight(r, 25)

        total_height_of_all_rows = 0
        for r in range(0, self.table.rowCount() + 1):
            total_height_of_all_rows = total_height_of_all_rows + self.table.rowHeight(r)

        self.table.setFixedWidth(width - 40)
        self.table.setMinimumHeight(min(total_height_of_all_rows + 5 - 20 - 35, height - 40 - 25 - 20 - 35))

        if total_height_of_all_rows >= (self.table.height()):
            scrollbar_width = 15
        else:
            scrollbar_width = 0

        self.table.setColumnWidth(0, int(6 * (self.table.width() - scrollbar_width) / 10))
        self.table.setColumnWidth(1, int(2 * (self.table.width() - scrollbar_width) / 10))
        self.table.setColumnWidth(2, int(2 * (self.table.width() - scrollbar_width) / 10))
        # self.table.resizeRowToContents(r)
        # self.setMaximumHeight(total_height_of_all_rows+3+40+60)

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


class Key(QtWidgets.QLabel):
    """
    This class implements the key of an info field.
    """

    def __init__(self, *args):
        """
        Initialize the key.
        """
        super().__init__(*args)
        self.setFixedSize(88, 25)


class String(StringField):
    """
    This class implements the string value of an info field.
    """

    def __init__(self, *args):
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(25)
        self.setFixedWidth(80)
