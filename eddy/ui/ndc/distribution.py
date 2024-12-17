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

from PyQt5 import (
    QtCore,
    QtWidgets,
)
from rdflib import (
    Literal,
    URIRef,
)

from eddy.core.common import HasWidgetSystem
from eddy.core.functions.signals import connect
from eddy.core.ndc import (
    Distribution,
    NDCDataset,
)
from eddy.ui.fields import StringField


class DistributionBuilderDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    Subclass of `QtWidgets.QDialog` used to define annotation assertions.
    """

    def __init__(self, parent: QtWidgets.QWidget, dataset: NDCDataset) -> None:
        """
        Initialize the distribution builder dialog.
        """
        super().__init__(parent)
        self.dataset = dataset

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
        layout.addRow(self.widget('distribution_title_label'),
                      self.widget('distribution_ITtitle_field'))
        layout.addRow(self.widget('no_label'), self.widget('distribution_ENtitle_field'))
        layout.addRow(self.widget('distribution_description_label'),
                      self.widget('distribution_ITdescription_field'))
        layout.addRow(self.widget('no_label'), self.widget('distribution_ENdescription_field'))
        layout.addRow(self.widget('distribution_format_label'),
                      self.widget('distribution_format_field'))
        layout.addRow(self.widget('distribution_license_label'),
                      self.widget('distribution_license_field'))
        layout.addRow(self.widget('distribution_accessURL_label'),
                      self.widget('distribution_accessURL_field'))
        layout.addRow(self.widget('distribution_downloadURL_label'),
                      self.widget('distribution_downloadURL_field'))

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

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def accept(self) -> None:
        distrib = Distribution(
            URIRef(self.widget('distribution_iri_field').text().strip()),
            Literal(self.widget('distribution_ENtitle_field').text().strip(), lang='en'),
            Literal(self.widget('distribution_ITtitle_field').text().strip(), lang='it'),
            Literal(self.widget('distribution_ENdescription_field').text().strip(), lang='en'),
            Literal(self.widget('distribution_ITdescription_field').text().strip(), lang='it'),
            Literal(self.widget('distribution_format_field').text().strip()),
            Literal(self.widget('distribution_license_field').text().strip()),
            URIRef(self.widget('distribution_accessURL_field').text().strip()),
            URIRef(self.widget('distribution_downloadURL_field').text().strip()),
        )
        for triple in distrib.triples():
            self.dataset.add(triple)
        self.dataset.save()
        super().accept()
