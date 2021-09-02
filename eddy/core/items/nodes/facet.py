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


from PyQt5 import (
    QtCore,
    QtGui,
)

from eddy.core.datatypes.graphol import (
    Identity,
    Item,
)
from eddy.core.functions.misc import first
from eddy.core.items.common import Polygon
from eddy.core.items.nodes.common.base import AbstractNode
from eddy.core.items.nodes.common.label import NodeLabel


class FacetNode(AbstractNode):
    """
    This class implements the 'Facet' node.
    """
    IndexTL = 0
    IndexTR = 1
    IndexBR = 2
    IndexBL = 3
    IndexEE = 4

    DefaultBrushA = QtGui.QBrush(QtGui.QColor(222, 222, 222, 255))
    DefaultBrushB = QtGui.QBrush(QtGui.QColor(252, 252, 252, 255))
    DefaultPenA = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
    DefaultPenB = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
    Identities = {Identity.Facet}
    Type = Item.FacetNode

    def __init__(self, facet=None, width=80, height=40, brush=None, **kwargs):
        """
        Initialize the node.
        :type facet: Facet
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(**kwargs)
        self.background = Polygon(self.createPolygon(88, 48))
        self.selection = Polygon(self.createPolygon(88, 48))
        self.polygon = Polygon(self.createPolygon(80, 40))
        self.polygonA = Polygon(self.createPolygonA(80, 40), FacetNode.DefaultBrushA, FacetNode.DefaultPenA)
        self.polygonB = Polygon(self.createPolygonA(80, 40), FacetNode.DefaultBrushB, FacetNode.DefaultPenB)
        self._facet = facet

        self.labelA = NodeLabel('Empty', pos=self.centerA, editable=False, movable=False, parent=self)
        self.labelB = NodeLabel('"Empty"', pos=self.centerB, editable=False, movable=False, parent=self)
        self.updateNode()
        self.updateTextPos()

    #############################################
    #   PROPERTIES
    #################################

    @property
    def datatype(self):
        """
        Returns the datatype this facet is restricting, or None if the node is isolated.
        :rtype: Datatype
        """
        f1 = lambda x: x.type() is Item.InputEdge
        f2 = lambda x: x.type() is Item.DatatypeRestrictionNode
        f3 = lambda x: x.type() is Item.ValueDomainNode
        outgoing = first(self.outgoingNodes(filter_on_edges=f1, filter_on_nodes=f2))
        if outgoing:
            incoming = first(outgoing.incomingNodes(filter_on_edges=f1, filter_on_nodes=f3))
            if incoming:
                return incoming.datatype
        return None

    @property
    def facet(self):
        """
        Returns the facet associated with this node.
        :rtype: Facet
        """
        return self._facet

    @facet.setter
    def facet(self, facet):
        """
        Sets the facet associated with this node.
        :type facet: Facet
        """
        self._facet = facet
        if self.diagram:
            self.doUpdateNodeLabel()
            self.diagram.project.sgnUpdated.emit()

    #############################################
    #   EVENTS
    #################################

    def mouseDoubleClickEvent(self, mouseEvent):
        """
        Executed when the mouse is double clicked on the text item.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        self.session.doOpenConstrainingFacetBuilder(self)
        mouseEvent.accept()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def doUpdateNodeLabel(self):
        iri = self.facet.constrainingFacet
        prefixed = iri.manager.getShortestPrefixedForm(iri)
        if prefixed:
            self.labelA.setText(str(prefixed))
        else:
            self.labelA.setText('<{}>'.format(str(iri)))

        literal = self.facet.literal
        self.labelB.setText(str(literal))

    #############################################
    #   INTERFACE
    #################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QtCore.QRectF
        """
        path = QtGui.QPainterPath()
        path.addPolygon(self.selection.geometry())
        return path.boundingRect()

    def brushA(self):
        """
        Returns the brush used to paint the shape A of this node.
        :rtype: QtGui.QBrush
        """
        return self.polygonA.brush()

    def brushB(self):
        """
        Returns the brush used to paint the shape B of this node.
        :rtype: QtGui.QBrush
        """
        return self.polygonB.brush()

    def centerA(self):
        """
        Returns the center point of polygon A.
        :rtype: QPointF
        """
        return self.boundingRect().center() - QtCore.QPointF(0, 40 / 4)

    def centerB(self):
        """
        Returns the center point of polygon A.
        :rtype: QPointF
        """
        return self.boundingRect().center() + QtCore.QPointF(0, 40 / 4)

    @staticmethod
    def compose(facet, value):
        """
        Compose the restriction string.
        :type facet: Facet
        :type value: str
        :return: str
        """
        return '{0}^^"{1}"'.format(facet.value, value.strip().strip('"'))

    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        node = diagram.factory.create(self.type(), **{
            'id': self.id,
            'facet': self.facet,
            'height': self.height(),
            'width': self.width()
        })
        node.setPos(self.pos())
        node.setText(self.text())
        node.updateNode()
        node.setTextPos(node.mapFromScene(self.mapToScene(self.textPos())))
        return node

    def definition(self):
        """
        Returns the list of nodes which contribute to the definition of this very node.
        :rtype: set
        """
        return set(self.incomingNodes(filter_on_edges=lambda x: x.type() is Item.InputEdge))

    @staticmethod
    def createPolygon(w, h):
        """
        Returns the initialized polygon according to the given width/height.
        :type w: int
        :type h: int
        :rtype: QtGui.QPolygonF
        """
        return QtGui.QPolygonF([
            QtCore.QPointF(-w / 2 + 10, -h / 2),
            QtCore.QPointF(+w / 2, -h / 2),
            QtCore.QPointF(+w / 2 - 10, +h / 2),
            QtCore.QPointF(-w / 2, +h / 2),
            QtCore.QPointF(-w / 2 + 10, -h / 2),
        ])

    @staticmethod
    def createPolygonA(w, h):
        """
        Returns the initialized top-half polygon according to the given width/height.
        :type w: int
        :type h: int
        :rtype: QtGui.QPolygonF
        """
        return QtGui.QPolygonF([
            QtCore.QPointF(-w / 2 + 10, -h / 2),
            QtCore.QPointF(+w / 2, -h / 2),
            QtCore.QPointF(+w / 2 - 10 / 2, 0),
            QtCore.QPointF(-w / 2 + 10 / 2, 0),
            QtCore.QPointF(-w / 2 + 10, -h / 2),
        ])

    @staticmethod
    def createPolygonB(w, h):
        """
        Returns the initialized bottom-half polygon according to the given width/height.
        :type w: int
        :type h: int
        :rtype: QtGui.QPolygonF
        """
        return QtGui.QPolygonF([
            QtCore.QPointF(-w / 2 + 10 / 2, 0),
            QtCore.QPointF(+w / 2 - 10 / 2, 0),
            QtCore.QPointF(+w / 2 - 10, +h / 2),
            QtCore.QPointF(-w / 2, +h / 2),
            QtCore.QPointF(-w / 2 + 10 / 2, 0),
        ])

    def geometryA(self):
        """
        Returns the geometry of the shape A of this node.
        :rtype: QtGui.QPolygonF
        """
        return self.polygonA.geometry()

    def geometryB(self):
        """
        Returns the geometry of the shape B of this node.
        :rtype: QtGui.QPolygonF
        """
        return self.polygonB.geometry()

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        polygonA = self.polygonA.geometry()
        polygonB = self.polygonB.geometry()
        return polygonA[self.IndexBL].y() - polygonB[self.IndexTL].y()

    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        return Identity.Facet

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
        painter.drawPolygon(self.selection.geometry())
        # SYNTAX VALIDATION
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(self.background.pen())
        painter.setBrush(self.background.brush())
        painter.drawPolygon(self.background.geometry())
        # SHAPE
        painter.setPen(self.polygonA.pen())
        painter.setBrush(self.polygonA.brush())
        painter.drawPolygon(self.polygonA.geometry())
        painter.setPen(self.polygonB.pen())
        painter.setBrush(self.polygonB.brush())
        painter.drawPolygon(self.polygonB.geometry())

    def painterPath(self):
        """
        Returns the current shape as QtGui.QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addPolygon(self.polygon.geometry())
        return path

    def penA(self):
        """
        Returns the pen used to paint the shape A of this node.
        :rtype: QtGui.QPen
        """
        return self.polygonA.pen()

    def penB(self):
        """
        Returns the pen used to paint the shape B of this node.
        :rtype: QtGui.QPen
        """
        return self.polygonB.pen()

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
        pass

    def setTextPos(self, pos):
        """
        Set the label position.
        :type pos: QPointF
        """
        pass

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addPolygon(self.polygon.geometry())
        return path

    def text(self):
        """
        Returns the label text.
        :rtype: str
        """
        if self.facet:
            return str(self.facet)
        return 'Facet'

    def textPos(self):
        """
        Returns the current label position in item coordinates.
        :rtype: QPointF
        """
        return self.boundingRect().center()

    def updateNode(self, *args, **kwargs):
        """
        Update the current node.
        """
        # POLYGONS + BACKGROUND + SELECTION (GEOMETRY)
        width = max(self.labelA.width() + 16, self.labelB.width() + 16, 80)
        self.background.setGeometry(self.createPolygon(width + 8, 48))
        self.selection.setGeometry(self.createPolygon(width + 8, 48))
        self.polygon.setGeometry(self.createPolygon(width, 40))
        self.polygonA.setGeometry(self.createPolygonA(width, 40))
        self.polygonB.setGeometry(self.createPolygonB(width, 40))
        self.updateTextPos()
        self.updateEdges()

        # SELECTION + BACKGROUND + CACHE REFRESH
        super().updateNode(**kwargs)

    def updateTextPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        self.labelA.updatePos()
        self.labelB.updatePos()

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        polygonA = self.polygonA.geometry()
        polygonB = self.polygonB.geometry()
        return polygonA[self.IndexTR].x() - polygonB[self.IndexBL].x()
