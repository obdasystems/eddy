from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import Qt

from eddy.core.items.nodes.common.base import OntologyEntityNode
from eddy.core.output import getLogger
from eddy.ui.notification import Notification

from eddy.core.common import HasWidgetSystem

from eddy.core.owl import IRI, IllegalNamespaceError, AnnotationAssertion

from eddy.core.functions.signals import connect
from eddy.ui.fields import ComboBox, StringField

from eddy.core.datatypes.qt import Font

LOGGER = getLogger()

class IriBuilderDialog(QtWidgets.QDialog, HasWidgetSystem):

    sgnIRIAccepted = QtCore.pyqtSignal(OntologyEntityNode)
    sgnIRIRejected = QtCore.pyqtSignal(OntologyEntityNode)


    noPrefixString = ''

    def __init__(self,node,diagram,session):
        """
        Initialize the IRI builder dialog.
        :type diagram: Diagram
        :type node: ConceptNode|AttributeNode|RoleNode|IndividualNode
        :type session: Session
        """
        super().__init__(session)
        self.diagram = diagram

        connect(self.sgnIRIAccepted,self.diagram.doAddOntologyEntityNode)

        self.node = node
        self.project = diagram.project

        #############################################
        # IRI TAB
        #################################
        comboBoxLabel = QtWidgets.QLabel(self, objectName='iri_prefix_combobox_label')
        comboBoxLabel.setFont(Font('Roboto', 12))
        comboBoxLabel.setText('Prefix')
        self.addWidget(comboBoxLabel)

        combobox = ComboBox(objectName='iri_prefix_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        combobox.addItem(self.noPrefixString)
        #combobox.addItems([x+':' for x in self.project.getManagedPrefixes()])
        combobox.addItems([x+':'+'  <'+y+'>' for x,y in self.project.prefixDictItems()])
        combobox.setCurrentText(self.noPrefixString)
        self.addWidget(combobox)

        inputLabel = QtWidgets.QLabel(self, objectName='input_field_label')
        inputLabel.setFont(Font('Roboto', 12))
        inputLabel.setText('Input')
        self.addWidget(inputLabel)

        inputField = StringField(self, objectName='iri_input_field')
        #inputField.setFixedWidth(300)
        inputField.setFont(Font('Roboto', 12))
        inputField.setValue('')
        self.addWidget(inputField)

        fullIriLabel = QtWidgets.QLabel(self, objectName='full_iri_label')
        fullIriLabel.setFont(Font('Roboto', 12))
        fullIriLabel.setText('Full IRI')
        self.addWidget(fullIriLabel)
        fullIriField = StringField(self, objectName='full_iri_field')
        #fullIriField.setFixedWidth(300)
        fullIriField.setFont(Font('Roboto', 12))
        fullIriField.setReadOnly(True)
        self.addWidget(fullIriField)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('iri_prefix_combobox_label'), self.widget('iri_prefix_switch'))
        formlayout.addRow(self.widget('input_field_label'), self.widget('iri_input_field'))
        formlayout.addRow(self.widget('full_iri_label'), self.widget('full_iri_field'))

        widget = QtWidgets.QWidget()
        widget.setLayout(formlayout)
        widget.setObjectName('iri_widget')
        self.addWidget(widget)

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self, objectName='confirmation_widget')
        confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setContentsMargins(10, 0, 10, 10)
        confirmation.setFont(Font('Roboto', 12))
        self.addWidget(confirmation)


        #############################################
        # MAIN WIDGET
        #################################
        widget = QtWidgets.QTabWidget(self, objectName='main_widget')
        widget.addTab(self.widget('iri_widget'), QtGui.QIcon(':/icons/24/ic_settings_black'),
                      'IRI')
        widget.addTab(self.widget('annotation_widget'), QtGui.QIcon(':/icons/24/ic_settings_black'),
                      'Annotation')

        self.addWidget(widget)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(740, 420)
        self.setWindowTitle('IRI Builder')

        connect(self.widget('iri_prefix_switch').currentIndexChanged,self.onPrefixChanged)
        connect(self.widget('iri_input_field').textChanged, self.onInputChanged)
        #connect(inputField.textEdited, self.onInputChanged)
        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(int)
    def onPrefixChanged(self, val):
        self.onInputChanged('')

    @QtCore.pyqtSlot('QString')
    def onInputChanged(self, val):
        prefix = self.widget('iri_prefix_switch').currentText()
        input = self.widget('iri_input_field').value()
        resolvedPrefix = self.resolvePrefix(prefix)
        fullIri = '{}{}'.format(resolvedPrefix,input)
        self.widget('full_iri_field').setValue(fullIri)

    @QtCore.pyqtSlot()
    def accept(self):
        try:
            iri = self.project.getIRI(self.widget('full_iri_field').value())
            self.node.iri = iri
            self.sgnIRIAccepted.emit(self.node)
            if self.node.diagram:
                self.node.doUpdateNodeLabel()
            super().accept()
        except IllegalNamespaceError:
            errorDialog = QtWidgets.QErrorMessage(parent=self)
            errorDialog.showMessage('The input string is not a valid IRI')
            errorDialog.setWindowModality(QtCore.Qt.ApplicationModal)
            errorDialog.show()
            errorDialog.raise_()
            errorDialog.activateWindow()

    @QtCore.pyqtSlot()
    def reject(self):
        self.sgnIRIRejected.emit(self.node)
        super().reject()

    #############################################
    #   INTERFACE
    #################################

    def resolvePrefix(self, prefixStr):
        prefixLimit = prefixStr.find(':')
        if prefixLimit<0:
            return ''
        else:
            prefixStr = prefixStr[0:prefixLimit]
            return self.project.getPrefixResolution(prefixStr)
            # return self.project.getPrefixResolution(prefixStr[:-1])


