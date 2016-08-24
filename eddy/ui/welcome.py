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


import os
import webbrowser

from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtCore import Qt, QSettings, QSize
from PyQt5.QtGui import QIcon, QPainter
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QFileDialog
from PyQt5.QtWidgets import QLabel, QWidget, QDesktopWidget, QMessageBox
from PyQt5.QtWidgets import QMenu, QAction, QStyle, QStyleOption

from eddy import APPNAME, ORGANIZATION, VERSION
from eddy import PROJECT_HOME, BUG_TRACKER
from eddy import GRAPHOL_HOME, WORKSPACE
from eddy.core.functions.fsystem import is_dir, rmdir
from eddy.core.functions.misc import first, format_exception
from eddy.core.functions.path import expandPath, shortPath
from eddy.core.functions.path import compressPath, isSubPath
from eddy.core.datatypes.qt import Font, PHCQPushButton, PHCQToolButton
from eddy.core.functions.signals import connect

from eddy.ui.project import ProjectDialog


class Welcome(QWidget):
    """
    This class is used to display the welcome screen of Eddy.
    """
    sgnCreateSession = pyqtSignal(str)

    def __init__(self, application, parent=None):
        """
        Initialize the workspace dialog.
        :type application: QApplication
        :type parent: QWidget
        """
        super(Welcome, self).__init__(parent)

        arial12b = Font('Arial', 12)
        arial12b.setBold(True)
        arial13r = Font('Arial', 13)
        arial14r = Font('Arial', 14)
        arial28rsc = Font('Arial', 28)
        arial28rsc.setCapitalization(Font.SmallCaps)

        settings = QSettings(ORGANIZATION, APPNAME)

        self.workspace = settings.value('workspace/home', WORKSPACE, str)

        #############################################
        # LEFT AREA
        #################################

        self.innerWidgetL = QWidget(self)
        self.innerWidgetL.setProperty('class', 'inner-left')
        self.innerWidgetL.setContentsMargins(0, 0, 0, 0)

        self.innerLayoutL = QVBoxLayout(self.innerWidgetL)
        self.innerLayoutL.setContentsMargins(0, 0, 0, 0)
        self.innerLayoutL.setSpacing(0)

        for path in settings.value('project/recent', None, str) or []:
            project = ProjectBlock(path, self.innerWidgetL)
            connect(project.sgnDeleteProject, self.doDeleteProject)
            connect(project.sgnOpenProject, self.doOpenRecentProject)
            self.innerLayoutL.addWidget(project, 0, Qt.AlignTop)

        #############################################
        # RIGHT AREA
        #################################

        self.actionBugTracker = QAction('Report a bug', self)
        self.actionBugTracker.setData(BUG_TRACKER)
        connect(self.actionBugTracker.triggered, self.doOpenURL)
        self.actionGrapholWeb = QAction('Visit Graphol website', self)
        self.actionGrapholWeb.setData(GRAPHOL_HOME)
        connect(self.actionGrapholWeb.triggered, self.doOpenURL)
        self.actionProjectHome = QAction('GitHub repository', self)
        self.actionProjectHome.setData(PROJECT_HOME)
        connect(self.actionProjectHome.triggered, self.doOpenURL)

        self.menuHelp = QMenu(self)
        self.menuHelp.addAction(self.actionBugTracker)
        self.menuHelp.addAction(self.actionProjectHome)
        self.menuHelp.addAction(self.actionGrapholWeb)

        self.innerWidgetR = QWidget(self)
        self.innerWidgetR.setProperty('class', 'inner-right')
        self.innerWidgetR.setContentsMargins(0, 30, 0, 0)

        self.appPix = QLabel(self)
        self.appPix.setPixmap(QIcon(':/icons/128/ic_eddy').pixmap(128))
        self.appPix.setContentsMargins(0, 0, 0, 0)
        self.appName = QLabel(APPNAME, self)
        self.appName.setFont(arial28rsc)
        self.appName.setProperty('class', 'appname')
        self.appVersion = QLabel('Version: {0}'.format(VERSION), self)
        self.appVersion.setFont(arial14r)
        self.appVersion.setProperty('class', 'version')

        self.buttonNewProject = PHCQPushButton(self)
        self.buttonNewProject.setFont(arial13r)
        self.buttonNewProject.setIcon(QIcon(':/icons/24/ic_add_document_black'))
        self.buttonNewProject.setIconSize(QSize(24, 24))
        self.buttonNewProject.setText('Create new project')
        connect(self.buttonNewProject.clicked, self.doNewProject)
        self.buttonOpenProject = PHCQPushButton(self)
        self.buttonOpenProject.setFont(arial13r)
        self.buttonOpenProject.setIcon(QIcon(':/icons/24/ic_folder_open_black'))
        self.buttonOpenProject.setIconSize(QSize(24, 24))
        self.buttonOpenProject.setText('Open project')
        connect(self.buttonOpenProject.clicked, self.doOpenProject)
        
        self.buttonHelp = PHCQToolButton(self)
        self.buttonHelp.setFont(arial13r)
        self.buttonHelp.setIcon(QIcon(':/icons/24/ic_help_outline_black'))
        self.buttonHelp.setIconSize(QSize(24, 24))
        self.buttonHelp.setText('Help')
        self.buttonHelp.setMenu(self.menuHelp)
        self.buttonHelp.setPopupMode(PHCQToolButton.InstantPopup)
        self.buttonHelp.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.buttonLayoutRT = QVBoxLayout()
        self.buttonLayoutRT.addWidget(self.buttonNewProject)
        self.buttonLayoutRT.addWidget(self.buttonOpenProject)
        self.buttonLayoutRT.setContentsMargins(0, 38, 0, 0)
        self.buttonLayoutRT.setAlignment(Qt.AlignHCenter)
        self.buttonLayoutRB = QHBoxLayout()
        self.buttonLayoutRB.addWidget(self.buttonHelp)
        self.buttonLayoutRB.setAlignment(Qt.AlignBottom|Qt.AlignRight)
        self.buttonLayoutRB.setContentsMargins(0, 38, 8, 0)

        self.innerLayoutR = QVBoxLayout(self.innerWidgetR)
        self.innerLayoutR.setContentsMargins(0, 0, 0, 0)
        self.innerLayoutR.addWidget(self.appPix, 0, Qt.AlignHCenter)
        self.innerLayoutR.addWidget(self.appName, 0, Qt.AlignHCenter)
        self.innerLayoutR.addWidget(self.appVersion, 0, Qt.AlignHCenter)
        self.innerLayoutR.addLayout(self.buttonLayoutRT)
        self.innerLayoutR.addLayout(self.buttonLayoutRB)

        #############################################
        # SETUP DIALOG LAYOUT
        #################################

        self.outerWidgetL = QWidget(self)
        self.outerWidgetL.setProperty('class', 'outer-left')
        self.outerWidgetL.setContentsMargins(0, 0, 0, 0)
        self.outerWidgetL.setFixedWidth(280)
        self.outerLayoutL = QVBoxLayout(self.outerWidgetL)
        self.outerLayoutL.setContentsMargins(0, 0, 0, 0)
        self.outerLayoutL.addWidget(self.innerWidgetL, 0,  Qt.AlignTop)

        self.outerWidgetR = QWidget(self)
        self.outerWidgetR.setProperty('class', 'outer-right')
        self.outerWidgetR.setContentsMargins(0, 0, 0, 0)
        self.outerLayoutR = QVBoxLayout(self.outerWidgetR)
        self.outerLayoutR.setContentsMargins(0, 0, 0, 0)
        self.outerLayoutR.addWidget(self.innerWidgetR, 0,  Qt.AlignTop)

        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.outerWidgetL)
        self.mainLayout.addWidget(self.outerWidgetR)

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFixedSize(720, 400)
        self.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle('Welcome to {0}'.format(APPNAME))
        connect(self.sgnCreateSession, application.doCreateSession)

        desktop = QDesktopWidget()
        screen = desktop.screenGeometry()
        widget = self.geometry()
        x = (screen.width() - widget.width()) / 2
        y = (screen.height() - widget.height()) / 2
        self.move(x, y)

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
    #   SLOTS
    #################################

    @pyqtSlot(str)
    def doDeleteProject(self, path):
        """
        Delete the given project.
        :type path: str
        """
        msgbox = QMessageBox(self)
        msgbox.setFont(Font('Arial', 10))
        msgbox.setIconPixmap(QIcon(':/icons/48/ic_question_outline_black').pixmap(48))
        msgbox.setInformativeText('<b>NOTE: This action is not reversible!</b>')
        msgbox.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        msgbox.setTextFormat(Qt.RichText)
        msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
        msgbox.setWindowTitle('Remove project: {0}?'.format(os.path.basename(path)))
        msgbox.setText('Are you sure you want to remove project: <b>{0}</b>'.format(os.path.basename(path)))
        msgbox.exec_()
        if msgbox.result() == QMessageBox.Yes:
            try:
                # REMOVE THE PROJECT FROM DISK
                rmdir(path)
            except Exception as e:
                msgbox = QMessageBox(self)
                msgbox.setDetailedText(format_exception(e))
                msgbox.setIconPixmap(QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
                msgbox.setStandardButtons(QMessageBox.Close)
                msgbox.setTextFormat(Qt.RichText)
                msgbox.setText('Eddy could not remove the specified project: <b>{0}</b>!'.format(os.path.basename(path)))
                msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
                msgbox.setWindowTitle('ERROR!')
                msgbox.exec_()
            else:
                # UPDATE THE RECENT PROJECT LIST
                recentList = []
                settings = QSettings(ORGANIZATION, APPNAME)
                for path in map(expandPath, settings.value('project/recent')):
                    if is_dir(path):
                        recentList.append(path)
                settings.setValue('project/recent', recentList)
                settings.sync()
                # CLEAR CURRENT LAYOUT
                for i in reversed(range(self.innerLayoutL.count())):
                    item = self.innerLayoutL.itemAt(i)
                    self.innerLayoutL.removeItem(item)
                # DISPOSE NEW PROJECT BLOCK
                for path in recentList:
                    project = ProjectBlock(path, self.innerWidgetL)
                    connect(project.sgnDeleteProject, self.doDeleteProject)
                    connect(project.sgnOpenProject, self.doOpenRecentProject)
                    self.innerLayoutL.addWidget(project, 0, Qt.AlignTop)

    @pyqtSlot()
    def doNewProject(self):
        """
        Bring up a modal window used to create a new project.
        """
        form = ProjectDialog(self)
        if form.exec_() == ProjectDialog.Accepted:
            path = form.pathField.value()
            self.sgnCreateSession.emit(path)

    @pyqtSlot()
    def doOpenProject(self):
        """
        Bring up a modal window used to open a project.
        """
        dialog = QFileDialog(self)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setDirectory(self.workspace)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setViewMode(QFileDialog.Detail)

        if dialog.exec_() == QFileDialog.Accepted:
            path = first(dialog.selectedFiles())
            self.sgnCreateSession.emit(path)

    @pyqtSlot(str)
    def doOpenRecentProject(self, path):
        """
        Open a recent project in a new session of Eddy.
        :type path: str
        """
        self.sgnCreateSession.emit(path)

    @pyqtSlot()
    def doOpenURL(self):
        """
        Open a URL using the operating system default browser.
        """
        action = self.sender()
        weburl = action.data()
        if weburl:
            webbrowser.open(weburl)


class ProjectBlock(QWidget):
    """
    This class implements the project block displayed in the welcome dialog.
    """
    sgnDeleteProject = pyqtSignal(str)
    sgnOpenProject = pyqtSignal(str)

    def __init__(self, project, parent=None):
        """
        Initialize the project block.
        :type project: str
        :type parent: QWidget
        """
        super().__init__(parent)

        arial12b = Font('Arial', 12)
        arial12b.setBold(True)
        arial12r = Font('Arial', 12)

        self.nameLabel = QLabel(os.path.basename(project), self)
        self.nameLabel.setContentsMargins(20, 0, 20, 0)
        self.nameLabel.setProperty('class', 'name')
        self.nameLabel.setFont(arial12b)
        self.pathLabel = QLabel(compressPath(shortPath(project), 34), self)
        self.pathLabel.setContentsMargins(20, 0, 20, 0)
        self.pathLabel.setProperty('class', 'path')
        self.pathLabel.setFont(arial12r)
        self.deleteBtn = PHCQPushButton(self)
        self.deleteBtn.setIcon(QIcon(':/icons/24/ic_delete_black'))
        self.deleteBtn.setVisible(not isSubPath(expandPath('@examples/'), project))
        connect(self.deleteBtn.clicked, self.onDeleteButtonClicked)
        self.leftWidget = QWidget(self)
        self.leftWidget.setContentsMargins(0, 0, 0, 0)
        self.leftLayout = QVBoxLayout(self.leftWidget)
        self.leftLayout.setContentsMargins(0, 0, 0, 0)
        self.leftLayout.setSpacing(0)
        self.leftLayout.addWidget(self.nameLabel)
        self.leftLayout.addWidget(self.pathLabel)
        self.rightWidget = QWidget(self)
        self.rightWidget.setContentsMargins(0, 0, 10, 0)
        self.rightLayout = QVBoxLayout(self.rightWidget)
        self.rightLayout.setContentsMargins(0, 0, 0, 0)
        self.rightLayout.setSpacing(0)
        self.rightLayout.addWidget(self.deleteBtn)
        self.mainLayout = QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addWidget(self.leftWidget)
        self.mainLayout.addWidget(self.rightWidget, 1, Qt.AlignRight)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(40)
        self.path = project

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def onDeleteButtonClicked(self):
        """
        Executed when the delete button is clicked.
        """
        self.sgnDeleteProject.emit(self.path)

    #############################################
    #   EVENTS
    #################################

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when a mouse button is released from this widget.
        :type mouseEvent: QMouseEvent
        """
        if mouseEvent.button() == Qt.LeftButton:
            self.sgnOpenProject.emit(self.path)

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
