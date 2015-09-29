# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  pyGraphol: a python design tool for the Graphol language.             #
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


from copy import deepcopy
from pygraphol.commands import CommandNodeRezize
from pygraphol.dialogs.properties import NodePropertiesDialog
from PyQt5.QtCore import Qt, QPointF, QRectF, QLineF
from PyQt5.QtGui import QColor, QPen, QPainter, QIcon
from PyQt5.QtWidgets import QGraphicsItem, QMenu


class AbstractNodeShape(QGraphicsItem):
    """
    This is the base class for all the node shapes.
    """
    shapeBrush = QColor(252, 252, 252)
    shapeBrushSelected = QColor(251, 255, 148)
    shapePen = QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine)

    def __init__(self, item, **kwargs):
        """
        Initialize basic shape attributes.
        :param item: the item this shape is attached to
        """
        self.item = item
        self.anchors = {}

        kwargs.pop('id', None)

        super().__init__(**kwargs)

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

    ################################################### PROPERTIES #####################################################

    @property
    def node(self):
        """
        Returns the node this shape is attached to.
        :rtype: Node
        """
        return self.item

    @property
    def resizable(self):
        """
        Tells whether the shape can be resized or not.
        :rtype: bool
        """
        return False

    ################################################# EVENT HANDLERS ###################################################

    def contextMenuEvent(self, menuEvent):
        """
        Bring up the context menu for the given node.
        :param menuEvent: the context menu event instance.
        """
        scene = self.scene()
        scene.clearSelection()

        self.setSelected(True)

        contextMenu = self.contextMenu()
        contextMenu.exec_(menuEvent.screenPos())

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the item.
        :param mouseEvent: the mouse event instance.
        """
        # here is a slightly modified version of the default behavior
        # which improves the interaction with multiple selected nodes
        if mouseEvent.modifiers() & Qt.ControlModifier:
            # if the control modifier is being held switch the selection flag
            self.setSelected(not self.isSelected())
        else:
            scene = self.scene()
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
        Executed when the mouse is being moved over the item while being pressed.
        :param mouseEvent: the mouse move event instance.
        """
        pass

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the item.
        :param mouseEvent: the mouse event instance.
        """
        pass

    ##################################################### GEOMETRY #####################################################

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        raise NotImplementedError('method `painterPath` must be implemented in inherited class')

    ################################################ AUXILIARY METHODS #################################################

    def anchor(self, edge):
        """
        Returns the anchor point of the given edge (shape) in scene coordinates.
        :rtype: QPointF
        """
        try:
            return self.anchors[edge]
        except KeyError:
            self.anchors[edge] = self.mapToScene(self.center())
            return self.anchors[edge]

    def center(self):
        """
        Returns the point at the center of the shape.
        :rtype: QPointF
        """
        return self.boundingRect().center()

    def contextMenu(self):
        """
        Returns the basic nodes context menu.
        :rtype: QMenu
        """
        menu = QMenu()
        scene = self.scene()

        menu.addAction(scene.actionItemDelete)
        menu.addSeparator()
        menu.addAction(scene.actionItemCut)
        menu.addAction(scene.actionItemCopy)
        menu.addAction(scene.actionItemPaste)
        menu.addSeparator()
        menu.addAction(scene.actionBringToFront)
        menu.addAction(scene.actionSendToBack)
        menu.addSeparator()

        prop = menu.addAction(QIcon(':/icons/preferences'), 'Properties...')
        prop.triggered.connect(self.handleNodeProperties)

        return menu

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        raise NotImplementedError('method `height` must be implemented in inherited class')

    def intersection(self, line):
        """
        Returns the intersection of the shape with the given line (in scene coordinates).
        :param line: the line whose intersection needs to be calculated (in scene coordinates).
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

    def setAnchor(self, edge, pos):
        """
        Set the given position as anchor for the given edge.
        :param edge: the edge used to index the new position.
        :param pos: the anchor position.
        """
        self.anchors[edge] = pos

    def updateEdges(self):
        """
        Update all the edges attached to the node.
        """
        try:
            # update it for all the selected nodes in case we are
            # moving multiple nodes across the whole scene
            scene = self.scene()
            for shape in scene.selectedNodes():
                for edge in shape.node.edges:
                    edge.shape.updateEdge()
        except AttributeError:
            # if we don't have the scene update only local edges: this is
            # mostly used when we load a graphol document from disk
            for edge in self.node.edges:
                edge.shape.updateEdge()

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        raise NotImplementedError('method `width` must be implemented in inherited class')

    ################################################# LABEL SHORTCUTS ##################################################

    def labelPos(self):
        """
        Returns the current label position.
        :rtype: QPointF
        """
        raise NotImplementedError('method `labelPos` must be implemented in inherited class')

    def labelText(self):
        """
        Returns the label text.
        :rtype: str
        """
        raise NotImplementedError('method `labelText` must be implemented in inherited class')

    def setLabelPos(self, pos):
        """
        Set the label position updating the 'moved' flag accordingly.
        :param pos: the node position.
        """
        raise NotImplementedError('method `setLabelPos` must be implemented in inherited class')

    def setLabelText(self, text):
        """
        Set the label text.
        :param text: the text value to set.
        """
        raise NotImplementedError('method `setLabelText` must be implemented in inherited class')

    def updateLabelPos(self):
        """
        Update the label text position.
        """
        raise NotImplementedError('method `updateLabelPos` must be implemented in inherited class')

    ################################################## ACTION HANDLERS #################################################

    def handleNodeProperties(self):
        """
        Executed when node properties needs to be diplayed.
        """
        prop = NodePropertiesDialog(scene=self.scene, node=self.node)
        prop.exec_()


