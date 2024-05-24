import os
from urllib.parse import urlparse

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QRadioButton, QButtonGroup, QAbstractButton

from eddy.core.commands.project import CommandProjectAddOntologyImport
from eddy.core.common import HasWidgetSystem, HasThreadingSystem
from eddy.core.datatypes.system import File
from eddy.core.functions.misc import first
from eddy.core.functions.signals import connect
from eddy.core.loaders.owl2 import OwlOntologyImportWorker
from eddy.core.output import getLogger
from eddy.core.owl import ImportedOntology
from eddy.ui.fields import StringField
from eddy.ui.file import FileDialog

LOGGER = getLogger()


class ImportOntologyDialog(QtWidgets.QDialog, HasWidgetSystem, HasThreadingSystem):
    sgnOntologyImportAccepted = QtCore.pyqtSignal(ImportedOntology)
    sgnOntologyImportCorrectlyReloaded = QtCore.pyqtSignal(ImportedOntology)
    sgnOntologyImportRejected = QtCore.pyqtSignal()

    IMPORT_THREAD_NAME = 'OWL2OntologyImport'

    def __init__(self, session, importedOntology=None):
        """
        Initialize the OWL ontology import dialog.
        :type session: Session
        :type importedOntology: ImportedOntology
        """
        super().__init__(session)
        self.session = session
        self.project = session.project
        self.importedOntology = importedOntology
        self.isReloadAttempt = not importedOntology is None
        self.classes = set()
        self.objectProperties = set()
        self.dataProperties = set()
        self.individuals = set()
        self.missingImports = dict()
        self.step = 0

        self.stacked = QtWidgets.QStackedWidget(self)
        self.stacked.setContentsMargins(0, 0, 0, 0)

        self.widgetImportType = ImportTypeWidget(self.session, self.stacked)
        self.widgetLocalImport = LocalFileWidget(self.session, self.stacked)
        connect(self.widgetLocalImport.sgnValidPath,self.onValidFilePath)
        connect(self.widgetLocalImport.sgnNotValidPath, self.onNonValidFilePath)
        self.widgetRemoteImport = WebFileWidget(self.session, self.stacked)
        connect(self.widgetRemoteImport.sgnValidURI, self.onValidURI)
        connect(self.widgetRemoteImport.sgnNotValidURI, self.onNonValidURI)
        self.widgetVerify = VerifyWidget(self.session, self.stacked)
        self.widgetConfirm = ConfirmWidget(self.session, parent=self.stacked)
        self.widgetError = ErrorWidget(self.session, parent=self.stacked)

        self.stacked.addWidget(self.widgetImportType)
        self.stacked.addWidget(self.widgetLocalImport)
        self.stacked.addWidget(self.widgetRemoteImport)
        self.stacked.addWidget(self.widgetVerify)
        self.stacked.addWidget(self.widgetConfirm)
        self.stacked.addWidget(self.widgetError)

        self.stacked.setCurrentWidget(self.widgetImportType)

        #############################################
        # CONFIRMATION AND NAVIGATION BOX
        #################################
        backBtn = QtWidgets.QPushButton('Back', objectName='back_button')
        connect(backBtn.clicked, self.onBackClicked)
        backBtn.setEnabled(False)
        self.addWidget(backBtn)
        continueBtn = QtWidgets.QPushButton('Continue', objectName='continue_button')
        connect(continueBtn.clicked, self.onContinueClicked)
        self.addWidget(continueBtn)
        saveBtn = QtWidgets.QPushButton('Save', objectName='save_button')
        saveBtn.setEnabled(False)
        self.addWidget(saveBtn)
        cancelBtn = QtWidgets.QPushButton('Cancel', objectName='cancel_button')
        self.addWidget(cancelBtn)
        confirmation = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal, self, objectName='confirmation_widget')
        confirmation.addButton(backBtn, QtWidgets.QDialogButtonBox.ActionRole)
        confirmation.addButton(continueBtn, QtWidgets.QDialogButtonBox.ActionRole)
        confirmation.addButton(saveBtn, QtWidgets.QDialogButtonBox.AcceptRole)
        confirmation.addButton(cancelBtn, QtWidgets.QDialogButtonBox.RejectRole)
        confirmation.setContentsMargins(10, 0, 10, 10)
        self.addWidget(confirmation)
        connect(confirmation.accepted, self.accept)
        connect(confirmation.rejected, self.reject)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.stacked)
        formlayout.addRow(self.widget('confirmation_widget'))

        self.setLayout(formlayout)

        self.setMinimumSize(740, 380)
        if not self.isReloadAttempt:
            self.setWindowTitle('Import ontology')
            self.redraw()
        else:
            self.setWindowTitle('Reload ontology <{}>'.format(str(self.importedOntology.ontologyIRI)))
            self.step = 2
            self.startImportProcess()


    def redraw(self):
        """
        Redraw the dialog components, reloading their contents.
        """
        if self.step==0:
            self.stacked.setCurrentWidget(self.widgetImportType)
        elif self.step==1:
            if self.widgetImportType.getSelectedRadioId()==0:
                self.stacked.setCurrentWidget(self.widgetLocalImport)
            elif self.widgetImportType.getSelectedRadioId()==1:
                self.stacked.setCurrentWidget(self.widgetRemoteImport)
        elif self.step==2:
            self.stacked.setCurrentWidget(self.widgetVerify)
        elif self.step==3:
            self.stacked.setCurrentWidget(self.widgetConfirm)
        elif self.step==4:
            self.stacked.setCurrentWidget(self.widgetError)

        self.widget('back_button').setEnabled(self.isBackButtonEnabled())
        self.widget('continue_button').setEnabled(self.isContinueButtonEnabled())
        self.widget('save_button').setEnabled(self.isSaveButtonEnabled())
        self.widget('cancel_button').setEnabled(self.isCancelButtonEnabled())

    def isBackButtonEnabled(self):
        widget = self.stacked.currentWidget()
        return not (widget is self.widgetImportType or widget is self.widgetVerify)

    def isContinueButtonEnabled(self):
        widget = self.stacked.currentWidget()
        return widget is self.widgetImportType or (widget is self.widgetLocalImport and widget.isValidPath) or (widget is self.widgetRemoteImport and widget.isValidUri)

    def isSaveButtonEnabled(self):
        widget = self.stacked.currentWidget()
        return widget is self.widgetConfirm

    def isCancelButtonEnabled(self):
        widget = self.stacked.currentWidget()
        return not widget is self.widgetVerify

    def startImportProcess(self):
        self.worker = None
        if not self.isReloadAttempt:
            current = self.stacked.currentWidget()
            if current is self.widgetLocalImport:
                self.worker = OwlOntologyImportWorker(current.pathField.value(), self.session)
            elif current is self.widgetRemoteImport:
                self.worker = OwlOntologyImportWorker(current.uriField.value(), self.session, isLocalImport=False)
        else:
            self.worker = OwlOntologyImportWorker(self.importedOntology.docLocation, self.session, isLocalImport=self.importedOntology.isLocalDocument, isReloadAttempt=True)
        connect(self.worker.sgnCompleted, self.onImportCompleted)
        connect(self.worker.sgnErrored, self.onImportError)
        connect(self.worker.sgnStepPerformed, self.widgetVerify.progressStep)
        connect(self.worker.sgnOntologyDocumentLoaded, self.onOntologyDocumentLoaded)
        connect(self.worker.sgnClassFetched, self.onClassFetched)
        connect(self.worker.sgnObjectPropertyFetched, self.onObjectPropertyFetched)
        connect(self.worker.sgnDataPropertyFetched, self.onDataPropertyFetched)
        connect(self.worker.sgnIndividualFetched, self.onIndividualFetched)
        connect(self.worker.sgnMissingOntologyImportFound, self.onMissingOntologyImportFound)
        self.redraw()
        self.startThread(self.IMPORT_THREAD_NAME, self.worker)

    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot(str,str,str,bool)
    def onOntologyDocumentLoaded(self,ontIri, docLoc, versionIri, isLocal):
        if not self.isReloadAttempt:
            self.importedOntology = ImportedOntology(ontIri, docLoc, versionIri, isLocal, self.project)

    @QtCore.pyqtSlot(str)
    def onClassFetched(self, iri):
        self.classes.add(self.project.getIRI(iri,imported=True))

    @QtCore.pyqtSlot(str)
    def onObjectPropertyFetched(self, iri):
        self.objectProperties.add(self.project.getIRI(iri, imported=True))

    @QtCore.pyqtSlot(str)
    def onDataPropertyFetched(self, iri):
        self.dataProperties.add(self.project.getIRI(iri, imported=True))

    @QtCore.pyqtSlot(str)
    def onIndividualFetched(self, iri):
        self.individuals.add(self.project.getIRI(iri, imported=True))

    @QtCore.pyqtSlot()
    def accept(self):
        """
        Executed when the dialog is accepted.
        """
        if not self.isReloadAttempt:
            command = CommandProjectAddOntologyImport(self.project, self.importedOntology)
            self.session.undostack.beginMacro('Add ontology import {0} '.format(self.importedOntology.docLocation))
            if command:
                self.session.undostack.push(command)
            self.session.undostack.endMacro()
            self.sgnOntologyImportAccepted.emit(self.importedOntology)
        else:
            self.project.sgnImportedOntologyLoaded.emit(self.importedOntology)
            self.sgnOntologyImportCorrectlyReloaded.emit(self.importedOntology)
        super().accept()

    @QtCore.pyqtSlot()
    def reject(self):
        """
        Executed when the dialog is accepted.
        """
        super().reject()

    @QtCore.pyqtSlot(bool)
    def onBackClicked(self, _):
        """
        Back button pressed
        :type _: bool
        """
        if not self.isReloadAttempt:
            if self.step==3:
                self.step -= 2
            elif self.step==4:
                self.step -=3
            else:
                self.step -= 1
            self.redraw()
        else:
            if self.step==3:
                self.step -= 1
            elif self.step==4:
                self.step -=2
            self.startImportProcess()

    @QtCore.pyqtSlot(bool)
    def onContinueClicked(self, _):
        """
        Back button pressed
        :type _: bool
        """
        if self.step==0:
            self.step += 1
            self.redraw()
        elif self.step==1:
            self.step += 1
            self.startImportProcess()
        else:
            self.step += 1
            self.redraw()

    @QtCore.pyqtSlot()
    def onValidFilePath(self):
        widget = self.stacked.currentWidget()
        if widget is self.widgetLocalImport:
            self.widget('continue_button').setEnabled(True)

    @QtCore.pyqtSlot()
    def onNonValidFilePath(self):
        widget = self.stacked.currentWidget()
        if widget is self.widgetLocalImport:
            self.widget('continue_button').setEnabled(False)

    @QtCore.pyqtSlot()
    def onValidURI(self):
        widget = self.stacked.currentWidget()
        if widget is self.widgetRemoteImport:
            self.widget('continue_button').setEnabled(True)

    @QtCore.pyqtSlot()
    def onNonValidURI(self):
        widget = self.stacked.currentWidget()
        if widget is self.widgetRemoteImport:
            self.widget('continue_button').setEnabled(True)

    @QtCore.pyqtSlot(str, str)
    def onMissingOntologyImportFound(self, ontIri, excMsg):
        self.missingImports[ontIri] = excMsg
        LOGGER.exception('Failed to load imported ontology at {}\n{}'.format(ontIri, excMsg))

    @QtCore.pyqtSlot()
    def onImportCompleted(self):
        for iri in self.classes:
            self.importedOntology.addClass(iri)
        for iri in self.objectProperties:
            self.importedOntology.addObjectProperty(iri)
        for iri in self.dataProperties:
            self.importedOntology.addDataProperty(iri)
        for iri in self.individuals:
            self.importedOntology.addIndividual(iri)
        self.importedOntology.correctlyLoaded=True
        self.widgetVerify.progressStep(0)
        if self.missingImports:
            self.widgetConfirm.msgLabel.setText('The following ontology will be imported:\n(With errors, check the log for more details)')
        self.widgetConfirm.locationText.setValue('{}'.format(self.importedOntology.docLocation))
        self.widgetConfirm.iriText.setValue('{}'.format(self.importedOntology.ontologyIRI))
        self.widgetConfirm.versionText.setValue('{}'.format(self.importedOntology.versionIRI))
        self.stopThread(self.IMPORT_THREAD_NAME)
        self.step += 1
        self.redraw()

    @QtCore.pyqtSlot(str, Exception)
    def onImportError(self, location, exc):
        self.classes = set()
        self.objectProperties = set()
        self.dataProperties = set()
        self.individuals = set()
        self.widgetVerify.progressStep(0)
        self.widgetError.locationText.setText('{}'.format(location))
        self.widgetError.problemTextArea.setPlainText('{}'.format(str(exc)))
        self.stopThread(self.IMPORT_THREAD_NAME)
        self.step += 2
        self.redraw()


