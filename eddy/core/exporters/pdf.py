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
from PyQt5 import QtPrintSupport

from eddy.core.datatypes.system import File
from eddy.core.exporters.common import AbstractDiagramExporter
from eddy.core.items.common import AbstractItem
from eddy.core.output import getLogger
from eddy.ui.DiagramsSelectionDialog import DiagramsSelectionDialog
from eddy.core.datatypes.owl import OWLStandardIRIPrefixPairsDict
from eddy.core.datatypes.qt import Font


LOGGER = getLogger()


class PdfDiagramExporter(AbstractDiagramExporter):
    """
    Extends AbstractDiagramExporter with facilities to export the structure of Graphol diagrams in PDF format.
    """
    def __init__(self, diagram, session=None):
        """
        Initialize the Pdf Exporter.
        :type session: Session
        """
        super().__init__(diagram, session)

        self.project = diagram.project

    def append_row_and_column_to_table(self,iri,prefix,brush):

        item_iri = QtWidgets.QTableWidgetItem()
        item_iri.setText(iri)

        if brush is not None:
            item_iri.setBackground(brush)

        item_prefix = QtWidgets.QTableWidgetItem()
        item_prefix.setText(prefix)

        if brush is not None:
            item_prefix.setBackground(brush)

        self.table.setItem(self.table.rowCount() - 1, 0, item_iri)
        self.table.setItem(self.table.rowCount() - 1, 1, item_prefix)

        self.table.setRowCount(self.table.rowCount() + 1)


    def FillTableWithIRIPrefixNodesDictionaryKeysAndValues(self):

        #if (iri_to_update is None) and (nodes_to_update is None):
        #print('>>>  FillTableWithIRIPrefixNodesDictionaryKeysAndValues')
        # first delete all entries from the dictionary id present
        # add standard IRIs
        # add key value pairs from dict


        """
        for r in range (0,self.table.rowCount()+1):
            iri_item_to_el = self.table.item(r,0)
            del iri_item_to_el
            prefix_item_to_del = self.table.item(r,1)
            del prefix_item_to_del
            cw=self.table.cellWidget(r,2)
            if cw is not None:
                disconnect(cw.toggled, self.set_project_IRI)
                self.table.removeCellWidget(r,2)
                cw.destroy()
        """

        self.table.clear()
        self.table.setRowCount(1)
        self.table.setColumnCount(3)

        header_iri = QtWidgets.QTableWidgetItem()
        header_iri.setText('IRI')
        header_iri.setFont(Font('Roboto', 15, bold=True))
        header_iri.setTextAlignment(QtCore.Qt.AlignCenter)
        #header_iri.setBackground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        #header_iri.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_iri.setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_iri.setForeground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        header_iri.setFlags(QtCore.Qt.NoItemFlags)

        header_prefix = QtWidgets.QTableWidgetItem()
        header_prefix.setText('PREFIX')
        header_prefix.setFont(Font('Roboto', 15, bold=True))
        header_prefix.setTextAlignment(QtCore.Qt.AlignCenter)
        #header_prefix.setBackground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        #header_prefix.setForeground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_prefix.setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_prefix.setForeground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        header_prefix.setFlags(QtCore.Qt.NoItemFlags)


        self.table.setItem(self.table.rowCount() - 1, 0, header_iri)
        self.table.setItem(self.table.rowCount() - 1, 1, header_prefix)

        self.table.setRowCount(self.table.rowCount() + 1)

        for iri in self.project.IRI_prefixes_nodes_dict.keys():
            if iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():
                standard_prefixes = self.project.IRI_prefixes_nodes_dict[iri][0]
                standard_prefix = standard_prefixes[0]
                self.append_row_and_column_to_table(iri, standard_prefix, None)
                                                    #QtGui.QBrush(QtGui.QColor(50, 50, 205, 50)))


        for iri in sorted(self.project.IRI_prefixes_nodes_dict.keys()):

            if iri in OWLStandardIRIPrefixPairsDict.std_IRI_prefix_dict.keys():
                continue

            prefixes = self.project.IRI_prefixes_nodes_dict[iri][0]

            if len(prefixes) > 0:
                for p in prefixes:
                    if iri == self.project.iri:
                        self.append_row_and_column_to_table(iri, p, None)
                    else:
                        self.append_row_and_column_to_table(iri, p, None)
            else:
                if 'display_in_widget' in self.project.IRI_prefixes_nodes_dict[iri][2]:
                    if iri == self.project.iri:
                        self.append_row_and_column_to_table(iri, '', None)
                    else:
                        self.append_row_and_column_to_table(iri, '', None)


        self.append_row_and_column_to_table('', '', None)

        self.table.setRowCount(self.table.rowCount() - 1)



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
        #diagrams = self.diagram.project.diagrams()
        diagrams_selection_dialog = DiagramsSelectionDialog(self.diagram.project, self.session)
        diagrams_selection_dialog.exec_()
        selected_diagrams = diagrams_selection_dialog.diagrams_selected

        selected_diagrams_sorted = diagrams_selection_dialog.sort(selected_diagrams)

        printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
        printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        #printer.setPaperSize(QtPrintSupport.QPrinter.Custom)
        printer.setPrinterName(self.diagram.project.name)

        #max_height = 0.0
        #max_width = 0.0

        size_of_pages = []

        for c, diag in enumerate(selected_diagrams_sorted):

            shape = diag.visibleRect(margin=200)

            #print(diag.name,'-',shape.height(), '-', shape.width())

            page_size = []

            page_size.append(shape.width())
            page_size.append(shape.height())

            size_of_pages.append(page_size)

            #max_height = max(max_height,shape.height())
            #max_width = max(max_width, shape.width())

        #print('max-',max_height, '-', max_width)

        painter = QtGui.QPainter()

        for c, diag in enumerate(selected_diagrams_sorted):

            LOGGER.info('Exporting diagram %s to %s', diag.name, path)

            shape = diag.visibleRect(margin=200)

            width_to_set = size_of_pages[c][0]
            height_to_set = size_of_pages[c][1]

            valid = printer.setPageSize(
               QtGui.QPageSize(QtCore.QSizeF(width_to_set, height_to_set), QtGui.QPageSize.Point))

            if not valid:
                LOGGER.critical('Error in setting page size. please contact programmer')
                return

            if c != 0:
                printer.newPage()

            if painter.isActive() or painter.begin(printer):
                # TURN CACHING OFF
                for item in diag.items():
                    if item.isNode() or item.isEdge():
                        item.setCacheMode(AbstractItem.NoCache)
                # RENDER THE DIAGRAM IN THE PAINTER
                diag.render(painter, source=shape)
                # TURN CACHING ON
                for item in diag.items():
                    if item.isNode() or item.isEdge():
                        item.setCacheMode(AbstractItem.DeviceCoordinateCache)

        LOGGER.info('All diagrams exported ')

        self.table = QtWidgets.QTableWidget()

        self.FillTableWithIRIPrefixNodesDictionaryKeysAndValues()
        self.table.setFixedWidth(600)
        total_height_of_all_rows = 0
        for r in range(0, self.table.rowCount() + 1):
            total_height_of_all_rows = total_height_of_all_rows + self.table.rowHeight(r)
        self.table.setMinimumHeight(total_height_of_all_rows + 100)
        shape = self.table.visibleRegion().boundingRect()

        valid = printer.setPageSize(
            QtGui.QPageSize(QtCore.QSizeF(shape.width()+200, shape.height()+200), QtGui.QPageSize.Point))

        if not valid:
            LOGGER.critical('Error in setting page size. please contact programmer')
            return

        printer.newPage()

        if painter.isActive() or painter.begin(printer):
            self.table.render(painter, sourceRegion=QtGui.QRegion(self.table.rect()))

        if painter.isActive():
            # COMPLETE THE EXPORT
            painter.end()
        # OPEN THE DOCUMENT
        # openPath(path)