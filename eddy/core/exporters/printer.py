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


from PyQt5 import QtGui
from PyQt5 import QtPrintSupport

from eddy.core.exporters.common import AbstractDiagramExporter
from eddy.core.items.common import AbstractItem


class PrinterDiagramExporter(AbstractDiagramExporter):
    """
    Extends AbstractDiagramExporter with facilities to print the structure of Graphol diagrams.
    """
    def __init__(self, diagram, session=None):
        """
        Initialize the Printer Exporter.
        :type session: Session
        """
        super().__init__(diagram, session)

        self.success = False

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        In this particular case we don't have any type, so we return None.
        :return: File
        """
        return None

    def run(self, *args, **kwargs):
        """
        Print the diagram.
        """
        shape = self.diagram.visibleRect(margin=220)
        if shape:
            printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
            printer.setOutputFormat(QtPrintSupport.QPrinter.NativeFormat)
            dialog = QtPrintSupport.QPrintDialog(printer)
            if dialog.exec_() == QtPrintSupport.QPrintDialog.Accepted:
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
                    # COMPLETE THE PRINT
                    painter.end()

                    self.success = True