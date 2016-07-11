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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import QSizeF, Qt
from PyQt5.QtGui import QPainter, QPageSize, QStandardItemModel, QStandardItem
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QTableView

from eddy.core.datatypes.graphol import Item
from eddy.core.exporters.common import AbstractExporter
from eddy.core.items.common import AbstractItem
from eddy.core.qt import Font

from eddy.lang import gettext as _


class PdfExporter(AbstractExporter):
    """
    This class can be used to export graphol projects in PDF format.
    """
    def __init__(self, project, path=None, parent=None):
        """
        Initialize the Pdf Exporter.
        :type project: Project
        :type path: str
        :type parent: QObject
        """
        super().__init__(parent)
        self.path = path
        self.project = project
        self.printer = None
        self.painter = None
        self.metamodel = None
        self.metaview = None
        self.newPage = False
        self.arial12r = Font('Arial', 12)
        self.arial12i = Font('Arial', 12, italic=True)
        self.arial12b = Font('Arial', 12)
        self.arial12b.setBold(True)
        self.exportFuncForItem = {
            Item.AttributeNode: self.exportAttributeMetaData,
            Item.RoleNode: self.exportRoleMetaData,
        }

    #############################################
    #   ELEMENTS EXPORT
    #################################

    def exportDiagrams(self):
        """
        Export all the diagrams in the current project.
        """
        for diagram in sorted(self.project.diagrams(), key=lambda x: x.name.lower()):
            if not diagram.isEmpty():
                source = diagram.visibleRect(margin=20)
                self.printer.setPageSize(QPageSize(QSizeF(source.width(), source.height()), QPageSize.Point))
                if self.newPage:
                    self.printer.newPage()
                diagram.clearSelection()
                diagram.render(self.painter, source=source)
                self.newPage = True

    def exportMetaData(self):
        """
        Export elements metadata.
        """
        metas = sorted(self.project.metas(Item.AttributeNode, Item.RoleNode), key=lambda x: x[1].lower())

        self.metamodel = QStandardItemModel()
        self.metamodel.setHorizontalHeaderLabels([
            _('META_HEADER_PREDICATE'),
            _('META_HEADER_TYPE'),
            _('META_HEADER_FUNCTIONAL'),
            _('META_HEADER_INVERSE_FUNCTIONAL'),
            _('META_HEADER_ASYMMETRIC'),
            _('META_HEADER_IRREFLEXIVE'),
            _('META_HEADER_REFLEXIVE'),
            _('META_HEADER_SYMMETRIC'),
            _('META_HEADER_TRANSITIVE')])

        # GENERATE DATA
        for entry in metas:
            meta = self.project.meta(entry[0], entry[1])
            func = self.exportFuncForItem[meta.item]
            data = func(meta)
            self.metamodel.appendRow(data)

        self.metaview = QTableView()
        self.metaview.setStyleSheet("""
        QTableView {
        border: 0;
        }
        QHeaderView {
        background: #D3D3D3;
        }""")

        self.metaview.setModel(self.metamodel)
        self.metaview.resizeColumnsToContents()
        self.metaview.setFixedWidth(sum(self.metaview.columnWidth(i) for i in range(self.metamodel.columnCount())))
        self.metaview.setFixedHeight(sum(self.metaview.rowHeight(i) for i in \
                                         range(self.metamodel.rowCount())) + self.metaview.horizontalHeader().height())
        self.metaview.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.metaview.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.metaview.verticalHeader().setVisible(False)

        self.printer.setPageSize(QPageSize(QSizeF(self.metaview.width(), self.metaview.height()), QPageSize.Point))
        if self.newPage:
            self.printer.newPage()

        xscale = self.printer.pageRect().width() / self.metaview.width()
        yscale = self.printer.pageRect().height() / self.metaview.height()
        self.painter.scale(min(xscale, yscale), min(xscale, yscale))
        self.metaview.render(self.painter)

    def exportAttributeMetaData(self, meta):
        """
        Export the given attribute meta data in the given row.
        :type meta: AttributeMetaData
        """
        i1 = QStandardItem(meta.predicate)
        i1.setFont(self.arial12r)
        i1.setTextAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        i2 = QStandardItem(meta.item.shortname)
        i2.setFont(self.arial12r)
        i2.setTextAlignment(Qt.AlignCenter)
        i3 = QStandardItem('Yes' if meta.functional else 'No')
        i3.setFont(self.arial12i)
        i3.setTextAlignment(Qt.AlignCenter)
        i4 = QStandardItem('-')
        i4.setFont(self.arial12i)
        i4.setTextAlignment(Qt.AlignCenter)
        i5 = QStandardItem('-')
        i5.setFont(self.arial12i)
        i5.setTextAlignment(Qt.AlignCenter)
        i6 = QStandardItem('-')
        i6.setFont(self.arial12i)
        i6.setTextAlignment(Qt.AlignCenter)
        i7 = QStandardItem('-')
        i7.setFont(self.arial12i)
        i7.setTextAlignment(Qt.AlignCenter)
        i8 = QStandardItem('-')
        i8.setFont(self.arial12i)
        i8.setTextAlignment(Qt.AlignCenter)
        i9 = QStandardItem('-')
        i9.setFont(self.arial12i)
        i9.setTextAlignment(Qt.AlignCenter)
        return [i1, i2, i3, i4, i5, i6, i7, i8, i9]

    def exportRoleMetaData(self, meta):
        """
        Export the given role meta data in the given row.
        :type meta: RoleMetaData
        """
        i1 = QStandardItem(meta.predicate)
        i1.setFont(self.arial12r)
        i1.setTextAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        i2 = QStandardItem(meta.item.shortname)
        i2.setFont(self.arial12r)
        i2.setTextAlignment(Qt.AlignCenter)
        i3 = QStandardItem('Yes' if meta.functional else 'No')
        i3.setFont(self.arial12i)
        i3.setTextAlignment(Qt.AlignCenter)
        i4 = QStandardItem('Yes' if meta.inverseFunctional else 'No')
        i4.setFont(self.arial12i)
        i4.setTextAlignment(Qt.AlignCenter)
        i5 = QStandardItem('Yes' if meta.asymmetric else 'No')
        i5.setFont(self.arial12i)
        i5.setTextAlignment(Qt.AlignCenter)
        i6 = QStandardItem('Yes' if meta.irreflexive else 'No')
        i6.setFont(self.arial12i)
        i6.setTextAlignment(Qt.AlignCenter)
        i7 = QStandardItem('Yes' if meta.reflexive else 'No')
        i7.setFont(self.arial12i)
        i7.setTextAlignment(Qt.AlignCenter)
        i8 = QStandardItem('Yes' if meta.symmetric else 'No')
        i8.setFont(self.arial12i)
        i8.setTextAlignment(Qt.AlignCenter)
        i9 = QStandardItem('Yes' if meta.transitive else 'No')
        i9.setFont(self.arial12i)
        i9.setTextAlignment(Qt.AlignCenter)
        return [i1, i2, i3, i4, i5, i6, i7, i8, i9]

    #############################################
    #   AUXILIARY METHODS
    #################################

    def setCachingOff(self):
        """
        Turns caching OFF for all the items in the project.
        """
        for item in self.project.items():
            if item.isNode() or item.isEdge():
                item.setCacheMode(AbstractItem.NoCache)

    def setCachingOn(self):
        """
        Turns caching ON for all the items in the project.
        """
        for item in self.project.items():
            if item.isNode() or item.isEdge():
                item.setCacheMode(AbstractItem.DeviceCoordinateCache)

    #############################################
    #   DOCUMENT GENERATION
    #################################

    def run(self):
        """
        Perform document generation.
        """
        self.printer = QPrinter(QPrinter.HighResolution)
        self.printer.setOutputFormat(QPrinter.PdfFormat)
        self.printer.setOutputFileName(self.path)
        self.painter = QPainter()
        self.painter.begin(self.printer)
        self.setCachingOff()
        self.exportDiagrams()
        self.exportMetaData()
        self.setCachingOn()
        self.painter.end()