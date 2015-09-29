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


import os

from pygraphol import __appname__ as appname, __organization__ as organization
from pygraphol.commands import CommandItemsMultiAdd, CommandItemsMultiRemove
from pygraphol.commands import CommandNodeAdd, CommandNodeSetZValue, CommandNodeMove
from pygraphol.commands import CommandEdgeAdd
from pygraphol.functions import rangeF, snapPointToGrid
from pygraphol.datatypes import DistinctList
from pygraphol.items.nodes import Node
from pygraphol.items.edges import Edge
from pygraphol.items.nodes.shapes.common.label import Label as NodeLabel
from pygraphol.items.edges.shapes.common.label import Label as EdgeLabel
from pygraphol.tools import UniqueID

from PyQt5.QtCore import Qt, pyqtSignal, QPointF, pyqtSlot, QSettings
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QGraphicsScene, QUndoStack, QMenu
from PyQt5.QtXml import QDomDocument


class GraphicsScene(QGraphicsScene):
    """
    This class implements the main Graphics scene.
    """
    ## OPERATION MODE
    InsertNode = 1
    InsertEdge = 2
    MoveItem = 3

    ## CONTANTS
    GridPen = QPen(QColor(80, 80, 80), 0, Qt.SolidLine)
    GridSize = 20
    PasteOffsetX = 20
    PasteOffsetY = 10

    ## SIGNALS
    nodeInsertEnd = pyqtSignal(Node)
    edgeInsertEnd = pyqtSignal(Edge)
    modeChanged = pyqtSignal(int)

    ####################################################################################################################
    #                                                                                                                  #
    #   SCENE DOCUMENT                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    class Document(object):
        """
        This class is used to hold scene saved file data (filepath, filename etc).
        """
        def __init__(self):
            """
            Initialize the scene document.
            """
            self.filepath = None

        @property
        def name(self):
            """
            Returns the name of the saved file.
            :rtype: str
            """
            if not self.filepath:
                return 'Untitled'
            return os.path.basename(os.path.normpath(self.filepath))

    ####################################################################################################################
    #                                                                                                                  #
    #   SCENE IMPLEMENTATION                                                                                           #
    #                                                                                                                  #
    ####################################################################################################################

    def __init__(self, mainwindow, parent=None):
        """
        Initialize the graphic scene.
        :param mainwindow: the reference to the main window.
        :param parent: the parent widget.
        """
        super().__init__(parent)
        self.command = None  ## undo/redo command to be added in the stack
        self.clipboard = {}  ## used to store copy of scene nodes/edges
        self.clipboardPasteOffsetX = GraphicsScene.PasteOffsetX  ## X offset to be added to item position upon paste
        self.clipboardPasteOffsetY = GraphicsScene.PasteOffsetY  ## Y offset to be added to item position upon paste
        self.clipboardPasteOffsetZ = 0  ## > offset to be added to item zValue upon paste
        self.document = GraphicsScene.Document()  ## will contain the filepath of the graphol document
        self.itemList = DistinctList()  ## list of nodes (not shapes)
        self.settings = QSettings(organization, appname)  ## application settings
        self.uniqueID = UniqueID()  ## used to generate unique incrementsl ids
        self.undoStack = QUndoStack(self)  ## use to push actions and keep history for undo/redo
        self.undoStack.setUndoLimit(50)
        self.mode = self.MoveItem ## operation mode
        self.modeParam = None  ## extra parameter for the operation mode (see setMode())
        self.mousePressPos = None  ## scene position where the mouse has been pressed
        self.mousePressShape = None  ## shape acting as mouse grabber during mouse move events
        self.mousePressShapePos = None  ## position of the shape acting as mouse grabber during mouse move events
        self.mousePressData = {}  ## extra data needed to process item interactive movements
        self.mouseMoved = False  ## will be set to true whenever nodes will be moved using the mouse
        self.resizing = False  ## will be set to true when interactive resize is triggered

        ################################################# ACTIONS ######################################################

        self.actionItemCut = mainwindow.actionItemCut
        self.actionItemCopy = mainwindow.actionItemCopy
        self.actionItemPaste = mainwindow.actionItemPaste
        self.actionItemDelete = mainwindow.actionItemDelete
        self.actionBringToFront = mainwindow.actionBringToFront
        self.actionSendToBack = mainwindow.actionSendToBack
        self.actionSelectAll = mainwindow.actionSelectAll

        ################################################# SIGNALS ######################################################

        self.nodeInsertEnd.connect(self.handleNodeInsertEnd)
        self.edgeInsertEnd.connect(self.handleEdgeInsertEnd)
        self.selectionChanged.connect(self.handleSelectionChanged)

    ####################################################################################################################
    #                                                                                                                  #
    #   ACTION HANDLERS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    def handleItemCut(self):
        """
        Cut selected items from the scene.
        """
        self.setMode(GraphicsScene.MoveItem)
        self.updateClipboard()
        self.updateActions()

        selection = self.selectedItems()
        if selection:
            collection = [x.item for x in self.addHangingEdges(selection)]
            self.undoStack.push(CommandItemsMultiRemove(scene=self, collection=collection))

        # set the offset to 0 so we can paste in the same position
        self.clipboardPasteOffsetX = 0
        self.clipboardPasteOffsetY = 0
        self.clipboardPasteOffsetZ = 0

    def handleItemCopy(self):
        """
        Make a copy of selected items.
        """
        self.setMode(GraphicsScene.MoveItem)
        self.updateClipboard()
        self.updateActions()

    def handleItemPaste(self):
        """
        Paste previously copied items.
        """
        self.setMode(GraphicsScene.MoveItem)

        def ncopy(node):
            """
            Create a copy of the given node generating a new id.
            Will also adjust the node position according to the incremental offset.
            :param node: the node to copy.
            """
            copy = node.copy(self)
            copy.id = self.uniqueID.next(self.uniqueID.parse(node.id)[0])
            copy.shape.setPos(copy.shape.pos() + QPointF(self.clipboardPasteOffsetX, self.clipboardPasteOffsetY))
            copy.shape.setZValue(self.clipboardPasteOffsetZ + 0.1)
            return copy

        # create a copy of all the nodes in the clipboard and store them in a dict using the old
        # node id: this is needed later when we add edges since we need to attach the copied edge
        # to a new source/target so we need a mapping between the old id and the new id
        nodes = {x:ncopy(n) for x, n in self.clipboard['nodes'].items()}

        def ecopy(edge):
            """
            Create a copy of the given edge generating a new id and performing the following actions:
                - adjust edge breakpoints positions according to the incremental offset
                - attach the copied edge to the correspondend previously copied nodes
                - copy the edge reference into source and target nodes.
            :param edge: the edge to copy.
            """
            copy = edge.copy(self)

            # calculate the offset to be added to every position
            offset = QPointF(self.clipboardPasteOffsetX, self.clipboardPasteOffsetY)

            # generate a new id for this edge
            copy.id = self.uniqueID.next(self.uniqueID.parse(edge.id)[0])
            # attach the edge to the copy of source and target nodes
            copy.source = nodes[edge.source.id]
            copy.target = nodes[edge.target.id]
            # copy source and target anchor points moving them according to the offsets
            copy.source.shape.setAnchor(copy.shape, edge.source.shape.anchor(edge.shape) + offset)
            copy.target.shape.setAnchor(copy.shape, edge.target.shape.anchor(edge.shape) + offset)

            # copy breakpoints moving them according to the offsets
            copy.shape.breakpoints = [x + offset for x in copy.shape.breakpoints]

            # map the copied edge over source and target nodes
            nodes[edge.source.id].addEdge(copy)
            nodes[edge.target.id].addEdge(copy)

            # update the edge to generate internal stuff
            copy.shape.updateEdge()
            return copy

        # copy all the needed edges
        edges = {x:ecopy(e) for x, e in self.clipboard['edges'].items()}

        # push the command in the stack: note that python3 returns an object view when values() is called on a dict
        # and views are not joinable using the + operator (this is not thread safe it should be OK doing this w/o locks)
        self.undoStack.push(CommandItemsMultiAdd(scene=self, collection=list(nodes.values()) + list(edges.values())))

        # increase paste offsets for the next paste
        self.clipboardPasteOffsetX += GraphicsScene.PasteOffsetX
        self.clipboardPasteOffsetY += GraphicsScene.PasteOffsetY
        self.clipboardPasteOffsetZ += 0.1 * len(nodes)

    def handleItemDelete(self):
        """
        Delete the currently selected items from the graphic scene.
        """
        self.setMode(GraphicsScene.MoveItem)

        selection = self.selectedItems()
        if selection:
            collection = [x.item for x in self.addHangingEdges(selection)]
            self.undoStack.push(CommandItemsMultiRemove(scene=self, collection=collection))

    def handleBringToFront(self):
        """
        Bring the selected item to the top of the scene.
        """
        for selected in self.selectedNodes():
            zValue = 0
            colliding = selected.collidingItems()
            for item in filter(lambda x: not isinstance(x, NodeLabel) and not isinstance(x, EdgeLabel), colliding):
                if item.zValue() >= zValue:
                    zValue = item.zValue() + 0.1
            if zValue != selected.zValue():
                self.undoStack.push(CommandNodeSetZValue(scene=self, node=selected.node, zValue=zValue))

    def handleSendToBack(self):
        """
        Send the selected item to the back of the scene.
        """
        for selected in self.selectedNodes():
            zValue = 0
            colliding = selected.collidingItems()
            for item in filter(lambda x: not isinstance(x, NodeLabel) and not isinstance(x, EdgeLabel), colliding):
                if item.zValue() >= zValue:
                    zValue = item.zValue() - 0.1
            if zValue != selected.zValue():
                self.undoStack.push(CommandNodeSetZValue(scene=self, node=selected.node, zValue=zValue))

    def handleSelectAll(self):
        """
        Select all the items in the scene.
        """
        self.setMode(GraphicsScene.MoveItem)
        self.clearSelection()
        for item in self.nodes() + self.edges():
            item.shape.setSelected(True)

    ####################################################################################################################
    #                                                                                                                  #
    #   SIGNAL HANDLERS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot(Node)
    def handleNodeInsertEnd(self, node):
        """
        Triggered after a node insertion process ends.
        :param node: the inserted node.
        """
        self.setMode(GraphicsScene.MoveItem)

    @pyqtSlot(Edge)
    def handleEdgeInsertEnd(self, edge):
        """
        Triggered after a edge insertion process ends.
        :param edge: the inserted edge.
        """
        self.setMode(GraphicsScene.MoveItem)
        self.command = None

    @pyqtSlot()
    def handleSelectionChanged(self):
        """
        Executed when the scene selection changes.
        """
        self.updateActions()

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENT HANDLERS                                                                                                 #
    #                                                                                                                  #
    ####################################################################################################################

    def contextMenuEvent(self, menuEvent):
        """
        Bring up the context menu if necessary.
        :param menuEvent: the context menu event instance.
        """
        if not self.items(menuEvent.scenePos()):
            contextMenu = QMenu()
            contextMenu.addAction(self.actionSelectAll)
            if self.clipboard:
                contextMenu.addSeparator()
                contextMenu.addAction(self.actionItemPaste)
            contextMenu.exec_(menuEvent.screenPos())
        else:
            super().contextMenuEvent(menuEvent)

    def keyPressEvent(self, keyEvent):
        """
        Executed when a keyboard button is pressed on the scene.
        :param keyEvent: the keyboard event instance.
        """
        if keyEvent.key() in {Qt.Key_Delete, Qt.Key_Backspace}:
            # handle this here and not using a shortcut otherwise we won't be able
            # to delete elements on systems not having the CANC button on the keyboard
            self.handleItemDelete()
        super().keyPressEvent(keyEvent)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when a mouse button is clicked on the scene.
        :param mouseEvent: the mouse event instance.
        """
        if self.mode == GraphicsScene.InsertNode:

            # create a new node and place it under the mouse position
            func = self.modeParam
            node = func(scene=self)
            node.shape.setPos(self.snapToGrid(mouseEvent.scenePos()))

            # push the command in the undo stack so we can revert the action
            self.undoStack.push(CommandNodeAdd(scene=self, node=node))
            self.nodeInsertEnd.emit(node)

            super().mousePressEvent(mouseEvent)

        elif self.mode == GraphicsScene.InsertEdge:

            # see if we are pressing the mouse on a shape and if so set the edge add command
            shape = self.shapeOnTopOf(mouseEvent.scenePos(), edges=False)
            if shape:

                func = self.modeParam
                edge = func(scene=self, source=shape.item)
                edge.shape.updateEdge(target=mouseEvent.scenePos())

                # put the command on hold since we don't know if the edge will be truly inserted or the
                # insertion will be aborted (case when the user fails to release the edge arrow on top of a node)
                self.command = CommandEdgeAdd(scene=self, edge=edge)
                self.command.redo()

            super().mousePressEvent(mouseEvent)

        elif self.mode == GraphicsScene.MoveItem:

            # execute the mouse press event first: this is needed before we prepare data for the move event because
            # we may select another node (eventually using the control modifier) or init a shape interactive resize
            # that will clear the selection hence bypass the interactive move.
            super().mousePressEvent(mouseEvent)

            if not self.resizing and mouseEvent.buttons() & Qt.LeftButton:

                # prepare data for mouse move event
                self.mousePressShape = self.shapeOnTopOf(mouseEvent.scenePos(), edges=False)

                if self.mousePressShape:

                    # execute only if there is at least one item selected
                    self.mousePressShapePos = self.mousePressShape.pos()
                    self.mousePressPos = mouseEvent.scenePos()

                    # initialize data
                    self.mousePressData = {
                        'nodes': {
                            shape: {
                                'anchors': {k: v for k, v in shape.anchors.items()},
                                'pos': shape.pos(),
                            } for shape in self.selectedNodes()},
                        'edges': {}
                    }

                    # figure out if the nodes we are moving are sharing edges: if so, move the edge
                    # together with the nodes (which actually means moving the edge breakpoints)
                    for shape in self.mousePressData['nodes']:
                        for edge in shape.node.edges:
                            if edge.shape not in self.mousePressData['edges']:
                                if edge.other(shape.node).shape.isSelected():
                                    self.mousePressData['edges'][edge.shape] = edge.shape.breakpoints[:]

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when then mouse is moved on the scene.
        :param mouseEvent: the mouse event instance.
        """
        if self.mode == GraphicsScene.InsertEdge and self.command and self.command.edge:

            # update the edge position so that it will follow the mouse cursor
            self.command.edge.shape.updateEdge(target=mouseEvent.scenePos())

        elif self.mode == GraphicsScene.MoveItem:

            if not self.resizing and self.mousePressShape and mouseEvent.buttons() & Qt.LeftButton:

                # calculate the delta and adjust the value if the snap to grid feature is
                # enabled: we'll use the position of the shape acting as mouse grabber to
                # determine the new delta value and move other items accordingly
                snapped = self.snapToGrid(self.mousePressShapePos + mouseEvent.scenePos() - self.mousePressPos)
                delta = snapped - self.mousePressShapePos

                # update all the breakpoints positions
                for shape, breakpoints in self.mousePressData['edges'].items():
                    for i in range(len(breakpoints)):
                        shape.breakpoints[i] = breakpoints[i] + delta

                # move all the selected nodes
                for shape, data in self.mousePressData['nodes'].items():
                    # update node position and attached edges
                    shape.setPos(data['pos'] + delta)
                    # update anchors points
                    for edge, pos in data['anchors'].items():
                        shape.setAnchor(edge, pos + delta)
                    # update the edges connected to the shape
                    shape.updateEdges()

                # mark mouse move as happened so we can push
                # the undo command in the stack on mouse release
                self.mouseMoved = True

        # always call super for this event since it will also trigger hover events on shapes
        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the scene.
        :param mouseEvent: the mouse event instance.
        """
        if self.mode == GraphicsScene.InsertEdge and self.command and self.command.edge:

            # keep the edge only if it's overlapping a node in the scene
            shape = self.shapeOnTopOf(mouseEvent.scenePos(), edges=False)

            if shape:

                self.command.edge.target = shape.node
                self.command.edge.source.addEdge(self.command.edge)
                self.command.edge.target.addEdge(self.command.edge)
                self.command.edge.shape.updateEdge()

                # undo the command and push it on the stack
                # right after so redo will be executed
                self.command.undo()
                self.undoStack.push(self.command)

            else:

                # just undo the command without pushing it on the stack
                self.command.undo()

            self.edgeInsertEnd.emit(self.command.edge)
            self.clearSelection()

        elif self.mode == GraphicsScene.MoveItem:

            if self.mouseMoved:

                # collect new positions for the undo command
                data = {
                    'nodes': {
                        shape: {
                            'anchors': {k: v for k, v in shape.anchors.items()},
                            'pos': shape.pos(),
                        } for shape in self.mousePressData['nodes']},
                    'edges': {x: x.breakpoints[:] for x in self.mousePressData['edges']}
                }

                # push the command in the stack so we can revert the moving operation
                self.undoStack.push(CommandNodeMove(pos1=self.mousePressData, pos2=data))

            self.mousePressPos = None
            self.mousePressShape = None
            self.mousePressShapePos = None
            self.mousePressData = None
            self.mouseMoved = False

        super().mouseReleaseEvent(mouseEvent)

    ####################################################################################################################
    #                                                                                                                  #
    #   SCENE DRAWING                                                                                                  #
    #                                                                                                                  #
    ####################################################################################################################

    def drawBackground(self, painter, rect):
        """
        Draw the scene background.
        :param painter: the current active painter.
        :param rect: the exposed rectangle.
        """
        # do not draw the background grid if we are printing the scene
        if self.settings.value('scene/snap_to_grid', False, bool) and not isinstance(painter.device(), QPrinter):
            painter.setPen(GraphicsScene.GridPen)
            startX = int(rect.left()) - (int(rect.left()) % self.GridSize)
            startY = int(rect.top()) - (int(rect.top()) % self.GridSize)
            points = [QPointF(x, y) for x in rangeF(startX, rect.right(), self.GridSize) \
                                        for y in rangeF(startY, rect.bottom(), self.GridSize)]
            painter.drawPoints(*points)

    ####################################################################################################################
    #                                                                                                                  #
    #   SCENE EXPORT                                                                                                   #
    #                                                                                                                  #
    ####################################################################################################################

    def exportToGraphol(self):
        """
        Export the current node in Graphol format.
        :rtype: QDomDocument
        """
        document = QDomDocument()
        document.appendChild(document.createProcessingInstruction('xml', 'version="1.0" encoding="UTF-8" standalone="no"'))

        root = document.createElement('graphol')
        root.setAttribute('xmlns', 'http://www.dis.uniroma1.it/~graphol/schema')
        root.setAttribute('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.setAttribute('xmlns:data', 'http://www.dis.uniroma1.it/~graphol/schema/data')
        root.setAttribute('xmlns:line', 'http://www.dis.uniroma1.it/~graphol/schema/line')
        root.setAttribute('xmlns:shape', 'http://www.dis.uniroma1.it/~graphol/schema/shape')
        root.setAttribute('xsi:schemaLocation', 'http://www.dis.uniroma1.it/~graphol/schema '
                                                'http://www.dis.uniroma1.it/~graphol/schema/graphol.xsd')

        document.appendChild(root)

        graph = document.createElement('graph')
        graph.setAttribute('width', self.sceneRect().width())
        graph.setAttribute('height', self.sceneRect().height())

        for node in self.nodes():
            # append all the nodes to the graph element
            graph.appendChild(node.exportToGraphol(document))

        for edge in self.edges():
            # append all the edges to the graph element
            graph.appendChild(edge.exportToGraphol(document))

        # append the whole graph to the root
        root.appendChild(graph)

        return document

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    @staticmethod
    def addHangingEdges(collection):
        """
        Extend the given selection of items adding missing edges which are connected to the nodes in the selection.
        This is mostly used to add to the collections all the edges which will be hanging in the scene (being attached
        only to one node) after a items removal operation.
        :param collection: the collection of items to extend.
        :rtype: list
        """
        return collection + [edge.shape for shape in collection if shape.item.isNode() \
                                        for edge in shape.item.edges if edge.shape not in collection]

    def clear(self):
        """
        Clear the graphics scene by removing all the elements.
        """
        self.clipboard.clear()
        self.undoStack.clear()
        self.itemList.clear()
        super().clear()

    def edge(self, eid):
        """
        Returns a reference to the edge (not the shape) matching the given node id.
        :param eid: the edge id.
        :raise KeyError: if there is no such edge in our scene.
        """
        # iterating over the whole item list is not actually very performant but currently
        # this method is used only when we have to generate a GraphicsScene by loading a Graphol
        # document so it won't any real time performance impact once the document is loaded.
        for item in self.itemList:
            if item.isEdge() and item.id == eid:
                return item
        raise KeyError('no edge found with id <%s>' % eid)

    def edges(self):
        """
        Returns all the edges of the scene (not the shapes).
        :rtype: list
        """
        return [x for x in self.itemList if x.isEdge()]

    def node(self, nid):
        """
        Returns a reference to the node (not the shape) matching the given node id.
        :param nid: the node id.
        :raise KeyError: if there is no such node in our scene.
        """
        # iterating over the whole item list is not actually very performant but currently
        # this method is used only when we have to generate a GraphicsScene by loading a Graphol
        # document so it won't any real time performance impact once the document is loaded.
        for item in self.itemList:
            if item.isNode() and item.id == nid:
                return item
        raise KeyError('no node found with id <%s>' % nid)

    def nodes(self):
        """
        Returns all the nodes of the scene (not the shapes).
        :rtype: list
        """
        return [x for x in self.itemList if x.isNode()]

    def selectedEdges(self):
        """
        Returns the edge shapes selected in the scene.
        :rtype: list
        """
        return [x for x in self.selectedItems() if hasattr(x, 'item') and x.item.isEdge()]

    def selectedItems(self):
        """
        Returns the shapes selected in the scene (will filter out labels since we don't need them).
        :rtype: list
        """
        return [x for x in super().selectedItems() if hasattr(x, 'item') and \
                                                       not isinstance(x, NodeLabel) and \
                                                           not isinstance(x, EdgeLabel)]

    def selectedNodes(self):
        """
        Returns the node shapes selected in the scene.
        :rtype: list
        """
        return [x for x in self.selectedItems() if hasattr(x, 'item') and x.item.isNode()]

    def setMode(self, mode, param=None):
        """
        Set the operation mode.
        :param mode: the operation mode.
        :param param: the mode parameter (if any).
        """
        self.mode = mode
        self.modeParam = param
        self.modeChanged.emit(mode)

    def shapeOnTopOf(self, point, nodes=True, edges=True):
        """
        Returns the shape which is on top of the given point.
        :type point: QPointF
        :type nodes: bool
        :type edges: bool
        :param point: the graphic point of the scene from where to pick items.
        :param nodes: whether to include nodes in our search.
        :param edges: whether to include edges in our search.
        """
        collection = [x for x in self.items(point) if hasattr(x, 'item')]
        collection = [x for x in collection if nodes and x.item.isNode() or edges and x.item.isEdge()]
        return max(collection, key=lambda x: x.zValue()) if collection else None

    def snapToGrid(self, point):
        """
        Snap the shape position to the grid.
        :type point: QPointF
        :param point: the position of the shape.
        :return: the position of the shape snapped to the grid if the feature is enabled.
        :rtype: QPointF
        """
        if self.settings.value('scene/snap_to_grid', False, bool):
            newX = snapPointToGrid(point.x(), GraphicsScene.GridSize)
            newY = snapPointToGrid(point.y(), GraphicsScene.GridSize)
            return QPointF(newX, newY)
        else:
            return point

    def updateActions(self):
        """
        Update scene specific actions enabling/disabling them according to the scene state.
        """
        isNode = len(self.selectedNodes()) != 0
        isEdge = len(self.selectedEdges()) != 0
        isClip = len(self.clipboard) != 0 and len(self.clipboard['nodes']) != 0
        self.actionItemCut.setEnabled(isNode)
        self.actionItemCopy.setEnabled(isNode)
        self.actionItemPaste.setEnabled(isClip)
        self.actionBringToFront.setEnabled(isNode)
        self.actionSendToBack.setEnabled(isNode)
        self.actionItemDelete.setEnabled(isNode or isEdge)

    def updateClipboard(self):
        """
        Update the clipboard collecting nodes and edges which needs to be copied.
        """
        # reset paste offset for next paste
        self.clipboardPasteOffsetX = GraphicsScene.PasteOffsetX
        self.clipboardPasteOffsetY = GraphicsScene.PasteOffsetY
        self.clipboardPasteOffsetZ = 0

        self.clipboard = {
            'nodes': {},
            'edges': {},
        }

        # since we are creating a copy of the node (which doesn't carry all the edges with it)
        # we can't iterate over the copy 'edges': because of this we store the original selection
        # locally and we iterate over it matching nodes id to re-attach edge copies.
        nodes = self.selectedNodes()

        for shape in nodes:
            self.clipboard['nodes'][shape.node.id] = shape.node.copy(self)
            self.clipboardPasteOffsetZ = max(self.clipboardPasteOffsetZ, shape.zValue())

        # figure out if the nodes we are copying are sharing edges:
        # if that's the case, copy the edge together with the nodes
        for shape in nodes:
            for edge in shape.node.edges:
                if edge.id not in self.clipboard['edges']:
                    if edge.other(shape.node).shape.isSelected():
                        copy = edge.copy(self)
                        # attach source and target nodes
                        copy.source = self.clipboard['nodes'][edge.source.id]
                        copy.target = self.clipboard['nodes'][edge.target.id]
                        # copy source and target nodes anchor points
                        copy.source.shape.setAnchor(copy.shape, edge.source.shape.anchor(edge.shape))
                        copy.target.shape.setAnchor(copy.shape, edge.target.shape.anchor(edge.shape))
                        # add the copy of the edge to the collection
                        self.clipboard['edges'][edge.id] = copy
                        self.clipboardPasteOffsetZ = max(self.clipboardPasteOffsetZ, edge.shape.zValue())