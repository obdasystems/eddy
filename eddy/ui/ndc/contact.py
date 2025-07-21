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
    ContactPoint,
    NDCDataset,
)
from eddy.ui.fields import StringField


class ContactBuilderDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    Subclass of `QtWidgets.QDialog` used to define annotation assertions.
    """

    def __init__(self, parent: QtWidgets.QWidget, dataset: NDCDataset) -> None:
        """
        Initialize the contact builder dialog.
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
        layout.addRow(self.widget('contact_telephone_label'),
                      self.widget('contact_telephone_field'))

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

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def accept(self) -> None:
        contact = ContactPoint(
            URIRef(self.widget('contact_iri_field').text().strip()),
            Literal(self.widget('contact_ENname_field').text().strip(), lang='en'),
            Literal(self.widget('contact_ITname_field').text().strip(), lang='it'),
            Literal(self.widget('contact_email_field').text().strip()),
            Literal(self.widget('contact_telephone_field').text().strip()),
        )
        for triple in contact.triples():
            self.dataset.add(triple)
        self.dataset.save()
        super().accept()
