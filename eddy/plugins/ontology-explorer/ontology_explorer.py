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
import typing

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.system import File
from eddy.core.datatypes.annotation import Status
from eddy.core.functions.misc import first, rstrip
from eddy.core.functions.signals import connect, disconnect
from eddy.core.items.nodes.common.base import OntologyEntityNode, AbstractNode, OntologyEntityResizableNode
from eddy.core.owl import IRIRender, AnnotationAssertion, IRI, ImportedOntology
from eddy.core.plugin import AbstractPlugin

from eddy.ui.dock import DockWidget
from eddy.ui.fields import StringField


class OntologyExplorerPlugin(AbstractPlugin):
    """
    This plugin provides the Ontology Explorer widget.
    """
    sgnFakeItemAdded = QtCore.pyqtSignal('QGraphicsScene', 'QGraphicsItem')
    sgnFakeImportedOntologyAdded = QtCore.pyqtSignal(ImportedOntology)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onSessionReady(self):
        """
        Executed whenever the main session completes the startup sequence.
        """
        # CONNECT TO PROJECT SPECIFIC SIGNALS
        widget = self.widget('ontology_explorer')
        self.debug('Connecting to project: %s', self.project.name)
        connect(self.project.sgnItemAdded, widget.doAddNode)
        connect(self.project.sgnImportedOntologyAdded, widget.onImportedOntologyAdded)
        connect(self.project.sgnImportedOntologyLoaded, widget.onImportedOntologyAdded)
        connect(self.project.sgnItemRemoved, widget.doRemoveNode)
        connect(self.project.sgnImportedOntologyRemoved, widget.onImportedOntologyRemoved)
        #connect(self.project.sgnUpdated, widget.doResetReasonerHighlight)
        connect(self.session.sgnUnsatisfiableClass, widget.onUnsatisfiableClass)
        connect(self.session.sgnUnsatisfiableObjectProperty, widget.onUnsatisfiableObjectProperty)
        connect(self.session.sgnUnsatisfiableDataProperty, widget.onUnsatisfiableDataProperty)
        connect(self.session.sgnConsistencyCheckReset, widget.doResetReasonerHighlight)

        # FILL IN ONTOLOGY EXPLORER WITH DATA
        connect(self.sgnFakeImportedOntologyAdded, widget.onImportedOntologyAdded)
        for impOnt in self.project.importedOntologies:
            self.sgnFakeImportedOntologyAdded.emit(impOnt)
        connect(self.sgnFakeItemAdded, widget.doAddNode)
        for node in self.project.nodes():
            self.sgnFakeItemAdded.emit(node.diagram, node)
        widget.doFilterItem('')
        disconnect(self.sgnFakeItemAdded, widget.doAddNode)
        disconnect(self.sgnFakeImportedOntologyAdded, widget.onImportedOntologyAdded)

    #############################################
    #   HOOKS
    #################################

    def dispose(self):
        """
        Executed whenever the plugin is going to be destroyed.
        """
        # DISCONNECT FROM CURRENT PROJECT
        widget = self.widget('ontology_explorer')
        self.debug('Disconnecting from project: %s', self.project.name)
        disconnect(self.project.sgnItemAdded, widget.doAddNode)
        disconnect(self.project.sgnItemRemoved, widget.doRemoveNode)
        disconnect(self.project.sgnImportedOntologyAdded, widget.onImportedOntologyAdded)
        disconnect(self.project.sgnImportedOntologyLoaded, widget.onImportedOntologyAdded)
        disconnect(self.project.sgnImportedOntologyRemoved, widget.onImportedOntologyRemoved)

        # DISCONNECT FROM ACTIVE SESSION
        self.debug('Disconnecting from active session')
        disconnect(self.session.sgnReady, self.onSessionReady)
        disconnect(self.session.sgnUnsatisfiableClass, widget.onUnsatisfiableClass)
        disconnect(self.session.sgnUnsatisfiableObjectProperty, widget.onUnsatisfiableObjectProperty)
        disconnect(self.session.sgnUnsatisfiableDataProperty, widget.onUnsatisfiableDataProperty)

        # REMOVE DOCKING AREA WIDGET MENU ENTRY
        self.debug('Removing docking area widget toggle from "view" menu')
        menu = self.session.menu('view')
        menu.removeAction(self.widget('ontology_explorer_dock').toggleViewAction())

        # UNINSTALL THE PALETTE DOCK WIDGET
        self.debug('Uninstalling docking area widget')
        self.session.removeDockWidget(self.widget('ontology_explorer_dock'))

    # noinspection PyArgumentList
    def start(self):
        """
        Perform initialization tasks for the plugin.
        """
        # INITIALIZE THE WIDGET
        self.debug('Creating ontology explorer widget')
        widget = OntologyExplorerWidget(self)
        widget.setObjectName('ontology_explorer')
        self.addWidget(widget)

        # CREATE TOGGLE ACTIONS
        self.debug('Creating explorer toggle actions')
        group = QtWidgets.QActionGroup(self, objectName='explorer_item_toggle')
        group.setExclusive(False)
        for item in widget.items:
            action = QtWidgets.QAction(item.realName.title(), group, objectName=item.name, checkable=True)
            action.setChecked(True)
            action.setData(item)
            connect(action.triggered, widget.onMenuButtonClicked)
            group.addAction(action)
        self.addAction(group)

        group = QtWidgets.QActionGroup(self, objectName='explorer_status_toggle')
        group.setExclusive(False)
        for status in widget.status:
            action = QtWidgets.QAction(status.value if status.value else 'Default', group, objectName=status.name, checkable=True)
            action.setChecked(True)
            action.setData(status)
            connect(action.triggered, widget.onMenuButtonClicked)
            group.addAction(action)
        self.addAction(group)

        # CREATE TOGGLE MENU
        self.debug('Creating explorer toggle menu')
        menu = QtWidgets.QMenu(objectName='explorer_toggle')
        menu.addSection('Items')
        menu.addActions(self.action('explorer_item_toggle').actions())
        menu.addSection('Description')
        menu.addActions(self.action('explorer_status_toggle').actions())
        self.addMenu(menu)

        # CREATE CONTROL WIDGET
        self.debug('Creating explorer toggle control widget')
        button = QtWidgets.QToolButton(objectName='explorer_toggle')
        button.setIcon(QtGui.QIcon(':/icons/18/ic_settings_black'))
        button.setContentsMargins(0, 0, 0, 0)
        button.setFixedSize(18, 18)
        button.setFocusPolicy(QtCore.Qt.NoFocus)
        button.setMenu(self.menu('explorer_toggle'))
        button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.addWidget(button)

        # CREATE DOCKING AREA WIDGET
        self.debug('Creating docking area widget')
        widget = DockWidget('Ontology Explorer', QtGui.QIcon(':icons/18/ic_explore_black'), self.session)
        widget.addTitleBarButton(self.widget('explorer_toggle'))
        widget.installEventFilter(self)
        widget.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea | QtCore.Qt.BottomDockWidgetArea)
        widget.setObjectName('ontology_explorer_dock')
        widget.setWidget(self.widget('ontology_explorer'))
        self.addWidget(widget)

        # CREATE SHORTCUTS
        action = widget.toggleViewAction()
        action.setParent(self.session)
        action.setShortcut(QtGui.QKeySequence('Alt+4'))

        # CREATE ENTRY IN VIEW MENU
        self.debug('Creating docking area widget toggle in "view" menu')
        menu = self.session.menu('view')
        menu.addAction(self.widget('ontology_explorer_dock').toggleViewAction())

        # CONFIGURE SIGNALS
        self.debug('Configuring session specific signals')
        connect(self.session.sgnReady, self.onSessionReady)

        # INSTALL DOCKING AREA WIDGET
        self.debug('Installing docking area widget')
        self.session.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.widget('ontology_explorer_dock'))