class IriPropsDialog(QtWidgets.QDialog, HasWidgetSystem):

    noPrefixString = ''

    def __init__(self,iri,session):
        """
        Initialize the IRI properties dialog.
        :type iri: IRI
        :type session: Session
        """
        super().__init__(session)

        self.iri = iri

        shortest = self.session.project.getShortestPrefixedForm(self.iri)

        #############################################
        # IRI TAB
        #################################
        comboBoxLabel = QtWidgets.QLabel(self, objectName='iri_prefix_combobox_label')
        comboBoxLabel.setFont(Font('Roboto', 12))
        comboBoxLabel.setText('Prefix')
        self.addWidget(comboBoxLabel)

        combobox = ComboBox(objectName='iri_prefix_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        combobox.addItem(self.noPrefixString)
        #combobox.addItems([x+':' for x in self.project.getManagedPrefixes()])
        combobox.addItems([x+':'+'  <'+y+'>' for x,y in self.project.prefixDictItems()])
        if shortest:
            combobox.setCurrentText(shortest.prefix+':'+' <'+self.project.getNamespace(shortest.prefix)+'>')
        else:
            combobox.setCurrentText(self.noPrefixString)
        self.addWidget(combobox)

        inputLabel = QtWidgets.QLabel(self, objectName='input_field_label')
        inputLabel.setFont(Font('Roboto', 12))
        inputLabel.setText('Input')
        self.addWidget(inputLabel)

        inputField = StringField(self, objectName='iri_input_field')
        #inputField.setFixedWidth(300)
        inputField.setFont(Font('Roboto', 12))
        if shortest:
            inputField.setText(shortest.suffix)
        else:
            inputField.setText(str(iri))
        self.addWidget(inputField)

        fullIriLabel = QtWidgets.QLabel(self, objectName='full_iri_label')
        fullIriLabel.setFont(Font('Roboto', 12))
        fullIriLabel.setText('Full IRI')
        self.addWidget(fullIriLabel)
        fullIriField = StringField(self, objectName='full_iri_field')
        #fullIriField.setFixedWidth(300)
        fullIriField.setFont(Font('Roboto', 12))
        fullIriField.setReadOnly(True)
        fullIriField.setText(str(iri))
        self.addWidget(fullIriField)

        # addBtn = QtWidgets.QPushButton('Add', objectName='annotation_properties_add_button')
        saveBtn = QtWidgets.QPushButton('Remove', objectName='save_iri_button')
        # connect(addBtn.clicked, self.addAnnotationProperty)
        connect(saveBtn.clicked, self.saveIRI)
        # self.addWidget(addBtn)
        self.addWidget(saveBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('save_iri_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('iri_prefix_combobox_label'), self.widget('iri_prefix_switch'))
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

        table = QtWidgets.QTableWidget(0, 2, self, objectName='annotations_table_widget')
        table.setHorizontalHeaderLabels(['Property', 'Connected Resource'])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionsClickable(False)
        table.horizontalHeader().setMinimumSectionSize(170)
        table.horizontalHeader().setSectionsClickable(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setSectionsClickable(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setFont(Font('Roboto', 13))
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

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self, objectName='confirmation_widget')
        confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setContentsMargins(10, 0, 10, 10)
        confirmation.setFont(Font('Roboto', 12))
        self.addWidget(confirmation)


        #############################################
        # MAIN WIDGET
        #################################
        widget = QtWidgets.QTabWidget(self, objectName='main_widget')
        widget.addTab(self.widget('iri_widget'), QtGui.QIcon(':/icons/24/ic_settings_black'),
                      'IRI')
        widget.addTab(self.widget('annotation_widget'), QtGui.QIcon(':/icons/24/ic_settings_black'),
                      'Annotation')

        self.addWidget(widget)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(740, 420)
        self.setWindowTitle('IRI Builder')

        connect(self.widget('iri_prefix_switch').currentIndexChanged,self.onPrefixChanged)
        connect(self.widget('iri_input_field').textChanged, self.onInputChanged)
        #connect(inputField.textEdited, self.onInputChanged)
        doneBtn = QtWidgets.QPushButton('Done', objectName='done_button')
        confirmation.addButton(doneBtn, QtWidgets.QDialogButtonBox.AcceptRole)

        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

        self.redraw()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def redraw(self):
        shortest = self.session.project.getShortestPrefixedForm(self.iri)

        #############################################
        # IRI TAB
        #################################
        combobox = self.widget('iri_prefix_switch')
        combobox.clear()
        combobox.addItem(self.noPrefixString)
        # combobox.addItems([x+':' for x in self.project.getManagedPrefixes()])
        combobox.addItems([x + ':' + '  <' + y + '>' for x, y in self.project.prefixDictItems()])
        if shortest:
            combobox.setCurrentText(shortest.prefix + ':' + ' <' + self.project.getNamespace(shortest.prefix) + '>')
        else:
            combobox.setCurrentText(self.noPrefixString)

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
        table = self.widget('annotations_table_widget')
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
            valueItem = QtWidgets.QTableWidgetItem(str(assertion.getObjectResourceString(self.project, True)))
            valueItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
            table.setItem(rowcount, 1, QtWidgets.QTableWidgetItem(valueItem))
            rowcount += 1
        table.resizeColumnToContents(0)

    @QtCore.pyqtSlot(bool)
    def addAnnotation(self, _):
        """
        Adds an annotation to the current IRI.
        :type _: bool
        """
        # TODO: not implemented yet
        LOGGER.debug("addOntologyAnnotation called")
        assertionBuilder = self.session.doOpenAnnotationAssertionBuilder(self.iri) #AnnotationAssertionBuilderDialog(self.project.ontologyIRI,self.session)
        connect(assertionBuilder.sgnAnnotationAssertionAccepted, self.onAnnotationAssertionAccepted)
        assertionBuilder.exec_()

    @QtCore.pyqtSlot(AnnotationAssertion)
    def onAnnotationAssertionAccepted(self,assertion):
        '''
        :type assertion:AnnotationAssertion
        '''
        table = self.widget('annotations_table_widget')
        rowcount = table.rowCount()
        table.setRowCount(rowcount + 1)
        propertyItem = QtWidgets.QTableWidgetItem(str(assertion.assertionProperty))
        propertyItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        propertyItem.setData(Qt.UserRole,assertion)
        table.setItem(rowcount, 0, propertyItem)
        valueItem = QtWidgets.QTableWidgetItem(str(assertion.getObjectResourceString(self.project, True)))
        valueItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        table.setItem(rowcount, 1, QtWidgets.QTableWidgetItem(valueItem))
        table.scrollToItem(table.item(rowcount, 0))
        table.resizeColumnToContents(0)


    @QtCore.pyqtSlot(bool)
    def removeAnnotation(self, _):
        """
        Removes an annotation from the current IRI.
        :type _: bool
        """
        table = self.widget('annotations_table_widget')
        rowcount = table.rowCount()
        selectedRanges = table.selectedRanges()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                removedItem = table.item(row, 0)
                assertion = removedItem.data(Qt.UserRole)
                self.iri.removeAnnotationAssertion(assertion)
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                table.removeRow(row)
        table.setRowCount(rowcount - sum(map(lambda x: x.rowCount(), selectedRanges)))

    @QtCore.pyqtSlot(bool)
    def editAnnotation(self, _):
        table = self.widget('ontology_annotations_table_widget')
        selectedRanges = table.selectedRanges()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                editItem = table.item(row, 0)
                assertion = editItem.data(Qt.UserRole)
                assertionBuilder = self.session.doOpenAnnotationAssertionBuilder(self.iri,assertion)
                connect(assertionBuilder.sgnAnnotationAssertionCorrectlyModified,self.onAnnotationAssertionModified)
                assertionBuilder.exec_()

    @QtCore.pyqtSlot(AnnotationAssertion)
    def onAnnotationAssertionModified(self,assertion):
        '''
        :type assertion:AnnotationAssertion
        '''
        table = self.widget('ontology_annotations_table_widget')
        rowcount = table.rowCount()
        for row in range(0,rowcount):
            propItem = table.item(row, 0)
            itemAssertion = propItem.data(Qt.UserRole)
            if itemAssertion is assertion:
                newPropertyItem = QtWidgets.QTableWidgetItem(str(assertion.assertionProperty))
                newPropertyItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                newPropertyItem.setData(Qt.UserRole, assertion)
                table.setItem(row, 0, newPropertyItem)
                valueItem = QtWidgets.QTableWidgetItem(str(assertion.getObjectResourceString(self.project, True)))
                valueItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                table.setItem(row, 1, QtWidgets.QTableWidgetItem(valueItem))
                break

    @QtCore.pyqtSlot(int)
    def onPrefixChanged(self, val):
        self.onInputChanged('')

    @QtCore.pyqtSlot('QString')
    def onInputChanged(self, val):
        prefix = self.widget('iri_prefix_switch').currentText()
        input = self.widget('iri_input_field').value()
        resolvedPrefix = self.resolvePrefix(prefix)
        fullIri = '{}{}'.format(resolvedPrefix,input)
        self.widget('full_iri_field').setValue(fullIri)

    @QtCore.pyqtSlot(bool)
    def saveIRI(self,_):
        try:
            #QUANDO MODIFICHI UN'IRI potresti dover cambiare l'associazione dei nodi con le IRI
            '''
            NODO1--->IRI1
            NODO2--->IRI2
            NODO3--->IRI2
            
            se modifico IRI2 in modo che sia uguale a IRI1, allora 
            NODO1--->IRI1
            NODO2--->IRI1
            NODO3--->IRI1
            
            quindi il project deve segnalare a tutti i nodi che, qualora fossero associati ad IRI2,
            devono ora essere associati a IRI1 e modificarsi di conseguenza
            '''
            newIRI = self.project.getIRI(self.widget('full_iri_field').value())
            if not newIRI is self.iri:
                print()
                #gestisci cambiamento oggetto iri


        except IllegalNamespaceError:
            errorDialog = QtWidgets.QErrorMessage(parent=self)
            errorDialog.showMessage('The input string is not a valid IRI')
            errorDialog.setWindowModality(QtCore.Qt.ApplicationModal)
            errorDialog.show()
            errorDialog.raise_()
            errorDialog.activateWindow()

    @QtCore.pyqtSlot()
    def accept(self):
        super().accept()

    @QtCore.pyqtSlot()
    def reject(self):
        super().reject()

    #############################################
    #   INTERFACE
    #################################

    def resolvePrefix(self, prefixStr):
        prefixLimit = prefixStr.find(':')
        if prefixLimit<0:
            return ''
        else:
            prefixStr = prefixStr[0:prefixLimit]
            return self.project.getPrefixResolution(prefixStr)
            # return self.project.getPrefixResolution(prefixStr[:-1])