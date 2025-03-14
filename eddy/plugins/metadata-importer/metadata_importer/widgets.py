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

from abc import (
    ABCMeta,
    abstractmethod,
)
import json
import textwrap
from typing import (
    Any,
    cast,
)

from PyQt5 import (
    QtCore,
    QtGui,
    QtNetwork,
    QtWidgets,
)
from rdflib import Graph
from rdflib.namespace import NamespaceManager

from eddy.core.commands.iri import CommandIRIAddAnnotationAssertion
from eddy.core.datatypes.graphol import Item
from eddy.core.functions.misc import first
from eddy.core.functions.signals import connect
from eddy.core.metadata import (
    Entity,
    K_GRAPH,
    LiteralValue,
    MetadataRequest,
    NamedEntity,
    Repository,
)
from eddy.core.output import getLogger
from eddy.ui.fields import (
    ComboBox,
    IntegerField,
    StringField,
    TextField,
)

LOGGER = getLogger()


class MetadataImporterWidget(QtWidgets.QWidget):
    """
    This class implements the metadata importer used to search external metadata sources.
    """
    sgnItemActivated = QtCore.pyqtSignal(QtGui.QStandardItem)
    sgnItemClicked = QtCore.pyqtSignal(QtGui.QStandardItem)
    sgnItemDoubleClicked = QtCore.pyqtSignal(QtGui.QStandardItem)
    sgnItemRightClicked = QtCore.pyqtSignal(QtGui.QStandardItem)

    def __init__(self, plugin):
        """
        Initialize the metadata importer widget.
        :type plugin: Session
        """
        super().__init__(plugin.session)

        self.plugin = plugin
        self.settings = QtCore.QSettings()
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
        self.combobox = QtWidgets.QComboBox(self)
        self.combobox.addItems(map(lambda r: r.name, Repository.load()))
        self.combobox.setCurrentIndex(self.settings.value('metadata/index', 0, int))
        self.model = QtGui.QStandardItemModel(self)
        self.proxy = MetadataImporterFilterProxyModel(self)
        self.proxy.setDynamicSortFilter(False)
        self.proxy.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.proxy.setSortCaseSensitivity(QtCore.Qt.CaseSensitive)
        self.proxy.setSourceModel(self.model)
        self.entityview = MetadataImporterView(self)
        self.entityview.setModel(self.proxy)
        self.details = MetadataInfoWidget(self)

        self.searchLayout = QtWidgets.QHBoxLayout()
        self.searchLayout.setContentsMargins(0, 0, 0, 0)
        self.searchLayout.addWidget(self.search)
        self.searchLayout.addWidget(self.combobox)
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addLayout(self.searchLayout)
        self.mainLayout.addWidget(self.entityview)
        self.mainLayout.addWidget(self.details)
        self.setTabOrder(self.search, self.combobox)
        self.setTabOrder(self.combobox, self.entityview)
        self.setTabOrder(self.entityview, self.details)

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

        connect(self.entityview.activated, self.onItemActivated)
        connect(self.entityview.doubleClicked, self.onItemDoubleClicked)
        connect(self.entityview.pressed, self.onItemPressed)
        connect(self.search.textChanged, self.doFilterItem)
        connect(self.search.returnPressed, self.onReturnPressed)
        connect(self.combobox.currentIndexChanged, self.onRepositoryChanged)
        # connect(self.sgnItemActivated, self.session.doFocusItem)
        # connect(self.sgnItemDoubleClicked, self.session.doFocusItem)
        # connect(self.sgnItemRightClicked, self.session.doFocusItem)

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
    def doFilterItem(self, key):
        """
        Executed when the search box is filled with data.
        :type key: str
        """
        self.proxy.setFilterFixedString(key)
        self.proxy.sort(QtCore.Qt.AscendingOrder)

    @QtCore.pyqtSlot()
    def doUpdateState(self):
        """
        Executed to refresh the metadata widget.
        """
        repos = Repository.load()
        if len(repos) > 0:
            index = self.combobox.currentIndex()
            # Prevent signals while refreshing the combobox
            status = self.combobox.blockSignals(True)
            self.combobox.clear()
            self.combobox.addItems(map(lambda r: r.name, repos))
            self.combobox.blockSignals(status)
            # Force repetition of current selection to trigger refresh
            self.combobox.setCurrentIndex(index)
            self.combobox.currentIndexChanged.emit(index)
        else:
            self.model.clear()
            self.details.repository = None
            self.details.entity = None
            self.details.stack()

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def onItemActivated(self, index):
        """
        Executed when an item in the list view is activated (e.g. by pressing Return or Enter key).
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QtWidgets.QApplication.mouseButtons() == QtCore.Qt.NoButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item:
                self.details.entity = item.data()
                self.sgnItemActivated.emit(item)
                # KEEP FOCUS ON THE TREE VIEW UNLESS SHIFT IS PRESSED
                if QtWidgets.QApplication.queryKeyboardModifiers() & QtCore.Qt.SHIFT:
                    return
                self.entityview.setFocus()
                self.details.stack()

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def onItemDoubleClicked(self, index):
        """
        Executed when an item in the list view is double-clicked.
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QtWidgets.QApplication.mouseButtons() & QtCore.Qt.LeftButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item:
                self.details.entity = item.data()
                self.details.repository = item.data().repository
                self.sgnItemDoubleClicked.emit(item)
                self.details.stack()

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def onItemPressed(self, index):
        """
        Executed when an item in the treeview is clicked.
        :type index: QModelIndex
        """
        # noinspection PyArgumentList
        if QtWidgets.QApplication.mouseButtons() & QtCore.Qt.LeftButton:
            item = self.model.itemFromIndex(self.proxy.mapToSource(index))
            if item:
                self.details.entity = item.data()
                #self.details.repository = item.data().repository
                self.sgnItemDoubleClicked.emit(item)
                self.details.stack()

    @QtCore.pyqtSlot()
    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot(str, str)
    def onPrefixChanged(self, _name: str = None, _ns: str = None):
        """
        Executed when a project prefix is changed to update the medatata namespace manager.
        """
        # There is currently no support for unbinding a namespace in rdflib,
        # so we have to resort to recreating it from scratch.
        # See: https://github.com/RDFLib/rdflib/issues/1932
        K_GRAPH.namespace_manager = NamespaceManager(Graph(), bind_namespaces='none')
        for prefix, ns in self.project.prefixDictItems():
            K_GRAPH.bind(prefix, ns, override=True)
        self.redraw()

    @QtCore.pyqtSlot()
    def onReturnPressed(self):
        """
        Executed when the Return or Enter key is pressed in the search field.
        """
        self.focusNextChild()

    @QtCore.pyqtSlot(int)
    def onRepositoryChanged(self, index):
        """
        Executed when the selected repository in the combobox changes.
        """
        name = self.combobox.itemText(index)
        repo = first(Repository.load(), filter_on_item=lambda i: i.name == name)
        self.model.clear()
        if repo:
            self.settings.setValue('metadata/index', self.combobox.currentIndex())
            url = QtCore.QUrl(repo.uri)
            url.setPath(f'{url.path()}/classes')
            request = QtNetwork.QNetworkRequest(url)
            request.setAttribute(MetadataRequest.RepositoryAttribute, repo)
            reply = self.session.nmanager.get(request)
            connect(reply.finished, self.onRequestCompleted)
        else:
            repo = None
        self.details.repository = repo
        self.details.entity = None
        self.details.stack()

    @QtCore.pyqtSlot()
    def onRequestCompleted(self):
        """
        Executed when a metadata request has completed to update the widget.
        """
        reply = self.sender()
        try:
            reply.deleteLater()
            if reply.isFinished() and reply.error() == QtNetwork.QNetworkReply.NoError:
                data = json.loads(str(reply.readAll(), encoding='utf-8'))
                entities = [NamedEntity.from_dict(d) for d in data if "iri" in d]
                for e in entities:
                    e.repository = reply.request().attribute(MetadataRequest.RepositoryAttribute)
                    try:
                        itemText = K_GRAPH.namespace_manager.curie(e.iri, generate=False)
                    except KeyError:
                        itemText = e.iri
                    item = QtGui.QStandardItem(self.iconConcept, f"{itemText}")
                    item.setData(e)
                    self.model.appendRow(item)
                self.session.statusBar().showMessage('Metadata fetch completed')
            elif reply.isFinished() and reply.error() != QtNetwork.QNetworkReply.NoError:
                msg = f'Failed to retrieve metadata: {reply.errorString()}'
                LOGGER.warning(msg)
                self.session.statusBar().showMessage(msg)
        except Exception as e:
            LOGGER.error(f'Failed to retrieve metadata: {e}')

    #############################################
    #   INTERFACE
    #################################

    def redraw(self) -> None:
        """
        Redraw the content of the widget.
        """
        for index in range(self.model.rowCount()):
            item = self.model.item(index, 0)
            if isinstance(item.data(), NamedEntity):
                try:
                    itemText = K_GRAPH.namespace_manager.curie(item.data().iri, generate=False)
                except KeyError:
                    itemText = item.data().iri
                item.setText(itemText)
        self.entityview.update()
        self.details.redraw()

    def sizeHint(self):
        """
        Returns the recommended size for this widget.
        :rtype: QtCore.QSize
        """
        return QtCore.QSize(216, 266)


