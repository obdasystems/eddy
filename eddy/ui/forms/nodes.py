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
from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QLabel
from PyQt5.QtWidgets import QMessageBox

from eddy.core.datatypes.graphol import Identity
from eddy.core.datatypes.owl import XsdDatatype, Facet
from eddy.core.functions.misc import isEmpty
from eddy.core.functions.signals import connect
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
                msgbox.setIconPixmap(QPixmap(':/icons/warning'))
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


class RenameForm(QDialog):
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
        self.renameField = StringField(self)
        self.renameField.setFixedWidth(200)
        self.renameField.setValue(self.node.text())
        self.invalidName = QLabel('\'\' is not a valid predicate name', self)
        self.invalidName.setProperty('class', 'invalid')
        self.invalidName.setVisible(False)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        self.mainLayout = QFormLayout(self)
        self.mainLayout.addRow('Name', self.renameField)
        self.mainLayout.addRow(self.invalidName)
        self.mainLayout.addRow(self.buttonBox)
        self.setWindowTitle('Rename')
        self.setWindowIcon(QIcon(':/images/eddy'))
        self.setFixedSize(self.sizeHint())

        connect(self.buttonBox.accepted, self.accept)
        connect(self.buttonBox.rejected, self.reject)
        connect(self.renameField.textChanged, self.nameChanged)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def nameChanged(self):
        """
        Executed whenever the text in the rename field changes.
        """
        button = self.buttonBox.button(QDialogButtonBox.Ok)
        empty = isEmpty(self.renameField.value())
        button.setDisabled(empty)
        self.invalidName.setVisible(empty)
        self.setFixedSize(self.sizeHint())

    @pyqtSlot()
    def accept(self):
        """
        Validate the form and trigger accept() if the form is valid.
        """
        if isEmpty(self.renameField.value()):
            msgbox = QMessageBox(self)
            msgbox.setIconPixmap(QPixmap(':/icons/warning'))
            msgbox.setWindowIcon(QIcon(':/images/eddy'))
            msgbox.setWindowTitle('Invalid predicate')
            msgbox.setText('You specified an invalid predicate name!')
            msgbox.setStandardButtons(QMessageBox.Ok)
            msgbox.exec_()
        else:
            # This will strip out leading/trailing whitespaces.
            self.renameField.setValue(self.renameField.value())
            super().accept()


class ValueRestrictionForm(QDialog):
    """
    This class implements the form used to select the restriction of a datatype.
    """
    # noinspection PyUnresolvedReferences
    def __init__(self, node, parent=None):
        """
        Initialize the form dialog.
        :type node: ValueRestrictionNode
        :type parent: QWidget
        """
        super().__init__(parent)

        # DATATYPE COMBO BOX
        self.datatypeField = ComboBox(self)
        for datatype in XsdDatatype:
            # hide unrestrictable elements.
            if Facet.forDatatype(datatype):
                self.datatypeField.addItem(datatype.value, datatype)

        datatype = node.datatype
        for i in range(self.datatypeField.count()):
            if self.datatypeField.itemData(i) is datatype:
                self.datatypeField.setCurrentIndex(i)
                break

        # FACET COMBO BOX
        self.facetField = ComboBox(self)
        for facet in Facet.forDatatype(datatype):
            self.facetField.addItem(facet.value, facet)

        facet = node.facet
        for i in range(self.facetField.count()):
            if self.facetField.itemData(i) is facet:
                self.facetField.setCurrentIndex(i)
                break

        # VALUE STRING FIELD
        self.valueField = StringField(self)
        self.valueField.setFixedWidth(300)
        self.valueField.setValue(node.value)

        # CONFIRMATION BOX
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)

        self.mainLayout = QFormLayout(self)
        self.mainLayout.addRow('Datatype', self.datatypeField)
        self.mainLayout.addRow('Facet', self.facetField)
        self.mainLayout.addRow('Value', self.valueField)
        self.mainLayout.addRow(self.buttonBox)

        self.setWindowTitle('Compose value restriction')
        self.setWindowIcon(QIcon(':/images/eddy'))
        self.setFixedSize(self.sizeHint())

        connect(self.buttonBox.accepted, self.accept)
        connect(self.buttonBox.rejected, self.reject)
        connect(self.datatypeField.currentIndexChanged[int], self.datatypeFieldChanged)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot(int)
    def datatypeFieldChanged(self, index):
        """
        Executed whenever the index of the datatype field changes.
        :type index: int
        """
        currentFacet = self.facetField.currentData()
        self.facetField.clear()
        for facet in Facet.forDatatype(self.datatypeField.itemData(index)):
            self.facetField.addItem(facet.value, facet)
        for i in range(self.facetField.count()):
            if self.facetField.itemData(i) is currentFacet:
                self.facetField.setCurrentIndex(i)
                break
        else:
            self.facetField.setCurrentIndex(0)