# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QPainterPath, QBrush

from eddy.core.datatypes import DiagramMode, DistinctList, Item, Identity
from eddy.core.items.nodes.common.base import AbstractNode


class PropertyAssertionNode(AbstractNode):
    """
    This class implements the 'Property Assertion' node.
    """
    identities = {Identity.Link}
    item = Item.PropertyAssertionNode
    minheight = 30
    minwidth = 52
    radius = 16
    xmlname = 'property-assertion'

    def __init__(self, width=minwidth, height=minheight, brush=None, inputs=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: T <= QBrush | QColor | Color | tuple | list | bytes | unicode
        :type inputs: DistinctList
        """
        super().__init__(**kwargs)
        self.brush = QBrush(QColor(252, 252, 252))
        self.pen = QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine)
        self.inputs = inputs or DistinctList()
        self.polygon = self.createRect(self.minwidth, self.minheight)

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return Identity.Link

    @identity.setter
    def identity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def addEdge(self, edge):
        """
        Add the given edge to the current node.
        :type edge: AbstractEdge
        """
        super().addEdge(edge)
        if edge.isItem(Item.InputEdge) and edge.target is self:
            # FIXME: this cause troubles when loading a document from a graphol file since it doesn't preserve ordering
            # self.inputs.sanitize(lambda x: x in {e.id for e in self.edges if e.target is self})
            self.inputs.append(edge.id)
            edge.updateEdge()

    def copy(self, scene):
        """
        Create a copy of the current item.
        :type scene: DiagramScene
        """
        kwargs = {
            'description': self.description,
            'id': self.id,
            'height': self.height(),
            'url': self.url,
            'width': self.width(),
        }
        node = scene.itemFactory.create(item=self.item, scene=scene, **kwargs)
        node.setPos(self.pos())
        return node

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.polygon.height()

    def removeEdge(self, edge):
        """
        Remove the given edge from the current node.
        :type edge: AbstractEdge
        """
        super().removeEdge(edge)
        scene = self.scene()
        self.inputs.remove(edge.id)
        # FIXME: this cause troubles when loading a document from a graphol file since it doesn't preserve ordering
        # self.inputs.sanitize(lambda x: x in {e.id for e in self.edges if e.target is self})
        for i in self.inputs:
            try:
                edge = scene.edge(i)
                edge.updateEdge()
            except KeyError:
                pass

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.polygon.width()

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    @staticmethod
    def createRect(shape_w, shape_h):
        """
        Returns the initialized rect according to the given width/height.
        :type shape_w: int
        :type shape_h: int
        :rtype: QRectF
        """
        return QRectF(-shape_w / 2, -shape_h / 2, shape_w, shape_h)

    ####################################################################################################################
    #                                                                                                                  #
    #   IMPORT / EXPORT                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    @classmethod
    def fromGraphol(cls, scene, E):
        """
        Create a new item instance by parsing a Graphol document item entry.
        :type scene: DiagramScene
        :type E: QDomElement
        :rtype: AbstractNode
        """
        U = E.elementsByTagName('data:url').at(0).toElement()
        D = E.elementsByTagName('data:description').at(0).toElement()
        G = E.elementsByTagName('shape:geometry').at(0).toElement()
        I = E.attribute('inputs', '').strip()


        kwargs = {
            'description': D.text(),
            'height': int(G.attribute('height')),
            'id': E.attribute('id'),
            'inputs': DistinctList(I.split(',') if I else []),
            'url': U.text(),
            'width': int(G.attribute('width')),
        }

        node = scene.itemFactory.create(item=cls.item, scene=scene, **kwargs)
        node.setPos(QPointF(int(G.attribute('x')), int(G.attribute('y'))))
        return node

    def toGraphol(self, document):
        """
        Export the current item in Graphol format.
        :type document: QDomDocument
        :rtype: QDomElement
        """
        pos = self.pos()

        # create the root element for this node
        node = document.createElement('node')
        node.setAttribute('id', self.id)
        node.setAttribute('type', self.xmlname)
        node.setAttribute('inputs', ','.join(self.inputs))

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

    ####################################################################################################################
    #                                                                                                                  #
    #   IMPORT / EXPORT                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QRectF
        """
        o = self.selectionOffset
        return self.polygon.adjusted(-o, -o, o, o)

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRoundedRect(self.polygon, self.radius, self.radius)
        return path

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRoundedRect(self.polygon, self.radius, self.radius)
        return path

    ####################################################################################################################
    #                                                                                                                  #
    #   LABEL SHORTCUTS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def textPos(self):
        """
        Returns the current label position in item coordinates.
        :rtype: QPointF
        """
        pass

    def text(self):
        """
        Returns the label text.
        :rtype: str
        """
        pass

    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        pass

    def setText(self, text):
        """
        Set the label text.
        :type text: str
        """
        pass

    def updateTextPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        :type painter: QPainter
        :type option: int
        :type widget: QWidget
        """
        scene = self.scene()

        if self.isSelected():
            painter.setPen(self.selectionPen)
            painter.drawRect(self.boundingRect())

        if scene.mode is DiagramMode.EdgeInsert and scene.mouseOverNode is self:

            edge = scene.command.edge
            brush = self.brushConnectionOk
            if not scene.validator.valid(edge.source, edge, scene.mouseOverNode):
                brush = self.brushConnectionBad

            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(brush)
            painter.drawRoundedRect(self.boundingRect(), self.radius, self.radius)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        painter.drawRoundedRect(self.polygon, self.radius, self.radius)

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
        rect = cls.createRect(50, 30)

        # Draw the rectangle
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine, Qt.SquareCap, Qt.RoundJoin))
        painter.setBrush(QColor(252, 252, 252))
        painter.translate(kwargs['w'] / 2, kwargs['h'] / 2)
        painter.drawRoundedRect(rect, 14, 14)

        return pixmap