from PyQt5 import QtWidgets, QtCore, QtGui

from eddy.core.common import HasWidgetSystem
from eddy.core.datatypes.qt import Font
from eddy.core.functions.signals import connect
from eddy.core.owl import AnnotationAssertion
from eddy.ui.fields import ComboBox


class AnnotationAssertionBuilderDialog(QtWidgets.QDialog, HasWidgetSystem):

    sgnAnnotationAssertionAccepted = QtCore.pyqtSignal(AnnotationAssertion)
    sgnAnnotationAssertionRejected = QtCore.pyqtSignal()

    emptyString = ''

    def __init__(self,iri,session):
        """
        Initialize the annotation assertion builder dialog (subject IRI = iri).
        :type iri: IRI
        :type session: Session
        """
        super().__init__(session)
        self.project = session.project
        self.iri = iri
        '''
        widget = AnnotationPropertyExplorerWidget(session)
        widget.setObjectName('annotation_property_explorer')
        #widget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Maximum)
        self.addWidget(widget)

        self.setMinimumSize(740, 420)
        self.setWindowTitle('Annotation assertion builder')

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.widget('annotation_property_explorer'))

        self.setLayout(layout)
        '''

        comboBoxLabel = QtWidgets.QLabel(self, objectName='property_combobox_label')
        comboBoxLabel.setFont(Font('Roboto', 12))
        comboBoxLabel.setText('Property')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='property_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(True)
        combobox.addItem(self.emptyString)
        combobox.addItems([str(x) for x in self.project.getAnnotationPropertyIRIs()])
        combobox.setCurrentText(self.emptyString)
        self.addWidget(combobox)
        connect(combobox.currentIndexChanged, self.onPropertySwitched)

        '''
        formlayout = QtWidgets.QFormLayout(self, objectName='property_layout')
        formlayout.addRow(self.widget('property_combobox_label'), self.widget('property_switch'))
        self.addWidget(formlayout)
        '''

        textArea = QtWidgets.QTextEdit(self, objectName='valueTextArea')
        textArea.setFont(Font('Roboto', 12))
        self.addWidget(textArea)


        comboBoxLabel = QtWidgets.QLabel(self, objectName='type_combobox_label')
        comboBoxLabel.setFont(Font('Roboto', 12))
        comboBoxLabel.setText('Type')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='type_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(True)
        combobox.addItem(self.emptyString)
        combobox.addItems([str(x) for x in self.project.getDatatypeIRIs()])
        combobox.setCurrentText(self.emptyString)
        self.addWidget(combobox)
        connect(combobox.currentIndexChanged,self.onTypeSwitched)
        '''
        boxlayout = QtWidgets.QHBoxLayout(self, objectName='type_layout')
        boxlayout.setAlignment(QtCore.Qt.AlignLeft)
        boxlayout.addWidget(self.widget('type_combobox_label'))
        boxlayout.addWidget(self.widget('type_switch'))
        self.addWidget(boxlayout)
        '''

        comboBoxLabel = QtWidgets.QLabel(self, objectName='lang_combobox_label')
        comboBoxLabel.setFont(Font('Roboto', 12))
        comboBoxLabel.setText('Lang')
        self.addWidget(comboBoxLabel)
        combobox = ComboBox(self, objectName='lang_switch')
        combobox.setEditable(False)
        combobox.setFont(Font('Roboto', 12))
        combobox.setFocusPolicy(QtCore.Qt.StrongFocus)
        combobox.setScrollEnabled(True)
        combobox.addItem(self.emptyString)
        combobox.addItems(['it','eng'])
        combobox.setCurrentText(self.emptyString)
        self.addWidget(combobox)

        '''
        boxlayout = QtWidgets.QHBoxLayout(self, objectName='lang_layout')
        boxlayout.setAlignment(QtCore.Qt.AlignLeft)
        boxlayout.addWidget(self.widget('lang_combobox_label'))
        boxlayout.addWidget(self.widget('lang_switch'))
        self.addWidget(boxlayout)

        
        boxlayout = QtWidgets.QHBoxLayout(self, objectName='type_lang_layout')
        boxlayout.setAlignment(QtCore.Qt.AlignLeft)
        boxlayout.addWidget(self.widget('type_layout'))
        boxlayout.addWidget(self.widget('lang_layout'))
        

        formlayout = QtWidgets.QFormLayout(self, objectName='type_lang_layout')
        formlayout.addRow(self.widget('type_layout'))
        formlayout.addRow(self.widget('lang_layout'))
        self.addWidget(formlayout)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('valueTextArea'))
        formlayout.addRow(self.widget('type_lang_layout'))

        groupbox = QtWidgets.QGroupBox('Object resource', self, objectName='object_resource_widget')
        groupbox.setLayout(formlayout)
        self.addWidget(groupbox)
        '''

        #############################################
        # CONFIRMATION BOX
        #################################

        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self, objectName='confirmation_widget')
        confirmation.addButton(QtWidgets.QDialogButtonBox.Save)
        confirmation.addButton(QtWidgets.QDialogButtonBox.Cancel)
        confirmation.setContentsMargins(10, 0, 10, 10)
        confirmation.setFont(Font('Roboto', 12))
        confirmation.button(QtWidgets.QDialogButtonBox.Save).setEnabled(False)
        self.addWidget(confirmation)
        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.widget('property_combobox_label'), self.widget('property_switch'))
        formlayout.addRow(self.widget('valueTextArea'))
        formlayout.addRow(self.widget('type_combobox_label'), self.widget('type_switch'))
        formlayout.addRow(self.widget('lang_combobox_label'), self.widget('lang_switch'))
        formlayout.addRow(self.widget('confirmation_widget'))

        self.setLayout(formlayout)

        self.setMinimumSize(740, 380)
        self.setWindowTitle('Annotation assertion builder <{}>'.format(str(iri)))

    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot(int)
    def onPropertySwitched(self, index):
        propIRI = str(self.widget('property_switch').itemText(index))
        if propIRI and not propIRI==self.emptyString:
            self.widget('confirmation_widget').button(QtWidgets.QDialogButtonBox.Save).setEnabled(True)
        else:
            self.widget('confirmation_widget').button(QtWidgets.QDialogButtonBox.Save).setEnabled(False)

    @QtCore.pyqtSlot(int)
    def onTypeSwitched(self, index):
        typeIRI = str(self.widget('type_switch').itemText(index))
        if not self.project.canAddLanguageTag(typeIRI):
            self.widget('lang_switch').setEnabled(False)
        else:
            self.widget('lang_switch').setEnabled(True)

    @QtCore.pyqtSlot()
    def accept(self):
        propertyStr = str(self.widget('property_switch').currentText())
        propertyIRI = self.project.getIRI(propertyStr)
        value = str(self.widget('valueTextArea').toPlainText())
        typeStr = str(self.widget('type_switch').currentText())
        typeIRI = None
        if typeStr and not typeStr==self.emptyString:
            typeIRI = self.project.getIRI(typeStr)
        language = None
        if self.widget('lang_switch').isEnabled():
            language = str(self.widget('type_switch').currentText())
        annAss = AnnotationAssertion(propertyIRI,value,typeIRI,language)
        self.iri.addAnnotationAssertion(annAss)
        self.accepted.emit()
        super().accept()

    @QtCore.pyqtSlot()
    def reject(self):
        self.rejected.emit()
        super().reject()

