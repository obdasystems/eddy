from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QObject, Qt

from eddy.core.commands.iri import CommandIRIRemoveAnnotation, CommandChangeIRIOfNode, CommandChangeFacetOfNode, \
    CommandChangeLiteralOfNode, CommandIRIRefactor, CommandChangeIRIIdentifier
from eddy.core.items.nodes.attribute_iri import AttributeNode
from eddy.core.items.nodes.common.base import OntologyEntityNode
from eddy.core.items.nodes.facet_iri import FacetNode
from eddy.core.items.nodes.literal import LiteralNode
from eddy.core.items.nodes.value_domain_iri import ValueDomainNode
from eddy.core.output import getLogger
from eddy.ui.notification import Notification

from eddy.core.common import HasWidgetSystem

from eddy.core.owl import IRI, IllegalNamespaceError, AnnotationAssertion, Facet, Literal, IllegalLiteralError

from eddy.core.functions.signals import connect
from eddy.ui.fields import ComboBox, StringField, CheckBox

from eddy.core.datatypes.qt import Font

LOGGER = getLogger()

class IRIDialogsWidgetFactory(QObject):

    @staticmethod
    def getFunctionalLabel(parent):
        label = QtWidgets.QLabel(parent, objectName='functional_label')
        label.setFont(Font('Roboto', 12))
        label.setText('Functional')
        return label

    @staticmethod
    def getFunctionalCheckBox(parent):
        checkBox = CheckBox(parent, objectName='functional_checkbox')
        return checkBox

    @staticmethod
    def getPredefinedDatatypeComboBoxLabel(parent):
        comboBoxLabel = QtWidgets.QLabel(parent, objectName='datatype_combobox_label')
        comboBoxLabel.setFont(Font('Roboto', 12))
        comboBoxLabel.setText('Datatype')
        return comboBoxLabel

    @staticmethod
    def getPredefinedDatatypeComboBox(parent):
        combobox = ComboBox(parent, objectName='datatype_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        return combobox

    @staticmethod
    def getPredefinedConstrainingFacetComboBoxLabel(parent):
        comboBoxLabel = QtWidgets.QLabel(parent, objectName='constraining_facet_combobox_label')
        comboBoxLabel.setFont(Font('Roboto', 12))
        comboBoxLabel.setText('Constraining facet')
        return comboBoxLabel

    @staticmethod
    def getPredefinedConstrainingFacetComboBox(parent):
        combobox = ComboBox(parent, objectName='constraining_facet_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        return combobox

    @staticmethod
    def getLexicalFormLabel(parent):
        inputLabel = QtWidgets.QLabel(parent, objectName='lexical_form_label')
        inputLabel.setFont(Font('Roboto', 12))
        inputLabel.setText('Lexical form')
        return inputLabel

    @staticmethod
    def getLexicalFormTextArea(parent):
        textArea = QtWidgets.QTextEdit(parent, objectName='lexical_form_area')
        textArea.setFont(Font('Roboto', 12))
        return textArea

    @staticmethod
    def getIRIPrefixComboBoxLabel(parent):
        comboBoxLabel = QtWidgets.QLabel(parent, objectName='iri_prefix_combobox_label')
        comboBoxLabel.setFont(Font('Roboto', 12))
        comboBoxLabel.setText('Prefix')
        return  comboBoxLabel

    @staticmethod
    def getIRIPrefixComboBox(parent):
        combobox = ComboBox(parent,objectName='iri_prefix_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        return combobox

    @staticmethod
    def getInputLabel(parent):
        inputLabel = QtWidgets.QLabel(parent, objectName='input_field_label')
        inputLabel.setFont(Font('Roboto', 12))
        inputLabel.setText('Input')
        return inputLabel

    @staticmethod
    def getInputField(parent):
        inputField = StringField(parent, objectName='iri_input_field')
        # inputField.setFixedWidth(300)
        inputField.setFont(Font('Roboto', 12))
        return inputField

    @staticmethod
    def getFullIRILabel(parent):
        fullIriLabel = QtWidgets.QLabel(parent, objectName='full_iri_label')
        fullIriLabel.setFont(Font('Roboto', 12))
        fullIriLabel.setText('Full IRI')
        return  fullIriLabel

    @staticmethod
    def getFullIRIField(parent):
        fullIriField = StringField(parent, objectName='full_iri_field')
        # fullIriField.setFixedWidth(300)
        fullIriField.setFont(Font('Roboto', 12))
        fullIriField.setReadOnly(True)
        return fullIriField

    @staticmethod
    def getAnnotationAssertionsTable(parent):
        table = QtWidgets.QTableWidget(0, 2, parent, objectName='annotations_table_widget')
        table.setHorizontalHeaderLabels(['Property', 'Connected Resource'])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionsClickable(False)
        table.horizontalHeader().setMinimumSectionSize(170)
        table.horizontalHeader().setSectionsClickable(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setSectionsClickable(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setFont(Font('Roboto', 13))
        return table

#TODO DOVRAI POI PENSARE A MECCANISMO PER IMPEDIRE MODIFICA IRI DI DEFAULT (owl:Thing, rdfs:label, xsd:string ....)
#TODO in caso nodo sia associato a IRI di default, allora modifica dovrà essere solo locale (a parte forse aggiunta e rimozione annotation assertions)

class IriBuilderDialog(QtWidgets.QDialog, HasWidgetSystem):

    sgnIRIAccepted = QtCore.pyqtSignal(OntologyEntityNode)
    sgnIRIRejected = QtCore.pyqtSignal(OntologyEntityNode)


    emptyString = ''

    def __init__(self,node,diagram,session):
        """
        Initialize the IRI builder dialog.
        :type diagram: Diagram
        :type node: ConceptNode|AttributeNode|RoleNode|IndividualNode
        :type session: Session
        """
        super().__init__(session)
        self.diagram = diagram
        self.session = session
        connect(self.sgnIRIAccepted,self.diagram.doAddOntologyEntityNode)

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
        comboBoxLabel = IRIDialogsWidgetFactory.getIRIPrefixComboBoxLabel(self)
        self.addWidget(comboBoxLabel)

        combobox = IRIDialogsWidgetFactory.getIRIPrefixComboBox(self)
        combobox.clear()
        combobox.addItem(self.emptyString)
        # combobox.addItems([x+':' for x in self.project.getManagedPrefixes()])
        combobox.addItems([x + ':' + '  <' + y + '>' for x, y in self.project.prefixDictItems()])
        if shortest:
            combobox.setCurrentText(shortest.prefix + ':' + '  <' + self.project.getNamespace(shortest.prefix) + '>')
        else:
            ontPrefix = self.project.ontologyPrefix
            if ontPrefix:
                combobox.setCurrentText(ontPrefix + ':' + '  <' + self.project.getNamespace(ontPrefix) + '>')
            else:
                combobox.setCurrentText(self.emptyString)
        self.addWidget(combobox)

        inputLabel = IRIDialogsWidgetFactory.getInputLabel(self)
        self.addWidget(inputLabel)

        inputField = IRIDialogsWidgetFactory.getInputField(self)
        if shortest:
            inputField.setText(shortest.suffix)
        elif self.iri:
            inputField.setText(str(self.iri))
        else:
            inputField.setText('')
        self.addWidget(inputField)

        fullIriLabel = IRIDialogsWidgetFactory.getFullIRILabel(self)
        self.addWidget(fullIriLabel)

        fullIriField = IRIDialogsWidgetFactory.getFullIRIField(self)
        if self.iri:
            fullIriField.setText(str(self.iri))
        else:
            ontPrefix = self.project.ontologyPrefix
            if ontPrefix:
                fullIriField.setText(self.project.getNamespace(ontPrefix))
            else:
                fullIriField.setText('')
        self.addWidget(fullIriField)

        ###########################

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('iri_prefix_combobox_label'), self.widget('iri_prefix_switch'))
        formlayout.addRow(self.widget('input_field_label'), self.widget('iri_input_field'))
        formlayout.addRow(self.widget('full_iri_label'), self.widget('full_iri_field'))

        '''
        if isinstance(node, AttributeNode):
            functLabel = IRIDialogsWidgetFactory.getFunctionalLabel(self)
            self.addWidget(functLabel)
            functCheckBox = IRIDialogsWidgetFactory.getFunctionalCheckBox(self)
            self.addWidget(functCheckBox)
            formlayout.addRow(self.widget('functional_label'), self.widget('functional_checkbox'))
        '''

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
        mainWidget = QtWidgets.QTabWidget(self, objectName='main_widget')
        iriTabLabel = 'IRI'

        #############################################
        # PREDEFINED DATATYPE TAB
        #################################
        if isinstance(self.node, ValueDomainNode):
            comboBoxLabel = IRIDialogsWidgetFactory.getPredefinedDatatypeComboBoxLabel(self)
            self.addWidget(comboBoxLabel)

            combobox = IRIDialogsWidgetFactory.getPredefinedDatatypeComboBox(self)
            combobox.clear()
            combobox.addItem(self.emptyString)
            sortedItems = sorted(self.project.getDatatypeIRIs(), key=str)
            combobox.addItems([str(x) for x in sortedItems])
            if self.iri and self.iri in self.project.getDatatypeIRIs():
                combobox.setCurrentText(str(self.iri))
            else:
                combobox.setCurrentText(self.emptyString)
            self.addWidget(combobox)

            formlayout = QtWidgets.QFormLayout()
            formlayout.addRow(self.widget('datatype_combobox_label'), self.widget('datatype_switch'))
            widget = QtWidgets.QWidget()
            widget.setLayout(formlayout)
            widget.setObjectName('predefined_datatype_widget')
            self.addWidget(widget)
            mainWidget.addTab(self.widget('predefined_datatype_widget'), QtGui.QIcon(':/icons/24/ic_settings_black'),
                              'Predefined Datatypes')
            iriTabLabel = 'Custom Datatype'

        mainWidget.addTab(self.widget('iri_widget'), QtGui.QIcon(':/icons/24/ic_settings_black'),
                      iriTabLabel)

        self.addWidget(mainWidget)
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
        combobox.addItem(self.emptyString)
        # combobox.addItems([x+':' for x in self.project.getManagedPrefixes()])
        combobox.addItems([x + ':' + '  <' + y + '>' for x, y in self.project.prefixDictItems()])
        if shortest:
            combobox.setCurrentText(shortest.prefix + ':' + '  <' + self.project.getNamespace(shortest.prefix) + '>')
        else:
            ontPrefix = self.project.ontologyPrefix
            if ontPrefix:
                combobox.setCurrentText(ontPrefix + ':' + '  <' + self.project.getNamespace(ontPrefix) + '>')
            else:
                combobox.setCurrentText(self.emptyString)

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

        '''
        if isinstance(self.node, AttributeNode):
            functCheckBox = self.widget('functional_checkbox')
            if self.node.iri and self.node.iri.functional:
                functCheckBox.setChecked(True)
            else:
                functCheckBox.setChecked(False)
        '''

        #############################################
        # PREDEFINED DATATYPE TAB
        #################################
        if isinstance(self.node, ValueDomainNode):
            combobox = self.widget('datatype_switch')
            combobox.clear()
            combobox.addItem(self.emptyString)
            sortedItems = sorted(self.project.getDatatypeIRIs(), key=str)
            combobox.addItems([str(x) for x in sortedItems])
            if self.iri and self.iri in self.project.getDatatypeIRIs():
                combobox.setCurrentText(str(self.iri))
            else:
                combobox.setCurrentText(self.emptyString)

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
            activeTab = self.widget('main_widget').currentWidget()
            if activeTab is self.widget('iri_widget'):
                inputIriString = self.widget('full_iri_field').value()
                self.project.isValidIdentifier(inputIriString)
                if self.iri:
                    if not str(self.iri) == inputIriString:
                        command = CommandChangeIRIOfNode(self.project, self.node, inputIriString, str(self.iri))
                        self.session.undostack.beginMacro('Node {} set IRI <{}> '.format(self.node.id,inputIriString))
                        if command:
                            self.session.undostack.push(command)
                        self.session.undostack.endMacro()
                else:
                    inputIri = self.project.getIRI(inputIriString, addLabelFromSimpleName=True)
                    self.node.iri = inputIri
                    self.sgnIRIAccepted.emit(self.node)
                    if self.node.diagram:
                        self.node.doUpdateNodeLabel()
                super().accept()
            elif activeTab is self.widget('predefined_datatype_widget'):
                currText = str(self.widget('datatype_switch').currentText())
                if currText==self.emptyString:
                    errorDialog = QtWidgets.QErrorMessage(parent=self)
                    errorDialog.showMessage('Please select a non-empty element from the combobox')
                    errorDialog.setWindowModality(QtCore.Qt.ApplicationModal)
                    errorDialog.show()
                    errorDialog.raise_()
                    errorDialog.activateWindow()
                else:
                    if self.iri:
                        if not str(self.iri) == currText:
                            command = CommandChangeIRIOfNode(self.project, self.node, currText, str(self.iri))
                            self.session.undostack.beginMacro('Node {} set IRI <{}> '.format(self.node.id, currText))
                            if command:
                                self.session.undostack.push(command)
                            self.session.undostack.endMacro()
                    else:
                        inputIri = self.project.getIRI(currText)
                        self.node.iri = inputIri
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

    sgnIRISwitch = QtCore.pyqtSignal(IRI,IRI)
    sgnReHashIRI = QtCore.pyqtSignal(IRI, str)

    def __init__(self,iri,session):
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

        #############################################
        # IRI TAB
        #################################
        comboBoxLabel = IRIDialogsWidgetFactory.getIRIPrefixComboBoxLabel(self)
        self.addWidget(comboBoxLabel)

        combobox = IRIDialogsWidgetFactory.getIRIPrefixComboBox(self)
        combobox.clear()
        combobox.addItem(self.noPrefixString)
        # combobox.addItems([x+':' for x in self.project.getManagedPrefixes()])
        combobox.addItems([x + ':' + '  <' + y + '>' for x, y in self.project.prefixDictItems()])
        if shortest:
            combobox.setCurrentText(shortest.prefix+':'+'  <'+self.project.getNamespace(shortest.prefix)+'>')
        else:
            ontPrefix = self.project.ontologyPrefix
            if ontPrefix:
                combobox.setCurrentText(ontPrefix + ':' + '  <' + self.project.getNamespace(ontPrefix) + '>')
            else:
                combobox.setCurrentText(self.emptyString)
        self.addWidget(combobox)

        inputLabel = IRIDialogsWidgetFactory.getInputLabel(self)
        self.addWidget(inputLabel)

        inputField = IRIDialogsWidgetFactory.getInputField(self)
        if shortest:
            inputField.setText(shortest.suffix)
        else:
            inputField.setText(str(iri))
        self.addWidget(inputField)

        fullIriLabel = IRIDialogsWidgetFactory.getFullIRILabel(self)
        self.addWidget(fullIriLabel)

        fullIriField = IRIDialogsWidgetFactory.getFullIRIField(self)
        fullIriField.setText(str(iri))
        self.addWidget(fullIriField)

        saveBtn = QtWidgets.QPushButton('Save', objectName='save_iri_button')
        connect(saveBtn.clicked, self.saveIRI)
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
        table = IRIDialogsWidgetFactory.getAnnotationAssertionsTable(self)
        table.clear()
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
        doneBtn = QtWidgets.QPushButton('Done', objectName='done_button')
        confirmation.addButton(doneBtn, QtWidgets.QDialogButtonBox.AcceptRole)
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
                      'Annotations')

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
        combobox.addItem(self.noPrefixString)
        # combobox.addItems([x+':' for x in self.project.getManagedPrefixes()])
        combobox.addItems([x + ':' + '  <' + y + '>' for x, y in self.project.prefixDictItems()])
        if shortest:
            combobox.setCurrentText(shortest.prefix + ':' + '  <' + self.project.getNamespace(shortest.prefix) + '>')
        else:
            ontPrefix = self.project.ontologyPrefix
            if ontPrefix:
                combobox.setCurrentText(ontPrefix + ':' + '  <' + self.project.getNamespace(ontPrefix) + '>')
            else:
                combobox.setCurrentText(self.emptyString)

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
            valueItem = QtWidgets.QTableWidgetItem(str(assertion.getObjectResourceString(True)))
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
        valueItem = QtWidgets.QTableWidgetItem(str(assertion.getObjectResourceString(True)))
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
        commands = []
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                removedItem = table.item(row, 0)
                assertion = removedItem.data(Qt.UserRole)
                command = CommandIRIRemoveAnnotation(self.project, self.iri, assertion)
                commands.append(command)
                #self.iri.removeAnnotationAssertion(assertion)

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
    def editAnnotation(self, _):
        table = self.widget('annotations_table_widget')
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
        table = self.widget('annotations_table_widget')
        rowcount = table.rowCount()
        for row in range(0,rowcount):
            propItem = table.item(row, 0)
            itemAssertion = propItem.data(Qt.UserRole)
            if itemAssertion is assertion:
                newPropertyItem = QtWidgets.QTableWidgetItem(str(assertion.assertionProperty))
                newPropertyItem.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                newPropertyItem.setData(Qt.UserRole, assertion)
                table.setItem(row, 0, newPropertyItem)
                valueItem = QtWidgets.QTableWidgetItem(str(assertion.getObjectResourceString(True)))
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
            fullIRIString = self.widget('full_iri_field').value()
            existIRI = self.project.existIRI(fullIRIString)
            if existIRI:
                print('IRI corresponding to string {} already exists'.format(fullIRIString))
                newIRI = self.project.getIRI(fullIRIString, addLabelFromSimpleName=True)
                if not newIRI is self.iri:
                    oldIRI = self.iri
                    self.iri = newIRI
                    self.redraw()
                    command = CommandIRIRefactor(self.project, self.iri, oldIRI)
                    self.session.undostack.beginMacro('IRI <{}> refactor'.format(self.iri))
                    if command:
                        self.session.undostack.push(command)
                    self.session.undostack.endMacro()
            else:
                print('IRI corresponding to string {} does not exist'.format(fullIRIString))
                if not self.iri.namespace == fullIRIString:
                    oldStr = self.iri.namespace
                    command = CommandChangeIRIIdentifier(self.project, self.iri, fullIRIString, oldStr)
                    self.session.undostack.beginMacro('IRI <{}> refactor'.format(fullIRIString))
                    if command:
                        self.session.undostack.push(command)
                    self.session.undostack.endMacro()
        except IllegalNamespaceError:
            errorDialog = QtWidgets.QErrorMessage(parent=self)
            errorDialog.showMessage('The input string cannot be used to build a valid IRI')
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

class ConstrainingFacetDialog(QtWidgets.QDialog, HasWidgetSystem):

    sgnFacetAccepted = QtCore.pyqtSignal(FacetNode)
    sgnFacetRejected = QtCore.pyqtSignal(FacetNode)

    sgnFacetChanged = QtCore.pyqtSignal(FacetNode,Facet)

    emptyString = ''

    def __init__(self,node,diagram,session):
        """
        Initialize the Facet builder dialog.
        :type diagram: Diagram
        :type node: FacetNode
        :type session: Session
        """
        super().__init__(session)
        self.diagram = diagram
        self.session = session
        connect(self.sgnFacetAccepted,self.diagram.doAddOntologyFacetNode)

        self.node = node
        self.facet = None
        if self.node.facet:
            self.facet = self.node.facet
        self.project = diagram.project

        #############################################
        # FACET TAB
        #################################
        comboBoxLabel = IRIDialogsWidgetFactory.getPredefinedConstrainingFacetComboBoxLabel(self)
        self.addWidget(comboBoxLabel)

        combobox = IRIDialogsWidgetFactory.getPredefinedConstrainingFacetComboBox(self)
        combobox.clear()
        combobox.addItem(self.emptyString)
        # combobox.addItems([x+':' for x in self.project.getManagedPrefixes()])
        sortedItems = sorted(self.project.constrainingFacets, key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if self.facet:
            combobox.setCurrentText(str(self.facet.constrainingFacet))
        else:
            combobox.setCurrentText(self.emptyString)
        self.addWidget(combobox)

        lfLabel = IRIDialogsWidgetFactory.getLexicalFormLabel(self)
        self.addWidget(lfLabel)

        lfTextArea= IRIDialogsWidgetFactory.getLexicalFormTextArea(self)
        if self.facet:
            lfTextArea.setText(str(self.facet.literal.lexicalForm))
        else:
            lfTextArea.setText(self.emptyString)
        self.addWidget(lfTextArea)

        comboBoxLabel = IRIDialogsWidgetFactory.getPredefinedDatatypeComboBoxLabel(self)
        self.addWidget(comboBoxLabel)

        combobox = IRIDialogsWidgetFactory.getPredefinedDatatypeComboBox(self)
        combobox.clear()
        combobox.addItem(self.emptyString)
        sortedItems = sorted(self.project.getDatatypeIRIs(), key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if self.facet and self.facet.literal.datatype and self.facet.literal.datatype in self.project.getDatatypeIRIs():
            combobox.setCurrentText(str(self.facet.literal.datatype))
        else:
            combobox.setCurrentText(self.emptyString)
        self.addWidget(combobox)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('constraining_facet_combobox_label'), self.widget('constraining_facet_switch'))
        formlayout.addRow(self.widget('lexical_form_label'), self.widget('lexical_form_area'))
        formlayout.addRow(self.widget('datatype_combobox_label'), self.widget('datatype_switch'))

        widget = QtWidgets.QWidget()
        widget.setLayout(formlayout)
        widget.setObjectName('facet_widget')
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
        mainWidget = QtWidgets.QTabWidget(self, objectName='main_widget')
        mainWidget.addTab(self.widget('facet_widget'), QtGui.QIcon(':/icons/24/ic_settings_black'),
                      'Facet')
        self.addWidget(mainWidget)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(740, 420)
        self.setWindowTitle('Facet Builder')

        #connect(inputField.textEdited, self.onInputChanged)
        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def redraw(self):

        combobox = self.widget('constraining_facet_switch')
        combobox.clear()
        combobox.addItem(self.emptyString)
        # combobox.addItems([x+':' for x in self.project.getManagedPrefixes()])
        sortedItems = sorted(self.project.constrainingFacets, key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if self.facet:
            combobox.setCurrentText(str(self.facet.constrainingFacet))
        else:
            combobox.setCurrentText(self.emptyString)
        self.addWidget(combobox)

        lfTextArea = self.widget('lexical_form_area')
        if self.facet:
            lfTextArea.setText(str(self.facet.literal.lexicalForm))
        else:
            lfTextArea.setText(self.emptyString)

        combobox = self.widget('datatype_switch')
        combobox.clear()
        combobox.addItem(self.emptyString)
        sortedItems = sorted(self.project.getDatatypeIRIs(), key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if self.facet and self.facet.literal.datatype and self.facet.literal.datatype in self.project.getDatatypeIRIs():
            combobox.setCurrentText(str(self.facet.literal.datatype))
        else:
            combobox.setCurrentText(self.emptyString)
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
            currDataType = str(self.widget('datatype_switch').currentText())
            literal = Literal(lexForm, self.project.getIRI(currDataType))
            facet = Facet(self.project.getIRI(currConstrFacet), literal)
            if self.facet:
                command = CommandChangeFacetOfNode(self.project, self.node, facet, self.facet)
                self.session.undostack.beginMacro('Node {} modify Facet '.format(self.node.id))
                if command:
                    self.session.undostack.push(command)
                self.session.undostack.endMacro()
            else:
                self.node.facet = facet
                self.sgnFacetAccepted.emit(self.node)
                if self.node.diagram:
                    self.node.doUpdateNodeLabel()
            super().accept()
        except RuntimeError as e:
            errorDialog = QtWidgets.QErrorMessage(parent=self)
            errorDialog.showMessage(str(e))
            errorDialog.setWindowModality(QtCore.Qt.ApplicationModal)
            errorDialog.show()
            errorDialog.raise_()
            errorDialog.activateWindow()

    @QtCore.pyqtSlot()
    def reject(self):
        self.sgnFacetRejected.emit(self.node)
        super().reject()

class LiteralDialog(QtWidgets.QDialog, HasWidgetSystem):

    sgnLiteralAccepted = QtCore.pyqtSignal(LiteralNode)
    sgnLiteralRejected = QtCore.pyqtSignal(LiteralNode)

    sgnLiteralChanged = QtCore.pyqtSignal(LiteralNode,Literal)

    emptyString = ''

    def __init__(self,node,diagram,session):
        """
        Initialize the Literal builder dialog.
        :type diagram: Diagram
        :type node: LiteralNode
        :type session: Session
        """
        super().__init__(session)
        self.diagram = diagram
        self.session = session
        connect(self.sgnLiteralAccepted,self.diagram.doAddOntologyLiteralNode)

        self.node = node
        self.literal = None
        if self.node._literal:
            self.literal = self.node._literal
        self.project = diagram.project

        #############################################
        # LITERAL TAB
        #################################
        comboBoxLabel = IRIDialogsWidgetFactory.getPredefinedDatatypeComboBoxLabel(self)
        self.addWidget(comboBoxLabel)

        combobox = IRIDialogsWidgetFactory.getPredefinedDatatypeComboBox(self)
        combobox.clear()
        combobox.addItem(self.emptyString)
        # combobox.addItems([x+':' for x in self.project.getManagedPrefixes()])
        sortedItems = sorted(self.project.getDatatypeIRIs(), key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if self.literal and self.literal.datatype:
            combobox.setCurrentText(str(self.literal.datatype))
        else:
            combobox.setCurrentText(self.emptyString)
        self.addWidget(combobox)
        connect(combobox.currentIndexChanged, self.onTypeSwitched)

        lfLabel = IRIDialogsWidgetFactory.getLexicalFormLabel(self)
        self.addWidget(lfLabel)

        lfTextArea= IRIDialogsWidgetFactory.getLexicalFormTextArea(self)
        if self.literal:
            lfTextArea.setText(str(self.literal.lexicalForm))
        else:
            lfTextArea.setText(self.emptyString)
        self.addWidget(lfTextArea)

        comboBoxLabel = QtWidgets.QLabel(self, objectName='lang_combobox_label')
        comboBoxLabel.setFont(Font('Roboto', 12))
        comboBoxLabel.setText('Lang')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='lang_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(True)
        combobox.addItem(self.emptyString)
        combobox.addItems([x for x in self.project.getLanguages()])
        if self.literal and self.literal.language:
            combobox.setCurrentText(str(self.literal.language))
        else:
            combobox.setCurrentText(self.emptyString)
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

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self, objectName='confirmation_widget')
        confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setContentsMargins(10, 0, 10, 10)
        confirmation.setFont(Font('Roboto', 12))
        self.addWidget(confirmation)

        #############################################
        # MAIN WIDGET
        #################################
        mainWidget = QtWidgets.QTabWidget(self, objectName='main_widget')
        mainWidget.addTab(self.widget('literal_widget'), QtGui.QIcon(':/icons/24/ic_settings_black'),
                      'Literal')
        self.addWidget(mainWidget)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(740, 420)
        self.setWindowTitle('Literal Builder')

        #connect(inputField.textEdited, self.onInputChanged)
        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def redraw(self):
        combobox = self.widget('datatype_switch')
        combobox.clear()
        combobox.addItem(self.emptyString)
        sortedItems = sorted(self.project.getDatatypeIRIs(), key=str)
        combobox.addItems([str(x) for x in sortedItems])
        if self.literal and self.literal.datatype:
            combobox.setCurrentText(str(self.literal.datatype))
        else:
            combobox.setCurrentText(self.emptyString)
        self.addWidget(combobox)

        lfTextArea = self.widget('lexical_form_area')
        if self.literal:
            lfTextArea.setText(str(self.literal.literal.lexicalForm))
        else:
            lfTextArea.setText(self.emptyString)

        combobox = self.widget('lang_switch')
        combobox.clear()
        combobox.addItem(self.emptyString)
        combobox.addItems([x for x in self.project.getLanguages()])
        if self.literal and self.literal.language:
            combobox.setCurrentText(str(self.literal.language))
        else:
            combobox.setCurrentText(self.emptyString)


    @QtCore.pyqtSlot(int)
    def onTypeSwitched(self, index):
        typeIRI = str(self.widget('datatype_switch').itemText(index))
        if not self.project.canAddLanguageTag(typeIRI):
            '''
            model = self.widget('lang_switch').model()
            allItems = [model.item(i) for i in range(model.rowCount())]
            for item in allItems:
                #item.setBackground(QtGui.QColor('grey'))

            palette = self.widget('lang_switch').palette()
            palette.setColor(QtGui.QPalette.Active,QtGui.QPalette.Button,QtGui.QColor('red'))
            palette.setColor(QtGui.QPalette.Inactive, QtGui.QPalette.Button, QtGui.QColor('pink'))
            self.widget('lang_switch').setPalette(palette)
            '''

            self.widget('lang_switch').setStyleSheet("background:#808080");
            self.widget('lang_switch').setEnabled(False)
        else:
            self.widget('lang_switch').setStyleSheet("background:#FFFFFF");
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
            literal = Literal(lexForm, datatypeIRI,language)

            if self.literal:
                command = CommandChangeLiteralOfNode(self.project, self.node, literal, self.literal)
                self.session.undostack.beginMacro('Node {} modify Literal '.format(self.node.id))
                if command:
                    self.session.undostack.push(command)
                self.session.undostack.endMacro()
            else:
                self.node._literal = literal
                self.sgnLiteralAccepted.emit(self.node)
                if self.node.diagram:
                    self.node.doUpdateNodeLabel()
            super().accept()
        except IllegalLiteralError as e:
            errorDialog = QtWidgets.QErrorMessage(parent=self)
            errorDialog.showMessage(str(e))
            errorDialog.setWindowModality(QtCore.Qt.ApplicationModal)
            errorDialog.show()
            errorDialog.raise_()
            errorDialog.activateWindow()

    @QtCore.pyqtSlot()
    def reject(self):
        self.sgnLiteralRejected.emit(self.node)
        super().reject()