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


from textwrap import dedent

from PyQt5.QtCore import Qt, QSettings, pyqtSlot
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt5.QtWidgets import QDialogButtonBox, QFileDialog, QPushButton, QMessageBox

from eddy import ORGANIZATION, APPNAME, WORKSPACE
from eddy.core.functions.fsystem import mkdir
from eddy.core.functions.misc import first, format_exception
from eddy.core.functions.path import isPathValid, expandPath
from eddy.core.functions.signals import connect
from eddy.core.qt import Font

from eddy.ui.fields import StringField


class WorkspaceDialog(QDialog):
    """
    This class can be used to setup the workspace path.
    """
    def __init__(self, parent=None):
        """
        Initialize the workspace dialog.
        :type parent: QWidget
        """
        super().__init__(parent)

        arial12b = Font('Arial', 12)
        arial12b.setBold(True)
        arial12r = Font('Arial', 12)

        #############################################
        # HEAD AREA
        #################################

        self.headTitle = QLabel('Select a workspace', self)
        self.headTitle.setFont(arial12b)
        self.headDescription = QLabel(dedent("""
        Eddy stores your projects in a directory called workspace.\n'
        Please choose a workspace directory to use.""", self))
        self.headDescription.setFont(arial12r)
        self.headPix = QLabel(self)
        self.headPix.setPixmap(QPixmap(':/images/eddy-smile-small-noframe'))
        self.headPix.setContentsMargins(0, 0, 0, 0)

        self.headWidget = QWidget(self)
        self.headWidget.setProperty('class', 'head')
        self.headWidget.setContentsMargins(0, 0, 0, 0)

        self.headLayoutL = QVBoxLayout()
        self.headLayoutL.addWidget(self.headTitle)
        self.headLayoutL.addWidget(self.headDescription)
        self.headLayoutL.setContentsMargins(10, 10, 10, 10)
        self.headLayoutR = QVBoxLayout()
        self.headLayoutR.addWidget(self.headPix, 0, Qt.AlignRight)
        self.headLayoutR.setContentsMargins(0, 0, 0, 0)
        self.headLayoutM = QHBoxLayout(self.headWidget)
        self.headLayoutM.addLayout(self.headLayoutL)
        self.headLayoutM.addLayout(self.headLayoutR)
        self.headLayoutM.setContentsMargins(0, 0, 0, 0)

        #############################################
        # EDIT AREA
        #################################

        self.workspacePrefix = QLabel('Workspace', self)
        self.workspacePrefix.setFont(arial12r)

        self.workspaceField = StringField(self)
        self.workspaceField.setFont(arial12r)
        self.workspaceField.setFixedWidth(400)
        self.workspaceField.setReadOnly(True)
        self.workspaceField.setText(expandPath(WORKSPACE))

        self.btnBrowse = QPushButton(self)
        self.btnBrowse.setFont(arial12r)
        self.btnBrowse.setFixedWidth(30)
        self.btnBrowse.setText('...')

        self.editLayout = QHBoxLayout()
        self.editLayout.setContentsMargins(10, 10, 10, 10)
        self.editLayout.addWidget(self.workspacePrefix)
        self.editLayout.addWidget(self.workspaceField)
        self.editLayout.addWidget(self.btnBrowse)

        #############################################
        # CONFIRMATION AREA
        #################################

        self.confirmationBox = QDialogButtonBox(QDialogButtonBox.Ok, self)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.setFont(arial12r)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.headWidget)
        self.mainLayout.addLayout(self.editLayout)
        self.mainLayout.addWidget(self.confirmationBox, 0, Qt.AlignRight)

        self.setFixedSize(self.sizeHint())
        self.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Configure workspace')

        connect(self.btnBrowse.clicked, self.choosePath)
        connect(self.confirmationBox.accepted, self.accept)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def accept(self):
        """
        Create Eddy workspace (if necessary).
        """
        path = self.workspaceField.value()

        try:
            mkdir(path)
        except Exception as e:
            msgbox = QMessageBox(self)
            msgbox.setDetailedText(format_exception(e))
            msgbox.setIconPixmap(QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
            msgbox.setStandardButtons(QMessageBox.Close)
            msgbox.setText('Eddy could not create the specified workspace: {0}!'.format(path))
            msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Workspace setup failed!')
            msgbox.exec_()
            super().reject()
        else:
            settings = QSettings(ORGANIZATION, APPNAME)
            settings.setValue('workspace/home', path)
            settings.sync()
            super().accept()

    @pyqtSlot()
    def choosePath(self):
        """
        Bring up a modal window that allows the user to choose a valid workspace path.
        """
        path = self.workspaceField.value()
        if not isPathValid(path):
            path = expandPath('~')

        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setDirectory(path)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setViewMode(QFileDialog.Detail)

        if dialog.exec_() == QFileDialog.Accepted:
            self.workspaceField.setValue(first(dialog.selectedFiles()))