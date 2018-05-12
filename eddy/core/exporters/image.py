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


from PyQt5 import QtGui, QtCore, QtWidgets

from eddy.core.datatypes.system import File
from eddy.core.exporters.common import AbstractDiagramExporter
from eddy.core.output import getLogger

LOGGER = getLogger()


class ImageExporter(AbstractDiagramExporter):
    """
    Extends AbstractDiagramExporter with facilities to export the structure of Graphol diagrams in JPEG format.
    """
    def __init__(self, diagram, session=None):
        """
        Initialize the JPEG Exporter.
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
        :return: File
        """
        return File.Jpeg

    def run(self, path):
        """
        Perform JPEG document generation.
        :type path: str
        """

        shape = self.diagram.visibleRect(margin=220)

        empty_image = QtGui.QImage(int(shape.width()), int(shape.height()),QtGui.QImage.Format_RGB32)
        empty_image.invertPixels()

        pixmap = QtGui.QPixmap(empty_image)

        painter = QtGui.QPainter()

        started = painter.begin(pixmap)

        if started:
            self.diagram.render(painter,source=shape)

            image = pixmap.toImage()

            #pixmap.save(path)
            image.save(path)

            painter.end()

            self.success = True
