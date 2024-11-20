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


from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)
from rfc3987 import parse

from eddy.core.commands.iri import (
    CommandEdgeAddAnnotation,
    CommandEdgeModifyAnnotation,
    CommandIRIAddAnnotationAssertion,
    CommandIRIModifyAnnotationAssertion,
)
from eddy.core.common import HasWidgetSystem
from eddy.core.datatypes.graphol import Item
from eddy.core.functions.signals import connect
from eddy.core.owl import (
    Annotation,
    AnnotationAssertion,
    IRI,
    OWL2Datatype,
)
from eddy.ui.fields import (
    ComboBox,
    StringField,
)
from eddy.ui.iri import resolvePrefix

if TYPE_CHECKING:
    from eddy.ui.session import Session
    from eddy.core.items.edges.common.base import AxiomEdge


class AnnotationAssertionBuilderDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    Subclass of `QtWidgets.QDialog` used to define annotation assertions.
    """
    sgnAnnotationAssertionAccepted = QtCore.pyqtSignal(AnnotationAssertion)
    sgnAnnotationAssertionCorrectlyModified = QtCore.pyqtSignal(AnnotationAssertion)
    sgnAnnotationAssertionRejected = QtCore.pyqtSignal()

    def __init__(
        self,
        session: Session,
        iri: IRI = None,
        assertion: AnnotationAssertion = None,
    ) -> None:
        """
        Initialize the annotation assertion builder dialog (subject IRI = iri).
        """
        super().__init__(session)
        self.session = session
        self.project = session.project
        self.iri = iri
        self.assertion = assertion

        self.iconAttribute = QtGui.QIcon(':/icons/18/ic_treeview_attribute')
        self.iconConcept = QtGui.QIcon(':/icons/18/ic_treeview_concept')
        self.iconInstance = QtGui.QIcon(':/icons/18/ic_treeview_instance')
        self.iconRole = QtGui.QIcon(':/icons/18/ic_treeview_role')
        self.iconValue = QtGui.QIcon(':/icons/18/ic_treeview_value')

        # Occurrences in diagrams
        self.classes = sorted(self.project.itemIRIs(Item.ConceptNode), key=str)
        self.objectProperties = sorted(self.project.itemIRIs(Item.RoleNode), key=str)
        self.dataProperties = sorted(self.project.itemIRIs(Item.AttributeNode), key=str)
        self.individuals = sorted(self.project.itemIRIs(Item.IndividualNode), key=str)
        self.datatypes = sorted(self.project.itemIRIs(Item.ValueDomainNode), key=str)
        self.annotations = sorted(self.project.getAnnotationPropertyIRIs(), key=str)

        self.subjects = QtGui.QStandardItemModel(self)
        self.predicates = QtGui.QStandardItemModel(self)
        self.types = QtGui.QStandardItemModel(self)

        comboBoxLabel = QtWidgets.QLabel('&Subject', self, objectName='subject_combobox_label')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='subject_switch')
        comboBoxLabel.setBuddy(combobox)
        combobox.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        combobox.setModel(self.subjects)
        combobox.addItem('')
        if not self.iri:
            for e in self.classes:
                self.subjects.appendRow(QtGui.QStandardItem(self.iconConcept, str(e)))
            for e in self.individuals:
                self.subjects.appendRow(QtGui.QStandardItem(self.iconInstance, str(e)))
            for e in self.objectProperties:
                self.subjects.appendRow(QtGui.QStandardItem(self.iconRole, str(e)))
            for e in self.dataProperties:
                self.subjects.appendRow(QtGui.QStandardItem(self.iconAttribute, str(e)))
            for e in self.datatypes:
                self.subjects.appendRow(QtGui.QStandardItem(self.iconValue, str(e)))
            combobox.setCurrentText('')
        else:
            combobox.addItem(str(self.iri))
            combobox.setCurrentText(str(self.iri))
            combobox.setEnabled(False)

        self.addWidget(combobox)
        connect(combobox.currentIndexChanged, self.onSubjectSwitched)

        comboBoxLabel = QtWidgets.QLabel('&Property', self, objectName='property_combobox_label')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='property_switch')
        comboBoxLabel.setBuddy(combobox)
        combobox.setModel(self.predicates)
        combobox.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        combobox.addItem('')
        for p in self.annotations:
            self.predicates.appendRow(QtGui.QStandardItem(str(p)))
        if not self.assertion:
            combobox.setCurrentText('')
        elif self.assertion.assertionProperty not in self.annotations:
            combobox.addItem(str(self.assertion.assertionProperty))
            combobox.setCurrentText(str(self.assertion.assertionProperty))
            combobox.setEnabled(False)
        else:
            combobox.setCurrentText(str(self.assertion.assertionProperty))
        self.addWidget(combobox)
        connect(combobox.currentIndexChanged, self.onPropertySwitched)

        valueLabel = QtWidgets.QLabel('Value', self, objectName='value_label')
        self.addWidget(valueLabel)

        #############################################
        # LITERAL TAB
        #################################

        textArea = QtWidgets.QTextEdit(self, objectName='value_textedit')
        if self.assertion and not self.assertion.isIRIValued():
            textArea.setText(str(self.assertion.value))
        self.addWidget(textArea)

        comboBoxLabel = QtWidgets.QLabel('&Type', self, objectName='type_combobox_label')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='type_switch')
        comboBoxLabel.setBuddy(combobox)
        combobox.setEditable(False)
        combobox.setModel(self.types)
        combobox.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        combobox.addItem('')
        # Declared or used first
        for d in self.datatypes:
            self.types.appendRow(QtGui.QStandardItem(self.iconValue, str(d)))
        # Remaining not used
        for d in OWL2Datatype:
            if d.value not in self.datatypes:
                self.types.appendRow(QtGui.QStandardItem(self.iconValue, str(d.value)))
        if not self.assertion:
            combobox.setCurrentText('')
        else:
            if self.assertion.datatype:
                combobox.setCurrentText(str(self.assertion.datatype))
            else:
                combobox.setCurrentText('')
        self.addWidget(combobox)
        connect(combobox.currentIndexChanged, self.onTypeSwitched)

        comboBoxLabel = QtWidgets.QLabel('&Lang', self, objectName='lang_combobox_label')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='lang_switch')
        comboBoxLabel.setBuddy(combobox)
        combobox.setEditable(True)
        combobox.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        combobox.addItem('')
        combobox.addItems([x for x in self.project.getLanguages()])
        if not self.assertion:
            combobox.setCurrentText('')
        else:
            if self.assertion.language:
                combobox.setCurrentText(str(self.assertion.language))
            else:
                combobox.setCurrentText('')
        self.addWidget(combobox)
        connect(combobox.editTextChanged, self.onLangChanged)

        formlayout = QtWidgets.QFormLayout(self)
        formlayout.addRow(self.widget('value_textedit'))
        formlayout.addRow(self.widget('type_combobox_label'), self.widget('type_switch'))
        formlayout.addRow(self.widget('lang_combobox_label'), self.widget('lang_switch'))
        widget = QtWidgets.QWidget()
        widget.setLayout(formlayout)
        widget.setObjectName('literal_widget')
        self.addWidget(widget)

        #############################################
        # IRI TAB
        #################################

        comboBoxLabel = QtWidgets.QLabel('Pre&fix', self, objectName='iri_prefix_combobox_label')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='iri_prefix_switch')
        comboBoxLabel.setBuddy(combobox)
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setEditable(False)
        combobox.addItem('')
        combobox.addItems([x + ':' + '  <' + y + '>' for x, y in self.project.prefixDictItems()])
        ontPrefix = self.project.ontologyPrefix
        if ontPrefix is not None:
            combobox.setCurrentText(
                ontPrefix + ':' + '  <' + self.project.getNamespace(ontPrefix) + '>'
            )
        else:
            combobox.setCurrentText('')
        self.addWidget(combobox)

        inputLabel = QtWidgets.QLabel('&Input', self, objectName='input_field_label')
        self.addWidget(inputLabel)
        inputField = StringField('', self, objectName='iri_input_field')
        inputLabel.setBuddy(inputField)
        self.addWidget(inputField)

        fullIriLabel = QtWidgets.QLabel('Full IRI', self, objectName='full_iri_label')
        self.addWidget(fullIriLabel)
        fullIriField = StringField('', self, objectName='full_iri_field')
        fullIriField.setReadOnly(True)
        self.addWidget(fullIriField)

        formlayout2 = QtWidgets.QFormLayout()
        formlayout2.addRow(self.widget('iri_prefix_combobox_label'),
                          self.widget('iri_prefix_switch'))
        formlayout2.addRow(self.widget('input_field_label'), self.widget('iri_input_field'))
        formlayout2.addRow(self.widget('full_iri_label'), self.widget('full_iri_field'))
        widget2 = QtWidgets.QWidget()
        widget2.setLayout(formlayout2)
        widget2.setObjectName('iri_widget')
        self.addWidget(widget2)

        connect(self.widget('iri_prefix_switch').currentIndexChanged, self.onPrefixChanged)
        connect(self.widget('iri_input_field').textChanged, self.onInputChanged)

        if self.assertion and self.assertion.isIRIValued():
            prefixed = self.project.getLongestSuffixPrefixedForm(self.assertion.value)
            if prefixed:
                self.widget('iri_prefix_switch').setCurrentText(
                    f'{prefixed.prefix}:  <{str(self.project.getNamespace(prefixed.prefix))}>'
                )
                self.widget('iri_input_field').setText(prefixed.suffix)
            else:
                self.widget('iri_input_field').setText(str(self.assertion.value))

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        confirmation.setObjectName('confirmation_widget')
        confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setContentsMargins(10, 0, 10, 10)
        if not assertion or not iri:
            confirmation.button(QtWidgets.QDialogButtonBox.Save).setEnabled(False)
        self.addWidget(confirmation)
        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

        #############################################
        # MAIN WIDGET
        #################################

        main_widget = QtWidgets.QTabWidget(self, objectName='main_widget')
        main_widget.addTab(self.widget('literal_widget'), 'Literal')
        main_widget.addTab(self.widget('iri_widget'), 'IRI')
        if self.assertion and self.assertion.isIRIValued():
            main_widget.setCurrentWidget(self.widget('iri_widget'))
        self.addWidget(main_widget)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.widget('subject_combobox_label'))
        layout.addWidget(self.widget('subject_switch'))
        layout.addWidget(self.widget('property_combobox_label'))
        layout.addWidget(self.widget('property_switch'))
        layout.addWidget(self.widget('value_label'))
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)

        typeCombo = self.widget('type_switch')
        langCombo = self.widget('lang_switch')
        if langCombo.currentText():
            typeCombo.setStyleSheet("background: #808080")
            typeCombo.setEnabled(False)
        if typeCombo.currentText():
            langCombo.setStyleSheet("background: #808080")
            langCombo.setEnabled(False)
        self.setMinimumSize(740, 380)
        self.setWindowTitle('Annotation assertion builder <{}>'.format(str(iri)))

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(int)
    def onSubjectSwitched(self, index):
        subIRI = self.widget('subject_switch').itemText(index)
        propIRI = self.widget('property_switch').currentText()
        confirmation = self.widget('confirmation_widget')
        if subIRI != '' and propIRI != '':
            confirmation.button(QtWidgets.QDialogButtonBox.Save).setEnabled(True)
        else:
            confirmation.button(QtWidgets.QDialogButtonBox.Save).setEnabled(False)

    @QtCore.pyqtSlot(int)
    def onPropertySwitched(self, index):
        propIRI = self.widget('property_switch').itemText(index)
        subIRI = self.widget('subject_switch').currentText()
        confirmation = self.widget('confirmation_widget')
        if subIRI != '' and propIRI != '':
            confirmation.button(QtWidgets.QDialogButtonBox.Save).setEnabled(True)
        else:
            confirmation.button(QtWidgets.QDialogButtonBox.Save).setEnabled(False)

    @QtCore.pyqtSlot(int)
    def onTypeSwitched(self, index):
        typeCombo: QtWidgets.QComboBox = self.widget('type_switch')
        langCombo: QtWidgets.QComboBox = self.widget('lang_switch')
        langCombo.setCurrentText('')
        if typeCombo.itemText(index):
            langCombo.setStyleSheet("background: #808080")
            langCombo.setEnabled(False)
        else:
            langCombo.setStyleSheet("background: #FFFFFF")
            langCombo.setEnabled(True)

    @QtCore.pyqtSlot(str)
    def onLangChanged(self, text):
        typeCombo: QtWidgets.QComboBox = self.widget('type_switch')
        typeCombo.setCurrentText('')
        if text:
            typeCombo.setStyleSheet("background: #808080")
            typeCombo.setEnabled(False)
        else:
            typeCombo.setStyleSheet("background: #FFFFFF")
            typeCombo.setEnabled(True)

    @QtCore.pyqtSlot(int)
    def onPrefixChanged(self, _):
        self.onInputChanged('')

    @QtCore.pyqtSlot(str)
    def onInputChanged(self, _):
        prefix = self.widget('iri_prefix_switch').currentText()
        input = self.widget('iri_input_field').value()
        resolvedPrefix = resolvePrefix(self.project, prefix)
        fullIri = '{}{}'.format(resolvedPrefix, input)
        self.widget('full_iri_field').setValue(fullIri)

    @QtCore.pyqtSlot()
    def accept(self):
        subjectStr = self.widget('subject_switch').currentText().strip()
        subjectIRI = self.project.getIRI(subjectStr)
        propertyStr = self.widget('property_switch').currentText().strip()
        propertyIRI = self.project.getIRI(propertyStr)
        activeTab = self.widget('main_widget').currentWidget()
        if activeTab is self.widget('literal_widget'):
            value = self.widget('value_textedit').toPlainText().strip()
            typeStr = self.widget('type_switch').currentText().strip()
            typeIRI = self.project.getIRI(typeStr) if typeStr else None
            if self.widget('lang_switch').isEnabled():
                langStr = self.widget('lang_switch').currentText().strip()
                language = langStr if langStr else None
                if language and language not in self.project.getLanguages():
                    self.project.addLanguageTag(language)
            else:
                language = None
        else:
            value = self.widget('full_iri_field').value()
            try:
                parse(value, rule='IRI')
                value = self.project.getIRI(value)
                typeIRI = None
                language = None
            except ValueError:
                dialog = QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Warning,
                    'IRI Definition Error',
                    'The input string is not a valid IRI',
                    parent=self)
                dialog.open()
                return

        if not self.assertion:
            annAss = AnnotationAssertion(subjectIRI, propertyIRI, value, typeIRI, language)
            command = CommandIRIAddAnnotationAssertion(self.project, subjectIRI, annAss)
            self.session.undostack.push(command)
            self.sgnAnnotationAssertionAccepted.emit(annAss)
        else:
            undo = {
                'assertionProperty': self.assertion.assertionProperty,
                'datatype': self.assertion.datatype,
                'language': self.assertion.language,
                'value': self.assertion.value,
            }
            redo = {
                'assertionProperty': propertyIRI,
                'datatype': typeIRI,
                'language': language,
                'value': value,
            }
            command = CommandIRIModifyAnnotationAssertion(self.project, self.assertion, undo, redo)
            self.session.undostack.push(command)
            self.sgnAnnotationAssertionCorrectlyModified.emit(self.assertion)
        super().accept()


class AnnotationBuilderDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    Subclass of `QtWidgets.QDialog` used to define new annotation properties.
    """
    sgnAnnotationAccepted = QtCore.pyqtSignal(Annotation)
    sgnAnnotationCorrectlyModified = QtCore.pyqtSignal(Annotation)
    sgnAnnotationRejected = QtCore.pyqtSignal()

    def __init__(
        self,
        edge: AxiomEdge,
        session: Session,
        annotation: Annotation = None,
    ) -> None:
        """
        Initialize the annotation builder dialog
        """
        super().__init__(session)
        self.session = session
        self.project = session.project
        self.edge = edge
        self.annotation = annotation

        self.iconAttribute = QtGui.QIcon(':/icons/18/ic_treeview_attribute')
        self.iconConcept = QtGui.QIcon(':/icons/18/ic_treeview_concept')
        self.iconInstance = QtGui.QIcon(':/icons/18/ic_treeview_instance')
        self.iconRole = QtGui.QIcon(':/icons/18/ic_treeview_role')
        self.iconValue = QtGui.QIcon(':/icons/18/ic_treeview_value')

        # Occurrences in diagrams
        self.individuals = sorted(self.project.itemIRIs(Item.IndividualNode), key=str)
        self.datatypes = sorted(self.project.itemIRIs(Item.ValueDomainNode), key=str)
        self.annotations = sorted(self.project.getAnnotationPropertyIRIs(), key=str)

        self.predicates = QtGui.QStandardItemModel(self)
        self.types = QtGui.QStandardItemModel(self)

        comboBoxLabel = QtWidgets.QLabel('&Property', self, objectName='property_combobox_label')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='property_switch')
        comboBoxLabel.setBuddy(combobox)
        combobox.setModel(self.predicates)
        combobox.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        combobox.addItem('')
        for p in self.annotations:
            self.predicates.appendRow(QtGui.QStandardItem(str(p)))
        if not self.annotation:
            combobox.setCurrentText('')
        elif self.annotation.assertionProperty not in self.annotations:
            combobox.addItem(str(self.annotation.assertionProperty))
            combobox.setCurrentText(str(self.annotation.assertionProperty))
            combobox.setEnabled(False)
        else:
            combobox.setCurrentText(str(self.annotation.assertionProperty))
        self.addWidget(combobox)
        connect(combobox.currentIndexChanged, self.onPropertySwitched)

        valueLabel = QtWidgets.QLabel('Value', self, objectName='value_label')
        self.addWidget(valueLabel)

        #############################################
        # LITERAL TAB
        #################################

        textArea = QtWidgets.QTextEdit(self, objectName='value_textedit')
        if self.annotation and not self.annotation.isIRIValued():
            textArea.setText(str(self.annotation.value))
        self.addWidget(textArea)

        comboBoxLabel = QtWidgets.QLabel('&Type', self, objectName='type_combobox_label')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='type_switch')
        comboBoxLabel.setBuddy(combobox)
        combobox.setEditable(False)
        combobox.setModel(self.types)
        combobox.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        combobox.addItem('')
        # Declared or used first
        for d in self.datatypes:
            self.types.appendRow(QtGui.QStandardItem(self.iconValue, str(d)))
        # Remaining not used
        for d in OWL2Datatype:
            if d.value not in self.datatypes:
                self.types.appendRow(QtGui.QStandardItem(self.iconValue, str(d.value)))
        if not self.annotation:
            combobox.setCurrentText('')
        else:
            if self.annotation.datatype:
                combobox.setCurrentText(str(self.annotation.datatype))
            else:
                combobox.setCurrentText('')
        self.addWidget(combobox)
        connect(combobox.currentIndexChanged, self.onTypeSwitched)

        comboBoxLabel = QtWidgets.QLabel('&Lang', self, objectName='lang_combobox_label')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='lang_switch')
        comboBoxLabel.setBuddy(combobox)
        combobox.setEditable(True)
        combobox.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        combobox.addItem('')
        combobox.addItems([x for x in self.project.getLanguages()])
        if not self.annotation:
            combobox.setCurrentText('')
        else:
            if self.annotation.language:
                combobox.setCurrentText(str(self.annotation.language))
            else:
                combobox.setCurrentText('')
        self.addWidget(combobox)
        connect(combobox.editTextChanged, self.onLangChanged)

        formlayout = QtWidgets.QFormLayout(self)
        formlayout.addRow(self.widget('value_textedit'))
        formlayout.addRow(self.widget('type_combobox_label'), self.widget('type_switch'))
        formlayout.addRow(self.widget('lang_combobox_label'), self.widget('lang_switch'))
        widget = QtWidgets.QWidget()
        widget.setLayout(formlayout)
        widget.setObjectName('literal_widget')
        self.addWidget(widget)

        #############################################
        # IRI TAB
        #################################

        comboBoxLabel = QtWidgets.QLabel('Pre&fix', self, objectName='iri_prefix_combobox_label')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='iri_prefix_switch')
        comboBoxLabel.setBuddy(combobox)
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setEditable(False)
        combobox.addItem('')
        combobox.addItems([x + ':' + '  <' + y + '>' for x, y in self.project.prefixDictItems()])
        ontPrefix = self.project.ontologyPrefix
        if ontPrefix is not None:
            combobox.setCurrentText(
                ontPrefix + ':' + '  <' + self.project.getNamespace(ontPrefix) + '>'
            )
        else:
            combobox.setCurrentText('')
        self.addWidget(combobox)

        inputLabel = QtWidgets.QLabel('&Input', self, objectName='input_field_label')
        self.addWidget(inputLabel)
        inputField = StringField('', self, objectName='iri_input_field')
        inputLabel.setBuddy(inputField)
        self.addWidget(inputField)

        fullIriLabel = QtWidgets.QLabel('Full IRI', self, objectName='full_iri_label')
        self.addWidget(fullIriLabel)
        fullIriField = StringField('', self, objectName='full_iri_field')
        fullIriField.setReadOnly(True)
        self.addWidget(fullIriField)

        formlayout2 = QtWidgets.QFormLayout()
        formlayout2.addRow(self.widget('iri_prefix_combobox_label'),
                           self.widget('iri_prefix_switch'))
        formlayout2.addRow(self.widget('input_field_label'), self.widget('iri_input_field'))
        formlayout2.addRow(self.widget('full_iri_label'), self.widget('full_iri_field'))
        widget2 = QtWidgets.QWidget()
        widget2.setLayout(formlayout2)
        widget2.setObjectName('iri_widget')
        self.addWidget(widget2)

        connect(self.widget('iri_prefix_switch').currentIndexChanged, self.onPrefixChanged)
        connect(self.widget('iri_input_field').textChanged, self.onInputChanged)

        if self.annotation and self.annotation.isIRIValued():
            prefixed = self.project.getLongestSuffixPrefixedForm(self.annotation.value)
            if prefixed:
                self.widget('iri_prefix_switch').setCurrentText(
                    f'{prefixed.prefix}:  <{str(self.project.getNamespace(prefixed.prefix))}>'
                )
                self.widget('iri_input_field').setText(prefixed.suffix)
            else:
                self.widget('iri_input_field').setText(str(self.annotation.value))

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        confirmation.setObjectName('confirmation_widget')
        confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setContentsMargins(10, 0, 10, 10)
        if not annotation:
            confirmation.button(QtWidgets.QDialogButtonBox.Save).setEnabled(False)
        self.addWidget(confirmation)
        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

        #############################################
        # MAIN WIDGET
        #################################

        main_widget = QtWidgets.QTabWidget(self, objectName='main_widget')
        main_widget.addTab(self.widget('literal_widget'), 'Literal')
        main_widget.addTab(self.widget('iri_widget'), 'IRI')
        if self.annotation and self.annotation.isIRIValued():
            main_widget.setCurrentWidget(self.widget('iri_widget'))
        self.addWidget(main_widget)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.widget('subject_combobox_label'))
        layout.addWidget(self.widget('subject_switch'))
        layout.addWidget(self.widget('property_combobox_label'))
        layout.addWidget(self.widget('property_switch'))
        layout.addWidget(self.widget('value_label'))
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)

        typeCombo = self.widget('type_switch')
        langCombo = self.widget('lang_switch')
        if langCombo.currentText():
            typeCombo.setStyleSheet("background: #808080")
            typeCombo.setEnabled(False)
        if typeCombo.currentText():
            langCombo.setStyleSheet("background: #808080")
            langCombo.setEnabled(False)
        self.setMinimumSize(740, 380)
        self.setWindowTitle('Annotation builder <{}>'.format(str(edge)))

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(int)
    def onPropertySwitched(self, index):
        propIRI = self.widget('property_switch').itemText(index)
        confirmation = self.widget('confirmation_widget')
        confirmation.button(QtWidgets.QDialogButtonBox.Save).setEnabled(bool(propIRI))

    @QtCore.pyqtSlot(int)
    def onTypeSwitched(self, index):
        typeCombo: QtWidgets.QComboBox = self.widget('type_switch')
        langCombo: QtWidgets.QComboBox = self.widget('lang_switch')
        langCombo.setCurrentText('')
        if typeCombo.itemText(index):
            langCombo.setStyleSheet("background: #808080")
            langCombo.setEnabled(False)
        else:
            langCombo.setStyleSheet("background: #FFFFFF")
            langCombo.setEnabled(True)

    @QtCore.pyqtSlot(str)
    def onLangChanged(self, text):
        typeCombo: QtWidgets.QComboBox = self.widget('type_switch')
        typeCombo.setCurrentText('')
        if text:
            typeCombo.setStyleSheet("background: #808080")
            typeCombo.setEnabled(False)
        else:
            typeCombo.setStyleSheet("background: #FFFFFF")
            typeCombo.setEnabled(True)

    @QtCore.pyqtSlot(int)
    def onPrefixChanged(self, _):
        self.onInputChanged('')

    @QtCore.pyqtSlot(str)
    def onInputChanged(self, _):
        prefix = self.widget('iri_prefix_switch').currentText()
        input = self.widget('iri_input_field').value()
        resolvedPrefix = resolvePrefix(self.project, prefix)
        fullIri = '{}{}'.format(resolvedPrefix, input)
        self.widget('full_iri_field').setValue(fullIri)

    @QtCore.pyqtSlot()
    def accept(self):
        propertyStr = self.widget('property_switch').currentText().strip()
        propertyIRI = self.project.getIRI(propertyStr)
        activeTab = self.widget('main_widget').currentWidget()
        if activeTab is self.widget('literal_widget'):
            value = self.widget('value_textedit').toPlainText().strip()
            typeStr = self.widget('type_switch').currentText().strip()
            typeIRI = self.project.getIRI(typeStr) if typeStr else None
            if self.widget('lang_switch').isEnabled():
                langStr = self.widget('lang_switch').currentText().strip()
                language = langStr if langStr else None
                if language and language not in self.project.getLanguages():
                    self.project.addLanguageTag(language)
            else:
                language = None
        else:
            value = self.widget('full_iri_field').value()
            try:
                parse(value, rule='IRI')
                value = self.project.getIRI(value)
                typeIRI = None
                language = None
            except ValueError:
                dialog = QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Warning,
                    'IRI Definition Error',
                    'The input string is not a valid IRI',
                    parent=self)
                dialog.open()
                return
        if not self.annotation:
            annotation = Annotation(propertyIRI, value, typeIRI, language)
            command = CommandEdgeAddAnnotation(self.project, self.edge, annotation)
            self.session.undostack.push(command)
            self.sgnAnnotationAccepted.emit(annotation)
        else:
            undo = {
                'assertionProperty': self.annotation.assertionProperty,
                'value': self.annotation.value,
                'datatype': self.annotation.datatype,
                'language': self.annotation.language,
            }
            redo = {
                'assertionProperty': propertyIRI,
                'value': value,
                'datatype': typeIRI,
                'language': language,
            }
            command = CommandEdgeModifyAnnotation(self.project, self.annotation, undo, redo)
            self.session.undostack.push(command)
            self.sgnAnnotationCorrectlyModified.emit(self.annotation)
        super().accept()
