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
#     - Daniele Pantaleone <pantaleone@dis.uniroma1.it>                  #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.graphol import Special
from eddy.core.datatypes.qt import Font
from eddy.core.datatypes.system import File
from eddy.core.functions.misc import first, rstrip
from eddy.core.functions.signals import connect, disconnect
from eddy.core.output import getLogger
from eddy.core.plugin import AbstractPlugin
from eddy.ui.dock import DockWidget
from eddy.ui.fields import StringField

LOGGER = getLogger()


class UnsatisfiableEntityExplorerPlugin(AbstractPlugin):
    """
    This plugin provides the UnsatisfiableEntitiesExplorer widget.
    """
    sgnFakeItemAdded = QtCore.pyqtSignal('QGraphicsScene', 'QGraphicsItem')
    sgnFakeExplanationAdded = QtCore.pyqtSignal('QGraphicsItem', list)

    def checkmatchforOWLtermandnodename(self, OWL_term_1, OWL_term_2):
        # it should not be a complement of a class; i.e. the raw term should start with <
        if (OWL_term_1 is None) or (OWL_term_2 is None):
            return False

        if str(type(OWL_term_1)) == '<class \'list\'>':
            for t1 in OWL_term_1:
                if str(type(OWL_term_2)) == '<class \'list\'>':
                    for t2 in OWL_term_2:
                        if (t1[0] == '<') and (t2[0] == '<'):
                            if t1 == t2:
                                return True
                else:
                    if (t1[0] == '<') and (t2[0] == '<'):
                        if t1 == t2:
                            return True

        if (OWL_term_1[0] == '<') and (OWL_term_2[0] == '<'):
            if OWL_term_1 == OWL_term_2:
                return True

        top_and_bottom_entities = []
        top_and_bottom_entities.extend(Special.return_group(Special.AllTopEntities))
        top_and_bottom_entities.extend(Special.return_group(Special.AllBottomEntities))

        if (OWL_term_1 in top_and_bottom_entities) and (OWL_term_1 == OWL_term_2):
            return True

        return False

    def get_list_of_nodes_in_diagram_from_OWL_terms(self, input_list):
        return_list = []

        for ue in input_list:
            # OWL_term_for_uc = uc
            temp = []

            for p in self.project.nodes():
                OWL_term_for_p = self.project.getOWLtermfornode(p)
                match = self.checkmatchforOWLtermandnodename(ue, OWL_term_for_p)

                if match is True:
                    temp.append(p)

            if len(temp) == 0:
                LOGGER.critical('no nodes found for WOL term-' + ue)

            return_list.append(temp)

        return return_list

    def add_unsatisfiable_nodes_in_widget(self, input_list, inp_type):
        count = 0

        for entity in input_list:
            for node in entity:
                self.sgnFakeItemAdded.emit(node.diagram, node)

            if inp_type == 'unsatisfiable_classes':
                explanation_for_node = self.project.explanations_for_unsatisfiable_classes[count]
            elif inp_type == 'unsatisfiable_attributes':
                explanation_for_node = self.project.explanations_for_unsatisfiable_attributes[count]
            elif inp_type == 'unsatisfiable_roles':
                explanation_for_node = self.project.explanations_for_unsatisfiable_roles[count]
            else:
                LOGGER.error('invalid inp_type in module add_unsatisfiable_nodes_in_widget')

            if len(entity) > 0:
                self.sgnFakeExplanationAdded.emit(entity[0], explanation_for_node)

            count = count + 1

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onSessionReady(self):
        """
        Executed whenever the main session completes the startup sequence.
        """
        self.widget('unsatisfiable_entity_explorer').doClear()

    @QtCore.pyqtSlot()
    def onConsistencyCheckStarted(self):
        """
        Executed when the consistency check is started.
        """
        self.widget('unsatisfiable_entity_explorer').doClear()

    @QtCore.pyqtSlot()
    def onConsistencyCheckReset(self):
        """
        Executed when the consistency check is resetted.
        """
        self.widget('unsatisfiable_entity_explorer').doClear()
        if self.widget('unsatisfiable_entity_explorer_dock').isVisible():
            self.widget('unsatisfiable_entity_explorer_dock').toggleViewAction().trigger()

    @QtCore.pyqtSlot()
    def onPerfectOntology(self):
        """
        Executed when the consistency check detects that the ontology is consistent and all classes
        are satisfiable.
        """
        self.widget('unsatisfiable_entity_explorer').doClear()

    @QtCore.pyqtSlot()
    def onInconsistentOntology(self):
        """
        Executed when the consistency check detects that the active ontology is inconsistent.
        """
        self.widget('unsatisfiable_entity_explorer').doClear()

    @QtCore.pyqtSlot()
    def onUnsatisfiableEntities(self):
        """
        Executed when the consistency check detects unsatisfiable entities in the ontology.
        """
        # CONNECT TO PROJECT SPECIFIC SIGNALS
        widget = self.widget('unsatisfiable_entity_explorer')
        connect(self.project.sgnItemAdded, widget.doAddNode)
        connect(self.project.sgnItemRemoved, widget.doRemoveNode)

        # FILL IN UNSATISFIABLE ENTITIES EXPLORER WITH DATA
        connect(self.sgnFakeItemAdded, widget.doAddNode)
        connect(self.sgnFakeExplanationAdded, widget.doAddExplanation)

        classes_only_unsatisfiable_nodes_in_diagram = \
            self.get_list_of_nodes_in_diagram_from_OWL_terms(self.project.unsatisfiable_classes)
        attributes_only_unsatisfiable_nodes_in_diagram = \
            self.get_list_of_nodes_in_diagram_from_OWL_terms(self.project.unsatisfiable_attributes)
        roles_only_unsatisfiable_nodes_in_diagram = \
            self.get_list_of_nodes_in_diagram_from_OWL_terms(self.project.unsatisfiable_roles)

        for n in classes_only_unsatisfiable_nodes_in_diagram:
            self.project.nodes_of_unsatisfiable_entities.extend(n)
        for n in attributes_only_unsatisfiable_nodes_in_diagram:
            self.project.nodes_of_unsatisfiable_entities.extend(n)
        for n in roles_only_unsatisfiable_nodes_in_diagram:
            self.project.nodes_of_unsatisfiable_entities.extend(n)

        temp = []

        for n in self.project.nodes_of_unsatisfiable_entities:
            owl_term = self.project.getOWLtermfornode(n)
            temp.append(owl_term)
        self.project.nodes_of_unsatisfiable_entities.extend(temp)

        self.add_unsatisfiable_nodes_in_widget(
            classes_only_unsatisfiable_nodes_in_diagram, 'unsatisfiable_classes')
        self.add_unsatisfiable_nodes_in_widget(
            attributes_only_unsatisfiable_nodes_in_diagram, 'unsatisfiable_attributes')
        self.add_unsatisfiable_nodes_in_widget(
            roles_only_unsatisfiable_nodes_in_diagram, 'unsatisfiable_roles')

        disconnect(self.sgnFakeItemAdded, widget.doAddNode)
        disconnect(self.sgnFakeExplanationAdded, widget.doAddExplanation)

        # SHOW THE PLUGIN DOCK WIDGET
        if not self.widget('unsatisfiable_entity_explorer_dock').isVisible():
            self.widget('unsatisfiable_entity_explorer_dock').toggleViewAction().trigger()
            self.widget('unsatisfiable_entity_explorer_dock').raise_()

    #############################################
    #   HOOKS
    #################################

    def dispose(self):
        """
        Executed whenever the plugin is going to be destroyed.
        """
        # DISCONNECT FROM CURRENT PROJECT
        widget = self.widget('unsatisfiable_entity_explorer')
        self.debug('Disconnecting from project: %s', self.project.name)
        disconnect(self.project.sgnItemAdded, widget.doAddNode)
        disconnect(self.project.sgnItemRemoved, widget.doRemoveNode)

        # DISCONNECT FROM ACTIVE SESSION
        self.debug('Disconnecting from active session')
        disconnect(self.session.sgnReady, self.onSessionReady)
        disconnect(self.session.sgnConsistencyCheckStarted, self.onConsistencyCheckStarted)
        disconnect(self.session.sgnConsistencyCheckReset, self.onConsistencyCheckReset)
        disconnect(self.session.sgnPerfectOntology, self.onPerfectOntology)
        disconnect(self.session.sgnInconsistentOntology, self.onInconsistentOntology)
        disconnect(self.session.sgnUnsatisfiableEntities, self.onUnsatisfiableEntities)

        # REMOVE DOCKING AREA WIDGET MENU ENTRY
        self.debug('Removing docking area widget toggle from "view" menu')
        menu = self.session.menu('view')
        menu.removeAction(self.widget('unsatisfiable_entity_explorer_dock').toggleViewAction())

        # UNINSTALL THE PALETTE DOCK WIDGET
        self.debug('Uninstalling docking area widget')
        self.session.removeDockWidget(self.widget('unsatisfiable_entity_explorer_dock'))

    def start(self):
        """
        Perform initialization tasks for the plugin.
        """
        # INITIALIZE THE WIDGET
        self.debug('Creating Unsatisfiable_Entity_Explorer widget')
        widget = UnsatisfiableEntityExplorerWidget(self)
        widget.setObjectName('unsatisfiable_entity_explorer')
        self.addWidget(widget)

        # CREATE DOCKING AREA WIDGET
        self.debug('Creating docking area widget')
        widget = DockWidget('Unsatisfiable Entity Explorer', QtGui.QIcon(':icons/18/ic_explore_black'), self.session)
        widget.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.BottomDockWidgetArea)
        widget.setObjectName('unsatisfiable_entity_explorer_dock')
        widget.setWidget(self.widget('unsatisfiable_entity_explorer'))
        self.addWidget(widget)

        # CREATE ENTRY IN VIEW MENU
        self.debug('Creating docking area widget toggle in "view" menu')
        menu = self.session.menu('view')
        menu.addAction(self.widget('unsatisfiable_entity_explorer_dock').toggleViewAction())

        # CONFIGURE SIGNALS
        self.debug('Configuring session specific signals')
        connect(self.session.sgnReady, self.onSessionReady)
        connect(self.session.sgnConsistencyCheckStarted, self.onConsistencyCheckStarted)
        connect(self.session.sgnConsistencyCheckReset, self.onConsistencyCheckReset)
        connect(self.session.sgnPerfectOntology, self.onPerfectOntology)
        connect(self.session.sgnInconsistentOntology, self.onInconsistentOntology)
        connect(self.session.sgnUnsatisfiableEntities, self.onUnsatisfiableEntities)

        # INSTALL DOCKING AREA WIDGET
        self.debug('Installing docking area widget')
        self.session.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.widget('unsatisfiable_entity_explorer_dock'))

        # HIDE THE DOCK WIDGET BY DEFAULT
        if self.widget('unsatisfiable_entity_explorer_dock').toggleViewAction().isVisible():
            self.widget('unsatisfiable_entity_explorer_dock').toggleViewAction().trigger()


