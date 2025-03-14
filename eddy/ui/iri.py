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

from eddy.core.commands.iri import (
    CommandChangeIRIOfNode,
    CommandChangeFacetOfNode,
    CommandChangeLiteralOfNode,
    CommandChangeIRIIdentifier,
    CommandEdgeRemoveAnnotation,
    CommandIRIRefactor,
    CommandIRIRemoveAnnotationAssertion,
)
from eddy.core.commands.nodes import (
    CommandNodeAdd,
    CommandNodeSetFont,
)
from eddy.core.common import HasWidgetSystem
from eddy.core.diagram import Diagram
from eddy.core.functions.signals import connect
from eddy.core.items.nodes.attribute import AttributeNode
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.core.items.nodes.facet import FacetNode
from eddy.core.items.nodes.literal import LiteralNode
from eddy.core.items.nodes.value_domain import ValueDomainNode
from eddy.core.owl import (
    Facet,
    IllegalLiteralError,
    IllegalNamespaceError,
    IRI,
    Literal,
    OWL2Datatype, AnnotationAssertionProperty,
)
from eddy.ui.fields import (
    ComboBox,
    StringField,
    CheckBox,
    SpinBox,
)

if TYPE_CHECKING:
    from eddy.ui.session import Session


#############################################
#   GLOBALS
#################################


# noinspection PyArgumentList
def getFunctionalLabel(parent):
    label = QtWidgets.QLabel(parent, objectName='functional_label')
    label.setText('Functional')
    return label


# noinspection PyArgumentList
def getFunctionalCheckBox(parent):
    checkBox = CheckBox(parent, objectName='functional_checkbox')
    return checkBox


# noinspection PyArgumentList
def getPredefinedDatatypeComboBoxLabel(parent):
    comboBoxLabel = QtWidgets.QLabel(parent, objectName='datatype_combobox_label')
    comboBoxLabel.setText('Datatype')
    return comboBoxLabel


# noinspection PyArgumentList
def getPredefinedDatatypeComboBox(parent):
    combobox = ComboBox(parent, objectName='datatype_switch')
    combobox.setEditable(False)
    combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
    combobox.setScrollEnabled(False)
    return combobox


# noinspection PyArgumentList
def getPredefinedConstrainingFacetComboBoxLabel(parent):
    comboBoxLabel = QtWidgets.QLabel(parent, objectName='constraining_facet_combobox_label')
    comboBoxLabel.setText('Constraining facet')
    return comboBoxLabel


# noinspection PyArgumentList
def getPredefinedConstrainingFacetComboBox(parent):
    combobox = ComboBox(parent, objectName='constraining_facet_switch')
    combobox.setEditable(False)
    combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
    combobox.setScrollEnabled(False)
    return combobox


# noinspection PyArgumentList
def getLexicalFormLabel(parent):
    inputLabel = QtWidgets.QLabel(parent, objectName='lexical_form_label')
    inputLabel.setText('Lexical form')
    return inputLabel


# noinspection PyArgumentList
def getLexicalFormTextArea(parent):
    textArea = QtWidgets.QTextEdit(parent, objectName='lexical_form_area')
    return textArea


# noinspection PyArgumentList
def getIRIPrefixComboBoxLabel(parent):
    comboBoxLabel = QtWidgets.QLabel(parent, objectName='iri_prefix_combobox_label')
    comboBoxLabel.setText('Prefix')
    return comboBoxLabel


# noinspection PyArgumentList
def getIRIPrefixComboBox(parent):
    combobox = ComboBox(parent, objectName='iri_prefix_switch')
    combobox.setEditable(False)
    combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
    combobox.setScrollEnabled(False)
    return combobox


# noinspection PyArgumentList
def getInputLabel(parent):
    inputLabel = QtWidgets.QLabel(parent, objectName='input_field_label')
    inputLabel.setText('Input')
    return inputLabel


# noinspection PyArgumentList
def getInputField(parent):
    inputField = StringField(parent, objectName='iri_input_field')
    return inputField


# noinspection PyArgumentList
def getFullIRILabel(parent):
    fullIriLabel = QtWidgets.QLabel(parent, objectName='full_iri_label')
    fullIriLabel.setText('Full IRI')
    return fullIriLabel


# noinspection PyArgumentList
def getFullIRIField(parent):
    fullIriField = StringField(parent, objectName='full_iri_field')
    fullIriField.setReadOnly(True)
    return fullIriField


# noinspection PyArgumentList
def getAnnotationAssertionsTable(parent):
    table = QtWidgets.QTableWidget(0, 2, parent, objectName='annotation_assertions_table_widget')
    table.setHorizontalHeaderLabels(['Property', 'Connected Resource'])
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionsClickable(False)
    table.horizontalHeader().setMinimumSectionSize(170)
    table.horizontalHeader().setSectionsClickable(False)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setSectionsClickable(False)
    table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    return table

def getImportedAnnotationAssertionsTable(parent):
    table = QtWidgets.QTableWidget(0, 2, parent, objectName='imported_annotation_assertions_table_widget')
    table.setHorizontalHeaderLabels(['Property', 'Connected Resource'])
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionsClickable(False)
    table.horizontalHeader().setMinimumSectionSize(170)
    table.horizontalHeader().setSectionsClickable(False)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setSectionsClickable(False)
    table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    return table
# noinspection PyArgumentList
def getAnnotationsTable(parent):
    table = QtWidgets.QTableWidget(0, 2, parent, objectName='annotations_table_widget')
    table.setHorizontalHeaderLabels(['Property', 'Connected Resource'])
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionsClickable(False)
    table.horizontalHeader().setMinimumSectionSize(170)
    table.horizontalHeader().setSectionsClickable(False)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setSectionsClickable(False)
    table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    return table


def resolvePrefix(project, prefixStr):
    """
    :type project: Project
    :type prefixStr: str
    """
    prefixLimit = prefixStr.find(':')
    if prefixLimit < 0:
        return ''
    else:
        prefixStr = prefixStr[0:prefixLimit]
        return project.getPrefixResolution(prefixStr)


class IriBuilderDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    Dialog used to define new IRIs.
    """
    sgnIRIAccepted = QtCore.pyqtSignal(QtWidgets.QGraphicsItem)

    def __init__(
        self,
        node: AbstractNode,
        diagram: Diagram,
        session: Session,
    ) -> None:
        """
        Initialize the IRI builder dialog.
        :type diagram: Diagram
        :type node: ConceptNode|AttributeNode|RoleNode|IndividualNode
        :type session: Session
        """
        super().__init__(session)
        self.diagram = diagram
        self.session = session

        self.node = node
        self.iri = None
        shortest = None
        if self.node.iri:
            self.iri = self.node.iri
            shortest = self.session.project.getShortestPrefixedForm(self.iri)
        self.project = diagram.project

        #############################################
        # IRI TAB
        #################################

        comboBoxLabel = getIRIPrefixComboBoxLabel(self)
        self.addWidget(comboBoxLabel)

        combobox = getIRIPrefixComboBox(self)
        combobox.clear()
        combobox.addItem('')
        combobox.addItems([x + ':' + '  <' + y + '>' for x, y in self.project.prefixDictItems()])
        if shortest:
            combobox.setCurrentText(
                shortest.prefix + ':' + '  <' + self.project.getNamespace(shortest.prefix) + '>'
            )
        else:
            if not self.iri:
                ontPrefix = self.project.ontologyPrefix
                if ontPrefix is not None:
                    combobox.setCurrentText(
                        ontPrefix + ':' + '  <' + self.project.getNamespace(ontPrefix) + '>'
                    )
                else:
                    combobox.setCurrentText('')
            else:
                combobox.setCurrentText('')
        self.addWidget(combobox)

        inputLabel = getInputLabel(self)
        self.addWidget(inputLabel)

        inputField = getInputField(self)
        if shortest:
            inputField.setText(shortest.suffix)
        elif self.iri:
            inputField.setText(str(self.iri))
        else:
            inputField.setText('')
        self.addWidget(inputField)

        fullIriLabel = getFullIRILabel(self)
        self.addWidget(fullIriLabel)

        fullIriField = getFullIRIField(self)
        if self.iri:
            fullIriField.setText(str(self.iri))
        else:
            ontPrefix = self.project.ontologyPrefix
            if ontPrefix:
                fullIriField.setText(self.project.getNamespace(ontPrefix))
            else:
                fullIriField.setText('')
        self.addWidget(fullIriField)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('iri_prefix_combobox_label'),
                          self.widget('iri_prefix_switch'))
        formlayout.addRow(self.widget('input_field_label'), self.widget('iri_input_field'))
        formlayout.addRow(self.widget('full_iri_label'), self.widget('full_iri_field'))

        # groupbox = QtWidgets.QGroupBox('', self, objectName='iri_definition_group_widget')
        # groupbox.setLayout(formlayout)
        # self.addWidget(groupbox)

        checkBoxLabel = QtWidgets.QLabel(self, objectName='checkBox_label_simplename')
        checkBoxLabel.setText('Derive rdfs:label from simple name')
        self.addWidget(checkBoxLabel)
        checked = self.project.addLabelFromSimpleName
        checkBox = CheckBox('', self, enabled=True, checked=checked,
                            clicked=self.onLabelSimpleNameCheckBoxClicked,
                            objectName='label_simplename_checkbox')
        self.addWidget(checkBox)

        checkBoxLabel = QtWidgets.QLabel(self, objectName='checkBox_label_userinput')
        checkBoxLabel.setText('Derive rdfs:label from user input')
        self.addWidget(checkBoxLabel)
        checked = self.project.addLabelFromUserInput
        checkBox = CheckBox('', self, enabled=True, checked=checked,
                            clicked=self.onLabelUserInputCheckBoxClicked,
                            objectName='label_userinput_checkbox')
        self.addWidget(checkBox)

        snakeCheckbox = CheckBox('convert snake_case to space separated values', self, checked=self.project.convertSnake,
                                 objectName='convert_snake')
        snakeCheckbox.clicked.connect(lambda: self.project.convertCase(snakeCheckbox))
        self.addWidget(snakeCheckbox)
        snakeCheckbox.setEnabled(checked)

        camelCheckbox = CheckBox('convert camelCase to space separated values', self, checked=self.project.convertCamel,
                                 objectName='convert_camel')
        camelCheckbox.clicked.connect(lambda: self.project.convertCase(camelCheckbox))
        self.addWidget(camelCheckbox)
        camelCheckbox.setEnabled(checked)

        comboBoxLabel = QtWidgets.QLabel(self, objectName='lang_combobox_label')
        comboBoxLabel.setText('rdfs:label language')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='lang_switch')
        combobox.setEditable(False)
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(True)
        combobox.addItem('')
        combobox.addItems([x for x in self.project.getLanguages()])
        if self.project.defaultLanguage:
            combobox.setCurrentText(self.project.defaultLanguage)
        else:
            combobox.setCurrentText('')
        if (
            self.widget('label_simplename_checkbox').isChecked()
            or self.widget('label_userinput_checkbox').isChecked()
        ):
            combobox.setStyleSheet("background:#FFFFFF")
            combobox.setEnabled(True)
        else:
            combobox.setStyleSheet("background:#808080")
            combobox.setEnabled(False)

        self.addWidget(combobox)
        iriLabelLayout = QtWidgets.QFormLayout()
        iriLabelLayout.addRow(self.widget('checkBox_label_simplename'),
                              self.widget('label_simplename_checkbox'))
        iriLabelLayout.addRow(self.widget('checkBox_label_userinput'),
                              self.widget('label_userinput_checkbox'))
        iriLabelLayout.addRow(self.widget('convert_snake'))
        iriLabelLayout.addRow(self.widget('convert_camel'))
        iriLabelLayout.addRow(self.widget('lang_combobox_label'), self.widget('lang_switch'))

        groupbox = QtWidgets.QGroupBox('', self, objectName='iri_label_group_widget')
        groupbox.setLayout(iriLabelLayout)
        self.addWidget(groupbox)
        groupbox.setEnabled(not self.iri and not isinstance(self.node, ValueDomainNode))

        outerFormlayout = QtWidgets.QFormLayout()
        outerFormlayout.addRow(formlayout)
        outerFormlayout.addRow(groupbox)

        widget = QtWidgets.QWidget()
        widget.setLayout(outerFormlayout)
        widget.setObjectName('iri_widget')
        self.addWidget(widget)

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self,
                                                  objectName='confirmation_widget')
        confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setContentsMargins(10, 0, 10, 10)
        self.addWidget(confirmation)

        #############################################
        # MAIN WIDGET
        #################################

        mainWidget = QtWidgets.QTabWidget(self, objectName='main_widget')
        iriTabLabel = 'IRI'

        #############################################
        # PREDEFINED DATATYPE TAB
        #################################

        if isinstance(self.node, ValueDomainNode):
            comboBoxLabel = getPredefinedDatatypeComboBoxLabel(self)
            self.addWidget(comboBoxLabel)

            combobox = getPredefinedDatatypeComboBox(self)
            combobox.clear()
            combobox.addItem('')
            sortedItems = sorted(self.project.getDatatypeIRIs(), key=str)
            combobox.addItems([str(x) for x in sortedItems])
            if self.iri and self.iri in self.project.getDatatypeIRIs():
                combobox.setCurrentText(str(self.iri))
            else:
                combobox.setCurrentText('')
            self.addWidget(combobox)

            formlayout = QtWidgets.QFormLayout()
            formlayout.addRow(self.widget('datatype_combobox_label'),
                              self.widget('datatype_switch'))
            widget = QtWidgets.QWidget()
            widget.setLayout(formlayout)
            widget.setObjectName('predefined_datatype_widget')
            self.addWidget(widget)
            mainWidget.addTab(self.widget('predefined_datatype_widget'),
                              QtGui.QIcon(':/icons/24/ic_settings_black'), 'Predefined Datatypes')
            iriTabLabel = 'Custom Datatype'

        mainWidget.addTab(self.widget('iri_widget'),
                          QtGui.QIcon(':/icons/24/ic_settings_black'), iriTabLabel)
        self.addWidget(mainWidget)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(740, 420)
        self.setWindowTitle('IRI Builder')

        connect(self.widget('iri_prefix_switch').currentIndexChanged, self.onPrefixChanged)
        connect(self.widget('iri_input_field').textChanged, self.onInputChanged)
        connect(self.sgnIRIAccepted, self.doAddNode)
        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(QtWidgets.QGraphicsItem)
    def doAddNode(self, node: QtWidgets.QGraphicsItem) -> None:
        """
        Add the given node to the diagram.
        """
        if node:
            self.session.undostack.push(CommandNodeAdd(self.diagram, node))

    @QtCore.pyqtSlot()
    def redraw(self):
        shortest = None
        if self.iri:
            shortest = self.project.getShortestPrefixedForm(self.iri)

        #############################################
        # IRI TAB
        #################################

        combobox = self.widget('iri_prefix_switch')
        combobox.clear()
        combobox.addItem('')
        combobox.addItems([x + ':' + '  <' + y + '>' for x, y in self.project.prefixDictItems()])
        if shortest:
            combobox.setCurrentText(
                shortest.prefix + ':' + '  <' + self.project.getNamespace(shortest.prefix) + '>'
            )
        else:
            if not self.iri:
                ontPrefix = self.project.ontologyPrefix
                if not ontPrefix is None:
                    combobox.setCurrentText(
                        ontPrefix + ':' + '  <' + self.project.getNamespace(ontPrefix) + '>'
                    )
                else:
                    combobox.setCurrentText('')
            else:
                combobox.setCurrentText('')

        inputField = self.widget('iri_input_field')
        if shortest:
            inputField.setText(shortest.suffix)
        elif self.iri:
            inputField.setText(str(self.iri))
        else:
            inputField.setText('')

        fullIriField = self.widget('full_iri_field')
        if self.iri:
            fullIriField.setText(str(self.iri))
        else:
            ontPrefix = self.project.ontologyPrefix
            if ontPrefix:
                fullIriField.setText(self.project.getNamespace(ontPrefix))
            else:
                fullIriField.setText('')

        checked = self.project.addLabelFromSimpleName
        checkBox = self.widget('label_simplename_checkbox')
        checkBox.setChecked(checked)

        checked = self.project.addLabelFromUserInput
        checkBox = self.widget('label_userinput_checkbox')
        checkBox.setChecked(checked)

        combobox = self.widget('lang_switch')
        combobox.setEditable(False)
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(True)
        combobox.addItem('')
        combobox.addItems([x for x in self.project.getLanguages()])
        if self.project.defaultLanguage:
            combobox.setCurrentText(self.project.defaultLanguage)
        else:
            combobox.setCurrentText('')
        if (
            self.widget('label_simplename_checkbox').isChecked()
            or self.widget('label_userinput_checkbox').isChecked()
        ):
            combobox.setStyleSheet("background:#FFFFFF")
            combobox.setEnabled(True)
        else:
            combobox.setStyleSheet("background:#808080")
            combobox.setEnabled(False)

        groupbox = self.widget('iri_label_group_widget')
        groupbox.setEnabled(not self.iri and not isinstance(self.node, ValueDomainNode))

        #############################################
        # PREDEFINED DATATYPE TAB
        #################################

        if isinstance(self.node, ValueDomainNode):
            combobox = self.widget('datatype_switch')
            combobox.clear()
            combobox.addItem('')
            sortedItems = sorted(self.project.getDatatypeIRIs(), key=str)
            combobox.addItems([str(x) for x in sortedItems])
            if self.iri and self.iri in self.project.getDatatypeIRIs():
                combobox.setCurrentText(str(self.iri))
            else:
                combobox.setCurrentText('')

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
    def onLabelSimpleNameCheckBoxClicked(self):
        checkBoxSimpleName = self.widget('label_simplename_checkbox')
        checkBoxUserInput = self.widget('label_userinput_checkbox')
        if checkBoxSimpleName.isChecked() or checkBoxUserInput.isChecked():
            self.widget('lang_switch').setStyleSheet("background:#FFFFFF")
            self.widget('lang_switch').setEnabled(True)
        else:
            self.widget('lang_switch').setStyleSheet("background:#808080")
            self.widget('lang_switch').setEnabled(False)

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

    @QtCore.pyqtSlot()
    def accept(self):
        try:
            activeTab = self.widget('main_widget').currentWidget()
            if activeTab is self.widget('iri_widget'):
                userExplicitInput = self.widget('iri_input_field').value()
                inputIriString = self.widget('full_iri_field').value()
                labelLang = self.widget('lang_switch').currentText()
                self.project.isValidIdentifier(inputIriString)
                if self.iri:
                    if not str(self.iri) == inputIriString:
                        if len(self.project.iriOccurrences(iri=self.iri)) == 1:
                            existIRI = self.project.existIRI(inputIriString)
                            if existIRI:
                                newIRI = self.project.getIRI(inputIriString,
                                                             addLabelFromSimpleName=True,
                                                             addLabelFromUserInput=True,
                                                             userInput=userExplicitInput,
                                                             labelLang=labelLang)
                                if newIRI is not self.iri:
                                    oldIRI = self.iri
                                    self.iri = newIRI
                                    self.redraw()
                                    command = CommandIRIRefactor(self.project, self.iri, oldIRI)
                                    self.session.undostack.push(command)
                            else:
                                oldStr = self.iri.namespace
                                command = CommandChangeIRIIdentifier(self.project, self.iri,
                                                                     inputIriString, oldStr)
                                self.session.undostack.push(command)
                        else:
                            command = CommandChangeIRIOfNode(self.project, self.node,
                                                             inputIriString, str(self.iri))
                            self.session.undostack.push(command)
                else:
                    inputIri = self.project.getIRI(
                        inputIriString,
                        addLabelFromSimpleName=self.widget('label_simplename_checkbox').isChecked(),
                        addLabelFromUserInput=self.widget('label_userinput_checkbox').isChecked(),
                        userInput=userExplicitInput,
                        labelExplicitChecked=True, labelLang=labelLang
                    )
                    self.node.iri = inputIri
                    self.sgnIRIAccepted.emit(self.node)
                super().accept()
            elif activeTab is self.widget('predefined_datatype_widget'):
                currText = str(self.widget('datatype_switch').currentText())
                if currText == '':
                    dialog = QtWidgets.QMessageBox(
                        QtWidgets.QMessageBox.Warning,
                        'IRI Datatype Error',
                        'Please select a non-empty element from the combobox',
                        parent=self)
                    dialog.open()
                else:
                    if self.iri:
                        if not str(self.iri) == currText:
                            command = CommandChangeIRIOfNode(
                                self.project, self.node, currText, str(self.iri)
                            )
                            self.session.undostack.push(command)
                    else:
                        inputIri = self.project.getIRI(currText)
                        self.node.iri = inputIri
                        self.sgnIRIAccepted.emit(self.node)
                        if self.node.diagram:
                            self.node.doUpdateNodeLabel()
                    super().accept()
        except IllegalNamespaceError:
            dialog = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'IRI Definition Error',
                'The input string is not a valid IRI',
                parent=self)
            dialog.open()


class IriPropsDialog(QtWidgets.QDialog, HasWidgetSystem):
    sgnIRISwitch = QtCore.pyqtSignal(IRI, IRI)

    def __init__(self, iri, session, focusOnAnnotations=False):
        """
        Initialize the IRI properties dialog.
        :type iri: IRI
        :type session: Session
        """
        super().__init__(session)
        self.session = session
        self.project = session.project
        self.iri = iri

        shortest = self.project.getShortestPrefixedForm(self.iri)
        self.focusOnAnnotation = focusOnAnnotations

        #############################################
        # IRI TAB
        #################################

        comboBoxLabel = getIRIPrefixComboBoxLabel(self)
        self.addWidget(comboBoxLabel)

        combobox = getIRIPrefixComboBox(self)
        combobox.clear()
        combobox.addItem('')
        combobox.addItems([x + ':' + '  <' + y + '>' for x, y in self.project.prefixDictItems()])
        if shortest:
            combobox.setCurrentText(
                shortest.prefix + ':' + '  <' + self.project.getNamespace(shortest.prefix) + '>'
            )
        else:
            combobox.setCurrentText('')
        self.addWidget(combobox)

        inputLabel = getInputLabel(self)
        self.addWidget(inputLabel)

        inputField = getInputField(self)
        if shortest:
            inputField.setText(shortest.suffix)
        else:
            inputField.setText(str(iri))
        self.addWidget(inputField)

        fullIriLabel = getFullIRILabel(self)
        self.addWidget(fullIriLabel)

        fullIriField = getFullIRIField(self)
        fullIriField.setText(str(iri))
        self.addWidget(fullIriField)

        saveBtn = QtWidgets.QPushButton('Save', objectName='save_iri_button')
        connect(saveBtn.clicked, self.saveIRI)
        saveBtn.setEnabled(False)
        self.addWidget(saveBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('save_iri_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('iri_prefix_combobox_label'),
                          self.widget('iri_prefix_switch'))
        formlayout.addRow(self.widget('input_field_label'), self.widget('iri_input_field'))
        formlayout.addRow(self.widget('full_iri_label'), self.widget('full_iri_field'))
        formlayout.addRow(boxlayout)

        widget = QtWidgets.QWidget()
        widget.setLayout(formlayout)
        widget.setObjectName('iri_widget')
        self.addWidget(widget)

        #############################################
        # ANNOTATIONS TAB
        #################################

        table = getAnnotationAssertionsTable(self)
        table.clear()
        connect(table.cellDoubleClicked, self.editAnnotation)
        self.addWidget(table)

        addBtn = QtWidgets.QPushButton('Add', objectName='annotations_add_button')
        delBtn = QtWidgets.QPushButton('Remove', objectName='annotations_delete_button')
        editBtn = QtWidgets.QPushButton('Edit', objectName='annotations_edit_button')
        connect(addBtn.clicked, self.addAnnotation)
        connect(delBtn.clicked, self.removeAnnotation)
        connect(editBtn.clicked, self.editAnnotation)
        self.addWidget(addBtn)
        self.addWidget(delBtn)
        self.addWidget(editBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('annotations_add_button'))
        boxlayout.addWidget(self.widget('annotations_delete_button'))
        boxlayout.addWidget(self.widget('annotations_edit_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('annotation_assertions_table_widget'))
        formlayout.addRow(boxlayout)
        widget = QtWidgets.QWidget()
        widget.setLayout(formlayout)
        widget.setObjectName('annotation_widget')
        self.addWidget(widget)

        #############################################
        # IMPORTED ANNOTATIONS TAB
        #################################

        table = getImportedAnnotationAssertionsTable(self)
        table.clear()
        self.addWidget(table)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('imported_annotation_assertions_table_widget'))
        widget = QtWidgets.QWidget()
        widget.setLayout(formlayout)
        widget.setObjectName('imported_annotation_widget')
        self.addWidget(widget)

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self,
                                                  objectName='confirmation_widget')
        doneBtn = QtWidgets.QPushButton('Done', objectName='done_button')
        confirmation.addButton(doneBtn, QtWidgets.QDialogButtonBox.AcceptRole)
        confirmation.setContentsMargins(10, 0, 10, 10)
        self.addWidget(confirmation)

        #############################################
        # MAIN WIDGET
        #################################

        widget = QtWidgets.QTabWidget(self, objectName='main_widget')
        widget.addTab(self.widget('iri_widget'),
                      QtGui.QIcon(':/icons/24/ic_settings_black'), 'IRI')
        widget.addTab(self.widget('annotation_widget'),
                      QtGui.QIcon(':/icons/24/ic_settings_black'), 'Annotations')

        if self.focusOnAnnotation:
            widget.setCurrentWidget(self.widget('annotation_widget'))

        self.addWidget(widget)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(740, 420)
        self.setWindowTitle('IRI Builder')

        connect(self.widget('iri_prefix_switch').currentIndexChanged, self.onPrefixChanged)
        connect(self.widget('iri_input_field').textChanged, self.onInputChanged)

        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

        self.redraw()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def redraw(self):
        shortest = self.project.getShortestPrefixedForm(self.iri)

        #############################################
        # IRI TAB
        #################################

        combobox = self.widget('iri_prefix_switch')
        combobox.clear()
        combobox.addItem('')
        combobox.addItems([x + ':' + '  <' + y + '>' for x, y in self.project.prefixDictItems()])
        if shortest:
            combobox.setCurrentText(
                shortest.prefix + ':' + '  <' + self.project.getNamespace(shortest.prefix) + '>')
        else:
            combobox.setCurrentText('')

        inputField = self.widget('iri_input_field')
        if shortest:
            inputField.setText(shortest.suffix)
        else:
            inputField.setText(str(self.iri))

        fullIriField = self.widget('full_iri_field')
        fullIriField.setText(str(self.iri))

        #############################################
        # ANNOTATIONS TAB
        #################################

        table = self.widget('annotation_assertions_table_widget')
        annAss = self.iri.annotationAssertions
        table.clear()
        table.setRowCount(len(annAss))
        table.setHorizontalHeaderLabels(['Property', 'Connected Resource'])
        rowcount = 0
        for assertion in annAss:
            propertyItem = QtWidgets.QTableWidgetItem(str(assertion.assertionProperty))
            propertyItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            propertyItem.setData(QtCore.Qt.UserRole, assertion)
            table.setItem(rowcount, 0, propertyItem)
            valueItem = QtWidgets.QTableWidgetItem(str(assertion.getObjectResourceString(True)))
            valueItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            table.setItem(rowcount, 1, QtWidgets.QTableWidgetItem(valueItem))
            rowcount += 1
            if str(assertion.assertionProperty) == str(AnnotationAssertionProperty.fetchedFrom.value):
                # TODO: fetch annotation assertions from source
                source = assertion.getObjectResourceString(True)
                main_widget = self.widget('main_widget')
                main_widget.addTab(self.widget('imported_annotation_widget'),
                      QtGui.QIcon(':/icons/24/ic_settings_black'), 'Imported Annotations')
                imported_ann_table = self.widget('imported_annotation_assertions_table_widget')
                imported_ann_table.clear()
                imported_ann_table.setHorizontalHeaderLabels(['Property', 'Connected Resource'])
        table.resizeColumnToContents(0)

        if self.focusOnAnnotation:
            self.widget('main_widget').setCurrentWidget(self.widget('annotation_widget'))

    @QtCore.pyqtSlot(bool)
    def addAnnotation(self, _):
        """
        Adds an annotation to the current IRI.
        :type _: bool
        """
        assertionBuilder = self.session.doOpenAnnotationAssertionBuilder(self.iri)
        connect(assertionBuilder.sgnAnnotationAssertionAccepted, self.redraw)
        assertionBuilder.exec_()

    @QtCore.pyqtSlot(bool)
    def removeAnnotation(self, _):
        """
        Removes an annotation from the current IRI.
        :type _: bool
        """
        table = self.widget('annotation_assertions_table_widget')
        rowcount = table.rowCount()
        selectedRanges = table.selectedRanges()
        commands = []
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                removedItem = table.item(row, 0)
                assertion = removedItem.data(QtCore.Qt.UserRole)
                command = CommandIRIRemoveAnnotationAssertion(self.project, self.iri, assertion)
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

    @QtCore.pyqtSlot(bool)
    @QtCore.pyqtSlot(int, int)
    def editAnnotation(self, _):
        table = self.widget('annotation_assertions_table_widget')
        selectedRanges = table.selectedRanges()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                editItem = table.item(row, 0)
                assertion = editItem.data(QtCore.Qt.UserRole)
                assertionBuilder = self.session.doOpenAnnotationAssertionBuilder(self.iri,
                                                                                 assertion)
                connect(assertionBuilder.sgnAnnotationAssertionCorrectlyModified,
                        self.redraw)
                assertionBuilder.exec_()

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
        if not fullIri == str(self.iri):
            self.widget('save_iri_button').setEnabled(True)
        else:
            self.widget('save_iri_button').setEnabled(False)

    @QtCore.pyqtSlot(bool)
    def saveIRI(self, _):
        try:
            userExplicitInput = self.widget('iri_input_field').value()
            fullIRIString = self.widget('full_iri_field').value()
            existIRI = self.project.existIRI(fullIRIString)
            if existIRI:
                newIRI = self.project.getIRI(
                    fullIRIString,
                    addLabelFromSimpleName=True,
                    addLabelFromUserInput=True,
                    userInput=userExplicitInput,
                )
                if newIRI is not self.iri:
                    oldIRI = self.iri
                    self.iri = newIRI
                    self.redraw()
                    command = CommandIRIRefactor(self.project, self.iri, oldIRI)
                    self.session.undostack.push(command)
            else:
                if not self.iri.namespace == fullIRIString:
                    oldStr = self.iri.namespace
                    command = CommandChangeIRIIdentifier(self.project, self.iri, fullIRIString,
                                                         oldStr)
                    self.session.undostack.push(command)
        except IllegalNamespaceError:
            dialog = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'IRI Definition Error',
                'The input string cannot be used to build a valid IRI',
                parent=self)
            dialog.open()
        finally:
            self.widget('save_iri_button').setEnabled(False)


class ConstrainingFacetDialog(QtWidgets.QDialog, HasWidgetSystem):
    sgnFacetAccepted = QtCore.pyqtSignal(QtWidgets.QGraphicsItem)
    sgnFacetRejected = QtCore.pyqtSignal(QtWidgets.QGraphicsItem)

    def __init__(self, node, diagram, session):
        """
        Initialize the Facet builder dialog.
        :type diagram: Diagram
        :type node: FacetNode
        :type session: Session
        """
        super().__init__(session)
        self.diagram = diagram
        self.session = session

        self.node = node
        self.facet = None
        if self.node.facet:
            self.facet = self.node.facet
        self.project = diagram.project

        #############################################
        # FACET TAB
        #################################

        comboBoxLabel = getPredefinedConstrainingFacetComboBoxLabel(self)
        self.addWidget(comboBoxLabel)

        combobox = getPredefinedConstrainingFacetComboBox(self)
        combobox.clear()
        combobox.addItem('')
        sortedItems = sorted(self.project.constrainingFacets, key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if self.facet:
            combobox.setCurrentText(str(self.facet.constrainingFacet))
        else:
            combobox.setCurrentText('')
        self.addWidget(combobox)

        lfLabel = getLexicalFormLabel(self)
        self.addWidget(lfLabel)

        lfTextArea = getLexicalFormTextArea(self)
        if self.facet:
            lfTextArea.setText(str(self.facet.literal.lexicalForm))
        else:
            lfTextArea.setText('')
        self.addWidget(lfTextArea)

        comboBoxLabel = getPredefinedDatatypeComboBoxLabel(self)
        self.addWidget(comboBoxLabel)

        combobox = getPredefinedDatatypeComboBox(self)
        combobox.clear()
        combobox.addItem('')
        sortedItems = sorted(self.project.getDatatypeIRIs(), key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if (
            self.facet and self.facet.literal.datatype
            and self.facet.literal.datatype in self.project.getDatatypeIRIs()
        ):
            combobox.setCurrentText(str(self.facet.literal.datatype))
        else:
            combobox.setCurrentText('')
        self.addWidget(combobox)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('constraining_facet_combobox_label'),
                          self.widget('constraining_facet_switch'))
        formlayout.addRow(self.widget('lexical_form_label'), self.widget('lexical_form_area'))
        formlayout.addRow(self.widget('datatype_combobox_label'), self.widget('datatype_switch'))

        widget = QtWidgets.QWidget()
        widget.setLayout(formlayout)
        widget.setObjectName('facet_widget')
        self.addWidget(widget)

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self,
                                                  objectName='confirmation_widget')
        confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setContentsMargins(10, 0, 10, 10)
        self.addWidget(confirmation)

        #############################################
        # MAIN WIDGET
        #################################

        mainWidget = QtWidgets.QTabWidget(self, objectName='main_widget')
        mainWidget.addTab(self.widget('facet_widget'),
                          QtGui.QIcon(':/icons/24/ic_settings_black'), 'Facet')
        self.addWidget(mainWidget)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(740, 420)
        self.setWindowTitle('Facet Builder')

        connect(self.sgnFacetAccepted, self.doAddNode)
        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(QtWidgets.QGraphicsItem)
    def doAddNode(self, node: QtWidgets.QGraphicsItem) -> None:
        """
        Add the given node to the diagram.
        """
        if node:
            self.session.undostack.push(CommandNodeAdd(self.diagram, node))

    @QtCore.pyqtSlot()
    def redraw(self):
        combobox = self.widget('constraining_facet_switch')
        combobox.clear()
        combobox.addItem('')
        sortedItems = sorted(self.project.constrainingFacets, key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if self.facet:
            combobox.setCurrentText(str(self.facet.constrainingFacet))
        else:
            combobox.setCurrentText('')
        self.addWidget(combobox)

        lfTextArea = self.widget('lexical_form_area')
        if self.facet:
            lfTextArea.setText(str(self.facet.literal.lexicalForm))
        else:
            lfTextArea.setText('')

        combobox = self.widget('datatype_switch')
        combobox.clear()
        combobox.addItem('')
        sortedItems = sorted(self.project.getDatatypeIRIs(), key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if (
            self.facet and self.facet.literal.datatype
            and self.facet.literal.datatype in self.project.getDatatypeIRIs()
        ):
            combobox.setCurrentText(str(self.facet.literal.datatype))
        else:
            combobox.setCurrentText('')
        self.addWidget(combobox)

    @QtCore.pyqtSlot()
    def accept(self):
        try:
            currConstrFacet = str(self.widget('constraining_facet_switch').currentText())
            if not currConstrFacet:
                raise RuntimeError('Please select a constraining facet')
            lexForm = str(self.widget('lexical_form_area').toPlainText())
            if not lexForm:
                raise RuntimeError('Please insert a constraining value')
            currDataTypeStr = str(self.widget('datatype_switch').currentText())
            currDataType = None
            if currDataTypeStr == '':
                currDataType = OWL2Datatype.PlainLiteral.value
            else:
                currDataType = self.project.getIRI(currDataTypeStr)
            literal = Literal(lexForm, currDataType)
            facet = Facet(self.project.getIRI(currConstrFacet), literal)
            if self.facet:
                command = CommandChangeFacetOfNode(self.project, self.node, facet, self.facet)
                self.session.undostack.push(command)
            else:
                self.node.facet = facet
                self.sgnFacetAccepted.emit(self.node)
                if self.node.diagram:
                    self.node.doUpdateNodeLabel()
            super().accept()
        except RuntimeError as e:
            dialog = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'Constraining Facet Definition Error',
                str(e), parent=self)
            dialog.open()

    @QtCore.pyqtSlot()
    def reject(self):
        self.sgnFacetRejected.emit(self.node)
        super().reject()


class LiteralDialog(QtWidgets.QDialog, HasWidgetSystem):
    sgnLiteralAccepted = QtCore.pyqtSignal(QtWidgets.QGraphicsItem)

    def __init__(self, node, diagram, session):
        """
        Initialize the Literal builder dialog.
        :type diagram: Diagram
        :type node: LiteralNode
        :type session: Session
        """
        super().__init__(session)
        self.diagram = diagram
        self.session = session

        self.node = node
        self.literal = None
        if self.node._literal:
            self.literal = self.node._literal
        self.project = diagram.project

        #############################################
        # LITERAL TAB
        #################################

        comboBoxLabel = getPredefinedDatatypeComboBoxLabel(self)
        self.addWidget(comboBoxLabel)

        combobox = getPredefinedDatatypeComboBox(self)
        combobox.clear()
        combobox.addItem('')
        sortedItems = sorted(self.project.getDatatypeIRIs(), key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if self.literal and self.literal.datatype:
            combobox.setCurrentText(str(self.literal.datatype))
        else:
            combobox.setCurrentText('')
        self.addWidget(combobox)
        connect(combobox.currentIndexChanged, self.onTypeSwitched)

        lfLabel = getLexicalFormLabel(self)
        self.addWidget(lfLabel)

        lfTextArea = getLexicalFormTextArea(self)
        if self.literal:
            lfTextArea.setText(str(self.literal.lexicalForm))
        else:
            lfTextArea.setText('')
        self.addWidget(lfTextArea)

        comboBoxLabel = QtWidgets.QLabel(self, objectName='lang_combobox_label')
        comboBoxLabel.setText('Lang')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='lang_switch')
        combobox.setEditable(False)
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(True)
        combobox.addItem('')
        combobox.addItems([x for x in self.project.getLanguages()])
        if self.literal and self.literal.language:
            combobox.setCurrentText(str(self.literal.language))
        else:
            combobox.setCurrentText('')
        self.addWidget(combobox)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('datatype_combobox_label'), self.widget('datatype_switch'))
        formlayout.addRow(self.widget('lexical_form_label'), self.widget('lexical_form_area'))
        formlayout.addRow(self.widget('lang_combobox_label'), self.widget('lang_switch'))

        widget = QtWidgets.QWidget()
        widget.setLayout(formlayout)
        widget.setObjectName('literal_widget')
        self.addWidget(widget)

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self,
                                                  objectName='confirmation_widget')
        confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setContentsMargins(10, 0, 10, 10)
        self.addWidget(confirmation)

        #############################################
        # MAIN WIDGET
        #################################

        mainWidget = QtWidgets.QTabWidget(self, objectName='main_widget')
        mainWidget.addTab(self.widget('literal_widget'),
                          QtGui.QIcon(':/icons/24/ic_settings_black'), 'Literal')
        self.addWidget(mainWidget)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(740, 420)
        self.setWindowTitle('Literal Builder')

        connect(self.sgnLiteralAccepted, self.doAddNode)
        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(QtWidgets.QGraphicsItem)
    def doAddNode(self, node: QtWidgets.QGraphicsItem) -> None:
        """
        Add the given node to the diagram.
        """
        if node:
            self.session.undostack.push(CommandNodeAdd(self.diagram, node))

    @QtCore.pyqtSlot()
    def redraw(self):
        combobox = self.widget('datatype_switch')
        combobox.clear()
        combobox.addItem('')
        sortedItems = sorted(self.project.getDatatypeIRIs(), key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if self.literal and self.literal.datatype:
            combobox.setCurrentText(str(self.literal.datatype))
        else:
            combobox.setCurrentText('')
        self.addWidget(combobox)

        lfTextArea = self.widget('lexical_form_area')
        if self.literal:
            lfTextArea.setText(str(self.literal.literal.lexicalForm))
        else:
            lfTextArea.setText('')

        combobox = self.widget('lang_switch')
        combobox.clear()
        combobox.addItem('')
        combobox.addItems([x for x in self.project.getLanguages()])
        if self.literal and self.literal.language:
            combobox.setCurrentText(str(self.literal.language))
        else:
            combobox.setCurrentText('')

    @QtCore.pyqtSlot(int)
    def onTypeSwitched(self, index):
        typeIRI = str(self.widget('datatype_switch').itemText(index))
        if not self.project.canAddLanguageTag(typeIRI):
            self.widget('lang_switch').setStyleSheet("background:#808080")
            self.widget('lang_switch').setEnabled(False)
        else:
            self.widget('lang_switch').setStyleSheet("background:#FFFFFF")
            self.widget('lang_switch').setEnabled(True)

    @QtCore.pyqtSlot()
    def accept(self):
        try:
            datatypeIRI = None
            dataType = str(self.widget('datatype_switch').currentText())
            if dataType:
                datatypeIRI = self.project.getIRI(dataType)
            lexForm = None
            if str(self.widget('lexical_form_area').toPlainText()):
                lexForm = str(self.widget('lexical_form_area').toPlainText())
            language = None
            if str(self.widget('lang_switch').currentText()):
                language = str(self.widget('lang_switch').currentText())
            literal = Literal(lexForm, datatypeIRI, language)

            if self.literal:
                command = CommandChangeLiteralOfNode(self.project, self.node, literal, self.literal)
                self.session.undostack.push(command)
            else:
                self.node._literal = literal
                self.sgnLiteralAccepted.emit(self.node)

                if self.node.diagram:
                    self.node.doUpdateNodeLabel()
            super().accept()
        except IllegalLiteralError as e:
            dialog = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                'Literal Definition Error',
                str(e), parent=self)
            dialog.open()


class FontDialog(QtWidgets.QDialog, HasWidgetSystem):

    def __init__(self, session, node, refactor=False):
        """
        Initialize the Preferences dialog.
        :type session: Session
        """
        super().__init__(session)
        self.node = node
        self.session = session
        self.refactor = refactor

        prefix = QtWidgets.QLabel(self, objectName='font_size_prefix')
        prefix.setText('Node font size (px)')
        self.addWidget(prefix)

        spinbox = SpinBox(self, objectName='font_size_field')
        spinbox.setRange(node.diagram.MinFontSize, node.diagram.MaxFontSize)
        spinbox.setSingleStep(1)
        if not refactor:
            spinbox.setToolTip('Font size for node label (px)')
        else:
            spinbox.setToolTip('Font size for IRI label (px)')
        spinbox.setValue(node.label.font().pixelSize())
        self.addWidget(spinbox)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('font_size_prefix'), self.widget('font_size_field'))
        groupbox = QtWidgets.QGroupBox('Editor', self, objectName='editor_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('editor_widget'), 0, QtCore.Qt.AlignTop)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('general_widget')
        self.addWidget(widget)

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self,
                                                  objectName='confirmation_widget')
        confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setContentsMargins(10, 0, 10, 10)
        self.addWidget(confirmation)

        #############################################
        # MAIN WIDGET
        #################################

        widget = QtWidgets.QTabWidget(self, objectName='main_widget')
        widget.addTab(self.widget('general_widget'),
                      QtGui.QIcon(':/icons/24/ic_settings_black'), 'General')
        self.addWidget(widget)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(740, 420)
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        if not refactor:
            self.setWindowTitle('Set font size of node {}'.format(node.id))
        else:
            self.setWindowTitle('Set font size of IRI {}'.format(str(node.iri)))

        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

    @QtCore.pyqtSlot()
    def accept(self):
        """
        Executed when the dialog is accepted.
        """
        pixelSize = self.widget('font_size_field').value()
        nodes = None
        if self.refactor:
            nodes = self.session.project.iriOccurrences(self.node.type(), self.node.iri)
        else:
            nodes = [self.node]
        command = CommandNodeSetFont(self.node.diagram, nodes, pixelSize)
        self.session.undostack.beginMacro(
            'set {} font size on {} node(s)'.format(pixelSize, len(nodes)))
        if command:
            self.session.undostack.push(command)
        self.session.undostack.endMacro()
        super().accept()


class EdgeAxiomDialog(QtWidgets.QDialog, HasWidgetSystem):

    def __init__(self, edge, session):
        """
        Initialize the edge axiom properties dialog.
        :type edge: AxiomEdge
        :type session: Session
        """
        super().__init__(session)
        self.session = session
        self.project = session.project
        self.edge = edge

        #############################################
        # ANNOTATIONS TAB
        #################################

        table = getAnnotationsTable(self)
        table.clear()
        connect(table.cellDoubleClicked, self.editAnnotation)
        self.addWidget(table)

        addBtn = QtWidgets.QPushButton('Add', objectName='annotations_add_button')
        delBtn = QtWidgets.QPushButton('Remove', objectName='annotations_delete_button')
        editBtn = QtWidgets.QPushButton('Edit', objectName='annotations_edit_button')
        connect(addBtn.clicked, self.addAnnotation)
        connect(delBtn.clicked, self.removeAnnotation)
        connect(editBtn.clicked, self.editAnnotation)
        self.addWidget(addBtn)
        self.addWidget(delBtn)
        self.addWidget(editBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('annotations_add_button'))
        boxlayout.addWidget(self.widget('annotations_delete_button'))
        boxlayout.addWidget(self.widget('annotations_edit_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('annotations_table_widget'))
        formlayout.addRow(boxlayout)
        widget = QtWidgets.QWidget()
        widget.setLayout(formlayout)
        widget.setObjectName('annotation_widget')
        self.addWidget(widget)

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self,
                                                  objectName='confirmation_widget')
        doneBtn = QtWidgets.QPushButton('Done', objectName='done_button')
        confirmation.addButton(doneBtn, QtWidgets.QDialogButtonBox.AcceptRole)
        confirmation.setContentsMargins(10, 0, 10, 10)
        self.addWidget(confirmation)

        #############################################
        # MAIN WIDGET
        #################################

        widget = QtWidgets.QTabWidget(self, objectName='main_widget')
        widget.addTab(self.widget('annotation_widget'),
                      QtGui.QIcon(':/icons/24/ic_settings_black'), 'Annotations')
        self.addWidget(widget)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(740, 420)
        self.setWindowTitle('Axiom annotation {}'.format(str(self.edge)))

        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

        self.redraw()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def redraw(self):

        #############################################
        # ANNOTATIONS TAB
        #################################

        table = self.widget('annotations_table_widget')
        annAss = self.edge.annotations
        table.clear()
        table.setRowCount(len(annAss))
        table.setHorizontalHeaderLabels(['Property', 'Connected Resource'])
        rowcount = 0
        for assertion in annAss:
            propertyItem = QtWidgets.QTableWidgetItem(str(assertion.assertionProperty))
            propertyItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            propertyItem.setData(QtCore.Qt.UserRole, assertion)
            table.setItem(rowcount, 0, propertyItem)
            valueItem = QtWidgets.QTableWidgetItem(str(assertion.getObjectResourceString(True)))
            valueItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            table.setItem(rowcount, 1, QtWidgets.QTableWidgetItem(valueItem))
            rowcount += 1
        table.resizeColumnToContents(0)

    @QtCore.pyqtSlot(bool)
    def addAnnotation(self, _):
        """
        Adds an annotation to the current edge.
        :type _: bool
        """
        annotationBuilder = self.session.doOpenAnnotationBuilder(self.edge)
        connect(annotationBuilder.sgnAnnotationAccepted, self.redraw)
        annotationBuilder.exec_()

    @QtCore.pyqtSlot(bool)
    def removeAnnotation(self, _):
        """
        Removes an annotation from the current edge(axiom).
        :type _: bool
        """
        table = self.widget('annotations_table_widget')
        rowcount = table.rowCount()
        selectedRanges = table.selectedRanges()
        commands = []
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                removedItem = table.item(row, 0)
                assertion = removedItem.data(QtCore.Qt.UserRole)
                command = CommandEdgeRemoveAnnotation(self.project, self.edge, assertion)
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

    @QtCore.pyqtSlot(bool)
    @QtCore.pyqtSlot(int, int)
    def editAnnotation(self, _):
        table = self.widget('annotations_table_widget')
        selectedRanges = table.selectedRanges()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                editItem = table.item(row, 0)
                annotation = editItem.data(QtCore.Qt.UserRole)
                annotationBuilder = self.session.doOpenAnnotationBuilder(self.edge, annotation)
                connect(annotationBuilder.sgnAnnotationCorrectlyModified, self.redraw)
                annotationBuilder.exec_()

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
        if not fullIri == str(self.iri):
            self.widget('save_iri_button').setEnabled(True)
        else:
            self.widget('save_iri_button').setEnabled(False)
