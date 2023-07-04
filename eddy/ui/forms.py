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


from abc import ABCMeta
from operator import attrgetter

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from eddy.core.commands.labels import CommandLabelChange
from eddy.core.datatypes.graphol import Identity
from eddy.core.datatypes.owl import Datatype
from eddy.core.functions.misc import isEmpty
from eddy.core.functions.signals import connect
from eddy.ui.fields import ComboBox
from eddy.ui.fields import IntegerField
from eddy.ui.fields import StringField


class CardinalityRestrictionForm(QtWidgets.QDialog):
    """
    This class implements the form used to input domain/range restriction cardinalities.
    """

    def __init__(self, parent=None):
        """
        Initialize the form dialog.
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)

        #############################################
        # FORM AREA
        #################################

        self.minLabel = QtWidgets.QLabel(self)
        self.minLabel.setText('Min. cardinality')
        self.minField = IntegerField(self)
        self.minField.setFixedWidth(80)

        self.maxLabel = QtWidgets.QLabel(self)
        self.maxLabel.setText('Max. cardinality')
        self.maxField = IntegerField(self)
        self.maxField.setFixedWidth(80)

        self.formWidget = QtWidgets.QWidget(self)
        self.formLayout = QtWidgets.QFormLayout(self.formWidget)
        self.formLayout.addRow(self.minLabel, self.minField)
        self.formLayout.addRow(self.maxLabel, self.maxField)

        #############################################
        # CONFIRMATION AREA
        #################################

        self.confirmationBox = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Ok)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Cancel)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.formWidget)
        self.mainLayout.addWidget(self.confirmationBox, 0, QtCore.Qt.AlignRight)

        self.setFixedSize(self.sizeHint())
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Insert cardinality')

        connect(self.confirmationBox.accepted, self.accept)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def accept(self):
        """
        Validate the form and trigger accept() if the form is valid.
        """
        v1 = self.min()
        v2 = self.max()

        try:
            if v1 is not None and v1 < 0 or v2 is not None and v2 < 0:
                raise ValueError('Please enter only <b>positive</b> integers!')
            if v1 is not None and v2 is not None and v1 > v2:
                raise ValueError('Min. cardinality <b>{0}</b> must be '
                                 '<= than Max. cardinality <b>{1}</b>'.format(v1, v2))
        except ValueError as e:
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_warning_black').pixmap(48))
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Invalid range specified')
            msgbox.setText(str(e))
            msgbox.setTextFormat(QtCore.Qt.RichText)
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgbox.exec_()
        else:
            super().accept()

    #############################################
    #   INTERFACE
    #################################

    def max(self):
        """
        Returns the maximum cardinality value.
        :rtype: int
        """
        try:
            return int(self.maxField.text())
        except ValueError:
            return None

    def min(self):
        """
        Returns the minimum cardinality value.
        :rtype: int
        """
        try:
            return int(self.minField.text())
        except ValueError:
            return None


class RefactorNameForm(QtWidgets.QDialog):
    """
    This class implements the form used to rename nodes during refactor operations.
    """

    def __init__(self, node, session):
        """
        Initialize the form dialog.
        :type node: AbstractNode
        :type session: Session
        """
        super().__init__(session)

        self.node = node

        #############################################
        # FORM AREA
        #################################

        self.renameLabel = QtWidgets.QLabel(self)
        self.renameLabel.setText('Name')
        self.renameField = StringField(self)
        self.renameField.setFixedWidth(200)
        self.renameField.setValue(self.node.text())
        connect(self.renameField.textChanged, self.nameChanged)

        self.formWidget = QtWidgets.QWidget(self)
        self.formLayout = QtWidgets.QFormLayout(self.formWidget)
        self.formLayout.addRow(self.renameLabel, self.renameField)

        #############################################
        # CONFIRMATION AREA
        #################################

        self.confirmationBox = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Ok)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Cancel)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        self.caption = QtWidgets.QLabel(self)
        self.caption.setContentsMargins(8, 0, 8, 0)
        self.caption.setProperty('class', 'invalid')
        self.caption.setVisible(False)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.formWidget)
        self.mainLayout.addWidget(self.caption)
        self.mainLayout.addWidget(self.confirmationBox, 0, QtCore.Qt.AlignRight)

        self.setFixedSize(self.sizeHint())
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Rename')

        connect(self.confirmationBox.accepted, self.accept)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self):
        """
        Returns the reference to the active project.
        :rtype: Project
        """
        return self.session.project

    @property
    def session(self):
        """
        Returns the reference to the active session (alias for RefactorNameForm.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def accept(self):
        """
        Accepts the rename form and perform refactoring.
        """
        name = self.renameField.value()
        self.session.undostack.beginMacro('change predicate "{0}" to "{1}"'.format(self.node.text(), name))
        for node in self.project.predicates(self.node.type(), self.node.text()):
            command = CommandLabelChange(node.diagram, node, node.text(), name, refactor=True)
            self.session.undostack.push(command)
        self.session.undostack.endMacro()
        super().accept()

    @QtCore.pyqtSlot()
    def nameChanged(self):
        """
        Executed whenever the text in the rename field changes.
        """
        caption = ''
        enabled = True

        if isEmpty(self.renameField.value()):
            caption = "\'{0}\' is not a valid predicate name".format(self.renameField.value())
            enabled = False

        self.caption.setText(caption)
        self.caption.setVisible(not isEmpty(caption))
        self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(enabled)
        self.setFixedSize(self.sizeHint())


class ValueForm(QtWidgets.QDialog):
    """
    This class implements the form used to select the Value of an Individual node.
    """

    def __init__(self, node, session):
        """
        Initialize the form dialog.
        :type node: IndividualNode
        :type session: Session
        """
        super().__init__(session)

        self.node = node

        #############################################
        # FORM AREA
        #################################

        self.datatypeLabel = QtWidgets.QLabel(self)
        self.datatypeLabel.setText('Datatype')
        self.datatypeField = ComboBox(self)
        self.datatypeField.setFixedWidth(300)
        for datatype in sorted(Datatype.forProfile(self.project.profile.type()), key=attrgetter('value')):
            self.datatypeField.addItem(datatype.value, datatype)

        self.valueLabel = QtWidgets.QLabel(self)
        self.valueLabel.setText('Value')
        self.valueField = StringField(self)
        self.valueField.setFixedWidth(300)

        if node.identity() is Identity.Value:
            self.valueField.setValue(node.value)
            datatype = node.datatype
            for i in range(self.datatypeField.count()):
                if self.datatypeField.itemData(i) is datatype:
                    self.datatypeField.setCurrentIndex(i)
                    break
        else:
            self.valueField.setValue('')
            self.datatypeField.setCurrentIndex(0)

        self.formWidget = QtWidgets.QWidget(self)
        self.formLayout = QtWidgets.QFormLayout(self.formWidget)
        self.formLayout.addRow(self.datatypeLabel, self.datatypeField)
        self.formLayout.addRow(self.valueLabel, self.valueField)

        #############################################
        # CONFIRMATION AREA
        #################################

        self.confirmationBox = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Ok)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Cancel)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.formWidget)
        self.mainLayout.addWidget(self.confirmationBox, 0, QtCore.Qt.AlignRight)

        self.setFixedSize(self.sizeHint())
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Compose value')

        connect(self.confirmationBox.accepted, self.accept)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self):
        """
        Returns the reference to the active project.
        :rtype: Project
        """
        return self.session.project

    @property
    def session(self):
        """
        Returns the reference to the active session (alias for RefactorNameForm.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def accept(self):
        """
        Accepts the form and set the new value.
        """
        node = self.node
        diagram = node.diagram
        datatype = self.datatypeField.currentData()
        value = self.valueField.value()
        data = node.compose(value, datatype)
        if node.text() != data:
            name = 'change {0} to {1}'.format(node.text(), data)
            self.session.undostack.push(CommandLabelChange(diagram, node, node.text(), data, name=name))
        super().accept()


class AbstractDiagramForm(QtWidgets.QDialog):
    """
    Base class for diagram dialogs.
    """
    __metaclass__ = ABCMeta

    def __init__(self, project, parent=None):
        """
        Initialize the dialog.
        :type project: Project
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)

        self.project = project

        #############################################
        # FORM AREA
        #################################

        self.nameField = StringField(self)
        self.nameField.setMinimumWidth(400)
        self.nameField.setMaxLength(64)
        self.nameField.setPlaceholderText('Name...')
        connect(self.nameField.textChanged, self.onNameFieldChanged)

        self.warnLabel = QtWidgets.QLabel(self)
        self.warnLabel.setContentsMargins(0, 0, 0, 0)
        self.warnLabel.setProperty('class', 'invalid')
        self.warnLabel.setVisible(False)

        #############################################
        # CONFIRMATION AREA
        #################################

        self.confirmationBox = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Ok)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Cancel)
        self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.addWidget(self.nameField)
        self.mainLayout.addWidget(self.warnLabel)
        self.mainLayout.addWidget(self.confirmationBox, 0, QtCore.Qt.AlignRight)

        self.setFixedSize(self.sizeHint())
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))

        connect(self.confirmationBox.accepted, self.accept)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(str)
    def onNameFieldChanged(self, name):
        """
        Executed when the content of the input field changes.
        :type name: str
        """
        name = name.strip()
        if not name:
            caption = ''
            enabled = False
        else:
            for diagram in self.project.diagrams():
                if diagram.name.upper() == name.upper():
                    caption = "Diagram '{0}' already exists!".format(name)
                    enabled = False
                    break
            else:
                caption = ''
                enabled = True
        self.warnLabel.setText(caption)
        self.warnLabel.setVisible(not isEmpty(caption))
        self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(enabled)
        self.setFixedSize(self.sizeHint())

    #############################################
    #   INTERFACE
    #################################

    def name(self):
        """
        Returns the new diagram name.
        :rtype: str
        """
        return self.nameField.value()


