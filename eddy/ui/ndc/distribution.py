from PyQt5 import QtCore, QtWidgets

from eddy.core.ndc import addDistributionToStore
from eddy.core.common import HasWidgetSystem
from eddy.core.functions.signals import connect
from eddy.core.owl import IRI
from eddy.ui.fields import StringField


class DistributionBuilderDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    Subclass of `QtWidgets.QDialog` used to define annotation assertions.
    """
    sgnDistributionAccepted = QtCore.pyqtSignal()
    sgnDistributionRejected = QtCore.pyqtSignal()

    emptyString = ''

    def __init__(self,session):
        """
        Initialize the distribution builder dialog.
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

        iri = QtWidgets.QLabel(self, objectName='distribution_iri_label')
        iri.setText('IRI')
        self.addWidget(iri)

        iriField = StringField(self, objectName='distribution_iri_field')
        self.addWidget(iriField)

        title = QtWidgets.QLabel(self, objectName='distribution_title_label')
        title.setText('Title')
        self.addWidget(title)

        ITtitleField = StringField(self, objectName='distribution_ITtitle_field')
        ITtitleField.setPlaceholderText('@it')
        self.addWidget(ITtitleField)

        noLabel = QtWidgets.QLabel(self, objectName='no_label')
        self.addWidget(noLabel)

        ENtitleField = StringField(self, objectName='distribution_ENtitle_field')
        ENtitleField.setPlaceholderText('@en')
        self.addWidget(ENtitleField)

        description = QtWidgets.QLabel(self, objectName='distribution_description_label')
        description.setText('Description')
        self.addWidget(description)

        ITdescriptionField = StringField(self, objectName='distribution_ITdescription_field')
        ITdescriptionField.setPlaceholderText('@it')
        self.addWidget(ITdescriptionField)

        ENdescriptionField = StringField(self, objectName='distribution_ENdescription_field')
        ENdescriptionField.setPlaceholderText('@en')
        self.addWidget(ENdescriptionField)

        format = QtWidgets.QLabel(self, objectName='distribution_format_label')
        format.setText('Format')
        self.addWidget(format)

        formatField = StringField(self, objectName='distribution_format_field')
        self.addWidget(formatField)

        license = QtWidgets.QLabel(self, objectName='distribution_license_label')
        license.setText('License')
        self.addWidget(license)

        licenseField = StringField(self, objectName='distribution_license_field')
        self.addWidget(licenseField)

        accessURL = QtWidgets.QLabel(self, objectName='distribution_accessURL_label')
        accessURL.setText('Access URL')
        self.addWidget(accessURL)

        accessURLField = StringField(self, objectName='distribution_accessURL_field')
        self.addWidget(accessURLField)

        downloadURL = QtWidgets.QLabel(self, objectName='distribution_downloadURL_label')
        downloadURL.setText('Download URL')
        self.addWidget(downloadURL)

        downloadURLField = StringField(self, objectName='distribution_downloadURL_field')
        self.addWidget(downloadURLField)

        layout = QtWidgets.QFormLayout()
        layout.addRow(self.widget('distribution_iri_label'), self.widget('distribution_iri_field'))
        layout.addRow(self.widget('distribution_title_label'), self.widget('distribution_ITtitle_field'))
        layout.addRow(self.widget('no_label'), self.widget('distribution_ENtitle_field'))
        layout.addRow(self.widget('distribution_description_label'),
                      self.widget('distribution_ITdescription_field'))
        layout.addRow(self.widget('no_label'), self.widget('distribution_ENdescription_field'))
        layout.addRow(self.widget('distribution_format_label'), self.widget('distribution_format_field'))
        layout.addRow(self.widget('distribution_license_label'), self.widget('distribution_license_field'))
        layout.addRow(self.widget('distribution_accessURL_label'), self.widget('distribution_accessURL_field'))
        layout.addRow(self.widget('distribution_downloadURL_label'), self.widget('distribution_downloadURL_field'))

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('distribution_widget')
        self.addWidget(widget)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.widget('distribution_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)

        self.setMinimumSize(740, 380)
        self.setWindowTitle('Add Distribution')
        #self.redraw()

    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot()
    def accept(self):
        iri = self.widget('distribution_iri_field').text()
        titleIT = self.widget('distribution_ITtitle_field').text()
        titleEN = self.widget('distribution_ENtitle_field').text()
        descriptionIT = self.widget('distribution_ITdescription_field').text()
        descriptionEN = self.widget('distribution_ENdescription_field').text()
        format = self.widget('distribution_format_field').text()
        license = self.widget('distribution_license_field').text()
        accessURL = self.widget('distribution_accessURL_field').text()
        downloadURL = self.widget('distribution_downloadURL_field').text()
        addDistributionToStore(iri, titleIT, titleEN, descriptionIT, descriptionEN, format, license, accessURL, downloadURL)
        self.sgnDistributionAccepted.emit()
        super().accept()
