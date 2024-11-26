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

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from eddy.core.commands.iri import (
    CommandCommmonSubstringIRIsRefactor,
    CommandIRIRemoveAnnotationAssertion, CommandIRIAddAnnotationAssertion,
)
from eddy.core.commands.project import (
    CommandProjectAddAnnotationProperty,
    CommandProjectAddPrefix,
    CommandProjectModifyPrefixResolution,
    CommandProjectModifyNamespacePrefix,
    CommandProjectRemoveAnnotationProperty,
    CommandProjectRemoveOntologyImport,
    CommandProjectRemovePrefix,
    CommandProjectSetLabelFromSimpleNameOrInputAndLanguage,
    CommandProjectSetOntologyIRIAndVersion,
)
from eddy.core.common import HasWidgetSystem
from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.system import File
from eddy.core.exporters.metadata import (
    AnnotationsOverridingDialog,
    CsvTemplateExporter,
    XlsxTemplateExporter,
)
from eddy.core.functions.fsystem import fexists
from eddy.core.functions.misc import first
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect
from eddy.core.ndc import (
    getAgentsFromStore,
    getContactPointsFromStore,
    getProjectsFromStore,
    getDataFromEndpoint,
    getDistributionsFromStore, addIriAnnotationsToProject,
)
from eddy.core.output import getLogger
from eddy.core.owl import (
    AnnotationAssertion,
    IllegalPrefixError,
    IllegalNamespaceError,
    ImportedOntology, IRI, OWL2Datatype,
)
from eddy.ui.annotation import AnnotationAssertionBuilderDialog
from eddy.ui.checkable_combobox import CheckableComboBox
from eddy.ui.fields import (
    StringField,
    CheckBox,
    ComboBox,
)
from eddy.ui.file import FileDialog
from eddy.ui.ndc.agent import AgentBuilderDialog
from eddy.ui.ndc.contact import ContactBuilderDialog
from eddy.ui.ndc.distribution import DistributionBuilderDialog
from eddy.ui.ndc.project import ProjectBuilderDialog

LOGGER = getLogger()


class OntologyManagerDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    This class implements the 'Ontology Manager' dialog.
    """

    noPrefixString = ''
    emptyString = ''

    def __init__(self, session):
        """
        Initialize the Ontology Manager dialog.
        :type session: Session
        """
        super().__init__(session)

        settings = QtCore.QSettings()
        self.addingNewPrefix = False
        self.prefixIndexMap = {}
        self.project = session.project
        self.hiddenRows = []
        #############################################
        # GENERAL TAB
        #################################

        # ONTOLOGY PROPERTIES GROUP
        iriLabel = QtWidgets.QLabel(self, objectName='ontology_iri_label')
        iriLabel.setText('Ontology IRI')
        self.addWidget(iriLabel)

        iriField = StringField(self, objectName='ontology_iri_field')
        connect(iriField.textEdited, self.onOntologyIriOrVersionEdited)
        iriField.setPlaceholderText('e.g. http://example.com/ontologies/myontology/')
        self.addWidget(iriField)

        versionLabel = QtWidgets.QLabel(self, objectName='ontology_version_label')
        versionLabel.setText('Ontology Version IRI')
        self.addWidget(versionLabel)

        versionField = StringField(self, objectName='ontology_version_field')
        connect(versionField.textEdited,self.onOntologyIriOrVersionEdited)
        versionField.setPlaceholderText('e.g. http://example.com/ontologies/myontology/1.0')
        self.addWidget(versionField)

        saveBtn = QtWidgets.QPushButton('Save', objectName='save_ont_iri_version_button')
        saveBtn.setEnabled(False)
        connect(saveBtn.clicked, self.saveOntologyIRIAndVersion)
        self.addWidget(saveBtn)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('ontology_iri_label'), self.widget('ontology_iri_field'))
        formlayout.addRow(self.widget('ontology_version_label'), self.widget('ontology_version_field'))

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('save_ont_iri_version_button'))

        outerFormLayout = QtWidgets.QFormLayout()
        outerFormLayout.addRow(formlayout)
        outerFormLayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Ontology IRI', self, objectName='ontology_iri_widget')
        groupbox.setLayout(outerFormLayout)
        self.addWidget(groupbox)

        # ONTOLOGY IMPORTS GROUP
        table = QtWidgets.QTableWidget(0, 3, self, objectName='ontology_imports_table_widget')
        table.setHorizontalHeaderLabels(['Ontology IRI', 'Version IRI', 'Location'])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionsClickable(False)
        table.horizontalHeader().setMinimumSectionSize(130)
        table.horizontalHeader().setSectionsClickable(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setSectionsClickable(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        connect(table.cellClicked, self.onImportCellClicked)
        self.addWidget(table)

        addBtn = QtWidgets.QPushButton('Add', objectName='ontology_imports_add_button')
        delBtn = QtWidgets.QPushButton('Remove', objectName='ontology_imports_delete_button')
        delBtn.setEnabled(False)
        reloadBtn = QtWidgets.QPushButton('Reload', objectName='ontology_imports_reload_button')
        reloadBtn.setEnabled(False)
        connect(addBtn.clicked, self.addOntologyImport)
        connect(delBtn.clicked, self.removeOntologyImport)
        connect(reloadBtn.clicked, self.reloadOntologyImport)
        self.addWidget(addBtn)
        self.addWidget(delBtn)
        self.addWidget(reloadBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('ontology_imports_add_button'))
        boxlayout.addWidget(self.widget('ontology_imports_delete_button'))
        boxlayout.addWidget(self.widget('ontology_imports_reload_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('ontology_imports_table_widget'))
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Imported Ontologies', self, objectName='ontology_imports_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        # ONTOLOGY ANNOTATIONS GROUP
        table = QtWidgets.QTableWidget(0, 2, self, objectName='annotations_table_widget')
        table.clear()
        table.setHorizontalHeaderLabels(['Property', 'Connected Resource'])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionsClickable(False)
        table.horizontalHeader().setMinimumSectionSize(170)
        table.horizontalHeader().setSectionsClickable(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setSectionsClickable(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        connect(table.cellClicked, self.onAnnotationCellClicked)
        self.addWidget(table)

        addBtn = QtWidgets.QPushButton('Add', objectName='ontology_annotations_add_button')
        delBtn = QtWidgets.QPushButton('Remove', objectName='ontology_annotations_delete_button')
        delBtn.setEnabled(False)
        editBtn = QtWidgets.QPushButton('Edit', objectName='ontology_annotations_edit_button')
        editBtn.setEnabled(False)
        connect(addBtn.clicked, self.addOntologyAnnotation)
        connect(delBtn.clicked, self.removeOntologyAnnotation)
        connect(editBtn.clicked, self.editOntologyAnnotation)
        self.addWidget(addBtn)
        self.addWidget(delBtn)
        self.addWidget(editBtn)


        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('ontology_annotations_add_button'))
        boxlayout.addWidget(self.widget('ontology_annotations_delete_button'))
        boxlayout.addWidget(self.widget('ontology_annotations_edit_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('annotations_table_widget'))
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Ontology Annotations', self, objectName='ontology_annotations_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        # GENERAL TAB LAYOUT CONFIGURATION
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('ontology_iri_widget'), 0, QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('ontology_imports_widget'), 0, QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('ontology_annotations_widget'), 0, QtCore.Qt.AlignTop)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('general_widget')
        self.addWidget(widget)

        #############################################
        # PREFIXES TAB
        #################################

        # PREFIXES GROUP
        table = QtWidgets.QTableWidget(1, 2, self, objectName='prefixes_table_widget')
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionsClickable(False)
        table.horizontalHeader().setMinimumSectionSize(100)
        table.horizontalHeader().setSectionsClickable(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setSectionsClickable(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.addWidget(table)

        delBtn = QtWidgets.QPushButton('Remove', objectName='prefixes_delete_button')
        #connect(addBtn.clicked, self.addPrefix)
        connect(delBtn.clicked, self.removePrefix)
        #self.addWidget(addBtn)
        self.addWidget(delBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        #boxlayout.addWidget(self.widget('prefixes_add_button'))
        boxlayout.addWidget(self.widget('prefixes_delete_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('prefixes_table_widget'))
        formlayout.addRow(boxlayout)

        definedPrefixesGroupbox = QtWidgets.QGroupBox('Defined Prefixes', self, objectName='defined_prefixes_group_widget')
        definedPrefixesGroupbox.setLayout(formlayout)
        self.addWidget(definedPrefixesGroupbox)

        prefixLabel = QtWidgets.QLabel(self, objectName='prefix_input_label')
        prefixLabel.setText('Prefix')
        self.addWidget(prefixLabel)

        prefixField = StringField(self, objectName='prefix_input_field')
        #prefixField.setPlaceholderText('e.g. http://example.com/ontologies/myontology/')
        self.addWidget(prefixField)

        nsLabel = QtWidgets.QLabel(self, objectName='ns_input_label')
        nsLabel.setText('Namespace')
        self.addWidget(nsLabel)

        nsField = StringField(self, objectName='ns_input_field')
        #nsField.setPlaceholderText('e.g. http://example.com/ontologies/myontology/1.0')
        self.addWidget(nsField)
        inputPrefixLayout = QtWidgets.QFormLayout()
        inputPrefixLayout.addRow(self.widget('prefix_input_label'), self.widget('prefix_input_field'))
        inputPrefixLayout.addRow(self.widget('ns_input_label'), self.widget('ns_input_field'))

        addBtn = QtWidgets.QPushButton('Add', objectName='prefixes_add_button')
        connect(addBtn.clicked, self.addPrefix)
        self.addWidget(addBtn)
        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('prefixes_add_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(inputPrefixLayout)
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Define new prefix', self, objectName='add_prefix_group_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        # PREFIXES TAB LAYOUT CONFIGURATION
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('defined_prefixes_group_widget'), 0, QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('add_prefix_group_widget'), 1, QtCore.Qt.AlignTop)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('prefixes_widget')
        self.addWidget(widget)

        #############################################
        # ANNOTATIONS TAB
        #################################

        # ANNOTATIONS GROUP
        table = QtWidgets.QTableWidget(0, 2, self, objectName='annotation_properties_table_widget')
        table.setHorizontalHeaderLabels(['IRI', 'Comment'])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionsClickable(False)
        table.horizontalHeader().setMinimumSectionSize(100)
        table.horizontalHeader().setSectionsClickable(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setSectionsClickable(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.addWidget(table)

        #addBtn = QtWidgets.QPushButton('Add', objectName='annotation_properties_add_button')
        delBtn = QtWidgets.QPushButton('Remove', objectName='annotation_properties_delete_button')
        #connect(addBtn.clicked, self.addAnnotationProperty)
        connect(delBtn.clicked, self.removeAnnotationProperty)
        #self.addWidget(addBtn)
        self.addWidget(delBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        #boxlayout.addWidget(self.widget('annotation_properties_add_button'))
        boxlayout.addWidget(self.widget('annotation_properties_delete_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('annotation_properties_table_widget'))
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Annotation Properties', self, objectName='annotation_properties_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        # ADDED

        comboBoxLabel = QtWidgets.QLabel(self, objectName='iri_prefix_combobox_label')
        comboBoxLabel.setText('Prefix')
        self.addWidget(comboBoxLabel)

        combobox = ComboBox(objectName='iri_prefix_switch')
        combobox.setEditable(False)
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        combobox.addItem(self.noPrefixString)
        # combobox.addItems([x+':' for x in self.project.getManagedPrefixes()])
        combobox.addItems([x + ':' + '  <' + y + '>' for x, y in self.project.prefixDictItems()])
        combobox.setCurrentText(self.noPrefixString)
        self.addWidget(combobox)

        inputLabel = QtWidgets.QLabel(self, objectName='input_field_label')
        inputLabel.setText('Input')
        self.addWidget(inputLabel)

        inputField = StringField(self, objectName='iri_input_field')
        # inputField.setFixedWidth(300)
        inputField.setValue('')
        self.addWidget(inputField)

        fullIriLabel = QtWidgets.QLabel(self, objectName='full_iri_label')
        fullIriLabel.setText('Full IRI')
        self.addWidget(fullIriLabel)
        fullIriField = StringField(self, objectName='full_iri_field')
        # fullIriField.setFixedWidth(300)
        fullIriField.setReadOnly(True)
        self.addWidget(fullIriField)

        addBtn = QtWidgets.QPushButton('Add', objectName='annotation_add_button')
        connect(addBtn.clicked, self.addAnnotationProperty)
        self.addWidget(addBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('annotation_add_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('iri_prefix_combobox_label'), self.widget('iri_prefix_switch'))
        formlayout.addRow(self.widget('input_field_label'), self.widget('iri_input_field'))
        formlayout.addRow(self.widget('full_iri_label'), self.widget('full_iri_field'))
        formlayout.addRow(boxlayout)

        groupbox = QtWidgets.QGroupBox('Define new annotation property', self, objectName='add_annotation_group_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        connect(self.widget('iri_prefix_switch').currentIndexChanged, self.onAnnotationPrefixChanged)
        connect(self.widget('iri_input_field').textChanged, self.onAnnotationInputChanged)

        # IMPORT/EXPORT TEMPLATE
        templateBtn = QtWidgets.QPushButton('Generate Template',
                                            objectName='annotation_create_template_button')
        connect(templateBtn.clicked, self.createTemplate)
        self.addWidget(templateBtn)

        importBtn = QtWidgets.QPushButton('Import from Template',
                                          objectName='annotation_import_template_button')
        connect(importBtn.clicked, self.importTemplate)
        self.addWidget(importBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('annotation_create_template_button'))
        boxlayout.addWidget(self.widget('annotation_import_template_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Import/Export Template', self,
                                       objectName='template_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        # ANNOTATIONS TAB LAYOUT CONFIGURATION

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('annotation_properties_widget'), 0, QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('add_annotation_group_widget'), 1, QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('template_widget'), 2, QtCore.Qt.AlignTop)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('annotations_widget')
        self.addWidget(widget)

        ###################################
        # ANNOTATION ASSERTIONS TAB
        ##################################

        # ANNOTATION ASSERTIONS GROUP

        searchbar = QtWidgets.QLineEdit(objectName='searchbar_annotations')
        searchbar.setPlaceholderText("Search...")
        connect(searchbar.textChanged, self.searchAnnotationTable)
        self.addWidget(searchbar)

        table = QtWidgets.QTableWidget(0, 6, self, objectName='annotation_assertions_table_widget')
        table.setHorizontalHeaderLabels([
            'IRI',
            'SimpleName',
            'AnnotationProperty',
            'Value',
            'Datatype',
            'Lang',
        ])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionsClickable(False)
        table.horizontalHeader().setMinimumSectionSize(120)
        table.horizontalHeader().setSectionsClickable(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setSectionsClickable(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        #table.setSelectionMode(QAbstractItemView.MultiSelection)
        connect(table.cellDoubleClicked, self.onAssertionCellDoubleClicked)
        self.addWidget(table)

        selectBtn = QtWidgets.QPushButton('Select All', objectName = 'annotation_assertions_selectall_button')
        connect(selectBtn.clicked, self.selectAllAnnotationAssertion)
        self.addWidget(selectBtn)

        addBtn = QtWidgets.QPushButton('Add', objectName='annotation_assertions_add_button')
        editBtn = QtWidgets.QPushButton('Edit', objectName='annotation_assertions_edit_button')
        delBtn = QtWidgets.QPushButton('Remove', objectName='annotation_assertions_delete_button')
        connect(addBtn.clicked, self.addAnnotationAssertion)
        connect(editBtn.clicked, self.editAnnotationAssertion)
        connect(delBtn.clicked, self.removeAnnotationAssertion)
        self.addWidget(addBtn)
        self.addWidget(editBtn)
        self.addWidget(delBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('annotation_assertions_selectall_button'))
        boxlayout.addStretch(5)
        boxlayout.addWidget(self.widget('annotation_assertions_add_button'))
        boxlayout.addWidget(self.widget('annotation_assertions_edit_button'))
        boxlayout.addWidget(self.widget('annotation_assertions_delete_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('searchbar_annotations'))
        formlayout.addRow(self.widget('annotation_assertions_table_widget'))
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Annotation Assertions', self,
                                       objectName='annotation_assertions_widget')
        groupbox.setLayout(formlayout)
        groupbox.setMinimumSize(400, 650)
        self.addWidget(groupbox)

        # ANNOTATION ASSERTIONS TAB LAYOUT CONFIGURATION

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('annotation_assertions_widget'), 0, QtCore.Qt.AlignTop)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('assertions_widget')
        self.addWidget(widget)

        #############################################
        # Global IRI
        #################################

        checkBoxLabel = QtWidgets.QLabel(self, objectName='checkBox_label_simplename')
        checkBoxLabel.setText('Derive rdfs:label from simple name')
        self.addWidget(checkBoxLabel)
        checked = self.project.addLabelFromSimpleName
        checkBox = CheckBox('', self, enabled=True, checked=checked, clicked=self.onLabelSimpleNameCheckBoxClicked, objectName='label_simplename_checkbox')
        self.addWidget(checkBox)

        checkBoxLabel = QtWidgets.QLabel(self, objectName='checkBox_label_userinput')
        checkBoxLabel.setText('Derive rdfs:label from user input')
        self.addWidget(checkBoxLabel)
        checked = self.project.addLabelFromUserInput
        checkBox = CheckBox('', self, enabled=True, checked=checked, clicked=self.onLabelUserInputCheckBoxClicked,
                            objectName='label_userinput_checkbox')
        self.addWidget(checkBox)

        snakeCheckbox = CheckBox('convert snake_case to space separated values', self,
                                 checked=self.project.convertSnake,
                                 objectName='convert_snake')
        connect(snakeCheckbox.clicked, self.onCaseCheckBoxClicked)
        self.addWidget(snakeCheckbox)
        snakeCheckbox.setEnabled(checked)

        camelCheckbox = CheckBox('convert camelCase to space separated values', self,
                                 checked=self.project.convertCamel,
                                 objectName='convert_camel')
        connect(camelCheckbox.clicked, self.onCaseCheckBoxClicked)
        self.addWidget(camelCheckbox)
        camelCheckbox.setEnabled(checked)

        comboBoxLabel = QtWidgets.QLabel(self, objectName='lang_combobox_label')
        comboBoxLabel.setText('Default rdfs:label language')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='lang_switch')
        combobox.setEditable(False)
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(True)
        combobox.addItem(self.emptyString)
        combobox.addItems([x for x in self.project.getLanguages()])
        if self.project.defaultLanguage:
            combobox.setCurrentText(self.project.defaultLanguage)
        else:
            combobox.setCurrentText(self.emptyString)
        if self.widget('label_simplename_checkbox').isChecked() or self.widget('label_userinput_checkbox').isChecked():
            combobox.setStyleSheet("background:#FFFFFF")
            combobox.setEnabled(True)
        else:
            combobox.setStyleSheet("background:#808080")
            combobox.setEnabled(False)
        connect(combobox.currentIndexChanged, self.onLanguageSwitched)

        self.addWidget(combobox)
        iriLabelLayout = QtWidgets.QFormLayout()
        iriLabelLayout.addRow(self.widget('checkBox_label_simplename'), self.widget('label_simplename_checkbox'))
        iriLabelLayout.addRow(self.widget('checkBox_label_userinput'), self.widget('label_userinput_checkbox'))
        iriLabelLayout.addRow(self.widget('convert_snake'))
        iriLabelLayout.addRow(self.widget('convert_camel'))
        iriLabelLayout.addRow(self.widget('lang_combobox_label'), self.widget('lang_switch'))

        applyBtn = QtWidgets.QPushButton('Apply', objectName='iri_label_button')
        applyBtn.setEnabled(False)
        connect(applyBtn.clicked, self.doApplyIriLabel)
        self.addWidget(applyBtn)
        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('iri_label_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(iriLabelLayout)
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('IRI Definition', self, objectName='iri_definition_group_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        #REFACTOR
        preLabel = QtWidgets.QLabel(self, objectName='pre_input_label')
        preLabel.setText('Pre ')
        self.addWidget(preLabel)

        preField = StringField(self, objectName='pre_input_field')
        # prefixField.setPlaceholderText('e.g. http://example.com/ontologies/myontology/')
        self.addWidget(preField)

        postLabel = QtWidgets.QLabel(self, objectName='post_input_label')
        postLabel.setText('Post ')
        self.addWidget(postLabel)

        postField = StringField(self, objectName='post_input_field')
        # prefixField.setPlaceholderText('e.g. http://example.com/ontologies/myontology/')
        self.addWidget(postField)

        iriRefactorLayout = QtWidgets.QFormLayout()
        iriRefactorLayout.addRow(self.widget('pre_input_label'), self.widget('pre_input_field'))
        iriRefactorLayout.addRow(self.widget('post_input_label'), self.widget('post_input_field'))

        refactorBtn = QtWidgets.QPushButton('Refactor', objectName='iri_refactor_button')
        connect(refactorBtn.clicked, self.doIriRefactor)
        self.addWidget(refactorBtn)
        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('iri_refactor_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(iriRefactorLayout)
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('IRI Refactor', self, objectName='iri_refactor_group_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('iri_definition_group_widget'), 0, QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('iri_refactor_group_widget'), 1, QtCore.Qt.AlignTop)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('iri_widget')
        self.addWidget(widget)

        ###################################
        # NDC Metadata
        ###################################

        #ENDPOINT
        endpoint = QtWidgets.QLabel(self, objectName='endpoint_label')
        endpoint.setText('Endpoint')
        self.addWidget(endpoint)

        #linewidget = QtWidgets.QWidget()
        layout_h = QtWidgets.QHBoxLayout()

        endpointField = StringField(self, objectName='endpoint_field')
        endpointField.setText('https://schema.gov.it/sparql')
        #endpointField.setPlaceholderText('@it')
        self.addWidget(endpointField)

        connectBtn = QtWidgets.QPushButton(objectName='endpoint_connect_button')
        connectBtn.setIcon(QtGui.QIcon(':/icons/18/ic_treeview_branch_closed'))
        connect(connectBtn.clicked, self.doConnectEndpoint)
        self.addWidget(connectBtn)

        #refreshBtn = QtWidgets.QPushButton(objectName='endpoint_refresh_button')
        #refreshBtn.setIcon(QtGui.QIcon(':/icons/24/ic_refresh_black'))
        #self.addWidget(refreshBtn)

        layout_h.addWidget(endpointField)
        layout_h.addWidget(connectBtn)
        #layout_h.addWidget(refreshBtn)

        linelayout = QtWidgets.QFormLayout()
        linelayout.addRow(self.widget('endpoint_label'), layout_h)
        groupbox0 = QtWidgets.QGroupBox('Metadata Endpoint', self,
                                       objectName='ndc_metadata_endpoint')
        groupbox0.setLayout(linelayout)
        self.addWidget(groupbox0)

        #FORM

        ndcTitle = QtWidgets.QLabel(self, objectName='ndc_title_label')
        ndcTitle.setText('Title')
        self.addWidget(ndcTitle)

        ndcITtitleField = StringField(self, objectName='ndc_ITtitle_field')
        ndcITtitleField.setPlaceholderText('@it')
        self.addWidget(ndcITtitleField)

        ndcENtitleField = StringField(self, objectName='ndc_ENtitle_field')
        ndcENtitleField.setPlaceholderText('@en')
        self.addWidget(ndcENtitleField)

        ndcLabel = QtWidgets.QLabel(self, objectName='ndc_label_label')
        ndcLabel.setText('Label')
        self.addWidget(ndcLabel)

        ndcITLabelField = StringField(self, objectName='ndc_ITlabel_field')
        ndcITLabelField.setPlaceholderText('@it')
        self.addWidget(ndcITLabelField)

        noLabel = QtWidgets.QLabel(self, objectName='no_label')
        self.addWidget(noLabel)

        ndcENLabelField = StringField(self, objectName='ndc_ENlabel_field')
        ndcENLabelField.setPlaceholderText('@en')
        self.addWidget(ndcENLabelField)

        ndcComment = QtWidgets.QLabel(self, objectName='ndc_comment_label')
        ndcComment.setText('Comment')
        self.addWidget(ndcComment)

        ndcITCommentField = StringField(self, objectName='ndc_ITcomment_field')
        ndcITCommentField.setPlaceholderText('@it')
        self.addWidget(ndcITCommentField)

        ndcENCommentField = StringField(self, objectName='ndc_ENcomment_field')
        ndcENCommentField.setPlaceholderText('@en')
        self.addWidget(ndcENCommentField)

        ndcOfficialURI = QtWidgets.QLabel(self, objectName='ndc_officialURI_label')
        ndcOfficialURI.setText('Official URI')
        self.addWidget(ndcOfficialURI)

        ndcOfficialURIField = StringField(self, objectName='ndc_officialURI_field')
        self.addWidget(ndcOfficialURIField)

        ndcIdentifier = QtWidgets.QLabel(self, objectName='ndc_id_label')
        ndcIdentifier.setText('Identifier')
        self.addWidget(ndcIdentifier)

        ndcIdentifierField = StringField(self, objectName='ndc_id_field')
        self.addWidget(ndcIdentifierField)

        ndcRightsHolder = QtWidgets.QLabel(self, objectName='ndc_rightsHolder_label')
        ndcRightsHolder.setText('Rights Holder')
        self.addWidget(ndcRightsHolder)

        ndcRightsHolderField = CheckableComboBox(self, objectName='ndc_rightsHolder_field')
        self.addWidget(ndcRightsHolderField)

        addRightsHolderBtn = QtWidgets.QPushButton(objectName='add_rightsHolder_button')
        addRightsHolderBtn.setIcon(QtGui.QIcon(':/icons/24/ic_create_black'))
        addRightsHolderBtn.setFixedSize(QtCore.QSize(30, 20))
        connect(addRightsHolderBtn.clicked, self.doAddAgent)
        self.addWidget(addRightsHolderBtn)

        layout_rightsHolder = QtWidgets.QHBoxLayout()
        layout_rightsHolder.addWidget(ndcRightsHolderField)
        layout_rightsHolder.addWidget(addRightsHolderBtn)

        ndcCreationDate = QtWidgets.QLabel(self, objectName='ndc_creationDate_label')
        ndcCreationDate.setText('Creation Date')
        self.addWidget(ndcCreationDate)

        ndcCreationDateField = QtWidgets.QDateEdit(self, objectName='ndc_creationDate_field')
        self.addWidget(ndcCreationDateField)

        ndcLastModifiedDate = QtWidgets.QLabel(self, objectName='ndc_lastModifiedDate_label')
        ndcLastModifiedDate.setText('Last Modified Date')
        self.addWidget(ndcLastModifiedDate)

        ndcLastModifiedDateField = QtWidgets.QDateEdit(self, objectName='ndc_lastModifiedDate_field')
        self.addWidget(ndcLastModifiedDateField)

        ndcVersionInfo = QtWidgets.QLabel(self, objectName='ndc_versionInfo_label')
        ndcVersionInfo.setText('Version Info')
        self.addWidget(ndcVersionInfo)

        ndcVersionInfoITField = StringField(self, objectName='ndc_ITversionInfo_field')
        ndcVersionInfoITField.setPlaceholderText('@it')
        self.addWidget(ndcVersionInfoITField)

        ndcVersionInfoENField = StringField(self, objectName='ndc_ENversionInfo_field')
        ndcVersionInfoENField.setPlaceholderText('@en')
        self.addWidget(ndcVersionInfoENField)

        ndcAccrualPeriodicity = QtWidgets.QLabel(self, objectName='ndc_accrualPeriodicity_label')
        ndcAccrualPeriodicity.setText('Accrual Periodicity')
        self.addWidget(ndcAccrualPeriodicity)

        ndcAccrualPeriodicityField = QtWidgets.QComboBox(self, objectName='ndc_accrualPeriodicity_field')
        periodicities = ["", "http://publications.europa.eu/resource/authority/frequency/TRIDECENNIAL",
                         "http://publications.europa.eu/resource/authority/frequency/BIHOURLY",
                         "http://publications.europa.eu/resource/authority/frequency/TRIHOURLY",
                         "http://publications.europa.eu/resource/authority/frequency/OTHER",
                            "http://publications.europa.eu/resource/authority/frequency/WEEKLY",
                         "http://publications.europa.eu/resource/authority/frequency/NOT_PLANNED",
                         "http://publications.europa.eu/resource/authority/frequency/AS_NEEDED",
                         "http://publications.europa.eu/resource/authority/frequency/5MIN",
                         "http://publications.europa.eu/resource/authority/frequency/30MIN",
                         "http://publications.europa.eu/resource/authority/frequency/HOURLY",
                         "http://publications.europa.eu/resource/authority/frequency/QUADRENNIAL",
                         "http://publications.europa.eu/resource/authority/frequency/QUINQUENNIAL",
                         "http://publications.europa.eu/resource/authority/frequency/DECENNIAL",
                         "http://publications.europa.eu/resource/authority/frequency/1MIN",
"http://publications.europa.eu/resource/authority/frequency/15MIN",
"http://publications.europa.eu/resource/authority/frequency/WEEKLY_2",
"http://publications.europa.eu/resource/authority/frequency/WEEKLY_3",
"http://publications.europa.eu/resource/authority/frequency/12HRS",
"http://publications.europa.eu/resource/authority/frequency/UNKNOWN",
"http://publications.europa.eu/resource/authority/frequency/10MIN",
"http://publications.europa.eu/resource/authority/frequency/UPDATE_CONT",
"http://publications.europa.eu/resource/authority/frequency/QUARTERLY",
"http://publications.europa.eu/resource/authority/frequency/TRIENNIAL",
"http://publications.europa.eu/resource/authority/frequency/NEVER",
"http://publications.europa.eu/resource/authority/frequency/OP_DATPRO",
"http://publications.europa.eu/resource/authority/frequency/MONTHLY_2",
"http://publications.europa.eu/resource/authority/frequency/MONTHLY_3",
"http://publications.europa.eu/resource/authority/frequency/IRREG",
"http://publications.europa.eu/resource/authority/frequency/MONTHLY",
"http://publications.europa.eu/resource/authority/frequency/DAILY",
"http://publications.europa.eu/resource/authority/frequency/DAILY_2",
"http://publications.europa.eu/resource/authority/frequency/BIWEEKLY",
"http://publications.europa.eu/resource/authority/frequency/CONT",
"http://publications.europa.eu/resource/authority/frequency/BIENNIAL",
"http://publications.europa.eu/resource/authority/frequency/BIMONTHLY",
"http://publications.europa.eu/resource/authority/frequency/ANNUAL_2",
"http://publications.europa.eu/resource/authority/frequency/ANNUAL_3",
"http://publications.europa.eu/resource/authority/frequency/ANNUAL"]
        ndcAccrualPeriodicityField.addItems(periodicities)
        self.addWidget(ndcAccrualPeriodicityField)

        ndcContacts = QtWidgets.QLabel(self, objectName='ndc_contacts_label')
        ndcContacts.setText('Contact Point')
        self.addWidget(ndcContacts)

        ndcContactsField = CheckableComboBox(self, objectName='ndc_contacts_field')
        self.addWidget(ndcContactsField)

        addContactBtn = QtWidgets.QPushButton(objectName='add_contact_button')
        addContactBtn.setIcon(QtGui.QIcon(':/icons/24/ic_create_black'))
        addContactBtn.setFixedSize(QtCore.QSize(30, 20))
        connect(addContactBtn.clicked, self.doAddContact)
        self.addWidget(addContactBtn)

        layout_contact = QtWidgets.QHBoxLayout()
        layout_contact.addWidget(ndcContactsField)
        layout_contact.addWidget(addContactBtn)

        ndcPublisher = QtWidgets.QLabel(self, objectName='ndc_publisher_label')
        ndcPublisher.setText('Publisher')
        self.addWidget(ndcPublisher)

        ndcPublisherField = CheckableComboBox(self, objectName='ndc_publisher_field')
        self.addWidget(ndcPublisherField)

        addPublisherBtn = QtWidgets.QPushButton(objectName='add_publisher_button')
        addPublisherBtn.setIcon(QtGui.QIcon(':/icons/24/ic_create_black'))
        addPublisherBtn.setFixedSize(QtCore.QSize(30, 20))
        connect(addPublisherBtn.clicked, self.doAddAgent)
        self.addWidget(addPublisherBtn)

        layout_publisher = QtWidgets.QHBoxLayout()
        layout_publisher.addWidget(ndcPublisherField)
        layout_publisher.addWidget(addPublisherBtn)

        ndcCreator = QtWidgets.QLabel(self, objectName='ndc_creator_label')
        ndcCreator.setText('Creator')
        self.addWidget(ndcCreator)

        ndcCreatorField = CheckableComboBox(self, objectName='ndc_creator_field')
        self.addWidget(ndcCreatorField)

        addCreatorBtn = QtWidgets.QPushButton(objectName='add_creator_button')
        addCreatorBtn.setIcon(QtGui.QIcon(':/icons/24/ic_create_black'))
        addCreatorBtn.setFixedSize(QtCore.QSize(30, 20))
        connect(addCreatorBtn.clicked, self.doAddAgent)
        self.addWidget(addCreatorBtn)

        layout_creator = QtWidgets.QHBoxLayout()
        layout_creator.addWidget(ndcCreatorField)
        layout_creator.addWidget(addCreatorBtn)

        ndcLanguages = QtWidgets.QLabel(self, objectName='ndc_languages_label')
        ndcLanguages.setText('Languages')
        self.addWidget(ndcLanguages)

        ndcLanguagesField = CheckableComboBox(self, objectName='ndc_languages_field')
        languages = ["http://publications.europa.eu/resource/authority/language/ITA","http://publications.europa.eu/resource/authority/language/ENG"]
        ndcLanguagesField.addItems(languages)
        self.addWidget(ndcLanguagesField)

        ndcMainClasses = QtWidgets.QLabel(self, objectName='ndc_mainClasses_label')
        ndcMainClasses.setText('Key Classes')
        self.addWidget(ndcMainClasses)

        ndcMainClassesField = CheckableComboBox(self, objectName='ndc_mainClasses_field')
        classes = []
        for diagram in self.project.diagrams():
            for node in self.project.iriOccurrences(diagram=diagram):
                if node.type() == Item.ConceptNode and str(node.iri) not in classes:
                    classes.append(str(node.iri))
        ndcMainClassesField.addItems(classes)
        self.addWidget(ndcMainClassesField)

        ndcPrefix = QtWidgets.QLabel(self, objectName='ndc_prefix_label')
        ndcPrefix.setText('Prefix')
        self.addWidget(ndcPrefix)

        ndcPrefixField = StringField(self, objectName='ndc_prefix_field')
        if self.project.ontologyPrefix is not None:
            prefix = str(self.project.ontologyPrefix)
            ndcPrefixField.setValue(prefix)
        self.addWidget(ndcPrefixField)

        ndcProjects = QtWidgets.QLabel(self, objectName='ndc_projects_label')
        ndcProjects.setText('Projects')
        self.addWidget(ndcProjects)

        ndcProjectsField = CheckableComboBox(self, objectName='ndc_projects_field')
        self.addWidget(ndcProjectsField)

        addProjectBtn = QtWidgets.QPushButton(objectName='add_project_button')
        addProjectBtn.setIcon(QtGui.QIcon(':/icons/24/ic_create_black'))
        addProjectBtn.setFixedSize(QtCore.QSize(30, 20))
        connect(addProjectBtn.clicked, self.doAddProject)
        self.addWidget(addProjectBtn)

        layout_projects = QtWidgets.QHBoxLayout()
        layout_projects.addWidget(ndcProjectsField)
        layout_projects.addWidget(addProjectBtn)

        ndcDistributions = QtWidgets.QLabel(self, objectName='ndc_distributions_label')
        ndcDistributions.setText('Distributions')
        self.addWidget(ndcDistributions)

        ndcDistributionsField = CheckableComboBox(self, objectName='ndc_distributions_field')
        self.addWidget(ndcDistributionsField)

        addDistributionBtn = QtWidgets.QPushButton(objectName='add_distribution_button')
        addDistributionBtn.setIcon(QtGui.QIcon(':/icons/24/ic_create_black'))
        addDistributionBtn.setFixedSize(QtCore.QSize(30, 20))
        connect(addDistributionBtn.clicked, self.doAddDistribution)
        self.addWidget(addDistributionBtn)

        layout_distributions = QtWidgets.QHBoxLayout()
        layout_distributions.addWidget(ndcDistributionsField)
        layout_distributions.addWidget(addDistributionBtn)

        NDCLayout = QtWidgets.QFormLayout()
        NDCLayout.addRow(self.widget('ndc_title_label'), self.widget('ndc_ITtitle_field'))
        NDCLayout.addRow(self.widget('no_label'), self.widget('ndc_ENtitle_field'))
        NDCLayout.addRow(self.widget('ndc_label_label'), self.widget('ndc_ITlabel_field'))
        NDCLayout.addRow(self.widget('no_label'), self.widget('ndc_ENlabel_field'))
        NDCLayout.addRow(self.widget('ndc_comment_label'), self.widget('ndc_ITcomment_field'))
        NDCLayout.addRow(self.widget('no_label'), self.widget('ndc_ENcomment_field'))
        NDCLayout.addRow(self.widget('ndc_officialURI_label'), self.widget('ndc_officialURI_field'))
        NDCLayout.addRow(self.widget('ndc_id_label'), self.widget('ndc_id_field'))
        NDCLayout.addRow(self.widget('ndc_rightsHolder_label'), layout_rightsHolder)
        NDCLayout.addRow(self.widget('ndc_creationDate_label'), self.widget('ndc_creationDate_field'))
        NDCLayout.addRow(self.widget('ndc_lastModifiedDate_label'), self.widget('ndc_lastModifiedDate_field'))
        NDCLayout.addRow(self.widget('ndc_versionInfo_label'), self.widget('ndc_ITversionInfo_field'))
        NDCLayout.addRow(self.widget('no_label'), self.widget('ndc_ENversionInfo_field'))
        NDCLayout.addRow(self.widget('ndc_accrualPeriodicity_label'), self.widget('ndc_accrualPeriodicity_field'))
        NDCLayout.addRow(self.widget('ndc_contacts_label'), layout_contact)
        NDCLayout.addRow(self.widget('ndc_publisher_label'), layout_publisher)
        NDCLayout.addRow(self.widget('ndc_creator_label'), layout_creator)
        NDCLayout.addRow(self.widget('ndc_languages_label'), self.widget('ndc_languages_field'))
        NDCLayout.addRow(self.widget('ndc_mainClasses_label'), self.widget('ndc_mainClasses_field'))
        NDCLayout.addRow(self.widget('ndc_prefix_label'), self.widget('ndc_prefix_field'))
        NDCLayout.addRow(self.widget('ndc_projects_label'), layout_projects)
        #NDCLayout.addRow(self.widget('ndc_groups_label'), self.widget('ndc_groups_field'))
        NDCLayout.addRow(self.widget('ndc_distributions_label'), layout_distributions)

        applyBtn = QtWidgets.QPushButton('Apply', objectName='ndc_apply_button')
        applyBtn.setEnabled(True)
        connect(applyBtn.clicked, self.doAddMetadata)
        self.addWidget(applyBtn)
        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('ndc_apply_button'))

        scroll = QtWidgets.QScrollArea()
        scrollWidget = QtWidgets.QWidget()
        scrollWidget.setLayout(NDCLayout)
        scroll.setWidget(scrollWidget)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(500)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(scroll)
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Add NDC Metadata', self,
                                       objectName='ndc_metadata_group_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        # NDC TAB LAYOUT CONFIGURATION
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('ndc_metadata_endpoint'), 0, QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('ndc_metadata_group_widget'), 1, QtCore.Qt.AlignTop)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('NDCmetadata_widget')
        self.addWidget(widget)

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self, objectName='confirmation_widget')
        confirmation.addButton(QtWidgets.QDialogButtonBox.Ok)
        confirmation.setContentsMargins(10, 0, 10, 10)
        self.addWidget(confirmation)

        #############################################
        # MAIN WIDGET
        #################################

        widget = QtWidgets.QTabWidget(self, objectName='main_widget')
        widget.addTab(self.widget('general_widget'), 'General')
        widget.addTab(self.widget('prefixes_widget'), 'Prefixes')
        widget.addTab(self.widget('annotations_widget'), 'Annotations')
        widget.addTab(self.widget('iri_widget'), 'Global IRIs')
        widget.addTab(self.widget('assertions_widget'), 'Annotation Assertions')
        widget.addTab(self.widget('NDCmetadata_widget'), 'NDC Metadata')
        self.addWidget(widget)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(800, 800)
        self.restoreGeometry(settings.value(
            'manager/geometry',
            QtCore.QByteArray(),
            QtCore.QByteArray),
        )
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Ontology Manager')
        self.redraw()

        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

        table = self.widget('prefixes_table_widget')
        connect(table.cellChanged, self.managePrefixTableEntryModification)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the main session (alias for PreferencesDialog.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def accept(self) -> None:
        """
        Executed when the dialog is accepted.
        """
        settings = QtCore.QSettings()
        settings.setValue('manager/geometry', self.saveGeometry())
        settings.sync()
        super().accept()

    @QtCore.pyqtSlot()
    def redraw(self):
        """
        Redraw the dialog components, reloading their contents.
        """
        #############################################
        # GENERAL TAB
        #################################

        iriField = self.widget('ontology_iri_field')
        if self.project.ontologyIRI:
            iriField.setText(str(self.project.ontologyIRI))

        versionField = self.widget('ontology_version_field')
        if self.project.version and self.project.version != 'NULL':
            versionField.setText(self.project.version)

        self.widget('save_ont_iri_version_button').setEnabled(False)
        table = self.widget('ontology_imports_table_widget')
        importedOntologies = self.project.importedOntologies
        table.clear()
        table.setRowCount(len(importedOntologies))
        table.setHorizontalHeaderLabels(['Ontology IRI', 'Version IRI', 'Document location'])
        rowcount = 0
        for impOnt in importedOntologies:
            ontIriItem = QtWidgets.QTableWidgetItem(str(impOnt.ontologyIRI))
            ontIriItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            ontIriItem.setData(QtCore.Qt.UserRole, impOnt)
            versionItem = QtWidgets.QTableWidgetItem(str(impOnt.versionIRI))
            versionItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            locationItem = QtWidgets.QTableWidgetItem(str(impOnt.docLocation))
            locationItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            if not impOnt.correctlyLoaded:
                versionItem.setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                ontIriItem.setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                locationItem.setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
            table.setItem(rowcount, 0, ontIriItem)
            table.setItem(rowcount, 1, QtWidgets.QTableWidgetItem(versionItem))
            table.setItem(rowcount, 2, QtWidgets.QTableWidgetItem(locationItem))
            rowcount += 1
        table.resizeColumnToContents(0)
        if table.selectedRanges():
            self.widget('ontology_imports_reload_button').setEnabled(True)
            self.widget('ontology_imports_delete_button').setEnabled(True)
        else:
            self.widget('ontology_imports_reload_button').setEnabled(False)
            self.widget('ontology_imports_delete_button').setEnabled(False)

        table = self.widget('annotations_table_widget')
        ontAnnAss=[]
        if self.project.ontologyIRI:
            ontAnnAss = self.project.ontologyIRI.annotationAssertions
        table.clear()
        table.setRowCount(len(ontAnnAss))
        table.setHorizontalHeaderLabels(['Property', 'Connected Resource'])
        rowcount = 0
        for assertion in ontAnnAss:
            propertyItem = QtWidgets.QTableWidgetItem(str(assertion.assertionProperty))
            propertyItem.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
            propertyItem.setData(QtCore.Qt.UserRole, assertion)
            table.setItem(rowcount, 0, propertyItem)
            valueItem = QtWidgets.QTableWidgetItem(str(assertion.getObjectResourceString(True)))
            valueItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            table.setItem(rowcount, 1, QtWidgets.QTableWidgetItem(valueItem))
            rowcount += 1
        table.resizeColumnToContents(0)
        selectedRanges = table.selectedRanges()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                reloadItem = table.item(row, 0)
                impOnt = reloadItem.data(QtCore.Qt.UserRole)
                if not impOnt.correctlyLoaded:
                    self.widget('ontology_imports_reload_button').setEnabled(True)
                    break

        #############################################
        # PREFIXES TAB
        #################################

        # Reload prefixes table contents
        prefixDictItems = self.project.prefixDictItems()
        table = self.widget('prefixes_table_widget')
        table.clear()
        table.setRowCount(len(prefixDictItems))
        table.setHorizontalHeaderLabels(['Prefix', 'Namespace'])

        rowcount = 0
        for prefix, namespace in prefixDictItems:
            table.setItem(rowcount, 0, QtWidgets.QTableWidgetItem(prefix))
            table.setItem(rowcount, 1, QtWidgets.QTableWidgetItem(namespace))
            rowcount += 1
        self.buildPrefixIndexMap()
        table.resizeColumnsToContents()

        #############################################
        # ANNOTATIONS TAB
        #################################

        annotationProperties = [str(e) for e in self.project.getAnnotationPropertyIRIs()]
        table = self.widget('annotation_properties_table_widget')
        table.clear()
        table.setHorizontalHeaderLabels(['IRI', 'Comment'])
        table.setRowCount(len(annotationProperties))
        annotationProperties.sort()
        rowcount = 0
        for annIRI in annotationProperties:
            propertyItem = QtWidgets.QTableWidgetItem(str(annIRI))
            propertyItem.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
            table.setItem(rowcount,0,propertyItem)
            rowcount += 1
        table.resizeColumnsToContents()

        ###########################################
        # ANNOTATION ASSERTIONS TAB
        ################################

        table = self.widget('annotation_assertions_table_widget')
        table.clearContents()
        for iri in self.project.iris:
            for assertion in iri.annotationAssertions:
                self._insertAssertionTableRow(assertion)
        table.resizeColumnsToContents()
        table.sortItems(0)

        #############################################
        # Global IRI
        #################################

        checked = self.project.addLabelFromSimpleName
        checkBoxSimpleName = self.widget('label_simplename_checkbox')
        checkBoxSimpleName.setChecked(checked)

        checked = self.project.addLabelFromUserInput
        checkBoxUserInput = self.widget('label_userinput_checkbox')
        checkBoxUserInput.setChecked(checked)

        combobox = self.widget('lang_switch')
        if self.project.defaultLanguage:
            combobox.setCurrentText(self.project.defaultLanguage)
        else:
            combobox.setCurrentText(self.emptyString)
        if checkBoxSimpleName.isChecked() or checkBoxUserInput.isChecked():
            self.widget('lang_switch').setStyleSheet("background:#FFFFFF")
            self.widget('lang_switch').setEnabled(True)
        else:
            self.widget('lang_switch').setStyleSheet("background:#808080")
            self.widget('lang_switch').setEnabled(False)

        # REFACTOR
        self.widget('iri_label_button').setEnabled(False)
        preField = self.widget('pre_input_field')
        postField = self.widget('post_input_field')

    #############################################
    # GENERAL TAB
    #################################

    @QtCore.pyqtSlot(str)
    def onOntologyIriOrVersionEdited(self, textValue):
        self.widget('save_ont_iri_version_button').setEnabled(True)

    @QtCore.pyqtSlot(bool)
    def saveOntologyIRIAndVersion(self, _):
        """
        Adds an ontology import to the current project.
        :type _: bool
        """
        try:
            oldIri = ''
            if self.project.ontologyIRI:
                oldIri = str(self.project.ontologyIRI)
            oldVersion = ''
            if self.project.version:
                oldVersion = self.project.version
            iriField = self.widget('ontology_iri_field')
            ontIriString = iriField.value()
            versionField = self.widget('ontology_version_field')
            version = versionField.value()
            self.project.isValidIdentifier(ontIriString)
            command = CommandProjectSetOntologyIRIAndVersion(self.project, ontIriString, version, oldIri, oldVersion)
            self.session.undostack.beginMacro('Set ontology IRI')
            if command:
                self.session.undostack.push(command)
            self.session.undostack.endMacro()
            self.widget('save_ont_iri_version_button').setEnabled(False)
        except IllegalNamespaceError as e:
            # noinspection PyArgumentList
            msgBox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'IRI Definition Error',
                'Illegal identifier defined.',
                informativeText='The string "{}" is not a legal identifier'.format(ontIriString),
                detailedText=str(e),
                parent=self,
            )
            msgBox.exec_()

    @QtCore.pyqtSlot(int, int)
    def onImportCellClicked(self, row, column):
        table = self.widget('ontology_imports_table_widget')
        found = False
        selectedRanges = table.selectedRanges()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                reloadItem = table.item(row, 0)
                impOnt = reloadItem.data(QtCore.Qt.UserRole)
                if not impOnt.correctlyLoaded:
                    found= True
                    break
        self.widget('ontology_imports_reload_button').setEnabled(found)
        self.widget('ontology_imports_delete_button').setEnabled(True)

    @QtCore.pyqtSlot(bool)
    def reloadOntologyImport(self, _):
        """
        Try to reload an ontology import that has not been resolved so far.
        :type _: bool
        """
        self.widget('ontology_imports_reload_button').setEnabled(False)
        self.widget('ontology_imports_delete_button').setEnabled(False)
        table = self.widget('ontology_imports_table_widget')
        selectedRanges = table.selectedRanges()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                reloadItem = table.item(row, 0)
                impOnt = reloadItem.data(QtCore.Qt.UserRole)
                if not impOnt.correctlyLoaded:
                    ontImportWidget = self.session.doOpenImportOntologyWizard(impOnt)
                    connect(ontImportWidget.sgnOntologyImportCorrectlyReloaded, self.onOntologyImportCorrectlyReloaded)
                    ontImportWidget.exec_()
                    break

    @QtCore.pyqtSlot(bool)
    def addOntologyImport(self, _):
        """
        Adds an ontology import to the current project.
        :type _: bool
        """
        ontImportWidget = self.session.doOpenImportOntologyWizard()
        connect(ontImportWidget.sgnOntologyImportAccepted,self.onOntologyImportAccepted)
        ontImportWidget.exec_()

    @QtCore.pyqtSlot(ImportedOntology)
    def onOntologyImportAccepted(self,impOnt):
        table = self.widget('ontology_imports_table_widget')
        rowcount = table.rowCount()
        table.setRowCount(rowcount + 1)
        ontIriItem = QtWidgets.QTableWidgetItem(str(impOnt.ontologyIRI))
        ontIriItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        ontIriItem.setData(QtCore.Qt.UserRole,impOnt)
        table.setItem(rowcount, 0, ontIriItem)
        versionItem = QtWidgets.QTableWidgetItem(str(impOnt.versionIRI))
        versionItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        table.setItem(rowcount, 1, QtWidgets.QTableWidgetItem(versionItem))
        locationItem = QtWidgets.QTableWidgetItem(str(impOnt.docLocation))
        locationItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        table.setItem(rowcount, 2, QtWidgets.QTableWidgetItem(locationItem))
        table.scrollToItem(table.item(rowcount, 0))
        table.resizeColumnToContents(0)

    @QtCore.pyqtSlot(ImportedOntology)
    def onOntologyImportCorrectlyReloaded(self, impOnt):
        table = self.widget('ontology_imports_table_widget')
        rowcount = table.rowCount()
        for row in range(0, rowcount):
            ontIriItem = table.item(row, 0)
            itemImpOnt = ontIriItem.data(QtCore.Qt.UserRole)
            if itemImpOnt is impOnt:
                versionItem = table.item(row, 1)
                locationItem = table.item(row, 2)
                ontIriItem.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
                versionItem.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
                locationItem.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
                break

    @QtCore.pyqtSlot(bool)
    def removeOntologyImport(self, _):
        """
        Removes an ontology import from the current project.
        :type _: bool
        """
        self.widget('ontology_imports_reload_button').setEnabled(False)
        self.widget('ontology_imports_delete_button').setEnabled(False)
        table = self.widget('ontology_imports_table_widget')
        rowcount = table.rowCount()
        selectedRanges = table.selectedRanges()
        commands = []
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                removedItem = table.item(row, 0)
                impOnt = removedItem.data(QtCore.Qt.UserRole)
                command = CommandProjectRemoveOntologyImport(self.project, impOnt)
                commands.append(command)
        self.session.undostack.beginMacro('Remove ontology imports >>')
        for command in commands:
            if command:
                self.session.undostack.push(command)
        self.session.undostack.endMacro()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                table.removeRow(row)
        table.setRowCount(rowcount - sum(map(lambda x: x.rowCount(), selectedRanges)))

    @QtCore.pyqtSlot(bool)
    def addOntologyAnnotation(self, _):
        """
        Adds an annotation to the current ontology.
        :type _: bool
        """
        LOGGER.debug("addOntologyAnnotation called")
        assertionBuilder = AnnotationAssertionBuilderDialog(self.session, self.project.ontologyIRI)
        connect(assertionBuilder.sgnAnnotationAssertionAccepted, self.redraw)
        assertionBuilder.open()

    @QtCore.pyqtSlot(bool)
    def removeOntologyAnnotation(self, _):
        """
        Removes an annotation from the current ontology.
        :type _: bool
        """
        self.widget('ontology_annotations_delete_button').setEnabled(False)
        self.widget('ontology_annotations_edit_button').setEnabled(False)
        table = self.widget('annotations_table_widget')
        rowcount = table.rowCount()
        selectedRanges = table.selectedRanges()
        commands = []
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                removedItem = table.item(row, 0)
                assertion = removedItem.data(QtCore.Qt.UserRole)
                command = CommandIRIRemoveAnnotationAssertion(self.project, self.project.ontologyIRI, assertion)
                commands.append(command)
        self.session.undostack.beginMacro('Remove annotations >>')
        for command in commands:
            if command:
                self.session.undostack.push(command)
        self.session.undostack.endMacro()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                table.removeRow(row)
        table.setRowCount(rowcount - sum(map(lambda x: x.rowCount(), selectedRanges)))

    @QtCore.pyqtSlot(int,int)
    def onAnnotationCellClicked(self,row,column):
        self.widget('ontology_annotations_delete_button').setEnabled(True)
        self.widget('ontology_annotations_edit_button').setEnabled(True)

    @QtCore.pyqtSlot(int, int)
    def onAssertionCellDoubleClicked(self, row: int, _col: int) -> None:
        table: QtWidgets.QTableWidget = self.widget('annotation_assertions_table_widget')
        assertion = table.item(row, 2).data(QtCore.Qt.ItemDataRole.UserRole)
        assertionBuilder = AnnotationAssertionBuilderDialog(
            self.session,
            self.project.ontologyIRI,
            assertion,
        )
        connect(assertionBuilder.sgnAnnotationAssertionCorrectlyModified, self.redraw)
        assertionBuilder.open()

    @QtCore.pyqtSlot(bool)
    def editOntologyAnnotation(self, _):
        self.widget('ontology_annotations_edit_button').setEnabled(False)
        table = self.widget('annotations_table_widget')
        selectedRanges = table.selectedRanges()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                editItem = table.item(row, 0)
                assertion = editItem.data(QtCore.Qt.UserRole)
                assertionBuilder = AnnotationAssertionBuilderDialog(
                    self.session,
                    self.project.ontologyIRI,
                    assertion,
                )
                connect(assertionBuilder.sgnAnnotationAssertionCorrectlyModified,self.redraw)
                assertionBuilder.open()

    #############################################
    # PREFIXES TAB
    #################################

    @QtCore.pyqtSlot(int,int)
    def managePrefixTableEntryModification(self, row, column):
        if not self.addingNewPrefix:
            if column==0:
                self.managePrefixModification(row,column)
            else:
                self.manageNamespaceModification(row,column)
        else:
            self.addingNewPrefix = False

    def managePrefixModification(self, row, column):
        table = self.widget('prefixes_table_widget')
        modifiedItem = table.item(row, column)
        itemText = modifiedItem.text()
        text = str(itemText)
        for index,prefix in self.prefixIndexMap.items():
            if not index==row:
                if prefix==text:
                    table.setItem(row, 0, QtWidgets.QTableWidgetItem(self.prefixIndexMap[row]))
                    # noinspection PyArgumentList
                    msgBox = QtWidgets.QMessageBox(
                        QtWidgets.QMessageBox.Warning,
                        'Prefix Definition Error',
                        'Prefix already defined.',
                        informativeText='The prefix "{}" is already used'.format(text),
                        parent=self,
                    )
                    msgBox.exec_()
                    return
        corrNSItem = table.item(row, 1)
        if corrNSItem:
            nsItemText = corrNSItem.text()
            nsText = str(nsItemText)
            try:
                self.project.isValidPrefixEntry(text,nsText)

                oldPrefix = None
                for pr,ns in self.project.prefixDictItems():
                    if ns==nsText:
                        oldPrefix = pr
                        break

                command = CommandProjectModifyNamespacePrefix(self.project,nsText,text,oldPrefix)
                self.session.undostack.beginMacro('Replace prefix {0} '.format(oldPrefix))
                if command:
                    self.session.undostack.push(command)
                self.session.undostack.endMacro()

                #aggiorno mappa
                self.prefixIndexMap[row]=text
            except IllegalPrefixError as e:
                table.setItem(row, 0, QtWidgets.QTableWidgetItem(self.prefixIndexMap[row]))
                # noinspection PyArgumentList
                msgBox = QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Warning,
                    'Prefix Definition Error',
                    'Illegal prefix defined.',
                    informativeText='The string "{}" is not a legal prefix'.format(text),
                    detailedText=str(e),
                    parent=self,
                )
                msgBox.exec_()

    def manageNamespaceModification(self, row, column):
        table = self.widget('prefixes_table_widget')
        modifiedItem = table.item(row, column)
        itemText = modifiedItem.text()
        text = str(itemText)
        corrPrefixItem = table.item(row, 0)
        prefixItemText = corrPrefixItem.text()
        prefixText = str(prefixItemText)
        try:
            self.project.isValidPrefixEntry(prefixText, text)
            namespace = self.project.getPrefixResolution(prefixText)
            command = CommandProjectModifyPrefixResolution(self.project,prefixText,text,namespace)
            self.session.undostack.beginMacro('Modify prefix {0} '.format(text))
            if command:
                self.session.undostack.push(command)
            self.session.undostack.endMacro()

        except IllegalNamespaceError as e:
            # noinspection PyArgumentList
            msgBox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'Prefix Definition Error',
                'Illegal namespace defined.',
                informativeText='The string "{}" is not a legal namespace'.format(text),
                detailedText=str(e),
                parent=self,
            )
            msgBox.exec_()

    def buildPrefixIndexMap(self):
        self.prefixIndexMap = {}
        table = self.widget('prefixes_table_widget')
        rowcount = table.rowCount()
        for row in range(0,rowcount):
            item = table.item(row, 0)
            itemText = item.text()
            text = str(itemText)
            self.prefixIndexMap[row]=text

    @QtCore.pyqtSlot(bool)
    def addPrefix(self, _):
        """
        Add a new prefix entry to the list of ontology prefixes.
        :type _: bool
        """
        try:
            prefixField = self.widget('prefix_input_field')
            prefixValue = prefixField.value()
            currentPrefixes = self.project.getManagedPrefixes()
            if prefixValue in currentPrefixes:
                # noinspection PyArgumentList
                msgBox = QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Warning,
                    'Prefix Definition Error',
                    'Prefix already defined.',
                    informativeText='The prefix "{}" is already used'.format(prefixValue),
                    parent=self,
                )
                msgBox.exec_()
                return
            nsField = self.widget('ns_input_field')
            nsValue = nsField.value()

            self.project.isValidPrefixEntry(prefixValue, nsValue)

            command = CommandProjectAddPrefix(self.project,prefixValue,nsValue)
            self.session.undostack.beginMacro('Add prefix {0} '.format(prefixValue))
            if command:
                self.session.undostack.push(command)
            self.session.undostack.endMacro()

            self.addingNewPrefix = True
            table = self.widget('prefixes_table_widget')
            rowcount = table.rowCount()
            table.setRowCount(rowcount + 1)
            table.setItem(rowcount, 0, QtWidgets.QTableWidgetItem(prefixValue))
            table.setItem(rowcount, 1, QtWidgets.QTableWidgetItem(nsValue))
            self.buildPrefixIndexMap()
            table.scrollToItem(table.item(rowcount, 0))
            prefixField.setValue('')
            nsField.setValue('')
        except IllegalPrefixError as e:
            # noinspection PyArgumentList
            msgBox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'Prefix Definition Error',
                'Illegal prefix defined.',
                informativeText='The string "{}" is not a legal prefix'.format(prefixValue),
                detailedText=str(e),
                parent=self,
            )
            msgBox.exec_()
        except IllegalNamespaceError as e:
            # noinspection PyArgumentList
            msgBox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'Prefix Definition Error',
                'Illegal namespace defined.',
                informativeText='The string "{}" is not a legal namespace'.format(nsValue),
                detailedText=str(e),
                parent=self,
            )
            msgBox.exec_()

    @QtCore.pyqtSlot(bool)
    def removePrefix(self, _):
        """
        Removes a set of prefix entries from the list of ontology prefixes.
        :type _: bool
        """
        table = self.widget('prefixes_table_widget')
        rowcount = table.rowCount()
        selectedRanges = table.selectedRanges()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                removedItem = table.item(row, 0)
                itemText = removedItem.text()
                text = str(itemText)
                namespace = self.project.getPrefixResolution(text)
                command = CommandProjectRemovePrefix(self.project, text, namespace)
                self.session.undostack.beginMacro('Remove prefix {0} '.format(text))
                if command:
                    self.session.undostack.push(command)
                self.session.undostack.endMacro()

        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                table.removeRow(row)
        table.setRowCount(rowcount - sum(map(lambda x: x.rowCount(), selectedRanges)))
        self.buildPrefixIndexMap()

    #############################################
    # ANNOTATIONS TAB
    #################################

    @QtCore.pyqtSlot(bool)
    def addAnnotationProperty(self, _):
        """
        Adds an annotation property to the ontology alphabet.
        :type _: bool
        """
        try:
            annIRI = self.widget('full_iri_field').value()
            if not self.project.existAnnotationProperty(annIRI):
                self.project.isValidIdentifier(annIRI)

                command = CommandProjectAddAnnotationProperty(self.project, annIRI)
                self.session.undostack.beginMacro('Add annotation property {0} '.format(annIRI))
                if command:
                    self.session.undostack.push(command)
                self.session.undostack.endMacro()

                table = self.widget('annotation_properties_table_widget')
                rowcount = table.rowCount()
                table.setRowCount(rowcount + 1)
                propertyItem = QtWidgets.QTableWidgetItem(str(annIRI))
                propertyItem.setFlags(QtCore.Qt.ItemIsEnabled)
                annotationProperties = [str(e) for e in self.project.getAnnotationPropertyIRIs()]
                annotationProperties.sort()
                idx = annotationProperties.index(str(annIRI)) if str(annIRI) in annotationProperties else rowcount
                table.setItem(idx, 0, propertyItem)
                table.setItem(idx, 1, QtWidgets.QTableWidgetItem(''))
                table.scrollToItem(table.item(idx, 0))
            self.widget('iri_prefix_switch').setCurrentText(self.noPrefixString)
            self.widget('iri_input_field').setText('')
        except IllegalNamespaceError as e:
            # noinspection PyArgumentList
            msgBox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'Entity Definition Error',
                'Illegal namespace defined.',
                informativeText='The string "{}" is not a legal IRI'.format(annIRI),
                detailedText=str(e),
                parent=self,
            )
            msgBox.exec_()

    @QtCore.pyqtSlot(bool)
    def removeAnnotationProperty(self, _):
        """
        Removes an annotation property from the ontology alphabet.
        :type _: bool
        """
        table = self.widget('annotation_properties_table_widget')
        rowcount = table.rowCount()
        selectedRanges = table.selectedRanges()
        commands = []
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                removedItem = table.item(row, 0)
                itemText = removedItem.text()
                text = str(itemText)
                commands.append(CommandProjectRemoveAnnotationProperty(self.project,text))
        self.session.undostack.beginMacro('remove annotation properties >>')
        for command in commands:
            if command:
                self.session.undostack.push(command)
        self.session.undostack.endMacro()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                table.removeRow(row)
        table.setRowCount(rowcount - sum(map(lambda x: x.rowCount(), selectedRanges)))

    @QtCore.pyqtSlot(int)
    def onAnnotationPrefixChanged(self, val):
        self.onAnnotationInputChanged('')

    @QtCore.pyqtSlot('QString')
    def onAnnotationInputChanged(self, val):
        prefix = self.widget('iri_prefix_switch').currentText()
        input = self.widget('iri_input_field').value()
        resolvedPrefix = self.resolvePrefix(prefix)
        fullIri = '{}{}'.format(resolvedPrefix, input)
        self.widget('full_iri_field').setValue(fullIri)

    def resolvePrefix(self, prefixStr):
        prefixLimit = prefixStr.find(':')
        if prefixLimit < 0:
            return ''
        else:
            prefixStr = prefixStr[0:prefixLimit]
            return self.project.getPrefixResolution(prefixStr)
            # return self.project.getPrefixResolution(prefixStr[:-1])

    @QtCore.pyqtSlot(bool)
    def doIriRefactor(self, _):
        """
        Add a new prefix entry to the list of ontology prefixes.
        :type _: bool
        """
        try:
            preField = self.widget('pre_input_field')
            preValue = preField.value()
            #if not preValue:
            #    raise RuntimeError('Please insert a non-empty pre string')
            postField = self.widget('post_input_field')
            postValue = postField.value()
            if postValue:
                self.project.isValidIdentifier(postValue)
            if preValue == postValue:
                return
            matchingIRIS = self.project.getAllIriStartingWith(preValue)
            commandDict = dict()
            for iri in matchingIRIS:
                preIriStr = str(iri)
                postIriStr = str(iri).replace(preValue,postValue,1)
                try:
                    self.project.isValidIdentifier(postIriStr)
                    commandDict[preIriStr] = postIriStr
                except IllegalNamespaceError as e:
                    LOGGER.warning("doIriRefactor(pre='{}' post='{}'): {} excluded from refactoring [{}]".format(preValue,postValue,preIriStr,str(e)))
            command = CommandCommmonSubstringIRIsRefactor(self.project,preValue,commandDict)
            self.session.undostack.beginMacro("IRIs starting with '{}' refactor".format(preValue))
            if command:
                self.session.undostack.push(command)
            self.session.undostack.endMacro()
            # noinspection PyArgumentList
            msgBox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Information,
                'IRI Refactor', 'IRI refactor.',
                informativeText="{} IRIs starting with'{}' have been modified".format(len(commandDict), preValue),
                parent=self,
            )
            msgBox.exec_()
            preField.setValue('')
            postField.setValue('')
        except IllegalNamespaceError as e:
            # noinspection PyArgumentList
            msgBox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'IRI Refactor Error',
                'Illegal post-value.',
                informativeText='The string "{}" is not a legal namespace'.format(postValue),
                detailedText=str(e),
                parent=self,
            )
            msgBox.exec_()
        except RuntimeError as e:
            # noinspection PyArgumentList
            msgBox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'IRI Refactor Error',
                'Illegal pre-value.',
                informativeText='Empty string is not allowed as pre-value',
                detailedText=str(e),
                parent=self,
            )
            msgBox.exec_()

    #############################################
    # Global IRI
    #################################

    @QtCore.pyqtSlot()
    def onLabelSimpleNameCheckBoxClicked(self):
        checkBoxSimpleName = self.widget('label_simplename_checkbox')
        checkBoxUserInput = self.widget('label_userinput_checkbox')
        if checkBoxSimpleName.isChecked() or checkBoxUserInput.isChecked():
            self.widget('lang_switch').setStyleSheet("background:#FFFFFF")
            self.widget('lang_switch').setEnabled(True)
        else:
            self.widget('lang_switch').setStyleSheet("background:#808080")
            self.widget('lang_switch').setEnabled(False)
        self.widget('iri_label_button').setEnabled(True)

    @QtCore.pyqtSlot()
    def onLabelUserInputCheckBoxClicked(self):
        checkBoxSimpleName = self.widget('label_simplename_checkbox')
        checkBoxUserInput = self.widget('label_userinput_checkbox')
        if checkBoxSimpleName.isChecked() or checkBoxUserInput.isChecked():
            self.widget('lang_switch').setStyleSheet("background:#FFFFFF")
            self.widget('lang_switch').setEnabled(True)
            if checkBoxUserInput.isChecked():
                if self.widget('convert_snake') and not self.widget('convert_snake').isEnabled():
                    self.widget('convert_snake').setEnabled(True)
                    self.widget('convert_camel').setEnabled(True)
            else:
                if self.widget('convert_snake') and self.widget('convert_snake').isEnabled():
                    self.widget('convert_snake').setChecked(False)
                    self.widget('convert_snake').setEnabled(False)
                    self.widget('convert_camel').setChecked(False)
                    self.widget('convert_camel').setEnabled(False)
        else:
            self.widget('lang_switch').setStyleSheet("background:#808080")
            self.widget('lang_switch').setEnabled(False)
            if self.widget('convert_snake') and self.widget('convert_snake').isEnabled():
                self.widget('convert_snake').setChecked(False)
                self.widget('convert_snake').setEnabled(False)
                self.widget('convert_camel').setChecked(False)
                self.widget('convert_camel').setEnabled(False)
        self.widget('iri_label_button').setEnabled(True)

    @QtCore.pyqtSlot()
    def onCaseCheckBoxClicked(self, _):
        self.widget('iri_label_button').setEnabled(True)
        self.project.convertCase(self.sender())

    @QtCore.pyqtSlot(int)
    def onLanguageSwitched(self,index):
        self.widget('iri_label_button').setEnabled(True)

    @QtCore.pyqtSlot()
    def doApplyIriLabel(self):
        simpleNameCheckBox = self.widget('label_simplename_checkbox')
        userInputCheckBox = self.widget('label_userinput_checkbox')
        undoLanguage = self.project.defaultLanguage
        redoLanguage = str(self.widget('lang_switch').currentText())
        snakeCheckBox = self.widget('convert_snake')
        camelCheckBox = self.widget('convert_camel')
        command = CommandProjectSetLabelFromSimpleNameOrInputAndLanguage(self.project, simpleNameCheckBox.isChecked(), userInputCheckBox.isChecked(),redoLanguage, snakeCheckBox.isChecked(), camelCheckBox.isChecked(), not simpleNameCheckBox.isChecked(), not userInputCheckBox.isChecked(), undoLanguage, not snakeCheckBox.isChecked(), not camelCheckBox.isChecked())
        self.session.undostack.beginMacro('Set automatic rdfs:label management')
        if command:
            self.session.undostack.push(command)
        self.session.undostack.endMacro()

        self.widget('iri_label_button').setEnabled(False)

    def createTemplate(self):

        session = self.session
        dialog = FileDialog(session)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        filters = ['Comma-separated values (*.csv)', 'Excel Spreadsheet (*.xlsx)']
        dialog.setNameFilters(sorted(filters))
        dialog.selectFile(session.project.name)
        dialog.selectNameFilter(File.Csv.value)
        if dialog.exec_():
            filetype = File.valueOf(dialog.selectedNameFilter())
            try:

                path = expandPath(first(dialog.selectedFiles()))
                try:
                    if filetype == File.Csv:
                        worker = CsvTemplateExporter(session.project, session)
                    if filetype == File.Xlsx:
                        worker = XlsxTemplateExporter(session.project, session)
                except ValueError as e:
                    print(e)
                worker.run(path)
                if fexists(expandPath(first(dialog.selectedFiles()))):
                    session.addNotification("""
                    Ontology export completed: <br><br>
                    <b><a href=file:{0}>{1}</a></b>
                    """.format(expandPath(first(dialog.selectedFiles())), 'Open File'))
            except Exception as e:
                LOGGER.error('error during export: {}', e)
                session.addNotification("""
                <b><font color="#7E0B17">ERROR</font></b>:
                Could not complete the export, see the System Log for details.
                """)

    def importTemplate(self):

        session = self.session

        dialog = AnnotationsOverridingDialog(session)
        if not dialog.exec_():
            return
        override = dialog.checkedOption()

        dialog = FileDialog(session)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        filters = ['Comma-separated values (*.csv)', 'Excel Spreadsheet (*.xlsx)']
        dialog.setNameFilters(sorted(filters))
        dialog.selectNameFilter(File.Csv.value)

        if dialog.exec_():
            files = dialog.selectedFiles()
            path = expandPath(first(dialog.selectedFiles()))
            for file in files:
                filetype = File.valueOf(dialog.selectedNameFilter())
                try:
                    loader = session.createOntologyLoader(filetype, path, session.project, session)
                    if filetype == File.Csv:
                        loader.run(file, override)
                    else:
                        loader.run(path, override)
                    self.redraw()
                except Exception as e:
                    print(e)

        return

    @QtCore.pyqtSlot()
    def addAnnotationAssertion(self):
        assertionBuilder = AnnotationAssertionBuilderDialog(self.session)
        connect(assertionBuilder.sgnAnnotationAssertionAccepted,
                self.onAnnotationAssertionAccepted)
        assertionBuilder.open()

    @QtCore.pyqtSlot(AnnotationAssertion)
    def onAnnotationAssertionAccepted(self, assertion: AnnotationAssertion):
        table: QtWidgets.QTableWidget = self.widget('annotation_assertions_table_widget')
        self._insertAssertionTableRow(assertion)
        table.resizeColumnToContents(0)
        table.scrollToItem(table.item(table.rowCount(), 0))

    @QtCore.pyqtSlot()
    def editAnnotationAssertion(self):
        table = self.widget('annotation_assertions_table_widget')
        selectedRanges = table.selectedRanges()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                itemIri = self.project.getIRI(str(table.item(row, 0).text()))
                assertion = table.item(row, 2).data(QtCore.Qt.UserRole)
                assertionBuilder = AnnotationAssertionBuilderDialog(
                    self.session, itemIri, assertion)
                connect(assertionBuilder.sgnAnnotationAssertionCorrectlyModified,
                        self.onAnnotationAssertionModified)
                assertionBuilder.exec_()  # Needed here but should be replaced with open()

    @QtCore.pyqtSlot(AnnotationAssertion)
    def onAnnotationAssertionModified(self, assertion: AnnotationAssertion):
        table: QtWidgets.QTableWidget = self.widget('annotation_assertions_table_widget')
        for rowcount in range(table.rowCount()):
            itemAssertion = table.item(rowcount, 2).data(QtCore.Qt.UserRole)
            if itemAssertion is assertion:
                table.removeRow(rowcount)
                self._insertAssertionTableRow(assertion, rowcount)
                break

    @QtCore.pyqtSlot()
    def removeAnnotationAssertion(self):
        """
        Removes an annotation assertion from the ontology alphabet.
        """
        table: QtWidgets.QTableWidget = self.widget('annotation_assertions_table_widget')
        # Must remove in reverse order of selection to avoid changing row indexes while removing
        selection = sorted([
            r
            for s in table.selectedRanges()
            for r in range(s.bottomRow(), s.topRow() + 1)
        ], reverse=True)
        self.session.undostack.beginMacro('remove annotation assertions >>')
        for row in selection:
            itemIri = self.project.getIRI(str(table.item(row, 0).text()))
            assertion = table.item(row, 2).data(QtCore.Qt.UserRole)
            self.session.undostack.push(CommandIRIRemoveAnnotationAssertion(
                self.project,
                itemIri,
                assertion,
            ))
            table.removeRow(row)
        self.session.undostack.endMacro()

    @QtCore.pyqtSlot(str)
    def searchAnnotationTable(self, text):
        table = self.widget('annotation_assertions_table_widget')
        columnCount = table.columnCount()
        for row in range(table.rowCount()):
            table.showRow(row)

        self.hiddenRows = []
        for row in range(table.rowCount()):
            contains = False
            for col in range(columnCount):
                item = table.item(row, col).text()
                if text.lower() in item.lower():
                    contains = True
            if not contains:
                table.hideRow(row)
                self.hiddenRows.append(row)

    @QtCore.pyqtSlot()
    def selectAllAnnotationAssertion(self):
        table = self.widget('annotation_assertions_table_widget')
        table.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        table.clearSelection()
        for row in range(table.rowCount()):
            if row not in self.hiddenRows:
                table.selectRow(row)
        table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def _insertAssertionTableRow(
        self,
        assertion: AnnotationAssertion,
        row: int = None,
    ) -> None:
        """
        Insert an annotation assertion into the assertion table.

        :param assertion: the assertion to insert.
        :param row: position to insert the row to.
        """
        table = self.widget('annotation_assertions_table_widget')
        rowcount = row if row is not None else table.rowCount()
        table.insertRow(rowcount)
        iriItem = QtWidgets.QTableWidgetItem(str(assertion.subject))
        iriItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        table.setItem(rowcount, 0, iriItem)
        simpleNameItem = QtWidgets.QTableWidgetItem(assertion.subject.getSimpleName())
        simpleNameItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        table.setItem(rowcount, 1, simpleNameItem)
        propItem = QtWidgets.QTableWidgetItem(str(assertion.assertionProperty))
        propItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        propItem.setData(QtCore.Qt.UserRole, assertion)
        table.setItem(rowcount, 2, propItem)
        valueItem = QtWidgets.QTableWidgetItem(str(assertion.value))
        valueItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        table.setItem(rowcount, 3, valueItem)
        datatypeItem = QtWidgets.QTableWidgetItem(str(assertion.datatype or ''))
        datatypeItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        table.setItem(rowcount, 4, datatypeItem)
        langItem = QtWidgets.QTableWidgetItem(assertion.language or '')
        langItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        table.setItem(rowcount, 5, langItem)

    @QtCore.pyqtSlot()
    def doAddAgent(self):
        agentBuilder = AgentBuilderDialog(self)
        connect(agentBuilder.sgnAgentAccepted, self.onAgentAccepted)
        agentBuilder.open()

    @QtCore.pyqtSlot()
    def onAgentAccepted(self):
        endpointURL = self.widget('endpoint_field').text()
        self.setAgentSuggestions(endpointURL)

    @QtCore.pyqtSlot()
    def doAddProject(self):
        projectBuilder = ProjectBuilderDialog(self)
        connect(projectBuilder.sgnProjectAccepted, self.onProjectAccepted)
        projectBuilder.open()

    @QtCore.pyqtSlot()
    def onProjectAccepted(self):
        endpointURL = self.widget('endpoint_field').text()
        self.setProjectSuggestions(endpointURL)

    @QtCore.pyqtSlot()
    def doAddDistribution(self):
        distributionBuilder = DistributionBuilderDialog(self)
        connect(distributionBuilder.sgnDistributionAccepted, self.onDistributionAccepted)
        distributionBuilder.open()

    @QtCore.pyqtSlot()
    def onDistributionAccepted(self):
        endpointURL = self.widget('endpoint_field').text()
        self.setDistributionSuggestions(endpointURL)

    @QtCore.pyqtSlot()
    def doAddContact(self):
        contactBuilder = ContactBuilderDialog(self)
        connect(contactBuilder.sgnContactAccepted, self.onContactAccepted)
        contactBuilder.open()

    @QtCore.pyqtSlot()
    def onContactAccepted(self):
        endpointURL = self.widget('endpoint_field').text()
        self.setContactPointSuggestions(endpointURL)

    def setAgentSuggestions(self, url):
        agents = getAgentsFromStore(url)
        rightsHolderWidget = self.widget('ndc_rightsHolder_field')
        rightsHolderWidget.addItems(agents)
        publisherWidget = self.widget('ndc_publisher_field')
        publisherWidget.addItems(agents)
        creatorWidget = self.widget('ndc_creator_field')
        creatorWidget.addItems(agents)

    def setContactPointSuggestions(self, url):
        contactPoints = getContactPointsFromStore(url)
        contactPointWidget = self.widget('ndc_contacts_field')
        contactPointWidget.addItems(contactPoints)

    def setProjectSuggestions(self, url):
        projects = getProjectsFromStore(url)
        projectWidget = self.widget('ndc_projects_field')
        projectWidget.addItems(projects)

    def setDistributionSuggestions(self, url):
        distributions = getDistributionsFromStore(url)
        distributionWidget = self.widget('ndc_distributions_field')
        distributionWidget.addItems(distributions)

    def doConnectEndpoint(self):
        endpointWidget = self.widget('endpoint_field')
        url = endpointWidget.text()
        success = getDataFromEndpoint(url)
        if success:
            self.setAgentSuggestions(url)
            self.setContactPointSuggestions(url)
            self.setProjectSuggestions(url)
            self.setDistributionSuggestions(url)
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_done_black').pixmap(48))
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Done!')
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
            msgbox.setText('Triples retrieved from endpoint!')
            msgbox.setTextFormat(QtCore.Qt.RichText)
            msgbox.exec_()
    def doAddMetadata(self):
        annotations = []
        subjectIRI = self.project.ontologyIRI
        url = self.widget('endpoint_field').text()
        titleIT = self.widget('ndc_ITtitle_field').text()
        annotations.append({
            'prop': 'http://purl.org/dc/terms/title',
            'value': titleIT,
            'type': OWL2Datatype.PlainLiteral.value,
            'lang': 'it'})
        titleEN = self.widget('ndc_ENtitle_field').text()
        annotations.append({
            'prop': 'http://purl.org/dc/terms/title',
            'value': titleEN,
            'type': OWL2Datatype.PlainLiteral.value,
            'lang': 'en'
        })
        labelIT = self.widget('ndc_ITlabel_field').text()
        annotations.append({
            'prop': 'http://www.w3.org/2000/01/rdf-schema#label',
            'value': labelIT,
            'type': OWL2Datatype.PlainLiteral.value,
            'lang': 'it'
        })
        labelEN = self.widget('ndc_ENlabel_field').text()
        annotations.append({
            'prop': 'http://www.w3.org/2000/01/rdf-schema#label',
            'value': labelEN,
            'type': OWL2Datatype.PlainLiteral.value,
            'lang': 'en'
        })
        commentIT = self.widget('ndc_ITcomment_field').text()
        annotations.append({
            'prop': 'http://www.w3.org/2000/01/rdf-schema#comment',
            'value': commentIT,
            'type': OWL2Datatype.PlainLiteral.value,
            'lang': 'it'
        })
        commentEN = self.widget('ndc_ENcomment_field').text()
        annotations.append({
            'prop': 'http://www.w3.org/2000/01/rdf-schema#comment',
            'value': commentEN,
            'type': OWL2Datatype.PlainLiteral.value,
            'lang': 'en'
        })
        officialURI = self.widget('ndc_officialURI_field').text()
        annotations.append({
            'prop': 'https://w3id.org/italia/onto/ADMS/officialURI',
            'value': officialURI,
            'type': OWL2Datatype.anyURI.value,
            'lang': ''
        })
        identifier = self.widget('ndc_id_field').text()
        annotations.append({
            'prop': 'http://purl.org/dc/terms/identifier',
            'value': identifier,
            'type': OWL2Datatype.PlainLiteral.value,
            'lang': ''
        })
        creationDate = self.widget('ndc_creationDate_field').date().toString("yyyy-MM-dd")
        annotations.append({
            'prop': 'http://purl.org/dc/terms/issued',
            'value': creationDate+'T00:00:00+00:00',
            'type': OWL2Datatype.dateTime.value,
            'lang': ''
        })
        lastModifiedDate = self.widget('ndc_lastModifiedDate_field').date().toString("yyyy-MM-dd")
        annotations.append({
            'prop': 'http://purl.org/dc/terms/modified',
            'value': lastModifiedDate + 'T00:00:00+00:00',
            'type': OWL2Datatype.dateTime.value,
            'lang': ''
        })
        versionInfoIT = self.widget('ndc_ITversionInfo_field').text()
        annotations.append({
            'prop': 'http://www.w3.org/2002/07/owl#versionInfo',
            'value': versionInfoIT,
            'type': OWL2Datatype.PlainLiteral.value,
            'lang': 'it'
        })
        versionInfoEN = self.widget('ndc_ENversionInfo_field').text()
        annotations.append({
            'prop': 'http://www.w3.org/2002/07/owl#versionInfo',
            'value': versionInfoEN,
            'type': OWL2Datatype.PlainLiteral.value,
            'lang': 'en'
        })
        accrualPeriodicity = self.widget('ndc_accrualPeriodicity_field').currentText()
        annotations.append({
            'prop': 'http://purl.org/dc/terms/accrualPeriodicity',
            'value':  self.project.getIRI(accrualPeriodicity) if accrualPeriodicity else '',
            'type': None,
            'lang': ''
        })
        languages = self.widget('ndc_languages_field').currentData()
        for l in languages:
            annotations.append({
                'prop': 'http://purl.org/dc/terms/language',
                'value': self.project.getIRI(l),
                'type': None,
                'lang': ''
            })
        keyClasses = self.widget('ndc_mainClasses_field').currentData()
        for c in keyClasses:
            annotations.append({
                'prop': 'https://w3id.org/italia/onto/ADMS/hasKeyClass',
                'value': self.project.getIRI(c),
                'type': None,
                'lang': ''
            })
        prefix = self.widget('ndc_prefix_field').text()
        annotations.append({
            'prop': 'https://w3id.org/italia/onto/ADMS/prefix',
            'value': prefix,
            'type': OWL2Datatype.PlainLiteral.value,
            'lang': ''
        })
        rightsHolders = self.widget('ndc_rightsHolder_field').currentData()
        for r in rightsHolders:
            self.project.addIRI(self.project.getIRI(r))
            addIriAnnotationsToProject(url, self.project, r)
            self.redraw()
            annotations.append({
                'prop': 'http://purl.org/dc/terms/rightsHolder',
                'value': self.project.getIRI(r),
                'type': None,
                'lang': ''
            })
        publishers = self.widget('ndc_publisher_field').currentData()
        for p in publishers:
            self.project.addIRI(self.project.getIRI(p))
            addIriAnnotationsToProject(url, self.project, p)
            self.redraw()
            annotations.append({
                'prop': 'http://purl.org/dc/terms/publisher',
                'value': self.project.getIRI(p),
                'type': None,
                'lang': ''
            })
        creators = self.widget('ndc_creator_field').currentData()
        for c in creators:
            self.project.addIRI(self.project.getIRI(c))
            addIriAnnotationsToProject(url, self.project, c)
            self.redraw()
            annotations.append({
                'prop': 'http://purl.org/dc/terms/creator',
                'value': self.project.getIRI(c),
                'type': None,
                'lang': ''
            })
        projects = self.widget('ndc_projects_field').currentData()
        for p in projects:
            self.project.addIRI(self.project.getIRI(p))
            addIriAnnotationsToProject(url, self.project, p)
            self.redraw()
            annotations.append({
                'prop': 'https://w3id.org/italia/onto/ADMS/semanticAssetInUse',
                'value': self.project.getIRI(p),
                'type': None,
                'lang': ''
            })
        distributions = self.widget('ndc_distributions_field').currentData()
        for d in distributions:
            self.project.addIRI(self.project.getIRI(d))
            addIriAnnotationsToProject(url, self.project, d)
            self.redraw()
            annotations.append({
                'prop': 'https://w3id.org/italia/onto/ADMS/hasSemanticAssetDistribution',
                'value': self.project.getIRI(d),
                'type': None,
                'lang': ''
            })
        contacts = self.widget('ndc_contacts_field').currentData()
        for c in contacts:
            self.project.addIRI(self.project.getIRI(c))
            addIriAnnotationsToProject(url, self.project, c)
            self.redraw()
            annotations.append({
                'prop': 'http://www.w3.org/ns/dcat#contactPoint',
                'value': self.project.getIRI(c),
                'type': None,
                'lang': ''
            })
        for a in annotations:
            if(a['value']):
                annotationAssertion = AnnotationAssertion(subjectIRI, self.project.getIRI(a['prop']), a['value'], a['type'], a['lang'])
                command = CommandIRIAddAnnotationAssertion(self.project, subjectIRI, annotationAssertion)
                self.session.undostack.push(command)
                self.redraw()



