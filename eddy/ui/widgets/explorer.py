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


from PyQt5.QtCore import pyqtSlot, QSortFilterProxyModel, Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPainter, QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import QWidget, QTreeView, QVBoxLayout, QHeaderView, QAction, QMenu
from PyQt5.QtWidgets import QStyleOption, QStyle, QApplication

from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.system import File
from eddy.core.diagram import Diagram
from eddy.core.functions.misc import first, cutR
from eddy.core.functions.signals import connect, emit
from eddy.core.qt import Font

from eddy.lang import gettext as _

from eddy.ui.fields import StringField


class OntologyExplorer(QWidget):
    """
    This class implements the ontology explorer used to list ontology predicates.
    """
    sgnItemClicked = pyqtSignal('QGraphicsItem')
    sgnItemDoubleClicked = pyqtSignal('QGraphicsItem')
    sgnItemRightClicked = pyqtSignal('QGraphicsItem')

    def __init__(self, parent):
        """
        Initialize the ontology explorer.
        :type parent: MainWindow
        """
        super().__init__(parent)
        self.mainwindow = parent

        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(216)

        self.iconA = QIcon(':/icons/treeview-predicate-attribute')
        self.iconC = QIcon(':/icons/treeview-predicate-concept')
        self.iconI = QIcon(':/icons/treeview-predicate-instance')
        self.iconRoot = QIcon(':/icons/treeview-predicate-role')
        self.iconV = QIcon(':/icons/treeview-predicate-value')

        self.search = StringField(self)
        self.search.setAcceptDrops(False)
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText(_('ONTO_EXPLORER_SEARCH_PLACEHOLDER'))
        self.search.setFixedHeight(30)
        self.model = QStandardItemModel(self)
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setDynamicSortFilter(False)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setSortCaseSensitivity(Qt.CaseSensitive)
        self.proxy.setSourceModel(self.model)
        self.ontoview = OntologyExplorerView(self)
        self.ontoview.setModel(self.proxy)
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.search)
        self.mainLayout.addWidget(self.ontoview)

        connect(self.ontoview.doubleClicked, self.onItemDoubleClicked)
        connect(self.ontoview.pressed, self.onItemPressed)
        connect(self.search.textChanged, self.doFilterItem)

    #############################################
    #   EVENTS
    #################################

    def paintEvent(self, paintEvent):
        """
        This is needed for the widget to pick the stylesheet.
        :type paintEvent: QPaintEvent
        """
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def doAddNode(self, diagram, node):
        """
        Add a node in the tree view.
        :type diagram: QGraphicsScene
        :type node: AbstractItem
        """
        if node.type() in {Item.ConceptNode, Item.RoleNode, Item.AttributeNode, Item.IndividualNode}:
            parent = self.parentFor(node)
            if not parent:
                parent = QStandardItem(self.parentKey(node))
                parent.setIcon(self.iconFor(node))
                self.model.appendRow(parent)
                self.proxy.sort(0, Qt.AscendingOrder)
            child = QStandardItem(self.childKey(diagram, node))
            child.setData(node)
            parent.appendRow(child)
            self.proxy.sort(0, Qt.AscendingOrder)

    @pyqtSlot(str)
    def doFilterItem(self, key):
        """
        Executed when the search box is filled with data.
        :type key: str
        """
        self.proxy.setFilterFixedString(key)
        self.proxy.sort(Qt.AscendingOrder)

    @pyqtSlot('QGraphicsScene', 'QGraphicsItem')
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

    @pyqtSlot('QModelIndex')
    def onItemDoubleClicked(self, index):
        """
        Executed when an item in the treeview is double clicked.
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QApplication.mouseButtons() & Qt.LeftButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item and item.data():
                emit(self.sgnItemDoubleClicked['QGraphicsItem'], item.data())

    @pyqtSlot('QModelIndex')
    def onItemPressed(self, index):
        """
        Executed when an item in the treeview is clicked.
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QApplication.mouseButtons() & Qt.LeftButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item and item.data():
                emit(self.sgnItemClicked['QGraphicsItem'], item.data())

    #############################################
    #   INTERFACE
    #################################

    def browse(self, project):
        """
        Set the ontology explorer to browse the given project.
        :type project: Project
        """
        for node in project.nodes():
            self.doAddNode(node.diagram, node)

        header = self.ontoview.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

        connect(project.sgnItemAdded, self.doAddNode)
        connect(project.sgnItemRemoved, self.doRemoveNode)

    def childFor(self, parent, diagram, node):
        """
        Search the item representing this node among parent children.
        :type parent: QStandardItem
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
        diagram = cutR(diagram.name, File.Graphol.extension)
        return '{0} ({1} - {2})'.format(predicate, diagram, node.id)

    def iconFor(self, node):
        """
        Returns the icon for the given node.
        :type node:
        """
        if node.type() is Item.AttributeNode:
            return self.iconA
        if node.type() is Item.ConceptNode:
            return self.iconC
        if node.type() is Item.IndividualNode:
            if node.identity is Identity.Instance:
                return self.iconI
            if node.identity is Identity.Value:
                return self.iconV
        if node.type() is Item.RoleNode:
            return self.iconRoot

    def parentFor(self, node):
        """
        Search the parent element of the given node.
        :type node: AbstractNode
        :rtype: QStandardItem
        """
        for i in self.model.findItems(self.parentKey(node), Qt.MatchExactly):
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
        :rtype: QSize
        """
        return QSize(216, 266)