class UnsatisfiableEntityExplorerWidget(QtWidgets.QWidget):
    """
    This class implements the UnsatisfiableEntitiesExplorer
    """
    sgnItemClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnItemDoubleClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnItemRightClicked = QtCore.pyqtSignal('QGraphicsItem')

    sgnStringClicked = QtCore.pyqtSignal('QStandardItem')
    sgnStringDoubleClicked = QtCore.pyqtSignal('QStandardItem')
    sgnStringRightClicked = QtCore.pyqtSignal('QStandardItem')

    sgnListClicked = QtCore.pyqtSignal('QStandardItem')
    sgnListDoubleClicked = QtCore.pyqtSignal('QStandardItem')
    sgnListRightClicked = QtCore.pyqtSignal('QStandardItem')

    def __init__(self, plugin):
        """
        Initialize the UnsatisfiableEntitiesExplorer widget.
        :type plugin: Session
        """
        super().__init__(plugin.session)
        self.plugin = plugin

        self.brush_orange = QtGui.QBrush(QtGui.QColor(255, 165, 0, 160))
        self.iconAttribute = QtGui.QIcon(':/icons/18/ic_treeview_attribute')
        self.iconConcept = QtGui.QIcon(':/icons/18/ic_treeview_concept')
        self.iconInstance = QtGui.QIcon(':/icons/18/ic_treeview_instance')
        self.iconRole = QtGui.QIcon(':/icons/18/ic_treeview_role')
        self.iconValue = QtGui.QIcon(':/icons/18/ic_treeview_value')

        self.search = StringField(self)
        self.search.setAcceptDrops(False)
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText('Search...')
        self.search.setFixedHeight(30)
        self.model = QtGui.QStandardItemModel(self)
        self.proxy = QtCore.QSortFilterProxyModel(self)
        self.proxy.setDynamicSortFilter(False)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setSortCaseSensitivity(QtCore.Qt.CaseSensitive)
        self.proxy.setSourceModel(self.model)
        self.ontoview = UnsatisfiableEntityExplorerView(self)
        self.ontoview.setModel(self.proxy)
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.search)
        self.mainLayout.addWidget(self.ontoview)

        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(216)

        self.setStyleSheet("""
            QLineEdit,
            QLineEdit:editable,
            QLineEdit:hover,
            QLineEdit:pressed,
            QLineEdit:focus {
              border: none;
              border-radius: 0;
              background: #FFFFFF;
              color: #000000;
              padding: 4px 4px 4px 4px;
            }
        """)

        header = self.ontoview.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        connect(self.ontoview.doubleClicked, self.onItemDoubleClicked)
        connect(self.ontoview.pressed, self.onItemPressed)
        connect(self.search.textChanged, self.doFilterItem)
        connect(self.sgnItemDoubleClicked, self.session.doFocusItem)
        connect(self.sgnItemRightClicked, self.session.doFocusItem)

        connect(self.sgnStringClicked, self.doStartExplanationExplorer)
        connect(self.sgnStringDoubleClicked, self.doStartExplanationExplorer)

        connect(self.sgnListClicked, self.doStartExplanationExplorer)
        connect(self.sgnListDoubleClicked, self.doStartExplanationExplorer)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self):
        """
        Returns the reference to the active project.
        :rtype: Session
        """
        return self.session.project

    @property
    def session(self):
        """
        Returns the reference to the active session.
        :rtype: Session
        """
        return self.plugin.parent()

    #############################################
    #   EVENTS
    #################################

    def paintEvent(self, paintEvent):
        """
        This is needed for the widget to pick the stylesheet.
        :type paintEvent: QPaintEvent
        """
        option = QtWidgets.QStyleOption()
        option.initFrom(self)
        painter = QtGui.QPainter(self)
        style = self.style()
        style.drawPrimitive(QtWidgets.QStyle.PE_Widget, option, painter, self)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot('QGraphicsItem', list)
    def doAddExplanation(self, node, explanation):
        if explanation is not None and len(explanation) > 0:
            exp_to_add = QtGui.QStandardItem()
            exp_to_add.setText('<Explanation(s)> \n**(click to open Explanation Explorer)')
            font = QtGui.QFont()
            font.setBold(True)
            font.setItalic(True)
            font.setUnderline(True)
            exp_to_add.setFont(font)
            exp_to_add.setData(explanation)
            parent = self.parentFor(node)
            parent.appendRow(exp_to_add)

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def doAddNode(self, diagram, node):
        """
        Add a node in the tree view.
        :type diagram: QGraphicsScene
        :type node: AbstractItem
        """
        owl_term_for_node = self.project.getOWLtermfornode(node)

        if (node not in self.project.nodes_of_unsatisfiable_entities) and ((owl_term_for_node is not None) and (
                owl_term_for_node in self.project.nodes_of_unsatisfiable_entities)):
            self.project.nodes_of_unsatisfiable_entities.append(node)

        if (node in self.project.nodes_of_unsatisfiable_entities) or ((owl_term_for_node is not None) and (
                owl_term_for_node in self.project.nodes_of_unsatisfiable_entities)):
            parent = self.parentFor(node)
            if not parent:
                parent = QtGui.QStandardItem(self.parentKey(node))
                parent.setIcon(self.iconFor(node))
                parent.setData(node)
                self.model.appendRow(parent)
                self.proxy.sort(0, QtCore.Qt.AscendingOrder)
            child = QtGui.QStandardItem(self.childKey(diagram, node))
            child.setData(node)
            parent.appendRow(child)
            self.proxy.sort(0, QtCore.Qt.AscendingOrder)

            node.selection.setBrush(self.brush_orange)
            # node.updateNode(valid=False)
            # FORCE CACHE REGENERATION
            node.setCacheMode(node.NoCache)
            node.setCacheMode(node.DeviceCoordinateCache)

            # SCHEDULE REPAINT
            node.update(node.boundingRect())
            node.diagram.sgnUpdated.emit()

    @QtCore.pyqtSlot('QStandardItem')
    def doStartExplanationExplorer(self, item):
        parent = item.parent()
        self.project.uc_as_input_for_explanation_explorer = str(parent.data())
        # Should be removed when the new reasoner API is implemented
        self.session.plugin('explanation_explorer').doUpdateExplanations()

    @QtCore.pyqtSlot()
    def doClear(self):
        """
        Clear all the nodes in the tree view.
        """
        self.search.clear()
        self.model.clear()
        self.ontoview.update()

    @QtCore.pyqtSlot(str)
    def doFilterItem(self, key):
        """
        Executed when the search box is filled with data.
        :type key: str
        """
        self.proxy.setFilterFixedString(key)
        self.proxy.sort(QtCore.Qt.AscendingOrder)

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def doRemoveNode(self, diagram, node):
        """
        Remove a node from the tree view.
        :type diagram: QGraphicsScene
        :type node: AbstractItem
        """
        if node.type() in {Item.ConceptNode, Item.RoleNode, Item.AttributeNode, Item.IndividualNode}:
            if node in self.project.nodes_of_unsatisfiable_entities:
                self.project.nodes_of_unsatisfiable_entities.remove(node)
            parent = self.parentFor(node)
            if parent:
                child = self.childFor(parent, diagram, node)
                if child:
                    parent.removeRow(child.index().row())
                if not parent.rowCount():
                    self.model.removeRow(parent.index().row())

    @QtCore.pyqtSlot('QModelIndex')
    def onItemDoubleClicked(self, index):
        """
        Executed when an item in the treeview is double clicked.
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QtWidgets.QApplication.mouseButtons() & QtCore.Qt.LeftButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))

            if item and item.data():
                if (str(type(item.data())) == '<class \'str\'>') or (str(type(item.data())) == 'str'):
                    self.sgnStringDoubleClicked.emit(item)
                elif (str(type(item.data())) == '<class \'list\'>') or (str(type(item.data())) == 'list'):
                    self.sgnListDoubleClicked.emit(item)
                else:
                    self.sgnItemDoubleClicked.emit(item.data())

    @QtCore.pyqtSlot('QModelIndex')
    def onItemPressed(self, index):
        """
        Executed when an item in the treeview is clicked.
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QtWidgets.QApplication.mouseButtons() & QtCore.Qt.LeftButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item and item.data():
                if (str(type(item.data())) == '<class \'str\'>') or (str(type(item.data())) == 'str'):
                    self.sgnStringClicked.emit(item)
                elif (str(type(item.data())) == '<class \'list\'>') or (str(type(item.data())) == 'list'):
                    self.sgnListClicked.emit(item)
                else:
                    self.sgnItemClicked.emit(item.data())

    #############################################
    #   INTERFACE
    #################################

    def childFor(self, parent, diagram, node):
        """
        Search the item representing this node among parent children.
        :type parent: QtGui.QStandardItem
        :type diagram: Diagram
        :type node: AbstractNode
        """
        key = self.childKey(diagram, node)
        for i in range(parent.rowCount()):
            child = parent.child(i)
            if child.text() == key:
                return child
        return None

    @staticmethod
    def childKey(diagram, node):
        """
        Returns the child key (text) used to place the given node in the treeview.
        :type diagram: Diagram
        :type node: AbstractNode
        :rtype: str
        """
        predicate = node.text().replace('\n', '')
        diagram = rstrip(diagram.name, File.Graphol.extension)
        return '{0} ({1} - {2})'.format(predicate, diagram, node.id)

    def iconFor(self, node):
        """
        Returns the icon for the given node.
        :type node:
        """
        if node.type() is Item.AttributeNode:
            return self.iconAttribute
        if node.type() is Item.ConceptNode:
            return self.iconConcept
        if node.type() is Item.IndividualNode:
            if node.identity() is Identity.Individual:
                return self.iconInstance
            if node.identity() is Identity.Value:
                return self.iconValue
        if node.type() is Item.RoleNode:
            return self.iconRole

    def parentFor(self, node):
        """
        Search the parent element of the given node.
        :type node: AbstractNode
        :rtype: QtGui.QStandardItem
        """
        for i in self.model.findItems(self.parentKey(node), QtCore.Qt.MatchExactly):
            if (i.text() == node.text()) or (i.text() == node.text().replace('\n', '')):
                return i
        return None

    @staticmethod
    def parentKey(node):
        """
        Returns the parent key (text) used to place the given node in the treeview.
        :type node: AbstractNode
        :rtype: str
        """
        return node.text().replace('\n', '')

    def sizeHint(self):
        """
        Returns the recommended size for this widget.
        :rtype: QtCore.QSize
        """
        return QtCore.QSize(216, 266)


