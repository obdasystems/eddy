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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QDialog, QFormLayout, QLabel, QVBoxLayout
from PyQt5.QtWidgets import QMessageBox, QDialogButtonBox, QWidget

from eddy.core.commands.nodes import CommandNodeLabelChange
from eddy.core.datatypes.graphol import Identity
from eddy.core.datatypes.owl import XsdDatatype
from eddy.core.functions.misc import isEmpty
from eddy.core.functions.signals import connect
from eddy.core.qt import Font

from eddy.lang import gettext as _

from eddy.ui.fields import IntegerField, StringField, ComboBox


class CardinalityRestrictionForm(QDialog):
    """
    This class implements the form used to input domain/range restriction cardinalities.
    """
    def __init__(self, parent=None):
        """
        Initialize the form dialog.
        :type parent: QWidget
        """
        super().__init__(parent)
        self.minValue = None
        self.maxValue = None
        self.minField = IntegerField(self)
        self.maxField = IntegerField(self)
        self.minField.setFixedWidth(80)
        self.maxField.setFixedWidth(80)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.mainLayout = QFormLayout(self)
        self.mainLayout.addRow('Min. cardinality', self.minField)
        self.mainLayout.addRow('Max. cardinality', self.maxField)
        self.mainLayout.addRow(self.buttonBox)
        self.setWindowTitle('Insert cardinality')
        self.setWindowIcon(QIcon(':/images/eddy'))
        self.setFixedSize(self.sizeHint())

        connect(self.buttonBox.accepted, self.accept)
        connect(self.buttonBox.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def accept(self):
        """
        Validate the form and trigger accept() if the form is valid.
        """
        valid = True
        if not isEmpty(self.minField.text()) and not isEmpty(self.maxField.text()):
            v1 = int(self.minField.text())
            v2 = int(self.maxField.text())
            if v1 > v2:
                msgbox = QMessageBox(self)
                msgbox.setIconPixmap(QPixmap(':/icons/48/warning'))
                msgbox.setWindowIcon(QIcon(':/images/eddy'))
                msgbox.setWindowTitle('Invalid range specified')
                msgbox.setText('Min. cardinality {0} must be lower or equal than Max. cardinality {1}'.format(v1, v2))
                msgbox.setStandardButtons(QMessageBox.Ok)
                msgbox.exec_()
                valid = False
        if valid:
            if not isEmpty(self.minField.text()):
                self.minValue = int(self.minField.text())
            if not isEmpty(self.maxField.text()):
                self.maxValue = int(self.maxField.text())
            super().accept()


class ValueForm(QDialog):
    """
    This class implements the form used to select the Value of an Individual node.
    """
    def __init__(self, node, parent=None):
        """
        Initialize the form dialog.
        :type node: IndividualNode
        :type parent: QWidget
        """
        super().__init__(parent)

        # DATATYPE COMBO BOX
        self.datatypeField = ComboBox(self)
        for datatype in XsdDatatype:
            self.datatypeField.addItem(datatype.value, datatype)

        # VALUE STRING FIELD
        self.valueField = StringField(self)
        self.valueField.setFixedWidth(300)

        # FILL FIELDS WITH DATA
        if node.identity is Identity.Value:
            datatype = node.datatype
            for i in range(self.datatypeField.count()):
                if self.datatypeField.itemData(i) is datatype:
                    self.datatypeField.setCurrentIndex(i)
                    break
            self.valueField.setValue(node.value)

        else:
            self.datatypeField.setCurrentIndex(0)
            self.valueField.setValue('')

        # CONFIRMATION BOX
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)

        self.mainLayout = QFormLayout(self)
        self.mainLayout.addRow('Datatype', self.datatypeField)
        self.mainLayout.addRow('Value', self.valueField)
        self.mainLayout.addRow(self.buttonBox)

        self.setWindowTitle('Compose value')
        self.setWindowIcon(QIcon(':/images/eddy'))
        self.setFixedSize(self.sizeHint())

        connect(self.buttonBox.accepted, self.accept)
        connect(self.buttonBox.rejected, self.reject)


class RefactorNameDialog(QDialog):
    """
    This class implements the form used to rename nodes during refactor operations.
    """
    def __init__(self, node, parent=None):
        """
        Initialize the form dialog.
        :type node: AbstractNode
        :type parent: QWidget
        """
        super().__init__(parent)
        self.node = node

        arial12r = Font('Arial', 12)

        #############################################
        # FORM AREA
        #################################

        self.renameLabel = QLabel(self)
        self.renameLabel.setFont(arial12r)
        self.renameLabel.setText(_('REFACTOR_NAME_RENAME_LABEL'))
        self.renameField = StringField(self)
        self.renameField.setFixedWidth(200)
        self.renameField.setFont(arial12r)
        self.renameField.setValue(self.node.text())
        connect(self.renameField.textChanged, self.nameChanged)

        self.formWidget = QWidget(self)
        self.formLayout = QFormLayout(self.formWidget)
        self.formLayout.addRow(self.renameLabel, self.renameField)

        #############################################
        # CONFIRMATION AREA
        #################################

        self.confirmationBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.setFont(arial12r)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        self.caption = QLabel(self)
        self.caption.setFont(arial12r)
        self.caption.setContentsMargins(8, 0, 8, 0)
        self.caption.setProperty('class', 'invalid')
        self.caption.setVisible(False)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.formWidget)
        self.mainLayout.addWidget(self.caption)
        self.mainLayout.addWidget(self.confirmationBox, 0, Qt.AlignRight)

        self.setFixedSize(self.sizeHint())
        self.setWindowTitle(_('REFACTOR_NAME_WINDOW_TITLE'))

        connect(self.confirmationBox.accepted, self.accept)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def accept(self):
        """
        Accepts the rename form and perform refactoring.
        """
        name = self.renameField.value()
        name = name.strip()
        diagram = self.node.diagram
        project = self.node.project

        diagram.undoStack.beginMacro(_('COMMAND_NODE_REFACTOR_NAME', self.node.text(), name))
        for n in project.predicates(self.node.type(), self.node.text()):
            diagram.undoStack.push(CommandNodeLabelChange(n.diagram, n, n.text(), name))
        diagram.undoStack.endMacro()

        super().accept()

    @pyqtSlot()
    def nameChanged(self):
        """
        Executed whenever the text in the rename field changes.
        """
        caption = ''
        enabled = True

        if isEmpty(self.renameField.value()):
            caption = _('REFACTOR_NAME_CAPTION_NAME_NOT_VALID', self.renameField.value())
            enabled = False

        self.caption.setText(caption)
        self.caption.setVisible(not isEmpty(caption))
        self.confirmationBox.button(QDialogButtonBox.Ok).setEnabled(enabled)
        self.setFixedSize(self.sizeHint())