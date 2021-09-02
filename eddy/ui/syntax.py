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

import time

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy.core.common import HasThreadingSystem
from eddy.core.datatypes.graphol import Item
from eddy.core.datatypes.qt import Font
from eddy.core.functions.signals import connect
from eddy.core.worker import AbstractWorker


class SyntaxValidationDialog(QtWidgets.QDialog, HasThreadingSystem):
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

        # Here we perform the validation on all the edges in the project and the isolated nodes. This is
        # due to the implementation of the checkEdge() function in the Profile class which validates the
        # edge endpoints at first, and then (if no error is detected) will perform the validation on the
        # edge itself. However, disconnected nodes won't be taken into account and thus we must perform
        # an additional step to validate the isolated nodes separately.
        self.items = list(project.edges()) + list(filter(lambda n: not n.adjacentNodes(), project.nodes()))
        self.project = project
        self.workerThread = None
        self.worker = None
        self.i = 0

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

        #self.buttonAbort = QtWidgets.QPushButton('Abort', self)
        self.buttonIgnore = QtWidgets.QPushButton('Ignore', self)
        self.buttonShow = QtWidgets.QPushButton('Show', self)

        self.buttonBox = QtWidgets.QWidget(self)
        self.buttonBox.setVisible(False)
        self.buttonBoxLayout = QtWidgets.QHBoxLayout(self.buttonBox)
        self.buttonBoxLayout.setContentsMargins(10, 0, 10, 10)
        #self.buttonBoxLayout.addWidget(self.buttonAbort, 0, QtCore.Qt.AlignRight)
        self.buttonBoxLayout.addWidget(self.buttonIgnore, 0, QtCore.Qt.AlignRight)
        self.buttonBoxLayout.addWidget(self.buttonShow, 0, QtCore.Qt.AlignRight)

        #############################################
        # MESSAGE AREA
        #################################

        self.messageField = QtWidgets.QTextEdit(self)
        self.messageField.setAcceptRichText(True)
        self.messageField.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.messageField.setFixedSize(400, 100)
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

        #connect(self.buttonAbort.clicked, self.doAbort)
        connect(self.buttonIgnore.clicked, self.doIgnore)
        connect(self.buttonShow.clicked, self.doShow)
        connect(self.sgnWork, self.doWork)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Running syntax validation...')
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))

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
        #self.sgnWork.emit(self.i + 1)  #previous dialog pops up if this command is not executed.
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
        worker = SyntaxValidationWorker(i, self.items, self.project)
        connect(worker.sgnCompleted, self.onCompleted)
        connect(worker.sgnProgress, self.onProgress)
        connect(worker.sgnSyntaxError, self.onSyntaxError)
        self.startThread('syntaxCheck', worker)

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
            self.progressBar.update()

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


class SyntaxValidationWorker(AbstractWorker):
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
        super().__init__()
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
                pvr = self.project.profile.checkEdge(source, item, target)
                if not pvr.isValid():
                    s = '{} <b>({})</b>'.format(source.name, source.id)
                    t = '{} <b>({})</b>'.format(target.name, target.id)
                    if source.type() in {Item.AttributeNode, Item.ConceptNode, Item.RoleNode, Item.ValueDomainNode}:
                        s = '{} <b>{} ({})</b>'.format(source.name, source.text(), source.id)
                    if target.type() in {Item.AttributeNode, Item.ConceptNode, Item.RoleNode, Item.ValueDomainNode}:
                        t = '{} <b>{} ({})</b>'.format(target.name, target.text(), target.id)
                    i = '{}{}'.format(pvr.message()[:1].lower(), pvr.message()[1:])
                    errorMsg = 'Syntax error detected on {} from {} to {}: <i>{}</i>.'.format(item.name, s, t, i)
                    break

            # VALIDATE NODE (ISOLATED)
            elif item.isNode():
                pvr = self.project.profile.checkNode(item)
                if not pvr.isValid():
                    name = '{} <b>({})</b>'.format(item.name, item.id)
                    if item.isPredicate():
                        name = '{} <b>{} ({})</b>'.format(item.name, item.text(), item.id)
                    i = '{}{}'.format(pvr.message()[:1].lower(), pvr.message()[1:])
                    errorMsg = 'Syntax error detected on {}: <i>{}</i>.'.format(name, i)
                    break

            self.i += 1

        if errorMsg:
            self.sgnSyntaxError.emit(errorMsg)
        else:
            self.sgnCompleted.emit()

        self.finished.emit()
