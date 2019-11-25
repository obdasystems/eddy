from PyQt5 import QtWidgets, QtCore, QtGui
from eddy.core.common import HasWidgetSystem

from eddy.core.owl import IRI

from eddy.core.functions.signals import connect
from eddy.ui.fields import ComboBox, StringField

from eddy.core.datatypes.qt import Font


class IriBuilderDialog(QtWidgets.QDialog, HasWidgetSystem):

    noPrefixString = ''

    def __init__(self,node,diagram,session):
        """
        Initialize the IRI builder dialog.
        :type session: Session
        :type diagram: Diagram
        :type node: ConceptNode|AttributeNode|RoleNode|IndividualNode
        """
        super().__init__(session)
        self.diagram = diagram
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
        combobox.addItems([x+':' for x in self.project.getManagedPrefixes()])
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
        fullIri = '{}{}'.format(self.resolvePrefix(prefix),input)
        self.widget('full_iri_field').setValue(fullIri)

    @QtCore.pyqtSlot()
    def accept(self):
        iri = self.project.getIRI(self.widget('full_iri_field').value())
        self.node.iri = iri
        super().accept()




    #############################################
    #   INTERFACE
    #################################

    def resolvePrefix(self,prefixStr):
        if prefixStr==self.noPrefixString:
            return ''
        else:
            return self.project.getPrefixResolution(prefixStr[:-1])