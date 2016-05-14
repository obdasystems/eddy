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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QColor, QTextCursor, QPainterPath

from eddy.core.commands.nodes import CommandNodeLabelChange
from eddy.core.commands.nodes import CommandNodeLabelMove
from eddy.core.datatypes.misc import DiagramMode
from eddy.core.functions.misc import isEmpty
from eddy.core.items.common import AbstractLabel
from eddy.core.qt import Font


class NodeLabel(AbstractLabel):
    """
    This class implements the label to be attached to the graphol nodes.
    """
    def __init__(self, template='', pos=None, movable=True, editable=True, parent=None):
        """
        Initialize the label.
        :type template: str
        :type pos: callable
        :type movable: bool
        :type editable: bool
        :type parent: QObject
        """
        super().__init__(parent)

        defaultPos = lambda: QPointF(0, 0)
        self.defaultPos = pos or defaultPos
        self.editable = bool(editable)
        self.movable = bool(movable)
        self.template = template

        self.focusInData = None
        self.mousePressPos = None

        self.setDefaultTextColor(QColor(0, 0, 0, 255))
        self.setFlag(AbstractLabel.ItemIsMovable, self.movable)
        self.setFlag(AbstractLabel.ItemIsFocusable, self.editable)
        self.setFont(Font('Arial', 12, Font.Light))
        self.setText(self.template)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.setPos(self.defaultPos())
        self.updatePos()

    #############################################
    #   INTERFACE
    #################################

    def center(self):
        """
        Returns the point at the center of the label in item coordinates.
        :rtype: QPointF
        """
        return self.boundingRect().center()

    def height(self):
        """
        Returns the height of the text label.
        :rtype: int
        """
        return self.boundingRect().height()

    def isEditable(self):
        """
        Returns True if the label is editable, else False.
        :rtype: bool
        """
        return self.editable

    def isMovable(self):
        """
        Returns True if the label is movable, else False.
        :rtype: bool
        """
        return self.movable

    def isMoved(self):
        """
        Returns True if the label has been moved from its default location, else False.
        :return: bool
        """
        return (self.pos() - self.defaultPos()).manhattanLength() >= 1

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
            raise TypeError('too many arguments; expected {}, got {}'.format(2, len(__args)))
        super().setPos(pos - QPointF(self.width() / 2, self.height() / 2))

    def setEditable(self, editable):
        """
        Set the editable status of the label.
        :type editable: bool.
        """
        self.editable = bool(editable)
        self.setFlag(AbstractLabel.ItemIsFocusable, self.editable)

    def setMovable(self, movable):
        """
        Set the movable status of the Label.
        :type movable: bool.
        """
        self.movable = bool(movable)
        self.setFlag(AbstractLabel.ItemIsMovable, self.movable)

    def setText(self, text):
        """
        Set the given text as plain text.
        :type text: str.
        """
        moved = self.isMoved()
        self.setPlainText(text)
        self.updatePos(moved)

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        :rtype: QPainterPath
        """
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def text(self):
        """
        Returns the text of the label.
        :rtype: str
        """
        return self.toPlainText().strip()

    def updatePos(self, moved=False):
        """
        Update the current text position with respect to its parent node.
        :type moved: bool.
        """
        if not moved:
            self.setPos(self.defaultPos())

    def width(self):
        """
        Returns the width of the text label.
        :rtype: int
        """
        return self.boundingRect().width()

    #############################################
    #   EVENTS
    #################################

    def focusInEvent(self, focusEvent):
        """
        Executed when the text item is focused.
        :type focusEvent: QFocusEvent
        """
        # Make the label focusable only by performing a double click on the
        # text: this will exclude any other type of focus action (dunno why
        # but sometime the label gets the focus when hovering the mouse cursor
        # on the text: mostly happens when loading a diagram from file)
        if focusEvent.reason() == Qt.OtherFocusReason:
            self.diagram.setMode(DiagramMode.EditText)
            cursor = self.textCursor()
            cursor.select(QTextCursor.BlockUnderCursor)
            self.setTextCursor(cursor)
            self.focusInData = self.text()
            self.diagram.clearSelection()
            super().focusInEvent(focusEvent)
        else:
            self.clearFocus()

    def focusOutEvent(self, focusEvent):
        """
        Executed when the text item lose the focus.
        :type focusEvent: QFocusEvent
        """
        if self.diagram.mode is DiagramMode.EditText:

            if isEmpty(self.text()):
                self.setText(self.template)

            focusInData = self.focusInData
            currentData = self.text()

            # The code below is a bit tricky: to be able to properly
            # update the node in the project index we need to force
            # the value of the label to it's previous one and let the
            # command implementation update the index.
            self.setText(focusInData)

            if focusInData and focusInData != currentData:
                command = CommandNodeLabelChange(self.diagram, self.parentItem(), focusInData, currentData)
                self.diagram.undoStack.push(command)

            cursor = self.textCursor()
            cursor.clearSelection()
            self.focusInData = None
            self.setTextCursor(cursor)
            self.setTextInteractionFlags(Qt.NoTextInteraction)
            self.diagram.setMode(DiagramMode.Idle)
            self.diagram.sgnUpdated.emit()

        super().focusOutEvent(focusEvent)

    def hoverMoveEvent(self, moveEvent):
        """
        Executed when the mouse move over the text area (NOT PRESSED).
        :type moveEvent: QGraphicsSceneHoverEvent
        """
        if self.isEditable() and self.hasFocus():
            self.setCursor(Qt.IBeamCursor)
            super().hoverMoveEvent(moveEvent)

    def hoverLeaveEvent(self, moveEvent):
        """
        Executed when the mouse leaves the text area (NOT PRESSED).
        :type moveEvent: QGraphicsSceneHoverEvent
        """
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)

    def keyPressEvent(self, keyEvent):
        """
        Executed when a key is pressed.
        :type keyEvent: QKeyEvent
        """
        moved = self.isMoved()
        if keyEvent.key() in {Qt.Key_Enter, Qt.Key_Return}:
            # Enter has been pressed: allow insertion of a newline
            # character only if the shift modifier is being held.
            if keyEvent.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(keyEvent)
            else:
                self.clearFocus()
        else:
            # Normal key press => allow insertion.
            super().keyPressEvent(keyEvent)
        self.updatePos(moved)

    def mouseDoubleClickEvent(self, mouseEvent):
        """
        Executed when the mouse is double clicked on the text item.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if self.isEditable():
            super().mouseDoubleClickEvent(mouseEvent)
            self.setTextInteractionFlags(Qt.TextEditorInteraction)
            self.setFocus()

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the text item.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if self.diagram.mode is DiagramMode.Idle:

            if mouseEvent.modifiers() & Qt.ControlModifier:
                # Allow the moving of the label if the CTRL modifier is being held.
                self.diagram.clearSelection()
                self.diagram.setMode(DiagramMode.MoveText)
                self.mousePressPos = self.pos()
                super().mousePressEvent(mouseEvent)
            else:
                # See if the mouse is hovering the parent item: if so see if the
                # item is not selected and in case select it so the mouseMoveEvent
                # in the Diagram class can perform the node movement.
                parent = self.parentItem()
                if parent in self.diagram.items(mouseEvent.scenePos()):
                    if not parent.isSelected():
                        self.diagram.clearSelection()
                        parent.setSelected(True)

        elif self.diagram.mode is DiagramMode.EditText:

            # Call super method in this case so we can move the mouse
            # ibeam cursor within the label while being in EDIT mode.
            super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the text is moved with the mouse.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the label.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        super().mouseReleaseEvent(mouseEvent)

        if self.diagram.mode is DiagramMode.MoveText:
            if self.mousePressPos is not None:
                pos = self.pos()
                if self.mousePressPos != pos:
                    node = self.parentItem()
                    command = CommandNodeLabelMove(self.diagram, node, self.mousePressPos, pos)
                    self.diagram.undoStack.push(command)
                    self.diagram.setMode(DiagramMode.Idle)

        self.mousePressPos = None


