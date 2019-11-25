from PyQt5 import QtCore
from PyQt5 import QtGui

from eddy.core.datatypes.graphol import Identity, Item, Special
from eddy.core.functions.misc import snapF
from eddy.core.items.common import Polygon
from eddy.core.items.nodes.common.base import AbstractResizableNode
from eddy.core.items.nodes.common.label import NodeLabel

from eddy.core.functions.signals import connect, disconnect

from eddy import ORGANIZATION, APPNAME
from eddy.core.owl import IRIRender, AnnotationAssertion, IRI, AnnotationAssertionProperty, PrefixedIRI


class ConceptNode(AbstractResizableNode):
    """
    This class implements the 'Concept' node.
    """
    DefaultBrush = QtGui.QBrush(QtGui.QColor(252, 252, 252, 255))
    DefaultPen = QtGui.QPen(QtGui.QBrush(QtGui.QColor(0, 0, 0, 255)), 1.0, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
    Identities = {Identity.Concept}
    Type = Item.ConceptIRINode

    sgnIri

    def __init__(self, iri = None, width=110, height=50, brush=None, **kwargs):
        """
        Initialize the node.
        :type iri: IRI
        :type width: int
        :type height: int
        :type brush: QBrush
        """
        super().__init__(**kwargs)
        w = max(width, 110)
        h = max(height, 50)
        brush = brush or ConceptNode.DefaultBrush
        pen = ConceptNode.DefaultPen
        self.background = Polygon(QtCore.QRectF(-(w + 8) / 2, -(h + 8) / 2, w + 8, h + 8))
        self.selection = Polygon(QtCore.QRectF(-(w + 8) / 2, -(h + 8) / 2, w + 8, h + 8))
        self.polygon = Polygon(QtCore.QRectF(-w / 2, -h / 2, w, h), brush, pen)

        self._iri = iri

        #store the object(IRI, AnnotationAssertion) that is currently used to set the value of the qt label of the node
        self.nodeLabelObject = None

        #self.remaining_characters = remaining_characters

        self.label = NodeLabel(template='Empty', pos=self.center, parent=self, editable=False)
        #TODO to obtain node parent of label ---> self.label.parentItem()
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.updateNode()
        self.updateTextPos()

    def connectSignals(self):
        connect(self.project.sgnPrefixAdded, self.onPrefixAdded)
        connect(self.project.sgnPrefixRemoved, self.onPrefixRemoved)
        connect(self.project.sgnPrefixModified, self.onPrefixModified)
        connect(self.session.sgnRenderingModified, self.onRenderingModified)
        self.connectIRISignals()

    def connectIRISignals(self):
        connect(self.iri.sgnIRIModified, self.onIRIModified)
        connect(self.iri.sgnAnnotationAdded, self.onAnnotationAdded)
        connect(self.iri.sgnAnnotationRemoved, self.onAnnotationRemoved)
        connect(self.iri.sgnAnnotationModified, self.onAnnotationModified)


    def disconnectIRISignals(self):
        disconnect(self.iri.sgnIRIModified, self.onIRIModified)
        disconnect(self.iri.sgnAnnotationAdded, self.onAnnotationAdded)
        disconnect(self.iri.sgnAnnotationRemoved, self.onAnnotationRemoved)
        disconnect(self.iri.sgnAnnotationModified, self.onAnnotationModified)

    @property
    def iri(self):
        '''
        :rtype: IRI
        '''
        return self._iri

    @iri.setter
    def iri(self,iriObj):
        '''
        :type iriObj:IRI
        '''
        if self.iri:
            self.disconnectIRISignals()
        self._iri = iriObj
        self.connectIRISignals()


    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def doUpdateNodeLabel(self):
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering == IRIRender.FULL.value:
            self.setText(str(self.iri))
            self.nodeLabelObject = self.iri
        elif rendering == IRIRender.PREFIX.value:
            prefixed = self.project.getShortestPrefixedForm(self.iri)
            if prefixed:
                self.setText(str(prefixed))
                self.nodeLabelObject = prefixed
            else:
                self.setText(str(self.iri))
                self.nodeLabelObject = self.iri
        elif rendering == IRIRender.LABEL.value:
            labelAssertion = self.iri.getLabelAnnotationAssertion()
            if labelAssertion:
                self.setText(str(labelAssertion.value))
                self.nodeLabelObject = labelAssertion


    @QtCore.pyqtSlot(str)
    def onRenderingModified(self,rendering):
        self.doUpdateNodeLabel()

    @QtCore.pyqtSlot(AnnotationAssertion)
    def onAnnotationAdded(self, annotation):
        '''
        :type annotation: AnnotationAssertion
        '''
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering == IRIRender.LABEL:
            if isinstance(self.nodeLabelObject, IRI) or isinstance(self.nodeLabelObject, PrefixedIRI):
                if annotation.assertionProperty==AnnotationAssertionProperty.Label:
                    self.doUpdateNodeLabel()

    @QtCore.pyqtSlot(AnnotationAssertion)
    def onAnnotationRemoved(self, annotation):
        '''
        :type annotation: AnnotationAssertion
        '''
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering == IRIRender.LABEL:
            if self.nodeLabelObject==annotation:
                self.doUpdateNodeLabel()

    @QtCore.pyqtSlot(AnnotationAssertion)
    def onAnnotationModified(self, annotation):
        '''
        :type annotation: AnnotationAssertion
        '''
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering == IRIRender.LABEL:
            if self.nodeLabelObject == annotation:
                self.doUpdateNodeLabel()

    @QtCore.pyqtSlot()
    def onIRIModified(self):
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering==IRIRender.PREFIX.value or rendering==IRIRender.FULL.value:
            self.doUpdateNodeLabel()

    @QtCore.pyqtSlot()
    def onPrefixAdded(self):
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering==IRIRender.PREFIX.value:
            self.doUpdateNodeLabel()

    @QtCore.pyqtSlot()
    def onPrefixRemoved(self):
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering==IRIRender.PREFIX.value:
            self.doUpdateNodeLabel()

    @QtCore.pyqtSlot()
    def onPrefixModified(self):
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering==IRIRender.PREFIX.value or rendering==IRIRender.FULL.value:
            self.doUpdateNodeLabel()

    #############################################
    #   INTERFACE
    #################################

    def boundingRect(self):
        """
        Returns the shape bounding rectangle.
        :rtype: QtCore.QRectF
        """
        return self.selection.geometry()

    def copy(self, diagram):
        """
        Create a copy of the current item.
        :type diagram: Diagram
        """
        #print('copy >> self',self)
        #print('copy >> type(self)', type(self))
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
        #print('copy END >> self', self)
        return node

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
        return Identity.Concept

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
        painter.drawRect(self.selection.geometry())
        # SYNTAX VALIDATION
        painter.setPen(self.background.pen())
        painter.setBrush(self.background.brush())
        painter.drawRect(self.background.geometry())
        # ITEM SHAPE
        painter.setPen(self.polygon.pen())
        painter.setBrush(self.polygon.brush())
        painter.drawRect(self.polygon.geometry())
        # RESIZE HANDLES
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        for polygon in self.handles:
            painter.setPen(polygon.pen())
            painter.setBrush(polygon.brush())
            painter.drawEllipse(polygon.geometry())

    def painterPath(self):
        """
        Returns the current shape as QtGui.QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        path = QtGui.QPainterPath()
        path.addRect(self.polygon.geometry())
        return path

    def resize(self, mousePos):
        """
        Handle the interactive resize of the shape.
        :type mousePos: QtCore.QPointF
        """
        snap = self.session.action('toggle_grid').isChecked()
        size = self.diagram.GridSize
        moved = self.label.isMoved()
        background = self.background.geometry()
        selection = self.selection.geometry()
        polygon = self.polygon.geometry()

        R = QtCore.QRectF(self.boundingRect())
        D = QtCore.QPointF(0, 0)

        mbrh = 58
        mbrw = 118

        self.prepareGeometryChange()

        if self.mp_Handle == self.HandleTL:

            fromX = self.mp_Bound.left()
            fromY = self.mp_Bound.top()
            toX = fromX + mousePos.x() - self.mp_Pos.x()
            toY = fromY + mousePos.y() - self.mp_Pos.y()
            toX = snapF(toX, size, -4, snap)
            toY = snapF(toY, size, -4, snap)
            D.setX(toX - fromX)
            D.setY(toY - fromY)
            R.setLeft(toX)
            R.setTop(toY)

            ## CLAMP SIZE
            if R.width() < mbrw:
                D.setX(D.x() - mbrw + R.width())
                R.setLeft(R.left() - mbrw + R.width())
            if R.height() < mbrh:
                D.setY(D.y() - mbrh + R.height())
                R.setTop(R.top() - mbrh + R.height())

            background.setLeft(R.left())
            background.setTop(R.top())
            selection.setLeft(R.left())
            selection.setTop(R.top())
            polygon.setLeft(R.left() + 4)
            polygon.setTop(R.top() + 4)

        elif self.mp_Handle == self.HandleTM:

            fromY = self.mp_Bound.top()
            toY = fromY + mousePos.y() - self.mp_Pos.y()
            toY = snapF(toY, size, -4, snap)
            D.setY(toY - fromY)
            R.setTop(toY)

            ## CLAMP SIZE
            if R.height() < mbrh:
                D.setY(D.y() - mbrh + R.height())
                R.setTop(R.top() - mbrh + R.height())

            background.setTop(R.top())
            selection.setTop(R.top())
            polygon.setTop(R.top() + 4)

        elif self.mp_Handle == self.HandleTR:

            fromX = self.mp_Bound.right()
            fromY = self.mp_Bound.top()
            toX = fromX + mousePos.x() - self.mp_Pos.x()
            toY = fromY + mousePos.y() - self.mp_Pos.y()
            toX = snapF(toX, size, +4, snap)
            toY = snapF(toY, size, -4, snap)
            D.setX(toX - fromX)
            D.setY(toY - fromY)
            R.setRight(toX)
            R.setTop(toY)

            ## CLAMP SIZE
            if R.width() < mbrw:
                D.setX(D.x() + mbrw - R.width())
                R.setRight(R.right() + mbrw - R.width())
            if R.height() < mbrh:
                D.setY(D.y() - mbrh + R.height())
                R.setTop(R.top() - mbrh + R.height())

            background.setRight(R.right())
            background.setTop(R.top())
            selection.setRight(R.right())
            selection.setTop(R.top())
            polygon.setRight(R.right() - 4)
            polygon.setTop(R.top() + 4)

        elif self.mp_Handle == self.HandleML:

            fromX = self.mp_Bound.left()
            toX = fromX + mousePos.x() - self.mp_Pos.x()
            toX = snapF(toX, size, -4, snap)
            D.setX(toX - fromX)
            R.setLeft(toX)

            ## CLAMP SIZE
            if R.width() < mbrw:
                D.setX(D.x() - mbrw + R.width())
                R.setLeft(R.left() - mbrw + R.width())

            background.setLeft(R.left())
            selection.setLeft(R.left())
            polygon.setLeft(R.left() + 4)

        elif self.mp_Handle == self.HandleMR:

            fromX = self.mp_Bound.right()
            toX = fromX + mousePos.x() - self.mp_Pos.x()
            toX = snapF(toX, size, +4, snap)
            D.setX(toX - fromX)
            R.setRight(toX)

            ## CLAMP SIZE
            if R.width() < mbrw:
                D.setX(D.x() + mbrw - R.width())
                R.setRight(R.right() + mbrw - R.width())

            background.setRight(R.right())
            selection.setRight(R.right())
            polygon.setRight(R.right() - 4)

        elif self.mp_Handle == self.HandleBL:

            fromX = self.mp_Bound.left()
            fromY = self.mp_Bound.bottom()
            toX = fromX + mousePos.x() - self.mp_Pos.x()
            toY = fromY + mousePos.y() - self.mp_Pos.y()
            toX = snapF(toX, size, -4, snap)
            toY = snapF(toY, size, +4, snap)
            D.setX(toX - fromX)
            D.setY(toY - fromY)
            R.setLeft(toX)
            R.setBottom(toY)

            ## CLAMP SIZE
            if R.width() < mbrw:
                D.setX(D.x() - mbrw + R.width())
                R.setLeft(R.left() - mbrw + R.width())
            if R.height() < mbrh:
                D.setY(D.y() + mbrh - R.height())
                R.setBottom(R.bottom() + mbrh - R.height())

            background.setLeft(R.left())
            background.setBottom(R.bottom())
            selection.setLeft(R.left())
            selection.setBottom(R.bottom())
            polygon.setLeft(R.left() + 4)
            polygon.setBottom(R.bottom() - 4)

        elif self.mp_Handle == self.HandleBM:

            fromY = self.mp_Bound.bottom()
            toY = fromY + mousePos.y() - self.mp_Pos.y()
            toY = snapF(toY, size, +4, snap)
            D.setY(toY - fromY)
            R.setBottom(toY)

            ## CLAMP SIZE
            if R.height() < mbrh:
                D.setY(D.y() + mbrh - R.height())
                R.setBottom(R.bottom() + mbrh - R.height())

            background.setBottom(R.bottom())
            selection.setBottom(R.bottom())
            polygon.setBottom(R.bottom() - 4)

        elif self.mp_Handle == self.HandleBR:

            fromX = self.mp_Bound.right()
            fromY = self.mp_Bound.bottom()
            toX = fromX + mousePos.x() - self.mp_Pos.x()
            toY = fromY + mousePos.y() - self.mp_Pos.y()
            toX = snapF(toX, size, +4, snap)
            toY = snapF(toY, size, +4, snap)
            D.setX(toX - fromX)
            D.setY(toY - fromY)
            R.setRight(toX)
            R.setBottom(toY)

            ## CLAMP SIZE
            if R.width() < mbrw:
                D.setX(D.x() + mbrw - R.width())
                R.setRight(R.right() + mbrw - R.width())
            if R.height() < mbrh:
                D.setY(D.y() + mbrh - R.height())
                R.setBottom(R.bottom() + mbrh - R.height())

            background.setRight(R.right())
            background.setBottom(R.bottom())
            selection.setRight(R.right())
            selection.setBottom(R.bottom())
            polygon.setRight(R.right() - 4)
            polygon.setBottom(R.bottom() - 4)

        self.background.setGeometry(background)
        self.selection.setGeometry(selection)
        self.polygon.setGeometry(polygon)

        self.updateNode(selected=True, handle=self.mp_Handle, anchors=(self.mp_Data, D))
        self.updateTextPos(moved=moved)

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
        path.addRect(self.polygon.geometry())
        for polygon in self.handles:
            path.addEllipse(polygon.geometry())
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