class ImportTypeWidget(QtWidgets.QWidget):

    def __init__(self, session, parent=None):
        """
        Initialize the base information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)
        self.session = session

        self.fileSystemRadioButton = QRadioButton('Import an ontology from a local document',self)
        self.fileSystemRadioButton.setChecked(True)
        self.checkedId = 0
        self.webRadioButton = QRadioButton('Import an ontology from a document on the web',self)

        self.buttonGroup = QButtonGroup(self)
        self.buttonGroup.addButton(self.fileSystemRadioButton,id=0)
        self.buttonGroup.addButton(self.webRadioButton, id=1)
        self.buttonGroup.setExclusive(True)
        connect(self.buttonGroup.buttonClicked, self.onButtonClicked)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.fileSystemRadioButton)
        formlayout.addRow(self.webRadioButton)

        groupbox = QtWidgets.QGroupBox('Import type', self)
        groupbox.setLayout(formlayout)
        outerFormLayout = QtWidgets.QFormLayout()
        outerFormLayout.addRow(groupbox)
        self.setLayout(outerFormLayout)


    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot(QAbstractButton)
    def onButtonClicked(self, button):
        """
        Executed when a radio button is clicked
        """
        self.checkedId = self.buttonGroup.checkedId()

    def getSelectedRadioId(self):
        return self.buttonGroup.checkedId()

class LocalFileWidget(QtWidgets.QWidget):
    sgnValidPath = QtCore.pyqtSignal()
    sgnNotValidPath = QtCore.pyqtSignal()

    def __init__(self, session, parent=None):
        """
        Initialize the base information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)
        self.session = session
        self.isValidPath = False
        pathLabel = QtWidgets.QLabel(self, objectName='path_label')
        pathLabel.setText('Path')
        self.pathField = StringField(self, objectName='path_field')
        connect(self.pathField.textChanged, self.onPathFieldChanged)
        self.browseBtn = QtWidgets.QPushButton('Browse')
        self.browseBtn.setEnabled(True)
        connect(self.browseBtn.clicked, self.onBrowseClicked)
        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(pathLabel, self.pathField)
        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.browseBtn)
        outerFormLayout = QtWidgets.QFormLayout()
        outerFormLayout.addRow(formlayout)
        outerFormLayout.addRow(boxlayout)
        groupbox = QtWidgets.QGroupBox('Import from local document', self)
        groupbox.setLayout(outerFormLayout)
        outerFormLayout = QtWidgets.QFormLayout()
        outerFormLayout.addRow(groupbox)
        self.setLayout(outerFormLayout)

    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot(str)
    def onPathFieldChanged(self, path):
        if os.path.isfile(path):
            self.isValidPath = True
            self.sgnValidPath.emit()
            self.pathField.setStyleSheet("color: black;")
        else:
            self.isValidPath = False
            self.sgnNotValidPath.emit()
            self.pathField.setStyleSheet("color: red;")

    @QtCore.pyqtSlot(bool)
    def onBrowseClicked(self, _):
        """
        Back button pressed
        :type _: bool
        """
        self.browseBtn.setDown(False)
        dialog = FileDialog(self)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        dialog.setNameFilters([File.Owl.value, File.Any.value])
        if dialog.exec_() == QtWidgets.QFileDialog.Accepted:
            path = first(dialog.selectedFiles())
            if path:
                self.pathField.setText(path)


