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
from PyQt5 import QtPrintSupport

from eddy.core.datatypes.system import File
from eddy.core.exporters.common import AbstractDiagramExporter
from eddy.core.items.common import AbstractItem
from eddy.core.output import getLogger
from eddy.ui.DiagramsSelectionDialog import DiagramsSelectionDialog

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

        if painter.isActive():
            # COMPLETE THE EXPORT
            painter.end()
        # OPEN THE DOCUMENT
        # openPath(path)