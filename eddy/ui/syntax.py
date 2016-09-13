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


from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy.core.datatypes.graphol import Item, Identity
from eddy.core.datatypes.qt import Font
from eddy.core.functions.signals import connect


class SyntaxValidationDialog(QtWidgets.QDialog):
    """
    Extends QtWidgets.QDialog with facilities to perform manual syntax validation.
    """
    sgnWork = QtCore.pyqtSignal(int)

    def __init__(self, project, session):
        """
        Initialize the dialog.
        :type project: Project
        :type session: Session
        """
        super().__init__(session)

        arial12r = Font('Arial', 12)

        self.i = 0
        self.items = list(project.edges()) + list(project.nodes())
        self.project = project
        self.workerThread = None
        self.worker = None

        #############################################
        # TOP AREA
        #################################

        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.setAlignment(QtCore.Qt.AlignHCenter)
        self.progressBar.setRange(self.i, len(self.items) - 1)
        self.progressBar.setFixedSize(400, 30)
        self.progressBar.setValue(self.i)

        self.progressBox = QtWidgets.QWidget(self)
        self.progressBoxLayout = QtWidgets.QVBoxLayout(self.progressBox)
        self.progressBoxLayout.setContentsMargins(10, 10, 10, 10)
        self.progressBoxLayout.addWidget(self.progressBar)

        #############################################
        # CONTROLS AREA
        #################################

        self.buttonAbort = QtWidgets.QPushButton('Abort', self)
        self.buttonAbort.setFont(arial12r)
        self.buttonIgnore = QtWidgets.QPushButton('Ignore', self)
        self.buttonIgnore.setFont(arial12r)
        self.buttonShow = QtWidgets.QPushButton('Show', self)
        self.buttonShow.setFont(arial12r)

        self.buttonBox = QtWidgets.QWidget(self)
        self.buttonBox.setVisible(False)
        self.buttonBoxLayout = QtWidgets.QHBoxLayout(self.buttonBox)
        self.buttonBoxLayout.setContentsMargins(10, 0, 10, 10)
        self.buttonBoxLayout.addWidget(self.buttonAbort, 0, QtCore.Qt.AlignRight)
        self.buttonBoxLayout.addWidget(self.buttonIgnore, 0, QtCore.Qt.AlignRight)
        self.buttonBoxLayout.addWidget(self.buttonShow, 0, QtCore.Qt.AlignRight)

        #############################################
        # MESSAGE AREA
        #################################

        self.messageField = QtWidgets.QTextEdit(self)
        self.messageField.setAcceptRichText(True)
        self.messageField.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.messageField.setFixedSize(400, 100)
        self.messageField.setFont(arial12r)
        self.messageField.setReadOnly(True)

        self.messageBox = QtWidgets.QWidget(self)
        self.messageBox.setVisible(False)
        self.messageBoxLayout = QtWidgets.QVBoxLayout(self.messageBox)
        self.messageBoxLayout.setContentsMargins(10, 0, 10, 10)
        self.messageBoxLayout.addWidget(self.messageField)

        #############################################
        # CONFIGURE LAYOUT
        #################################

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.progressBox)
        self.mainLayout.addWidget(self.buttonBox, 0, QtCore.Qt.AlignRight)
        self.mainLayout.addWidget(self.messageBox)

        connect(self.buttonAbort.clicked, self.doAbort)
        connect(self.buttonIgnore.clicked, self.doIgnore)
        connect(self.buttonShow.clicked, self.doShow)
        connect(self.sgnWork, self.doWork)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Running syntax validation...')
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))

        desktop = QtWidgets.QDesktopWidget()
        screen = desktop.screenGeometry()
        widget = self.geometry()
        x = (screen.width() - widget.width()) / 2
        y = (screen.height() - widget.height()) / 2
        self.move(x, y)

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
        self.sgnWork.emit(0)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(bool)
    def doAbort(self, _=False):
        """
        Executed when the abort button is pressed.
        :type _: bool
        """
        self.close()

    @QtCore.pyqtSlot(bool)
    def doIgnore(self, _=False):
        """
        Executed when the ignore button is pressed.
        :type _: bool
        """
        self.sgnWork.emit(self.i + 1)

    @QtCore.pyqtSlot(bool)
    def doShow(self, _=False):
        """
        Executed when the show button is pressed.
        :type _: bool
        """
        if self.i < len(self.items):
            item = self.items[self.i]
            focus = item
            if item.isEdge():
                try:
                    focus = item.breakpoints[int(len(item.breakpoints) / 2)]
                except IndexError:
                    pass
            self.session.doFocusDiagram(item.diagram)
            self.session.mdi.activeView().centerOn(focus)
            self.session.mdi.activeDiagram().clearSelection()
            item.setSelected(True)
        self.close()

    @QtCore.pyqtSlot(int)
    def doWork(self, i):
        """
        Perform on or more advancements step in the validation procedure.
        :type i: int
        """
        # ADAPT DISPLAY
        self.buttonBox.setVisible(False)
        self.messageBox.setVisible(False)
        self.messageField.setText('')
        self.setFixedSize(self.sizeHint())
        # MAKE SURE WE ARE CLEAR
        self.dispose()
        # RUN THE WORKER
        self.workerThread = QtCore.QThread()
        self.worker = SyntaxValidationWorker(i, self.items, self.project)
        self.worker.moveToThread(self.workerThread)
        connect(self.worker.sgnCompleted, self.onCompleted)
        connect(self.worker.sgnProgress, self.onProgress)
        connect(self.worker.sgnSyntaxError, self.onSyntaxError)
        connect(self.workerThread.started, self.worker.run)
        self.workerThread.start()

    @QtCore.pyqtSlot()
    def onCompleted(self):
        """
        Executed when the syntax validation procedure is completed.
        """
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_done_black').pixmap(48))
        msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        msgbox.setWindowTitle('Done!')
        msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
        msgbox.setText('Syntax validation completed!')
        msgbox.setTextFormat(QtCore.Qt.RichText)
        msgbox.exec_()
        self.close()

    @QtCore.pyqtSlot(int)
    def onProgress(self, i):
        """
        Adjust the value of the progress bar.
        :type i: int
        """
        if i < len(self.items):
            self.i = i
            self.progressBar.setValue(self.i)

    @QtCore.pyqtSlot(str)
    def onSyntaxError(self, message):
        """
        Executed when a syntax error is detected.
        :type message: str
        """
        self.buttonBox.setVisible(True)
        self.messageBox.setVisible(True)
        self.messageField.setHtml(message)
        self.setFixedSize(self.sizeHint())


