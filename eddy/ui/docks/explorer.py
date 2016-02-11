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
from PyQt5.QtWidgets import QWidget, QTreeView, QVBoxLayout, QHeaderView
from PyQt5.QtWidgets import QStyleOption, QStyle

from eddy.core.datatypes import Item, Identity
from eddy.core.functions import disconnect, connect

from eddy.ui.fields import StringField


class Explorer(QWidget):
    """
    This class implements the diagram predicate node explorer.
    """
    def __init__(self, mainwindow):
        """
        Initialize the Explorer.
        :type mainwindow: MainWindow
        """
        super().__init__(mainwindow)
        self.expanded = {}
        self.searched = {}
        self.scrolled = {}
        self.mainview = None
        self.iconA = QIcon(':/icons/treeview-attribute')
        self.iconC = QIcon(':/icons/treeview-concept')
        self.iconD = QIcon(':/icons/treeview-datarange')
        self.iconI = QIcon(':/icons/treeview-individual')
        self.iconL = QIcon(':/icons/treeview-literal')
        self.iconR = QIcon(':/icons/treeview-role')
        self.search = StringField(self)
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText('Search...')
        self.search.setFixedHeight(30)
        self.model = QStandardItemModel(self)
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setDynamicSortFilter(False)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setSortCaseSensitivity(Qt.CaseSensitive)
        self.proxy.setSourceModel(self.model)
        self.view = ExplorerView(mainwindow, self)
        self.view.setModel(self.proxy)
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.search)
        self.mainLayout.addWidget(self.view)
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(216)

        connect(self.view.doubleClicked, self.itemDoubleClicked)
        connect(self.view.pressed, self.itemPressed)
        connect(self.view.collapsed, self.itemCollapsed)
        connect(self.view.expanded, self.itemExpanded)
        connect(self.search.textChanged, self.filterItem)

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

    @pyqtSlot(str)
    def filterItem(self, key):
        """
        Executed when the search box is filled with data.
        :type key: str
        """
        if self.mainview:
            self.proxy.setFilterFixedString(key)
            self.proxy.sort(Qt.AscendingOrder)
            self.searched[self.mainview] = key

    @pyqtSlot('QModelIndex')
    def itemCollapsed(self, index):
        """
        Executed when an item in the tree view is collapsed.
        :type index: QModelIndex
        """
        if self.mainview:
            if self.mainview in self.expanded:
                item = self.model.itemFromIndex(self.proxy.mapToSource(index))
                expanded = self.expanded[self.mainview]
                expanded.remove(item.text())

    @pyqtSlot('QModelIndex')
    def itemDoubleClicked(self, index):
        """
        Executed when an item in the tree view is double clicked.
        :type index: QModelIndex
        """
        item = self.model.itemFromIndex(self.proxy.mapToSource(index))
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
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if self.mainview not in self.expanded:
                self.expanded[self.mainview] = set()
            expanded = self.expanded[self.mainview]
            expanded.add(item.text())

    @pyqtSlot('QModelIndex')
    def itemPressed(self, index):
        """
        Executed when an item in the tree view is clicked.
        :type index: QModelIndex
        """
        item = self.model.itemFromIndex(self.proxy.mapToSource(index))
        node = item.data()
        if node:
            self.selectNode(node)

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
                self.proxy.sort(Qt.AscendingOrder)
            child = ChildItem(item)
            child.setData(item)
            parent.appendRow(child)
            parent.sortChildren(Qt.AscendingOrder)

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

            # Backup current scoll index.
            rect = self.rect()
            item = self.model.itemFromIndex(self.proxy.mapToSource(self.view.indexAt(rect.topLeft())))
            if item:
                node = item.data()
                key = ParentItem.key(node) if node else item.text()
                self.scrolled[self.mainview] = key
            else:
                self.scrolled.pop(self.mainview, None)

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
        Flush the cache of the given mainview.
        :type view: MainView
        """
        self.expanded.pop(view, None)
        self.searched.pop(view, None)
        self.scrolled.pop(view, None)

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
                    index = self.proxy.mapFromSource(self.model.indexFromItem(item))
                    self.view.setExpanded(index, item.text() in expanded)

            key = ''
            if self.mainview in self.searched:
                key = self.searched[self.mainview]
            self.search.setText(key)

            if self.mainview in self.scrolled:
                rect = self.rect()
                item = next(iter(self.model.findItems(self.scrolled[self.mainview])), None)
                for i in range(self.model.rowCount()):
                    self.view.scrollTo(self.proxy.mapFromSource(self.model.indexFromItem(self.model.item(i))))
                    index = self.proxy.mapToSource(self.view.indexAt(rect.topLeft()))
                    if self.model.itemFromIndex(index) is item:
                        break


class ExplorerView(QTreeView):
    """
    This class implements the explorer tree view.
    """
    def __init__(self, mainwindow, parent=None):
        """
        Initialize the explorer view.
        :type mainwindow: MainWindow
        :type parent: QWidget
        """
        super().__init__(parent)
        self.setAnimated(True)
        self.setContextMenuPolicy(Qt.PreventContextMenu)
        self.setEditTriggers(QTreeView.NoEditTriggers)
        self.setFocusPolicy(Qt.NoFocus)
        self.setHeaderHidden(True)
        self.setHorizontalScrollMode(QTreeView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSelectionMode(QTreeView.SingleSelection)
        self.setSortingEnabled(True)
        self.setWordWrap(True)
        self.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.header().setStretchLastSection(False)
        self.mainwindow = mainwindow

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the tree view
        :type mouseEvent: QMouseEvent
        """
        self.clearSelection()
        # We call super after clearing the selection so that we click off an
        # item it will be deselected by clearSelection here above and the default
        # mousePressEvent will not evit the clicked signal that will select the item.
        super().mousePressEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the tree view
        :type mouseEvent: QMouseEvent
        """
        if mouseEvent.button() == Qt.RightButton:
            index = next(iter(self.selectedIndexes()), None)
            if index:
                model = self.model().sourceModel()
                index = self.model().mapToSource(index)
                item = model.itemFromIndex(index)
                node = item.data()
                if node:
                    menu = self.mainwindow.menuFactory.create(self.mainwindow, node.scene(), node)
                    menu.exec_(mouseEvent.screenPos().toPoint())
        super().mouseReleaseEvent(mouseEvent)


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
        return node.text().replace('\n', '')


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
        return '{} ({})'.format(node.text().replace('\n', ''), node.id)