class MetadataImporterView(QtWidgets.QListView):
    """
    This class implements the metadata importer list view.
    """
    def __init__(self, parent):
        """
        Initialize the metadata importer list view.
        :type parent: MetadataImporterWidget
        """
        super().__init__(parent)
        self.startPos = None
        self.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        self.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setHorizontalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setSelectionMode(QtWidgets.QListView.SelectionMode.SingleSelection)
        self.setWordWrap(True)
        # self.setItemDelegate(MetadataImporterItemDelegate(self))

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the reference to the Session holding the MetadataImporter widget.
        :rtype: Session
        """
        return self.widget.session

    @property
    def widget(self):
        """
        Returns the reference to the MetadataImporter widget.
        :rtype: MetadataImporterWidget
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
            distance = (mouseEvent.pos() - self.startPos).manhattanLength()
            if distance >= QtWidgets.QApplication.startDragDistance():
                index = first(self.selectedIndexes())
                if index:
                    model = self.model().sourceModel()
                    index = self.model().mapToSource(index)
                    item = model.itemFromIndex(index)
                    data = item.data()
                    if data:
                        if isinstance(data, Entity):
                            mimeData = QtCore.QMimeData()
                            mimeData.setText(str(Item.ConceptNode.value))
                            buf = QtCore.QByteArray()
                            buf.append(data.name)
                            mimeData.setData(str(Item.ConceptNode.value), buf)
                            drag = QtGui.QDrag(self)
                            drag.setMimeData(mimeData)
                            drag.exec_(QtCore.Qt.CopyAction)

                            # Add assertion indicating source
                            from eddy.core.owl import IRI, AnnotationAssertion
                            subj = self.session.project.getIRI(str(data.name))  # type: IRI
                            pred = self.session.project.getIRI('urn:x-graphol:origin')
                            loc = QtCore.QUrl(data.repository.uri)
                            loc.setPath(f'{loc.path()}/entities/{data.id}'.replace('//', '/'))
                            obj = IRI(loc.toString())
                            ast = AnnotationAssertion(subj, pred, obj)
                            cmd = CommandIRIAddAnnotationAssertion(self.session.project, subj, ast)
                            self.session.undostack.push(cmd)

        super().mouseMoveEvent(mouseEvent)

    def paintEvent(self, event: QtGui.QPaintEvent):
        """
        Overrides paintEvent to display a placeholder text.
        """
        super().paintEvent(event)
        if self.model().rowCount() == 0:
            painter = QtGui.QPainter(self.viewport())
            painter.save()
            painter.setPen(self.palette().placeholderText().color())
            fm = self.fontMetrics()
            bgMsg = 'No Metadata Available'
            elided_text = fm.elidedText(bgMsg, QtCore.Qt.ElideRight, self.viewport().width())
            painter.drawText(self.viewport().rect(), QtCore.Qt.AlignCenter, elided_text)
            painter.restore()

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