class OntologyExplorerWidget(QtWidgets.QWidget):
    """
    This class implements the ontology explorer used to list ontology predicates.
    """
    sgnItemActivated = QtCore.pyqtSignal('QGraphicsItem')
    sgnItemClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnItemDoubleClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnItemRightClicked = QtCore.pyqtSignal('QGraphicsItem')

    sgnIRIItemActivated = QtCore.pyqtSignal(IRI)
    sgnIRIItemClicked = QtCore.pyqtSignal(IRI)
    sgnIRIItemDoubleClicked = QtCore.pyqtSignal(IRI)
    sgnIRIItemRightClicked = QtCore.pyqtSignal(IRI)

    def __init__(self, plugin):
        """
        Initialize the ontology explorer widget.
        :type plugin: Session
        """
        super().__init__(plugin.session)

        self.plugin = plugin
        self.items = [
            Item.ConceptIRINode,
            Item.RoleIRINode,
            Item.AttributeIRINode,
            Item.IndividualIRINode,
            Item.ValueDomainIRINode
        ]
        self.status = [
            Status.DEFAULT,
            Status.DRAFT,
            Status.FINAL
        ]

        self.iconAttribute = QtGui.QIcon(':/icons/18/ic_treeview_attribute')
        self.iconConcept = QtGui.QIcon(':/icons/18/ic_treeview_concept')
        self.iconInstance = QtGui.QIcon(':/icons/18/ic_treeview_instance')
        self.iconRole = QtGui.QIcon(':/icons/18/ic_treeview_role')
        self.iconValue = QtGui.QIcon(':/icons/18/ic_treeview_value')

        self.searchShortcut = QtWidgets.QShortcut(QtGui.QKeySequence('Ctrl+f'), self.session)
        self.search = StringField(self)
        self.search.setAcceptDrops(False)
        self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText('Search...')
        self.search.setToolTip('Search ({})'.format(self.searchShortcut.key().toString(QtGui.QKeySequence.NativeText)))
        self.search.setFixedHeight(30)
        #TODO VALUTA SCOMMENTO
        #self.model = QtGui.QStandardItemModel(self)
        self.model =  OntologyExplorerModel(self)

        self.proxy = OntologyExplorerFilterProxyModel(self)
        self.proxy.setDynamicSortFilter(False)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setSortCaseSensitivity(QtCore.Qt.CaseSensitive)
        self.proxy.setSourceModel(self.model)
        self.ontoview = OntologyExplorerView(self)
        self.ontoview.setModel(self.proxy)
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.search)
        self.mainLayout.addWidget(self.ontoview)
        self.setTabOrder(self.search, self.ontoview)
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

        connect(self.ontoview.activated, self.onItemActivated)
        connect(self.ontoview.doubleClicked, self.onItemDoubleClicked)
        connect(self.ontoview.pressed, self.onItemPressed)
        connect(self.search.textChanged, self.doFilterItem)
        connect(self.search.returnPressed, self.onReturnPressed)
        connect(self.searchShortcut.activated, self.doFocusSearch)
        connect(self.sgnItemActivated, self.session.doFocusItem)
        connect(self.sgnItemDoubleClicked, self.session.doFocusItem)
        connect(self.sgnItemRightClicked, self.session.doFocusItem)

        connect(self.session.sgnPrefixAdded, self.onPrefixAdded)
        connect(self.session.sgnPrefixRemoved, self.onPrefixRemoved)
        connect(self.session.sgnPrefixModified, self.onPrefixModified)
        connect(self.session.sgnRenderingModified, self.onRenderingModified)

        connect(self.session.sgnIRIRemovedFromAllDiagrams,self.onIRIRemovedFromAllDiagrams)
        connect(self.session.sgnSingleNodeSwitchIRI, self.onSingleNodeIRISwitched)

        self.unsatisfiableItems = list()

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
    @QtCore.pyqtSlot(str)
    def onRenderingModified(self,rendering):
        # self.redrawIRIItem()
        if self.sender() != self.plugin:
            self.proxy.invalidateFilter()
        self.model.dataChanged.emit(self.model.index(0,0),self.model.index(self.model.rowCount()-1,0))
        if self.sender() != self.plugin:
            self.proxy.invalidateFilter()
            self.proxy.sort(0, QtCore.Qt.AscendingOrder)

    @QtCore.pyqtSlot(str, str)
    def onPrefixAdded(self, pref, ns):
        settings = QtCore.QSettings()
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering == IRIRender.PREFIX.value or rendering == IRIRender.LABEL.value:
            self.redrawIRIItem()

    @QtCore.pyqtSlot(str)
    def onPrefixRemoved(self, pref):
        settings = QtCore.QSettings()
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering == IRIRender.PREFIX.value or rendering == IRIRender.LABEL.value:
            self.redrawIRIItem()


    @QtCore.pyqtSlot(str)
    def onPrefixModified(self, pref):
        settings = QtCore.QSettings()
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering == IRIRender.PREFIX.value or rendering == IRIRender.LABEL.value:
            self.redrawIRIItem()

    @QtCore.pyqtSlot(str)
    def onIRIModified(self,str):
        iri = self.sender()
        self.redrawIRIItem(iri)

    @QtCore.pyqtSlot(AnnotationAssertion)
    def onIRIAnnotationAssertionAdded(self, ann):
        iri = self.sender()
        settings = QtCore.QSettings()
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering == IRIRender.PREFIX.value or rendering == IRIRender.LABEL.value:
            self.redrawIRIItem(iri)

    @QtCore.pyqtSlot(AnnotationAssertion)
    def onIRIAnnotationAssertionRemoved(self, ann):
        iri = self.sender()
        settings = QtCore.QSettings()
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering == IRIRender.PREFIX.value or rendering == IRIRender.LABEL.value:
            self.redrawIRIItem(iri)

    @QtCore.pyqtSlot(AnnotationAssertion)
    def onIRIAnnotationAssertionModified(self, ann):
        iri = self.sender()
        settings = QtCore.QSettings()
        rendering = settings.value('ontology/iri/render', IRIRender.PREFIX.value, str)
        if rendering == IRIRender.PREFIX.value or rendering == IRIRender.LABEL.value:
            self.redrawIRIItem(iri)

    @QtCore.pyqtSlot()
    def onNodeIRISwitched(self):
        node = self.sender()
        self.doAddNode(node.diagram,node)

    @QtCore.pyqtSlot(AbstractNode,IRI)
    def onSingleNodeIRISwitched(self,node,oldIRI):
        oldParentK = self.parentKeyForIRI(oldIRI)
        for parent in self.model.findItems(oldParentK, QtCore.Qt.MatchExactly):
            '''
            rowCount = parent.rowCount()
            for i in range(rowCount):
                child = parent.child(i)
                if child.data(QtCore.Qt.UserRole) is node:
                    parent.removeRow(i)
                    break
            if not parent.rowCount():
                if isinstance(node, OntologyEntityNode) or isinstance(node, OntologyEntityResizableNode):
                    self.disconnectIRISignals(parent.data(QtCore.Qt.UserRole))
                self.model.removeRow(parent.index().row())
            '''
            self.model.removeRow(parent.index().row())

    @QtCore.pyqtSlot(IRI)
    def onIRIRemovedFromAllDiagrams(self,iri):
        parentK = self.parentKeyForIRI(iri)
        for parent in self.model.findItems(parentK, QtCore.Qt.MatchExactly):
            '''
            removeParent = True
            rowCount = parent.rowCount()
            for i in range(rowCount):
                childData = parent.child(i).data(QtCore.Qt.UserRole)
                if isinstance(childData,OntologyEntityNode) or isinstance(childData, OntologyEntityResizableNode):
                    parent.removeRow(i)
                else:
                    removeParent = False
            if removeParent:
                self.model.removeRow(parent.index().row())
            '''
            self.model.removeRow(parent.index().row())

    @QtCore.pyqtSlot(IRI)
    def onUnsatisfiableClass(self, iri):
        parent = self.parentForIRI(iri)
        if parent:
            parent.setData(QtGui.QBrush(QtGui.QColor(255, 0, 0)), QtCore.Qt.ForegroundRole)
            self.unsatisfiableItems.append(parent)

    @QtCore.pyqtSlot(IRI)
    def onUnsatisfiableObjectProperty(self, iri):
        parent = self.parentForIRI(iri)
        if parent:
            parent.setData(QtGui.QBrush(QtGui.QColor(255, 0, 0)), QtCore.Qt.ForegroundRole)
            self.unsatisfiableItems.append(parent)

    @QtCore.pyqtSlot(IRI)
    def onUnsatisfiableDataProperty(self, iri):
        parent = self.parentForIRI(iri)
        if parent:
            parent.setData(QtGui.QBrush(QtGui.QColor(255, 0, 0)), QtCore.Qt.ForegroundRole)
            self.unsatisfiableItems.append(parent)

    @QtCore.pyqtSlot()
    def doResetReasonerHighlight(self):
        for item in self.unsatisfiableItems:
            item.setData(None, QtCore.Qt.ForegroundRole)
        self.unsatisfiableItems = list()

    @QtCore.pyqtSlot(ImportedOntology)
    def onImportedOntologyAdded(self, impOnt):
        """
        :param impOnt:ImportedOntology
        :return:
        """
        for classIRI in impOnt.classes:
            parent = self.parentForIRI(classIRI)
            if not parent:
                parent = QtGui.QStandardItem(self.parentKeyForIRI(classIRI))
                parent.setData(classIRI,QtCore.Qt.UserRole)
                self.connectIRISignals(classIRI)
                self.model.appendRow(parent)
            child = QtGui.QStandardItem(self.childKeyForImported(impOnt,classIRI))
            # CHECK FOR DUPLICATE NODES
            children = [parent.child(i) for i in range(parent.rowCount())]
            if not any([(child.text() == c.text() and c.icon() is self.iconConcept) for c in children]):
                child.setIcon(self.iconConcept)
                childData = [classIRI, Item.ConceptIRINode.value]
                child.setData(childData,QtCore.Qt.UserRole)
                child.setData(self.iconConcept, OntologyExplorerItemDelegate.IconRole)
                parent.appendRow(child)
                
        for objPropIRI in impOnt.objectProperties:
            parent = self.parentForIRI(objPropIRI)
            if not parent:
                parent = QtGui.QStandardItem(self.parentKeyForIRI(objPropIRI))
                parent.setData(objPropIRI,QtCore.Qt.UserRole)
                self.connectIRISignals(objPropIRI)
                self.model.appendRow(parent)
            child = QtGui.QStandardItem(self.childKeyForImported(impOnt,objPropIRI))
            # CHECK FOR DUPLICATE NODES
            children = [parent.child(i) for i in range(parent.rowCount())]
            if not any([(child.text() == c.text() and c.icon() is self.iconRole) for c in children]):
                child.setIcon(self.iconRole)
                childData = [objPropIRI, Item.RoleIRINode.value]
                child.setData(childData,QtCore.Qt.UserRole)
                child.setData(self.iconRole, OntologyExplorerItemDelegate.IconRole)
                parent.appendRow(child)
        
        for dataPropIRI in impOnt.dataProperties:
            parent = self.parentForIRI(dataPropIRI)
            if not parent:
                parent = QtGui.QStandardItem(self.parentKeyForIRI(dataPropIRI))
                parent.setData(dataPropIRI,QtCore.Qt.UserRole)
                self.connectIRISignals(dataPropIRI)
                self.model.appendRow(parent)
            child = QtGui.QStandardItem(self.childKeyForImported(impOnt,dataPropIRI))
            # CHECK FOR DUPLICATE NODES
            children = [parent.child(i) for i in range(parent.rowCount())]
            if not any([(child.text() == c.text() and c.icon() is self.iconAttribute) for c in children]):
                child.setIcon(self.iconAttribute)
                childData = [dataPropIRI, Item.AttributeIRINode.value]
                child.setData(childData,QtCore.Qt.UserRole)
                child.setData(self.iconAttribute, OntologyExplorerItemDelegate.IconRole)
                parent.appendRow(child)
                
        for indIRI in impOnt.individuals:
            parent = self.parentForIRI(indIRI)
            if not parent:
                parent = QtGui.QStandardItem(self.parentKeyForIRI(indIRI))
                parent.setData(indIRI,QtCore.Qt.UserRole)
                self.connectIRISignals(indIRI)
                self.model.appendRow(parent)
            child = QtGui.QStandardItem(self.childKeyForImported(impOnt,indIRI))
            # CHECK FOR DUPLICATE NODES
            children = [parent.child(i) for i in range(parent.rowCount())]
            if not any([(child.text() == c.text() and c.icon() is self.iconInstance) for c in children]):
                child.setIcon(self.iconInstance)
                childData = [indIRI, Item.IndividualIRINode.value]
                child.setData(childData,QtCore.Qt.UserRole)
                child.setData(self.iconInstance, OntologyExplorerItemDelegate.IconRole)
                parent.appendRow(child)
                
        #APPLY FILTERS AND SORT
        if self.sender() != self.plugin:
            self.proxy.invalidateFilter()
            self.proxy.sort(0, QtCore.Qt.AscendingOrder)
    
    @QtCore.pyqtSlot(ImportedOntology)
    def onImportedOntologyRemoved(self, impOnt):
        """
        :param impOnt:ImportedOntology
        :return:
        """
        for classIRI in impOnt.classes:
            parent = self.parentForIRI(classIRI)
            if parent:
                child = self.childForImported(parent,impOnt,classIRI)
                if child:
                    parent.removeRow((child.index().row()))
                if not parent.rowCount():
                    self.disconnectIRISignals(classIRI)
                    self.model.removeRow(parent.index().row())
        for objPropIRI in impOnt.objectProperties:
            parent = self.parentForIRI(objPropIRI)
            if parent:
                child = self.childForImported(parent, impOnt, objPropIRI)
                if child:
                    parent.removeRow((child.index().row()))
                if not parent.rowCount():
                    self.disconnectIRISignals(objPropIRI)
                    self.model.removeRow(parent.index().row())
        for dataPropIRI in impOnt.dataProperties:
            parent = self.parentForIRI(dataPropIRI)
            if parent:
                child = self.childForImported(parent, impOnt, dataPropIRI)
                if child:
                    parent.removeRow((child.index().row()))
                if not parent.rowCount():
                    self.disconnectIRISignals(dataPropIRI)
                    self.model.removeRow(parent.index().row())
        for indIRI in impOnt.individuals:
            parent = self.parentForIRI(indIRI)
            if parent:
                child = self.childForImported(parent, impOnt, indIRI)
                if child:
                    parent.removeRow((child.index().row()))
                if not parent.rowCount():
                    self.disconnectIRISignals(indIRI)
                    self.model.removeRow(parent.index().row())
        #APPLY FILTERS AND SORT
        if self.sender() != self.plugin:
            self.proxy.invalidateFilter()
            self.proxy.sort(0, QtCore.Qt.AscendingOrder)

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def doAddNode(self, diagram, node):
        """
        Add a node in the tree view.
        :type diagram: QGraphicsScene
        :type node: AbstractItem
        """
        #TODO REIMPLEMENTA TUTTO USANDO SOLO GLI INDICI E NON LE ITEM
        if node.type() in self.items:
            parent = self.parentFor(node)
            if not parent:
                if not (isinstance(node,OntologyEntityNode) or isinstance(node, OntologyEntityResizableNode)):
                    parent = QtGui.QStandardItem(self.parentKey(node))
                    parent.setIcon(self.iconFor(node))
                else:
                    parent = QtGui.QStandardItem(self.parentKeyForIRI(node.iri))
                    parent.setData(node.iri,QtCore.Qt.UserRole)
                    self.connectIRISignals(node.iri)
                self.model.appendRow(parent)
            child = QtGui.QStandardItem(self.childKey(diagram, node))
            if isinstance(node,OntologyEntityNode) or isinstance(node, OntologyEntityResizableNode):
                child.setIcon(self.iconFor(node))
                child.setData(self.iconFor(node), OntologyExplorerItemDelegate.IconRole)
                connect(node.sgnIRISwitched,self.onNodeIRISwitched)
            child.setData(node, QtCore.Qt.UserRole)
            # CHECK FOR DUPLICATE NODES
            children = [parent.child(i) for i in range(parent.rowCount())]
            if not any([child.text() == c.text() for c in children]):
                parent.appendRow(child)
            # APPLY FILTERS AND SORT
            #TODO questa operazione al momento del caricamento del progetto è particolarmente onerosa.
            # Quando ci sarà il tempo, valutare funzione apposita per bulk insert come su onImportedOntologyAdded
            # lasciando che questa funzione sia chiamata solo dopo l'aggiunta di singoli nodi sul diagramma
            if self.sender() != self.plugin:
                self.proxy.invalidateFilter()
                self.proxy.sort(0, QtCore.Qt.AscendingOrder)

    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem')
    def doRemoveNode(self, diagram, node):
        """
        Remove a node from the tree view.
        :type diagram: QGraphicsScene
        :type node: AbstractItem
        """
        if node.type() in self.items:
            parent = self.parentFor(node)
            if parent:
                child = self.childFor(parent, diagram, node)
                if child:
                    parent.removeRow(child.index().row())
                if not parent.rowCount():
                    if isinstance(node,OntologyEntityNode) or isinstance(node, OntologyEntityResizableNode):
                        self.disconnectIRISignals(parent.data(QtCore.Qt.UserRole))
                    self.model.removeRow(parent.index().row())

    @QtCore.pyqtSlot(str)
    def doFilterItem(self, key):
        """
        Executed when the search box is filled with data.
        :type key: str
        """
        self.proxy.setFilterFixedString(key)
        self.proxy.sort(QtCore.Qt.AscendingOrder)


    @QtCore.pyqtSlot()
    def doFocusSearch(self):
        """
        Focus the search bar.
        """
        # RAISE THE ENTIRE WIDGET TREE IF IT IS NOT VISIBLE
        if not self.isVisible():
            widget = self
            while widget != self.session:
                widget.show()
                widget.raise_()
                widget = widget.parent()
        self.search.setFocus()
        self.search.selectAll()

    @QtCore.pyqtSlot('QModelIndex')
    def onItemActivated(self, index):
        """
        Executed when an item in the treeview is activated (e.g. by pressing Return or Enter key).
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QtWidgets.QApplication.mouseButtons() == QtCore.Qt.NoButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item and item.data(QtCore.Qt.UserRole):
                if isinstance(item.data(QtCore.Qt.UserRole),IRI):
                    self.sgnIRIItemActivated.emit(item.data(QtCore.Qt.UserRole))
                else:
                    self.sgnItemActivated.emit(item.data(QtCore.Qt.UserRole))
                # KEEP FOCUS ON THE TREE VIEW UNLESS SHIFT IS PRESSED
                if QtWidgets.QApplication.queryKeyboardModifiers() & QtCore.Qt.SHIFT:
                    return
                self.ontoview.setFocus()
            elif item:
                # EXPAND/COLLAPSE PARENT ITEM
                if self.ontoview.isExpanded(index):
                    self.ontoview.collapse(index)
                else:
                    self.ontoview.expand(index)

    @QtCore.pyqtSlot('QModelIndex')
    def onItemDoubleClicked(self, index):
        """
        Executed when an item in the treeview is double clicked.
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QtWidgets.QApplication.mouseButtons() & QtCore.Qt.LeftButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item and item.data(QtCore.Qt.UserRole):
                if isinstance(item.data(QtCore.Qt.UserRole),IRI):
                    self.sgnIRIItemDoubleClicked.emit(item.data(QtCore.Qt.UserRole))
                elif isinstance(item.data(QtCore.Qt.UserRole), AbstractNode):
                    self.sgnItemDoubleClicked.emit(item.data(QtCore.Qt.UserRole))

    @QtCore.pyqtSlot('QModelIndex')
    def onItemPressed(self, index):
        """
        Executed when an item in the treeview is clicked.
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QtWidgets.QApplication.mouseButtons() & QtCore.Qt.LeftButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item and item.data(QtCore.Qt.UserRole):
                if isinstance(item.data(QtCore.Qt.UserRole),IRI):
                    self.sgnIRIItemClicked.emit(item.data(QtCore.Qt.UserRole))
                elif isinstance(item.data(QtCore.Qt.UserRole), AbstractNode):
                    self.sgnItemClicked.emit(item.data(QtCore.Qt.UserRole))

    @QtCore.pyqtSlot(bool)
    def onMenuButtonClicked(self, checked=False):
        """
        Executed when a button in the widget menu is clicked.
        """
        # UPDATE THE PALETTE LAYOUT
        data = self.sender().data()
        elems = self.proxy.items if isinstance(data, Item) else self.proxy.status
        if checked:
            elems.add(data)
        else:
            elems.discard(data)
        self.proxy.invalidateFilter()
        self.proxy.sort(0, QtCore.Qt.AscendingOrder)

    @QtCore.pyqtSlot()
    def onReturnPressed(self):
        """
        Executed when the Return or Enter key is pressed in the search field.
        """
        self.focusNextChild()

    #############################################
    #   INTERFACE
    #################################
    def connectNodeSignals(self, node):
        """
        :type node: OntologyEntityNode | OntologyEntityResizableNode
        """
        connect(node.sgnIRISwitched, self.onNodeIRISwitched)

    def connectIRISignals(self, iri):
        """
        :type iri: IRI
        """
        connect(iri.sgnAnnotationAdded, self.onIRIAnnotationAssertionAdded)
        connect(iri.sgnAnnotationRemoved, self.onIRIAnnotationAssertionRemoved)
        connect(iri.sgnAnnotationModified, self.onIRIAnnotationAssertionModified)
        connect(iri.sgnIRIModified, self.onIRIModified)

    def disconnectIRISignals(self, iri):
        """
        :type iri: IRI
        """
        disconnect(iri.sgnAnnotationAdded, self.onIRIAnnotationAssertionAdded)
        disconnect(iri.sgnAnnotationRemoved, self.onIRIAnnotationAssertionRemoved)
        disconnect(iri.sgnAnnotationModified, self.onIRIAnnotationAssertionModified)
        disconnect(iri.sgnIRIModified, self.onIRIModified)

    def redrawIRIItem(self, iri=None):
        if self.sender() != self.plugin:
            self.proxy.invalidateFilter()
        self.ontoview.setSortingEnabled(False)
        for row in range(0, self.model.rowCount()):
            currItem = self.model.item(row)
            if iri:
                currIRI = currItem.data(QtCore.Qt.UserRole)
                if currIRI is iri:
                    currItem.setText(self.parentKeyForIRI(iri))
                    break
            else:
                if isinstance(currItem.data(QtCore.Qt.UserRole),IRI):
                    currItem.setText(self.parentKeyForIRI(currItem.data(QtCore.Qt.UserRole)))
        self.ontoview.setSortingEnabled(True)
        if self.sender() != self.plugin:
            self.proxy.invalidateFilter()
            self.proxy.sort(0, QtCore.Qt.AscendingOrder)

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

    def childForImported(self, parent, impOnt, iri):
        """
        Search the item representing this node among parent children.
        :type parent: QtGui.QStandardItem
        :type impOnt: ImportedOntology
        :type iri: IRI
        """
        key = self.childKeyForImported(impOnt, iri)
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
        diagram = rstrip(diagram.name, File.Graphol.extension)

        if isinstance(node, OntologyEntityNode) or isinstance(node, OntologyEntityResizableNode):
            return '{0} - {1}'.format(diagram, node.id)
        else:
            predicate = node.text().replace('\n', '')
            return '{0} ({1} - {2})'.format(predicate, diagram, node.id)

    @staticmethod
    def childKeyForImported(impOnt, iri):
        """
        Returns the child key (text) used to place the given node in the treeview.
        :type impOnt: ImportedOntology
        :type iri: IRI
        :rtype: str
        """
        return 'Imported from {}'.format(impOnt.docLocation)

    def iconFor(self, node):
        """
        Returns the icon for the given node.
        :type node:
        """
        if node.type() is Item.AttributeIRINode:
            return self.iconAttribute
        if node.type() is Item.ConceptIRINode:
            return self.iconConcept
        if node.type() is Item.IndividualIRINode:
            return self.iconInstance
        if node.type() is Item.RoleIRINode:
            return self.iconRole
        if node.type() is Item.ValueDomainIRINode:
            return self.iconValue

    def parentFor(self, node):
        """
        Search the parent element of the given node.
        :type node: AbstractNode
        :rtype: QtGui.QStandardItem
        """
        parentK = None
        if isinstance(node,OntologyEntityNode) or isinstance(node, OntologyEntityResizableNode):
            parentK = self.parentKeyForIRI(node.iri)
            for i in self.model.findItems(parentK, QtCore.Qt.MatchExactly):
                parentIRI = i.data(QtCore.Qt.UserRole)
                if node.iri is parentIRI:
                    return i
        else:
            parentK = self.parentKey(node)
            for i in self.model.findItems(parentK, QtCore.Qt.MatchExactly):
                n = i.child(0).data(QtCore.Qt.UserRole)
                if node.type() is n.type():
                    return i
        return None

    def parentForIRI(self, iri):
        """
        Search the parent element of the given iri.
        :type node: IRI
        :rtype: QtGui.QStandardItem
        """
        parentK = self.parentKeyForIRI(iri)
        for i in self.model.findItems(parentK, QtCore.Qt.MatchExactly):
            parentIRI = i.data(QtCore.Qt.UserRole)
            if iri is parentIRI:
                return i
        return None

    @staticmethod
    def parentKeyForIRI(iri):
        return IRIRender.iriLabelString(iri)

    @staticmethod
    def parentKey(node):
        """
        Returns the parent key (text) used to place the given node in the treeview.
        :type node: AbstractNode
        :type project Project
        :rtype: str
        """
        return node.text().replace('\n', '')

    def sizeHint(self):
        """
        Returns the recommended size for this widget.
        :rtype: QtCore.QSize
        """
        return QtCore.QSize(216, 266)


class OntologyExplorerItemDelegate(QtWidgets.QStyledItemDelegate):
    IconRole = QtCore.Qt.UserRole + 1000

    def paint(self, painter, option, index):
        '''
        option.font.setWeight(QtGui.QFont.Bold)
        option.font.setItalic(True)
        option.font.setUnderline(True)
        '''
        painter.save()
        itemText = index.data(QtCore.Qt.DisplayRole)
        itemForeBrush = index.data(QtCore.Qt.ForegroundRole)
        itemIcon = index.data(OntologyExplorerItemDelegate.IconRole)

        if itemForeBrush:
            painter.setPen(itemForeBrush.color())

        iconRect = None
        if itemIcon:
            margin = 3
            mode = QtGui.QIcon.Normal
            state = QtGui.QIcon.On if option.state & QtWidgets.QStyle.State_Open else QtGui.QIcon.Off
            iconRect = QtCore.QRect(QtCore.QPoint(), option.decorationSize)
            iconRect.moveCenter(option.rect.center())
            iconRect.setLeft(option.rect.left())
            #r.moveLeft(option.rect.center())
            itemIcon.paint(painter, iconRect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, mode, state)
        if (option.state & QtWidgets.QStyle.State_Selected):
            painter.fillRect(option.rect, option.palette.highlight())
        textRect = None
        if iconRect:
            textRect = QtCore.QRect(QtCore.QPoint(), option.rect.size())
            textRect.moveCenter(option.rect.center())
            textRect.setLeft(option.rect.left() + option.decorationSize.width() + margin)
        else:
            textRect = option.rect
        
        painter.drawText(textRect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, itemText)
        painter.restore()

class OntologyExplorerView(QtWidgets.QTreeView):
    """
    This class implements the ontology explorer tree view.
    """
    def __init__(self, widget):
        """
        Initialize the ontology explorer view.
        :type widget: OntologyExplorerWidget
        """
        super().__init__(widget)
        self.startPos = None
        self.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        self.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setHeaderHidden(True)
        self.setHorizontalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setSelectionMode(QtWidgets.QTreeView.SingleSelection)
        self.setSortingEnabled(True)
        self.setWordWrap(True)
        self.setItemDelegate(OntologyExplorerItemDelegate(self))

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the Session holding the OntologyExplorer widget.
        :rtype: Session
        """
        return self.widget.session

    @property
    def widget(self):
        """
        Returns the reference to the OntologyExplorer widget.
        :rtype: OntologyExplorerWidget
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
        if mouseEvent.buttons() & QtCore.Qt.LeftButton:
            self.startPos = mouseEvent.pos()
        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse if moved while a button is being pressed.
        :type mouseEvent: QMouseEvent
        """
        if mouseEvent.buttons() & QtCore.Qt.LeftButton:
            #if Item.ConceptNode <= self.item < Item.InclusionEdge:
                distance = (mouseEvent.pos() - self.startPos).manhattanLength()
                if distance >= QtWidgets.QApplication.startDragDistance():

                    index = first(self.selectedIndexes())
                    if index:
                        model = self.model().sourceModel()
                        index = self.model().mapToSource(index)
                        item = model.itemFromIndex(index)
                        itemData = item.data(QtCore.Qt.UserRole)
                        if itemData and isinstance(itemData,AbstractNode):
                            pass
                        else:
                            if item.hasChildren():
                                itemData = item.child(0).data(QtCore.Qt.UserRole)
                        if itemData:
                            if isinstance(itemData,OntologyEntityNode) or isinstance(itemData, OntologyEntityResizableNode):
                                mimeData = QtCore.QMimeData()
                                mimeData.setText(str(itemData.Type.value))
                                node_iri = itemData.iri
                                byte_array = QtCore.QByteArray()
                                byte_array.append(str(node_iri))
                                mimeData.setData(str(itemData.Type.value), byte_array)
                                drag = QtGui.QDrag(self)
                                drag.setMimeData(mimeData)
                                drag.exec_(QtCore.Qt.CopyAction)
                            elif isinstance(itemData,list):
                                iri = itemData[0]
                                itemValue = itemData[1]
                                mimeData = QtCore.QMimeData()
                                mimeData.setText(str(itemValue))
                                byte_array = QtCore.QByteArray()
                                byte_array.append(str(iri))
                                mimeData.setData(str(itemValue), byte_array)
                                drag = QtGui.QDrag(self)
                                drag.setMimeData(mimeData)
                                drag.exec_(QtCore.Qt.CopyAction)
                            else:
                                #OLD ELEMENTS should not be used
                                mimeData = QtCore.QMimeData()
                                mimeData.setText(str(itemData.Type.value))
                                node_iri = self.session.project.get_iri_of_node(itemData)
                                node_remaining_characters = itemData.remaining_characters
                                comma_seperated_text = str(node_iri + ',' + node_remaining_characters + ',' + itemData.text())
                                byte_array = QtCore.QByteArray()
                                byte_array.append(comma_seperated_text)
                                mimeData.setData(str(itemData.Type.value), byte_array)
                                drag = QtGui.QDrag(self)
                                drag.setMimeData(mimeData)
                                # drag.setPixmap(self.icon().pixmap(60, 40))
                                # drag.setHotSpot(self.startPos - self.rect().topLeft())
                                drag.exec_(QtCore.Qt.CopyAction)

        super().mouseMoveEvent(mouseEvent)

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
                if item.data(QtCore.Qt.UserRole):
                    if isinstance(item.data(QtCore.Qt.UserRole),IRI):
                        iri = item.data(QtCore.Qt.UserRole)
                        self.widget.sgnIRIItemRightClicked.emit(iri)
                        #TODO gestisci creazione menu per IRI
                    elif isinstance(item.data(QtCore.Qt.UserRole), AbstractNode):
                        node = item.data(QtCore.Qt.UserRole)
                        self.widget.sgnItemRightClicked.emit(node)
                        menu = self.session.mf.create(node.diagram, [node])
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

