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
    AnnotationAssertion, IRI,
)
from eddy.ui.fields import ComboBox


class AnnotationAssertionBuilderDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    Subclass of `QtWidgets.QDialog` used to define annotation assertions.
    """
    sgnAnnotationAssertionAccepted = QtCore.pyqtSignal(AnnotationAssertion)
    sgnAnnotationAssertionCorrectlyModified = QtCore.pyqtSignal(AnnotationAssertion)
    sgnAnnotationAssertionRejected = QtCore.pyqtSignal()

    emptyString = ''

    def __init__(self,session,iri=None,assertion=None):
        """
        Initialize the annotation assertion builder dialog (subject IRI = iri).
        :type iri: IRI
        :type session: Session
        :type assertion: AnnotationAssertion
        """
        super().__init__(session)
        self.session = session
        self.project = session.project
        self.iri = iri
        self.assertion = assertion

        comboBoxLabel = QtWidgets.QLabel(self, objectName='subject_combobox_label')
        comboBoxLabel.setText('Subject')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='subject_switch')
        combobox.setEditable(False)
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(True)
        if not self.iri:
            combobox.addItem(self.emptyString)
            classes = self.project.itemIRIs(Item.ConceptNode)
            objProperties = self.project.itemIRIs(Item.RoleNode)
            dataProperties = self.project.itemIRIs(Item.AttributeNode)
            indiv = self.project.itemIRIs(Item.IndividualNode)
            datatypes = self.project.itemIRIs(Item.ValueDomainNode)
            items = list(set(classes) | set(objProperties) | set(dataProperties) | set(indiv) | set(
                datatypes))
            sortedItems = sorted(items, key=str)
            combobox.addItems([str(x) for x in sortedItems])
            combobox.setCurrentText(self.emptyString)
        else:
            items = [self.iri]
            sortedItems = sorted(items, key=str)
            combobox.addItems([str(x) for x in sortedItems])
            combobox.setCurrentText(str(self.iri))

        self.addWidget(combobox)
        connect(combobox.currentIndexChanged, self.onSubjectSwitched)

        comboBoxLabel = QtWidgets.QLabel(self, objectName='property_combobox_label')
        comboBoxLabel.setText('Property')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='property_switch')
        combobox.setEditable(False)
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(True)
        combobox.addItem(self.emptyString)
        sortedItems = sorted(self.project.getAnnotationPropertyIRIs(), key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if not self.assertion:
            combobox.setCurrentText(self.emptyString)
        else:
            combobox.setCurrentText(str(self.assertion.assertionProperty))
        self.addWidget(combobox)
        connect(combobox.currentIndexChanged, self.onPropertySwitched)

        textArea = QtWidgets.QTextEdit(self, objectName='value_textedit')
        if self.assertion:
            if self.assertion.value:
                textArea.setText(str(self.assertion.value))
        self.addWidget(textArea)

        comboBoxLabel = QtWidgets.QLabel(self, objectName='type_combobox_label')
        comboBoxLabel.setText('Type')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='type_switch')
        combobox.setEditable(False)
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(True)
        combobox.addItem(self.emptyString)

        sortedItems = sorted(self.project.getDatatypeIRIs(), key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if not self.assertion:
            combobox.setCurrentText(self.emptyString)
        else:
            if self.assertion.datatype:
                combobox.setCurrentText(str(self.assertion.datatype))
            else:
                combobox.setCurrentText(self.emptyString)
        self.addWidget(combobox)
        connect(combobox.currentIndexChanged,self.onTypeSwitched)

        comboBoxLabel = QtWidgets.QLabel(self, objectName='lang_combobox_label')
        comboBoxLabel.setText('Lang')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='lang_switch')
        combobox.setEditable(True)
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(True)
        combobox.addItem(self.emptyString)
        combobox.addItems([x for x in self.project.getLanguages()])
        if not self.assertion:
            combobox.setCurrentText(self.emptyString)
        else:
            if self.assertion.language:
                combobox.setCurrentText(str(self.assertion.language))
            else:
                combobox.setCurrentText(self.emptyString)
        self.addWidget(combobox)

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

        formlayout = QtWidgets.QFormLayout(self)
        formlayout.addRow(self.widget('subject_combobox_label'), self.widget('subject_switch'))
        formlayout.addRow(self.widget('property_combobox_label'), self.widget('property_switch'))
        formlayout.addRow(self.widget('value_textedit'))
        formlayout.addRow(self.widget('type_combobox_label'), self.widget('type_switch'))
        formlayout.addRow(self.widget('lang_combobox_label'), self.widget('lang_switch'))
        formlayout.addRow(self.widget('confirmation_widget'))

        self.setMinimumSize(740, 380)
        self.setWindowTitle('Annotation assertion builder <{}>'.format(str(iri)))
        self.redraw()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def redraw(self):
        combobox = self.widget('property_switch')
        combobox.clear()
        combobox.addItem(self.emptyString)
        sortedItems = sorted(self.project.getAnnotationPropertyIRIs(), key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if not self.assertion:
            combobox.setCurrentText(self.emptyString)
        else:
            combobox.setCurrentText(str(self.assertion.assertionProperty))

        textArea = self.widget('value_textedit')
        if self.assertion:
            if self.assertion.value:
                textArea.setText(str(self.assertion.value))

        combobox = self.widget('type_switch')
        combobox.clear()
        combobox.addItem(self.emptyString)
        sortedItems = sorted(self.project.getDatatypeIRIs(), key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if not self.assertion:
            combobox.setCurrentText(self.emptyString)
        else:
            if self.assertion.datatype:
                combobox.setCurrentText(str(self.assertion.datatype))
            else:
                combobox.setCurrentText(self.emptyString)

        combobox = self.widget('lang_switch')
        combobox.clear()
        combobox.addItem(self.emptyString)
        combobox.addItems([x for x in self.project.getLanguages()])
        if not self.assertion:
            combobox.setCurrentText(self.emptyString)
        else:
            if self.assertion.language:
                combobox.setCurrentText(str(self.assertion.language))
            else:
                combobox.setCurrentText(self.emptyString)

    @QtCore.pyqtSlot(int)
    def onSubjectSwitched(self, index):
        subIRI = self.widget('subject_switch').itemText(index)
        propIRI = self.widget('property_switch').currentText()
        confirmation = self.widget('confirmation_widget')
        if subIRI != self.emptyString and propIRI != self.emptyString:
            confirmation.button(QtWidgets.QDialogButtonBox.Save).setEnabled(True)
        else:
            confirmation.button(QtWidgets.QDialogButtonBox.Save).setEnabled(False)


    @QtCore.pyqtSlot(int)
    def onPropertySwitched(self, index):
        propIRI = self.widget('property_switch').itemText(index)
        subIRI = self.widget('subject_switch').currentText()
        confirmation = self.widget('confirmation_widget')
        if subIRI != self.emptyString and propIRI != self.emptyString:
            confirmation.button(QtWidgets.QDialogButtonBox.Save).setEnabled(True)
        else:
            confirmation.button(QtWidgets.QDialogButtonBox.Save).setEnabled(False)


    @QtCore.pyqtSlot(int)
    def onTypeSwitched(self, index):
        typeIRI = self.widget('type_switch').itemText(index)
        if not self.project.canAddLanguageTag(typeIRI):
            self.widget('lang_switch').setStyleSheet("background:#808080")
            self.widget('lang_switch').setEnabled(False)
        else:
            self.widget('lang_switch').setStyleSheet("background:#FFFFFF")
            self.widget('lang_switch').setEnabled(True)

    @QtCore.pyqtSlot()
    def accept(self):

        subjectStr = self.widget('subject_switch').currentText()
        subjectIRI = self.project.getIRI(subjectStr)
        propertyStr = self.widget('property_switch').currentText()
        propertyIRI = self.project.getIRI(propertyStr)
        value = self.widget('value_textedit').toPlainText()
        if not value:
            value = ' '
        else:
            try:
                parse(value, rule='IRI')
                value = self.project.getIRI(value)
            except:
                pass
        typeStr = self.widget('type_switch').currentText()
        typeIRI = None
        if typeStr:
            typeIRI = self.project.getIRI(typeStr)
        language = None
        if self.widget('lang_switch').isEnabled():
            language = self.widget('lang_switch').currentText()
            if language not in self.project.getLanguages():
                self.project.addLanguageTag(language)
        if not self.assertion:
            annAss = AnnotationAssertion(subjectIRI,propertyIRI,value,typeIRI,language)
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

    emptyString = ''

    def __init__(self, edge, session, annotation=None):
        """
        Initialize the annotation builder dialog
        :type edge: AxiomEdge
        :type session: Session
        :type assertion: Annotation
        """
        super().__init__(session)
        self.session = session
        self.project = session.project
        self.edge = edge
        self.annotation = annotation

        comboBoxLabel = QtWidgets.QLabel(self, objectName='property_combobox_label')
        comboBoxLabel.setText('Property')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='property_switch')
        combobox.setEditable(False)
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(True)
        combobox.addItem(self.emptyString)
        sortedItems = sorted(self.project.getAnnotationPropertyIRIs(), key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if not self.annotation:
            combobox.setCurrentText(self.emptyString)
        else:
            combobox.setCurrentText(str(self.annotation.assertionProperty))
        self.addWidget(combobox)
        connect(combobox.currentIndexChanged, self.onPropertySwitched)

        textArea = QtWidgets.QTextEdit(self, objectName='value_textedit')
        if self.annotation:
            if self.annotation.value:
                textArea.setText(str(self.annotation.value))
        self.addWidget(textArea)

        comboBoxLabel = QtWidgets.QLabel(self, objectName='type_combobox_label')
        comboBoxLabel.setText('Type')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='type_switch')
        combobox.setEditable(False)
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(True)
        combobox.addItem(self.emptyString)

        sortedItems = sorted(self.project.getDatatypeIRIs(), key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if not self.annotation:
            combobox.setCurrentText(self.emptyString)
        else:
            if self.annotation.datatype:
                combobox.setCurrentText(str(self.annotation.datatype))
            else:
                combobox.setCurrentText(self.emptyString)
        self.addWidget(combobox)
        connect(combobox.currentIndexChanged, self.onTypeSwitched)

        comboBoxLabel = QtWidgets.QLabel(self, objectName='lang_combobox_label')
        comboBoxLabel.setText('Lang')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='lang_switch')
        combobox.setEditable(True)
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(True)
        combobox.addItem(self.emptyString)
        combobox.addItems([x for x in self.project.getLanguages()])
        if not self.annotation:
            combobox.setCurrentText(self.emptyString)
        else:
            if self.annotation.language:
                combobox.setCurrentText(str(self.annotation.language))
            else:
                combobox.setCurrentText(self.emptyString)
        self.addWidget(combobox)

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

        formlayout = QtWidgets.QFormLayout(self)
        formlayout.addRow(self.widget('property_combobox_label'), self.widget('property_switch'))
        formlayout.addRow(self.widget('value_textedit'))
        formlayout.addRow(self.widget('type_combobox_label'), self.widget('type_switch'))
        formlayout.addRow(self.widget('lang_combobox_label'), self.widget('lang_switch'))
        formlayout.addRow(self.widget('confirmation_widget'))

        self.setMinimumSize(740, 380)
        self.setWindowTitle('Annotation builder <{}>'.format(str(edge)))
        self.redraw()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def redraw(self):
        combobox = self.widget('property_switch')
        combobox.clear()
        combobox.addItem(self.emptyString)
        sortedItems = sorted(self.project.getAnnotationPropertyIRIs(), key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if not self.annotation:
            combobox.setCurrentText(self.emptyString)
        else:
            combobox.setCurrentText(str(self.annotation.assertionProperty))

        textArea = self.widget('value_textedit')
        if self.annotation:
            if self.annotation.value:
                textArea.setText(str(self.annotation.value))

        combobox = self.widget('type_switch')
        combobox.clear()
        combobox.addItem(self.emptyString)
        sortedItems = sorted(self.project.getDatatypeIRIs(), key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if not self.annotation:
            combobox.setCurrentText(self.emptyString)
        else:
            if self.annotation.datatype:
                combobox.setCurrentText(str(self.annotation.datatype))
            else:
                combobox.setCurrentText(self.emptyString)

        combobox = self.widget('lang_switch')
        combobox.clear()
        combobox.addItem(self.emptyString)
        combobox.addItems([x for x in self.project.getLanguages()])
        if not self.annotation:
            combobox.setCurrentText(self.emptyString)
        else:
            if self.annotation.language:
                combobox.setCurrentText(str(self.annotation.language))
            else:
                combobox.setCurrentText(self.emptyString)

    @QtCore.pyqtSlot(int)
    def onPropertySwitched(self, index):
        propIRI = self.widget('property_switch').itemText(index)
        confirmation = self.widget('confirmation_widget')
        confirmation.button(QtWidgets.QDialogButtonBox.Save).setEnabled(bool(propIRI))

    @QtCore.pyqtSlot(int)
    def onTypeSwitched(self, index):
        typeIRI = self.widget('type_switch').itemText(index)
        if not self.project.canAddLanguageTag(typeIRI):
            self.widget('lang_switch').setStyleSheet("background:#808080")
            self.widget('lang_switch').setEnabled(False)
        else:
            self.widget('lang_switch').setStyleSheet("background:#FFFFFF")
            self.widget('lang_switch').setEnabled(True)

    @QtCore.pyqtSlot()
    def accept(self):
        propertyStr = self.widget('property_switch').currentText()
        propertyIRI = self.project.getIRI(propertyStr)
        value = self.widget('value_textedit').toPlainText()
        if not value:
            value = ' '
        typeStr = self.widget('type_switch').currentText()
        typeIRI = None
        if typeStr:
            typeIRI = self.project.getIRI(typeStr)
        language = None
        if self.widget('lang_switch').isEnabled():
            language = self.widget('lang_switch').currentText()
            if language not in self.project.getLanguages():
                self.project.addLanguageTag(language)
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
