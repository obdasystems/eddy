# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Grapholed: a diagramming software for the Graphol language.           #
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


from grapholed.commands import CommandNodeLabelMove, CommandNodeLabelEdit
from grapholed.datatypes import Font, DiagramMode
from grapholed.functions import isEmpty, distanceP, connect
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QColor, QTextCursor, QIcon, QPainterPath
from PyQt5.QtWidgets import QGraphicsTextItem, QGraphicsItem, QAction


class Label(QGraphicsTextItem):
    """
    This class implements the label to be attached to the graph nodes.
    """
    def __init__(self, default='', centered=True, movable=True, editable=True, parent=None):
        """
        Initialize the label.
        :param default: the text to be drawn when the shape is first created.
        :param centered: whether the text should be centered in the shape by default.
        :param movable: whether the text can be moved using the mouse.
        :param editable: whether the text can be edited by the user.
        :param parent: the parent node.
        """
        super().__init__(parent)

        self._defaultText = default
        self._centered = centered
        self._editable = editable
        self._movable = movable

        self.commandEdit = None
        self.commandMove = None

        self.setFlag(QGraphicsItem.ItemIsMovable, self.movable)
        self.setFlag(QGraphicsItem.ItemIsSelectable, self.movable)
        self.setFlag(QGraphicsItem.ItemIsFocusable, self.editable)
        self.setDefaultTextColor(QColor(0, 0, 0, 255))
        self.setFont(Font('Arial', 12, Font.Light))
        self.setText(self.defaultText)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setPos(self.defaultPos())

    ################################################## PROPERTIES ######################################################

    @property
    def centered(self):
        """
        Tells whether the label is centered in parent item by default.
        :rtype: bool
        """
        return self._centered

    @property
    def defaultText(self):
        """
        Returns the label default text.
        :rtype: str
        """
        return self._defaultText

    @property
    def editable(self):
        """
        Tells whether the label is movable
        :rtype: bool
        """
        return self._editable

    @property
    def movable(self):
        """
        Tells whether the label is movable
        :rtype: bool
        """
        return self._movable

    @property
    def moved(self):
        """
        Tells whether the label has been moved from its default position.
        :return: bool
        """
        return distanceP(self.pos(), self.defaultPos()) > 1.41421356237 # sqrt(2) => max distance in 1px

    ################################################ ITEM INTERFACE ####################################################

    def center(self):
        """
        Returns the point at the center of the label in item coordinates.
        :rtype: QPointF
        """
        return self.boundingRect().center()

    def contextMenuAdd(self):
        """
        Returns a list of actions for the item shape context menu.
        :rtype: list
        """
        collection = []
        if self.movable and self.moved:
            parent = self.parentItem()
            action = QAction('Reset text position', parent.scene())
            action.setIcon(QIcon(':/icons/refresh'))
            connect(action.triggered, self.doResetTextPosition)
            collection.append(action)
        return collection

    def defaultPos(self):
        """
        Returns the label default position in parent's item coordinates.
        :rtype: QPointF
        """
        parent = self.parentItem()
        pos = parent.center()
        if not self.centered:
            pos.setY(pos.y() - parent.height() / 2 - 12)
        return pos

    def height(self):
        """
        Returns the height of the text label.
        :rtype: int
        """
        return self.boundingRect().height()

    def pos(self):
        """
        Returns the position of the label in parent's item coordinates.
        :rtype: QPointF
        """
        return self.mapToParent(self.center())

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
            raise TypeError('too many arguments; expected {0}, got {1}'.format(2, len(__args)))
        super().setPos(pos - QPointF(self.width() / 2, self.height() / 2))

    def setText(self, text):
        """
        Set the given text as plain text.
        :param text: the text value to set.
        """
        moved = self.moved
        self.setPlainText(text)
        self.updatePos(moved)

    def text(self):
        """
        Returns the current shape text (shortcut for self.toPlainText()).
        :return: str
        """
        return self.toPlainText()

    def updatePos(self, moved=False):
        """
        Update the current text position with respect to the shape.
        :param moved: the moved status of the label.
        """
        if not moved:
            self.setPos(self.defaultPos())

    def width(self):
        """
        Returns the width of the text label.
        :rtype: int
        """
        return self.boundingRect().width()

    ################################################## EVENT HANDLERS ##################################################

    def focusInEvent(self, focusEvent):
        """
        Executed when the text item is focused.
        :param focusEvent: the focus event instance.
        """
        scene = self.scene()
        scene.setMode(DiagramMode.LabelEdit)
        parent = self.parentItem()
        cursor = self.textCursor()
        cursor.select(QTextCursor.BlockUnderCursor)
        self.setTextCursor(cursor)
        self.commandEdit = self.commandEdit or CommandNodeLabelEdit(scene, parent, self, self.text())
        scene.clearSelection()
        self.setSelected(True)
        super().focusInEvent(focusEvent)

    def focusOutEvent(self, focusEvent):
        """
        Executed when the text item lose the focus.
        :param focusEvent: the focus event instance.
        """
        scene = self.scene()

        if scene.mode is DiagramMode.LabelEdit:
            # make sure we have something in the label
            if isEmpty(self.text()):
                self.setText(self.defaultText)

            # push the edit command in the stack only if the label actually changed
            if self.commandEdit.isTextChanged(self.text()):
                self.commandEdit.end(self.text())
                scene.undoStack.push(self.commandEdit)

            cursor = self.textCursor()
            cursor.clearSelection()
            self.commandEdit = None
            self.setTextCursor(cursor)
            self.setTextInteractionFlags(Qt.NoTextInteraction)

            # go back idle so we can perform another operation
            scene.setMode(DiagramMode.Idle)

        super().focusOutEvent(focusEvent)

    def hoverMoveEvent(self, moveEvent):
        """
        Executed when the mouse move over the text area (NOT PRESSED).
        :param moveEvent: the move event instance.
        """
        if self.editable and self.hasFocus():
            self.setCursor(Qt.IBeamCursor)
            super().hoverMoveEvent(moveEvent)

    def hoverLeaveEvent(self, moveEvent):
        """
        Executed when the mouse leaves the text area (NOT PRESSED).
        :param moveEvent: the move event instance.
        """
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)

    def keyPressEvent(self, keyEvent):
        """
        Executed when a key is pressed.
        :param keyEvent: the key press event.
        """
        moved = self.moved
        if keyEvent.key() in {Qt.Key_Enter, Qt.Key_Return}:
            # enter has been pressed: allow insertion of a newline
            # character only if the shift modifier is being held
            if keyEvent.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(keyEvent)
            else:
                self.setSelected(False)
                self.clearFocus()
        else:
            # normal key press so allow insertion
            super().keyPressEvent(keyEvent)
        self.updatePos(moved)

    def mouseDoubleClickEvent(self, mouseEvent):
        """
        Executed when the mouse is double clicked on the text item.
        :param mouseEvent: the mouse event instance.
        """
        if self.editable:
            super().mouseDoubleClickEvent(mouseEvent)
            self.setTextInteractionFlags(Qt.TextEditorInteraction)
            self.setFocus()

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the text item.
        :param mouseEvent: the mouse event instance.
        """
        scene = self.scene()

        if scene.mode is DiagramMode.Idle:

            if mouseEvent.modifiers() & Qt.ControlModifier:
                # allow the moving of the label if the CTRL modifier is being held
                scene.clearSelection()
                scene.setMode(DiagramMode.LabelMove)
                self.setSelected(True)
                super().mousePressEvent(mouseEvent)
            else:
                # see if the mouse is hovering the parent item: if so select
                # it so that mouseMoveEvent method in DiagramScene can move it
                parent = self.parentItem()
                if parent in scene.items(mouseEvent.scenePos()):
                    scene.clearSelection()
                    parent.setSelected(True)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the text is moved with the mouse.
        :param mouseEvent: the mouse event instance.
        """
        scene = self.scene()
        if scene.mode is DiagramMode.LabelMove:
            super().mouseMoveEvent(mouseEvent)
            self.commandMove = self.commandMove or CommandNodeLabelMove(scene=scene, node=self.parentItem(), label=self)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the label.
        :param mouseEvent: the mouse event instance.
        """
        scene = self.scene()
        super().mouseReleaseEvent(mouseEvent)

        if scene.mode is DiagramMode.LabelMove:
            if self.commandMove:
                self.commandMove.end(pos=self.pos())
                scene.undoStack.push(self.commandMove)
                self.commandMove = None

    #################################################### GEOMETRY ######################################################

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    ################################################# ACTION HANDLERS ##################################################

    def doResetTextPosition(self):
        """
        Reset the text position to the default value.
        """
        if self.movable:
            scene = self.scene()
            command = CommandNodeLabelMove(scene=scene, node=self.parentItem(), label=self)
            command.end(pos=self.defaultPos())
            scene.undoStack.push(command)
            self.updatePos()