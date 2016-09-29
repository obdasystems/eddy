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
from eddy.core.datatypes.owl import OWLAxiom
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
        self.diagramSizeField.setToolTip('Default size of all the new created diagrams')
        self.diagramSizeField.setValue(settings.value('diagram/size', 5000, int))

        self.editorWidget = QtWidgets.QWidget()
        self.editorLayout = QtWidgets.QFormLayout(self.editorWidget)
        self.editorLayout.addRow(self.diagramSizePrefix, self.diagramSizeField)

        #############################################
        # EXPORT TAB
        #################################

        self.axiomsChecks = {x: CheckBox(x.value, self) for x in OWLAxiom}
        for axiom, checkbox in self.axiomsChecks.items():
            checkbox.setChecked(settings.value('export/axiom/{0}'.format(axiom.value), True, bool))
        self.axiomsNonLogicalLayout = QtWidgets.QGridLayout()
        self.axiomsNonLogicalLayout.setColumnMinimumWidth(0, 230)
        self.axiomsNonLogicalLayout.setColumnMinimumWidth(1, 230)
        self.axiomsNonLogicalLayout.setColumnMinimumWidth(2, 230)
        self.axiomsNonLogicalLayout.addWidget(self.axiomsChecks[OWLAxiom.Annotation], 0, 0)
        self.axiomsNonLogicalLayout.addWidget(self.axiomsChecks[OWLAxiom.Declaration], 0, 1)
        self.axiomsNonLogicalLayout.addWidget(QtWidgets.QWidget(self), 0, 2)
        self.axiomsNonLogicalGroup = QtWidgets.QGroupBox('Non-Logical', self)
        self.axiomsNonLogicalGroup.setLayout(self.axiomsNonLogicalLayout)
        self.axiomsIntensionalLayout = QtWidgets.QGridLayout()
        self.axiomsIntensionalLayout.setColumnMinimumWidth(0, 230)
        self.axiomsIntensionalLayout.setColumnMinimumWidth(1, 230)
        self.axiomsIntensionalLayout.setColumnMinimumWidth(2, 230)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.AsymmetricObjectProperty], 0, 0)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.DataPropertyDomain], 0, 1)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.DataPropertyRange], 0, 2)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.DisjointClasses], 1, 0)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.DisjointDataProperties], 1, 1)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.DisjointObjectProperties], 1, 2)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.EquivalentClasses], 2, 0)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.EquivalentDataProperties], 2, 1)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.EquivalentObjectProperties], 2, 2)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.FunctionalDataProperty], 3, 0)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.FunctionalObjectProperty], 3, 1)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.InverseFunctionalObjectProperty], 3, 2)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.InverseObjectProperties], 4, 0)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.IrreflexiveObjectProperty], 4, 1)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.ObjectPropertyDomain], 4, 2)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.ObjectPropertyRange], 5, 0)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.ReflexiveObjectProperty], 5, 1)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.SubClassOf], 5, 2)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.SubDataPropertyOf], 6, 0)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.SubObjectPropertyOf], 6, 1)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.SymmetricObjectProperty], 6, 2)
        self.axiomsIntensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.TransitiveObjectProperty], 7, 0)
        self.axiomsIntensionalGroup = QtWidgets.QGroupBox('Intensional', self)
        self.axiomsIntensionalGroup.setLayout(self.axiomsIntensionalLayout)
        self.axiomsExtensionalLayout = QtWidgets.QGridLayout()
        self.axiomsExtensionalLayout.setColumnMinimumWidth(0, 230)
        self.axiomsExtensionalLayout.setColumnMinimumWidth(1, 230)
        self.axiomsExtensionalLayout.setColumnMinimumWidth(2, 230)
        self.axiomsExtensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.ClassAssertion], 0, 0)
        self.axiomsExtensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.DataPropertyAssertion], 0, 1)
        self.axiomsExtensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.NegativeDataPropertyAssertion], 0, 2)
        self.axiomsExtensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.NegativeObjectPropertyAssertion], 1, 0)
        self.axiomsExtensionalLayout.addWidget(self.axiomsChecks[OWLAxiom.ObjectPropertyAssertion], 1, 1)
        self.axiomsExtensionalGroup = QtWidgets.QGroupBox('Extensional', self)
        self.axiomsExtensionalGroup.setLayout(self.axiomsExtensionalLayout)
        self.axiomsLogicalLayout = QtWidgets.QVBoxLayout()
        self.axiomsLogicalLayout.addWidget(self.axiomsIntensionalGroup)
        self.axiomsLogicalLayout.addWidget(self.axiomsExtensionalGroup)
        self.axiomsLogicalWidget = QtWidgets.QGroupBox('Logical', self)
        self.axiomsLogicalWidget.setLayout(self.axiomsLogicalLayout)
        self.axiomsMainLayout = QtWidgets.QVBoxLayout()
        self.axiomsMainLayout.addWidget(self.axiomsNonLogicalGroup)
        self.axiomsMainLayout.addWidget(self.axiomsLogicalWidget)
        self.axiomsGroup = QtWidgets.QGroupBox('OWL 2 Axioms for which exporting is enabled', self)
        self.axiomsGroup.setLayout(self.axiomsMainLayout)
        self.axiomsLayout = QtWidgets.QVBoxLayout()
        self.axiomsLayout.setContentsMargins(10, 10, 10, 10)
        self.axiomsLayout.addWidget(self.axiomsGroup)
        self.axiomsWidget = QtWidgets.QWidget(self)
        self.axiomsWidget.setLayout(self.axiomsLayout)

        #############################################
        # PLUGINS TAB
        #################################

        self.pluginsUninstall = dict()
        self.pluginsTable = QtWidgets.QTableWidget(len(self.session.plugins()), 5, self)
        self.pluginsTable.setHorizontalHeaderLabels(['Name', 'Version', 'Author', 'Contact', 'Uninstall'])
        self.pluginsTable.setFont(Font('Roboto', 12))
        self.pluginsTable.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.pluginsTable.setFocusPolicy(QtCore.Qt.NoFocus)

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
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.pluginsTable.setItem(row, 0, item)
            item = QtWidgets.QTableWidgetItem('v{0}'.format(plugin.version()))
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.pluginsTable.setItem(row, 1, item)
            item = QtWidgets.QTableWidgetItem(plugin.author())
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.pluginsTable.setItem(row, 2, item)
            item = QtWidgets.QTableWidgetItem(plugin.contact())
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
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

        self.pluginInstallButton = QtWidgets.QToolButton(self)
        self.pluginInstallButton.setDefaultAction(self.session.action('install_plugin'))
        self.pluginInstallButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.pluginInstallButton.setFont(Font('Roboto', 13))

        self.pluginsWidget = QtWidgets.QWidget()
        self.pluginsLayout = QtWidgets.QVBoxLayout(self.pluginsWidget)
        self.pluginsLayout.addWidget(self.pluginsTable, 1)
        self.pluginsLayout.addWidget(self.pluginInstallButton, 0, QtCore.Qt.AlignRight)
        
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
        self.mainWidget.addTab(self.axiomsWidget, QtGui.QIcon(':/icons/48/ic_save_black'), 'Export')
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
            for p in plugins_to_uninstall:
                plugins_to_uninstall_fmt.append('&nbsp;&nbsp;&nbsp;&nbsp;- {0} v{1}'.format(p.name(), p.version()))
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

        settings = QtCore.QSettings(ORGANIZATION, APPNAME)

        #############################################
        # EXPORT TAB
        #################################

        for axiom, checkbox in self.axiomsChecks.items():
            settings.setValue('export/axiom/{0}'.format(axiom.value), checkbox.isChecked())

        #############################################
        # EDITOR TAB
        #################################

        settings.setValue('diagram/size', self.diagramSizeField.value())

        #############################################
        # SAVE & EXIT
        #################################

        settings.sync()

        super(PreferencesDialog, self).accept()