class UnsatisfiableEntityExplorerView(QtWidgets.QTreeView):
    """
    This class implements the UnsatisfiableEntitiesExplorer tree view.
    """

    def __init__(self, widget):
        """
        Initialize the UnsatisfiableEntitiesExplorer view.
        :type widget: UnsatisfiableEntityExplorerWidget
        """
        super().__init__(widget)
        self.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        self.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setHeaderHidden(True)
        self.setHorizontalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setSelectionMode(QtWidgets.QTreeView.SingleSelection)
        self.setSortingEnabled(True)
        self.setWordWrap(True)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the Session holding the UnsatisfiableEntityExplorer widget.
        :rtype: Session
        """
        return self.widget.session

    @property
    def widget(self):
        """
        Returns the reference to the UnsatisfiableEntityExplorer widget.
        :rtype: UnsatisfiableEntityExplorerWidget
        """
        return self.parent()

    #############################################
    #   EVENTS
    #################################

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the treeview.
        :type mouseEvent: QMouseEvent
        """
        self.clearSelection()
        super().mousePressEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the tree view.
        :type mouseEvent: QMouseEvent
        """
        if mouseEvent.button() == QtCore.Qt.RightButton:
            index = first(self.selectedIndexes())
            if index:
                model = self.model().sourceModel()
                index = self.model().mapToSource(index)
                item = model.itemFromIndex(index)
                node_or_axiom = item.data()

                if node_or_axiom and 'eddy.core.items.nodes' in str(type(node_or_axiom)):
                    self.widget.sgnItemRightClicked.emit(node_or_axiom)
                    menu = self.session.mf.create(node_or_axiom.diagram, [node_or_axiom])
                    menu.exec_(mouseEvent.screenPos().toPoint())

        super().mouseReleaseEvent(mouseEvent)

    #############################################
    #   INTERFACE
    #################################

    def sizeHintForColumn(self, column):
        """
        Returns the size hint for the given column.
        This will make the column of the treeview as wide as the widget that contains the view.
        :type column: int
        :rtype: int
        """
        return max(super().sizeHintForColumn(column), self.viewport().width())