class WebFileWidget(QtWidgets.QWidget):
    sgnValidURI = QtCore.pyqtSignal()
    sgnNotValidURI = QtCore.pyqtSignal()

    def __init__(self, session, parent=None):
        """
        Initialize the base information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)
        self.session = session
        self.isValidUri = False
        uriLabel = QtWidgets.QLabel(self, objectName='uri_label')
        uriLabel.setText('URI')
        self.uriField = StringField(self, objectName='uri_field')
        connect(self.uriField.textChanged, self.onUriFieldChanged)
        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(uriLabel, self.uriField)
        groupbox = QtWidgets.QGroupBox('Import from remote document', self)
        groupbox.setLayout(formlayout)
        outerFormLayout = QtWidgets.QFormLayout()
        outerFormLayout.addRow(groupbox)
        self.setLayout(outerFormLayout)


    #############################################
    #   SLOTS
    #################################
    @QtCore.pyqtSlot(str)
    def onUriFieldChanged(self, uri):
        if urlparse(uri):
            self.isValidUri = True
            self.sgnValidURI.emit()
            self.uriField.setStyleSheet("color: black;")
        else:
            self.isValidUri = False
            self.sgnNotValidURI.emit()
            self.uriField.setStyleSheet("color: red;")

class VerifyWidget(QtWidgets.QWidget):

    def __init__(self, session, parent=None):
        """
        Initialize the base information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)
        self.session = session

        # PROGRESS BAR
        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.setAlignment(QtCore.Qt.AlignHCenter)
        self.progressBar.setRange(0, OwlOntologyImportWorker.TOTAL_STEP_COUNT)
        self.progressBar.setValue(0)

        msgLabel = QtWidgets.QLabel(self)
        msgLabel.setText('Verifying ontology import....')

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(msgLabel)
        boxlayout.addWidget(self.progressBar)

        groupbox = QtWidgets.QGroupBox('Import verification', self)
        groupbox.setLayout(boxlayout)
        outerFormLayout = QtWidgets.QFormLayout()
        outerFormLayout.addRow(groupbox)
        self.setLayout(outerFormLayout)

    @QtCore.pyqtSlot(int)
    def progressStep(self, step):
        self.progressBar.setValue(step)