class FacetNodeQuotedLabel(NodeLabel):
    """
    This class implements the quoted label of Facet nodes.
    """
    def __init__(self, **kwargs):
        """
        Initialize the label.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self.focusInFacet = None

    #############################################
    #   EVENTS
    #################################

    def focusInEvent(self, focusEvent):
        """
        Executed when the text item is focused.
        :type focusEvent: QFocusEvent
        """
        # Make the label focusable only by performing a double click on the
        # text: this will exclude any other type of focus action (dunno why
        # but sometime the label gets the focus when hovering the mouse cursor
        # on the text: mostly happens when loading a diagram from file)
        if focusEvent.reason() == Qt.OtherFocusReason:
            item = self.parentItem()
            self.diagram.setMode(DiagramMode.EditText)
            self.diagram.clearSelection()
            self.focusInData = self.text()
            self.focusInFacet = item.facet
            self.setText(self.text().strip('"'))
            cursor = self.textCursor()
            cursor.select(QTextCursor.BlockUnderCursor)
            self.setTextCursor(cursor)
            super(NodeLabel, self).focusInEvent(focusEvent)
        else:
            self.clearFocus()

    def focusOutEvent(self, focusEvent):
        """
        Executed when the text item lose the focus.
        :type focusEvent: QFocusEvent
        """
        if self.diagram.mode is DiagramMode.EditText:

            if isEmpty(self.text()):
                self.setText(self.template)

            focusInData = self.focusInData
            currentData = '"{0}"'.format(self.text().strip('"'))

            # The code below is a bit tricky: to be able to properly
            # update the node in the project index we need to force
            # the value of the label to it's previous one and let the
            # command implementation update the index.
            self.setText(focusInData)

            if focusInData and focusInData != currentData:
                item = self.parentItem()
                data1 = item.compose(self.focusInFacet, focusInData)
                data2 = item.compose(self.focusInFacet, currentData)
                command = CommandNodeLabelChange(self.diagram, self.parentItem(), data1, data2)
                self.diagram.undoStack.push(command)

            cursor = self.textCursor()
            cursor.clearSelection()
            self.focusInData = None
            self.focusInFacet = None
            self.setTextCursor(cursor)
            self.setTextInteractionFlags(Qt.NoTextInteraction)
            self.diagram.setMode(DiagramMode.Idle)
            self.diagram.sgnUpdated.emit()

        super(NodeLabel, self).focusOutEvent(focusEvent)
