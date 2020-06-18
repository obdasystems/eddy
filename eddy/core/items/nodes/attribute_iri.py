


from PyQt5 import QtCore
from PyQt5 import QtGui

from eddy.core.datatypes.graphol import Identity, Item, Special
from eddy.core.functions.signals import connect, disconnect
from eddy.core.items.common import Polygon
from eddy.core.items.nodes.common.base import AbstractNode, OntologyEntityNode
from eddy.core.items.nodes.common.label import NodeLabel


class AttributeNode(OntologyEntityNode):
    """
    This class implements the 'Attribute' node.
    """
    DefaultBrush = QtGui.QBrush(QtGui.QColor(252, 252, 252, 255))
    DefaultPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
    Identities = {Identity.Attribute,Identity.Individual}
    Type = Item.AttributeIRINode

    def __init__(self, iri = None, width=20, height=20, brush=None, **kwargs):
        """
        Initialize the node.
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(iri=iri, **kwargs)
        brush = brush or AttributeNode.DefaultBrush
        pen = AttributeNode.DefaultPen
        self.fpolygon = Polygon(QtGui.QPainterPath())
        self.background = Polygon(QtCore.QRectF(-14, -14, 28, 28))
        self.selection = Polygon(QtCore.QRectF(-14, -14, 28, 28))
        self.polygon = Polygon(QtCore.QRectF(-10, -10, 20, 20), brush, pen)



    def connectIRIMetaSignals(self):
        connect(self.iri.sgnFunctionalModified,self.onFunctionalModified)

    def disconnectIRIMetaSignals(self):
        disconnect(self.iri.sgnFunctionalModified,self.onFunctionalModified)

    @QtCore.pyqtSlot()
    def onFunctionalModified(self):
        self.updateNode()

    #############################################
    #   INTERFACE
    #################################
    def initialLabelPosition(self):
        return self.center() - QtCore.QPointF(0, 22)

    def occursAsIndividual(self):
        #Class Assertion
        for instEdge in [x for x in self.edges if x.type() is Item.MembershipEdge]:
            if instEdge.source is self:
                return True
        #Object[Data] Property Assertion
        for inputEdge in [x for x in self.edges if x.type() is Item.InputEdge]:
            if inputEdge.source is self and inputEdge.target.type() is Item.PropertyAssertionNode:
                return True
        return False

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
            'iri': None,
        })
        node.setPos(self.pos())
        node.iri = self.iri
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
        return self.iri.functional

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
        self.iri.functional = functional

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
        # TODO implementa nuova versione passando da metodo IRI.isTopBottomEntity (isOWlThing? etc etc...)
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
            if self.iri:
                functional = self.isFunctional()
                # TODO CANCELLA
                if functional is None:
                    functional = False
                # TODO END CANCELLA

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