class ConfirmWidget(QtWidgets.QWidget):

    def __init__(self, session, location='', ontIri='', versionIri='', parent=None):
        """
        Initialize the base information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)
        self.session = session

        self.msgLabel = QtWidgets.QLabel(self)
        self.msgLabel.setText('The following ontology will be imported:')

        self.locationLabel = QtWidgets.QLabel(self)
        self.locationLabel.setText('Location: '.format(location))
        self.locationText = StringField(self)
        self.locationText.setValue('{}'.format(location))
        self.locationText.setReadOnly(True)

        self.iriLabel = QtWidgets.QLabel(self)
        self.iriLabel.setText('Ontology IRI: ')
        self.iriText = StringField(self)
        self.iriText.setValue('{}'.format(ontIri))
        self.iriText.setReadOnly(True)

        self.versionLabel = QtWidgets.QLabel(self)
        self.versionLabel.setText('Version IRI: ')
        self.versionText = StringField(self)
        self.versionText.setValue('{}'.format(versionIri))
        self.versionText.setReadOnly(True)

        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.locationLabel,self.locationText)
        formlayout.addRow(self.iriLabel,self.iriText)
        formlayout.addRow(self.versionLabel,self.versionText)
        groupbox = QtWidgets.QGroupBox(parent=self)
        groupbox.setLayout(formlayout)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(self.msgLabel)
        boxlayout.addWidget(groupbox)

        groupbox = QtWidgets.QGroupBox('Finalize import', self)
        groupbox.setLayout(boxlayout)
        outerFormLayout = QtWidgets.QFormLayout()
        outerFormLayout.addRow(groupbox)
        self.setLayout(outerFormLayout)


class ErrorWidget(QtWidgets.QWidget):

    def __init__(self, session, location='', problemDescription='', parent=None):
        """
        Initialize the base information box.
        :type session: Session
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)
        self.session = session

        msgLabel = QtWidgets.QLabel(self)
        msgLabel.setText('Problems encountered while verifying import:')

        self.locationLabel = QtWidgets.QLabel(self)
        self.locationLabel.setText('Location: ')
        self.locationText = StringField(self)
        self.locationText.setValue('{}'.format(location))
        self.locationText.setReadOnly(True)

        self.problemLabel = QtWidgets.QLabel(self)
        self.problemLabel.setText('Problem: ')
        self.problemTextArea = QtWidgets.QPlainTextEdit(self)
        self.problemTextArea.setPlainText('{}'.format(problemDescription))
        self.problemTextArea.setReadOnly(True)
        formlayout = QtWidgets.QFormLayout()
        formlayout.addRow(self.locationLabel,self.locationText)
        formlayout.addRow(self.problemLabel,self.problemTextArea)
        groupbox = QtWidgets.QGroupBox(parent=self)
        groupbox.setLayout(formlayout)

        boxlayout = QtWidgets.QHBoxLayout()
        boxlayout.setAlignment(QtCore.Qt.AlignCenter)
        boxlayout.addWidget(msgLabel)
        boxlayout.addWidget(groupbox)

        groupbox = QtWidgets.QGroupBox('Revision needed', self)
        groupbox.setLayout(boxlayout)
        outerFormLayout = QtWidgets.QFormLayout()
        outerFormLayout.addRow(groupbox)
        self.setLayout(outerFormLayout)