class NewDiagramForm(AbstractDiagramForm):
    """
    This class is used to display a modal window used to create a new diagram.
    """

    def __init__(self, project, parent=None):
        """
        Initialize the new diagram dialog.
        :type project: Project
        :type parent: QtWidgets.QWidget
        """
        super().__init__(project, parent)
        self.setWindowTitle('New diagram')


class RenameDiagramForm(AbstractDiagramForm):
    """
    This class is used to display a modal window used to rename diagrams.
    """

    def __init__(self, project, diagram, parent=None):
        """
        Initialize the new diagram dialog.
        :type project: Project
        :type diagram: Diagram
        :type parent: QtWidgets.QWidget
        """
        super().__init__(project, parent)
        self.diagram = diagram
        self.nameField.setText(self.diagram.name)
        self.setWindowTitle('Rename diagram: {0}'.format(self.diagram.name))

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(str)
    def onNameFieldChanged(self, name):
        """
        Executed when the content of the input field changes.
        :type name: str
        """
        name = name.strip()
        if not name:
            caption = ''
            enabled = False
        else:
            for diagram in self.project.diagrams():
                if diagram.name.upper() == name.upper():
                    caption = ''
                    enabled = False
                    break
            else:
                caption = ''
                enabled = True
        self.warnLabel.setText(caption)
        self.warnLabel.setVisible(not isEmpty(caption))
        self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(enabled)
        self.setFixedSize(self.sizeHint())


class RenameProjectForm(AbstractDiagramForm):
    """
    This class is used to display a modal window used to rename the project.
    """

    def __init__(self, project, parent=None):
        """
        Initialize the new dialog.
        :type project: Project
        :type parent: QtWidgets.QWidget
        """
        super().__init__(project, parent)
        self.project = project
        self.nameField.setText(self.project.name)
        self.setWindowTitle('Rename project: {0}'.format(self.project.name))

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(str)
    def onNameFieldChanged(self, name):
        """
        Executed when the content of the input field changes.
        :type name: str
        """
        name = name.strip()
        if not name:
            caption = ''
            enabled = False
        else:
            caption = ''
            enabled = True
        self.warnLabel.setText(caption)
        self.warnLabel.setVisible(not isEmpty(caption))
        self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(enabled)
        self.setFixedSize(self.sizeHint())
