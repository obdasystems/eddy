# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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


import os

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy import ORGANIZATION, APPNAME, WORKSPACE
from eddy.core.datatypes.qt import Font
from eddy.core.exporters.graphol import GrapholProjectExporter
from eddy.core.functions.fsystem import is_dir
from eddy.core.functions.misc import isEmpty
from eddy.core.functions.path import expandPath, isPathValid
from eddy.core.functions.signals import connect
from eddy.core.profiles.owl2 import OWL2Profile
from eddy.core.project import Project

from eddy.ui.fields import StringField


class ProjectDialog(QtWidgets.QDialog):
    """
    This class is used to display a modal window to enter project specific data.
    """
    def __init__(self, parent=None):
        """
        Initialize the project dialog.
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)

        arial12r = Font('Arial', 12)

        #############################################
        # FORM AREA
        #################################

        settings = QtCore.QSettings(ORGANIZATION, APPNAME)

        self.workspace = expandPath(settings.value('workspace/home', WORKSPACE, str))
        self.workspace = '{0}{1}'.format(self.workspace.rstrip(os.path.sep), os.path.sep)

        self.nameLabel = QtWidgets.QLabel(self)
        self.nameLabel.setFont(arial12r)
        self.nameLabel.setText('Name')
        self.nameField = StringField(self)
        self.nameField.setFont(arial12r)
        self.nameField.setMinimumWidth(400)
        self.nameField.setMaxLength(64)
        connect(self.nameField.textChanged, self.onNameFieldChanged)

        self.prefixLabel = QtWidgets.QLabel(self)
        self.prefixLabel.setFont(arial12r)
        self.prefixLabel.setText('Prefix')
        self.prefixField = StringField(self)
        self.prefixField.setFont(arial12r)
        self.prefixField.setMinimumWidth(400)

        self.iriLabel = QtWidgets.QLabel(self)
        self.iriLabel.setFont(arial12r)
        self.iriLabel.setText('IRI')
        self.iriField = StringField(self)
        self.iriField.setFont(arial12r)
        self.iriField.setMinimumWidth(400)

        connect(self.iriField.textChanged, self.doProjectPathValidate)
        connect(self.nameField.textChanged, self.doProjectPathValidate)
        connect(self.prefixField.textChanged, self.doProjectPathValidate)

        self.pathLabel = QtWidgets.QLabel(self)
        self.pathLabel.setFont(arial12r)
        self.pathLabel.setText('Location')
        self.pathField = StringField(self)
        self.pathField.setFont(arial12r)
        self.pathField.setMinimumWidth(400)
        self.pathField.setReadOnly(True)
        self.pathField.setFocusPolicy(QtCore.Qt.NoFocus)
        self.pathField.setValue(self.workspace)

        spacer = QtWidgets.QFrame()
        spacer.setFrameShape(QtWidgets.QFrame.HLine)
        spacer.setFrameShadow(QtWidgets.QFrame.Sunken)

        self.formWidget = QtWidgets.QWidget(self)
        self.formLayout = QtWidgets.QFormLayout(self.formWidget)
        self.formLayout.addRow(self.nameLabel, self.nameField)
        self.formLayout.addRow(self.prefixLabel, self.prefixField)
        self.formLayout.addRow(self.iriLabel, self.iriField)
        self.formLayout.addWidget(spacer)
        self.formLayout.addRow(self.pathLabel, self.pathField)

        #############################################
        # CONFIRMATION AREA
        #################################

        self.confirmationBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.setFont(arial12r)
        self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        self.caption = QtWidgets.QLabel(self)
        self.caption.setFont(arial12r)
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
        self.setWindowTitle('New project')

        connect(self.confirmationBox.accepted, self.accept)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   INTERFACE
    #################################

    def iri(self):
        """
        Returns the value of the iri field (trimmed).
        :rtype: str
        """
        return self.iriField.value()

    def path(self):
        """
        Returns the value of the path field (expanded).
        :rtype: str
        """
        return expandPath(self.pathField.value())

    def prefix(self):
        """
        Returns the value of the prefix field (trimmed).
        :rtype: str
        """
        return self.prefixField.value()

    #############################################
    # SLOTS
    #################################

    @QtCore.pyqtSlot()
    def accept(self):
        """
        Accept the project form and creates a new empty project.
        """
        project = Project(self.path(), self.prefix(), self.iri(), OWL2Profile())
        exporter = GrapholProjectExporter(project)
        exporter.export()
        super().accept()

    @QtCore.pyqtSlot()
    def doProjectPathValidate(self):
        """
        Validate project settings.
        """
        caption = ''
        enabled = True

        #############################################
        # CHECK NAME
        #################################

        name = self.nameField.value()
        path = self.pathField.value()

        if not name:
            caption = ''
            enabled = False
        else:
            if is_dir(path):
                caption = "Project '{0}' already exists!".format(name)
                enabled = False
            elif not isPathValid(path):
                caption = "'{0}' is not a valid project name!".format(name)
                enabled = False

        #############################################
        # CHECK PREFIX
        #################################

        if enabled:
            if not self.prefixField.value():
                caption = ''
                enabled = False

        #############################################
        # CHECK IRI
        #################################

        if enabled:
            if not self.iriField.value():
                caption = ''
                enabled = False

        self.caption.setText(caption)
        self.caption.setVisible(not isEmpty(caption))
        self.confirmationBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(enabled)
        self.setFixedSize(self.sizeHint())

    @QtCore.pyqtSlot(str)
    def onNameFieldChanged(self, name):
        """
        Update the project location field to reflect the new project name.
        :type name: str
        """
        self.pathField.setValue('{0}{1}'.format(self.workspace, name.strip()))