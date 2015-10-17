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


import os

from PyQt5.QtCore import Qt, pyqtSignal, QPointF, pyqtSlot, QSettings
from PyQt5.QtGui import QPen, QColor, QIcon
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QGraphicsScene, QUndoStack, QMenu
from PyQt5.QtXml import QDomDocument

from grapholed import __appname__ as appname, __organization__ as organization
from grapholed.commands import CommandItemsMultiAdd, CommandItemsMultiRemove
from grapholed.commands import CommandNodeAdd, CommandNodeSetZValue, CommandNodeMove
from grapholed.commands import CommandEdgeAdd
from grapholed.dialogs.properties import ScenePropertiesDialog
from grapholed.functions import snapToGrid, rangeF
from grapholed.items import Item
from grapholed.tools import UniqueID


class DiagramScene(QGraphicsScene):
    """
    This class implements the main Diagram Scene.
    """
    ## OPERATION MODE
    MoveItem = 1
    InsertNode = 2
    InsertEdge = 3

    ## CONSTANTS
    GridPen = QPen(QColor(80, 80, 80), 0, Qt.SolidLine)
    GridSize = 20
    MinSize = 2000
    MaxSize = 1000000
    PasteOffsetX = 20
    PasteOffsetY = 10

    ## SIGNALS
    nodeInsertEnd = pyqtSignal('QGraphicsItem', int)  # emitted when a node is inserted in the scene
    edgeInsertEnd = pyqtSignal('QGraphicsItem', int)  # emitted when a edge is inserted in the scene
    modeChanged = pyqtSignal(int)  # emitted when the operational mode changes
    updated = pyqtSignal()  # emitted when the scene is updated

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
            self._filepath = ''
            self._edited = None

        @property
        def edited(self):
            """
            Returns the timestamp when the file has been last modified.
            :return: float
            """
            return self._edited

        @edited.setter
        def edited(self, value):
            """
            Set the timestamp when the file has been last modified
            :param value: the timestamp value
            """
            self._edited = float(value)

        @property
        def filepath(self):
            """
            Returns the filepath of the document.
            :return: str
            """
            return self._filepath

        @filepath.setter
        def filepath(self, value):
            """
            Set the filepath of the document.
            :param value: the filepath of the document.
            """
            self._filepath = value

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
        self.clipboardPasteOffsetX = DiagramScene.PasteOffsetX  ## X offset to be added to item position upon paste
        self.clipboardPasteOffsetY = DiagramScene.PasteOffsetY  ## Y offset to be added to item position upon paste
        self.clipboardPasteOffsetZ = 0  ## > offset to be added to item zValue upon paste
        self.document = DiagramScene.Document()  ## will contain the filepath of the graphol document
        self.settings = QSettings(organization, appname)  ## application settings
        self.uniqueID = UniqueID()  ## used to generate unique incrementsl ids
        self.undoStack = QUndoStack(self)  ## use to push actions and keep history for undo/redo
        self.undoStack.setUndoLimit(50) ## TODO: make the stack configurable
        self.mode = self.MoveItem ## operation mode
        self.modeParam = None  ## extra parameter for the operation mode (see setMode())
        self.mousePressPos = None  ## scene position where the mouse has been pressed
        self.mousePressNode = None  ## node acting as mouse grabber during mouse move events
        self.mousePressNodePos = None  ## position of the shape acting as mouse grabber during mouse move events
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

    @pyqtSlot()
    def handleItemCut(self):
        """
        Cut selected items from the scene.
        """
        self.setMode(DiagramScene.MoveItem)
        self.updateClipboard()
        self.updateActions()

        selection = self.selectedItems()
        if selection:
            # extend the selection adding hanging edges
            selection.extend([x for item in selection if item.isNode() for x in item.edges if x not in selection])
            self.undoStack.push(CommandItemsMultiRemove(scene=self, collection=selection))

        # set the offset to 0 so we can paste in the same position
        self.clipboardPasteOffsetX = 0
        self.clipboardPasteOffsetY = 0
        self.clipboardPasteOffsetZ = 0

    @pyqtSlot()
    def handleItemCopy(self):
        """
        Make a copy of selected items.
        """
        self.setMode(DiagramScene.MoveItem)
        self.updateClipboard()
        self.updateActions()

    @pyqtSlot()
    def handleItemPaste(self):
        """
        Paste previously copied items.
        """
        self.setMode(DiagramScene.MoveItem)

        def ncopy(node):
            """
            Create a copy of the given node generating a new id.
            Will also adjust the node position according to the incremental offset.
            :param node: the node to copy.
            """
            copy = node.copy(self)
            copy.id = self.uniqueID.next(self.uniqueID.parse(node.id)[0])
            copy.setPos(copy.pos() + QPointF(self.clipboardPasteOffsetX, self.clipboardPasteOffsetY))
            copy.setZValue(self.clipboardPasteOffsetZ + 0.1)
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
            copy.source.setAnchor(copy, edge.source.anchor(edge) + offset)
            copy.target.setAnchor(copy, edge.target.anchor(edge) + offset)

            # copy breakpoints moving them according to the offsets
            copy.breakpoints = [x + offset for x in copy.breakpoints]

            # map the copied edge over source and target nodes
            nodes[edge.source.id].addEdge(copy)
            nodes[edge.target.id].addEdge(copy)

            # update the edge to generate internal stuff
            copy.updateEdge()
            return copy

        # copy all the needed edges
        edges = {x:ecopy(e) for x, e in self.clipboard['edges'].items()}

        # push the command in the stack
        self.undoStack.push(CommandItemsMultiAdd(scene=self, collection=list(nodes.values()) + list(edges.values())))

        # increase paste offsets for the next paste
        self.clipboardPasteOffsetX += DiagramScene.PasteOffsetX
        self.clipboardPasteOffsetY += DiagramScene.PasteOffsetY
        self.clipboardPasteOffsetZ += 0.1 * len(nodes)

    @pyqtSlot()
    def handleItemDelete(self):
        """
        Delete the currently selected items from the graphic scene.
        """
        self.setMode(DiagramScene.MoveItem)

        selection = self.selectedItems()
        if selection:
            # extend the selection adding hanging edges
            selection.extend([x for item in selection if item.isNode() for x in item.edges if x not in selection])
            self.undoStack.push(CommandItemsMultiRemove(scene=self, collection=selection))

    @pyqtSlot()
    def handleBringToFront(self):
        """
        Bring the selected item to the top of the scene.
        """
        for selected in self.selectedNodes():
            zValue = 0
            colliding = selected.collidingItems()
            for item in filter(lambda x: isinstance(x, Item), colliding):
                if item.zValue() >= zValue:
                    zValue = item.zValue() + 0.1
            if zValue != selected.zValue():
                self.undoStack.push(CommandNodeSetZValue(scene=self, node=selected, zValue=zValue))

    @pyqtSlot()
    def handleSendToBack(self):
        """
        Send the selected item to the back of the scene.
        """
        for selected in self.selectedNodes():
            zValue = 0
            colliding = selected.collidingItems()
            for item in filter(lambda x: isinstance(x, Item), colliding):
                if item.zValue() >= zValue:
                    zValue = item.zValue() - 0.1
            if zValue != selected.zValue():
                self.undoStack.push(CommandNodeSetZValue(scene=self, node=selected, zValue=zValue))

    @pyqtSlot()
    def handleSelectAll(self):
        """
        Select all the items in the scene.
        """
        self.setMode(DiagramScene.MoveItem)
        self.clearSelection()
        for item in self.nodes() + self.edges():
            item.setSelected(True)

    @pyqtSlot()
    def handleSceneProperties(self):
        """
        Executed when scene properties needs to be diplayed.
        """
        prop = ScenePropertiesDialog(scene=self)
        prop.exec_()

    ####################################################################################################################
    #                                                                                                                  #
    #   SIGNAL HANDLERS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot('QGraphicsItem', int)
    def handleEdgeInsertEnd(self, edge, modifiers):
        """
        Triggered after a edge insertion process ends.
        :param edge: the inserted edge.
        :param modifiers: keyboard modifiers held during edge insertion.
        """
        self.command = None
        if not modifiers & Qt.ControlModifier:
            # set back default mode if CTRL is not being held
            self.setMode(DiagramScene.MoveItem)

    @pyqtSlot('QGraphicsItem', int)
    def handleNodeInsertEnd(self, node, modifiers):
        """
        Triggered after a node insertion process ends.
        :param node: the inserted node.
        :param modifiers: keyboard modifiers held during node insertion.
        """
        if not modifiers & Qt.ControlModifier:
            # set back default mode if CTRL is not being held
            self.setMode(DiagramScene.MoveItem)

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

            menu = QMenu()
            if self.clipboard:
                menu.addAction(self.actionItemPaste)
                menu.addSeparator()

            menu.addAction(self.actionSelectAll)
            menu.addSeparator()

            prop = menu.addAction(QIcon(':/icons/preferences'), 'Properties...')
            prop.triggered.connect(self.handleSceneProperties)

            menu.exec_(menuEvent.screenPos())
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
        if mouseEvent.buttons() & Qt.LeftButton:

            if self.mode == DiagramScene.InsertNode:

                ############################################ NODE INSERTION ############################################

                # create a new node and place it under the mouse position
                func = self.modeParam
                node = func(scene=self)
                node.setPos(self.snapToGrid(mouseEvent.scenePos()))

                # push the command in the undo stack so we can revert the action
                self.undoStack.push(CommandNodeAdd(scene=self, node=node))
                self.nodeInsertEnd.emit(node, mouseEvent.modifiers())

                super().mousePressEvent(mouseEvent)

            elif self.mode == DiagramScene.InsertEdge:

                ############################################ EDGE INSERTION ############################################

                # see if we are pressing the mouse on a node and if so set the edge add command
                node = self.itemOnTopOf(mouseEvent.scenePos(), edges=False)
                if node:

                    func = self.modeParam
                    edge = func(scene=self, source=node)
                    edge.updateEdge(target=mouseEvent.scenePos())

                    # put the command on hold since we don't know if the edge will be truly inserted or the
                    # insertion will be aborted (case when the user fails to release the edge arrow on top of a node)
                    self.command = CommandEdgeAdd(scene=self, edge=edge)

                    # add the edge to the scene
                    self.addItem(self.command.edge)

                super().mousePressEvent(mouseEvent)

            elif self.mode == DiagramScene.MoveItem:

                ############################################ ITEM MOVEMENT #############################################

                # execute the mouse press event first: this is needed before we prepare data for the move event because
                # we may select another node (eventually using the control modifier) or init a shape interactive resize
                # that will clear the selection hence bypass the interactive move.
                super().mousePressEvent(mouseEvent)

                if not self.resizing:

                    # see if we have some nodes selected in the scene: this is needed because itemOnTopOf
                    # will discard labels, so if we have a node whose label is overlapping the node shape,
                    # clicking on the label will make itemOnTopOf return the node item instad of the label itself.
                    selected = self.selectedNodes()

                    if selected:

                        # we have some nodes selected in the scene so we probably are going to do a
                        # move operation, prepare data for mouse move event => selecta node that will act
                        # as mouse grabber to compute delta movements for each componened in the selection
                        self.mousePressNode = self.itemOnTopOf(mouseEvent.scenePos(), edges=False)

                        if self.mousePressNode:

                            self.mousePressNodePos = self.mousePressNode.pos()
                            self.mousePressPos = mouseEvent.scenePos()

                            # initialize data
                            self.mousePressData = {
                                'nodes': {
                                    node: {
                                        'anchors': {k: v for k, v in node.anchors.items()},
                                        'pos': node.pos(),
                                    } for node in selected},
                                'edges': {}
                            }

                            # figure out if the nodes we are moving are sharing edges: if so, move the edge
                            # together with the nodes (which actually means moving the edge breakpoints)
                            for node in self.mousePressData['nodes']:
                                for edge in node.edges:
                                    if edge not in self.mousePressData['edges']:
                                        if edge.other(node).isSelected():
                                            self.mousePressData['edges'][edge] = edge.breakpoints[:]

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when then mouse is moved on the scene.
        :param mouseEvent: the mouse event instance.
        """
        if mouseEvent.buttons() & Qt.LeftButton:

            if self.mode == DiagramScene.InsertEdge and self.command and self.command.edge:

                ############################################ NODE INSERTION ############################################

                # update the edge position so that it will follow the mouse cursor
                self.command.edge.updateEdge(target=mouseEvent.scenePos())

            elif self.mode == DiagramScene.MoveItem:

                ############################################ ITEM MOVEMENT #############################################

                if not self.resizing and self.mousePressNode:

                    # calculate the delta and adjust the value if the snap to grid feature is
                    # enabled: we'll use the position of the node acting as mouse grabber to
                    # determine the new delta value and move other items accordingly
                    snapped = self.snapToGrid(self.mousePressNodePos + mouseEvent.scenePos() - self.mousePressPos)
                    delta = snapped - self.mousePressNodePos

                    # update all the breakpoints positions
                    for edge, breakpoints in self.mousePressData['edges'].items():
                        for i in range(len(breakpoints)):
                            edge.breakpoints[i] = breakpoints[i] + delta

                    # move all the selected nodes
                    for node, data in self.mousePressData['nodes'].items():
                        # update node position and attached edges
                        node.setPos(data['pos'] + delta)
                        # update anchors points
                        for edge, pos in data['anchors'].items():
                            node.setAnchor(edge, pos + delta)
                        # update the edges connected to the shape
                        node.updateEdges()

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
        if mouseEvent.button() == Qt.LeftButton:

            if self.mode == DiagramScene.InsertEdge and self.command and self.command.edge:

                ############################################ EDGE INSERTION ############################################

                # keep the edge only if it's overlapping a node in the scene
                node = self.itemOnTopOf(mouseEvent.scenePos(), edges=False)

                if node:

                    self.command.edge.target = node
                    self.command.edge.source.addEdge(self.command.edge)
                    self.command.edge.target.addEdge(self.command.edge)
                    self.command.edge.updateEdge()

                    # push the command in the undostack
                    self.undoStack.push(self.command)
                    self.updated.emit()

                else:

                    # remove the edge from the scene
                    self.removeItem(self.command.edge)

                self.edgeInsertEnd.emit(self.command.edge, mouseEvent.modifiers())
                self.clearSelection()
                self.command = None

            elif self.mode == DiagramScene.MoveItem:

                ############################################ NODE INSERTION ############################################

                if self.mouseMoved:

                    # collect new positions for the undo command
                    data = {
                        'nodes': {
                            node: {
                                'anchors': {k: v for k, v in node.anchors.items()},
                                'pos': node.pos(),
                            } for node in self.mousePressData['nodes']},
                        'edges': {x: x.breakpoints[:] for x in self.mousePressData['edges']}
                    }

                    # push the command in the stack so we can revert the moving operation
                    self.undoStack.push(CommandNodeMove(scene=self, pos1=self.mousePressData, pos2=data))

        super().mouseReleaseEvent(mouseEvent)

        self.mousePressPos = None
        self.mousePressNode = None
        self.mousePressNodePos = None
        self.mousePressData = None
        self.mouseMoved = False

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
            painter.setPen(DiagramScene.GridPen)
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

    def asGraphol(self):
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
            graph.appendChild(node.asGraphol(document))

        for edge in self.edges():
            # append all the edges to the graph element
            graph.appendChild(edge.asGraphol(document))

        # append the whole graph to the root
        root.appendChild(graph)

        return document

    ####################################################################################################################
    #                                                                                                                  #
    #   AUXILIARY METHODS                                                                                              #
    #                                                                                                                  #
    ####################################################################################################################

    def clear(self):
        """
        Clear the graphics scene by removing all the elements.
        """
        self.clipboard.clear()
        self.undoStack.clear()
        super().clear()

    def edge(self, eid):
        """
        Returns the edge matching the given node id.
        :param eid: the edge id.
        :raise KeyError: if there is no such edge in the scene.
        """
        # iterating over the whole item list is not actually very performant but currently
        # this method is used only when we have to generate a DiagramScene by loading a Graphol
        # document so it won't impact performances once the document is loaded.
        for edge in self.edges():
            if edge.id == eid:
                return edge
        raise KeyError('no edge found with id <{0}>'.format(eid))

    def edges(self):
        """
        Returns all the edges in the diagram scene.
        :rtype: list
        """
        return [x for x in self.items() if isinstance(x, Item) and x.isEdge()]

    def itemOnTopOf(self, point, nodes=True, edges=True):
        """
        Returns the shape which is on top of the given point.
        :type point: QPointF
        :type nodes: bool
        :type edges: bool
        :param point: the graphic point of the scene from where to pick items.
        :param nodes: whether to include nodes in our search.
        :param edges: whether to include edges in our search.
        :rtype: Item
        """
        collection = [x for x in self.items(point) if isinstance(x, Item)]
        collection = [x for x in collection if nodes and x.isNode() or edges and x.isEdge()]
        return max(collection, key=lambda x: x.zValue()) if collection else None

    def node(self, nid):
        """
        Returns the node matching the given node id.
        :param nid: the node id.
        :raise KeyError: if there is no such node in the scene.
        """
        # iterating over the whole item list is not actually very performant but currently
        # this method is used only when we have to generate a DiagramScene by loading a Graphol
        # document so it won't impact performances once the document is loaded.
        for node in self.nodes():
            if node.id == nid:
                return node
        raise KeyError('no node found with id <{0}>'.format(nid))

    def nodes(self):
        """
        Returns all the nodes of the scene (not the shapes).
        :rtype: list
        """
        return [x for x in self.items() if isinstance(x, Item) and x.isNode()]

    def selectedEdges(self):
        """
        Returns the edges selected in the scene.
        :rtype: list
        """
        return [x for x in self.selectedItems() if x.isEdge()]

    def selectedItems(self):
        """
        Returns the items selected in the scene (will filter out labels since we don't need them).
        :rtype: list
        """
        return [x for x in super().selectedItems() if isinstance(x, Item)]

    def selectedNodes(self):
        """
        Returns the nodes selected in the scene.
        :rtype: list
        """
        return [x for x in self.selectedItems() if x.isNode()]

    def setMode(self, mode, param=None):
        """
        Set the operation mode.
        :param mode: the operation mode.
        :param param: the mode parameter (if any).
        """
        self.mode = mode
        self.modeParam = param
        self.modeChanged.emit(mode)

    def snapToGrid(self, point):
        """
        Snap the shape position to the grid.
        :type point: QPointF
        :param point: the position of the shape.
        :return: the position of the shape snapped to the grid if the feature is enabled.
        :rtype: QPointF
        """
        if self.settings.value('scene/snap_to_grid', False, bool):
            newX = snapToGrid(point.x(), DiagramScene.GridSize)
            newY = snapToGrid(point.y(), DiagramScene.GridSize)
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
        Update the clipboard collecting nodes and edges that needs to be copied.
        """
        # reset paste offset for next paste
        self.clipboardPasteOffsetX = DiagramScene.PasteOffsetX
        self.clipboardPasteOffsetY = DiagramScene.PasteOffsetY
        self.clipboardPasteOffsetZ = 0

        self.clipboard = {
            'nodes': {},
            'edges': {},
        }

        # since we are creating a copy of the node (which doesn't carry all the edges with it)
        # we can't iterate over the copy 'edges': because of this we store the original selection
        # locally and we iterate over it matching nodes id to re-attach edge copies.
        nodes = self.selectedNodes()

        for node in nodes:
            self.clipboard['nodes'][node.id] = node.copy(self)
            self.clipboardPasteOffsetZ = max(self.clipboardPasteOffsetZ, node.zValue())

        # figure out if the nodes we are copying are sharing edges:
        # if that's the case, copy the edge together with the nodes
        for node in nodes:
            for edge in node.edges:
                if edge.id not in self.clipboard['edges']:
                    if edge.other(node).isSelected():
                        copy = edge.copy(self)
                        # attach source and target nodes
                        copy.source = self.clipboard['nodes'][edge.source.id]
                        copy.target = self.clipboard['nodes'][edge.target.id]
                        # copy source and target nodes anchor points
                        copy.source.setAnchor(copy, edge.source.anchor(edge))
                        copy.target.setAnchor(copy, edge.target.anchor(edge))
                        # add the copy of the edge to the collection
                        self.clipboard['edges'][edge.id] = copy
                        self.clipboardPasteOffsetZ = max(self.clipboardPasteOffsetZ, edge.zValue())