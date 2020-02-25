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


import os

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from eddy import APPNAME, ORGANIZATION, VERSION
from eddy import PROJECT_HOME, BUG_TRACKER
from eddy import GRAPHOL_HOME, WORKSPACE
from eddy.core.functions.fsystem import isdir, rmdir, faccess
from eddy.core.functions.misc import first, format_exception
from eddy.core.functions.path import expandPath, shortPath
from eddy.core.functions.path import compressPath
from eddy.core.datatypes.qt import Font, PHCQPushButton, PHCQToolButton
from eddy.core.functions.signals import connect

from eddy.ui.project import NewProjectDialog


class Welcome(QtWidgets.QDialog):
    """
    This class is used to display the welcome screen of Eddy.
    """
    sgnCreateSession = QtCore.pyqtSignal(str)
    sgnOpenProject = QtCore.pyqtSignal(str)
    sgnUpdateRecentProjects = QtCore.pyqtSignal()

    def __init__(self, application, parent=None):
        """
        Initialize the workspace dialog.
        :type application: QApplication
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)

        settings = QtCore.QSettings(ORGANIZATION, APPNAME)

        self.pending = False
        self.workspace = settings.value('workspace/home', WORKSPACE, str)

        #############################################
        # LEFT AREA
        #################################

        self.innerWidgetL = QtWidgets.QWidget(self)
        self.innerWidgetL.setProperty('class', 'inner-left')
        self.innerWidgetL.setContentsMargins(0, 0, 0, 0)

        self.innerLayoutL = QtWidgets.QVBoxLayout(self.innerWidgetL)
        self.innerLayoutL.setContentsMargins(0, 0, 0, 0)
        self.innerLayoutL.setSpacing(0)

        #############################################
        # RIGHT AREA
        #################################

        self.actionBugTracker = QtWidgets.QAction('Report a bug', self)
        self.actionBugTracker.setData(BUG_TRACKER)
        connect(self.actionBugTracker.triggered, self.doOpenURL)
        self.actionGrapholWeb = QtWidgets.QAction('Visit Graphol website', self)
        self.actionGrapholWeb.setData(GRAPHOL_HOME)
        connect(self.actionGrapholWeb.triggered, self.doOpenURL)
        self.actionProjectHome = QtWidgets.QAction('GitHub repository', self)
        self.actionProjectHome.setData(PROJECT_HOME)
        connect(self.actionProjectHome.triggered, self.doOpenURL)

        self.menuHelp = QtWidgets.QMenu(self)
        self.menuHelp.addAction(self.actionBugTracker)
        self.menuHelp.addAction(self.actionProjectHome)
        self.menuHelp.addAction(self.actionGrapholWeb)

        self.innerWidgetR = QtWidgets.QWidget(self)
        self.innerWidgetR.setProperty('class', 'inner-right')
        self.innerWidgetR.setContentsMargins(0, 30, 0, 0)

        self.appPix = QtWidgets.QLabel(self)
        self.appPix.setPixmap(QtGui.QIcon(':/icons/128/ic_eddy').pixmap(128))
        self.appPix.setContentsMargins(0, 0, 0, 0)
        self.appName = QtWidgets.QLabel(APPNAME, self)
        self.appName.setFont(Font(scale=2.5, capitalization=Font.SmallCaps))
        self.appName.setProperty('class', 'appname')
        self.appVersion = QtWidgets.QLabel('Version: {0}'.format(VERSION), self)
        self.appVersion.setFont(Font(scale=1.3333, capitalization=Font.SmallCaps))
        self.appVersion.setProperty('class', 'version')

        self.buttonNewProject = PHCQPushButton(self)
        self.buttonNewProject.setIcon(QtGui.QIcon(':/icons/24/ic_add_document_black'))
        self.buttonNewProject.setIconSize(QtCore.QSize(24, 24))
        self.buttonNewProject.setText('&Create new project')
        connect(self.buttonNewProject.clicked, self.doNewProject)
        self.buttonOpenProject = PHCQPushButton(self)
        self.buttonOpenProject.setIcon(QtGui.QIcon(':/icons/24/ic_folder_open_black'))
        self.buttonOpenProject.setIconSize(QtCore.QSize(24, 24))
        self.buttonOpenProject.setText('&Open project')
        connect(self.buttonOpenProject.clicked, self.doOpen)

        self.buttonHelp = PHCQToolButton(self)
        self.buttonHelp.setIcon(QtGui.QIcon(':/icons/24/ic_help_outline_black'))
        self.buttonHelp.setIconSize(QtCore.QSize(24, 24))
        self.buttonHelp.setText('&Help')
        self.buttonHelp.setMenu(self.menuHelp)
        self.buttonHelp.setPopupMode(PHCQToolButton.InstantPopup)
        self.buttonHelp.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)

        self.buttonLayoutRT = QtWidgets.QVBoxLayout()
        self.buttonLayoutRT.addWidget(self.buttonNewProject)
        self.buttonLayoutRT.addWidget(self.buttonOpenProject)
        self.buttonLayoutRT.setContentsMargins(0, 38, 0, 0)
        self.buttonLayoutRT.setAlignment(QtCore.Qt.AlignHCenter)
        self.buttonLayoutRB = QtWidgets.QHBoxLayout()
        self.buttonLayoutRB.addWidget(self.buttonHelp)
        self.buttonLayoutRB.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignRight)
        self.buttonLayoutRB.setContentsMargins(0, 30, 8, 0)

        self.innerLayoutR = QtWidgets.QVBoxLayout(self.innerWidgetR)
        self.innerLayoutR.setContentsMargins(0, 0, 0, 0)
        self.innerLayoutR.addWidget(self.appPix, 0, QtCore.Qt.AlignHCenter)
        self.innerLayoutR.addWidget(self.appName, 0, QtCore.Qt.AlignHCenter)
        self.innerLayoutR.addWidget(self.appVersion, 0, QtCore.Qt.AlignHCenter)
        self.innerLayoutR.addLayout(self.buttonLayoutRT)
        self.innerLayoutR.addLayout(self.buttonLayoutRB)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        self.placeholder = QtWidgets.QLabel('No Recent Projects', self)
        self.placeholder.setEnabled(False)
        self.placeholder.setFixedSize(300, 400)
        self.placeholder.setFont(Font(scale=1.5))
        self.placeholder.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignHCenter)

        self.outerWidgetL = QtWidgets.QWidget(self)
        self.outerWidgetL.setProperty('class', 'outer-left')
        self.outerWidgetL.setContentsMargins(0, 0, 0, 0)
        self.outerWidgetL.setFixedWidth(300)
        self.outerLayoutL = QtWidgets.QVBoxLayout(self.outerWidgetL)
        self.outerLayoutL.setContentsMargins(0, 0, 0, 0)
        self.outerLayoutL.addWidget(self.placeholder, 1,  QtCore.Qt.AlignTop)
        self.outerLayoutL.addWidget(self.innerWidgetL, 0,  QtCore.Qt.AlignTop)

        self.outerWidgetR = QtWidgets.QWidget(self)
        self.outerWidgetR.setProperty('class', 'outer-right')
        self.outerWidgetR.setContentsMargins(0, 0, 0, 0)
        self.outerLayoutR = QtWidgets.QVBoxLayout(self.outerWidgetR)
        self.outerLayoutR.setContentsMargins(0, 0, 0, 0)
        self.outerLayoutR.addWidget(self.innerWidgetR, 0,  QtCore.Qt.AlignTop)

        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.outerWidgetL)
        self.mainLayout.addWidget(self.outerWidgetR)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setFixedSize(720, 400)
        self.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Welcome to {0}'.format(APPNAME))
        
        connect(self.sgnCreateSession, application.doCreateSession)
        connect(self.sgnOpenProject, self.doOpenProject)
        connect(self.sgnUpdateRecentProjects, self.doUpdateRecentProjects)

        desktop = QtWidgets.QDesktopWidget()
        screen = desktop.availableGeometry(self)
        widget = self.geometry()
        x = screen.x() + (screen.width() - widget.width()) / 2
        y = screen.y() + (screen.height() - widget.height()) / 2
        self.move(x, y)

        # UPDATE RECENT PROJECTS
        self.sgnUpdateRecentProjects.emit()

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
    def doDeleteProject(self, path):
        """
        Delete the given project.
        :type path: str
        """
        msgbox = QtWidgets.QMessageBox(self)
        msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_question_outline_black').pixmap(48))
        msgbox.setInformativeText('<b>NOTE: This action is not reversible!</b>')
        msgbox.setStandardButtons(QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes)
        msgbox.setTextFormat(QtCore.Qt.RichText)
        msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
        msgbox.setWindowTitle('Remove project: {0}?'.format(os.path.basename(path)))
        msgbox.setText('Are you sure you want to remove project: <b>{0}</b>'.format(os.path.basename(path)))
        msgbox.exec_()
        if msgbox.result() == QtWidgets.QMessageBox.Yes:
            try:
                # REMOVE THE PROJECT FROM DISK
                rmdir(path)
            except Exception as e:
                msgbox = QtWidgets.QMessageBox(self)
                msgbox.setDetailedText(format_exception(e))
                msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
                msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
                msgbox.setTextFormat(QtCore.Qt.RichText)
                msgbox.setText('Eddy could not remove the specified project: <b>{0}</b>!'.format(os.path.basename(path)))
                msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
                msgbox.setWindowTitle('ERROR!')
                msgbox.exec_()
            else:
                self.sgnUpdateRecentProjects.emit()

    @QtCore.pyqtSlot()
    def doNewProject(self):
        """
        Bring up a modal window used to create a new project.
        """
        form = NewProjectDialog(self)
        if form.exec_() == NewProjectDialog.Accepted:
            self.sgnCreateSession.emit(expandPath(form.pathField.value()))

    @QtCore.pyqtSlot()
    def doOpen(self):
        """
        Bring up a modal window used to open a project.
        """
        dialog = QtWidgets.QFileDialog(self)
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dialog.setDirectory(expandPath(self.workspace))
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        dialog.setViewMode(QtWidgets.QFileDialog.Detail)
        if dialog.exec_() == QtWidgets.QFileDialog.Accepted:
            self.sgnOpenProject.emit(first(dialog.selectedFiles()))

    @QtCore.pyqtSlot(str)
    def doOpenProject(self, path):
        """
        Open a recent project in a new session of Eddy.
        :type path: str
        """
        if not self.pending:
            self.pending = True
            self.sgnCreateSession.emit(expandPath(path))

    @QtCore.pyqtSlot()
    def doOpenURL(self):
        """
        Open a URL using the operating system default browser.
        """
        action = self.sender()
        weburl = action.data()
        if weburl:
            # noinspection PyTypeChecker,PyCallByClass,PyCallByClass
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(weburl))

    @QtCore.pyqtSlot(str)
    def doRemoveProject(self, path):
        """
        Remove the given project from the recent list.
        :type path: str
        """
        recentList = []
        path = expandPath(path)
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        for recent in map(expandPath, settings.value('project/recent', None, str) or []):
            if recent != path:
                recentList.append(recent)
        settings.setValue('project/recent', recentList)
        settings.sync()
        self.sgnUpdateRecentProjects.emit()

    @QtCore.pyqtSlot()
    def doUpdateRecentProjects(self):
        """
        Update the list of recent projects.
        """
        # UPDATE THE RECENT PROJECT LIST
        recentList = []
        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        for path in map(expandPath, settings.value('project/recent', None, str) or []):
            if isdir(path):
                recentList.append(path)
        settings.setValue('project/recent', recentList)
        settings.sync()
        # CLEAR CURRENT LAYOUT
        for i in reversed(range(self.innerLayoutL.count())):
            item = self.innerLayoutL.itemAt(i)
            self.innerLayoutL.removeItem(item)
        # DISPOSE NEW PROJECT BLOCK
        if recentList:
            self.placeholder.setVisible(False)
            for path in recentList:
                project = ProjectBlock(path, self.innerWidgetL)
                connect(project.sgnDeleteProject, self.doDeleteProject)
                connect(project.sgnOpenProject, self.doOpenProject)
                connect(project.sgnRemoveProject, self.doRemoveProject)
                self.innerLayoutL.addWidget(project, 0, QtCore.Qt.AlignTop)
        else:
            self.placeholder.setVisible(True)


class ProjectBlock(QtWidgets.QWidget):
    """
    This class implements the project block displayed in the welcome dialog.
    """
    sgnDeleteProject = QtCore.pyqtSignal(str)
    sgnOpenProject = QtCore.pyqtSignal(str)
    sgnRemoveProject = QtCore.pyqtSignal(str)

    def __init__(self, project, parent=None):
        """
        Initialize the project block.
        :type project: str
        :type parent: QtWidgets.QWidget
        """
        super().__init__(parent)

        self.nameLabel = QtWidgets.QLabel(os.path.basename(project), self)
        self.nameLabel.setContentsMargins(20, 0, 20, 0)
        self.nameLabel.setProperty('class', 'name')
        self.nameLabel.setFont(Font(bold=True))
        self.pathLabel = QtWidgets.QLabel(compressPath(shortPath(project), 34), self)
        self.pathLabel.setContentsMargins(20, 0, 20, 0)
        self.pathLabel.setProperty('class', 'path')
        self.removeBtn = PHCQPushButton(self)
        self.removeBtn.setIcon(QtGui.QIcon(':icons/24/ic_close_black'))
        self.removeBtn.setToolTip('Remove Project')
        self.removeBtn.setVisible(False)
        connect(self.removeBtn.clicked, self.onRemoveButtonClicked)
        self.deleteBtn = PHCQPushButton(self)
        self.deleteBtn.setToolTip('Delete Project')
        self.deleteBtn.setIcon(QtGui.QIcon(':/icons/24/ic_delete_black'))
        self.deleteBtn.setVisible(False)
        connect(self.deleteBtn.clicked, self.onDeleteButtonClicked)
        self.leftWidget = QtWidgets.QWidget(self)
        self.leftWidget.setContentsMargins(0, 0, 0, 0)
        self.leftLayout = QtWidgets.QVBoxLayout(self.leftWidget)
        self.leftLayout.setContentsMargins(0, 0, 0, 0)
        self.leftLayout.setSpacing(0)
        self.leftLayout.addWidget(self.nameLabel)
        self.leftLayout.addWidget(self.pathLabel)
        self.rightWidget = QtWidgets.QWidget(self)
        self.rightWidget.setContentsMargins(0, 0, 10, 0)
        self.rightLayout = QtWidgets.QHBoxLayout(self.rightWidget)
        self.rightLayout.setContentsMargins(0, 0, 0, 0)
        self.rightLayout.setSpacing(0)
        self.rightLayout.addWidget(self.removeBtn)
        self.rightLayout.addWidget(self.deleteBtn)
        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.leftWidget)
        self.mainLayout.addWidget(self.rightWidget, 1, QtCore.Qt.AlignRight)
        self.installEventFilter(self)
        self.setContentsMargins(0, 0, 0, 0)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setFixedHeight(40)
        self.setFocusPolicy(QtCore.Qt.TabFocus)
        self.setToolTip(expandPath(project))
        self.path = project

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onDeleteButtonClicked(self):
        """
        Executed when the delete button is clicked.
        """
        self.sgnDeleteProject.emit(self.path)

    @QtCore.pyqtSlot()
    def onRemoveButtonClicked(self):
        """
        Executed when the remove button is clicked.
        """
        self.sgnRemoveProject.emit(self.path)

    #############################################
    #   EVENTS
    #################################

    def eventFilter(self, source, event):
        """
        Filters events to show remove and delete buttons only when hovered.
        :type source: QObject
        :type event: QtCore.QEvent
        :rtype: bool
        """
        if event.type() == QtCore.QEvent.HoverEnter:
            self.removeBtn.setVisible(True)
            self.deleteBtn.setVisible(faccess(self.path, os.R_OK | os.W_OK))
            self.setFocus()
        elif event.type() == QtCore.QEvent.HoverLeave:
            self.removeBtn.setVisible(False)
            self.deleteBtn.setVisible(False)
            self.clearFocus()
        elif event.type() == QtCore.QEvent.KeyPress:
            if event.key() in {QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return, QtCore.Qt.Key_Space}:
                self.sgnOpenProject.emit(self.path)
        return super().eventFilter(source, event)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when a mouse button is released from this widget.
        :type mouseEvent: QMouseEvent
        """
        if mouseEvent.button() == QtCore.Qt.LeftButton:
            self.sgnOpenProject.emit(self.path)

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