class MetadataImporterFilterProxyModel(QtCore.QSortFilterProxyModel):
    """
    Extends QSortFilterProxyModel adding filtering functionalities for the metadata importer
    """
    def __init__(self, parent=None):
        super().__init__(parent)

    #############################################
    #   INTERFACE
    #################################

    def filterAcceptsRow(self, sourceRow: int, sourceParent: QtCore.QModelIndex) -> bool:
        """
        Overrides filterAcceptsRow to include extra filtering conditions
        :type sourceRow: int
        :type sourceParent: QModelIndex
        :rtype: bool
        """
        return sourceParent.isValid() or super().filterAcceptsRow(sourceRow, sourceParent)


class MetadataInfoWidget(QtWidgets.QScrollArea):
    """
    This class implements the metadata detail widget.
    """
    def __init__(self, parent: QtWidgets.QWidget) -> None:
        """
        Initialize the metadata info box.
        """
        super().__init__(parent)

        self.repository = None
        self.entity = None
        self.stacked = QtWidgets.QStackedWidget(self)
        self.stacked.setContentsMargins(0, 0, 0, 0)
        self.infoEmpty = EmptyInfo(self.stacked)
        self.infoRepository = RepositoryInfo(self.stacked)
        self.infoEntity = EntityInfo(self.stacked)
        self.stacked.addWidget(self.infoEmpty)
        self.stacked.addWidget(self.infoRepository)
        self.stacked.addWidget(self.infoEntity)
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(QtCore.QSize(216, 120))
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setWidget(self.stacked)
        self.setWidgetResizable(True)

        self.setStyleSheet("""
        MetadataInfoWidget {
          background: #FFFFFF;
        }
        MetadataInfoWidget Header {
          background: #5A5050;
          padding-left: 4px;
          color: #FFFFFF;
        }
        MetadataInfoWidget Key {
          background: #BBDEFB;
          border-top: none;
          border-right: none;
          border-bottom: 1px solid #BBDEFB;
          border-left: none;
          padding: 0 0 0 4px;
        }
        MetadataInfoWidget Button,
        MetadataInfoWidget Button:focus,
        MetadataInfoWidget Button:hover,
        MetadataInfoWidget Button:hover:focus,
        MetadataInfoWidget Button:pressed,
        MetadataInfoWidget Button:pressed:focus,
        MetadataInfoWidget Text,
        MetadataInfoWidget Integer,
        MetadataInfoWidget String,
        MetadataInfoWidget Select,
        MetadataInfoWidget Parent {
          background: #E3F2FD;
          border-top: none;
          border-right: none;
          border-bottom: 1px solid #BBDEFB !important;
          border-left: 1px solid #BBDEFB !important;
          padding: 0 0 0 4px;
          text-align:left;
        }
        MetadataInfoWidget Button::menu-indicator {
          image: none;
        }
        MetadataInfoWidget Select:!editable,
        MetadataInfoWidget Select::drop-down:editable {
          background: #FFFFFF;
        }
        MetadataInfoWidget Select:!editable:on,
        MetadataInfoWidget Select::drop-down:editable:on {
          background: #FFFFFF;
        }
        MetadataInfoWidget QCheckBox {
          background: #FFFFFF;
          spacing: 0;
          margin-left: 4px;
          margin-top: 2px;
        }
        MetadataInfoWidget QCheckBox::indicator:disabled {
          background-color: #BABABA;
        }
        """)

        scrollbar = self.verticalScrollBar()
        scrollbar.installEventFilter(self)

    #############################################
    #   EVENTS
    #################################

    def eventFilter(self, source: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """
        Filter incoming events.
        """
        if source is self.verticalScrollBar():
            if event.type() in {QtCore.QEvent.Show, QtCore.QEvent.Hide}:
                self.redraw()
        return super().eventFilter(source, event)

    #############################################
    #   INTERFACE
    #################################

    def redraw(self) -> None:
        """
        Redraw the content of the widget.
        """
        width = self.width()
        scrollbar = self.verticalScrollBar()
        if scrollbar.isVisible():
            width -= scrollbar.width()
        widget = self.stacked.currentWidget()
        widget.setFixedWidth(width)
        sizeHint = widget.sizeHint()
        height = sizeHint.height()
        self.stacked.setFixedWidth(width)
        # self.stacked.setFixedHeight(clamp(height, 0))

    def stack(self) -> None:
        """
        Set the current stacked widget.
        """
        if self.entity:
            show = self.infoEntity
            show.updateData(self.repository, self.entity)
        elif self.repository:
            show = self.infoRepository
            show.updateData(self.repository)
        else:
            show = self.infoEmpty

        prev = self.stacked.currentWidget()
        self.stacked.setCurrentWidget(show)
        self.redraw()
        if prev is not show:
            scrollbar = self.verticalScrollBar()
            scrollbar.setValue(0)


#############################################
#   COMPONENTS
#################################


class Header(QtWidgets.QLabel):
    """
    This class implements the header of properties section.
    """
    def __init__(self, *args: Any) -> None:
        """
        Initialize the header.
        """
        super().__init__(*args)
        self.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.setFixedHeight(24)


class Key(QtWidgets.QLabel):
    """
    This class implements the key of an info field.
    """
    def __init__(self, *args: Any) -> None:
        """
        Initialize the key.
        """
        super().__init__(*args)
        self.setFixedSize(88, 20)


class Button(QtWidgets.QPushButton):
    """
    This class implements the button to which associate a QtWidgets.QMenu instance of an info field.
    """
    def __init__(self,  *args: Any) -> None:
        """
        Initialize the button.
        """
        super().__init__(*args)


class Integer(IntegerField):
    """
    This class implements the integer value of an info field.
    """
    def __init__(self,  *args: Any) -> None:
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)


