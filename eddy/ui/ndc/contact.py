from PyQt5 import QtCore, QtWidgets

from eddy.core.ndc import addContactToStore
from eddy.core.common import HasWidgetSystem
from eddy.core.functions.signals import connect
from eddy.core.owl import IRI
from eddy.ui.fields import StringField


class ContactBuilderDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    Subclass of `QtWidgets.QDialog` used to define annotation assertions.
    """
    sgnContactAccepted = QtCore.pyqtSignal()
    sgnContactRejected = QtCore.pyqtSignal()

    emptyString = ''

    def __init__(self,session):
        """
        Initialize the contact builder dialog.
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

        iri = QtWidgets.QLabel(self, objectName='contact_iri_label')
        iri.setText('IRI')
        self.addWidget(iri)

        iriField = StringField(self, objectName='contact_iri_field')
        self.addWidget(iriField)

        name = QtWidgets.QLabel(self, objectName='contact_name_label')
        name.setText('Name')
        self.addWidget(name)

        ITnameField = StringField(self, objectName='contact_ITname_field')
        ITnameField.setPlaceholderText('@it')
        self.addWidget(ITnameField)

        noLabel = QtWidgets.QLabel(self, objectName='no_label')
        self.addWidget(noLabel)

        ENnameField = StringField(self, objectName='contact_ENname_field')
        ENnameField.setPlaceholderText('@en')
        self.addWidget(ENnameField)

        email = QtWidgets.QLabel(self, objectName='contact_email_label')
        email.setText('Email')
        self.addWidget(email)

        emailField = StringField(self, objectName='contact_email_field')
        self.addWidget(emailField)

        telephone = QtWidgets.QLabel(self, objectName='contact_telephone_label')
        telephone.setText('Telephone')
        self.addWidget(telephone)

        telephoneField = StringField(self, objectName='contact_telephone_field')
        self.addWidget(telephoneField)

        layout = QtWidgets.QFormLayout()
        layout.addRow(self.widget('contact_iri_label'), self.widget('contact_iri_field'))
        layout.addRow(self.widget('contact_name_label'), self.widget('contact_ITname_field'))
        layout.addRow(self.widget('no_label'), self.widget('contact_ENname_field'))
        layout.addRow(self.widget('contact_email_label'), self.widget('contact_email_field'))
        layout.addRow(self.widget('contact_telephone_label'), self.widget('contact_telephone_field'))

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('contact_widget')
        self.addWidget(widget)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.widget('contact_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)

        self.setMinimumSize(740, 380)
        self.setWindowTitle('Add Contact')
        #self.redraw()

    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot()
    def accept(self):
        iri = self.widget('contact_iri_field').text()
        nameIT = self.widget('contact_ITname_field').text()
        nameEN = self.widget('contact_ENname_field').text()
        email = self.widget('contact_email_field').text()
        telephone = self.widget('contact_telephone_field').text()
        addContactToStore(iri, nameIT, nameEN, email, telephone)
        self.sgnContactAccepted.emit()
        super().accept()
