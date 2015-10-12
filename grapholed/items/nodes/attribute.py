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
from grapholed.items.nodes.common.base import Node
from grapholed.items.nodes.common.label import Label

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QPainterPath


class AttributeNode(Node):
    """
    This class implements the 'Attribute' node.
    """
    itemtype = ItemType.AttributeNode
    minHeight = 20
    minWidth = 20
    name = 'attribute'
    shapePen = QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine)
    xmlname = 'attribute'

    def __init__(self, width=minWidth, height=minHeight, **kwargs):
        """
        Initialize the Attribute node.
        :param width: the shape width (unused in current implementation).
        :param height: the shape height (unused in current implementation).
        """
        super().__init__(**kwargs)
        self.rect = self.createRect(self.minWidth, self.minHeight)
        self.label = Label(self.name, centered=False, parent=self)
        self.label.updatePos()

    ################################################ ITEM INTERFACE ####################################################

    def contextMenu(self):
        """
        Returns the basic nodes context menu.
        :rtype: QMenu
        """
        menu = super().contextMenu()

        collection = self.label.contextMenuAdd()
        if collection:
            menu.addSeparator()
            for action in collection:
                menu.addAction(action)

        return menu

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

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.rect.height()

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.rect.width()

    ############################################### AUXILIARY METHODS ##################################################

    @staticmethod
    def createRect(shape_w, shape_h):
        """
        Returns the initialized rect according to the given width/height.
        :param shape_w: the shape width.
        :param shape_h: the shape height.
        :rtype: QRectF
        """
        return QRectF(-shape_w / 2, -shape_h / 2, shape_w, shape_h)

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

    #################################################### GEOMETRY ######################################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QRectF
        """
        return self.rect

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addEllipse(self.rect)
        return path

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addEllipse(self.rect)
        return path

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
        self.label.setText(text)

    def updateLabelPos(self):
        """
        Update the label position.
        """
        self.label.updatePos()

    ################################################## ITEM DRAWING ####################################################

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        :param painter: the active painter.
        :param option: the style option for this item.
        :param widget: the widget that is being painted on.
        """
        shapeBrush = self.shapeBrushSelected if self.isSelected() else self.shapeBrush

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(shapeBrush)
        painter.setPen(self.shapePen)
        painter.drawEllipse(self.rect)

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        shape_w = 18
        shape_h = 18

        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)

        # Draw the text above the shape
        painter.setFont(Font('Arial', 9, Font.Light))
        painter.translate(0, 0)
        painter.drawText(QRectF(0, 0, kwargs['w'], kwargs['h'] / 2), Qt.AlignCenter, 'attribute')

        # Draw the ellipse
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.1, Qt.SolidLine))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2 + 6)
        painter.drawEllipse(cls.createRect(shape_w, shape_h))

        return pixmap