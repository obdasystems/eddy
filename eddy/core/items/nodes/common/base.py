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


from abc import ABCMeta, abstractmethod

from PyQt5.QtCore import QPointF, QLineF, Qt, QRectF
from PyQt5.QtGui import QColor, QPen, QPainter, QBrush
from PyQt5.QtWidgets import QMenu, QGraphicsItem

from eddy.core.commands import CommandNodeRezize
from eddy.core.datatypes import Color, DistinctList, DiagramMode, Identity, Item
from eddy.core.items import AbstractItem

from eddy.ui.properties import NodeProperties


class AbstractNode(AbstractItem):
    """
    Base class for all the diagram nodes.
    """
    __metaclass__ = ABCMeta

    identities = {} # a set of identities this node may assume
    name = 'node' # a string identifying this node
    prefix = 'n' # prefix to be prepended to node ids
    brushConnectionBad = QBrush(QColor(179, 12, 12, 160)) # brush used to highlight wrong connections
    brushConnectionOk = QBrush(QColor(43, 173, 63, 160)) # brush used to highlight good connections
    selectionOffset = 4 # used in non-resizable nodes to space the bounding rect from the shape
    selectionPen = QPen(QColor(0, 0, 0), 1.0, Qt.DashLine) # used to draw the bounding rect when the item is selected
    xmlname = 'node' # a string identifying this node in XML documents

    def __init__(self, **kwargs):
        """
        Initialize the node.
        """
        super().__init__(**kwargs)

        self._brush = None
        self._pen = None

        self.anchors = {}
        self.edges = DistinctList()

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    def brush(self):
        """
        Returns the brush used to paint this node.
        :rtype: QBrush
        """
        if self._brush is None:
            self._brush = QBrush(QColor(Color.White.value))
        return self._brush

    @brush.setter
    def brush(self, brush):
        """
        Set the brush used to paint this node.
        :type brush: T <= QBrush | QColor | Color | tuple | list | bytes | unicode
        """
        if isinstance(brush, QBrush):
            self._brush = brush
        elif isinstance(brush, QColor):
            self._brush = QBrush(brush)
        elif isinstance(brush, Color):
            self._brush = QBrush(QColor(brush.value))
        elif isinstance(brush, tuple) or isinstance(brush, list):
            self._brush = QBrush(QColor(*brush))
        elif isinstance(brush, str):
            self._brush = QBrush(QColor(brush))
        else:
            raise ValueError('invalid brush specified: {}'.format(brush))

    @property
    def constructor(self):
        """
        Tells whether this node is a constructor node.
        :rtype: bool
        """
        return Item.DomainRestrictionNode <= self.item <= Item.PropertyAssertionNode

    @property
    @abstractmethod
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        pass

    @identity.setter
    @abstractmethod
    def identity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

    @property
    def pen(self):
        """
        Returns the pen used to paint this node.
        :rtype: QPen
        """
        if self._pen is None:
            self._pen = QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine)
        return self._pen

    @pen.setter
    def pen(self, pen):
        """
        Set the pen used to paint this node.
        :type pen: QPen
        """
        self._pen = pen

    @property
    def predicate(self):
        """
        Tells whether this node is a predicate node.
        :rtype: bool
        """
        return Item.ConceptNode <= self.item <= Item.ValueRestrictionNode

    @property
    def resizable(self):
        """
        Tells whether the shape can be resized or not.
        :rtype: bool
        """
        return False

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
        self.edges.append(edge)

    def anchor(self, edge):
        """
        Returns the anchor point of the given edge in scene coordinates.
        :type edge: AbstractEdge
        :rtype: QPointF
        """
        try:
            return self.anchors[edge]
        except KeyError:
            self.anchors[edge] = self.mapToScene(self.center())
            return self.anchors[edge]

    def center(self):
        """
        Returns the point at the center of the shape in item's coordinate.
        :rtype: QPointF
        """
        return self.boundingRect().center()

    def contextMenu(self):
        """
        Returns the basic nodes context menu.
        :rtype: QMenu
        """
        scene = self.scene()
        menu = QMenu()
        menu.addAction(scene.mainwindow.actionDelete)
        menu.addSeparator()
        menu.addAction(scene.mainwindow.actionCut)
        menu.addAction(scene.mainwindow.actionCopy)
        menu.addAction(scene.mainwindow.actionPaste)
        menu.addSeparator()
        menu.addAction(scene.mainwindow.actionBringToFront)
        menu.addAction(scene.mainwindow.actionSendToBack)
        menu.addSeparator()
        menu.addAction(scene.mainwindow.actionOpenNodeProperties)
        return menu

    @abstractmethod
    def copy(self, scene):
        """
        Create a copy of the current item.
        :type scene: DiagramScene
        """
        pass

    @abstractmethod
    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        pass

    def intersection(self, line):
        """
        Returns the intersection of the shape with the given line (in scene coordinates).
        :type line: QLineF
        :rtype: QPointF
        """
        intersection = QPointF()
        path = self.painterPath()
        polygon = self.mapToScene(path.toFillPolygon(self.transform()))

        for i in range(0, polygon.size() - 1):
            polyline = QLineF(polygon[i], polygon[i + 1])
            if polyline.intersect(line, intersection) == QLineF.BoundedIntersection:
                return intersection

        return None

    def moveBy(self, x, y):
        """
        Move the node by the given deltas.
        :type x: T <= float | int
        :type y: T <= float | int
        """
        move = QPointF(x, y)
        self.setPos(self.pos() + move)
        self.anchors = {edge: pos + move for edge, pos in self.anchors.items()}

    def pos(self):
        """
        Returns the position of this node in scene coordinates.
        :rtype: QPointF
        """
        return self.mapToScene(self.center())

    def propertiesDialog(self):
        """
        Build and returns the node properties dialog.
        :rtype: QDialog
        """
        return NodeProperties(scene=self.scene(), node=self)

    def removeEdge(self, edge):
        """
        Remove the given edge from the current node.
        :type edge: AbstractEdge
        """
        self.edges.remove(edge)

    def setAnchor(self, edge, pos):
        """
        Set the given position as anchor for the given edge.
        :type edge: AbstractEdge
        :type pos: QPointF
        """
        self.anchors[edge] = pos

    def setPos(self, *__args):
        """
        Set the item position.
        QGraphicsItem.setPos(QPointF)
        QGraphicsItem.setPos(float, float)
        """
        if len(__args) == 1:
            pos = __args[0]
        elif len(__args) == 2:
            pos = QPointF(__args[0], __args[1])
        else:
            raise TypeError('too many arguments; expected {}, got {}'.format(2, len(__args)))
        super().setPos(pos + super().pos() - self.pos())

    def updateEdges(self):
        """
        Update all the edges attached to the node.
        """
        # The code below seems to be causing several slow downs to
        # the UI when moving multiple nodes across the diagram scene.
        #
        # try:
        #     # update it for all the selected nodes in case we are
        #     # moving multiple nodes across the whole scene
        #     scene = self.scene()
        #     for node in scene.selectedNodes():
        #         for edge in node.edges:
        #             edge.updateEdge()
        # except AttributeError:
        #     # if we don't have the scene update only local edges: this is
        #     # mostly used when we load a graphol document from disk
        #     for edge in self.edges:
        #         edge.updateEdge()
        for edge in self.edges:
            edge.updateEdge()

    @abstractmethod
    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   IMPORT / EXPORT                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    @classmethod
    @abstractmethod
    def fromGraphol(cls, scene, E):
        """
        Create a new item instance by parsing a Graphol document item entry.
        :type scene: DiagramScene
        :type E: QDomElement
        :rtype: AbstractNode
        """
        pass

    @abstractmethod
    def toGraphol(self, document):
        """
        Export the current item in Graphol format.
        :type document: QDomDocument
        :rtype: QDomElement
        """
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def contextMenuEvent(self, menuEvent):
        """
        Bring up the context menu for the given node.
        :type menuEvent: QGraphicsSceneContextMenuEvent
        """
        scene = self.scene()
        scene.clearSelection()

        self.setSelected(True)

        contextMenu = self.contextMenu()
        contextMenu.exec_(menuEvent.screenPos())

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the item.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()

        # allow node selection only if we are in DiagramMode.Idle state: resizable
        # nodes may have changed the scene mode to DiagramMode.NodeResize if a resize
        # handle is selected, thus we don't need to perform (multi)selection
        if scene.mode is DiagramMode.Idle:

            # here is a slightly modified version of the default behavior
            # which improves the interaction with multiple selected nodes
            if mouseEvent.modifiers() & Qt.ControlModifier:
                # if the control modifier is being held switch the selection flag
                self.setSelected(not self.isSelected())
            else:
                if scene.selectedItems():
                    # some elements are already selected (previoust mouse press event)
                    if not self.isSelected():
                        # there are some items selected but we clicked on a node
                        # which is not currently selected, so select only this one
                        scene.clearSelection()
                        self.setSelected(True)
                else:
                    # no node is selected and we just clicked on one so select it
                    # since we filter out the Label, clear the scene selection
                    # in any case to avoid strange bugs.
                    scene.clearSelection()
                    self.setSelected(True)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is being moved over the item while being pressed (EXCLUDED).
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        pass

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the item (EXCLUDED).
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   GEOMETRY                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    @abstractmethod
    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   LABEL SHORTCUTS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    @abstractmethod
    def labelPos(self):
        """
        Returns the current label position.
        :rtype: QPointF
        """
        pass

    @abstractmethod
    def labelText(self):
        """
        Returns the label text.
        :rtype: str
        """
        pass

    @abstractmethod
    def setLabelPos(self, pos):
        """
        Set the label position updating the 'moved' flag accordingly.
        :type pos: QPointF
        """
        pass

    @abstractmethod
    def setLabelText(self, text):
        """
        Set the label text.
        :type text: T <= bytes | unicode
        """
        pass

    @abstractmethod
    def updateLabelPos(self, *args, **kwargs):
        """
        Update the label position.
        """
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    @classmethod
    @abstractmethod
    def image(cls, **kwargs):
        """
        Returns an image suitable for the palette.
        :rtype: QPixmap
        """
        pass


