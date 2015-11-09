# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  GrapholEd: an editor for the Graphol ontology language.               #
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


from grapholed.datatypes import Font, ItemType, XsdDatatype
from grapholed.exceptions import ParseError
from grapholed.items.nodes.common.base import Node
from grapholed.items.nodes.common.label import Label

from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QPainterPath


class ValueDomainNode(Node):
    """
    This class implements the 'Value-Domain' node.
    """
    itemtype = ItemType.ValueDomainNode
    minHeight = 40
    minWidth = 90
    name = 'value domain'
    padding = 16
    radius = 8
    xmlname = 'value-domain'

    def __init__(self, width=minWidth, height=minHeight, brush='#fcfcfc', **kwargs):
        """
        Initialize the Value-Domain node.
        :param width: the shape width (unused in current implementation).
        :param height: the shape height (unused in current implementation).
        :param brush: the brush used to paint the node.
        """
        super().__init__(**kwargs)
        self.brush = brush
        self.pen = QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine)
        self.datatype = XsdDatatype.string
        self.rect = self.createRect(self.minWidth, self.minHeight)
        self.label = Label(self.datatype.value, movable=False, editable=False, parent=self)
        self.updateRect()

    ################################################ ITEM INTERFACE ####################################################

    def contextMenu(self):
        """
        Returns the basic nodes context menu.
        :rtype: QMenu
        """
        scene = self.scene()
        menu = super().contextMenu()
        menu.insertMenu(scene.actionOpenNodeProperties, scene.menuChangeNodeBrush)
        menu.insertMenu(scene.actionOpenNodeProperties, scene.menuChangeValueDomainDatatype)

        # switch the check matching the current datatype
        for action in scene.actionsChangeValueDomainDatatype:
            action.setChecked(self.datatype == action.data())

        menu.insertSeparator(scene.actionOpenNodeProperties)
        return menu

    def copy(self, scene):
        """
        Create a copy of the current item.
        :param scene: a reference to the scene where this item is being copied from.
        """
        kwargs = {
            'brush': self.brush,
            'description': self.description,
            'height': self.height(),
            'id': self.id,
            'scene': scene,
            'url': self.url,
            'width': self.width(),
        }

        node = self.__class__(**kwargs)
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

    def updateRect(self):
        """
        Update current shape rect according to the selected datatype.
        Will also center the shape text after the width adjustment.
        """
        shape_w = max(self.label.width() + self.padding, self.minWidth)
        self.rect = self.createRect(shape_w, self.minHeight)
        self.updateLabelPos()

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

    ############################################# ITEM IMPORT / EXPORT #################################################

    @classmethod
    def fromGraphol(cls, scene, E):
        """
        Create a new item instance by parsing a Graphol document item entry.
        :param scene: the scene where the element will be inserted.
        :param E: the Graphol document element entry.
        :rtype: Node
        """
        U = E.elementsByTagName('data:url').at(0).toElement()
        D = E.elementsByTagName('data:description').at(0).toElement()
        G = E.elementsByTagName('shape:geometry').at(0).toElement()
        L = E.elementsByTagName('shape:label').at(0).toElement()

        kwargs = {
            'brush': E.attribute('color', '#fcfcfc'),
            'description': D.text(),
            'height': int(G.attribute('height')),
            'id': E.attribute('id'),
            'scene': scene,
            'url': U.text(),
            'width': int(G.attribute('width')),
        }

        node = cls(**kwargs)
        node.setPos(QPointF(int(G.attribute('x')), int(G.attribute('y'))))
        node.setLabelText(L.text())
        node.setLabelPos(node.mapFromScene(QPointF(int(L.attribute('x')), int(L.attribute('y')))))
        return node

    def toGraphol(self, document):
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
        node.setAttribute('color', self.brush.color().name())

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
        path.addRoundedRect(self.rect, self.radius, self.radius)
        return path

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRoundedRect(self.rect, self.radius, self.radius)
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
        :raise ParseError: if an invalid datatype is given.
        :param text: the text value to set.
        """
        text = text.strip()
        for datatype in XsdDatatype:
            if datatype.value == text:
                self.datatype = datatype
                self.label.setText(datatype.value)
                self.updateRect()
                self.updateEdges()
                return

        # raise an error in case the given text doesn't match any XsdDatatype value
        raise ParseError('invalid datatype supplied: {0}'.format(text))

    def updateLabelPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        self.label.updatePos(*args, **kwargs)

    ################################################## ITEM DRAWING ####################################################

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        :param painter: the active painter.
        :param option: the style option for this item.
        :param widget: the widget that is being painted on.
        """
        brush = self.selectedBrush if self.isSelected() else self.brush
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(brush)
        painter.setPen(self.pen)
        painter.drawRoundedRect(self.rect, self.radius, self.radius)

    @classmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        # Initialize the pixmap
        pixmap = QPixmap(kwargs['w'], kwargs['h'])
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)

        # Initialize the shape
        rect = cls.createRect(54, 34)

        # Draw the rectangle
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine, Qt.SquareCap, Qt.RoundJoin))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawRoundedRect(rect, 6.0, 6.0)

        # Draw the text within the rectangle
        painter.setFont(Font('Arial', 10, Font.Light))
        painter.drawText(rect, Qt.AlignCenter, 'xsd:string')

        return pixmap