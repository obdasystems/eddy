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
from PyQt5 import QtNetwork
from PyQt5 import QtWidgets

from eddy import APPID, APPNAME, ORGANIZATION, WORKSPACE
from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.qt import Font
from eddy.core.datatypes.system import File
from eddy.core.functions.fsystem import isdir, fexists, fread
from eddy.core.functions.misc import format_exception
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect
from eddy.core.output import getLogger
from eddy.core.plugin import PluginManager
from eddy.core.reasoner import ReasonerManager
from eddy.core.project import ProjectNotFoundError
from eddy.core.project import ProjectNotValidError
from eddy.core.project import ProjectVersionError
from eddy.core.project import ProjectStopLoadingError

from eddy.ui.progress import BusyProgressDialog
from eddy.ui.session import Session
from eddy.ui.splash import Splash
from eddy.ui.style import EddyProxyStyle
from eddy.ui.workspace import WorkspaceDialog
from eddy.ui.welcome import Welcome

import jnius_config

LOGGER = getLogger()


class Eddy(QtWidgets.QApplication):
    """
    This class implements the main QtCore.Qt application.
    """
    sgnCreateSession = QtCore.pyqtSignal(str)

    def __init__(self, options, argv):
        """
        Initialize Eddy.
        :type options: Namespace
        :type argv: list
        """
        super().__init__(argv)

        self.server = None
        self.socket = QtNetwork.QLocalSocket()
        self.socket.connectToServer(APPID)
        self.running = self.socket.waitForConnected()
        self.sessions = DistinctList()
        self.welcome = None

        if not self.isRunning() or options.tests:
            self.server = QtNetwork.QLocalServer()
            self.server.listen(APPID)
            self.socket = None
            connect(self.sgnCreateSession, self.doCreateSession)

    #############################################
    #   INTERFACE
    #################################

    def configure(self, options):
        """
        Perform initial configuration tasks for Eddy to work properly.
        :type options: Namespace
        """
        #############################################
        # DRAW THE SPLASH SCREEN
        #################################

        splash = None
        if not options.nosplash:
            splash = Splash(mtime=4)
            splash.show()

        #############################################
        # CONFIGURE RECENT PROJECTS
        #################################

        settings = QtCore.QSettings(ORGANIZATION, APPNAME)
        examples = [
            expandPath('@examples/Animals'),
            expandPath('@examples/Diet'),
            expandPath('@examples/Family'),
            expandPath('@examples/LUBM'),
            expandPath('@examples/Pizza'),
        ]

        if not settings.contains('project/recent'):
            # From PyQt5 documentation: if the value of the setting is a container (corresponding
            # to either QVariantList, QVariantMap or QVariantHash) then the type is applied to the
            # contents of the container. So we can't use an empty list as default value because
            # PyQt5 needs to know the type of the contents added to the collection: we avoid
            # this problem by placing the list of example projects as recent project list.
            settings.setValue('project/recent', examples)
        else:
            # If we have some projects in our recent list, check whether they exists on the
            # filesystem. If they do not exists we remove them from our recent list.
            projects = []
            for path in map(expandPath, settings.value('project/recent')):
                if isdir(path) and path not in projects:
                    projects.append(path)
            settings.setValue('project/recent', projects or examples)
            settings.sync()

        #############################################
        # CONFIGURE FONTS
        #################################

        fontDB = QtGui.QFontDatabase()
        fontDB.addApplicationFont(':/fonts/Roboto-Black')
        fontDB.addApplicationFont(':/fonts/Roboto-BlackItalic')
        fontDB.addApplicationFont(':/fonts/Roboto-Bold')
        fontDB.addApplicationFont(':/fonts/Roboto-BoldItalic')
        fontDB.addApplicationFont(':/fonts/Roboto-Italic')
        fontDB.addApplicationFont(':/fonts/Roboto-Light')
        fontDB.addApplicationFont(':/fonts/Roboto-LightItalic')
        fontDB.addApplicationFont(':/fonts/Roboto-Medium')
        fontDB.addApplicationFont(':/fonts/Roboto-MediumItalic')
        fontDB.addApplicationFont(':/fonts/Roboto-Regular')
        fontDB.addApplicationFont(':/fonts/Roboto-Thin')
        fontDB.addApplicationFont(':/fonts/Roboto-ThinItalic')
        fontDB.addApplicationFont(':/fonts/RobotoCondensed-Bold')
        fontDB.addApplicationFont(':/fonts/RobotoCondensed-BoldItalic')
        fontDB.addApplicationFont(':/fonts/RobotoCondensed-Italic')
        fontDB.addApplicationFont(':/fonts/RobotoCondensed-Light')
        fontDB.addApplicationFont(':/fonts/RobotoCondensed-LightItalic')
        fontDB.addApplicationFont(':/fonts/RobotoCondensed-Medium')
        fontDB.addApplicationFont(':/fonts/RobotoCondensed-MediumItalic')
        fontDB.addApplicationFont(':/fonts/RobotoCondensed-Regular')
        fontDB.addApplicationFont(':/fonts/RobotoMono-Bold')
        fontDB.addApplicationFont(':/fonts/RobotoMono-BoldItalic')
        fontDB.addApplicationFont(':/fonts/RobotoMono-Italic')
        fontDB.addApplicationFont(':/fonts/RobotoMono-Light')
        fontDB.addApplicationFont(':/fonts/RobotoMono-LightItalic')
        fontDB.addApplicationFont(':/fonts/RobotoMono-Medium')
        fontDB.addApplicationFont(':/fonts/RobotoMono-MediumItalic')
        fontDB.addApplicationFont(':/fonts/RobotoMono-Regular')
        fontDB.addApplicationFont(':/fonts/RobotoMono-Thin')
        fontDB.addApplicationFont(':/fonts/RobotoMono-ThinItalic')

        self.setFont(Font('Roboto', 12))

        #############################################
        # CONFIGURE LAYOUT
        #################################

        buffer = ''
        resources = expandPath('@resources/styles/')
        for name in os.listdir(resources):
            path = os.path.join(resources, name)
            if fexists(path) and File.forPath(path) is File.Qss:
                buffer += fread(path)
        self.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
        self.setStyle(EddyProxyStyle('Fusion'))
        self.setStyleSheet(buffer)

        #############################################
        # LOOKUP PLUGINS
        #################################

        PluginManager.scan('@plugins/', '@home/plugins/')

        #############################################
        # LOOKUP REASONERS
        #################################

        ReasonerManager.scan('@reasoners/', '@home/reasoners/')

        #############################################
        # CLOSE THE SPLASH SCREEN
        #################################

        if splash and not options.nosplash:
            splash.sleep()
            splash.close()

        #############################################
        # CONFIGURE THE WORKSPACE
        #################################

        workspace = expandPath(settings.value('workspace/home', WORKSPACE, str))
        if not isdir(workspace):
            window = WorkspaceDialog()
            if window.exec_() == WorkspaceDialog.Rejected:
                raise SystemExit

    def isRunning(self):
        """
        Returns True if there is already another instance of Eddy which is running, False otherwise.
        :rtype: bool
        """
        return self.running

    def start(self, options):
        """
        Run the application by showing the welcome dialog.
        :type options: Namespace
        """
        self.welcome = Welcome(self)
        self.welcome.show()
        if options.open and isdir(options.open):
            self.sgnCreateSession.emit(expandPath(options.open))

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(str)
    def doCreateSession(self, path):
        """
        Create a session using the given project path.
        :type path: str
        """
        for session in self.sessions:
            # Look among the active sessions and see if we already have
            # a session loaded for the given project: if so, focus it.
            if session.project.path == path:
                session.show()
                break
        else:
            # If we do not have a session for the given project we'll create one.
            with BusyProgressDialog('Loading project: {0}'.format(os.path.basename(path))):
    
                try:
                    session = Session(self, path)
                except ProjectStopLoadingError:
                    pass
                except (ProjectNotFoundError, ProjectNotValidError, ProjectVersionError) as e:
                    LOGGER.warning('Failed to create session for project %s: %s', path, e)
                    msgbox = QtWidgets.QMessageBox()
                    msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
                    msgbox.setText('Failed to create session for project: <b>{0}</b>!'.format(os.path.basename(path)))
                    msgbox.setTextFormat(QtCore.Qt.RichText)
                    msgbox.setDetailedText(format_exception(e))
                    msgbox.setStandardButtons(QtWidgets.QMessageBox.Close)
                    msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
                    msgbox.setWindowTitle('Project Error!')
                    msgbox.exec_()
                except Exception as e:
                    raise e
                else:
                    
                    #############################################
                    # UPDATE RECENT PROJECTS
                    #################################
    
                    settings = QtCore.QSettings(ORGANIZATION, APPNAME)
                    projects = settings.value('project/recent', None, str) or []
    
                    try:
                        projects.remove(path)
                    except ValueError:
                        pass
                    finally:
                        projects.insert(0, path)
                        projects = projects[:8]
                        settings.setValue('project/recent', projects)
                        settings.sync()
    
                    #############################################
                    # CLOSE THE WELCOME SCREEN IF NECESSARY
                    #################################
    
                    try:
                        self.welcome.close()
                    except (AttributeError, RuntimeError):
                        pass
    
                    #############################################
                    # STARTUP THE SESSION
                    #################################
                    
                    connect(session.sgnQuit, self.doQuit)
                    connect(session.sgnClosed, self.onSessionClosed)
                    self.sessions.append(session)
                    session.show()
    
    @QtCore.pyqtSlot()
    def doQuit(self):
        """
        Quit Eddy.
        """
        for session in self.sessions:
            session.save()
        self.quit()

    @QtCore.pyqtSlot()
    def onSessionClosed(self):
        """
        Quit Eddy.
        """
        ## SAVE SESSION STATE
        session = self.sender()
        if session:
            session.save()
            self.sessions.remove(session)
        ## CLEANUP POSSIBLE LEFTOVERS
        self.sessions = DistinctList(filter(None, self.sessions))
        ## SWITCH TO AN ACTIVE WINDOW OR WELCOME PANEL
        if self.sessions:
            session = self.sessions[-1]
            session.show()
        else:
            self.welcome = Welcome(self)
            self.welcome.show()