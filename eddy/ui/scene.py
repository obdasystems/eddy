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


import sys

from PyQt5.QtCore import Qt, QPointF, QSettings, QRectF, pyqtSignal
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import QGraphicsScene, QUndoStack
from PyQt5.QtXml import QDomDocument

from eddy.core.commands import CommandEdgeAdd, CommandNodeAdd, CommandNodeMove
from eddy.core.datatypes import DiagramMode, DistinctList, File, Item, Special
from eddy.core.functions import expandPath, rangeF, snapF
from eddy.core.items.edges import InputEdge, InclusionEdge
from eddy.core.items.nodes import ConceptNode, ComplementNode, RoleChainNode, RoleInverseNode
from eddy.core.items.nodes import RangeRestrictionNode, DomainRestrictionNode
from eddy.core.items.factory import ItemFactory
from eddy.core.syntax import OWL2RLValidator
from eddy.core.utils import Clipboard, GUID


class DiagramScene(QGraphicsScene):
    """
    This class implements the main Diagram Scene.
    """
    GridPen = QPen(QColor(80, 80, 80), 0, Qt.SolidLine)
    GridSize = 20
    MinSize = 2000
    MaxSize = 1000000

    edgeInserted = pyqtSignal('QGraphicsItem', int)  # emitted when a edge is inserted in the scene
    nodeInserted = pyqtSignal('QGraphicsItem', int)  # emitted when a node is inserted in the scene
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
        :type mainwindow: MainWindow
        :type parent: QWidget
        """
        super().__init__(parent)
        self.mainwindow = mainwindow  ## main window reference
        self.command = None  ## undo/redo command to be added in the stack
        self.clipboardPasteOffsetX = Clipboard.PasteOffsetX  ## X offset to be added to item position upon paste
        self.clipboardPasteOffsetY = Clipboard.PasteOffsetY  ## Y offset to be added to item position upon paste
        self.document = File()  ## file associated with the current scene
        self.edgesById = {}  ## used to index edges using their id
        self.nodesById = {}  ## used to index nodes using their id
        self.nodesByLabel = {}  ## used to index nodes using their label text
        self.settings = QSettings(expandPath('@home/Eddy.ini'), QSettings.IniFormat)  ## settings
        self.guid = GUID(self)  ## used to generate unique incremental ids
        self.itemFactory = ItemFactory(self)  ## used to produce graphol items
        self.undostack = QUndoStack(self)  ## used to push actions and keep history for undo/redo
        self.undostack.setUndoLimit(50)  ## TODO: make the stack configurable
        self.validator = OWL2RLValidator(self)
        self.mode = DiagramMode.Idle  ## operation mode
        self.modeParam = None  ## extra parameter for the operation mode (see setMode())
        self.mouseOverNode = None  ## node below the mouse cursor during edge insertion
        self.mousePressPos = None  ## scene position where the mouse has been pressed
        self.mousePressNode = None  ## node acting as mouse grabber during mouse move events
        self.mousePressNodePos = None  ## position of the shape acting as mouse grabber during mouse move events
        self.mousePressData = {}  ## extra data needed to process item interactive movements

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def contextMenuEvent(self, menuEvent):
        """
        Bring up the context menu if necessary.
        :type menuEvent: QGraphicsSceneContextMenuEvent
        """
        item = self.itemOnTopOf(menuEvent.scenePos())
        if item:
            self.clearSelection()
            item.setSelected(True)

        menu = self.mainwindow.menuFactory.create(self.mainwindow, self, item, menuEvent.scenePos())
        menu.exec_(menuEvent.screenPos())

    def mousePressEvent(self, mouseEvent):
        """
        Executed when a mouse button is clicked on the scene.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:

            if self.mode is DiagramMode.NodeInsert:

                ########################################################################################################
                #                                                                                                      #
                #                                         NODE INSERTION                                               #
                #                                                                                                      #
                ########################################################################################################

                # create a new node and place it under the mouse position
                # noinspection PyTypeChecker
                node = self.itemFactory.create(item=self.modeParam, scene=self)
                node.setPos(self.snapToGrid(mouseEvent.scenePos()))

                # no need to switch back the operation mode here: the signal handlers already does that and takes
                # care of the keyboard modifiers being held (if CTRL is being held the operation mode doesn't change)
                self.undostack.push(CommandNodeAdd(scene=self, node=node))
                self.nodeInserted.emit(node, mouseEvent.modifiers())

                super().mousePressEvent(mouseEvent)

            elif self.mode is DiagramMode.EdgeInsert:

                ########################################################################################################
                #                                                                                                      #
                #                                         EDGE INSERTION                                               #
                #                                                                                                      #
                ########################################################################################################

                # see if we are pressing the mouse on a node and if so set the edge add command
                node = self.itemOnTopOf(mouseEvent.scenePos(), edges=False)
                if node:

                    # noinspection PyTypeChecker
                    edge = self.itemFactory.create(item=self.modeParam, scene=self, source=node)
                    edge.updateEdge(target=mouseEvent.scenePos())
                    self.command = CommandEdgeAdd(scene=self, edge=edge)
                    self.addItem(self.command.edge)

                super().mousePressEvent(mouseEvent)

            else:

                # see if this event needs to be handled in graphics items before we prepare data for a different
                # operational mode: a graphics item may bypass the actions being performed here below by
                # switching the operational mode to something different than DiagramMode.Idle.
                super().mousePressEvent(mouseEvent)

                if self.mode is DiagramMode.Idle:

                    ####################################################################################################
                    #                                                                                                  #
                    #                                       ITEM MOVEMENT                                              #
                    #                                                                                                  #
                    ####################################################################################################

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
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if mouseEvent.buttons() & Qt.LeftButton:

            if self.mode is DiagramMode.EdgeInsert:

                ########################################################################################################
                #                                                                                                      #
                #                                         EDGE INSERTION                                               #
                #                                                                                                      #
                ########################################################################################################

                if self.command and self.command.edge:
                    mousePos = mouseEvent.scenePos()
                    statusbar = self.mainwindow.statusBar()
                    self.command.edge.updateEdge(target=mousePos)
                    self.mouseOverNode = self.itemOnTopOf(mousePos, edges=False, skip={self.command.edge.source})
                    if self.mouseOverNode:
                        res = self.validator.result(self.command.edge.source, self.command.edge, self.mouseOverNode)
                        statusbar.showMessage(res.message)
                    else:
                        # always clear the validator and the message no matter if we didn't move out from a node
                        statusbar.clearMessage()
                        self.validator.clear()

            else:

                # if we are still idle we are probably going to start a node(s) move: if that's
                # the case change the operational mode before actually computing delta movements
                if self.mode is DiagramMode.Idle:
                    if self.mousePressNode:
                        self.setMode(DiagramMode.NodeMove)

                if self.mode is DiagramMode.NodeMove:

                    ####################################################################################################
                    #                                                                                                  #
                    #                                       ITEM MOVEMENT                                              #
                    #                                                                                                  #
                    ####################################################################################################

                    # calculate the delta and adjust the value if the snap to grid feature is enabled: we'll use the
                    # position of the node acting as mouse grabber to determine the new delta to and move other items
                    point = self.snapToGrid(self.mousePressNodePos + mouseEvent.scenePos() - self.mousePressPos)
                    delta = point - self.mousePressNodePos
                    edges = set()

                    # update all the breakpoints positions
                    for edge, breakpoints in self.mousePressData['edges'].items():
                        for i in range(len(breakpoints)):
                            edge.breakpoints[i] = breakpoints[i] + delta

                    # move all the selected nodes
                    for node, data in self.mousePressData['nodes'].items():
                        node.setPos(data['pos'] + delta)
                        for edge, pos in data['anchors'].items():
                            node.setAnchor(edge, pos + delta)
                            edges |= set(node.edges)

                    # update edges
                    for edge in edges:
                        edge.updateEdge()

        super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the scene.
        :type mouseEvent: QGraphicsSceneMouseEvent
        """
        if mouseEvent.button() == Qt.LeftButton:

            if self.mode is DiagramMode.EdgeInsert:

                ########################################################################################################
                #                                                                                                      #
                #                                         EDGE INSERTION                                               #
                #                                                                                                      #
                ########################################################################################################

                if self.command and self.command.edge:

                    edge = self.command.edge
                    node = self.itemOnTopOf(mouseEvent.scenePos(), edges=False, skip={edge.source})

                    if node and self.validator.valid(edge.source, edge, node):
                        self.command.end(node)
                        self.undostack.push(self.command)
                        self.updated.emit()
                    else:
                        self.removeItem(edge)

                    # always emit this signal even if the edge has not been inserted since this will clear
                    # also the toolbox switching back the operation mode to DiagramMode.Idle in case the CTRL
                    # keyboard modifier is not being held (in which case the toolbox button will stay selected)
                    self.edgeInserted.emit(edge, mouseEvent.modifiers())

                    self.command = None
                    self.mouseOverNode = None
                    statusbar = self.mainwindow.statusBar()
                    statusbar.clearMessage()
                    self.clearSelection()
                    self.validator.clear()

            elif self.mode is DiagramMode.NodeMove:

                ########################################################################################################
                #                                                                                                      #
                #                                         ITEM MOVEMENT                                                #
                #                                                                                                      #
                ########################################################################################################

                data = {
                    'nodes': {
                        node: {
                            'anchors': {k: v for k, v in node.anchors.items()},
                            'pos': node.pos(),
                        } for node in self.mousePressData['nodes']},
                    'edges': {x: x.breakpoints[:] for x in self.mousePressData['edges']}
                }

                self.undostack.push(CommandNodeMove(scene=self, pos1=self.mousePressData, pos2=data))
                self.setMode(DiagramMode.Idle)

        super().mouseReleaseEvent(mouseEvent)

        self.mousePressPos = None
        self.mousePressNode = None
        self.mousePressNodePos = None
        self.mousePressData = None

    ####################################################################################################################
    #                                                                                                                  #
    #   DRAWING                                                                                                        #
    #                                                                                                                  #
    ####################################################################################################################

    def drawBackground(self, painter, rect):
        """
        Draw the scene background.
        :type painter: QPainter
        :type rect: QRectF
        """
        # do not draw the background grid if we are printing the scene
        # TODO: replace isinstance with something smarter since this may be resource consuming
        if self.settings.value('scene/snap_to_grid', False, bool) and not isinstance(painter.device(), QPrinter):
            startX = int(rect.left()) - (int(rect.left()) % DiagramScene.GridSize)
            startY = int(rect.top()) - (int(rect.top()) % DiagramScene.GridSize)
            painter.setPen(DiagramScene.GridPen)
            painter.drawPoints(*(QPointF(x, y) for x in rangeF(startX, rect.right(), DiagramScene.GridSize) \
                                                 for y in rangeF(startY, rect.bottom(), DiagramScene.GridSize)))

    ####################################################################################################################
    #                                                                                                                  #
    #   EXPORT                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def toGraphol(self):
        """
        Export the current diagram in Graphol format.
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
            graph.appendChild(node.toGraphol(doc))
        for edge in self.edges():
            graph.appendChild(edge.toGraphol(doc))

        root.appendChild(graph)

        return doc

    ####################################################################################################################
    #                                                                                                                  #
    #   AXIOMS COMPOSITION                                                                                             #
    #                                                                                                                  #
    ####################################################################################################################

    def asymmetricRoleAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose an asymmetric role.
        :type source: AbstractNode
        :rtype: set
        """
        x1 = snapF(source.pos().x() + source.width() / 2 + 100, DiagramScene.GridSize, snap=True)
        y1 = snapF(source.pos().y() - source.height() / 2 - 40, DiagramScene.GridSize, snap=True)
        y2 = snapF(source.pos().y() - source.height() / 2 - 80, DiagramScene.GridSize, snap=True)

        node1 = RoleInverseNode(scene=self)
        node1.setPos(QPointF(x1, source.pos().y()))
        node2 = ComplementNode(scene=self)
        node2.setPos(QPointF(x1, y1))
        edge1 = InputEdge(scene=self, source=source, target=node1)
        edge2 = InputEdge(scene=self, source=node1, target=node2)
        edge3 = InclusionEdge(scene=self, source=source, target=node2, breakpoints=[
            QPointF(source.pos().x(), y2),
            QPointF(x1, y2)
        ])

        return {node1, node2, edge1, edge2, edge3}
    
    def functionalAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose a functional axiom.
        :type source: AbstractNode
        :rtype: set
        """
        node1 = DomainRestrictionNode(scene=self)
        edge1 = InputEdge(scene=self, source=source, target=node1, functional=True)

        size = DiagramScene.GridSize

        offsets = (
            QPointF(snapF(+source.width() / 2 + 90, size), 0),
            QPointF(snapF(-source.width() / 2 - 90, size), 0),
            QPointF(0, snapF(-source.height() / 2 - 70, size)),
            QPointF(0, snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(+source.width() / 2 + 90, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(-source.width() / 2 - 90, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(+source.width() / 2 + 90, size), snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(-source.width() / 2 - 90, size), snapF(+source.height() / 2 + 70, size)),
        )

        pos = None
        num = sys.maxsize
        rad = QPointF(node1.width() / 2, node1.height() / 2)

        for o in offsets:
            count = len(self.items(QRectF(source.pos() + o - rad, source.pos() + o + rad)))
            if count < num:
                num = count
                pos = source.pos() + o

        node1.setPos(pos)

        return {node1, edge1}
    
    def inverseFunctionalAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose an inverse functional axiom.
        :type source: AbstractNode
        :rtype: set
        """
        node1 = RangeRestrictionNode(scene=self)
        edge1 = InputEdge(scene=self, source=source, target=node1, functional=True)
        
        size = DiagramScene.GridSize
        
        offsets = (
            QPointF(snapF(+source.width() / 2 + 90, size), 0),
            QPointF(snapF(-source.width() / 2 - 90, size), 0),
            QPointF(0, snapF(-source.height() / 2 - 70, size)),
            QPointF(0, snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(+source.width() / 2 + 90, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(-source.width() / 2 - 90, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(+source.width() / 2 + 90, size), snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(-source.width() / 2 - 90, size), snapF(+source.height() / 2 + 70, size)),
        )
    
        pos = None
        num = sys.maxsize
        rad = QPointF(node1.width() / 2, node1.height() / 2)
    
        for o in offsets:
            count = len(self.items(QRectF(source.pos() + o - rad, source.pos() + o + rad)))
            if count < num:
                num = count
                pos = source.pos() + o
    
        node1.setPos(pos)

        return {node1, edge1}
        
    def irreflexiveRoleAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose an irreflexive role.
        :type source: AbstractNode
        :rtype: set
        """
        x1 = snapF(source.pos().x() + source.width() / 2 + 40, DiagramScene.GridSize, snap=True)
        x2 = snapF(source.pos().x() + source.width() / 2 + 120, DiagramScene.GridSize, snap=True)
        x3 = snapF(source.pos().x() + source.width() / 2 + 250, DiagramScene.GridSize, snap=True)

        node1 = DomainRestrictionNode(scene=self)
        node1.setText('self')
        node1.setPos(QPointF(x1, source.pos().y()))
        node2 = ComplementNode(scene=self)
        node2.setPos(QPointF(x2, source.pos().y()))
        node3 = ConceptNode(scene=self, special=Special.Top)
        node3.setPos(QPointF(x3, source.pos().y()))
        edge1 = InputEdge(scene=self, source=source, target=node1)
        edge2 = InputEdge(scene=self, source=node1, target=node2)
        edge3 = InclusionEdge(scene=self, source=node3, target=node2)

        return {node1, node2, node3, edge1, edge2, edge3}

    def propertyDomainAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose a property domain.
        :type source: AbstractNode
        :rtype: set
        """
        node = DomainRestrictionNode(scene=self)
        edge = InputEdge(scene=self, source=source, target=node)
        
        size = DiagramScene.GridSize
        
        offsets = (
            QPointF(snapF(+source.width() / 2 + 90, size), 0),
            QPointF(snapF(-source.width() / 2 - 90, size), 0),
            QPointF(0, snapF(-source.height() / 2 - 70, size)),
            QPointF(0, snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(+source.width() / 2 + 90, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(-source.width() / 2 - 90, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(+source.width() / 2 + 90, size), snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(-source.width() / 2 - 90, size), snapF(+source.height() / 2 + 70, size)),
        )

        pos = None
        num = sys.maxsize
        rad = QPointF(node.width() / 2, node.height() / 2)

        for o in offsets:
            count = len(self.items(QRectF(source.pos() + o - rad, source.pos() + o + rad)))
            if count < num:
                num = count
                pos = source.pos() + o

        node.setPos(pos)

        return {node, edge}

    def propertyRangeAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose a property range.
        :type source: AbstractNode
        :rtype: set
        """
        node = RangeRestrictionNode(scene=self)
        edge = InputEdge(scene=self, source=source, target=node)

        size = DiagramScene.GridSize

        offsets = (
            QPointF(snapF(+source.width() / 2 + 90, size), 0),
            QPointF(snapF(-source.width() / 2 - 90, size), 0),
            QPointF(0, snapF(-source.height() / 2 - 70, size)),
            QPointF(0, snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(+source.width() / 2 + 90, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(-source.width() / 2 - 90, size), snapF(-source.height() / 2 - 70, size)),
            QPointF(snapF(+source.width() / 2 + 90, size), snapF(+source.height() / 2 + 70, size)),
            QPointF(snapF(-source.width() / 2 - 90, size), snapF(+source.height() / 2 + 70, size)),
        )

        pos = None
        num = sys.maxsize
        rad = QPointF(node.width() / 2, node.height() / 2)

        for o in offsets:
            count = len(self.items(QRectF(source.pos() + o - rad, source.pos() + o + rad)))
            if count < num:
                num = count
                pos = source.pos() + o

        node.setPos(pos)

        return {node, edge}
            
    def reflexiveRoleAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose a reflexive role.
        :type source: AbstractNode
        :rtype: set
        """
        x1 = snapF(source.pos().x() + source.width() / 2 + 40, DiagramScene.GridSize, snap=True)
        x2 = snapF(source.pos().x() + source.width() / 2 + 250, DiagramScene.GridSize, snap=True)

        node1 = DomainRestrictionNode(scene=self)
        node1.setPos(QPointF(x1, source.pos().y()))
        node2 = ConceptNode(scene=self, special=Special.Top)
        node2.setPos(QPointF(x2, source.pos().y()))
        edge1 = InputEdge(scene=self, source=source, target=node1)
        edge2 = InclusionEdge(scene=self, source=node2, target=node1)

        return {node1, node2, edge1, edge2}

    def symmetricRoleAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose a symmetric role.
        :type source: AbstractNode
        :rtype: set
        """
        x1 = snapF(source.pos().x() + source.width() / 2 + 100, DiagramScene.GridSize, snap=True)
        y1 = snapF(source.pos().y() - source.height() / 2 - 80, DiagramScene.GridSize, snap=True)

        node1 = RoleInverseNode(scene=self)
        node1.setPos(QPointF(x1, source.pos().y()))
        edge1 = InputEdge(scene=self, source=source, target=node1)
        edge2 = InclusionEdge(scene=self, source=source, target=node1, breakpoints=[
            QPointF(source.pos().x(), y1),
            QPointF(x1, y1)
        ])

        return {node1, edge1, edge2}
    
    def transitiveRoleAxiomComposition(self, source):
        """
        Returns a collection of items to be added to the given source node to compose a transitive role.
        :type source: AbstractNode
        :rtype: set
        """
        x1 = snapF(source.pos().x() + source.width() / 2 + 90, DiagramScene.GridSize, snap=True)
        x2 = snapF(source.pos().x() + source.width() / 2 + 50, DiagramScene.GridSize, snap=True)
        x3 = snapF(source.pos().x() - source.width() / 2 - 20, DiagramScene.GridSize, snap=True)
        y1 = snapF(source.pos().y() - source.height() / 2 - 20, DiagramScene.GridSize, snap=True)
        y2 = snapF(source.pos().y() + source.height() / 2 + 20, DiagramScene.GridSize, snap=True)
        y3 = snapF(source.pos().y() - source.height() / 2 + 80, DiagramScene.GridSize, snap=True)

        node1 = RoleChainNode(scene=self)
        node1.setPos(QPointF(x1, source.pos().y()))

        edge1 = InputEdge(scene=self, source=source, target=node1, breakpoints=[
            QPointF(source.pos().x(), y1),
            QPointF(x2, y1),
        ])

        edge2 = InputEdge(scene=self, source=source, target=node1, breakpoints=[
            QPointF(source.pos().x(), y2),
            QPointF(x2, y2),
        ])

        edge3 = InclusionEdge(scene=self, source=node1, target=source, breakpoints=[
            QPointF(x1, y3),
            QPointF(x3, y3),
            QPointF(x3, source.pos().y()),
        ])

        return {node1, edge1, edge2, edge3}

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def addItem(self, item):
        """
        Add an item to the diagram scene.
        :type item: AbstractItem
        """
        super().addItem(item)

        # map the item over the index matching its type
        collection = self.nodesById if item.node else self.edgesById
        collection[item.id] = item

        try:
            # map the item in the nodesByLabel index if needed
            if item.node and item.label.editable:
                index = item.text()
                if not index in self.nodesByLabel:
                    self.nodesByLabel[index] = DistinctList()
                self.nodesByLabel[index].append(item)
        except AttributeError:
            # some nodes have no label hence we don't have to index them
            pass

    def clear(self):
        """
        Clear the Diagram Scene by removing all the elements.
        """
        self.edgesById.clear()
        self.nodesById.clear()
        self.nodesByLabel.clear()
        self.undostack.clear()
        super().clear()

    def edge(self, eid):
        """
        Returns the edge matching the given node id.
        :type eid: str
        :raise KeyError: if there is no such edge in the diagram.
        """
        return self.edgesById[eid]

    def edges(self):
        """
        Returns a view on all the edges of the diagram.
        :rtype: view
        """
        return self.edgesById.values()

    def itemOnTopOf(self, point, nodes=True, edges=True, skip=None):
        """
        Returns the shape which is on top of the given point.
        :type point: QPointF
        :type nodes: bool
        :type edges: bool
        :type skip: iterable
        :rtype: Item
        """
        skip = skip or {}
        data = [x for x in self.items(point) if (nodes and x.node or edges and x.edge) and x not in skip]
        if data:
            return max(data, key=lambda x: x.zValue())
        return None

    def node(self, nid):
        """
        Returns the node matching the given node id.
        :type nid: str
        :raise KeyError: if there is no such node in the diagram.
        """
        return self.nodesById[nid]

    def nodes(self):
        """
        Returns a view on all the nodes in the diagram.
        :rtype: view
        """
        return self.nodesById.values()

    def removeItem(self, item):
        """
        Remove an item from the Diagram scene.
        :type item: AbstractItem
        """
        super().removeItem(item)

        # remove the item from the index matching its type
        collection = self.nodesById if item.node else self.edgesById
        collection.pop(item.id, None)

        try:
            # remove the item from the nodesByLabel index if needed
            if item.node and item.label.editable:
                index = item.text()
                if index in self.nodesByLabel:
                    self.nodesByLabel[index].remove(item)
                    if not self.nodesByLabel[index]:
                        del self.nodesByLabel[index]
        except AttributeError:
            # some nodes have no label hence we don't have to index them
            pass

    def selectedEdges(self):
        """
        Returns the edges selected in the scene.
        :rtype: list
        """
        return [x for x in self.selectedItems() if x.edge]

    def selectedItems(self):
        """
        Returns the items selected in the scene (will filter out labels since we don't need them).
        :rtype: list
        """
        return [x for x in super().selectedItems() if x.node or x.edge]

    def selectedNodes(self):
        """
        Returns the nodes selected in the scene.
        :rtype: list
        """
        return [x for x in self.selectedItems() if x.node]

    def setMode(self, mode, param=None):
        """
        Set the operation mode.
        :type mode: DiagramMode
        :type param: int
        """
        if self.mode != mode or self.modeParam != param:
            self.mode = mode
            self.modeParam = param
            self.modeChanged.emit(mode)

    def snapToGrid(self, point):
        """
        Snap the shape position to the grid.
        :type point: QPointF
        :rtype: QPointF
        """
        if self.settings.value('scene/snap_to_grid', False, bool):
            newX = snapF(point.x(), DiagramScene.GridSize)
            newY = snapF(point.y(), DiagramScene.GridSize)
            return QPointF(newX, newY)
        else:
            return point

    def visibleRect(self, margin=0):
        """
        Returns a rectangle matching the area of visible items.
        Will return None if there is no item in the diagram.
        :type margin: float
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