class AnnotationPropertyExplorerWidget(QtWidgets.QWidget):
    """
    This class implements the ontology explorer used to list ontology predicates.
    """
    sgnItemActivated = QtCore.pyqtSignal('QGraphicsItem')
    sgnItemClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnItemDoubleClicked = QtCore.pyqtSignal('QGraphicsItem')
    sgnItemRightClicked = QtCore.pyqtSignal('QGraphicsItem')

    def __init__(self, session):
        """
        Initialize the ontology explorer widget.
        :type plugin: Session
        """
        super().__init__(session)

        self.iconRole = QtGui.QIcon(':/icons/18/ic_treeview_role')

        self.project = session.project

        self.model = QtGui.QStandardItemModel(self)
        self.propView = AnnotationPropertyExplorerView(self)
        self.propView.setModel(self.model)
        self.setContentsMargins(0, 0, 0, 0)
        #self.setMinimumWidth(216)

        #self.setMinimumHeight(420)

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

        self.populateAnnotationPropertyView()

        header = self.propView.header()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        #header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        header.setStretchLastSection(False)


        print('COLUMN COUNT = {}'.format(self.model.columnCount()))

    def populateAnnotationPropertyView(self):
        annotationProperties = self.project.getAnnotationPropertyIRIs()
        for propIRI in annotationProperties:
            item = QtGui.QStandardItem(str(propIRI))
            item.setData(propIRI)
            self.model.appendRow(item)

class AnnotationPropertyExplorerView(QtWidgets.QTreeView):
    """
    This class implements the annotation property explorer tree view.
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
        self.setFont(Font('Roboto', 14))
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setHeaderHidden(True)
        self.setHorizontalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setSelectionMode(QtWidgets.QTreeView.SingleSelection)
        self.setSortingEnabled(True)
        self.setWordWrap(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(420)
        #self.column
        #self.resizeColumnToContents(0)

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


