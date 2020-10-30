from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy.core.common import HasWidgetSystem, HasThreadingSystem
from eddy.core.functions.signals import connect
from eddy.core.output import getLogger
from eddy.core.owl import IRI
from eddy.ui.consistency_check import EmptyEntityExplanationWorker
from eddy.ui.fields import StringField

LOGGER = getLogger()


class LabelDialog(QtWidgets.QDialog, HasWidgetSystem):
    """
    This class implements the No matching label IRIs dialog.
    """

    def __init__(self, session, iris):
        """
        Initialize the Label dialog.
        :type session: Session
        :type explanations: list
        """
        # super().__init__()
        super().__init__(session)
        self.iris = iris
        self.project = session.project

        #############################################
        # EXPLANATIONS TAB
        #################################

        labelWidget = LabelExplorerWidget(self.project, self.session,
                                                      objectName='label_widget')
        self.addWidget(labelWidget)

        #############################################
        # MAIN WIDGET
        #################################


        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self,
                                                  objectName='confirmation_widget')
        doneBtn = QtWidgets.QPushButton('Done', objectName='done_button')
        confirmation.addButton(doneBtn, QtWidgets.QDialogButtonBox.AcceptRole)
        confirmation.setContentsMargins(10, 0, 10, 10)
        self.addWidget(confirmation)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('label_widget'))
        layout.addWidget(self.widget('confirmation_widget'), 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
        self.setMinimumSize(800, 520)
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        title = 'IRIs with no matching labels'
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
        explanationWidget = self.widget('label_widget')
        explanationWidget.doClear()
        explanationWidget.setIRIs(self.iris)
        self.setWindowModality(QtCore.Qt.NonModal)


#############################################
#   Label WIDGET
#################################

class LabelExplorerWidget(QtWidgets.QWidget):
    """
    This class implements the Label explorer used to list iris with no labels referencing their simple names.
    """
    sgnItemClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnItemDoubleClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnItemRightClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnFakeItemAdded = QtCore.pyqtSignal('QGraphicsScene', 'QGraphicsItem')
    sgnColourItem = QtCore.pyqtSignal('QStandardItem')

    def __init__(self, project, session, **kwargs):
        """
        Initialize the label explorer widget.
        """
        super().__init__(session, objectName=kwargs.get('objectName'))

        self.project = project
        self.iris = None

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
        self.proxy = LabelExplorerFilterProxyModel(self)
        self.proxy.setDynamicSortFilter(False)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setSortCaseSensitivity(QtCore.Qt.CaseSensitive)
        self.proxy.setSourceModel(self.model)
        self.ontoview = LabelExplorerView(self)
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

    @QtCore.pyqtSlot(IRI)
    def doAddIRI(self, iri):
        iri_to_add = QtGui.QStandardItem(
            '{}'.format(str(iri)))
        iri_to_add.setData(iri)
        self.model.appendRow(iri_to_add)
        self.proxy.sort(0, QtCore.Qt.AscendingOrder)
        return iri_to_add

    @QtCore.pyqtSlot('QStandardItem', str)
    def doAddLabel(self, q_item, label):
        label_to_add = QtGui.QStandardItem(label)
        label_to_add.setData(label)
        q_item.appendRow(label_to_add)
        self.proxy.sort(0, QtCore.Qt.AscendingOrder)



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



    #############################################
    #   INTERFACE
    #################################
    def setIRIs(self, iris):
        self.iris = iris
        for iri in self.iris:
            iriItem = self.doAddIRI(iri)
            for label in iri.getAllLabelAnnotationAssertions():
                self.doAddLabel(iriItem, label.getObjectResourceString(True))
        self.proxy.invalidateFilter()
        self.proxy.sort(0, QtCore.Qt.AscendingOrder)

    def sizeHint(self):
        """
        Returns the recommended size for this widget.
        :rtype: QtCore.QSize
        """
        return QtCore.QSize(216, 266)


class LabelExplorerView(QtWidgets.QTreeView):
    """
    This class implements the Label explorer tree view.
    """

    def __init__(self, widget):
        """
        Initialize the Label explorer view.
        :type widget: LabelExplorerWidget
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
        :rtype: ExplanationExplorerWidget
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


class LabelExplorerFilterProxyModel(QtCore.QSortFilterProxyModel):
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


