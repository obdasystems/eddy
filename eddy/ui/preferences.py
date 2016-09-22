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


import textwrap

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy import ORGANIZATION, APPNAME
from eddy.core.datatypes.qt import Font
from eddy.core.diagram import Diagram
from eddy.core.functions.signals import connect

from eddy.ui.fields import CheckBox, SpinBox


class PreferencesDialog(QtWidgets.QDialog):
    """
    This class implements the 'Preferences' dialog.
    """
    def __init__(self, session):
        """
        Initialize the Preferences dialog.
        :type session: Session
        """
        super(PreferencesDialog, self).__init__(session)

        settings = QtCore.QSettings(ORGANIZATION, APPNAME)

        #############################################
        # EDITOR TAB
        #################################

        self.diagramSizePrefix = QtWidgets.QLabel(self)
        self.diagramSizePrefix.setFont(Font('Roboto', 12))
        self.diagramSizePrefix.setText('Diagram size')
        self.diagramSizeField = SpinBox(self)
        self.diagramSizeField.setFont(Font('Roboto', 12))
        self.diagramSizeField.setRange(Diagram.MinSize, Diagram.MaxSize)
        self.diagramSizeField.setSingleStep(100)
        self.diagramSizeField.setToolTip('Default size of all the new created diagrams.')
        self.diagramSizeField.setValue(settings.value('diagram/size', 5000, int))

        self.editorWidget = QtWidgets.QWidget()
        self.editorLayout = QtWidgets.QFormLayout(self.editorWidget)
        self.editorLayout.addRow(self.diagramSizePrefix, self.diagramSizeField)

        #############################################
        # PLUGINS TAB
        #################################

        self.pluginsUninstall = dict()
        self.pluginsTable = QtWidgets.QTableWidget(len(self.session.plugins()), 5, self)
        self.pluginsTable.setHorizontalHeaderLabels(['Name', 'Version', 'Author', 'Contact', 'Uninstall'])
        self.pluginsTable.setFont(Font('Roboto', 12))
        self.pluginsTable.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        header = self.pluginsTable.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.Fixed)
        header.setSectionsClickable(False)
        header.setSectionsMovable(False)
        header = self.pluginsTable.verticalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        for row, plugin in enumerate(sorted(self.session.plugins(), key=lambda x: x.name())):
            item = QtWidgets.QTableWidgetItem(plugin.name())
            item.setTextAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
            self.pluginsTable.setItem(row, 0, item)
            item = QtWidgets.QTableWidgetItem('v{0}'.format(plugin.version()))
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.pluginsTable.setItem(row, 1, item)
            item = QtWidgets.QTableWidgetItem(plugin.author())
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.pluginsTable.setItem(row, 2, item)
            item = QtWidgets.QTableWidgetItem(plugin.contact())
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.pluginsTable.setItem(row, 3, item)
            p_widget = QtWidgets.QWidget()
            p_checkbox = CheckBox()
            p_checkbox.setEnabled(not plugin.isBuiltIn())
            p_layout = QtWidgets.QHBoxLayout(p_widget)
            p_layout.addWidget(p_checkbox)
            p_layout.setAlignment(QtCore.Qt.AlignCenter)
            p_layout.setContentsMargins(0, 0, 0, 0)
            self.pluginsTable.setCellWidget(row, 4, p_widget)
            self.pluginsUninstall[plugin] = p_checkbox

        self.pluginsWidget = QtWidgets.QWidget()
        self.pluginsLayout = QtWidgets.QHBoxLayout(self.pluginsWidget)
        self.pluginsLayout.addWidget(self.pluginsTable, 1)

        #############################################
        # CONFIRMATION BOX
        #################################

        self.confirmationBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel, QtCore.Qt.Horizontal, self)
        self.confirmationBox.setContentsMargins(10, 0, 10, 10)
        self.confirmationBox.setFont(Font('Roboto', 12))

        #############################################
        # MAIN WIDGET
        #################################

        self.mainWidget = QtWidgets.QTabWidget(self)
        self.mainWidget.addTab(self.editorWidget, QtGui.QIcon(':/icons/48/ic_edit_black'), 'Editor')
        self.mainWidget.addTab(self.pluginsWidget, QtGui.QIcon(':/icons/48/ic_extension_black'), 'Plugins')
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.mainWidget)
        self.mainLayout.addWidget(self.confirmationBox, 0, QtCore.Qt.AlignRight)

        self.setMinimumSize(740, 420)
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Preferences')

        connect(self.confirmationBox.accepted, self.accept)
        connect(self.confirmationBox.rejected, self.reject)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the main session (alias for PreferencesDialog.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def accept(self):
        """
        Executed when the dialog is accepted.
        """
        #############################################
        # PLUGINS TAB
        #################################

        plugins_to_uninstall = [plugin for plugin, checkbox in self.pluginsUninstall.items() if checkbox.isChecked()]
        if plugins_to_uninstall:
            plugins_to_uninstall_fmt = []
            for plugin in plugins_to_uninstall:
                plugins_to_uninstall_fmt.append('&nbsp;&nbsp;&nbsp;&nbsp;- {0} v{1}'.format(plugin.name(), plugin.version()))
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_question_outline_black').pixmap(48))
            msgbox.setInformativeText('<b>NOTE: This action is not reversible!</b>')
            msgbox.setStandardButtons(QtWidgets.QMessageBox.No|QtWidgets.QMessageBox.Yes)
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Are you sure?')
            msgbox.setText(textwrap.dedent("""You marked the following plugins for uninstall:<br/><br/>
            {0}<br/><br/>Are you sure you want to continue?""".format('<br/>'.join(plugins_to_uninstall_fmt))))
            msgbox.exec_()
            if msgbox.result() == QtWidgets.QMessageBox.No:
                return

        for plugin in plugins_to_uninstall:
            self.session.pmanager.uninstall(plugin)

        #############################################
        # EDITOR TAB
        #################################

        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        settings.setValue('diagram/size', self.diagramSizeField.value())
        settings.sync()

        super(PreferencesDialog, self).accept()