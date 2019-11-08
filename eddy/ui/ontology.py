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


from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy import ORGANIZATION, APPNAME
from eddy.core.common import HasWidgetSystem
from eddy.core.datatypes.qt import Font
from eddy.core.functions.signals import connect
from eddy.core.output import getLogger
from eddy.ui.fields import StringField

LOGGER = getLogger()


class OntologyManagerDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    This class implements the 'Ontology Manager' dialog.
    """
    def __init__(self, session):
        """
        Initialize the Ontology Manager dialog.
        :type session: Session
        """
        super().__init__(session)

        settings = QtCore.QSettings(ORGANIZATION, APPNAME)

        #############################################
        # GENERAL TAB
        #################################

        ## ONTOLOGY PROPERTIES GROUP

        iriLabel = QtWidgets.QLabel(self, objectName='ontology_iri_label')
        iriLabel.setFont(Font('Roboto', 13))
        iriLabel.setText('Ontology IRI')
        self.addWidget(iriLabel)

        iriField = StringField(self, objectName='ontology_iri_field')
        iriField.setFont(Font('Roboto', 13))
        iriField.setPlaceholderText('e.g. http://example.com/ontologies/myontology/')
        self.addWidget(iriField)

        versionLabel = QtWidgets.QLabel(self, objectName='ontology_version_label')
        versionLabel.setFont(Font('Roboto', 13))
        versionLabel.setText('Ontology Version IRI')
        self.addWidget(versionLabel)

        versionField = StringField(self, objectName='ontology_version_field')
        versionField.setFont(Font('Roboto', 13))
        versionField.setPlaceholderText('e.g. http://example.com/ontologies/myontology/1.0')
        self.addWidget(versionField)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('ontology_iri_label'), self.widget('ontology_iri_field'))
        formlayout.addRow(self.widget('ontology_version_label'), self.widget('ontology_version_field'))
        groupbox = QtWidgets.QGroupBox('Ontology IRI', self, objectName='ontology_iri_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        ## ONTOLOGY IMPORTS GROUP

        table = QtWidgets.QTableWidget(0, 2, self, objectName='ontology_imports_table_widget')
        table.setHorizontalHeaderLabels(['Name', 'Ontology IRI'])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionsClickable(False)
        table.horizontalHeader().setMinimumSectionSize(130)
        table.horizontalHeader().setSectionsClickable(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setSectionsClickable(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setFont(Font('Roboto', 13))
        self.addWidget(table)

        addBtn = QtWidgets.QPushButton('Add', objectName='ontology_imports_add_button')
        delBtn = QtWidgets.QPushButton('Remove', objectName='ontology_imports_delete_button')
        connect(addBtn.clicked, self.addOntologyImport)
        connect(delBtn.clicked, self.removeOntologyImport)
        self.addWidget(addBtn)
        self.addWidget(delBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('ontology_imports_add_button'))
        boxlayout.addWidget(self.widget('ontology_imports_delete_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('ontology_imports_table_widget'))
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Imported Ontologies', self, objectName='ontology_imports_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        ## ONTOLOGY ANNOTATIONS GROUP

        table = QtWidgets.QTableWidget(0, 3, self, objectName='ontology_annotations_table_widget')
        table.setHorizontalHeaderLabels(['Annotation', 'Datatype', 'Value'])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionsClickable(False)
        table.horizontalHeader().setMinimumSectionSize(100)
        table.horizontalHeader().setSectionsClickable(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setSectionsClickable(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setFont(Font('Roboto', 13))
        self.addWidget(table)

        addBtn = QtWidgets.QPushButton('Add', objectName='ontology_annotations_add_button')
        delBtn = QtWidgets.QPushButton('Remove', objectName='ontology_annotations_delete_button')
        connect(addBtn.clicked, self.addOntologyAnnotation)
        connect(delBtn.clicked, self.removeOntologyAnnotation)
        self.addWidget(addBtn)
        self.addWidget(delBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('ontology_annotations_add_button'))
        boxlayout.addWidget(self.widget('ontology_annotations_delete_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('ontology_annotations_table_widget'))
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Ontology Annotations', self, objectName='ontology_annotations_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        ## GENERAL TAB LAYOUT CONFIGURATION

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('ontology_iri_widget'), 0, QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('ontology_imports_widget'), 0, QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('ontology_annotations_widget'), 0, QtCore.Qt.AlignTop)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('general_widget')
        self.addWidget(widget)

        #############################################
        # PREFIXES TAB
        #################################

        ## PREFIXES GROUP
        table = QtWidgets.QTableWidget(1, 2, self, objectName='prefixes_table_widget')
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionsClickable(False)
        table.horizontalHeader().setMinimumSectionSize(100)
        table.horizontalHeader().setSectionsClickable(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setSectionsClickable(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setFont(Font('Roboto', 13))
        self.addWidget(table)

        addBtn = QtWidgets.QPushButton('Add', objectName='prefixes_add_button')
        delBtn = QtWidgets.QPushButton('Remove', objectName='prefixes_delete_button')
        connect(addBtn.clicked, self.addPrefix)
        connect(delBtn.clicked, self.removePrefix)
        self.addWidget(addBtn)
        self.addWidget(delBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('prefixes_add_button'))
        boxlayout.addWidget(self.widget('prefixes_delete_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('prefixes_table_widget'))
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Ontology Prefixes', self, objectName='prefixes_group_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        ## PREFIXES TAB LAYOUT CONFIGURATION

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('prefixes_group_widget'), 0, QtCore.Qt.AlignTop)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('prefixes_widget')
        self.addWidget(widget)

        #############################################
        # ANNOTATIONS TAB
        #################################

        ## ANNOTATIONS GROUP

        table = QtWidgets.QTableWidget(0, 2, self, objectName='annotation_properties_table_widget')
        table.setHorizontalHeaderLabels(['IRI', 'Comment'])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionsClickable(False)
        table.horizontalHeader().setMinimumSectionSize(100)
        table.horizontalHeader().setSectionsClickable(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setSectionsClickable(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setFont(Font('Roboto', 13))
        self.addWidget(table)

        addBtn = QtWidgets.QPushButton('Add', objectName='annotation_properties_add_button')
        delBtn = QtWidgets.QPushButton('Remove', objectName='annotation_properties_delete_button')
        connect(addBtn.clicked, self.addAnnotationProperty)
        connect(delBtn.clicked, self.removeAnnotationProperty)
        self.addWidget(addBtn)
        self.addWidget(delBtn)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.widget('annotation_properties_add_button'))
        boxlayout.addWidget(self.widget('annotation_properties_delete_button'))

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('annotation_properties_table_widget'))
        formlayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Annotation Properties', self, objectName='annotation_properties_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)

        ## ANNOTATIONS TAB LAYOUT CONFIGURATION

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(self.widget('annotation_properties_widget'), 0, QtCore.Qt.AlignTop)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.setObjectName('annotations_widget')
        self.addWidget(widget)

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self, objectName='confirmation_widget')
        confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setContentsMargins(10, 0, 10, 10)
        confirmation.setFont(Font('Roboto', 12))
        self.addWidget(confirmation)

        #############################################
        # MAIN WIDGET
        #################################

        widget = QtWidgets.QTabWidget(self, objectName='main_widget')
        widget.addTab(self.widget('general_widget'), 'General')
        widget.addTab(self.widget('prefixes_widget'), 'Prefixes')
        widget.addTab(self.widget('annotations_widget'), 'Annotations')
        self.addWidget(widget)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('main_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(800, 520)
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Ontology Manager')
        self.redraw()

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
    def redraw(self):
        """
        Redraw the dialog components, reloading their contents.
        """
        session = self.session
        project = session.project
        manager = project.prefixManager

        #############################################
        # GENERAL TAB
        #################################
        iriField = self.widget('ontology_iri_field')
        if project.iri and project.iri != 'NULL':
            iriField.setText(project.iri)

        versionField = self.widget('ontology_version_field')
        if project.version and project.version != 'NULL':
            versionField.setText(project.version)

        # TODO: reload imports when they are implemented

        #############################################
        # PREFIXES TAB
        #################################

        # Reload prefixes table contents
        table = self.widget('prefixes_table_widget')
        table.clear()
        table.setRowCount(len(manager))
        table.setHorizontalHeaderLabels(['Prefix', 'Namespace'])

        rowcount = 0
        for prefix in manager:
            table.setItem(rowcount, 0, QtWidgets.QTableWidgetItem(prefix))
            table.setItem(rowcount, 1, QtWidgets.QTableWidgetItem(str(manager.getPrefix(prefix))))
            rowcount += 1
        table.resizeColumnsToContents()

        #############################################
        # ANNOTATIONS TAB
        #################################

        # TODO: complete annotations support when it is implemented

        #############################################
        # SAVE & EXIT
        #################################

    @QtCore.pyqtSlot(bool)
    def addOntologyImport(self, _):
        """
        Adds an ontology import to the current project.
        :type _: bool
        """
        # TODO: not implemented yet
        LOGGER.debug("addOntologyImport called")

    @QtCore.pyqtSlot(bool)
    def removeOntologyImport(self, _):
        """
        Removes an ontology import from the current project.
        :type _: bool
        """
        # TODO: not implemented yet
        LOGGER.debug("removeOntologyImport called")

    @QtCore.pyqtSlot(bool)
    def addOntologyAnnotation(self, _):
        """
        Adds an annotation to the current ontology.
        :type _: bool
        """
        # TODO: not implemented yet
        LOGGER.debug("addOntologyAnnotation called")

    @QtCore.pyqtSlot(bool)
    def removeOntologyAnnotation(self, _):
        """
        Removes an annotation from the current ontology.
        :type _: bool
        """
        # TODO: not implemented yet
        LOGGER.debug("removeOntologyAnnotation called")

    @QtCore.pyqtSlot(bool)
    def addPrefix(self, _):
        """
        Add a new prefix entry to the list of ontology prefixes.
        :type _: bool
        """
        table = self.widget('prefixes_table_widget')
        rowcount = table.rowCount()
        table.setRowCount(rowcount + 1)
        table.setItem(rowcount, 0, QtWidgets.QTableWidgetItem('p0'))
        table.setItem(rowcount, 1, QtWidgets.QTableWidgetItem(self.session.project.iri or ''))
        table.scrollToItem(table.item(rowcount, 0))
        table.editItem(table.item(rowcount, 0))

    @QtCore.pyqtSlot(bool)
    def removePrefix(self, _):
        """
        Removes a set of prefix entries from the list of ontology prefixes.
        :type _: bool
        """
        table = self.widget('prefixes_table_widget')
        rowcount = table.rowCount()
        selectedRanges = table.selectedRanges()
        for selectedRange in selectedRanges:
            for row in range(selectedRange.bottomRow(), selectedRange.topRow() + 1):
                table.removeRow(row)
        table.setRowCount(rowcount - sum(map(lambda x: x.rowCount(), selectedRanges)))

    @QtCore.pyqtSlot(bool)
    def addAnnotationProperty(self, _):
        """
        Adds an annotation property to the ontology alphabet.
        :type _: bool
        """
        # TODO: not implemented yet
        LOGGER.debug("addAnnotationProperty called")

    @QtCore.pyqtSlot(bool)
    def removeAnnotationProperty(self, _):
        """
        Removes an annotation property from the ontology alphabet.
        :type _: bool
        """
        # TODO: not implemented yet
        LOGGER.debug("removeAnnotationProperty called")

    @QtCore.pyqtSlot()
    def accept(self):
        """
        Executed when the dialog is accepted.
        """
        ##
        ## TODO: complete validation and settings save
        ##
        #############################################
        # GENERAL TAB
        #################################

        #############################################
        # PREFIXES TAB
        #################################

        #############################################
        # ANNOTATIONS TAB
        #################################

        #############################################
        # SAVE & EXIT
        #################################

        super().accept()
