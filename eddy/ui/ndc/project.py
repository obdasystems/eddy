from PyQt5 import QtCore, QtWidgets

from eddy.core.ndc import addProjectToStore
from eddy.core.common import HasWidgetSystem
from eddy.core.functions.signals import connect
from eddy.core.owl import IRI
from eddy.ui.fields import StringField


class ProjectBuilderDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    Subclass of `QtWidgets.QDialog` used to define annotation assertions.
    """
    sgnProjectAccepted = QtCore.pyqtSignal()
    sgnProjectRejected = QtCore.pyqtSignal()

    emptyString = ''

    def __init__(self,session):
        """
        Initialize the project builder dialog.
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

        iri = QtWidgets.QLabel(self, objectName='project_iri_label')
        iri.setText('IRI')
        self.addWidget(iri)

        iriField = StringField(self, objectName='project_iri_field')
        self.addWidget(iriField)

        name = QtWidgets.QLabel(self, objectName='project_name_label')
        name.setText('Name')
        self.addWidget(name)

        ITnameField = StringField(self, objectName='project_ITname_field')
        ITnameField.setPlaceholderText('@it')
        self.addWidget(ITnameField)

        noLabel = QtWidgets.QLabel(self, objectName='no_label')
        self.addWidget(noLabel)

        ENnameField = StringField(self, objectName='project_ENname_field')
        ENnameField.setPlaceholderText('@en')
        self.addWidget(ENnameField)

        layout = QtWidgets.QFormLayout()
        layout.addRow(self.widget('project_iri_label'), self.widget('project_iri_field'))
        layout.addRow(self.widget('project_name_label'), self.widget('project_ITname_field'))
        layout.addRow(self.widget('no_label'), self.widget('project_ENname_field'))

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('project_widget')
        self.addWidget(widget)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.widget('project_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)

        self.setMinimumSize(740, 380)
        self.setWindowTitle('Add Project')
        #self.redraw()

    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot()
    def accept(self):
        iri = self.widget('project_iri_field').text()
        nameIT = self.widget('project_ITname_field').text()
        nameEN = self.widget('project_ENname_field').text()
        addProjectToStore(iri, nameIT, nameEN)
        self.sgnProjectAccepted.emit()
        super().accept()
