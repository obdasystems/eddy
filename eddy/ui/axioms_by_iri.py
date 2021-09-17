from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy.core.common import HasWidgetSystem, HasThreadingSystem
from eddy.core.datatypes.owl import OWLAxiom
from eddy.core.exporters.owl2 import OWLOntologyExporterWorker
from eddy.core.functions.signals import connect
from eddy.core.jvm import getJavaVM
from eddy.core.output import getLogger
from eddy.core.worker import AbstractWorker
from eddy.ui.consistency_check import EmptyEntityExplanationWorker
from eddy.ui.fields import StringField

LOGGER = getLogger()




class AxiomsByEntityDialog(QtWidgets.QDialog, HasThreadingSystem):
    """
    Extends QtWidgets.QDialog with facilities
    """
    sgnWork = QtCore.pyqtSignal()
    sgnErrored = QtCore.pyqtSignal()
    sgnAxiomsComputed = QtCore.pyqtSignal()

    def __init__(self, project, session, iri):
        """
        Initialize the dialog.
        :type project: Project
        :type session: Session
        :type iri : IRI
        """
        super().__init__(session)

        self.project = project
        self.workerThread = None
        self.worker = None
        self.iri = iri
        self.axioms_by_type = dict()

        self.msgbox_busy = QtWidgets.QMessageBox(self)
        self.msgbox_busy.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_busy.setWindowTitle('Please Wait!')
        self.msgbox_busy.setStandardButtons(QtWidgets.QMessageBox.NoButton)
        self.msgbox_busy.setText('Computing axioms...  (Please Wait!)')
        self.msgbox_busy.setTextFormat(QtCore.Qt.RichText)

        self.status_bar = QtWidgets.QStatusBar()
        self.status_bar.setMinimumWidth(350)

        ####################################################

        self.messageBoxLayout = QtWidgets.QVBoxLayout()
        self.messageBoxLayout.setContentsMargins(0, 6, 0, 0)
        self.messageBoxLayout.setAlignment(QtCore.Qt.AlignCenter)

        self.messageBoxLayout.addWidget(self.msgbox_busy)
        self.messageBoxLayout.addWidget(self.status_bar)

        self.messageBoxArea = QtWidgets.QWidget()
        self.messageBoxArea.setLayout(self.messageBoxLayout)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainLayout.addWidget(self.messageBoxArea)

        self.setLayout(self.mainLayout)

        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Please Wait!')
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.CustomizeWindowHint)
        # self.setWindowModality(QtCore.Qt.NonModal)
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.adjustSize()
        self.setFixedSize(self.width(), self.height())
        self.show()

        connect(self.sgnWork, self.doWork)
        self.sgnWork.emit()

    #############################################
    #   INTERFACE
    #################################

    def dispose(self):
        """
        Gracefully quits working thread.
        """
        if self.workerThread:
            self.workerThread.quit()
            if not self.workerThread.wait(2000):
                self.workerThread.terminate()
                self.workerThread.wait()
        axioms_dialog = AxiomsByTypeDialog(self.session, self.worker.getAxioms(), self.iri)
        axioms_dialog.open()

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the active session (alias for SyntaxValidationDialog.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   EVENTS
    #################################

    def closeEvent(self, closeEvent):
        """
        Executed when the dialog is closed.
        :type closeEvent: QCloseEvent
        """
        self.dispose()

    def showEvent(self, showEvent):
        """
        Executed whenever the dialog is shown.
        :type showEvent: QShowEvent
        """
        self.sgnWork.emit()

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def doWork(self):
        """
        Perform on or more advancements step in the explanation computation
        """
        self.worker = AxiomsByEntityWorker(self.status_bar, self.project, self.session,
                                                   self, self.iri)
        connect(self.worker.sgnError, self.onErrorInExec)
        connect(self.worker.sgnAxiomsComputed, self.onAxiomsComputed)
        self.startThread('AxiomsByEntity', self.worker)

    @QtCore.pyqtSlot(Exception)
    def onErrorInExec(self, exc):
        self.msgbox_error = QtWidgets.QMessageBox(self)
        self.msgbox_error.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.msgbox_error.setWindowTitle('Error!')
        self.msgbox_error.setStandardButtons(QtWidgets.QMessageBox.Close)
        self.msgbox_error.setTextFormat(QtCore.Qt.RichText)
        self.msgbox_error.setIconPixmap(QtGui.QIcon(':/icons/48/ic_done_black').pixmap(48))
        self.msgbox_error.setText('An error occurred!!\n{}'.format(str(exc)))
        self.close()
        self.msgbox_error.exec_()

    @QtCore.pyqtSlot()
    def onAxiomsComputed(self):
        """
        Executed when the ontology is inconsistent.
        """
        self.msgbox_busy.setText('Explanations computed')
        self.status_bar.hide()
        self.resize(self.sizeHint())
        self.sgnAxiomsComputed.emit()
        self.close()


#############################################
#   AXIOMS BY TYPE WIDGET
#################################
class AxiomsByTypeDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    This class implements the axioms by type dialog for a given IRI.
    """

    def __init__(self, session, axioms_by_type, entityIRI):
        """
        Initialize the Ontology Manager dialog.
        :type session: Session
        :type axioms_by_type: dict
        """
        super().__init__(session)
        self.axioms_by_type = axioms_by_type
        self.project = session.project
        self.entityIRI = entityIRI

        #############################################
        # EXPLANATIONS TAB
        #################################

        axiomsWidget = AxiomsByTypeExplorerWidget(self.project, self.session, objectName='axioms_widget')
        self.addWidget(axiomsWidget)

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self, objectName='confirmation_widget')
        doneBtn = QtWidgets.QPushButton('Done', objectName='done_button')
        confirmation.addButton(doneBtn, QtWidgets.QDialogButtonBox.AcceptRole)
        confirmation.setContentsMargins(10, 0, 10, 10)
        self.addWidget(confirmation)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('axioms_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(800, 520)
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        title = 'Explanations for inconsistent ontology'
        if self.entityIRI:
            title = 'Axioms referencing <{}>'.format(str(self.entityIRI))
        self.setWindowTitle(title)
        self.setWindowModality(QtCore.Qt.NonModal)
        self.redraw()

        connect(confirmation.accepted, self.accept)


    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the main session (alias for PreferencesDialog.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot()
    def accept(self):
        """
        Executed when the dialog is accepted.
        """
        ##
        ## TODO: complete validation and settings save
        ##
        #############################################
        # GENERAL TAB
        #################################

        #############################################
        # PREFIXES TAB
        #################################

        #############################################
        # ANNOTATIONS TAB
        #################################

        #############################################
        # SAVE & EXIT
        #################################

        super().accept()

    @QtCore.pyqtSlot()
    def reject(self):
        """
        Executed when the dialog is accepted.
        """
        ##
        ## TODO: complete validation and settings save
        ##
        #############################################
        # GENERAL TAB
        #################################

        #############################################
        # PREFIXES TAB
        #################################

        #############################################
        # ANNOTATIONS TAB
        #################################

        #############################################
        # SAVE & EXIT
        #################################

        super().reject()

    @QtCore.pyqtSlot()
    def redraw(self):
        """
        Redraw the dialog components, reloading their contents.
        """
        axiomsWidget = self.widget('axioms_widget')
        axiomsWidget.doClear()
        axiomsWidget.setAxioms(self.axioms_by_type)
        self.setWindowModality(QtCore.Qt.NonModal)


class AxiomsByTypeExplorerWidget(QtWidgets.QWidget):
    """
    This class implements the Explanation explorer used to list Explanation predicates.
    """
    sgnItemClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnItemDoubleClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnItemRightClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnFakeItemAdded = QtCore.pyqtSignal('QGraphicsScene', 'QGraphicsItem')
    sgnColourItem = QtCore.pyqtSignal('QStandardItem')

    def __init__(self, project, session, **kwargs):
        """
        Initialize the AXIOMS BY ENTITY explorer widget.
        """
        super().__init__(session, objectName=kwargs.get('objectName'))

        self.project = project
        self.axioms_by_type = None

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
        # self.proxy = QtCore.QSortFilterProxyModel(self)
        self.proxy = AxiomsByTypeExplorerFilterProxyModel(self)
        self.proxy.setDynamicSortFilter(False)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setSortCaseSensitivity(QtCore.Qt.CaseSensitive)
        self.proxy.setSourceModel(self.model)
        self.ontoview = AxiomsByTypeExplorerView(self)
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

        connect(self.search.textChanged, self.doFilterItem)

        '''
        connect(self.ontoview.doubleClicked, self.onItemDoubleClicked)
        connect(self.ontoview.pressed, self.onItemPressed)

        connect(self.sgnItemDoubleClicked, self.session.doFocusItem)
        connect(self.sgnItemRightClicked, self.session.doFocusItem)

        connect(self.sgnColourItem, self.doColorItems)
        '''

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the active session.
        :rtype: Session
        """
        return self.parent()

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
    '''
    @QtCore.pyqtSlot('QStandardItem')
    def doColorItems(self, item):
        row_count = item.rowCount()
        self.session.doResetConsistencyCheck(updateNodes=False, clearReasonerCache=False)
        self.project.nodes_or_edges_of_axioms_to_display_in_widget = []
        self.project.nodes_or_edges_of_explanations_to_display_in_widget = []

        for r in range(row_count):
            child = item.child(r, 0)
            node_or_edge_or_axiom = child.data()

            if 'eddy.core.items' in str(type(node_or_edge_or_axiom)):
                # item is an axiom
                # child is a node or an edge
                explanation_item = item.parent()
                explanation_item_row_count = explanation_item.rowCount()

                for r2 in range(0, explanation_item_row_count):
                    child_of_explanation_item = explanation_item.child(r2, 0)
                    child_of_explanation_item_row_count = child_of_explanation_item.rowCount()

                    for r3 in range(0, child_of_explanation_item_row_count):
                        nephew_or_child = child_of_explanation_item.child(r3, 0)
                        nephew_or_child_data = nephew_or_child.data()

                        if 'eddy.core.items' in str(type(nephew_or_child_data)):
                            if nephew_or_child_data.id == node_or_edge_or_axiom.id:
                                # if (nephew_or_child_data.text() == nephew_or_child_data.text()):
                                # print('nephew_or_child_data not coloured - ',nephew_or_child_data)
                                pass
                            else:
                                self.project.nodes_or_edges_of_explanations_to_display_in_widget.append(
                                    nephew_or_child_data)

                self.project.nodes_or_edges_of_axioms_to_display_in_widget.append(node_or_edge_or_axiom)

            if (str(type(node_or_edge_or_axiom)) == '<class \'str\'>') or (str(type(node_or_edge_or_axiom)) == 'str'):
                # item is an explanation
                # child is an axiom
                # colour all the nodes and edges involved in the axiom
                row_count_2 = child.rowCount()

                for r2 in range(0, row_count_2):
                    grand_child = child.child(r2, 0)
                    node_or_edge = grand_child.data()

                    if 'eddy.core.items' in str(type(node_or_edge)):
                        self.project.nodes_or_edges_of_explanations_to_display_in_widget.append(node_or_edge)

        self.project.colour_items_in_case_of_unsatisfiability_or_inconsistent_ontology()
    '''

    @QtCore.pyqtSlot(str)
    def doAddEntityType(self, type):
        type_to_add = QtGui.QStandardItem(
            '{}'.format(type))
        type_to_add.setData(type)
        self.model.appendRow(type_to_add)
        self.proxy.sort(0, QtCore.Qt.AscendingOrder)
        return type_to_add

    @QtCore.pyqtSlot('QStandardItem', str)
    def doAddAxiom(self, q_item, axiom):
        axiom_to_add = QtGui.QStandardItem(axiom)
        axiom_to_add.setData(axiom)
        q_item.appendRow(axiom_to_add)
        self.proxy.sort(0, QtCore.Qt.AscendingOrder)

    '''
    @QtCore.pyqtSlot('QGraphicsScene', 'QGraphicsItem', 'QStandardItem')
    def doAddNodeOREdge(self, diagram, node_or_edge, q_item):
        icon = None

        if 'eddy.core.items.nodes' in str(type(node_or_edge)):
            button_name = str(node_or_edge.id) + ':' + str(node_or_edge.text())
            icon = self.iconFor(node_or_edge)
        elif 'eddy.core.items.edges' in str(type(node_or_edge)):
            button_name = str(node_or_edge.id) + ':' + str(node_or_edge.type()).replace('Item.', '')

        node_or_edge_to_append = QtGui.QStandardItem(button_name)

        if icon is not None:
            node_or_edge_to_append.setIcon(icon)

        node_or_edge_to_append.setData(node_or_edge)
        q_item.appendRow(node_or_edge_to_append)
    '''

    '''
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
                self.model.appendRow(parent)
                self.proxy.sort(0, QtCore.Qt.AscendingOrder)
            child = QtGui.QStandardItem(self.childKey(diagram, node))
            child.setData(node)
            parent.appendRow(child)
            self.proxy.sort(0, QtCore.Qt.AscendingOrder)
    '''

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

    '''
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
    '''

    '''
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
                    # item is an explanation or an axiom
                    self.sgnColourItem.emit(item)
                else:
                    self.sgnItemDoubleClicked.emit(item.data())
    '''

    '''
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
                    # item is an explanation or an axiom
                    self.sgnColourItem.emit(item)
                else:
                    self.sgnItemClicked.emit(item.data())
    '''

    #############################################
    #   INTERFACE
    #################################
    def setAxioms(self, axioms):
        self.axioms_by_type = axioms
        for entity_type, axioms in self.axioms_by_type.items():
            if axioms:
                type_item = self.doAddEntityType(entity_type)
                for axiom in axioms:
                    self.doAddAxiom(type_item, axiom)
        self.proxy.invalidateFilter()
        self.proxy.sort(0, QtCore.Qt.AscendingOrder)

    '''
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
    '''

    '''
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
    '''

    '''
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
    '''

    '''
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
    '''

    '''
    @staticmethod
    def parentKey(node):
        """
        Returns the parent key (text) used to place the given node in the treeview.
        :type node: AbstractNode
        :rtype: str
        """
        return node.text().replace('\n', '')
    '''

    def sizeHint(self):
        """
        Returns the recommended size for this widget.
        :rtype: QtCore.QSize
        """
        return QtCore.QSize(216, 266)


# TODO AGGIUNGI OPPORTUNA FUNZIONE DI RICERCA (implementa come in ontology explorer), CONSENTI DI COPIARE ASSIOMI TRAMITE CLICK DESTRO
class AxiomsByTypeExplorerView(QtWidgets.QTreeView):
    """
    This class implements the Explanation explorer tree view.
    """

    def __init__(self, widget):
        """
        Initialize the Explanation explorer view.
        :type widget: AxiomsByTypeExplorerWidget
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
        self.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the Session holding the ExplanationExplorer widget.
        :rtype: Session
        """
        return self.widget.session

    @property
    def widget(self):
        """
        Returns the reference to the ExplanationExplorer widget.
        :rtype: AxiomsByTypeExplorerWidget
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

    # TODO IMPLEMENTA QUI FUNZIONE CHE COPIA TESTO DEGLI ELEMENTI SELEZIONATI(SE NECESSARIO)
    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the tree view.
        :type mouseEvent: QMouseEvent
        """
        '''
        if mouseEvent.button() == QtCore.Qt.RightButton:
            index = first(self.selectedIndexes())
            if index:
                model = self.model().sourceModel()
                index = self.model().mapToSource(index)
                item = model.itemFromIndex(index)
                node_edge_or_axiom = item.data()

                if 'eddy.core.items.nodes' in str(type(item.data())):
                    self.widget.sgnItemRightClicked.emit(node_edge_or_axiom)
                    menu = self.session.mf.create(node_edge_or_axiom.diagram, [node_edge_or_axiom])
                    menu.exec_(mouseEvent.screenPos().toPoint())
        '''

        super().mouseReleaseEvent(mouseEvent)

    #############################################
    #   INTERFACE
    #################################

    '''
    def sizeHintForColumn(self, column):
        """
        Returns the size hint for the given column.
        This will make the column of the treeview as wide as the widget that contains the view.
        :type column: int
        :rtype: int
        """
        return max(super().sizeHintForColumn(column), self.viewport().width())
    '''


class AxiomsByTypeExplorerFilterProxyModel(QtCore.QSortFilterProxyModel):
    """
    Extends QSortFilterProxyModel adding filtering functionalities for the explorer widget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

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

        filterRegExp = self.filterRegExp()
        patternToLower = filterRegExp.pattern().lower()

        index = self.sourceModel().index(sourceRow, 0, parentIndex)
        item = self.sourceModel().itemFromIndex(index)
        if parentIndex.isValid():
            if item.text():
                if patternToLower in item.text().lower():
                    return True
                else:
                    return False
            else:
                return True
        elif item.hasChildren():
            children = [item.child(i) for i in range(item.rowCount())]
            # TODO INSERISCI CONTROLLO NON CASE SENSITIVE
            if any([patternToLower in child.text().lower() for child in children]):
                return True
            else:
                return super().filterAcceptsRow(sourceRow, parentIndex)
        else:
            return super().filterAcceptsRow(sourceRow, parentIndex)

        '''
        if parentIndex.isValid():
            return True
        else:
            return super().filterAcceptsRow(sourceRow, parentIndex)
        '''

#############################################
#   WORKER
#################################
class AxiomsByEntityWorker(AbstractWorker):
    """
    Extends AbstractWorker providing a worker thread that will compute the set of axioms involving the given entity
    """
    sgnBusy = QtCore.pyqtSignal(bool)
    sgnStarted = QtCore.pyqtSignal()
    sgnError = QtCore.pyqtSignal(Exception)
    sgnAxiomsComputed = QtCore.pyqtSignal()

    def __init__(self, status_bar, project, session, dialog, iri):
        """
        Initialize the syntax validation worker.
        :type current: int
        :type items: list
        :type project: Project
        :type iri : IRI
        """
        super().__init__()
        self.axioms_by_type = dict()
        self.project = project
        self.session = session
        self.status_bar = status_bar
        self.dialog = dialog
        self.iri = iri
        self.vm = getJavaVM()
        if not self.vm.isRunning():
            self.vm.initialize()
        self.vm.attachThreadToJVM()
        self.IRIClass = self.vm.getJavaClass('org.semanticweb.owlapi.model.IRI')
        self.OWLManagerClass = self.vm.getJavaClass('org.semanticweb.owlapi.apibinding.OWLManager')
        self.IRIMapperClass = self.vm.getJavaClass('org.semanticweb.owlapi.util.SimpleIRIMapper')
        self.OWLClassClass = self.vm.getJavaClass('org.semanticweb.owlapi.model.OWLClass')
        self.OWLImportsEnum = self.vm.getJavaClass('org.semanticweb.owlapi.model.parameters.Imports')
        self.df = None

    def loadImportedOntologiesIntoManager(self):
        LOGGER.debug('Loading declared imports into the OWL 2 Manager')
        self.status_bar.showMessage('Loading declared imports into the OWL 2 Manager')
        for impOnt in self.project.importedOntologies:
            try:
                docObj = None
                if impOnt.isLocalDocument:
                    docObj = self.JavaFileClass(impOnt.docLocation)
                else:
                    docObj = self.URIClass(impOnt.docLocation)
                docLocationIRI = self.IRIClass.create(docObj)
                impOntIRI = self.IRIClass.create(impOnt.ontologyIRI)
                iriMapper = self.IRIMapperClass(impOntIRI, docLocationIRI)
                self.manager.getIRIMappers().add(iriMapper)
                loaded = self.manager.loadOntology(impOntIRI)
            except Exception as e:
                LOGGER.exception(
                    'The imported ontology <{}> cannot be loaded.\nError:{}'.format(impOnt, str(e)))
            else:
                LOGGER.debug('Ontology ({}) correctly loaded.'.format(impOnt))
                self.status_bar.showMessage('Ontology ({}) correctly loaded.'.format(impOnt))

    def initializeOWLManager(self, ontology):
        self.status_bar.showMessage('Initializing the OWL 2 Manager')
        self.manager = ontology.getOWLOntologyManager()
        self.df = self.manager.getOWLDataFactory()
        #self.loadImportedOntologiesIntoManager()
        self.status_bar.showMessage('OWL 2 Manager initialized')

    def initializeOWLOntology(self):
        self.status_bar.showMessage('Fetching the OWL 2 ontology')
        worker = OWLOntologyExporterWorker(self.project, axioms={axiom for axiom in OWLAxiom})
        worker.run()
        self.status_bar.showMessage('OWL 2 ontology fetched')
        self.ontology = worker.ontology
        self.initializeOWLManager(self.ontology)

    def getAxiomsAsClass(self):
        result = list()
        cl = self.df.getOWLClass(self.IRIClass.create(str(self.iri)))
        ##GENERALE
        referencing_axioms = self.ontology.getReferencingAxioms(cl)
        for axiom in referencing_axioms:
            result.append(axiom.toString())
        return result
        ##PER TIPO DI ASSIOMA
        '''
        sub_set = self.ontology.getSubClassAxiomsForSubClass(cl)
        for axiom in sub_set:
            result.append(axiom.toString())
        super_set = self.ontology.getSubClassAxiomsForSuperClass(cl)
        for axiom in super_set:
            result.append(axiom.toString())
        disjoint_set = self.ontology.getDisjointClassesAxioms(cl)
        for axiom in disjoint_set:
            result.append(axiom.toString())
        disjoint_union_set = self.ontology.getDisjointUnionAxioms(cl)
        for axiom in disjoint_union_set:
            result.append(axiom.toString())
        equivalent_set = self.ontology.getEquivalentClassesAxioms(cl)
        for axiom in equivalent_set:
            result.append(axiom.toString())
        key_set = self.ontology.getHasKeyAxioms(cl)
        for axiom in key_set:
            result.append(axiom.toString())
        assertion_set = self.ontology.getClassAssertionAxioms(cl)
        for axiom in assertion_set:
            result.append(axiom.toString())
        return result
        '''

    def getAxiomsAsObjectProperty(self, gen_cl_axioms):
        result = list()
        obj_prop = self.df.getOWLObjectProperty(self.IRIClass.create(str(self.iri)))
        ##GENERALE
        referencing_axioms = self.ontology.getReferencingAxioms(obj_prop)
        for axiom in referencing_axioms:
            result.append(axiom.toString())
        return result
        ##PER TIPO DI ASSIOMA
        ##DIRECT
        '''
        sub_set = self.ontology.getObjectSubPropertyAxiomsForSubProperty(obj_prop)
        for axiom in sub_set:
            result.append(axiom.toString())
        super_set = self.ontology.getObjectSubPropertyAxiomsForSuperProperty(obj_prop)
        for axiom in super_set:
            result.append(axiom.toString())
        dom_set = self.ontology.getObjectPropertyDomainAxioms(obj_prop)
        for axiom in dom_set:
            result.append(axiom.toString())
        ran_set = self.ontology.getObjectPropertyRangeAxioms(obj_prop)
        for axiom in ran_set:
            result.append(axiom.toString())
        inv_set = self.ontology.getInverseObjectPropertyAxioms(obj_prop)
        for axiom in inv_set:
            result.append(axiom.toString())
        equivalent_set = self.ontology.getEquivalentObjectPropertiesAxioms(obj_prop)
        for axiom in equivalent_set:
            result.append(axiom.toString())
        disjoint_set = self.ontology.getDisjointObjectPropertiesAxioms(obj_prop)
        for axiom in disjoint_set:
            result.append(axiom.toString())
        funct_set = self.ontology.getFunctionalObjectPropertyAxioms(obj_prop)
        for axiom in funct_set:
            result.append(axiom.toString())
        inv_funct_set = self.ontology.getInverseFunctionalObjectPropertyAxioms(obj_prop)
        for axiom in inv_funct_set:
            result.append(axiom.toString())
        sym_set = self.ontology.getSymmetricObjectPropertyAxioms(obj_prop)
        for axiom in sym_set:
            result.append(axiom.toString())
        asym_set = self.ontology.getAsymmetricObjectPropertyAxioms(obj_prop)
        for axiom in asym_set:
            result.append(axiom.toString())
        ref_set = self.ontology.getReflexiveObjectPropertyAxioms(obj_prop)
        for axiom in ref_set:
            result.append(axiom.toString())
        irr_set = self.ontology.getIrreflexiveObjectPropertyAxioms(obj_prop)
        for axiom in irr_set:
            result.append(axiom.toString())
        irr_set = self.ontology.getIrreflexiveObjectPropertyAxioms(obj_prop)
        for axiom in irr_set:
            result.append(axiom.toString())
        tran_set = self.ontology.getTransitiveObjectPropertyAxioms(obj_prop)
        for axiom in tran_set:
            result.append(axiom.toString())
        assertion_set = self.ontology.getObjectPropertyAssertionAxioms(obj_prop)
        for axiom in assertion_set:
            result.append(axiom.toString())
        ##INVERSE
        sub_set = self.ontology.getObjectSubPropertyAxiomsForSubProperty(obj_prop.getInverseProperty())
        for axiom in sub_set:
            result.append(axiom.toString())
        super_set = self.ontology.getObjectSubPropertyAxiomsForSuperProperty(obj_prop.getInverseProperty())
        dom_set = self.ontology.getObjectPropertyDomainAxioms(obj_prop.getInverseProperty())
        for axiom in dom_set:
            result.append(axiom.toString())
        ran_set = self.ontology.getObjectPropertyRangeAxioms(obj_prop.getInverseProperty())
        for axiom in ran_set:
            result.append(axiom.toString())
        for axiom in super_set:
            result.append(axiom.toString())
        inv_set = self.ontology.getInverseObjectPropertyAxioms(obj_prop.getInverseProperty())
        for axiom in inv_set:
            result.append(axiom.toString())
        equivalent_set = self.ontology.getEquivalentObjectPropertiesAxioms(obj_prop.getInverseProperty())
        for axiom in equivalent_set:
            result.append(axiom.toString())
        disjoint_set = self.ontology.getDisjointObjectPropertiesAxioms(obj_prop.getInverseProperty())
        for axiom in disjoint_set:
            result.append(axiom.toString())
        funct_set = self.ontology.getFunctionalObjectPropertyAxioms(obj_prop.getInverseProperty())
        for axiom in funct_set:
            result.append(axiom.toString())
        inv_funct_set = self.ontology.getInverseFunctionalObjectPropertyAxioms(obj_prop.getInverseProperty())
        for axiom in inv_funct_set:
            result.append(axiom.toString())
        sym_set = self.ontology.getSymmetricObjectPropertyAxioms(obj_prop.getInverseProperty())
        for axiom in sym_set:
            result.append(axiom.toString())
        asym_set = self.ontology.getAsymmetricObjectPropertyAxioms(obj_prop.getInverseProperty())
        for axiom in asym_set:
            result.append(axiom.toString())
        ref_set = self.ontology.getReflexiveObjectPropertyAxioms(obj_prop.getInverseProperty())
        for axiom in ref_set:
            result.append(axiom.toString())
        irr_set = self.ontology.getIrreflexiveObjectPropertyAxioms(obj_prop.getInverseProperty())
        for axiom in irr_set:
            result.append(axiom.toString())
        irr_set = self.ontology.getIrreflexiveObjectPropertyAxioms(obj_prop.getInverseProperty())
        for axiom in irr_set:
            result.append(axiom.toString())
        tran_set = self.ontology.getTransitiveObjectPropertyAxioms(obj_prop).getInverseProperty()
        for axiom in tran_set:
            result.append(axiom.toString())
        assertion_set = self.ontology.getObjectPropertyAssertionAxioms(obj_prop.getInverseProperty())
        for axiom in assertion_set:
            result.append(axiom.toString())
        #General class axioms
        for axiom in gen_cl_axioms:
            if axiom.containsEntityInSignature(obj_prop):
                result.append(axiom.toString())
        '''

        return result

    def getAxiomsAsDataProperty(self, gen_cl_axioms):
        result = list()
        dt_prop = self.df.getOWLDataProperty(self.IRIClass.create(str(self.iri)))
        ##GENERALE
        referencing_axioms = self.ontology.getReferencingAxioms(dt_prop)
        for axiom in referencing_axioms:
            result.append(axiom.toString())
        return result
        ##PER TIPO DI ASSIOMA
        '''
        sub_set = self.ontology.getDataSubPropertyAxiomsForSubProperty(dt_prop)
        for axiom in sub_set:
            result.append(axiom.toString())
        super_set = self.ontology.getDataSubPropertyAxiomsForSuperProperty(dt_prop)
        for axiom in super_set:
            result.append(axiom.toString())
        dom_set = self.ontology.getDataPropertyDomainAxioms(dt_prop)
        for axiom in dom_set:
            result.append(axiom.toString())
        ran_set = self.ontology.getDataPropertyRangeAxioms(dt_prop)
        for axiom in ran_set:
            result.append(axiom.toString())
        equivalent_set = self.ontology.getEquivalentDataPropertiesAxioms(dt_prop)
        for axiom in equivalent_set:
            result.append(axiom.toString())
        disjoint_set = self.ontology.getDisjointDataPropertiesAxioms(dt_prop)
        for axiom in disjoint_set:
            result.append(axiom.toString())
        funct_set = self.ontology.getFunctionalDataPropertyAxioms(dt_prop)
        for axiom in funct_set:
            result.append(axiom.toString())
        assertion_set = self.ontology.getDataPropertyAssertionAxioms(dt_prop)
        for axiom in assertion_set:
            result.append(axiom.toString())
        #General class axioms
        for axiom in gen_cl_axioms:
            if axiom.containsEntityInSignature(dt_prop):
                result.append(axiom.toString())
        return result
        '''

    def getAxiomsAsIndividual(self, gen_cl_axioms):
        result = list()
        ind = self.df.getOWLNamedIndividual(self.IRIClass.create(str(self.iri)))
        ##GENERALE
        referencing_axioms = self.ontology.getReferencingAxioms(ind)
        for axiom in referencing_axioms:
            result.append(axiom.toString())
        return result
        ##PER TIPO DI ASSIOMA
        '''
        assertion_cl_set = self.ontology.getClassAssertionAxioms(ind)
        for axiom in assertion_cl_set:
            result.append(axiom.toString())
        assertion_obj_set = self.ontology.getObjectPropertyAssertionAxioms(ind)
        for axiom in assertion_obj_set:
            result.append(axiom.toString())
        neg_assertion_obj_set = self.ontology.getNegativeObjectPropertyAssertionAxioms(ind)
        for axiom in neg_assertion_obj_set:
            result.append(axiom.toString())
        assertion_dt_set = self.ontology.getDataPropertyAssertionAxioms(ind)
        for axiom in assertion_dt_set:
            result.append(axiom.toString())
        neg_assertion_dt_set = self.ontology.getNegativeDataPropertyAssertionAxioms(ind)
        for axiom in neg_assertion_dt_set:
            result.append(axiom.toString())
        same_set = self.ontology.getSameIndividualAxioms(ind)
        for axiom in same_set:
            result.append(axiom.toString())
        diff_set = self.ontology.getDifferentIndividualAxioms(ind)
        for axiom in diff_set:
            result.append(axiom.toString())
        #General class axioms
        for axiom in gen_cl_axioms:
            if axiom.containsEntityInSignature(ind):
                result.append(axiom.toString())
        return result
        '''

    def getAxiomsAsDatatype(self, gen_cl_axioms):
        result = list()
        datatype = self.df.getOWLDatatype(self.IRIClass.create(str(self.iri)))
        ##GENERALE
        referencing_axioms = self.ontology.getReferencingAxioms(datatype)
        for axiom in referencing_axioms:
            result.append(axiom.toString())
        return result

    def computeAxioms(self):
        self.status_bar.showMessage('Computing axioms')
        gen_cl_axioms = self.ontology.getGeneralClassAxioms()
        self.axioms_by_type['Axioms involving {} as a Class'.format(str(self.iri))] = self.getAxiomsAsClass()
        self.axioms_by_type['Axioms involving {} as an ObjectProperty'.format(str(self.iri))] = self.getAxiomsAsObjectProperty(gen_cl_axioms)
        self.axioms_by_type['Axioms involving {} as a DataProperty'.format(str(self.iri))] = self.getAxiomsAsDataProperty(gen_cl_axioms)
        self.axioms_by_type['Axioms involving {} as an Individual'.format(str(self.iri))] = self.getAxiomsAsIndividual(gen_cl_axioms)
        self.axioms_by_type['Axioms involving {} as a Datatype'.format(str(self.iri))] = self.getAxiomsAsDatatype(gen_cl_axioms)
        #TODO AGGIUNGI ASSIOMI
        self.status_bar.showMessage('Axioms computed')
        self.sgnAxiomsComputed.emit()

    def getAxioms(self):
        return self.axioms_by_type

    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.sgnStarted.emit()
            # self.vm.attachThreadToJVM()
            self.initializeOWLOntology()
            self.computeAxioms()
        except Exception as e:
            LOGGER.exception('Fatal error while computing axioms.\nError:{}'.format(str(e)))
            self.sgnError.emit(e)
        finally:
            self.vm.detachThreadFromJVM()
            self.finished.emit()
