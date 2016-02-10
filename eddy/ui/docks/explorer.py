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


from PyQt5.QtCore import pyqtSlot, QSortFilterProxyModel, Qt
from PyQt5.QtGui import QPainter, QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import QWidget, QTreeView, QVBoxLayout
from PyQt5.QtWidgets import QStyleOption, QStyle

from eddy.core.datatypes import Item, Identity
from eddy.core.functions import disconnect, connect


class Explorer(QWidget):
    """
    This class implements the diagram predicate node explorer.
    """
    def __init__(self, *args):
        """
        Initialize the Explorer.
        """
        super().__init__(*args)
        self.expanded = {}
        self.mainview = None
        self.iconA = QIcon(':/icons/treeview-attribute')
        self.iconC = QIcon(':/icons/treeview-concept')
        self.iconD = QIcon(':/icons/treeview-datarange')
        self.iconI = QIcon(':/icons/treeview-individual')
        self.iconL = QIcon(':/icons/treeview-literal')
        self.iconR = QIcon(':/icons/treeview-role')
        self.model = QStandardItemModel(self)
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setSourceModel(self.model)
        self.view = ExplorerView(self)
        self.view.setModel(self.model)
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.view)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedWidth(216)

        connect(self.view.doubleClicked, self.itemDoubleClicked)
        connect(self.view.clicked, self.itemClicked)
        connect(self.view.collapsed, self.itemCollapsed)
        connect(self.view.expanded, self.itemExpanded)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

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

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot('QModelIndex')
    def itemClicked(self, index):
        """
        Executed when an item in the tree view is clicked.
        :type index: QModelIndex
        """
        item = self.model.itemFromIndex(index)
        node = item.data()
        if node:
            self.selectNode(node)

    @pyqtSlot('QModelIndex')
    def itemCollapsed(self, index):
        """
        Executed when an item in the tree view is collapsed.
        :type index: QModelIndex
        """
        if self.mainview:
            if self.mainview in self.expanded:
                item = self.model.itemFromIndex(index)
                expanded = self.expanded[self.mainview]
                expanded.remove(item.text())

    @pyqtSlot('QModelIndex')
    def itemDoubleClicked(self, index):
        """
        Executed when an item in the tree view is double clicked.
        :type index: QModelIndex
        """
        item = self.model.itemFromIndex(index)
        node = item.data()
        if node:
            self.selectNode(node)
            self.focusNode(node)

    @pyqtSlot('QModelIndex')
    def itemExpanded(self, index):
        """
        Executed when an item in the tree view is expanded.
        :type index: QModelIndex
        """
        if self.mainview:
            item = self.model.itemFromIndex(index)
            if self.mainview not in self.expanded:
                self.expanded[self.mainview] = set()
            expanded = self.expanded[self.mainview]
            expanded.add(item.text())

    @pyqtSlot('QGraphicsItem')
    def insert(self, item):
        """
        Insert a node in the tree view.
        :type item: AbstractItem
        """
        if item.node and item.predicate:
            parent = next(iter(self.model.findItems(ParentItem.key(item))), None)
            if not parent:
                parent = ParentItem(item)
                parent.setIcon(self.iconFor(item))
                self.model.appendRow(parent)
                self.model.sort(0)
            child = ChildItem(item)
            child.setData(item)
            parent.appendRow(child)
            parent.sortChildren(0)

    @pyqtSlot('QGraphicsItem')
    def remove(self, item):
        """
        Remove a node from the tree view.
        :type item: AbstractItem
        """
        if item.node and item.predicate:
            parent = next(iter(self.model.findItems(ParentItem.key(item))), None)
            if parent:
                compound = ChildItem.key(item)
                for i in range(parent.rowCount()):
                    child = parent.child(i)
                    if child.text() == compound:
                        parent.removeRow(i)
                        break
                if not parent.rowCount():
                    self.model.removeRow(parent.index().row())

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def clear(self):
        """
        Clear the widget from inspecting the current view.
        """
        if self.mainview:

            try:
                scene = self.mainview.scene()
                # Make sure to disconnect only the signals connected to the slots provided by this
                # widget otherwise we will experiences bugs when the MainWindow goes out of focus: for
                # more details on the matter read: https://github.com/danielepantaleone/eddy/issues/15
                disconnect(scene.index.itemAdded, self.insert)
                disconnect(scene.index.itemRemoved, self.remove)
            except RuntimeError:
                pass
            finally:
                self.mainview = None

        self.model.clear()

    def flush(self, view):
        """
        Flush the cache of the given mainview
        :type view: MainView
        """
        self.expanded.pop(view, None)

    def iconFor(self, node):
        """
        Returns the icon for the given node.
        :type node:
        """
        if node.item is Item.AttributeNode:
            return self.iconA
        if node.item is Item.ConceptNode:
            return self.iconC
        if node.item is Item.ValueDomainNode:
            return self.iconD
        if node.item is Item.ValueRestrictionNode:
            return self.iconD
        if node.item is Item.IndividualNode:
            if node.identity is Identity.Individual:
                return self.iconI
            if node.identity is Identity.Literal:
                return self.iconL
        if node.item is Item.RoleNode:
            return self.iconR

    def focusNode(self, node):
        """
        Focus the given node in the main view.
        :type node: AbstractNode
        """
        if self.mainview:
            self.mainview.centerOn(node)

    def selectNode(self, node):
        """
        Select the given node in the main view.
        :type node: AbstractNode
        """
        if self.mainview:
            scene = self.mainview.scene()
            scene.clearSelection()
            node.setSelected(True)

    def setView(self, view):
        """
        Set the widget to inspect the given view.
        :type view: QGraphicsView
        """
        self.clear()
        self.mainview = view

        if self.mainview:
            scene = self.mainview.scene()
            connect(scene.index.itemAdded, self.insert)
            connect(scene.index.itemRemoved, self.remove)
            for item in scene.index.nodes():
                self.insert(item)

            if self.mainview in self.expanded:
                expanded = self.expanded[self.mainview]
                for i in range(self.model.rowCount()):
                    item = self.model.item(i)
                    self.view.setExpanded(self.model.indexFromItem(item), item.text() in expanded)


class ExplorerView(QTreeView):
    """
    This class implements the explorer tree view.
    """
    def __init__(self, parent=None):
        """
        Initialize the explorer view.
        :type parent: QWidget
        """
        super().__init__(parent)
        self.setAnimated(True)
        self.setEditTriggers(QTreeView.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        self.setHeaderHidden(True)
        self.setSelectionMode(QTreeView.SingleSelection)
        self.setSortingEnabled(True)


class ParentItem(QStandardItem):
    """
    This class implements the single predicated section of the treeview.
    """
    def __init__(self, node):
        """
        Initialize the predicate section.
        :type node: AbstractNode
        """
        super().__init__(ParentItem.key(node))
        self.setFlags(self.flags() & ~Qt.ItemIsEditable)

    @classmethod
    def key(cls, node):
        """
        Returns the key used to index the given node.
        :type node: AbstractNode
        :rtype: str
        """
        return node.text()


class ChildItem(QStandardItem):
    """
    This class implements the single node of the treeview.
    """
    def __init__(self, node):
        """
        Initialize the node item.
        :type node: AbstractNode
        """
        super().__init__(ChildItem.key(node))

    @classmethod
    def key(cls, node):
        """
        Returns the key used to index the given node.
        :type node: AbstractNode
        :rtype: str
        """
        return '{}:{}'.format(node.text(), node.id)