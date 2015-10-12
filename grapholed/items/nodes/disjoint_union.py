# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Grapholed: a diagramming software for the Graphol language.           #
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
##########################################################################
#                                                                        #
#  Graphol is developed by members of the DASI-lab group of the          #
#  Dipartimento di Informatica e Sistemistica "A.Ruberti" at Sapienza    #
#  University of Rome: http://www.dis.uniroma1.it/~graphol/:             #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Marco Console <console@dis.uniroma1.it>                          #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#                                                                        #
##########################################################################


from grapholed.items import ItemType
from grapholed.items.nodes.common.hexagon import HexagonNode

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor


class DisjointUnionNode(HexagonNode):
    """
    This class implements the 'Disjoint Union' node.
    """
    itemtype = ItemType.DisjointUnionNode
    name = 'disjoint union'
    xmlname = 'disjoint-union'

    def __init__(self, **kwargs):
        """
        Initialize the Disjoint Union node.
        """
        super().__init__(brush=(0, 0, 0), **kwargs)

    ################################################ ITEM INTERFACE ####################################################

    def copy(self, scene):
        """
        Create a copy of the current item .
        :param scene: a reference to the scene where this item is being copied from.
        """
        node = self.__class__(scene=scene,
                              id=self.id,
                              description=self.description,
                              url=self.url,
                              width=self.width(),
                              height=self.height())

        node.setPos(self.pos())
        return node

    ################################################## ITEM EXPORT #####################################################

    def asGraphol(self, document):
        """
        Export the current item in Graphol format.
        :param document: the XML document where this item will be inserted.
        :rtype: QDomElement
        """
        pos = self.pos()

        # create the root element for this node
        node = document.createElement('node')
        node.setAttribute('id', self.id)
        node.setAttribute('type', self.xmlname)

        # add node attributes
        url = document.createElement('data:url')
        url.appendChild(document.createTextNode(self.url))
        description = document.createElement('data:description')
        description.appendChild(document.createTextNode(self.description))

        # add the shape geometry
        geometry = document.createElement('shape:geometry')
        geometry.setAttribute('height', self.height())
        geometry.setAttribute('width', self.width())
        geometry.setAttribute('x', pos.x())
        geometry.setAttribute('y', pos.y())

        node.appendChild(url)
        node.appendChild(description)
        node.appendChild(geometry)

        return node

    ################################################# LABEL SHORTCUTS ##################################################

    def labelPos(self):
        """
        Returns the current label position in item coordinates.
        :rtype: QPointF
        """
        pass

    def labelText(self):
        """
        Returns the label text.
        :rtype: str
        """
        pass

    def setLabelPos(self, pos):
        """
        Set the label position.
        :param pos: the node position in item coordinates.
        """
        pass

    def setLabelText(self, text):
        """
        Set the label text.
        :param text: the text value to set.
        """
        pass

    def updateLabelPos(self):
        """
        Update the label position.
        """
        pass

    ################################################### ITEM DRAWING ###################################################

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        shape_w = 48
        shape_h = 30
        oblique = 6

        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Initialize the shape
        polygon = cls.createPolygon(shape_w, shape_h, oblique)

        # Draw the polygon
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine))
        painter.setBrush(QColor(0, 0, 0))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawPolygon(polygon)

        return pixmap