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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import os
import webbrowser

from PyQt5.QtCore import Qt, QSettings, pyqtSlot, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QPainter
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QFileDialog, QMenu, QAction
from PyQt5.QtWidgets import QLabel, QWidget, QStyleOption, QStyle, QDesktopWidget

from eddy import APPNAME, ORGANIZATION, VERSION
from eddy import PROJECT_HOME, BUG_TRACKER, GRAPHOL_HOME, WORKSPACE
from eddy.core.functions.misc import first
from eddy.core.functions.path import shortPath, compressPath
from eddy.core.functions.signals import connect
from eddy.core.qt import Font, PHCQPushButton, PHCQToolButton
from eddy.lang import gettext as _
from eddy.ui.dialogs.project import ProjectDialog


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
        super().__init__(parent)

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
            connect(project.sgnClicked, self.doOpenRecentProject)
            self.innerLayoutL.addWidget(project, 0, Qt.AlignTop)

        #############################################
        # RIGHT AREA
        #################################

        self.actionBugTracker = QAction(_('WELCOME_ACTION_BUG_REPORT'), self)
        self.actionBugTracker.setData(BUG_TRACKER)
        connect(self.actionBugTracker.triggered, self.doOpenURL)
        self.actionGrapholWeb = QAction(_('WELCOME_ACTION_VISIT_GRAPHOL_WEBSITE'), self)
        self.actionGrapholWeb.setData(GRAPHOL_HOME)
        connect(self.actionGrapholWeb.triggered, self.doOpenURL)
        self.actionProjectHome = QAction(_('WELCOME_ACTION_VISIT_EDDY_HOME'), self)
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
        self.appVersion = QLabel(_('WELCOME_APP_VERSION', VERSION), self)
        self.appVersion.setFont(arial14r)
        self.appVersion.setProperty('class', 'version')

        self.buttonNewProject = PHCQPushButton(self)
        self.buttonNewProject.setFont(arial13r)
        self.buttonNewProject.setIcon(QIcon(':/icons/24/ic_add_document_black'))
        self.buttonNewProject.setIconSize(QSize(24, 24))
        self.buttonNewProject.setText(_('WELCOME_BTN_NEW_PROJECT'))
        connect(self.buttonNewProject.clicked, self.doNewProject)
        self.buttonOpenProject = PHCQPushButton(self)
        self.buttonOpenProject.setFont(arial13r)
        self.buttonOpenProject.setIcon(QIcon(':/icons/24/ic_folder_open_black'))
        self.buttonOpenProject.setIconSize(QSize(24, 24))
        self.buttonOpenProject.setText(_('WELCOME_BTN_OPEN_PROJECT'))
        connect(self.buttonOpenProject.clicked, self.doOpenProject)
        
        self.buttonHelp = PHCQToolButton(self)
        self.buttonHelp.setFont(arial13r)
        self.buttonHelp.setIcon(QIcon(':/icons/24/ic_help_outline_black'))
        self.buttonHelp.setIconSize(QSize(24, 24))
        self.buttonHelp.setText(_('WELCOME_BTN_HELP'))
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
        self.outerWidgetL.setFixedWidth(260)
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
        self.setFixedSize(700, 400)
        self.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
        self.setWindowTitle(_('WELCOME_WINDOW_TITLE', APPNAME))
        connect(self.sgnCreateSession, application.doCreateSession)

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
    #   INTERFACE
    #################################

    def center(self):
        """
        Make sure to have the widget centered in the screen.
        """
        desktop = QDesktopWidget()
        screen = desktop.screenGeometry()
        widget = self.geometry()
        x = (screen.width() - widget.width()) / 2
        y = (screen.height() - widget.height()) / 2
        self.move(x, y)

    #############################################
    #   SLOTS
    #################################

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
    sgnClicked = pyqtSignal(str)

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
        self.pathLabel = QLabel(compressPath(shortPath(project), 36), self)
        self.pathLabel.setContentsMargins(20, 0, 20, 0)
        self.pathLabel.setProperty('class', 'path')
        self.pathLabel.setFont(arial12r)
        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addWidget(self.nameLabel)
        self.mainLayout.addWidget(self.pathLabel)
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(40)
        self.path = project

    #############################################
    #   EVENTS
    #################################

    def enterEvent(self, event):
        """
        Executed when the mouse enter the widget.
        :type event: QEvent
        """
        self.setCursor(Qt.PointingHandCursor)

    def leaveEvent(self, event):
        """
        Executed when the mouse leave the widget.
        :type event: QEvent
        """
        self.unsetCursor()

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when a mouse button is released from this widget.
        :type mouseEvent: QMouseEvent
        """
        if mouseEvent.button() == Qt.LeftButton:
            self.sgnClicked.emit(self.path)

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