class OntologyExplorerFilterProxyModel(QtCore.QSortFilterProxyModel):
    """
    Extends QSortFilterProxyModel adding filtering functionalities for the explorer widget
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = {Item.ConceptIRINode, Item.IndividualIRINode, Item.RoleIRINode, Item.AttributeIRINode, Item.ValueDomainIRINode}
        self.status = {Status.DEFAULT, Status.DRAFT, Status.FINAL}

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self):
        return self.parent().project

    @property
    def session(self):
        return self.parent().session

    #############################################
    #   INTERFACE
    #################################

    def filterAcceptsRow(self, sourceRow, parentIndex):
        """
        Overrides filterAcceptsRow to include extra filtering conditions
        :type sourceRow: int
        :type parentIndex: QModelIndex
        :rtype: bool
        """
        '''
        index = self.sourceModel().index(sourceRow, 0, parentIndex)
        item = self.sourceModel().itemFromIndex(index)
        # PARENT NODE
        # LEAF NODE
        if item.parent():
            parentItemIndex = self.sourceModel().indexFromItem(item.parent())
            result = parentItemIndex.isValid()
        # PARENT NODE
        else:
            result = super().filterAcceptsRow(sourceRow, parentIndex)
        return result
        '''
        if parentIndex.isValid():
            return True
        else:
            return super().filterAcceptsRow(sourceRow, parentIndex)

class OntologyExplorerModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)


    def data(self,index,role):
        if role == QtCore.Qt.DisplayRole:
            dt = self.itemFromIndex(index).data(QtCore.Qt.UserRole)
            if isinstance(dt,IRI):
                return IRIRender.iriLabelString(dt)
            else:
                return super().data(index, role)
        else:
            return super().data(index,role)