class AbstractResizableNode(AbstractNode):
    """
    Base class for all the diagram resizable nodes.
    """
    __metaclass__ = ABCMeta

    handleTL = 1
    handleTM = 2
    handleTR = 3
    handleML = 4
    handleMR = 5
    handleBL = 6
    handleBM = 7
    handleBR = 8

    handleBrush = QColor(168, 168, 168, 255)
    handlePen = QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    handleSize = +8.0
    handleSpace = -4.0

    handleCursors = {
        handleTL: Qt.SizeFDiagCursor,
        handleTM: Qt.SizeVerCursor,
        handleTR: Qt.SizeBDiagCursor,
        handleML: Qt.SizeHorCursor,
        handleMR: Qt.SizeHorCursor,
        handleBL: Qt.SizeBDiagCursor,
        handleBM: Qt.SizeVerCursor,
        handleBR: Qt.SizeFDiagCursor,
    }

    def __init__(self, **kwargs):
        """
        Initialize the node.
        """
        super(AbstractResizableNode, self).__init__(**kwargs)

        self.command = None
        self.handles = dict()
        self.handleSelected = None
        self.mousePressData = None
        self.mousePressPos = None
        self.mousePressRect = None

    ####################################################################################################################
    #                                                                                                                  #
    #   PROPERTIES                                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    @property
    @abstractmethod
    def identity(self):
        """
        Returns the identity of the current node.
        :rtype: Identity
        """
        pass

    @identity.setter
    @abstractmethod
    def identity(self, identity):
        """
        Set the identity of the current node.
        :type identity: Identity
        """
        pass

    @property
    def resizable(self):
        """
        Tells whether the shape can be resized or not.
        :rtype: bool
        """
        return True

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def handleAt(self, point):
        """
        Returns the resize handle below the given point.
        Will return None if the mouse is not over a resizing handle.
        :type point: QPointF
        :rtype: int
        """
        for k, v, in self.handles.items():
            if v.contains(point):
                return k
        return None

    def updateHandlesPos(self):
        """
        Update current resize handles according to the shape size and position.
        """
        s = self.handleSize
        b = self.boundingRect()
        self.handles[self.handleTL] = QRectF(b.left(), b.top(), s, s)
        self.handles[self.handleTM] = QRectF(b.center().x() - s / 2, b.top(), s, s)
        self.handles[self.handleTR] = QRectF(b.right() - s, b.top(), s, s)
        self.handles[self.handleML] = QRectF(b.left(), b.center().y() - s / 2, s, s)
        self.handles[self.handleMR] = QRectF(b.right() - s, b.center().y() - s / 2, s, s)
        self.handles[self.handleBL] = QRectF(b.left(), b.bottom() - s, s, s)
        self.handles[self.handleBM] = QRectF(b.center().x() - s / 2, b.bottom() - s, s, s)
        self.handles[self.handleBR] = QRectF(b.right() - s, b.bottom() - s, s, s)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def hoverMoveEvent(self, hoverEvent):
        """
        Executed when the mouse moves over the shape (NOT PRESSED).
        :type hoverEvent: QGraphicsSceneHoverEvent
        """
        scene = self.scene()

        # display resize handle only if we are idle: it's not possible to start a resizing operation from any
        # other state so it makes no sense in displaying the cursor for the resize if we cannot enter the mode
        if scene.mode is DiagramMode.Idle:
            if self.isSelected():
                handle = self.handleAt(hoverEvent.pos())
                self.setCursor(Qt.ArrowCursor if handle is None else self.handleCursors[handle])

        super().hoverMoveEvent(hoverEvent)

    def hoverLeaveEvent(self, hoverEvent):
        """
        Executed when the mouse leaves the shape (NOT PRESSED).
        :type hoverEvent: QGraphicsSceneHoverEvent
        """
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(hoverEvent)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the item.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()

        if scene.mode is DiagramMode.Idle:
            self.handleSelected = self.handleAt(mouseEvent.pos())
            if self.handleSelected:
                scene.clearSelection()
                scene.setMode(DiagramMode.NodeResize)
                self.setSelected(True)
                self.mousePressPos = mouseEvent.pos()
                self.mousePressRect = self.boundingRect()
                self.mousePressData = {edge: pos for edge, pos in self.anchors.items()}

        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is being moved over the item while being pressed.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()

        if scene.mode is DiagramMode.NodeResize:
            self.command = self.command or CommandNodeRezize(scene=self.scene(), node=self)
            self.interactiveResize(mouseEvent.pos())
            self.updateEdges()

        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the item.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        scene = self.scene()

        if scene.mode is DiagramMode.NodeResize:
            if self.command:
                self.command.end()
                scene.undostack.push(self.command)
                scene.setMode(DiagramMode.Idle)

        super().mouseReleaseEvent(mouseEvent)

        self.command = None
        self.handleSelected = None
        self.mousePressData = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.updateEdges()
        self.update()

    ####################################################################################################################
    #                                                                                                                  #
    #   GEOMETRY                                                                                                       #
    #                                                                                                                  #
    ####################################################################################################################

    @abstractmethod
    def interactiveResize(self, mousePos):
        """
        Handle the interactive resize of the node.
        :type mousePos: QPointF
        """
        pass

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def paintHandles(self, painter):
        """
        Paint node resizing handles.
        :type painter: QPainter
        """
        if self.isSelected():
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(self.handleBrush)
            painter.setPen(self.handlePen)
            for handle, rect in self.handles.items():
                if self.handleSelected is None or handle == self.handleSelected:
                    painter.drawEllipse(rect)