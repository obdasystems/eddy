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


from grapholed.datatypes import Font
from grapholed.items import ItemType
from grapholed.items.nodes.common.hexagon import HexagonNode
from grapholed.items.nodes.common.label import Label

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor


class DatatypeRestrictionNode(HexagonNode):
    """
    This class implements the 'Datatype Restriction' node.
    """
    itemtype = ItemType.DatatypeRestrictionNode
    name = 'datatype restriction'
    xmlname = 'datatype-restriction'

    def __init__(self, **kwargs):
        """
        Initialize the Datatype Restriction node.
        """
        super().__init__(brush=(252, 252, 252), **kwargs)
        self.label = Label('data', movable=False, editable=False, parent=self)
        self.label.updatePos()

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
        node.setLabelText(self.labelText())
        node.setLabelPos(node.mapFromScene(self.mapToScene(self.labelPos())))

        return node

    ################################################## ITEM EXPORT #####################################################

    def asGraphol(self, document):
        """
        Export the current item in Graphol format.
        :param document: the XML document where this item will be inserted.
        :rtype: QDomElement
        """
        pos1 = self.pos()
        pos2 = self.mapToScene(self.labelPos())

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
        geometry.setAttribute('x', pos1.x())
        geometry.setAttribute('y', pos1.y())

        # add the shape label
        label = document.createElement('shape:label')
        label.setAttribute('height', self.label.height())
        label.setAttribute('width', self.label.width())
        label.setAttribute('x', pos2.x())
        label.setAttribute('y', pos2.y())
        label.appendChild(document.createTextNode(self.label.text()))

        node.appendChild(url)
        node.appendChild(description)
        node.appendChild(geometry)
        node.appendChild(label)

        return node

    ################################################# LABEL SHORTCUTS ##################################################

    def labelPos(self):
        """
        Returns the current label position in item coordinates.
        :rtype: QPointF
        """
        return self.label.pos()

    def labelText(self):
        """
        Returns the label text.
        :rtype: str
        """
        return self.label.text()

    def setLabelPos(self, pos):
        """
        Set the label position.
        :param pos: the node position in item coordinates.
        """
        self.label.setPos(pos)

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
        self.label.updatePos()

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
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawPolygon(polygon)

        # Draw the text within the polygon
        painter.setFont(Font('Arial', 11, Font.Light))
        painter.drawText(polygon.boundingRect(), Qt.AlignCenter, 'data')

        return pixmap