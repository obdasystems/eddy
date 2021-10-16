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
    QtPrintSupport,
)

from eddy.core.common import HasWidgetSystem
from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.qt import Font
from eddy.core.datatypes.system import File
from eddy.core.exporters.common import (
    AbstractDiagramExporter,
    AbstractProjectExporter,
)
from eddy.core.functions.misc import natsorted
from eddy.core.functions.path import openPath
from eddy.core.functions.signals import connect
from eddy.core.items.common import AbstractItem
from eddy.core.output import getLogger
from eddy.core.project import (
    K_ASYMMETRIC,
    K_FUNCTIONAL,
    K_INVERSE_FUNCTIONAL,
    K_IRREFLEXIVE,
    K_REFLEXIVE,
    K_SYMMETRIC,
    K_TRANSITIVE,
)
from eddy.ui.dialogs import DiagramSelectionDialog

LOGGER = getLogger()


class PdfDiagramExporter(AbstractDiagramExporter):
    """
    Extends AbstractDiagramExporter with facilities to export the structure of Graphol diagrams in PDF format.
    """
    def __init__(self, diagram, session=None, **kwargs):
        """
        Initialize the Pdf Exporter.
        :type session: Session
        """
        super().__init__(diagram, session)
        self.open = kwargs.get('open', False)

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        :return: File
        """
        return File.Pdf

    def run(self, path):
        """
        Perform PDF document generation.
        :type path: str
        """
        shape = self.diagram.visibleRect(margin=20)
        if shape:
            LOGGER.info('Exporting diagram %s to %s', self.diagram.name, path)
            printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
            printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            printer.setPaperSize(QtPrintSupport.QPrinter.Custom)
            printer.setPageSize(QtGui.QPageSize(QtCore.QSizeF(shape.width(), shape.height()), QtGui.QPageSize.Point))
            painter = QtGui.QPainter()
            if painter.begin(printer):
                # TURN CACHING OFF
                for item in self.diagram.items():
                    if item.isNode() or item.isEdge():
                        item.setCacheMode(AbstractItem.NoCache)
                # RENDER THE DIAGRAM IN THE PAINTER
                self.diagram.render(painter, source=shape)
                # TURN CACHING ON
                for item in self.diagram.items():
                    if item.isNode() or item.isEdge():
                        item.setCacheMode(AbstractItem.DeviceCoordinateCache)
                # COMPLETE THE EXPORT
                painter.end()
                # OPEN THE DOCUMENT
                if self.open:
                    openPath(path)


class PdfProjectExporter(AbstractProjectExporter):
    """
    Extends AbstractProjectExporter with facilities to export the structure of Graphol diagrams in PDF format.
    """

    def __init__(self, project, session=None, **kwargs):
        """
        Initialize the Pdf Exporter.
        :type session: Session
        """
        super().__init__(project, session)

        self.diagrams = kwargs.get('diagrams', None)
        self.includeTables = kwargs.get('includeTables', None)
        self.open = kwargs.get('open', False)
        self.pageSize = kwargs.get('pageSize', None)
        self.rowsPerPage = 23

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        :return: File
        """
        return File.Pdf

    def run(self, path):
        """
        Perform PDF document generation.
        :type path: str
        """
        printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
        printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        printer.setOrientation(QtPrintSupport.QPrinter.Landscape)
        printer.setPrinterName(self.project.name)
        painter = QtGui.QPainter()

        # DIAGRAM SELECTION
        if self.diagrams is None:
            dialog = DiagramSelectionDialog(self.session)
            if not dialog.exec_():
                return
            self.diagrams = dialog.selectedDiagrams()
        # DIAGRAM PAGE SIZE SELECTION
        if self.pageSize is None:
            dialog = PageSetupDialog(printer, self.session)
            if not dialog.exec_():
                return
        else:
            printer.setPageSize(self.pageSize)
        # ENTITY TABLES SELECTION
        if self.includeTables is None:
            dialog = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Question,
                'PDF Export',
                'Include entity tables in the generated PDF?',
                buttons=(
                    QtWidgets.QMessageBox.Yes
                    | QtWidgets.QMessageBox.No
                    | QtWidgets.QMessageBox.Cancel
                ),
                parent=self.session,
            )
            result = dialog.exec_()
            if result == QtWidgets.QMessageBox.Cancel:
                return
            self.includeTables = result == QtWidgets.QMessageBox.Yes

        ##############################################################
        # DIAGRAMS
        ##############################################################

        for n, diagram in enumerate(natsorted(self.diagrams, key=lambda diagram: diagram.name)):
            shape = diagram.visibleRect(margin=400)
            if shape:
                if n > 0:
                    printer.newPage()
                if painter.isActive() or painter.begin(printer):
                    # TURN CACHING OFF
                    for item in diagram.items():
                        if item.isNode() or item.isEdge():
                            item.setCacheMode(AbstractItem.NoCache)
                    # RENDER THE DIAGRAM
                    diagram.render(painter, source=shape)
                    # RENDER DIAGRAM NAME
                    title = QtGui.QTextDocument()
                    title.setDefaultFont(Font(pixelSize=140))
                    title.setHtml('{0}<hr width=100%/>'.format(diagram.name))
                    title.setTextWidth(printer.pageRect().width())
                    title.drawContents(painter)
                    # TURN CACHING ON
                    for item in diagram.items():
                        if item.isNode() or item.isEdge():
                            item.setCacheMode(AbstractItem.DeviceCoordinateCache)

        ##############################################################
        # ENTITY TABLES
        ##############################################################

        if self.includeTables:

            ##############################################################
            # IRI TABLE
            ##############################################################

            # RESET PAGE SIZE AND ORIENTATION FOR PREDICATE TABLES
            printer.setPageSize(QtPrintSupport.QPrinter.A4)
            printer.setOrientation(QtPrintSupport.QPrinter.Landscape)
            printer.setPageMargins(12.5, 12.5, 12.5, 12.5, QtPrintSupport.QPrinter.Millimeter)

            prefixRows = []
            for prefix in sorted(self.project.getManagedPrefixes()):
                ns = self.project.getPrefixResolution(prefix)
                prefixRows.append(dedent('''
                        <tr>
                            <td width=25%>{0}</td>
                            <td width=75%>{1}</td>
                        </tr>
                    '''.format(prefix, ns)))
            sections = [
                prefixRows[i:i+self.rowsPerPage]
                for i in range(0, len(prefixRows), self.rowsPerPage)
            ]

            for section in sections:
                if len(section) > 0:
                    if len(self.diagrams) > 0:
                        printer.newPage()
                    doc = QtGui.QTextDocument()
                    htmlTable = '''
                    <table width=100% border=5 cellspacing=0 cellpadding=60>
                        <thead>
                            <tr>
                                <th bgcolor=#c8c8c8>PREFIX</th>
                                <th bgcolor=#c8c8c8>IRI</th>
                            </tr>
                        </thead>
                     <tbody>'''
                    htmlTable += '\n'.join(section)
                    htmlTable += '</tbody>'
                    htmlTable += '</table>'
                    doc.setDefaultFont(Font(pixelSize=180))
                    doc.setHtml(htmlTable)
                    doc.setPageSize(QtCore.QSizeF(printer.pageRect().size()))
                    doc.drawContents(painter)

            ##############################################################
            # ROLES AND ATTRIBUTES TABLE
            ##############################################################

            predicateRows = []
            predicates = set()
            for item in {Item.RoleNode, Item.AttributeNode}:
                for node in self.project.iriOccurrences(item=item):
                    if not node.iri.isTopBottomEntity():
                        predicates.add(node.iri)

            for predicate in sorted(predicates, key=str):
                meta = predicate.getMetaProperties()
                attributes = [
                    meta.get(K_FUNCTIONAL, False),
                    meta.get(K_INVERSE_FUNCTIONAL, False),
                    meta.get(K_REFLEXIVE, False),
                    meta.get(K_IRREFLEXIVE, False),
                    meta.get(K_SYMMETRIC, False),
                    meta.get(K_ASYMMETRIC, False),
                    meta.get(K_TRANSITIVE, False),
                ]
                predicateRows.append('''
                    <tr>
                        <td width=30%>{0}</td>
                        <td width=10%><center>{1}</center></td>
                        <td width=10%><center>{2}</center></td>
                        <td width=10%><center>{3}</center></td>
                        <td width=10%><center>{4}</center></td>
                        <td width=10%><center>{5}</center></td>
                        <td width=10%><center>{6}</center></td>
                        <td width=10%><center>{7}</center></td>
                    </tr>
                '''.format(str(predicate), *map(lambda x: u'\u2713' if x else '', attributes)))
            sections = [
                predicateRows[i:i+self.rowsPerPage]
                for i in range(0, len(predicateRows), self.rowsPerPage)
            ]

            for section in sections:
                if len(section) > 0:
                    if len(self.diagrams) > 0:
                        printer.newPage()
                    doc = QtGui.QTextDocument()
                    htmlTable = '''
                    <table width=100% border=5 cellspacing=0 cellpadding=60>
                        <thead>
                            <tr>
                                <th bgcolor=#c8c8c8>ENTITY</th>
                                <th bgcolor=#c8c8c8>FUNCT</th>
                                <th bgcolor=#c8c8c8>INVERSE FUNCT</th>
                                <th bgcolor=#c8c8c8>TRANS</th>
                                <th bgcolor=#c8c8c8>REFL</th>
                                <th bgcolor=#c8c8c8>IRREFL</th>
                                <th bgcolor=#c8c8c8>SYMM</th>
                                <th bgcolor=#c8c8c8>ASYMM</th>
                            </tr>
                        </thead>
                     <tbody>'''
                    htmlTable += '\n'.join(section)
                    htmlTable += '</tbody>'
                    htmlTable += '</table>'
                    doc.setDefaultFont(Font(pixelSize=180))
                    doc.setHtml(htmlTable)
                    doc.setPageSize(QtCore.QSizeF(printer.pageRect().size()))
                    doc.drawContents(painter)

        # COMPLETE THE EXPORT
        if painter.isActive():
            painter.end()

        # OPEN THE DOCUMENT
        if self.open:
            openPath(printer.outputFileName())


class PageSetupDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    Extends QtWidgets.QDialog to recreate the platform-independent version of QPageSetupDialog.
    """
    # noinspection PyArgumentList
    def __init__(self, printer=None, parent=None):
        """
        Initializes the PageSetupDialog.
        """
        super().__init__(parent)

        self.printer = printer or QtPrintSupport.QPrinter()
        self.units = QtGui.QPageLayout.Millimeter

        #############################################
        #   UNITS
        #################################

        combobox = QtWidgets.QComboBox(self, objectName='units_combobox')
        combobox.addItem('Millimiters (mm)', QtGui.QPageLayout.Millimeter)
        combobox.addItem('Inches (in)', QtGui.QPageLayout.Inch)
        combobox.addItem('Points (pt)', QtGui.QPageLayout.Point)
        combobox.addItem('Pica (P̸)', QtGui.QPageLayout.Pica)
        combobox.addItem('Didot (DD)', QtGui.QPageLayout.Didot)
        combobox.addItem('Cicero (CC)', QtGui.QPageLayout.Cicero)
        connect(combobox.currentIndexChanged, self.onUnitsChanged)
        self.addWidget(combobox)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.widget('units_combobox'))

        groupbox = QtWidgets.QGroupBox('Units', self, objectName='units_group')
        groupbox.setLayout(layout)
        self.addWidget(groupbox)

        #############################################
        #   PAPER
        #################################

        label = QtWidgets.QLabel('Page size', self, objectName='page_size_label')
        combobox = QtWidgets.QComboBox(self, objectName='page_size_combobox')
        for sizeId in range(QtGui.QPageSize.A4, QtGui.QPageSize.LastPageSize):
            pageSize = QtGui.QPageSize(QtGui.QPageSize.PageSizeId(sizeId))
            combobox.addItem(pageSize.name() or 'Custom', pageSize)
        connect(combobox.currentIndexChanged, self.onPaperSizeChanged)
        self.addWidget(label)
        self.addWidget(combobox)

        labelW = QtWidgets.QLabel('Width', self, objectName='page_custom_width_label')
        spinboxW = QtWidgets.QDoubleSpinBox(self, objectName='page_custom_width_spinbox')
        self.addWidget(labelW)
        self.addWidget(spinboxW)

        labelH = QtWidgets.QLabel('Height', self, objectName='page_custom_height_label')
        spinboxH = QtWidgets.QDoubleSpinBox(self, objectName='page_custom_height_spinbox')
        self.addWidget(labelH)
        self.addWidget(spinboxH)

        layout = QtWidgets.QFormLayout()
        layout.addRow(self.widget('page_size_label'), self.widget('page_size_combobox'))
        layout.addRow(self.widget('page_custom_width_label'), self.widget('page_custom_width_spinbox'))
        layout.addRow(self.widget('page_custom_height_label'), self.widget('page_custom_height_spinbox'))

        groupbox = QtWidgets.QGroupBox('Paper', self, objectName='paper_group')
        groupbox.setLayout(layout)
        self.addWidget(groupbox)

        #############################################
        #   ORIENTATION
        #################################

        portrait = QtWidgets.QRadioButton('Portrait', self, objectName='orientation_portrait_radio')
        landscape = QtWidgets.QRadioButton('Landscape', self, objectName='orientation_landscape_radio')
        connect(portrait.toggled, self.onOrientationChanged)
        connect(landscape.toggled, self.onOrientationChanged)
        self.addWidget(portrait)
        self.addWidget(landscape)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(portrait)
        layout.addWidget(landscape)

        groupbox = QtWidgets.QGroupBox('Orientation', self, objectName='orientation_group')
        groupbox.setLayout(layout)
        self.addWidget(groupbox)

        #############################################
        #   MARGINS
        #################################

        spinboxT = QtWidgets.QDoubleSpinBox(self, objectName='margin_top_spinbox')
        spinboxB = QtWidgets.QDoubleSpinBox(self, objectName='margin_bottom_spinbox')
        spinboxL = QtWidgets.QDoubleSpinBox(self, objectName='margin_left_spinbox')
        spinboxR = QtWidgets.QDoubleSpinBox(self, objectName='margin_right_spinbox')
        self.addWidgets((spinboxT, spinboxB, spinboxL, spinboxR))

        layout = QtWidgets.QGridLayout()
        layout.addWidget(spinboxT, 0, 1)
        layout.addWidget(spinboxR, 1, 0)
        layout.addWidget(spinboxL, 1, 2)
        layout.addWidget(spinboxB, 2, 1)

        groupbox = QtWidgets.QGroupBox('Margins', self, objectName='margins_group')
        groupbox.setLayout(layout)
        self.addWidget(groupbox)

        #############################################
        #   BUTTONS
        #################################

        confirmation = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self, objectName='confirmation_buttons')
        self.addWidget(confirmation)

        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

        #############################################
        #   MAIN LAYOUT
        #################################

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.widget('units_group'))
        mainLayout.addWidget(self.widget('paper_group'))
        mainLayout.addWidget(self.widget('orientation_group'))
        mainLayout.addWidget(self.widget('margins_group'))
        mainLayout.addWidget(self.widget('confirmation_buttons'))

        self.setLayout(mainLayout)
        self.adjustSize()
        self.setWindowTitle('Page Setup')
        self.reloadPrinterLayout()
        # START WITH MILLIMITER UNITS
        combobox = self.widget('units_combobox')
        combobox.setCurrentIndex(combobox.findData(QtGui.QPageLayout.Millimeter))
        combobox.currentIndexChanged.emit(combobox.findData(QtGui.QPageLayout.Millimeter))

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(bool)
    def onOrientationChanged(self, _):
        """
        Executed when one of the orientation radio buttons is checked.
        :type _: bool
        """
        # TRIGGER UNITS UPDATE TO SET MARGINS RANGE
        self.convertUnits(self.units, self.units)

    @QtCore.pyqtSlot(int)
    def onPaperSizeChanged(self, index):
        """
        Executed when the paper size is selected through the QComboBox.
        :type index: int
        """
        data = self.widget('page_size_combobox').itemData(index)
        self.widget('page_custom_width_spinbox').setEnabled(data.id() == QtGui.QPageSize.Custom)
        self.widget('page_custom_width_spinbox').setRange(0, 9999)
        self.widget('page_custom_height_spinbox').setEnabled(data.id() == QtGui.QPageSize.Custom)
        self.widget('page_custom_height_spinbox').setRange(0, 9999)
        # TRIGGER UNITS UPDATE TO SET MARGINS RANGE
        self.convertUnits(self.units, self.units)

    @QtCore.pyqtSlot(int)
    def onUnitsChanged(self, index):
        """
        Executed when the units are selected through the QComboBox.
        :type index: int
        """
        combobox = self.widget('units_combobox')
        toUnits = combobox.itemData(index)
        self.convertUnits(self.units, toUnits)
        self.units = toUnits

    #############################################
    #   INTERFACE
    #################################

    def accept(self):
        """
        Executed when the dialog is accepted.
        Saves the user selections to the printer.
        """
        pageLayout = self.printer.pageLayout()
        pageUnits = self.units
        pageLayout.setUnits(pageUnits)
        # PAGE SIZE
        combobox = self.widget('page_size_combobox')
        pageSize = combobox.currentData()
        spinboxW = self.widget('page_custom_width_spinbox')
        customWidth = spinboxW.value()
        spinboxH = self.widget('page_custom_height_spinbox')
        customHeight = spinboxH.value()
        if pageSize.id() == QtGui.QPageSize.Custom:
            pageSize = QtGui.QPageSize(QtCore.QSizeF(customWidth, customHeight), pageUnits)
        pageLayout.setPageSize(pageSize)
        # ORIENTATION
        portrait = self.widget('orientation_portrait_radio')
        landscape = self.widget('orientation_landscape_radio')
        if portrait.isChecked():
            pageLayout.setOrientation(QtGui.QPageLayout.Portrait)
        elif landscape.isChecked():
            pageLayout.setOrientation(QtGui.QPageLayout.Landscape)
        # MARGINS
        spinboxT = self.widget('margin_top_spinbox')
        spinboxB = self.widget('margin_bottom_spinbox')
        spinboxL = self.widget('margin_left_spinbox')
        spinboxR = self.widget('margin_right_spinbox')
        pageMargins = QtCore.QMarginsF(
            spinboxL.value(), spinboxT.value(), spinboxR.value(), spinboxB.value())
        pageLayout.setMargins(pageMargins)
        # UPDATE PRINTER LAYOUT
        self.printer.setPageLayout(pageLayout)
        super().accept()

    def convertUnits(self, fromUnits, toUnits):
        """
        Updates the UI values from units fromUnits to toUnits, recomputing margin ranges.
        :type fromUnits: QtGui.QPageSize.Unit
        :type toUnits:  QtGui.QPageSize.Unit
        """
        # We copy the current printer page layout and set its units, orientation
        # and page size to the target units, orientation and page size to reflect
        # values in the UI which will trigger the computation of the new minimum
        # and maximum margins.
        combobox = self.widget('page_size_combobox')
        portrait = self.widget('orientation_portrait_radio')
        pageLayout = self.printer.pageLayout()
        pageLayout.setPageSize(QtGui.QPageSize(combobox.currentData()))
        pageLayout.setOrientation(QtGui.QPageLayout.Portrait if portrait.isChecked() else QtGui.QPageLayout.Landscape)
        pageLayout.setUnits(toUnits)
        pageMarginsMin = pageLayout.minimumMargins()
        pageMarginsMax = pageLayout.maximumMargins()
        unitSuffix = ('mm', 'pt', 'in', 'P̸', 'DD', 'CC')[toUnits]
        # CUSTOM WIDTH AND HEIGHT
        spinboxW = self.widget('page_custom_width_spinbox')
        spinboxW.setValue(self.convertValue(spinboxW.value(), fromUnits, toUnits))
        spinboxW.setSuffix(unitSuffix)
        spinboxH = self.widget('page_custom_height_spinbox')
        spinboxH.setValue(self.convertValue(spinboxH.value(), fromUnits, toUnits))
        spinboxH.setSuffix(unitSuffix)
        # UPDATE MARGINS
        spinboxT = self.widget('margin_top_spinbox')
        value = self.convertValue(spinboxT.value(), fromUnits, toUnits)
        spinboxT.setRange(pageMarginsMin.top(), pageMarginsMax.top())
        spinboxT.setSuffix(unitSuffix)
        spinboxT.setValue(value)
        spinboxB = self.widget('margin_bottom_spinbox')
        value = self.convertValue(spinboxB.value(), fromUnits, toUnits)
        spinboxB.setRange(pageMarginsMin.bottom(), pageMarginsMax.bottom())
        spinboxB.setSuffix(unitSuffix)
        spinboxB.setValue(value)
        spinboxL = self.widget('margin_left_spinbox')
        value = self.convertValue(spinboxL.value(), fromUnits, toUnits)
        spinboxL.setRange(pageMarginsMin.left(), pageMarginsMax.left())
        spinboxL.setSuffix(unitSuffix)
        spinboxL.setValue(value)
        spinboxR = self.widget('margin_right_spinbox')
        value = self.convertValue(spinboxR.value(), fromUnits, toUnits)
        spinboxR.setRange(pageMarginsMin.right(), pageMarginsMax.right())
        spinboxR.setSuffix(unitSuffix)
        spinboxR.setValue(value)

    def convertValue(self, value, fromUnits, toUnits):
        """
        Converts the specified value from units fromUnits to toUnits.
        Based on QtGui.QPageLayout::qt_convertPoint() implementation.
        :param value:
        :param fromUnits:
        :param toUnits:
        :return:
        """
        # If converting to points then convert and round to 0 decimal places
        if toUnits == QtGui.QPageLayout.Point:
            multiplier = self.pointMultiplier(fromUnits)
            return round(value * multiplier)

        # If converting to other units, need to convert to unrounded points first
        if fromUnits != QtGui.QPageLayout.Point:
            value *= self.pointMultiplier(fromUnits)

        # Then convert from points to required units rounded to 2 decimal places
        multiplier = self.pointMultiplier(toUnits)
        return round(value * 100 / multiplier) / 100.0

    @staticmethod
    def pointMultiplier(units):
        """
        Returns multiplier for converting the specified units to points.
        :type units: QtGui.QPageLayout.Unit
        :rtype: float
        """
        if units == QtGui.QPageLayout.Millimeter:
            return 2.83464566929
        elif units == QtGui.QPageLayout.Point:
            return 1.0
        elif units == QtGui.QPageLayout.Inch:
            return 72.0
        elif units == QtGui.QPageLayout.Pica:
            return 12
        elif units == QtGui.QPageLayout.Didot:
            return 1.065826771
        elif units == QtGui.QPageLayout.Cicero:
            return 12.789921252
        else:
            return 1.0

    def printer(self):
        """
        Returns the printer associated with this PageSetupDialog.
        :rtype: QtPrintSupport.QPrinter
        """
        return self.printer

    def reloadPrinterLayout(self):
        """
        Updates the UI to reflect the printer layout.
        """
        pageLayout = self.printer.pageLayout()
        pageMargins = pageLayout.margins(pageLayout.units())
        pageMarginsMin = pageLayout.minimumMargins()
        pageMarginsMax = pageLayout.maximumMargins()
        pageUnits = pageLayout.units()
        unitSuffix = ('mm', 'pt', 'in', 'P̸', 'DD', 'CC')[pageUnits]
        comboboxUnits = self.widget('units_combobox')
        comboboxUnits.setCurrentIndex(comboboxUnits.findData(pageUnits))
        comboboxSize = self.widget('page_size_combobox')
        comboboxSize.setCurrentIndex(int(self.printer.pageSize()))
        # CUSTOM WIDTH AND HEIGHT
        spinboxW = self.widget('page_custom_width_spinbox')
        spinboxW.setRange(0, 9999)
        spinboxW.setEnabled(self.printer.pageSize() == QtGui.QPageSize.Custom)
        spinboxH = self.widget('page_custom_height_spinbox')
        spinboxH.setRange(0, 9999)
        spinboxH.setEnabled(self.printer.pageSize() == QtGui.QPageSize.Custom)
        # ORIENTATION
        portrait = self.widget('orientation_portrait_radio')
        portrait.setChecked(pageLayout.orientation() == QtGui.QPageLayout.Portrait)
        landscape = self.widget('orientation_landscape_radio')
        landscape.setChecked(pageLayout.orientation() == QtGui.QPageLayout.Landscape)
        # MARGINS
        spinboxT = self.widget('margin_top_spinbox')
        spinboxT.setRange(pageMarginsMin.top(), pageMarginsMax.top())
        spinboxT.setSuffix(unitSuffix)
        spinboxT.setValue(pageMargins.top())
        spinboxB = self.widget('margin_bottom_spinbox')
        spinboxB.setRange(pageMarginsMin.bottom(), pageMarginsMax.bottom())
        spinboxB.setSuffix(unitSuffix)
        spinboxB.setValue(pageMargins.bottom())
        spinboxL = self.widget('margin_left_spinbox')
        spinboxL.setRange(pageMarginsMin.left(), pageMarginsMax.left())
        spinboxL.setSuffix(unitSuffix)
        spinboxL.setValue(pageMargins.left())
        spinboxR = self.widget('margin_right_spinbox')
        spinboxR.setRange(pageMarginsMin.right(), pageMarginsMax.right())
        spinboxR.setSuffix(unitSuffix)
        spinboxR.setValue(pageMargins.right())
