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
from eddy.core.datatypes.qt import Font
from eddy.core.datatypes.system import File
from eddy.core.functions.misc import first, rstrip
from eddy.core.functions.signals import connect, disconnect
from eddy.core.plugin import AbstractPlugin

from eddy.ui.dock import DockWidget
from eddy.ui.fields import StringField

from jnius import autoclass, cast, detach

class UnsatisfiableEntityExplorerPlugin(AbstractPlugin):
    """
    This plugin provides the UnsatisfiableEntitiesExplorer widget.
    """
    sgnFakeItemAdded = QtCore.pyqtSignal('QGraphicsScene', 'QGraphicsItem')
    sgnFakeExplanationAdded = QtCore.pyqtSignal('QGraphicsItem',list)

    brush = QtGui.QBrush(QtGui.QColor(179, 12, 12, 160))

    #############################################
    #   SLOTS
    #################################

    def checkmatchforOWLtermandnodename(self,OWL_term_1,OWL_term_2):

        #it should not be a complement of a class; i.e. the raw term should start with <

        if (OWL_term_1 is None) or (OWL_term_2 is None):
            return False

        if str(type(OWL_term_1)) == '<class \'list\'>':

            for t1 in OWL_term_1:

                if str(type(OWL_term_2)) == '<class \'list\'>':

                    for t2 in OWL_term_2:
                        if (t1[0] is '<') and (t2[0] is '<'):
                            if t1 == t2:
                                return True

                else:

                    if (t1[0] is '<') and (t2[0] is '<'):
                        if t1 == t2:
                            return True

        if (OWL_term_1[0] is '<') and (OWL_term_2[0] is '<'):
            if OWL_term_1 == OWL_term_2:
                return True

        return False

    def getOWLtermfornode(self,node):

        # looks up the dict for the raw term and then..
        # returns the string portion without the IRI and special characters

        for diag, val_in_diag in self.project.converted_nodes.items():
            for nd in val_in_diag:
                if (val_in_diag[nd] is not None) and (nd is node.id):
                    if str(type(val_in_diag[nd])) == '<class \'list\'>':

                        return_list = []
                        for ele in val_in_diag[nd]:

                            java_class = str(val_in_diag[nd])[2:str(val_in_diag[nd]).index(' ')]
                            cast(autoclass(java_class), ele)

                            return_list.append(ele.toString())

                        return return_list
                    else:
                        java_class = str(val_in_diag[nd])[1:str(val_in_diag[nd]).index(' ')]
                        cast(autoclass(java_class), val_in_diag[nd])

                        return val_in_diag[nd].toString()

        return None

    @QtCore.pyqtSlot()
    def onSessionReady(self):
        """
        Executed whenever the main session completes the startup sequence.
        """
        # CONNECT TO PROJECT SPECIFIC SIGNALS
        widget = self.widget('Unsatisfiable_Entity_Explorer')
        self.debug('Connecting to project: %s', self.project.name)
        #connect(self.project.sgnItemAdded, widget.doAddNode)
        connect(self.project.sgnItemRemoved, widget.doRemoveNode)
        # FILL IN UnsatisfiableEntitiesExplorer WITH DATA
        connect(self.sgnFakeItemAdded, widget.doAddNode)
        connect(self.sgnFakeExplanationAdded, widget.doAddExplanation)

        classes_only_unsatisfiable_nodes_in_diagram = []

        for uc in self.project.unsatisfiable_classes:
            #OWL_term_for_uc = uc
            temp = []

            for p in self.project.nodes():
                OWL_term_for_p = self.getOWLtermfornode(p)
                match = self.checkmatchforOWLtermandnodename(uc,OWL_term_for_p)
                if match is True:
                    temp.append(p)

            classes_only_unsatisfiable_nodes_in_diagram.append(temp)

        unsatisfiable_nodes_in_diagram = []

        for uc in self.project.bottom_data_property:
            #OWL_term_for_uc = uc
            temp = []

            for p in self.project.nodes():
                OWL_term_for_p = self.getOWLtermfornode(p)
                match = self.checkmatchforOWLtermandnodename(uc,OWL_term_for_p)
                if match is True:
                    temp.append(p)

            unsatisfiable_nodes_in_diagram.append(temp)

        for uc in self.project.bottom_object_property:
            #OWL_term_for_uc = uc
            temp = []

            for p in self.project.nodes():
                OWL_term_for_p = self.getOWLtermfornode(p)
                match = self.checkmatchforOWLtermandnodename(uc,OWL_term_for_p)
                if match is True:
                    temp.append(p)

            unsatisfiable_nodes_in_diagram.append(temp)

        self.project.nodes_of_unsatisfiable_entities = unsatisfiable_nodes_in_diagram


        for count,entity in enumerate(classes_only_unsatisfiable_nodes_in_diagram):
            for node in entity:

                self.sgnFakeItemAdded.emit(node.diagram, node)
                node.updateNode(valid=False)

            explanation_for_node = self.project.explanations_for_unsatisfiable_classes[count]
            self.sgnFakeExplanationAdded.emit(node,explanation_for_node)

        for entity in unsatisfiable_nodes_in_diagram:
            for node in entity:
                self.sgnFakeItemAdded.emit(node.diagram, node)
                node.updateNode(valid=False)

        disconnect(self.sgnFakeItemAdded, widget.doAddNode)
        disconnect(self.sgnFakeExplanationAdded, widget.doAddExplanation)

    #############################################
    #   HOOKS
    #################################

    def dispose(self):
        """
        Executed whenever the plugin is going to be destroyed.
        """
        # DISCONNECT FROM CURRENT PROJECT
        widget = self.widget('Unsatisfiable_Entity_Explorer')
        self.debug('Disconnecting from project: %s', self.project.name)
        disconnect(self.project.sgnItemAdded, widget.doAddNode)
        disconnect(self.project.sgnItemRemoved, widget.doRemoveNode)

        # DISCONNECT FROM ACTIVE SESSION
        self.debug('Disconnecting from active session')
        disconnect(self.session.sgnReady, self.onSessionReady)

        # REMOVE DOCKING AREA WIDGET MENU ENTRY
        self.debug('Removing docking area widget toggle from "view" menu')
        menu = self.session.menu('view')
        menu.removeAction(self.widget('Unsatisfiable_Entity_Explorer_dock').toggleViewAction())

        # UNINSTALL THE PALETTE DOCK WIDGET
        self.debug('Uninstalling docking area widget')
        self.session.removeDockWidget(self.widget('Unsatisfiable_Entity_Explorer_dock'))

    def start(self):
        """
        Perform initialization tasks for the plugin.
        """
        # INITIALIZE THE WIDGET
        self.debug('Creating Unsatisfiable_Entity_Explorer widget')
        widget = UnsatisfiableEntityExplorerWidget(self)
        widget.setObjectName('Unsatisfiable_Entity_Explorer')
        self.addWidget(widget)

        # CREATE DOCKING AREA WIDGET
        self.debug('Creating docking area widget')
        widget = DockWidget('Unsatisfiable Entity Explorer', QtGui.QIcon(':icons/18/ic_explore_black'), self.session)
        widget.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea|QtCore.Qt.RightDockWidgetArea)
        widget.setObjectName('Unsatisfiable_Entity_Explorer_dock')
        widget.setWidget(self.widget('Unsatisfiable_Entity_Explorer'))
        self.addWidget(widget)

        # CREATE ENTRY IN VIEW MENU
        self.debug('Creating docking area widget toggle in "view" menu')
        menu = self.session.menu('view')
        menu.addAction(self.widget('Unsatisfiable_Entity_Explorer_dock').toggleViewAction())

        # CONFIGURE SIGNALS
        self.debug('Configuring session specific signals')

        self.onSessionReady()

        # INSTALL DOCKING AREA WIDGET
        self.debug('Installing docking area widget')
        self.session.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.widget('Unsatisfiable_Entity_Explorer_dock'))


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

        connect(self.sgnStringClicked, self.start_explanation_explorer)
        connect(self.sgnStringDoubleClicked, self.start_explanation_explorer)

        connect(self.sgnListClicked, self.start_explanation_explorer)
        connect(self.sgnListDoubleClicked, self.start_explanation_explorer)
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
    @QtCore.pyqtSlot('QGraphicsItem','QStandardItem')
    def doAddExplanation_old(self, node, explanation):

        if explanation is not None:
            exp_to_add = QtGui.QStandardItem(explanation)
            exp_to_add.setData(explanation)
            parent = self.parentFor(node)
            parent.appendRow(exp_to_add)

    @QtCore.pyqtSlot('QGraphicsItem',list)
    def doAddExplanation(self, node, explanation):

        if explanation is not None and len(explanation)>0:
            exp_to_add = QtGui.QStandardItem('<Explanation(s)> \n**(click to open Explanation Explorer)')
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
        if node.type() in {Item.ConceptNode, Item.RoleNode, Item.AttributeNode, Item.IndividualNode}:
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

    def start_explanation_explorer(self, item=None):

        parent = item.parent()

        self.session.pmanager.dispose_and_remove_plugin_from_session(plugin_id='Explanation_explorer')
        self.project.uc_as_input_for_explanation_explorer = parent.text()
        self.session.pmanager.create_add_and_start_plugin('Explanation_explorer')

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
            n = i.child(0).data()
            if node.type() is n.type():
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
        self.setFont(Font('Roboto', 12))
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