class SyntaxValidationWorker(QtCore.QObject):
    """
    Extends QtCore.QObject providing a worker thread that will perform the project syntax validation.
    """
    sgnCompleted = QtCore.pyqtSignal()
    sgnProgress = QtCore.pyqtSignal(int)
    sgnSyntaxError = QtCore.pyqtSignal(str)

    def __init__(self, current, items, project):
        """
        Initialize the syntax validation worker.
        :type current: int
        :type items: list
        :type project: Project
        """
        super(SyntaxValidationWorker, self).__init__()
        self.project = project
        self.items = items
        self.i = current

    @QtCore.pyqtSlot()
    def run(self):
        """
        Main worker.
        """
        errorMsg = None
        while self.i < len(self.items):

            item = self.items[self.i]

            # UPDATE PROGRESS BAR
            self.sgnProgress.emit(self.i)

            # VALIDATE EDGE
            if item.isEdge():
                source = item.source
                target = item.target
                pvr = self.project.profile.check(source, item, target)
                if not pvr.isValid():
                    nA = '{0} <b>{1}</b>'.format(source.name, source.id)
                    nB = '{0} <b>{1}</b>'.format(target.name, target.id)
                    if source.type() in {Item.AttributeNode, Item.ConceptNode, Item.RoleNode}:
                        nA = '{0} <b>{1}:{2}</b>'.format(source.name, source.text(), source.id)
                    if target.type() in {Item.AttributeNode, Item.ConceptNode, Item.RoleNode}:
                        nB = '{0} <b>{1}:{2}</b>'.format(target.name, target.text(), target.id)
                    info = '{0}{1}'.format(pvr.message()[:1].lower(), pvr.message()[1:])
                    errorMsg = 'Syntax error detected on {} from {} to {}: <i>{}</i>.'.format(item.name, nA, nB, info)
                    break

            # VALIDATE NODE
            if item.isNode():
                if item.identity() is Identity.Unknown:
                    name = '{0} "{1}"'.format(item.name, item.id)
                    if item.isPredicate():
                        name = '{0} "{1}:{2}"'.format(item.name, item.text(), item.id)
                    errorMsg = 'Unkown node identity detected on {0}.'.format(name)
                    break

            self.i += 1

        if errorMsg:
            self.sgnSyntaxError.emit(errorMsg)
        else:
            self.sgnCompleted.emit()