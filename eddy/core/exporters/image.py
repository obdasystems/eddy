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


from abc import ABCMeta, abstractmethod

from PyQt5 import QtGui, QtCore

from eddy.core.datatypes.system import File
from eddy.core.exporters.common import AbstractDiagramExporter
from eddy.core.output import getLogger

LOGGER = getLogger()


class ImageDiagramExporter(AbstractDiagramExporter):
    """
    Extends AbstractDiagramExporter with facilities to export the structure of Graphol diagrams to an image file.
    """
    __metaclass__ = ABCMeta

    BmpFormat = 'BMP'
    JpegFormat = 'JPEG'
    PngFormat = 'PNG'
    PpmFormat = 'PPM'

    def __init__(self, diagram, format, session=None):
        """
        Initialize the ImageDiagramExporter.
        :type diagram: Diagram
        :type format: str
        :type session: Session
        """
        super().__init__(diagram, session)
        self._format = format

    #############################################
    #   PROPERTIES
    #################################

    @property
    def format(self):
        """
        Returns the image format for this exporter.
        :rtype: str
        """
        return self._format

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    @abstractmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        :rtype: File
        """
        pass

    def run(self, path):
        """
        Perform JPEG document generation.
        :type path: str
        """
        shape = self.diagram.visibleRect(margin=20).toAlignedRect()
        pixmap = QtGui.QPixmap(shape.width(), shape.height())
        painter = QtGui.QPainter()

        if painter.begin(pixmap):
            painter.setBackgroundMode(QtCore.Qt.OpaqueMode)
            # RENDER THE DIAGRAM IN THE PAINTER
            self.diagram.render(painter, source=QtCore.QRectF(shape))
            # COMPLETE THE EXPORT
            painter.end()
            image = pixmap.toImage()
            image.save(path, self.format)


class BmpDiagramExporter(ImageDiagramExporter):
    """
    Subclass of ImageDiagramExporter that exports a diagram to a BMP image file.
    """
    def __init__(self, diagram, session=None):
        """
        Initialize the BmpDiagramExporter.
        :type diagram: Diagram
        :type session: Session
        """
        super().__init__(diagram, ImageDiagramExporter.BmpFormat, session)

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        :return: File
        """
        return File.Bmp


class JpegDiagramExporter(ImageDiagramExporter):
    """
    Subclass of ImageDiagramExporter that exports a diagram to a JPEG image file.
    """
    def __init__(self, diagram, session=None):
        """
        Initialize the JpegDiagramExporter.
        :type diagram: Diagram
        :type session: Session
        """
        super().__init__(diagram, ImageDiagramExporter.JpegFormat, session)

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


class PngDiagramExporter(ImageDiagramExporter):
    """
    Subclass of ImageDiagramExporter that exports a diagram to a PNG image file.
    """
    def __init__(self, diagram, session=None):
        """
        Initialize the PngDiagramExporter.
        :type diagram: Diagram
        :type session: Session
        """
        super().__init__(diagram, ImageDiagramExporter.PngFormat, session)

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        :return: File
        """
        return File.Png
