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


import textwrap

from PyQt5 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from eddy.core.common import HasWidgetSystem
from eddy.core.datatypes.owl import OWLAxiom
from eddy.core.datatypes.qt import Font
from eddy.core.datatypes.system import Channel
from eddy.core.diagram import Diagram
from eddy.core.functions.signals import connect
from eddy.ui.fields import CheckBox
from eddy.ui.fields import ComboBox
from eddy.ui.fields import SpinBox


class PreferencesDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    This class implements the 'Preferences' dialog.
    """
    def __init__(self, session):
        """
        Initialize the Preferences dialog.
        :type session: Session
        """
        super().__init__(session)

        settings = QtCore.QSettings()

        #############################################
        # GENERAL TAB
        #################################

        ## EDITOR GROUP

        prefix = QtWidgets.QLabel(self, objectName='diagram_size_prefix')
        prefix.setText('Diagram size')
        self.addWidget(prefix)

        spinbox = SpinBox(self, objectName='diagram_size_field')
        spinbox.setRange(Diagram.MinSize, Diagram.MaxSize)
        spinbox.setSingleStep(100)
        spinbox.setToolTip('Default size of all the new created diagrams')
        spinbox.setValue(settings.value('diagram/size', 5000, int))
        self.addWidget(spinbox)

        prefix = QtWidgets.QLabel(self, objectName='diagram_font_size_prefix')
        prefix.setText('Diagram font size (px)')
        self.addWidget(prefix)

        spinbox = SpinBox(self, objectName='diagram_font_size_field')
        spinbox.setRange(Diagram.MinFontSize, Diagram.MaxFontSize)
        spinbox.setSingleStep(1)
        spinbox.setToolTip('Default font size for diagram labels (px)')
        spinbox.setValue(settings.value('diagram/fontsize', QtWidgets.qApp.font().pixelSize(), int))
        self.addWidget(spinbox)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('diagram_size_prefix'), self.widget('diagram_size_field'))
        formlayout.addRow(self.widget('diagram_font_size_prefix'), self.widget('diagram_font_size_field'))
        groupbox = QtWidgets.QGroupBox('Editor', self, objectName='editor_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        ## UPDATE GROUP

        prefix = QtWidgets.QLabel(self, objectName='update_startup_prefix')
        prefix.setText('Check for updates on startup')
        self.addWidget(prefix)

        checkbox = CheckBox(self, objectName='update_startup_checkbox')
        checkbox.setChecked(settings.value('update/check_on_startup', True, bool))
        checkbox.setToolTip('Whether or not application updates needs to be checked upon startup')
        self.addWidget(checkbox)

        prefix = QtWidgets.QLabel(self, objectName='update_channel_prefix')
        prefix.setText('Update channel')
        self.addWidget(prefix)

        combobox = ComboBox(objectName='update_channel_switch')
        combobox.setEditable(False)
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(False)
        combobox.setToolTip('Update channel (current = %s)' % settings.value('update/channel', Channel.Stable.value, str))
        combobox.addItems([x.value for x in Channel])
        combobox.setCurrentText(settings.value('update/channel', Channel.Stable.value, str))
        self.addWidget(combobox)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('update_startup_prefix'), self.widget('update_startup_checkbox'))
        formlayout.addRow(self.widget('update_channel_prefix'), self.widget('update_channel_switch'))
        groupbox = QtWidgets.QGroupBox('Update', self, objectName='update_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        ## GENERAL TAB LAYOUT CONFIGURATION

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('editor_widget'), 0, QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('update_widget'), 0, QtCore.Qt.AlignTop)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('general_widget')
        self.addWidget(widget)

        #############################################
        # EXPORT TAB
        #################################

        self.checks = {x: CheckBox(x.value, self) for x in OWLAxiom}
        for axiom, checkbox in self.checks.items():
            checkbox.setChecked(settings.value('export/axiom/{}'.format(axiom.value), True, bool))

        ## NON-LOGICAL GROUP

        layout = QtWidgets.QGridLayout()
        layout.setColumnMinimumWidth(0, 230)
        layout.setColumnMinimumWidth(1, 230)
        layout.setColumnMinimumWidth(2, 230)
        layout.addWidget(self.checks[OWLAxiom.Annotation], 0, 0)
        layout.addWidget(self.checks[OWLAxiom.Declaration], 0, 1)
        layout.addWidget(QtWidgets.QWidget(self), 0, 2)
        widget = QtWidgets.QGroupBox('Non-Logical', self, objectName='axioms_non_logical')
        widget.setLayout(layout)
        self.addWidget(widget)

        ## INTENSIONAL GROUP

        layout = QtWidgets.QGridLayout()
        layout.setColumnMinimumWidth(0, 230)
        layout.setColumnMinimumWidth(1, 230)
        layout.setColumnMinimumWidth(2, 230)
        layout.addWidget(self.checks[OWLAxiom.AsymmetricObjectProperty], 0, 0)
        layout.addWidget(self.checks[OWLAxiom.DataPropertyDomain], 1, 0)
        layout.addWidget(self.checks[OWLAxiom.DataPropertyRange], 2, 0)
        layout.addWidget(self.checks[OWLAxiom.DisjointClasses], 3, 0)
        layout.addWidget(self.checks[OWLAxiom.DisjointDataProperties], 4, 0)
        layout.addWidget(self.checks[OWLAxiom.DisjointObjectProperties], 5, 0)
        layout.addWidget(self.checks[OWLAxiom.EquivalentClasses], 6, 0)
        layout.addWidget(self.checks[OWLAxiom.EquivalentDataProperties], 7, 0)
        layout.addWidget(self.checks[OWLAxiom.EquivalentObjectProperties], 0, 1)
        layout.addWidget(self.checks[OWLAxiom.FunctionalDataProperty], 1, 1)
        layout.addWidget(self.checks[OWLAxiom.FunctionalObjectProperty], 2, 1)
        layout.addWidget(self.checks[OWLAxiom.HasKey], 3, 1)
        layout.addWidget(self.checks[OWLAxiom.InverseFunctionalObjectProperty], 4, 1)
        layout.addWidget(self.checks[OWLAxiom.InverseObjectProperties], 5, 1)
        layout.addWidget(self.checks[OWLAxiom.IrreflexiveObjectProperty], 6, 1)
        layout.addWidget(self.checks[OWLAxiom.ObjectPropertyDomain], 7, 1)
        layout.addWidget(self.checks[OWLAxiom.ObjectPropertyRange], 0, 2)
        layout.addWidget(self.checks[OWLAxiom.ReflexiveObjectProperty], 1, 2)
        layout.addWidget(self.checks[OWLAxiom.SubClassOf], 2, 2)
        layout.addWidget(self.checks[OWLAxiom.SubDataPropertyOf], 3, 2)
        layout.addWidget(self.checks[OWLAxiom.SubObjectPropertyOf], 4, 2)
        layout.addWidget(self.checks[OWLAxiom.SymmetricObjectProperty], 5, 2)
        layout.addWidget(self.checks[OWLAxiom.TransitiveObjectProperty], 6, 2)
        widget = QtWidgets.QGroupBox('Intensional', self, objectName='axioms_intensional')
        widget.setLayout(layout)
        self.addWidget(widget)

        ## EXTENSIONAL GROUP

        layout = QtWidgets.QGridLayout()
        layout.setColumnMinimumWidth(0, 230)
        layout.setColumnMinimumWidth(1, 230)
        layout.setColumnMinimumWidth(2, 230)
        layout.addWidget(self.checks[OWLAxiom.ClassAssertion], 0, 0)
        layout.addWidget(self.checks[OWLAxiom.DataPropertyAssertion], 1, 0)
        layout.addWidget(self.checks[OWLAxiom.DifferentIndividuals], 2, 0)
        layout.addWidget(self.checks[OWLAxiom.NegativeDataPropertyAssertion], 0, 1)
        layout.addWidget(self.checks[OWLAxiom.NegativeObjectPropertyAssertion], 1, 1)
        layout.addWidget(self.checks[OWLAxiom.ObjectPropertyAssertion], 2, 1)
        layout.addWidget(self.checks[OWLAxiom.SameIndividual], 0, 2)
        widget = QtWidgets.QGroupBox('Extensional', self, objectName='axioms_extensional')
        widget.setLayout(layout)
        self.addWidget(widget)

        ## LOGICAL GROUP

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.widget('axioms_intensional'))
        layout.addWidget(self.widget('axioms_extensional'))
        widget = QtWidgets.QGroupBox('Logical', self, objectName='axioms_logical')
        widget.setLayout(layout)
        self.addWidget(widget)

        ## EXPORT TAB LAYOUT CONFIGURATION

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.widget('axioms_non_logical'))
        layout.addWidget(self.widget('axioms_logical'))
        groupbox = QtWidgets.QGroupBox('OWL 2 Axioms for which exporting is enabled', self)
        groupbox.setLayout(layout)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(groupbox)
        widget = QtWidgets.QWidget(self, objectName='axioms_widget')
        widget.setLayout(layout)
        self.addWidget(widget)

        #############################################
        # PLUGINS TAB
        #################################

        table = QtWidgets.QTableWidget(len(self.session.plugins()), 3, self, objectName='plugins_table')
        table.setHorizontalHeaderLabels(['Name', 'Version',  'Uninstall'])
        table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        table.setFocusPolicy(QtCore.Qt.NoFocus)
        self.addWidget(table)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Fixed)
        header.setSectionsClickable(False)
        header.setSectionsMovable(False)
        header = table.verticalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        self.uninstall = dict()
        for row, plugin in enumerate(sorted(self.session.plugins(), key=lambda x: x.name())):
            item = QtWidgets.QTableWidgetItem(plugin.name())
            item.setTextAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            table.setItem(row, 0, item)
            item = QtWidgets.QTableWidgetItem('v{0}'.format(plugin.version()))
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
            table.setItem(row, 1, item)
            p_widget = QtWidgets.QWidget()
            p_checkbox = CheckBox()
            p_checkbox.setEnabled(not plugin.isBuiltIn())
            p_layout = QtWidgets.QHBoxLayout(p_widget)
            p_layout.addWidget(p_checkbox)
            p_layout.setAlignment(QtCore.Qt.AlignCenter)
            p_layout.setContentsMargins(0, 0, 0, 0)
            table.setCellWidget(row, 2, p_widget)
            self.uninstall[plugin] = p_checkbox

        button = QtWidgets.QToolButton(self, objectName='plugins_install_button')
        button.setDefaultAction(self.session.action('install_plugin'))
        button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.addWidget(button)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.widget('plugins_table'), 1)
        layout.addWidget(self.widget('plugins_install_button'), 0, QtCore.Qt.AlignRight)
        widget = QtWidgets.QWidget(objectName='plugins_widget')
        widget.setLayout(layout)
        self.addWidget(widget)

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self, objectName='confirmation_widget')
        confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setContentsMargins(10, 0, 10, 10)
        self.addWidget(confirmation)

        #############################################
        # MAIN WIDGET
        #################################

        widget = QtWidgets.QTabWidget(self, objectName='main_widget')
        widget.addTab(self.widget('general_widget'), QtGui.QIcon(':/icons/24/ic_settings_black'), 'General')
        widget.addTab(self.widget('axioms_widget'), QtGui.QIcon(':/icons/24/ic_export_black'), 'Export')
        widget.addTab(self.widget('plugins_widget'), QtGui.QIcon(':/icons/24/ic_extension_black'), 'Plugins')
        self.addWidget(widget)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(740, 420)
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Preferences')

        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

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

        plugins_to_uninstall = [plugin for plugin, checkbox in self.uninstall.items() if checkbox.isChecked()]
        if plugins_to_uninstall:
            plugins_to_uninstall_fmt = []
            for p in plugins_to_uninstall:
                plugins_to_uninstall_fmt.append('&nbsp;&nbsp;&nbsp;&nbsp;- {0} v{1}'.format(p.name(), p.version()))
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_help_outline_black').pixmap(48))
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

        settings = QtCore.QSettings()

        #############################################
        # EXPORT TAB
        #################################

        for axiom, checkbox in self.checks.items():
            settings.setValue('export/axiom/{0}'.format(axiom.value), checkbox.isChecked())

        #############################################
        # GENERAL TAB
        #################################

        settings.setValue('diagram/size', self.widget('diagram_size_field').value())
        settings.setValue('diagram/fontsize', self.widget('diagram_font_size_field').value())
        settings.setValue('update/channel', self.widget('update_channel_switch').currentText())
        settings.setValue('update/check_on_startup', self.widget('update_startup_checkbox').isChecked())

        for diagram in self.session.project.diagrams():
            QtWidgets.QApplication.processEvents()
            diagram.setFont(Font(font=diagram.font(), pixelSize=self.widget('diagram_font_size_field').value()))

        #############################################
        # SAVE & EXIT
        #################################

        settings.sync()

        super().accept()
