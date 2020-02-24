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

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtPrintSupport

from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.graphol import Special
from eddy.core.datatypes.qt import Font
from eddy.core.datatypes.system import File
from eddy.core.exporters.common import AbstractDiagramExporter
from eddy.core.exporters.common import AbstractProjectExporter
from eddy.core.functions.misc import natsorted
from eddy.core.functions.path import openPath
from eddy.core.items.common import AbstractItem
from eddy.core.output import getLogger
from eddy.core.project import K_ASYMMETRIC, K_SYMMETRIC
from eddy.core.project import K_FUNCTIONAL, K_INVERSE_FUNCTIONAL
from eddy.core.project import K_REFLEXIVE, K_IRREFLEXIVE
from eddy.core.project import K_TRANSITIVE
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
            dialog = QtPrintSupport.QPageSetupDialog(printer, self.session)
            if not dialog.exec_():
                return
        else:
            printer.setPageSize(self.pageSize)

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
                    # RENDER DIAGRAM NAME
                    title = QtGui.QTextDocument()
                    title.setDefaultFont(Font(pixelSize=140))
                    title.setHtml('{0}<hr width=100%/>'.format(diagram.name))
                    title.setTextWidth(printer.pageRect().width())
                    title.drawContents(painter)
                    # RENDER THE DIAGRAM IN THE PAINTER
                    diagram.render(painter, source=shape)
                    # TURN CACHING ON
                    for item in diagram.items():
                        if item.isNode() or item.isEdge():
                            item.setCacheMode(AbstractItem.DeviceCoordinateCache)

        ##############################################################
        # IRI TABLE
        ##############################################################

        # RESET PAGE SIZE AND ORIENTATION FOR PREDICATE TABLES
        printer.setPageSize(QtPrintSupport.QPrinter.A4)
        printer.setOrientation(QtPrintSupport.QPrinter.Landscape)
        printer.setPageMargins(12.5, 12.5, 12.5, 12.5, QtPrintSupport.QPrinter.Millimeter)

        prefixRows = []
        for iri in sorted(self.project.IRI_prefixes_nodes_dict.keys()):
            for prefix in self.project.IRI_prefixes_nodes_dict[iri][0]:
                prefixRows.append(dedent('''
                    <tr>
                        <td width=25%>{0}</td>
                        <td width=75%>{1}</td>
                    </tr>
                '''.format(prefix, iri)))
        sections = [prefixRows[i:i+self.rowsPerPage] for i in range(0, len(prefixRows), self.rowsPerPage)]

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
            for predicate in self.project.predicates(item=item):
                if not predicate.text() in Special.return_group(Special.AllTopEntities) \
                        or predicate.text() in Special.return_group(Special.AllBottomEntities):
                    predicates.add(predicate.text().replace('\n', ''))

        for predicate in sorted(predicates):
            meta = self.project.meta(Item.RoleNode, predicate) or \
                   self.project.meta(Item.AttributeNode, predicate) or \
                   {}
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
            '''.format(predicate, *map(lambda x: u'\u2713' if x else '', attributes)))
        sections = [predicateRows[i:i+self.rowsPerPage] for i in range(0, len(predicateRows), self.rowsPerPage)]

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
