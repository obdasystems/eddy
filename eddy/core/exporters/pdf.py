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
from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.graphol import Special

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

    def append_row_and_column_to_table_2(self,list_inp,entity=None):

        item_predicate_name = QtWidgets.QTableWidgetItem()
        item_predicate_name.setText(list_inp[0])
        self.table_2.setItem(self.table_2.rowCount() - 1, 0, item_predicate_name)

        if list_inp[1] is False:
            item_predicate_attribute_A = QtWidgets.QTableWidgetItem()
            self.table_2.setItem(self.table_2.rowCount() - 1, 1, item_predicate_attribute_A)
        else:
            checkbox_A = QtWidgets.QCheckBox()
            checkbox_A.setEnabled(True)
            checkbox_A.setChecked(True)
            self.table_2.setCellWidget(self.table_2.rowCount() - 1, 1, checkbox_A)

        if list_inp[2] is False:
            item_predicate_attribute_B = QtWidgets.QTableWidgetItem()
            self.table_2.setItem(self.table_2.rowCount() - 1, 2, item_predicate_attribute_B)
        else:
            checkbox_B = QtWidgets.QCheckBox()
            checkbox_B.setEnabled(True)
            checkbox_B.setChecked(True)
            self.table_2.setCellWidget(self.table_2.rowCount() - 1, 2, checkbox_B)

        if list_inp[3] is False:
            item_predicate_attribute_C = QtWidgets.QTableWidgetItem()
            self.table_2.setItem(self.table_2.rowCount() - 1, 3, item_predicate_attribute_C)
        else:
            checkbox_C = QtWidgets.QCheckBox()
            checkbox_C.setEnabled(True)
            checkbox_C.setChecked(True)
            #hl = QtWidgets.QHBoxLayout()
            #hl.addSpacing(6)
            #hl.addWidget(checkbox_C)
            #hl.addSpacing(6)
            #checkbox_C.setLayout(hl)
            self.table_2.setCellWidget(self.table_2.rowCount() - 1, 3, checkbox_C)

        if list_inp[4] is False:
            item_predicate_attribute_D = QtWidgets.QTableWidgetItem()
            self.table_2.setItem(self.table_2.rowCount() - 1, 4, item_predicate_attribute_D)
        else:
            checkbox_D = QtWidgets.QCheckBox()
            checkbox_D.setEnabled(True)
            checkbox_D.setChecked(True)
            self.table_2.setCellWidget(self.table_2.rowCount() - 1, 4, checkbox_D)

        if list_inp[5] is False:
            item_predicate_attribute_E = QtWidgets.QTableWidgetItem()
            self.table_2.setItem(self.table_2.rowCount() - 1, 5, item_predicate_attribute_E)
        else:
            checkbox_E = QtWidgets.QCheckBox()
            checkbox_E.setEnabled(True)
            checkbox_E.setChecked(True)
            self.table_2.setCellWidget(self.table_2.rowCount() - 1, 5, checkbox_E)

        if list_inp[6] is False:
            item_predicate_attribute_F = QtWidgets.QTableWidgetItem()
            self.table_2.setItem(self.table_2.rowCount() - 1, 6, item_predicate_attribute_F)
        else:
            checkbox_F = QtWidgets.QCheckBox()
            checkbox_F.setEnabled(True)
            checkbox_F.setChecked(True)
            self.table_2.setCellWidget(self.table_2.rowCount() - 1, 6, checkbox_F)

        if list_inp[7] is False:
            item_predicate_attribute_G = QtWidgets.QTableWidgetItem()
            self.table_2.setItem(self.table_2.rowCount() - 1, 7, item_predicate_attribute_G)
        else:
            checkbox_G = QtWidgets.QCheckBox()
            checkbox_G.setEnabled(True)
            checkbox_G.setChecked(True)
            self.table_2.setCellWidget(self.table_2.rowCount() - 1, 7, checkbox_G)

        self.table_2.setRowCount(self.table_2.rowCount() + 1)

    def append_row_and_column_to_table(self,iri,prefix,brush,bold=None):

        item_iri = QtWidgets.QTableWidgetItem()
        item_iri.setText(iri)

        if brush is not None:
            item_iri.setBackground(brush)

        item_prefix = QtWidgets.QTableWidgetItem()
        item_prefix.setText(prefix)

        if bold:
            font_iri = QtGui.QFont(item_iri.text())
            font_iri.setBold(True)
            item_iri.setFont(font_iri)

            font_prefix = QtGui.QFont(item_prefix.text())
            font_prefix.setBold(True)
            item_prefix.setFont(font_prefix)

        if brush is not None:
            item_prefix.setBackground(brush)

        self.table.setItem(self.table.rowCount() - 1, 0, item_iri)
        self.table.setItem(self.table.rowCount() - 1, 1, item_prefix)

        self.table.setRowCount(self.table.rowCount() + 1)

    def FillTableWithMetaDataInfoForRolesAndAttributes(self):

        self.table_2.setRowCount(1)
        self.table_2.setColumnCount(8)

        header_entity = QtWidgets.QTableWidgetItem()
        header_entity.setText('ENTITY')
        header_entity.setFont(Font('Roboto', 15, bold=True))
        header_entity.setTextAlignment(QtCore.Qt.AlignCenter)
        header_entity.setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_entity.setForeground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        header_entity.setFlags(QtCore.Qt.NoItemFlags)

        header_functional = QtWidgets.QTableWidgetItem()
        header_functional.setText('FUNCTIONAL')
        header_functional.setFont(Font('Roboto', 15, bold=True))
        header_functional.setTextAlignment(QtCore.Qt.AlignCenter)
        header_functional.setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_functional.setForeground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        header_functional.setFlags(QtCore.Qt.NoItemFlags)

        header_inversefunctional = QtWidgets.QTableWidgetItem()
        header_inversefunctional.setText('INVERSE\nFUNCTIONAL')
        header_inversefunctional.setFont(Font('Roboto', 15, bold=True))
        header_inversefunctional.setTextAlignment(QtCore.Qt.AlignCenter)
        header_inversefunctional.setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_inversefunctional.setForeground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        header_inversefunctional.setFlags(QtCore.Qt.NoItemFlags)

        header_transitive = QtWidgets.QTableWidgetItem()
        header_transitive.setText('TRANSITIVE')
        header_transitive.setFont(Font('Roboto', 15, bold=True))
        header_transitive.setTextAlignment(QtCore.Qt.AlignCenter)
        header_transitive.setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_transitive.setForeground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        header_transitive.setFlags(QtCore.Qt.NoItemFlags)

        header_reflexive = QtWidgets.QTableWidgetItem()
        header_reflexive.setText('REFLEXIVE')
        header_reflexive.setFont(Font('Roboto', 15, bold=True))
        header_reflexive.setTextAlignment(QtCore.Qt.AlignCenter)
        header_reflexive.setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_reflexive.setForeground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        header_reflexive.setFlags(QtCore.Qt.NoItemFlags)
        
        header_irreflexive = QtWidgets.QTableWidgetItem()
        header_irreflexive.setText('IRREFLEXIVE')
        header_irreflexive.setFont(Font('Roboto', 15, bold=True))
        header_irreflexive.setTextAlignment(QtCore.Qt.AlignCenter)
        header_irreflexive.setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_irreflexive.setForeground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        header_irreflexive.setFlags(QtCore.Qt.NoItemFlags)
        
        header_symmetric = QtWidgets.QTableWidgetItem()
        header_symmetric.setText('SYMMETRIC')
        header_symmetric.setFont(Font('Roboto', 15, bold=True))
        header_symmetric.setTextAlignment(QtCore.Qt.AlignCenter)
        header_symmetric.setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_symmetric.setForeground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        header_symmetric.setFlags(QtCore.Qt.NoItemFlags)

        header_asymmetric = QtWidgets.QTableWidgetItem()
        header_asymmetric.setText('ASYMMETRIC')
        header_asymmetric.setFont(Font('Roboto', 15, bold=True))
        header_asymmetric.setTextAlignment(QtCore.Qt.AlignCenter)
        header_asymmetric.setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_asymmetric.setForeground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        header_asymmetric.setFlags(QtCore.Qt.NoItemFlags)

        self.table_2.setItem(self.table_2.rowCount() - 1, 0, header_entity)
        self.table_2.setItem(self.table_2.rowCount() - 1, 1, header_functional)
        self.table_2.setItem(self.table_2.rowCount() - 1, 2, header_inversefunctional)
        self.table_2.setItem(self.table_2.rowCount() - 1, 3, header_reflexive)
        self.table_2.setItem(self.table_2.rowCount() - 1, 4, header_irreflexive)
        self.table_2.setItem(self.table_2.rowCount() - 1, 5, header_symmetric)
        self.table_2.setItem(self.table_2.rowCount() - 1, 6, header_asymmetric)
        self.table_2.setItem(self.table_2.rowCount() - 1, 7, header_transitive)

        self.table_2.setRowCount(self.table_2.rowCount() + 1)

        wanted_attributes = ['functional','inverseFunctional','reflexive','irreflexive','symmetric','asymmetric','transitive']



        attribute_predicates_filtered = set()
        for attribute_predicate in self.project.predicates(item=Item.AttributeNode):
            if (attribute_predicate.text() in Special.return_group(Special.AllTopEntities)) or (attribute_predicate.text() in Special.return_group(Special.AllBottomEntities)):
                continue
            else:
                attribute_predicates_filtered.add(attribute_predicate.text())

        for attribute_predicate_txt in attribute_predicates_filtered:
            meta_data = self.project.meta(Item.AttributeNode, attribute_predicate_txt)

            print('meta_data',meta_data)

            attributes = []

            if len(meta_data) > 0:
                for k in wanted_attributes:
                    if k in meta_data:
                        value = meta_data[k]
                    else:
                        value = False
                    attributes.append(value)
            else:
                attributes.append(False)
                attributes.append(False)
                attributes.append(False)
                attributes.append(False)
                attributes.append(False)
                attributes.append(False)
                attributes.append(False)

            print(attribute_predicate_txt, '-', attributes)

            attribute_predicate_plus_attributes = []

            attribute_predicate_plus_attributes.append(attribute_predicate_txt)
            attribute_predicate_plus_attributes.extend(attributes)

            self.append_row_and_column_to_table_2(attribute_predicate_plus_attributes,entity='attribute')
        
        
        role_predicates_filtered = set()
        for role_predicate in self.project.predicates(item=Item.RoleNode):
            if (role_predicate.text() in Special.return_group(Special.AllTopEntities)) or (role_predicate.text() in Special.return_group(Special.AllBottomEntities)):
                continue
            else:
                role_predicates_filtered.add(role_predicate.text())

        for role_predicate_txt in role_predicates_filtered:
            meta_data = self.project.meta(Item.RoleNode, role_predicate_txt)

            attributes = []

            if len(meta_data) >0:
                for k in wanted_attributes:
                    value = meta_data[k]
                    attributes.append(value)
            else:
                attributes.append(False)
                attributes.append(False)
                attributes.append(False)
                attributes.append(False)
                attributes.append(False)
                attributes.append(False)
                attributes.append(False)

            print(role_predicate_txt,'-',attributes)

            role_predicate_plus_attributes = []

            role_predicate_plus_attributes.append(role_predicate_txt)
            role_predicate_plus_attributes.extend(attributes)

            self.append_row_and_column_to_table_2(role_predicate_plus_attributes)

        self.table_2.setRowCount(self.table_2.rowCount() - 1)

    def FillTableWithIRIPrefixNodesDictionaryKeysAndValues(self):

        self.table.setRowCount(1)
        self.table.setColumnCount(2)

        header_iri = QtWidgets.QTableWidgetItem()
        header_iri.setText('IRI')
        header_iri.setFont(Font('Roboto', 15, bold=True))
        header_iri.setTextAlignment(QtCore.Qt.AlignCenter)
        header_iri.setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 255, 255)))
        header_iri.setForeground(QtGui.QBrush(QtGui.QColor(90, 80, 80, 200)))
        header_iri.setFlags(QtCore.Qt.NoItemFlags)

        header_prefix = QtWidgets.QTableWidgetItem()
        header_prefix.setText('PREFIX')
        header_prefix.setFont(Font('Roboto', 15, bold=True))
        header_prefix.setTextAlignment(QtCore.Qt.AlignCenter)
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
                        self.append_row_and_column_to_table(iri, p, None, bold=True)
                    else:
                        self.append_row_and_column_to_table(iri, p, None)
            else:
                if 'display_in_widget' in self.project.IRI_prefixes_nodes_dict[iri][2]:
                    if iri == self.project.iri:
                        self.append_row_and_column_to_table(iri, '', None, bold=True)
                    else:
                        self.append_row_and_column_to_table(iri, '', None)

        #self.append_row_and_column_to_table('', '', None)

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

        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.FillTableWithIRIPrefixNodesDictionaryKeysAndValues()

        max_size = 0
        max_A = 0
        max_B = 0

        #set font size for all cells
        for r in range(0, self.table.rowCount()):
            for c in range(0,2):
                cell_item = self.table.item(r,c)

                font = cell_item.font()

                if c == 0:
                    max_A = max(max_A,len(cell_item.text()))
                if c == 1:
                    max_B = max(max_B,len(cell_item.text()))

                #cell_item.setFont(font)

                max_size = max(max_size,font.pointSize())

        for r in range(0, self.table.rowCount()+1):
            self.table.setRowHeight(r,max_size+10)

        self.table.setColumnWidth(0, max_A*10)
        self.table.setColumnWidth(1, max_B*30)

        self.table.setFixedWidth(self.table.columnWidth(0) + self.table.columnWidth(1))

        #does not work; self.table.horizontalScrollBar().isVisible() method always returns false
        #while(self.table.horizontalScrollBar().isVisible()):
            #make all cells visible
            #self.table.setFixedWidth(self.table.width()+1)

       #set the table width and height
        total_height_of_all_rows = 0
        for r in range(0, self.table.rowCount()):
            total_height_of_all_rows = total_height_of_all_rows + self.table.rowHeight(r)
        self.table.setFixedHeight(total_height_of_all_rows+5)

        shape = self.table.rect()
        #shape_2 = self.table.visibleRegion().boundingRect()

        width_to_set = (shape.width()+220)/15
        height_to_set = (shape.height()+220)/15

        valid = printer.setPageSize(
            QtGui.QPageSize(QtCore.QSizeF(width_to_set, height_to_set), QtGui.QPageSize.Point))

        if not valid:
            LOGGER.critical('Error in setting page size. please contact programmer')
            return

        printer.newPage()

        if painter.isActive() or painter.begin(printer):
            self.table.render(painter, sourceRegion=QtGui.QRegion(shape))

        LOGGER.info('IRI-Prefix table exported')

        ##############################################################
        #table for meta data of roles and attributes

        self.table_2 = QtWidgets.QTableWidget()

        self.table_2.horizontalHeader().setVisible(False)
        self.table_2.verticalHeader().setVisible(False)
        self.table_2.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.table_2.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.FillTableWithMetaDataInfoForRolesAndAttributes()

        for r in range(0, self.table_2.rowCount() + 1):
            self.table_2.setRowHeight(r, 20)

        self.table_2.setRowHeight(0, 40)

        total_height_of_all_rows = 0
        for r in range(0, self.table_2.rowCount()):
            total_height_of_all_rows = total_height_of_all_rows + self.table_2.rowHeight(r)
        self.table_2.setFixedHeight(total_height_of_all_rows + 3)

        max_size = 0

        #set font size for all cells
        for r in range(0, self.table.rowCount()):
            cell_item = self.table.item(r,0)
            font = cell_item.font()
            max_size = max(max_size,font.pointSize(),len(cell_item.text()))

        self.table_2.setColumnWidth(0, max_size*10)
        self.table_2.setColumnWidth(1, 120)
        self.table_2.setColumnWidth(2, 120)
        self.table_2.setColumnWidth(3, 120)
        self.table_2.setColumnWidth(4, 120)
        self.table_2.setColumnWidth(5, 120)
        self.table_2.setColumnWidth(6, 120)
        self.table_2.setColumnWidth(7, 120)

        self.table_2.setFixedWidth(self.table_2.columnWidth(0) + self.table_2.columnWidth(1) + \
                                 self.table_2.columnWidth(2) + self.table_2.columnWidth(3) + \
                                 self.table_2.columnWidth(4) + self.table_2.columnWidth(5) + \
                                 self.table_2.columnWidth(6) + self.table_2.columnWidth(7))

        shape_2 = self.table_2.rect()
        # shape_2 = self.table.visibleRegion().boundingRect()

        print(shape_2.height())
        print(shape_2.width())
        print(self.table_2.rowCount())
        print(self.table_2.columnCount())

        width_to_set = (shape_2.width() + 220) / 15
        height_to_set = (shape_2.height() + 220) / 15

        valid = printer.setPageSize(
            QtGui.QPageSize(QtCore.QSizeF(width_to_set, height_to_set), QtGui.QPageSize.Point))

        if not valid:
            LOGGER.critical('Error in setting page size. please contact programmer')
            return

        printer.newPage()

        if painter.isActive() or painter.begin(printer):
            self.table_2.render(painter, sourceRegion=QtGui.QRegion(shape_2))

        LOGGER.info('Meta-Data table for attributes and roles exported')


        if painter.isActive():
            # COMPLETE THE EXPORT
            painter.end()
        # OPEN THE DOCUMENT
        # openPath(path)