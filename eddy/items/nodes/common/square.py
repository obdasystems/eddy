# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: an editor for the Graphol ontology language.                    #
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
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import re

from abc import ABCMeta

from eddy.datatypes import RestrictionType, DiagramMode
from eddy.exceptions import ParseError
from eddy.items.nodes.common.base import Node
from eddy.items.nodes.common.label import Label

from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QColor, QPainterPath, QPen


class SquaredNode(Node):
    """
    This is the base class for all the Squared shaped nodes.
    """
    __metaclass__ = ABCMeta

    def __init__(self, width=20, height=20, brush='#fcfcfc', restriction=None, cardinality=None, **kwargs):
        """
        Initialize the Squared shaped node.
        :param width: the shape width (unused in current implementation).
        :param height: the shape height (unused in current implementation).
        :param brush: the brush used to paint the node.
        :param restriction: the restriction of the node.
        :param cardinality: the cardinality of the node (if it's a cardinality restriction).
        """
        super().__init__(**kwargs)

        self._restriction = restriction or RestrictionType.exists
        self._cardinality = cardinality if self.restriction is RestrictionType.cardinality else dict(min=None, max=None)

        self.brush = brush
        self.pen = QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine)
        self.rect = self.createRect(20, 20)
        self.label = Label(self.restriction.label, centered=False, editable=False, parent=self)
        self.label.updatePos()

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def restriction(self):
        """
        Returns the restriction of the node.
        :rtype: RestrictionType
        """
        return self._restriction

    @restriction.setter
    def restriction(self, restriction):
        """
        Set the restriction of this node.
        Setting the restriction will also reset the cardinality which would need to be set again.
        :param restriction: the restriction type.
        """
        self._restriction = restriction
        self._cardinality = dict(min=None, max=None)

    @property
    def cardinality(self):
        """
        Returns the cardinality of the node.
        :rtype: dict
        """
        return self._cardinality if self._cardinality is not None else dict(min=None, max=None)

    @cardinality.setter
    def cardinality(self, cardinality):
        """
        Set the restriction of this node.
        Will not set the attribute in case the restriction is not RestrictionType.cardinality.
        :param cardinality: the cartinality of the node.
        """
        self._cardinality = cardinality if self.restriction is RestrictionType.cardinality else dict(min=None, max=None)

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def contextMenu(self):
        """
        Returns the basic nodes context menu.
        :rtype: QMenu
        """
        scene = self.scene()

        menu = super().contextMenu()
        menu.addSeparator()
        menu.insertMenu(scene.mainwindow.actionOpenNodeProperties, scene.mainwindow.menuRestrictionChange)

        # switch the check on the currently active restriction
        for action in scene.mainwindow.actionsRestrictionChange:
            action.setChecked(self.restriction is action.data())

        collection = self.label.contextMenuAdd()
        if collection:
            menu.addSeparator()
            for action in collection:
                menu.insertAction(scene.mainwindow.actionOpenNodeProperties, action)

        menu.insertSeparator(scene.mainwindow.actionOpenNodeProperties)
        return menu

    def copy(self, scene):
        """
        Create a copy of the current item .
        :param scene: a reference to the scene where this item is being copied from.
        """
        kwargs = {
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

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.rect.width()

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    @staticmethod
    def createRect(shape_w, shape_h):
        """
        Returns the initialized rect according to the given width/height.
        :param shape_w: the shape width.
        :param shape_h: the shape height.
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
        :param scene: the scene where the element will be inserted.
        :param E: the Graphol document element entry.
        :rtype: Node
        """
        U = E.elementsByTagName('data:url').at(0).toElement()
        D = E.elementsByTagName('data:description').at(0).toElement()
        G = E.elementsByTagName('shape:geometry').at(0).toElement()
        L = E.elementsByTagName('shape:label').at(0).toElement()

        kwargs = {
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

    ####################################################################################################################
    #                                                                                                                  #
    #   GEOMETRY                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QRectF
        """
        o = self.selectionOffset
        return self.rect.adjusted(-o, -o, o, o)

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRect(self.rect)
        return path

    def shape(self, *args, **kwargs):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRect(self.rect)
        return path

    ####################################################################################################################
    #                                                                                                                  #
    #   LABEL SHORTCUTS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def labelPos(self):
        """
        Returns the current label position.
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
        :param pos: the node position.
        """
        self.label.setPos(pos)

    def setLabelText(self, text):
        """
        Set the label text: will additionally parse the text value and set the restriction type accordingly.
        :raise ParseError: if an invalid text value is supplied.
        :param text: the text value to set.
        """
        value = text.strip().lower()
        if value == RestrictionType.exists.label:
            self.label.setText(value)
            self.restriction = RestrictionType.exists
        elif value == RestrictionType.forall.label:
            self.label.setText(value)
            self.restriction = RestrictionType.forall
        elif value == RestrictionType.self.label:
            self.label.setText(value)
            self.restriction = RestrictionType.self
        else:
            RE_PARSE = re.compile("""^\(\s*(?P<min>[\d-]+)\s*,\s*(?P<max>[\d-]+)\s*\)$""")
            match = RE_PARSE.match(value)
            if match:
                self.label.setText(value)
                self.restriction = RestrictionType.cardinality
                self.cardinality = {
                    'min': None if match.group('min') == '-' else int(match.group('min')),
                    'max': None if match.group('max') == '-' else int(match.group('max')),
                }
            else:
                raise ParseError('invalid restriction supplied: {0}'.format(text))

    def updateLabelPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        self.label.updatePos(*args, **kwargs)

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        :param painter: the active painter.
        :param option: the style option for this item.
        :param widget: the widget that is being painted on.
        """
        scene = self.scene()

        if self.isSelected():
            painter.setPen(self.selectionPen)
            painter.drawRect(self.boundingRect())

        if scene.mode is DiagramMode.EdgeInsert and scene.mouseOverNode is self:
            painter.setPen(self.connectionOkPen)
            painter.setBrush(self.connectionOkBrush)
            painter.drawRect(self.boundingRect())

        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        painter.drawRect(self.rect)