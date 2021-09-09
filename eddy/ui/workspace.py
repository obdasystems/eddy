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


from textwrap import dedent

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from eddy import (
    APPNAME,
    WORKSPACE,
)
from eddy.core.datatypes.qt import Font
from eddy.core.functions.fsystem import mkdir
from eddy.core.functions.misc import (
    first,
    format_exception,
)
from eddy.core.functions.path import (
    isPathValid,
    expandPath,
)
from eddy.core.functions.signals import connect
from eddy.ui.fields import StringField
from eddy.ui.file import FileDialog


class WorkspaceDialog(QtWidgets.QDialog):
    """
    This class can be used to setup the workspace path.
    """
    def __init__(self, parent=None):
        """
        Initialize the workspace dialog.
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)

        #############################################
        # HEAD AREA
        #################################

        self.headTitle = QtWidgets.QLabel('Select a workspace', self)
        self.headTitle.setFont(Font(bold=True))
        self.headDescription = QtWidgets.QLabel(dedent("""
        {0} stores your projects in a directory called <b>workspace</b>.<br/>
        Please choose a workspace directory to use.""".format(APPNAME)), self)
        self.headPix = QtWidgets.QLabel(self)
        self.headPix.setPixmap(QtGui.QIcon(':/icons/128/ic_eddy').pixmap(48))
        self.headPix.setContentsMargins(0, 0, 0, 0)
        self.headWidget = QtWidgets.QWidget(self)
        self.headWidget.setProperty('class', 'head')
        self.headWidget.setContentsMargins(10, 10, 10, 10)
        self.headLayoutL = QtWidgets.QVBoxLayout()
        self.headLayoutL.addWidget(self.headTitle)
        self.headLayoutL.addWidget(self.headDescription)
        self.headLayoutL.setContentsMargins(0, 0, 0, 0)
        self.headLayoutR = QtWidgets.QVBoxLayout()
        self.headLayoutR.addWidget(self.headPix, 0, QtCore.Qt.AlignRight)
        self.headLayoutR.setContentsMargins(0, 0, 0, 0)
        self.headLayoutM = QtWidgets.QHBoxLayout(self.headWidget)
        self.headLayoutM.addLayout(self.headLayoutL)
        self.headLayoutM.addLayout(self.headLayoutR)
        self.headLayoutM.setContentsMargins(0, 0, 0, 0)

        #############################################
        # EDIT AREA
        #################################

        self.workspaceField = StringField(self)
        self.workspaceField.setMinimumWidth(400)
        self.workspaceField.setReadOnly(True)
        self.workspaceField.setText(expandPath(WORKSPACE))

        self.btnBrowse = QtWidgets.QPushButton(self)
        self.btnBrowse.setText('Browse')

        self.editLayout = QtWidgets.QHBoxLayout()
        self.editLayout.setContentsMargins(10, 10, 10, 10)
        self.editLayout.addWidget(self.workspaceField)
        self.editLayout.addWidget(self.btnBrowse)

        #############################################
        # CONFIRMATION AREA
        #################################

        self.confirmationBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok, self)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.headWidget)
        self.mainLayout.addLayout(self.editLayout)
        self.mainLayout.addWidget(self.confirmationBox, 0, QtCore.Qt.AlignRight)

        self.setFixedSize(self.sizeHint())
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Configure workspace')

        connect(self.btnBrowse.clicked, self.choosePath)
        connect(self.confirmationBox.accepted, self.accept)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def accept(self):
        """
        Create Eddy workspace (if necessary).
        """
        path = self.workspaceField.value()

        try:
            mkdir(path)
        except Exception as e:
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setDetailedText(format_exception(e))
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
            msgbox.setText('{0} could not create the specified workspace: {1}!'.format(APPNAME, path))
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Workspace setup failed!')
            msgbox.exec_()
            super().reject()
        else:
            settings = QtCore.QSettings()
            settings.setValue('workspace/home', path)
            settings.sync()
            super().accept()

    @QtCore.pyqtSlot()
    def choosePath(self):
        """
        Bring up a modal window that allows the user to choose a valid workspace path.
        """
        path = self.workspaceField.value()
        if not isPathValid(path):
            path = expandPath('~')

        dialog = FileDialog(self)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setDirectory(path)
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)

        if dialog.exec_() == QtWidgets.QFileDialog.Accepted:
            self.workspaceField.setValue(first(dialog.selectedFiles()))
