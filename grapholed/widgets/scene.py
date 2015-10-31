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

from grapholed import __appname__, __organization__
from grapholed.commands import CommandItemsMultiAdd, CommandItemsMultiRemove
from grapholed.commands import CommandNodeAdd, CommandNodeSetZValue, CommandNodeMove
from grapholed.commands import CommandEdgeAdd
from grapholed.datatypes import DiagramMode
from grapholed.dialogs import ScenePropertiesDialog
from grapholed.functions import getPath, snapToGrid, rangeF, connect
from grapholed.items import Item
from grapholed.tools import UniqueID

from PyQt5.QtCore import Qt, pyqtSignal, QPointF, pyqtSlot, QSettings, QRectF
from PyQt5.QtGui import QPen, QColor, QIcon
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QGraphicsScene, QUndoStack, QMenu, QAction
from PyQt5.QtXml import QDomDocument


class DiagramDocument(object):
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
        self._filepath = getPath(value)

    @property
    def name(self):
        """
        Returns the name of the saved file.
        :rtype: str
        """
        if not self.filepath:
            return 'Untitled'
        return os.path.basename(os.path.normpath(self.filepath))


class DiagramScene(QGraphicsScene):
    """
    This class implements the main Diagram Scene.
    """
    GridPen = QPen(QColor(80, 80, 80), 0, Qt.SolidLine)
    GridSize = 20
    MinSize = 2000
    MaxSize = 1000000
    PasteOffsetX = 20
    PasteOffsetY = 10

    nodeInserted = pyqtSignal('QGraphicsItem', int)  # emitted when a node is inserted in the scene
    edgeInserted = pyqtSignal('QGraphicsItem', int)  # emitted when a edge is inserted in the scene
    modeChanged = pyqtSignal(DiagramMode)  # emitted when the operational mode changes
    updated = pyqtSignal()  # emitted when the scene is updated

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
        self.document = DiagramDocument()  ## document associated with the current scene
        self.settings = QSettings(__organization__, __appname__)  ## application settings
        self.uniqueID = UniqueID()  ## used to generate unique incrementsl ids
        self.undoStack = QUndoStack(self)  ## use to push actions and keep history for undo/redo
        self.undoStack.setUndoLimit(50) ## TODO: make the stack configurable
        self.mode = DiagramMode.Idle ## operation mode
        self.modeParam = None  ## extra parameter for the operation mode (see setMode())
        self.mousePressPos = None  ## scene position where the mouse has been pressed
        self.mousePressNode = None  ## node acting as mouse grabber during mouse move events
        self.mousePressNodePos = None  ## position of the shape acting as mouse grabber during mouse move events
        self.mousePressData = {}  ## extra data needed to process item interactive movements

        ################################################# ACTIONS ######################################################

        self.actionItemCut = mainwindow.actionItemCut
        self.actionItemCopy = mainwindow.actionItemCopy
        self.actionItemPaste = mainwindow.actionItemPaste
        self.actionItemDelete = mainwindow.actionItemDelete
        self.actionBringToFront = mainwindow.actionBringToFront
        self.actionSendToBack = mainwindow.actionSendToBack
        self.actionSelectAll = mainwindow.actionSelectAll
        self.actionProperties = QAction('Properties...', self)
        self.actionProperties.setIcon(QIcon(':/icons/preferences'))

        ################################################# SIGNALS ######################################################

        connect(self.nodeInserted, self.onNodeInserted)
        connect(self.edgeInserted, self.onEdgeInserted)
        connect(self.selectionChanged, self.onSelectionChanged)
        connect(self.actionProperties.triggered, self.doSceneProperties)

    ####################################################################################################################
    #                                                                                                                  #
    #   ACTION HANDLERS                                                                                                #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot()
    def doItemCut(self):
        """
        Cut selected items from the scene.
        """
        self.setMode(DiagramMode.Idle)
        self.updateClipboard()
        self.updateActions()

        selection = self.selectedItems()
        if selection:
            selection.extend([x for item in selection if item.isNode() for x in item.edges if x not in selection])
            self.undoStack.push(CommandItemsMultiRemove(scene=self, collection=selection))

        # clear offsets so we can paste in the same position
        self.clipboardPasteOffsetX = 0
        self.clipboardPasteOffsetY = 0
        self.clipboardPasteOffsetZ = 0

    @pyqtSlot()
    def doItemCopy(self):
        """
        Make a copy of selected items.
        """
        self.setMode(DiagramMode.Idle)
        self.updateClipboard()
        self.updateActions()

    @pyqtSlot()
    def doItemPaste(self):
        """
        Paste previously copied items.
        """
        self.setMode(DiagramMode.Idle)

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
    def doItemDelete(self):
        """
        Delete the currently selected items from the graphic scene.
        """
        self.setMode(DiagramMode.Idle)
        selection = self.selectedItems()
        if selection:
            selection.extend([x for item in selection if item.isNode() for x in item.edges if x not in selection])
            self.undoStack.push(CommandItemsMultiRemove(scene=self, collection=selection))

    @pyqtSlot()
    def doBringToFront(self):
        """
        Bring the selected item to the top of the scene.
        """
        self.setMode(DiagramMode.Idle)
        for selected in self.selectedNodes():
            zValue = 0
            colliding = selected.collidingItems()
            for item in filter(lambda x: isinstance(x, Item), colliding):
                if item.zValue() >= zValue:
                    zValue = item.zValue() + 0.1
            if zValue != selected.zValue():
                self.undoStack.push(CommandNodeSetZValue(scene=self, node=selected, zValue=zValue))

    @pyqtSlot()
    def doSendToBack(self):
        """
        Send the selected item to the back of the scene.
        """
        self.setMode(DiagramMode.Idle)
        for selected in self.selectedNodes():
            zValue = 0
            colliding = selected.collidingItems()
            for item in filter(lambda x: isinstance(x, Item), colliding):
                if item.zValue() >= zValue:
                    zValue = item.zValue() - 0.1
            if zValue != selected.zValue():
                self.undoStack.push(CommandNodeSetZValue(scene=self, node=selected, zValue=zValue))

    @pyqtSlot()
    def doSelectAll(self):
        """
        Select all the items in the scene.
        """
        self.setMode(DiagramMode.Idle)
        self.clearSelection()
        for item in self.nodes() + self.edges():
            item.setSelected(True)

    @pyqtSlot()
    def doSceneProperties(self):
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
    def onEdgeInserted(self, edge, modifiers):
        """
        Triggered after a edge insertion process ends.
        :param edge: the inserted edge.
        :param modifiers: keyboard modifiers held during edge insertion.
        """
        self.command = None
        if not modifiers & Qt.ControlModifier:
            self.setMode(DiagramMode.Idle)

    @pyqtSlot('QGraphicsItem', int)
    def onNodeInserted(self, node, modifiers):
        """
        Triggered after a node insertion process ends.
        :param node: the inserted node.
        :param modifiers: keyboard modifiers held during node insertion.
        """
        if not modifiers & Qt.ControlModifier:
            self.setMode(DiagramMode.Idle)

    @pyqtSlot()
    def onSelectionChanged(self):
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
            menu.addAction(self.actionProperties)
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
            self.doItemDelete()
        super().keyPressEvent(keyEvent)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when a mouse button is clicked on the scene.
        :param mouseEvent: the mouse event instance.
        """
        if mouseEvent.buttons() & Qt.LeftButton:

            if self.mode is DiagramMode.NodeInsert:

                ############################################ NODE INSERTION ############################################

                # create a new node and place it under the mouse position
                func = self.modeParam
                node = func(scene=self)
                node.setPos(self.snapToGrid(mouseEvent.scenePos()))

                # no need to switch back the operation mode here: the signal handlers already does that and takes
                # care of the keyboard modifiers being held (if CTRL is being held the operation mode doesn't change)
                self.undoStack.push(CommandNodeAdd(scene=self, node=node))
                self.nodeInserted.emit(node, mouseEvent.modifiers())

                super().mousePressEvent(mouseEvent)

            elif self.mode is DiagramMode.EdgeInsert:

                ############################################ EDGE INSERTION ############################################

                # see if we are pressing the mouse on a node and if so set the edge add command
                node = self.itemOnTopOf(mouseEvent.scenePos(), edges=False)
                if node:

                    func = self.modeParam
                    edge = func(scene=self, source=node)
                    edge.updateEdge(target=mouseEvent.scenePos())

                    # put the command on hold since we don't know if the edge will be truly inserted
                    self.command = CommandEdgeAdd(scene=self, edge=edge)

                    # add the edge to the scene
                    self.addItem(self.command.edge)

                super().mousePressEvent(mouseEvent)

            else:

                # see if this event needs to be handled in graphics items before we prepare data for a different
                # operational mode: a graphics item may bypass the actions being performed here below by
                # switching the operational mode to something different than DiagramMode.Idle.
                super().mousePressEvent(mouseEvent)

                if self.mode is DiagramMode.Idle:

                    ########################################## ITEM MOVEMENT ###########################################

                    # see if we have some nodes selected in the scene: this is needed because itemOnTopOf
                    # will discard labels, so if we have a node whose label is overlapping the node shape,
                    # clicking on the label will make itemOnTopOf return the node item instead of the label.
                    selected = self.selectedNodes()

                    if selected:

                        # we have some nodes selected in the scene so we probably are going to do a
                        # move operation, prepare data for mouse move event => select a node that will act
                        # as mouse grabber to compute delta movements for each componenet in the selection
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

            if self.mode is DiagramMode.EdgeInsert:

                ############################################ EDGE INSERTION ############################################

                # update the edge position so that it will follow the mouse one
                if self.command and self.command.edge:
                    self.command.edge.updateEdge(target=mouseEvent.scenePos())

            else:

                # if we are still idle we are probably going to start a node(s) move: if that's
                # the case change the operational mode before actually computing delta movements
                if self.mode is DiagramMode.Idle:
                    if self.mousePressNode:
                        self.setMode(DiagramMode.NodeMove)

                if self.mode is DiagramMode.NodeMove:

                    ########################################## ITEM MOVEMENT ###########################################

                    # calculate the delta and adjust the value if the snap to grid feature is enabled: we'll use the
                    # position of the node acting as mouse grabber to determine the new delta to and move other items
                    snapped = self.snapToGrid(self.mousePressNodePos + mouseEvent.scenePos() - self.mousePressPos)
                    delta = snapped - self.mousePressNodePos

                    # update all the breakpoints positions
                    for edge, breakpoints in self.mousePressData['edges'].items():
                        for i in range(len(breakpoints)):
                            edge.breakpoints[i] = breakpoints[i] + delta

                    # move all the selected nodes
                    for node, data in self.mousePressData['nodes'].items():
                        node.setPos(data['pos'] + delta)
                        for edge, pos in data['anchors'].items():
                            node.setAnchor(edge, pos + delta)
                        node.updateEdges()

        # !!! IMPORTANT !!! THIS MUST ALWAYS BE CALLED SINCE IT TRIGGERS ALSO HOVER EVENTS FOR GRAPHICS ITEMS
        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the scene.
        :param mouseEvent: the mouse event instance.
        """
        if mouseEvent.button() == Qt.LeftButton:

            if self.mode is DiagramMode.EdgeInsert:

                ############################################ EDGE INSERTION ############################################

                if self.command and self.command.edge:

                    # keep the edge only if it's overlapping a node in the scene
                    node = self.itemOnTopOf(mouseEvent.scenePos(), edges=False)

                    if node:

                        self.command.edge.target = node
                        self.command.edge.source.addEdge(self.command.edge)
                        self.command.edge.target.addEdge(self.command.edge)
                        self.command.edge.updateEdge()

                        self.undoStack.push(self.command)
                        self.updated.emit()

                    else:

                        # remove the edge from the scene
                        self.removeItem(self.command.edge)

                    # always emit this signal even if the edge has not been inserted since this will clear
                    # also the toolbox switching back the operation mode to DiagramMode.Idle in case the CTRL
                    # keyboard modifier is not being held (in which case the toolbox button will stay selected)
                    self.edgeInserted.emit(self.command.edge, mouseEvent.modifiers())

                    self.clearSelection()
                    self.command = None

            elif self.mode is DiagramMode.NodeMove:

                ########################################## ITEM MOVEMENT ###########################################

                data = {
                    'nodes': {
                        node: {
                            'anchors': {k: v for k, v in node.anchors.items()},
                            'pos': node.pos(),
                        } for node in self.mousePressData['nodes']},
                    'edges': {x: x.breakpoints[:] for x in self.mousePressData['edges']}
                }

                self.undoStack.push(CommandNodeMove(scene=self, pos1=self.mousePressData, pos2=data))
                self.setMode(DiagramMode.Idle)

        super().mouseReleaseEvent(mouseEvent)

        self.mousePressPos = None
        self.mousePressNode = None
        self.mousePressNodePos = None
        self.mousePressData = None

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
            startX = int(rect.left()) - (int(rect.left()) % DiagramScene.GridSize)
            startY = int(rect.top()) - (int(rect.top()) % DiagramScene.GridSize)
            painter.drawPoints(*(QPointF(x, y) for x in rangeF(startX, rect.right(), DiagramScene.GridSize) \
                                                 for y in rangeF(startY, rect.bottom(), DiagramScene.GridSize)))

    ####################################################################################################################
    #                                                                                                                  #
    #   SCENE EXPORT                                                                                                   #
    #                                                                                                                  #
    ####################################################################################################################

    def toGraphol(self):
        """
        Export the current node in Graphol format.
        :rtype: QDomDocument
        """
        doc = QDomDocument()
        doc.appendChild(doc.createProcessingInstruction('xml', 'version="1.0" encoding="UTF-8" standalone="no"'))

        root = doc.createElement('graphol')
        root.setAttribute('xmlns', 'http://www.dis.uniroma1.it/~graphol/schema')
        root.setAttribute('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.setAttribute('xmlns:data', 'http://www.dis.uniroma1.it/~graphol/schema/data')
        root.setAttribute('xmlns:line', 'http://www.dis.uniroma1.it/~graphol/schema/line')
        root.setAttribute('xmlns:shape', 'http://www.dis.uniroma1.it/~graphol/schema/shape')
        root.setAttribute('xsi:schemaLocation', 'http://www.dis.uniroma1.it/~graphol/schema '
                                                'http://www.dis.uniroma1.it/~graphol/schema/graphol.xsd')

        doc.appendChild(root)

        graph = doc.createElement('graph')
        graph.setAttribute('width', self.sceneRect().width())
        graph.setAttribute('height', self.sceneRect().height())

        for node in self.nodes():
            # append all the nodes to the graph element
            graph.appendChild(node.toGraphol(doc))

        for edge in self.edges():
            # append all the edges to the graph element
            graph.appendChild(edge.toGraphol(doc))

        # append the whole graph to the root
        root.appendChild(graph)

        return doc

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
        Returns all the nodes of the scene.
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
        if self.mode != mode or self.modeParam != param:
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

    def visibleRect(self, margin=0):
        """
        Returns a rectangle matching the area of visible items.
        Will return None if there is no item in the diagram.
        :param margin: extra margin to be added to the sides of the rectangle.
        :rtype: QRectF
        """
        items = self.items()
        if items:

            X = set()
            Y = set()
            for item in items:
                B = item.mapRectToScene(item.boundingRect())
                X |= {B.left(), B.right()}
                Y |= {B.top(), B.bottom()}

            return QRectF(QPointF(min(X) - margin, min(Y) - margin), QPointF(max(X) + margin, max(Y) + margin))

        return None