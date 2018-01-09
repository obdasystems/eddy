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

from eddy.core.datatypes.graphol import Identity, Item, Special
from eddy.core.datatypes.owl import OWLProfile
from eddy.core.items.common import Polygon
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.core.items.nodes.common.label import NodeLabel
from eddy.core.project import K_FUNCTIONAL


class AttributeNode(AbstractNode):
    """
    This class implements the 'Attribute' node.
    """
    DefaultBrush = QtGui.QBrush(QtGui.QColor(252, 252, 252, 255))
    DefaultPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
    Identities = {Identity.Attribute}
    Type = Item.AttributeNode

    def __init__(self, width=20, height=20, brush=None, remaining_characters='attribute', **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(**kwargs)
        brush = brush or AttributeNode.DefaultBrush
        pen = AttributeNode.DefaultPen
        self.fpolygon = Polygon(QtGui.QPainterPath())
        self.background = Polygon(QtCore.QRectF(-14, -14, 28, 28))
        self.selection = Polygon(QtCore.QRectF(-14, -14, 28, 28))
        self.polygon = Polygon(QtCore.QRectF(-10, -10, 20, 20), brush, pen)

        self.remaining_characters = remaining_characters

        self.label = NodeLabel(template='attribute', pos=lambda: self.center() - QtCore.QPointF(0, 22), parent=self, editable=True)
        self.label.setAlignment(QtCore.Qt.AlignCenter)

    def IRI(self,project):
        """
        Returns the datatype associated with this node.
        :rtype: str || 'Error multiple IRIS-'* | None | a single iri
        """
        iris = []

        #print('self',self)
        for iri in project.IRI_prefixes_nodes_dict.keys():
            nodes = project.IRI_prefixes_nodes_dict[iri][1]
            if (self in nodes) or (str(self) in str(nodes)):
                iris.append(iri)

        if len(iris) == 1:
            return iris[0]
        if len(iris) == 0:
            return None

        return str('Error multiple IRIS-'+iris)

    """
    def IRI_version(self,project):

        iri = self.IRI(project)

        if 'Error multiple IRIS-' in iri:
            return 'Error multiple IRIS-'
        else:
            if iri is None:
                return None
            else:
                return project.IRI_prefixes_nodes_dict[iri][3]
    """
    def prefix(self,project):
        """
        Returns the value value associated with this node.
        :rtype: str ||  'Error multiple IRIS-'* | None | a single prefix
        """
        iri = self.IRI(project)

        if iri is None:
            return None
        if 'Error multiple IRIS-' in iri:
            return iri

        prefixes = project.IRI_prefixes_nodes_dict[iri][0]

        if len(prefixes) == 0:
            return None

        sorted_lst = sorted(list(prefixes))

        return sorted_lst[0]

    #############################################
    #   INTERFACE
    #################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QRectF
        """
        return self.selection.geometry()

    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        node = diagram.factory.create(self.type(), **{
            'id': self.id,
            'brush': self.brush(),
            'height': self.height(),
            'width': self.width(),
            'remaining_characters': self.remaining_characters,
        })
        node.setPos(self.pos())
        node.setText(self.text())
        node.setTextPos(node.mapFromScene(self.mapToScene(self.textPos())))
        return node

    def definition(self):
        """
        Returns the list of nodes which contribute to the definition of this very node.
        :rtype: set
        """
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.type() in {Item.DomainRestrictionNode, Item.RangeRestrictionNode}
        return set(self.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        return self.polygon.geometry().height()

    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return Identity.Attribute

    def isFunctional(self):
        """
        Returns True if the predicate represented by this node is functional, else False.
        :rtype: bool
        """
        try:
            return self.project.meta(self.type(), self.text())[K_FUNCTIONAL] and \
                   self.project.profile.type() is not OWLProfile.OWL2QL
        except (AttributeError, KeyError):
            return False

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the diagram.
        :type painter: QPainter
        :type option: QStyleOptionGraphicsItem
        :type widget: QWidget
        """
        # SET THE RECT THAT NEEDS TO BE REPAINTED
        painter.setClipRect(option.exposedRect)
        # SELECTION AREA
        painter.setPen(self.selection.pen())
        painter.setBrush(self.selection.brush())
        painter.drawEllipse(self.selection.geometry())
        # SYNTAX VALIDATION
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(self.background.pen())
        painter.setBrush(self.background.brush())
        painter.drawEllipse(self.background.geometry())
        # ITEM SHAPE
        painter.setPen(self.polygon.pen())
        painter.setBrush(self.polygon.brush())
        painter.drawEllipse(self.polygon.geometry())
        # FUNCTIONALITY
        painter.setPen(self.fpolygon.pen())
        painter.setBrush(self.fpolygon.brush())
        painter.drawPath(self.fpolygon.geometry())

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addEllipse(self.polygon.geometry())
        return path

    def setFunctional(self, functional):
        """
        Set the functional property of the predicate represented by this node.
        :type functional: bool
        """
        meta = self.project.meta(self.type(), self.text())
        meta[K_FUNCTIONAL] = bool(functional)
        self.project.setMeta(self.type(), self.text(), meta)
        for node in self.project.predicates(self.type(), self.text()):
            node.updateNode(functional=functional, selected=node.isSelected())

    def setIdentity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

    def setText(self, text):
        """
        Set the label text.
        :type text: str
        """
        self.label.setText(text)
        self.label.setAlignment(QtCore.Qt.AlignCenter)

    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        self.label.setPos(pos)

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addEllipse(self.polygon.geometry())
        return path

    def special(self):
        """
        Returns the special type of this node.
        :rtype: Special
        """
        return Special.valueOf(self.text())

    def text(self):
        """
        Returns the label text.
        :rtype: str
        """
        return self.label.text()

    def textPos(self):
        """
        Returns the current label position in item coordinates.
        :rtype: QPointF
        """
        return self.label.pos()

    def updateNode(self, functional=None, **kwargs):
        """
        Update the current node.
        :type functional: bool
        """
        if functional is None:
            functional = self.isFunctional()

        # FUNCTIONAL POLYGON (SHAPE)
        path1 = QtGui.QPainterPath()
        path1.addEllipse(self.polygon.geometry())
        path2 = QtGui.QPainterPath()
        path2.addEllipse(QtCore.QRectF(-7, -7, 14, 14))
        self.fpolygon.setGeometry(path1.subtracted(path2))

        # FUNCTIONAL POLYGON (PEN & BRUSH)
        pen = QtGui.QPen(QtCore.Qt.NoPen)
        brush = QtGui.QBrush(QtCore.Qt.NoBrush)
        if functional:
            pen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
            brush = QtGui.QBrush(QtGui.QColor(252, 252, 252, 255))
        self.fpolygon.setPen(pen)
        self.fpolygon.setBrush(brush)

        # SELECTION + BACKGROUND + CACHE REFRESH
        super().updateNode(**kwargs)

    def updateTextPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        self.label.updatePos(*args, **kwargs)

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        return self.polygon.geometry().width()

    def __repr__(self):
        """
        Returns repr(self).
        """
        return '{0}:{1}:{2}'.format(self.__class__.__name__, self.text(), self.id)