class AbstractResizableNodeShape(AbstractNodeShape):
    """
    This is the base class for all the resizable node shapes.
    """
    handleTL = 1
    handleTM = 2
    handleTR = 3
    handleML = 4
    handleMR = 5
    handleBL = 6
    handleBM = 7
    handleBR = 8

    handleSize = +8.0
    handleSpace = -4.0
    handleBrush = QColor(79, 195, 247, 255)
    handlePen = QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine)

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
        Initialize resizable shape attributes.
        """
        self.command = None
        self.handles = dict()
        self.handleSelected = None
        self.mousePressData = None
        self.mousePressPos = None
        self.mousePressRect = None
        super().__init__(**kwargs)

    ################################################### PROPERTIES #####################################################

    @property
    def resizable(self):
        """
        Tells whether the shape can be resized or not.
        :rtype: bool
        """
        return True

    ################################################# EVENT HANDLERS ###################################################

    def hoverMoveEvent(self, moveEvent):
        """
        Executed when the mouse moves over the shape (NOT PRESSED).
        :param moveEvent: the move event.
        """
        if self.isSelected():
            handle = self.handleAt(moveEvent.pos())
            self.setCursor(Qt.ArrowCursor if handle is None else self.handleCursors[handle])
        super().hoverMoveEvent(moveEvent)

    def hoverLeaveEvent(self, moveEvent):
        """
        Executed when the mouse leaves the shape (NOT PRESSED).
        :param moveEvent: the move event.
        """
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the item.
        :param mouseEvent: the mouse event instance.
        """
        self.handleSelected = self.handleAt(mouseEvent.pos())
        if self.handleSelected:
            scene = self.scene()
            scene.resizing = True
            scene.clearSelection()
            self.setSelected(True)
            self.mousePressPos = mouseEvent.pos()
            self.mousePressRect = deepcopy(self.boundingRect())
            self.mousePressData = {edge: pos for edge, pos in self.anchors.items()}

        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is being moved over the item while being pressed.
        :param mouseEvent: the mouse move event instance.
        """
        if self.handleSelected:
            
            if not self.command:
                self.command = CommandNodeRezize(self.node)
            self.interactiveResize(mouseEvent.pos())
            self.updateEdges()

        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the item.
        :param mouseEvent: the mouse event instance.
        """
        scene = self.scene()
        scene.resizing = False

        if self.handleSelected and self.command:
            self.command.end()
            scene.undoStack.push(self.command)

        super().mouseReleaseEvent(mouseEvent)

        self.command = None
        self.handleSelected = None
        self.mousePressData = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.updateEdges()
        self.update()

    ##################################################### GEOMETRY #####################################################

    def interactiveResize(self, mousePos):
        """
        Handle the interactive resize of the shape.
        :param mousePos: the current mouse position.
        """
        raise NotImplementedError('method `interactiveResize` must be implemented in inherited class')

    def painterPath(self):
        """
        Returns the current shape as QPainterPath (used for collision detection).
        :rtype: QPainterPath
        """
        raise NotImplementedError('method `painterPath` must be implemented in inherited class')

    ################################################ AUXILIARY METHODS #################################################

    def handleAt(self, point):
        """
        Returns the resize handle below the given point.
        Will return None if the mouse is not over a resizing handle.
        :type point: QPointF
        :param point: the point where to look for a resizing handle.
        :rtype: int
        """
        for k, v, in self.handles.items():
            if v.contains(point):
                return k
        return None

    def height(self):
        """
        Returns the height of the shape.
        :rtype: int
        """
        raise NotImplementedError('method `height` must be implemented in inherited class')
    
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

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        raise NotImplementedError('method `width` must be implemented in inherited class')

    ################################################# LABEL SHORTCUTS ##################################################

    def labelPos(self):
        """
        Returns the current label position.
        :rtype: QPointF
        """
        raise NotImplementedError('method `labelPos` must be implemented in inherited class')

    def labelText(self):
        """
        Returns the label text.
        :rtype: str
        """
        raise NotImplementedError('method `labelText` must be implemented in inherited class')

    def setLabelPos(self, pos):
        """
        Set the label position updating the 'moved' flag accordingly.
        :param pos: the node position.
        """
        raise NotImplementedError('method `setLabelPos` must be implemented in inherited class')

    def setLabelText(self, text):
        """
        Set the label text.
        :param text: the text value to set.
        """
        raise NotImplementedError('method `setLabelText` must be implemented in inherited class')

    def updateLabelPos(self):
        """
        Update the label text position.
        """
        raise NotImplementedError('method `updateLabelPos` must be implemented in inherited class')

    ################################################### ITEM DRAWING ###################################################

    def paintHandles(self, painter):
        """
        Paint node resizing handles.
        :param painter: the active painter.
        """
        if self.isSelected():
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(self.handleBrush)
            painter.setPen(self.handlePen)
            for handle, rect in self.handles.items():
                if self.handleSelected is None or handle == self.handleSelected:
                    painter.drawEllipse(rect)