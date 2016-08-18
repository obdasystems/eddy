# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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


from PyQt5.QtCore import Qt, QSize, QSortFilterProxyModel
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtGui import QIcon, QPainter
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QApplication, QHeaderView, QTreeView
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QStyleOption
from PyQt5.QtWidgets import QStyle, QMenu

from verlib import NormalizedVersion

from eddy.core.datatypes.qt import Font
from eddy.core.functions.misc import first
from eddy.core.functions.signals import connect, disconnect
from eddy.core.plugin import AbstractPlugin

from eddy.ui.dock import DockWidget


class ProjectExplorer(AbstractPlugin):
    """
    This plugin provides the Project Explorer widget.
    """
    def __init__(self, session):
        """
        Initialize the plugin.
        :type session: session
        """
        super().__init__(session)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def onSessionReady(self):
        """
        Executed whenever the main session completes the startup sequence.
        """
        widget = self.widget('project_explorer')
        self.debug('Connecting to project: %s', self.project.name)
        connect(self.project.sgnDiagramAdded, widget.doAddDiagram)
        connect(self.project.sgnDiagramRemoved, widget.doRemoveDiagram)
        widget.setProject(self.project)

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def name(cls):
        """
        Returns the readable name of the plugin.
        :rtype: str
        """
        return 'Project Explorer'

    def objectName(self):
        """
        Returns the system name of the plugin.
        :rtype: str
        """
        return 'project_explorer'

    def startup(self):
        """
        Perform initialization tasks for the plugin.
        """
        # INITIALIZE THE WIDGET
        self.debug('Creating project explorer widget')
        widget = ProjectExplorerWidget(self)
        widget.setObjectName('project_explorer')
        self.addWidget(widget)

        # CREATE DOCKING AREA WIDGET
        self.debug('Creating docking area widget')
        widget = DockWidget('Project Explorer', QIcon(':icons/18/ic_storage_black'), self.session)
        widget.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        widget.setObjectName('project_explorer_dock')
        widget.setWidget(self.widget('project_explorer'))
        self.addWidget(widget)

        # CREATE ENTRY IN VIEW MENU
        self.debug('Creating docking area widget toggle in "view" menu')
        menu = self.session.menu('view')
        menu.addAction(self.widget('project_explorer_dock').toggleViewAction())

        # CONFIGURE SIGNALS/SLOTS
        self.debug('Configuring session specific signals')
        connect(self.session.sgnReady, self.onSessionReady)

        # INSTALL DOCKING AREA WIDGET
        self.debug('Installing docking area widget')
        self.session.addDockWidget(Qt.LeftDockWidgetArea, self.widget('project_explorer_dock'))

        super().startup()

    @classmethod
    def version(cls):
        """
        Returns the version of the plugin.
        :rtype: NormalizedVersion
        """
        return NormalizedVersion('0.1')


class ProjectExplorerWidget(QWidget):
    """
    This class implements the project explorer used to display the project structure.
    """
    sgnFakeDiagramAdded = pyqtSignal('QGraphicsScene')
    sgnItemClicked = pyqtSignal('QGraphicsScene')
    sgnItemDoubleClicked = pyqtSignal('QGraphicsScene')

    def __init__(self, plugin):
        """
        Initialize the project explorer.
        :type plugin: ProjectExplorer
        """
        super().__init__(plugin.session)

        self.plugin = plugin
        self.project = None

        self.arial12r = Font('Arial', 12)
        self.arial12b = Font('Arial', 12)
        self.arial12b.setBold(True)

        self.iconRoot = QIcon(':/icons/18/ic_folder_open_black')
        self.iconBlank = QIcon(':/icons/18/ic_document_blank')
        self.iconGraphol = QIcon(':/icons/18/ic_document_graphol')
        self.iconOwl = QIcon(':/icons/18/ic_document_owl')

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

        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumWidth(216)

        header = self.projectview.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

        connect(self.projectview.doubleClicked, self.onItemDoubleClicked)
        connect(self.projectview.pressed, self.onItemPressed)
        connect(self.sgnItemDoubleClicked, self.session.doFocusDiagram)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the active session.
        :rtype: Session
        """
        return self.plugin.parent()

    #############################################
    #   WIDGET INTERNAL SLOTS
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
                self.sgnItemDoubleClicked.emit(item.data())

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
                self.sgnItemClicked.emit(item.data())

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

    def setProject(self, project):
        """
        Set the project explorer to browse the given project.
        :type project: Project
        """
        self.model.clear()
        self.model.appendRow(self.root)
        self.root.setText(project.name)
        connect(self.sgnFakeDiagramAdded, self.doAddDiagram)
        for diagram in project.diagrams():
            self.sgnFakeDiagramAdded.emit(diagram)
        disconnect(self.sgnFakeDiagramAdded)
        sindex = self.root.index()
        pindex = self.proxy.mapFromSource(sindex)
        self.projectview.expand(pindex)

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
    def __init__(self, widget):
        """
        Initialize the project explorer view.
        :type widget: ProjectExplorerWidget
        """
        super().__init__(widget)
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
    def session(self):
        """
        Returns the reference to the Session holding the ProjectExplorer widget.
        :rtype: Session
        """
        return self.widget.session

    @property
    def widget(self):
        """
        Returns the reference to the ProjectExplorer widget.
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
                    menu.addAction(self.session.action('new_diagram'))
                    menu.addSeparator()
                    menu.addAction(self.session.action('rename_diagram'))
                    menu.addAction(self.session.action('remove_diagram'))
                    menu.addSeparator()
                    menu.addAction(self.session.action('diagram_properties'))
                    self.session.action('rename_diagram').setData(diagram)
                    self.session.action('remove_diagram').setData(diagram)
                    self.session.action('diagram_properties').setData(diagram)
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