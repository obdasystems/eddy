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


from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
    QtXmlPatterns,
)

from eddy.core.functions.misc import isEmpty
from eddy.core.functions.signals import connect
from eddy.core.owl import IRI
from eddy.ui.fields import StringField


class NewProjectDialog(QtWidgets.QDialog):
    """
    This class is used to display a modal window to enter new project specific data.
    """
    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize the project dialog.
        :type parent: QWidget
        """
        super().__init__(parent)

        #############################################
        # FORM AREA
        #################################

        self.nameLabel = QtWidgets.QLabel(self)
        self.nameLabel.setText('Project name')
        self.nameField = StringField(self)
        self.nameField.setMinimumWidth(400)
        self.nameField.setMaxLength(64)

        self.iriLabel = QtWidgets.QLabel(self)
        self.iriLabel.setText('Ontology IRI')
        self.iriField = StringField(self)
        self.iriField.setMinimumWidth(400)

        self.prefixLabel = QtWidgets.QLabel(self)
        self.prefixLabel.setText('Ontology prefix')
        self.prefixField = StringField(self)
        self.prefixField.setMinimumWidth(400)

        connect(self.prefixField.textChanged, self.doValidateForm)
        connect(self.iriField.textChanged, self.doValidateForm)
        connect(self.nameField.textChanged, self.doValidateForm)

        spacer = QtWidgets.QFrame()
        spacer.setFrameShape(QtWidgets.QFrame.HLine)
        spacer.setFrameShadow(QtWidgets.QFrame.Sunken)

        self.formWidget = QtWidgets.QWidget(self)
        self.formLayout = QtWidgets.QFormLayout(self.formWidget)
        self.formLayout.addRow(self.nameLabel, self.nameField)
        self.formLayout.addRow(self.iriLabel, self.iriField)
        self.formLayout.addRow(self.prefixLabel, self.prefixField)
        self.formLayout.addWidget(spacer)

        #############################################
        # CONFIRMATION AREA
        #################################

        self.confirmationBox = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Ok)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Cancel)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        self.caption = QtWidgets.QLabel(self)
        self.caption.setContentsMargins(8, 0, 8, 0)
        self.caption.setProperty('class', 'invalid')
        self.caption.setVisible(False)

        self.gridLayout = QtWidgets.QVBoxLayout(self)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.addWidget(self.formWidget)
        self.gridLayout.addWidget(self.caption)
        self.gridLayout.addWidget(self.confirmationBox, 0, QtCore.Qt.AlignRight)

        self.setFixedSize(self.sizeHint())
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('New project')

        connect(self.confirmationBox.accepted, self.accept)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   INTERFACE
    #################################

    def iri(self) -> str:
        """
        Returns the value of the iri field (trimmed).
        """
        return self.iriField.value()

    def name(self) -> str:
        """
        Returns the value of the name field (trimmed).
        """
        return self.nameField.value()

    def prefix(self) -> str:
        """
        Returns the value of the prefix field (trimmed).
        """
        return self.prefixField.value()

    #############################################
    # SLOTS
    #################################

    @QtCore.pyqtSlot()
    def doValidateForm(self) -> None:
        """
        Validate project settings.
        """
        caption = ''
        enabled = True

        #############################################
        # CHECK NAME
        #################################

        if not self.name():
            caption = ''
            enabled = False

        #############################################
        # CHECK PREFIX
        #################################

        if enabled:
            if self.prefix() and not QtXmlPatterns.QXmlName.isNCName(self.prefix()):
                caption = 'Please insert a legal prefix'
                enabled = False

        #############################################
        # CHECK IRI
        #################################

        if enabled:
            if not self.iri():
                caption = ''
                enabled = False
            elif not IRI.isValidNamespace(self.iri()):
                caption = 'Please insert a legal IRI'
                enabled = False

        self.caption.setText(caption)
        self.caption.setVisible(not isEmpty(caption))
        self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(enabled)
        self.setFixedSize(self.sizeHint())


class ProjectFromOWLDialog(QtWidgets.QDialog):
    """
    This class is used to display a modal window to enter new project specific data.
    """
    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize the project dialog.
        :type parent: QWidget
        """
        super().__init__(parent)

        #############################################
        # FORM AREA
        #################################

        self.nameLabel = QtWidgets.QLabel(self)
        self.nameLabel.setText('Project name')
        self.nameField = StringField(self)
        self.nameField.setMinimumWidth(400)
        self.nameField.setMaxLength(64)

        connect(self.nameField.textChanged, self.doValidateForm)

        self.formWidget = QtWidgets.QWidget(self)
        self.formLayout = QtWidgets.QFormLayout(self.formWidget)
        self.formLayout.addRow(self.nameLabel, self.nameField)

        #############################################
        # CONFIRMATION AREA
        #################################

        self.confirmationBox = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Ok)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Cancel)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        self.caption = QtWidgets.QLabel(self)
        self.caption.setContentsMargins(8, 0, 8, 0)
        self.caption.setProperty('class', 'invalid')
        self.caption.setVisible(False)

        self.gridLayout = QtWidgets.QVBoxLayout(self)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.addWidget(self.formWidget)
        self.gridLayout.addWidget(self.caption)
        self.gridLayout.addWidget(self.confirmationBox, 0, QtCore.Qt.AlignRight)

        self.setFixedSize(self.sizeHint())
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('New project from OWL file')

        connect(self.confirmationBox.accepted, self.accept)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   INTERFACE
    #################################

    def name(self) -> str:
        """
        Returns the value of the name field (trimmed).
        """
        return self.nameField.value()

    #############################################
    # SLOTS
    #################################

    @QtCore.pyqtSlot()
    def doValidateForm(self) -> None:
        """
        Validate project settings.
        """
        caption = ''
        enabled = True

        #############################################
        # CHECK NAME
        #################################

        if not self.name():
            caption = ''
            enabled = False

        #############################################

        self.caption.setText(caption)
        self.caption.setVisible(not isEmpty(caption))
        self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(enabled)
        self.setFixedSize(self.sizeHint())