class OntologyExplorerView(QTreeView):
    """
    This class implements the ontology explorer tree view.
    """
    def __init__(self, parent):
        """
        Initialize the ontology explorer view.
        :type parent: QWidget
        """
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.PreventContextMenu)
        self.setEditTriggers(QTreeView.NoEditTriggers)
        self.setFont(Font('Arial', 12))
        self.setFocusPolicy(Qt.NoFocus)
        self.setHeaderHidden(True)
        self.setHorizontalScrollMode(QTreeView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSelectionMode(QTreeView.SingleSelection)
        self.setSortingEnabled(True)
        self.setWordWrap(True)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def widget(self):
        """
        Returns the reference to the ProjectExporer widget.
        :rtype: ProjectExplorer
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
        if mouseEvent.button() == Qt.RightButton:
            index = first(self.selectedIndexes())
            if index:
                model = self.model().sourceModel()
                index = self.model().mapToSource(index)
                item = model.itemFromIndex(index)
                node = item.data()
                if node:
                    emit(self.widget.sgnItemRightClicked['QGraphicsItem'], node)
                    menu = self.widget.mainwindow.menuFactory.create(self.widget.mainwindow, node.diagram, node)
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


class ProjectExplorer(QWidget):
    """
    This class implements the project explorer used to display the project structure.
    """
    sgnItemClicked = pyqtSignal([str], ['QGraphicsScene'])
    sgnItemDoubleClicked = pyqtSignal([str], ['QGraphicsScene'])

    def __init__(self, parent):
        """
        Initialize the project explorer.
        :type parent: MainWindow
        """
        super().__init__(parent)
        self.mainwindow = parent

        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(216)

        self.arial12r = Font('Arial', 12)
        self.arial12b = Font('Arial', 12)
        self.arial12b.setBold(True)

        self.iconRoot = QIcon(':/icons/treeview-directory')
        self.iconBlank = QIcon(':/icons/treeview-document-blank')
        self.iconGraphol = QIcon(':/icons/treeview-document-graphol')
        self.iconOwl = QIcon(':/icons/treeview-document-owl')
        self.iconDelete = QIcon(':/icons/delete')
        
        self.actionDeleteDiagram = QAction(_('ACTION_DELETE_CONFIRM_N'), self)
        self.actionDeleteDiagram.setIcon(self.iconDelete)
        connect(self.actionDeleteDiagram.triggered, self.mainwindow.doRemoveDiagram)
        
        self.root = QStandardItem()
        self.root.setFlags(self.root.flags() & ~Qt.ItemIsEditable)
        self.root.setFont(self.arial12b)
        self.root.setIcon(self.iconRoot)

        self.model = QStandardItemModel(self)
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setDynamicSortFilter(False)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setSortCaseSensitivity(Qt.CaseSensitive)
        self.proxy.setSourceModel(self.model)
        self.projectview = ProjectExplorerView(self)
        self.projectview.setModel(self.proxy)
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.projectview)

        header = self.projectview.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

        connect(self.projectview.doubleClicked, self.onItemDoubleClicked)
        connect(self.projectview.pressed, self.onItemPressed)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot('QGraphicsScene')
    def doAddDiagram(self, diagram):
        """
        Add a diagram in the treeview.
        :type diagram: Diagram
        """
        if not self.findItem(diagram.name):
            item = QStandardItem(diagram.name)
            item.setData(diagram)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setFont(self.arial12r)
            item.setIcon(self.iconGraphol)
            self.root.appendRow(item)
            self.proxy.sort(0, Qt.AscendingOrder)

    @pyqtSlot('QGraphicsScene')
    def doRemoveDiagram(self, diagram):
        """
        Remove a diagram from the treeview.
        :type diagram: Diagram
        """
        item = self.findItem(diagram.name)
        if item:
            self.root.removeRow(item.index().row())

    @pyqtSlot('QModelIndex')
    def onItemDoubleClicked(self, index):
        """
        Executed when an item in the treeview is double clicked.
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QApplication.mouseButtons() & Qt.LeftButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item and item.data():
                emit(self.sgnItemDoubleClicked['QGraphicsScene'], item.data())

    @pyqtSlot('QModelIndex')
    def onItemPressed(self, index):
        """
        Executed when an item in the treeview is clicked.
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QApplication.mouseButtons() & Qt.LeftButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item and item.data():
                emit(self.sgnItemClicked['QGraphicsScene'], item.data())

    #############################################
    #   EVENTS
    #################################

    def paintEvent(self, paintEvent):
        """
        This is needed for the widget to pick the stylesheet.
        :type paintEvent: QPaintEvent
        """
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        style = self.style()
        style.drawPrimitive(QStyle.PE_Widget, option, painter, self)

    #############################################
    #   INTERFACE
    #################################

    def browse(self, project):
        """
        Set the project explorer to browse the given project.
        :type project: Project
        """
        self.model.clear()
        self.model.appendRow(self.root)
        self.root.setText(project.name)

        for diagram in project.diagrams():
            self.doAddDiagram(diagram)

        sindex = self.root.index()
        pindex = self.proxy.mapFromSource(sindex)
        self.projectview.expand(pindex)

        connect(project.sgnDiagramAdded, self.doAddDiagram)
        connect(project.sgnDiagramRemoved, self.doRemoveDiagram)

    def findItem(self, name):
        """
        Find the item with the given name inside the root element.
        :type name: str
        """
        for i in range(self.root.rowCount()):
            item = self.root.child(i)
            if item.text() == name:
                return item
        return None

    def sizeHint(self):
        """
        Returns the recommended size for this widget.
        :rtype: QSize
        """
        return QSize(216, 266)


class ProjectExplorerView(QTreeView):
    """
    This class implements the project explorer tree view.
    """
    def __init__(self, parent):
        """
        Initialize the project explorer view.
        :type parent: QWidget
        """
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.PreventContextMenu)
        self.setEditTriggers(QTreeView.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        self.setHeaderHidden(True)
        self.setHorizontalScrollMode(QTreeView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSelectionMode(QTreeView.SingleSelection)
        self.setSortingEnabled(True)
        self.setWordWrap(True)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def widget(self):
        """
        Returns the reference to the ProjectExporer widget.
        :rtype: ProjectExplorer
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
        if mouseEvent.button() == Qt.RightButton:
            index = first(self.selectedIndexes())
            if index:
                model = self.model().sourceModel()
                index = self.model().mapToSource(index)
                item = model.itemFromIndex(index)
                diagram = item.data()
                if diagram:
                    menu = QMenu()
                    menu.addAction(self.widget.actionDeleteDiagram)
                    self.widget.actionDeleteDiagram.setData(diagram)
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