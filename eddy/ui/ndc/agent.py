from PyQt5 import QtCore, QtWidgets

from eddy.core.ndc import addAgentToStore
from eddy.core.common import HasWidgetSystem
from eddy.core.functions.signals import connect
from eddy.core.owl import IRI
from eddy.ui.fields import StringField


class AgentBuilderDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    Subclass of `QtWidgets.QDialog` used to define annotation assertions.
    """
    sgnAgentAccepted = QtCore.pyqtSignal()
    sgnAgentRejected = QtCore.pyqtSignal()

    emptyString = ''

    def __init__(self,session):
        """
        Initialize the agent builder dialog.
        :type session: Session
        """
        super().__init__(session)
        self.session = session
        self.project = session.project

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        confirmation.setObjectName('confirmation_widget')
        confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setContentsMargins(10, 0, 10, 10)
        self.addWidget(confirmation)
        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

        #############################################
        # MAIN WIDGET
        #################################

        iri = QtWidgets.QLabel(self, objectName='agent_iri_label')
        iri.setText('IRI')
        self.addWidget(iri)

        iriField = StringField(self, objectName='agent_iri_field')
        self.addWidget(iriField)

        name = QtWidgets.QLabel(self, objectName='agent_name_label')
        name.setText('Name')
        self.addWidget(name)

        ITnameField = StringField(self, objectName='agent_ITname_field')
        ITnameField.setPlaceholderText('@it')
        self.addWidget(ITnameField)

        noLabel = QtWidgets.QLabel(self, objectName='no_label')
        self.addWidget(noLabel)

        ENnameField = StringField(self, objectName='agent_ENname_field')
        ENnameField.setPlaceholderText('@en')
        self.addWidget(ENnameField)

        identifier = QtWidgets.QLabel(self, objectName='agent_id_label')
        identifier.setText('Identifier')
        self.addWidget(identifier)

        identifierField = StringField(self, objectName='agent_id_field')
        self.addWidget(identifierField)

        layout = QtWidgets.QFormLayout()
        layout.addRow(self.widget('agent_iri_label'), self.widget('agent_iri_field'))
        layout.addRow(self.widget('agent_name_label'), self.widget('agent_ITname_field'))
        layout.addRow(self.widget('no_label'), self.widget('agent_ENname_field'))
        layout.addRow(self.widget('agent_id_label'), self.widget('agent_id_field'))

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('agent_widget')
        self.addWidget(widget)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.widget('agent_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)

        self.setMinimumSize(740, 380)
        self.setWindowTitle('Add Agent')
        #self.redraw()

    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot()
    def accept(self):
        iri = self.widget('agent_iri_field').text()
        nameIT = self.widget('agent_ITname_field').text()
        nameEN = self.widget('agent_ENname_field').text()
        id = self.widget('agent_id_field').text()
        addAgentToStore(iri, nameIT, nameEN, id)
        self.sgnAgentAccepted.emit()
        super().accept()

