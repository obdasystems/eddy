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
    Theme,
    NDCDataset,
)
from eddy.ui.fields import StringField


class ThemeBuilderDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    Subclass of `QtWidgets.QDialog` used to define annotation assertions.
    """

    def __init__(self, parent: QtWidgets.QWidget, dataset: NDCDataset) -> None:
        """
        Initialize the theme builder dialog.
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

        iri = QtWidgets.QLabel(self, objectName='theme_iri_label')
        iri.setText('IRI')
        self.addWidget(iri)

        iriField = StringField(self, objectName='theme_iri_field')
        self.addWidget(iriField)

        label = QtWidgets.QLabel(self, objectName='theme_label_label')
        label.setText('Label')
        self.addWidget(label)

        ITlabelField = StringField(self, objectName='theme_ITlabel_field')
        ITlabelField.setPlaceholderText('@it')
        self.addWidget(ITlabelField)

        noLabel = QtWidgets.QLabel(self, objectName='no_label')
        self.addWidget(noLabel)

        ENlabelField = StringField(self, objectName='theme_ENlabel_field')
        ENlabelField.setPlaceholderText('@en')
        self.addWidget(ENlabelField)

        scheme = QtWidgets.QLabel(self, objectName='theme_scheme_label')
        scheme.setText('In Scheme')
        self.addWidget(scheme)

        schemeField = StringField(self, objectName='theme_scheme_field')
        self.addWidget(schemeField)

        layout = QtWidgets.QFormLayout()
        layout.addRow(self.widget('theme_iri_label'), self.widget('theme_iri_field'))
        layout.addRow(self.widget('theme_label_label'), self.widget('theme_ITlabel_field'))
        layout.addRow(self.widget('no_label'), self.widget('theme_ENlabel_field'))
        layout.addRow(self.widget('theme_scheme_label'), self.widget('theme_scheme_field'))

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('theme_widget')
        self.addWidget(widget)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(self.widget('theme_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)

        self.setMinimumSize(740, 380)
        self.setWindowTitle('Add Theme')

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def accept(self) -> None:
        theme = Theme(
            URIRef(self.widget('theme_iri_field').text().strip()),
            Literal(self.widget('theme_ENlabel_field').text().strip(), lang='en'),
            Literal(self.widget('theme_ITlabel_field').text().strip(), lang='it'),
            URIRef(self.widget('theme_scheme_field').text().strip()),
        )
        for triple in theme.triples():
            self.dataset.add(triple)
        self.dataset.save()
        super().accept()