class String(StringField):
    """
    This class implements the string value of an info field.
    """
    def __init__(self,  *args: Any) -> None:
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)
        self.setReadOnly(True)


class Text(TextField):
    """
    This class implements the string value of an info field.
    """
    def __init__(self,  *args: Any) -> None:
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20 * (self.document().lineCount() + 1))
        self.setReadOnly(True)


class Select(ComboBox):
    """
    This class implements the selection box of an info field.
    """
    def __init__(self,  *args: Any) -> None:
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setScrollEnabled(False)


class Parent(QtWidgets.QWidget):
    """
    This class implements the parent placeholder to be used
    to store checkbox and radio button value fields.
    """
    def __init__(self,  *args: Any) -> None:
        """
        Initialize the field.
        """
        super().__init__(*args)
        self.setFixedHeight(20)

    def paintEvent(self, paintEvent: QtGui.QPaintEvent) -> None:
        """
        This is needed for the widget to pick the stylesheet.
        """
        option = QtWidgets.QStyleOption()
        option.initFrom(self)
        painter = QtGui.QPainter(self)
        style = self.style()
        style.drawPrimitive(QtWidgets.QStyle.PE_Widget, option, painter, self)


#############################################
#   INFO WIDGETS
#################################

class AbstractInfo(QtWidgets.QWidget):
    """
    This class implements the base information box.
    """
    __metaclass__ = ABCMeta

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize the base information box.
        """
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)

    #############################################
    #   INTERFACE
    #################################

    @abstractmethod
    def updateData(self, **kwargs: Any) -> None:
        """
        Fetch new information and fill the widget with data.
        """
        pass


class RepositoryInfo(AbstractInfo):
    """
    This class implements the repository information box.
    """
    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize the repository information box.
        """
        super().__init__(parent)

        self.nameKey = Key('Name', self)
        self.nameField = String(self)
        self.nameField.setReadOnly(True)

        self.uriKey = Key('Location', self)
        self.uriField = String(self)
        self.uriField.setReadOnly(True)

        self.versionKey = Key('Version', self)
        self.versionField = String(self)
        self.versionField.setReadOnly(True)

        self.infoHeader = Header('Repository Info', self)
        self.infoLayout = QtWidgets.QFormLayout()
        self.infoLayout.setSpacing(0)
        self.infoLayout.addRow(self.nameKey, self.nameField)
        self.infoLayout.addRow(self.uriKey, self.uriField)
        self.infoLayout.addRow(self.versionKey, self.versionField)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.insertWidget(0, self.infoHeader)
        self.mainLayout.insertLayout(1, self.infoLayout)

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, repository: Repository) -> None:
        """
        Fetch new information and fill the widget with data.
        """
        self.nameField.setValue(repository.name)
        self.uriField.setValue(repository.uri)
        self.versionField.setValue('1.0')


