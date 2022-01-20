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

from eddy import APPNAME
from eddy.core.datatypes.qt import Font
from eddy.core.datatypes.system import File
from eddy.core.functions.misc import (
    first,
    format_exception,
    isEmpty,
)
from eddy.core.functions.signals import connect
from eddy.core.output import getLogger
from eddy.ui.fields import StringField
from eddy.ui.file import FileDialog

LOGGER = getLogger()


class PluginInstallDialog(QtWidgets.QDialog):
    """
    Extends QtWidgets.QDialog providing an interface to install plugins.
    """
    def __init__(self, session):
        """
        Initialize the plugin install dialog.
        :type session: Session
        """
        super().__init__(session)

        #############################################
        # HEAD AREA
        #################################

        self.headTitle = QtWidgets.QLabel('Install a plugin', self)
        self.headTitle.setFont(Font(bold=True))
        self.headDescription = QtWidgets.QLabel(dedent("""
        Plugins are software components that add specific features to {0}.<br/>
        Please select the plugin you wish to install.""".format(APPNAME)), self)
        self.headPix = QtWidgets.QLabel(self)
        self.headPix.setPixmap(QtGui.QIcon(':/icons/48/ic_extension_black').pixmap(48))
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
        # SELECTION AREA
        #################################

        self.pluginField = StringField(self)
        self.pluginField.setMinimumWidth(400)
        self.pluginField.setReadOnly(True)

        self.btnBrowse = QtWidgets.QPushButton(self)
        self.btnBrowse.setMinimumWidth(30)
        self.btnBrowse.setText('Browse')

        self.editLayout = QtWidgets.QHBoxLayout()
        self.editLayout.setContentsMargins(10, 10, 10, 10)
        self.editLayout.addWidget(self.pluginField)
        self.editLayout.addWidget(self.btnBrowse)

        #############################################
        # CONFIRMATION AREA
        #################################

        self.confirmationBox = QtWidgets.QDialogButtonBox(self)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Cancel)
        self.btnOk = self.confirmationBox.addButton(QtWidgets.QDialogButtonBox.Ok)
        self.btnOk.setEnabled(False)

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
        self.setWindowTitle('Install a plugin')

        connect(self.btnBrowse.clicked, self.selectPlugin)
        connect(self.confirmationBox.accepted, self.accept)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the main session (alias for PluginInstallDialog.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def accept(self):
        """
        Trigger the install of the selected plugin.
        """
        try:
            spec = self.session.pmanager.install(self.pluginField.value())
        except Exception as e:
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
            msgbox.setText('{0} could not install plugin archive <b>{1}</b>: {2}'.format(APPNAME, self.pluginField.value(), e))
            msgbox.setDetailedText(format_exception(e))
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Plugin install failed!')
            msgbox.exec_()
        else:
            plugin_name = spec.get('plugin', 'name')
            plugin_version = spec.get('plugin', 'version')
            plugin_author = spec.get('plugin', 'author', fallback='<unknown>')
            message = dedent("""\
                Successfully installed plugin <b>{0} v{1}</b> by <b>{2}</b>.<br/>
                In order to load the plugin you have to restart {3}.<br/>
                <p>Would you like to restart now?</p>
                """.format(plugin_name, plugin_version, plugin_author, APPNAME))
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_done_black').pixmap(48))
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msgbox.setText(message)
            msgbox.setTextFormat(QtCore.Qt.RichText)
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Plugin installed!')
            buttonYes = msgbox.button(QtWidgets.QMessageBox.Yes)
            # noinspection PyArgumentList
            buttonYes.clicked.connect(QtWidgets.QApplication.instance().doRestart, QtCore.Qt.QueuedConnection)
            msgbox.exec_()
            super().accept()

    @QtCore.pyqtSlot()
    def selectPlugin(self):
        """
        Bring up a modal window that allows the user to choose a valid plugin archive.
        """
        dialog = FileDialog(self)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        dialog.setNameFilters([File.Zip.value])

        if dialog.exec_() == QtWidgets.QFileDialog.Accepted:
            self.pluginField.setValue(first(dialog.selectedFiles()))
            self.btnOk.setEnabled(not isEmpty(self.pluginField.value()))
