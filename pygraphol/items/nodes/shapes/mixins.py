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
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QColor, QPen, QPolygonF
from PyQt5.QtWidgets import QGraphicsItem, QMenu


class ShapeMixin(QGraphicsItem):
    """
    This class holds properties which are shared by all the shapes (all shapes must inherit from this class).
    """

    shapeBrush = QColor(252, 252, 252)
    shapeSelectedBrush = QColor(251, 255, 148)
    shapePen = QPen(QColor(0, 0, 0), 1.0, Qt.SolidLine)

    def __init__(self, item, **kwargs):
        """
        Initialize basic shape attributes.
        :param item: the item this shape is attached to
        """
        self.item = item
        self.command = None
        self.label = None

        # some nodes do not enforce customizable geometry so we might have some
        # argument keywords left in that will mess up QGraphicsItem.__init__().
        kwargs.pop('id', None)
        kwargs.pop('width', None)
        kwargs.pop('height', None)

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

    ################################################# EVENT HANDLERS ###################################################

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
            if len(self.scene().selectedItems()) > 0:
                # some elements are already selected (previoust mouse press event)
                if not self.isSelected():
                    # there are some items selected but we clicked on a node
                    # which is not currently selected, so select only this one
                    scene = self.scene()
                    scene.clearSelection()
                    self.setSelected(True)
            else:
                # no node is selected and we just clicked on one so select it
                # since we filter out the Label, clear the scene selection
                # in any case to avoid strange bugs.
                scene = self.scene()
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

    ################################################ AUXILIARY METHODS #################################################

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
        menu.addAction(self.scene().actionItemDelete)
        menu.addSeparator()
        menu.addAction(self.scene().actionItemCut)
        menu.addAction(self.scene().actionItemCopy)
        menu.addAction(self.scene().actionItemPaste)
        menu.addSeparator()
        menu.addAction(self.scene().actionBringToFront)
        menu.addAction(self.scene().actionSendToBack)
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
        raise NotImplementedError('method `intersection` must be implemented in inherited class')

    def labelPos(self):
        """
        Returns the current label position (shortcut for self.label.pos()).
        :rtype: QPointF
        """
        return self.label.pos()

    def labelText(self):
        """
        Returns the label text (shortcut for self.label.text()).
        :rtype: str
        """
        return self.label.text()

    def setLabelPos(self, pos):
        """
        Set the label position updating the 'moved' flag accordingly.
        :param pos: the node position.
        """
        # sometime it happens that when the graphol document is saved on file, the saved label position differs
        # from the real position by 1px (usually only on height). This is due to the fact that by default the text
        # item bounding rect heigh is 13px and to compute the correct position of the text item we use to subtract
        # width / 2 and height / 2 from the text item center position which results in a .5 float automaticall rounded
        # by QT. To fix this issue we'll simply try to see if the difference between the given position and the default
        # one is 1px and set the label moved flag accordingly.
        moved_X = True
        moved_Y = True
        defaultPos = self.label.defaultPos()
        if abs(pos.x() - defaultPos.x()) <= 1:
            moved_X = False
            pos.setX(defaultPos.x())
        if abs(pos.y() - defaultPos.y()) <= 1:
            moved_Y = False
            pos.setY(defaultPos.y())
        self.label.setPos(pos)
        self.label.moved = moved_X or moved_Y

    def setLabelText(self, text):
        """
        Set the label text (shortcut for self.label.setText).
        :param text: the text value to set.
        """
        self.label.setText(text)

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

    def updateLabelPos(self):
        """
        Update the label text position (shortcut for self.label.updatePos).
        """
        self.label.updatePos()

    def width(self):
        """
        Returns the width of the shape.
        :rtype: int
        """
        raise NotImplementedError('method `width` must be implemented in inherited class')


class ShapeResizableMixin(ShapeMixin):
    """
    This class holds properties which are shared by resizable shapes.
    """
    handleSize = +8.0
    handleSpan = -4.0
    handleBrush = QColor(79, 195, 247, 255)
    handlePen = QPen(QColor(0, 0, 0, 255), 1.0, Qt.SolidLine)

    handleTL = 1
    handleTM = 2
    handleTR = 3
    handleML = 4
    handleMR = 5
    handleBL = 6
    handleBM = 7
    handleBR = 8

    cursors = {
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
        :param item: the item this shape is attached to
        """
        self.command = None
        self.handles = dict()
        self.mousePressPos = None
        self.mousePressRect = None
        self.selectedHandle = None
        super().__init__(**kwargs)

    ################################################# EVENT HANDLERS ###################################################

    def hoverMoveEvent(self, moveEvent):
        """
        Executed when the mouse moves over the shape (NOT PRESSED).
        :param moveEvent: the move event.
        """
        if self.isSelected():
            handle = self.getHandleAt(moveEvent.pos())
            self.setCursor(Qt.ArrowCursor if handle is None else self.cursors[handle])
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
        self.selectedHandle = self.getHandleAt(mouseEvent.pos())
        if self.selectedHandle:
            scene = self.scene()
            scene.resizing = True
            scene.clearSelection()
            self.setSelected(True)
            self.mousePressPos = mouseEvent.pos()
            self.mousePressRect = deepcopy(self.rect()) if hasattr(self, 'rect') else self.boundingRect()

        super().mousePressEvent(mouseEvent)

    # noinspection PyTypeChecker
    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is being moved over the item while being pressed.
        :param mouseEvent: the mouse move event instance.
        """
        if self.selectedHandle:
            if not self.command:
                self.command = CommandNodeRezize(self.node)
            self.interactiveResize(self.selectedHandle, self.mousePressRect, self.mousePressPos, mouseEvent.pos())
            self.updateEdges()

        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the item.
        :param mouseEvent: the mouse event instance.
        """
        if self.selectedHandle and self.command:
            # resizing operation: push the command in the stack
            self.command.new = deepcopy(self.rect()) if hasattr(self, 'rect') else QPolygonF(self.polygon())
            scene = self.scene()
            scene.resizing = False
            scene.undoStack.push(self.command)

        super().mouseReleaseEvent(mouseEvent)

        self.command = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.selectedHandle = None
        self.updateEdges()
        self.update()

    ################################################ AUXILIARY METHODS #################################################

    def getHandleAt(self, point):
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

    def interactiveResize(self, handle, fromRect, mousePressedPos, mousePos):
        """
        Handle the interactive resize of the shape.
        :type handle: int
        :type fromRect: QRectF
        :type mousePressedPos: QPointF
        :type mousePos: QPointF
        :param handle: the currently selected resizing handle.
        :param fromRect: the rect before the resizing operation started.
        :param mousePressedPos: the position where the mouse has been pressed.
        :param mousePos: the current mouse position.
        """
        raise NotImplementedError('method `interactiveResize` must be implemented in inherited class')

    def intersection(self, line):
        """
        Returns the intersection of the shape with the given line (in scene coordinates).
        :param line: the line whose intersection needs to be calculated (in scene coordinates).
        :rtype: QPointF
        """
        raise NotImplementedError('method `intersection` must be implemented in inherited class')

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