class EntityInfo(AbstractInfo):
    """
    This class implements the information box for entities.
    """
    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        """
        Initialize the generic node information box.
        """
        super().__init__(parent)

        self.entity = None
        self.repoKey = Key('Repository', self)
        self.repoField = String(self)
        self.repoField.setReadOnly(True)

        self.idKey = Key('Entity ID', self)
        self.idField = String(self)
        self.idField.setReadOnly(True)

        self.iriKey = Key('Entity IRI', self)
        self.iriField = String(self)
        self.iriField.setReadOnly(True)

        self.nodePropHeader = Header('Entity properties', self)
        self.nodePropLayout = QtWidgets.QFormLayout()
        self.nodePropLayout.setSpacing(0)
        self.nodePropLayout.addRow(self.repoKey, self.repoField)
        self.nodePropLayout.addRow(self.idKey, self.idField)
        self.nodePropLayout.addRow(self.iriKey, self.iriField)

        self.typesHeader = Header('Entity Types', self)
        self.typesLayout = QtWidgets.QFormLayout()
        self.typesLayout.setSpacing(0)

        self.metadataHeader = Header('Entity Annotations', self)
        self.metadataLayout = QtWidgets.QFormLayout()
        self.metadataLayout.setSpacing(0)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.nodePropHeader)
        self.mainLayout.addLayout(self.nodePropLayout)
        self.mainLayout.addWidget(self.typesHeader)
        self.mainLayout.addLayout(self.typesLayout)
        self.mainLayout.addWidget(self.metadataHeader)
        self.mainLayout.addLayout(self.metadataLayout)

    #############################################
    #   INTERFACE
    #################################

    def updateData(self, repository: Repository, entity: Entity) -> None:
        """
        Fetch new information and fill the widget with data.
        """
        self.repoField.setValue(repository.uri)
        self.idField.setValue(entity.id)
        self.iriField.setValue(entity.name)

        # ENTITY TYPES
        while self.typesLayout.rowCount() > 0:
            self.typesLayout.removeRow(0)
        for t in entity.types:
            self.typesLayout.addRow(Key('Type', self), String(t.name, self))

        # ENTITY ANNOTATIONS
        while self.metadataLayout.rowCount() > 0:
            self.metadataLayout.removeRow(0)
        for a in entity.annotations:
            self.metadataLayout.addRow(Key('Property', self), String(a.predicate.n3(), self))
            if isinstance(a.object, LiteralValue):
                literal = cast(LiteralValue, a.object)
                value, lang, dtype = literal.value, literal.language, literal.datatype
                self.metadataLayout.addRow(Key('Value', self), Text(value, self))
                if lang:
                    self.metadataLayout.addRow(Key('lang', self), String(lang, self))
                if dtype:
                    self.metadataLayout.addRow(Key('dtype', self), String(dtype.n3(), self))
            else:
                self.metadataLayout.addRow(Key('Entity', self), String(a.object.n3(), self))
            self.metadataLayout.addItem(QtWidgets.QSpacerItem(10, 2))


class EmptyInfo(QtWidgets.QTextEdit):
    """
    This class implements the information box when there is no metadata repository.
    """

    #############################################
    #   INTERFACE
    #################################

    def paintEvent(self, event: QtGui.QPaintEvent):
        """
        Overrides paintEvent to display a placeholder text.
        """
        super().paintEvent(event)
        painter = QtGui.QPainter(self.viewport())
        painter.save()
        painter.setPen(self.palette().placeholderText().color())
        fm = self.fontMetrics()
        bgMsg = textwrap.dedent("""
        To start using the 'Metadata Importer', add a repository location
        in the 'Ontology Manager -> Metadata Repositories' tab.
        """)
        elided_text = fm.elidedText(bgMsg, QtCore.Qt.ElideRight, self.viewport().width())
        painter.drawText(self.viewport().rect(), QtCore.Qt.AlignCenter, elided_text)
        painter.restore()
