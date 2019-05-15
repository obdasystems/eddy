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


import argparse
import os
import pkg_resources
import platform
import sip
import sys

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtNetwork
from PyQt5 import QtWidgets

from eddy import APPID, APPNAME, ORGANIZATION, WORKSPACE, COPYRIGHT, VERSION, BUG_TRACKER
from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.qt import Font
from eddy.core.functions.fsystem import isdir
from eddy.core.functions.misc import format_exception
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect
from eddy.core.jvm import findJavaHome, addJVMClasspath, addJVMOptions
from eddy.core.output import getLogger
from eddy.core.plugin import PluginManager
from eddy.core.project import ProjectNotFoundError
from eddy.core.project import ProjectNotValidError
from eddy.core.project import ProjectStopLoadingError
from eddy.core.project import ProjectVersionError
from eddy.ui.progress import BusyProgressDialog
from eddy.ui.session import Session
from eddy.ui.splash import Splash
from eddy.ui.style import EddyProxyStyle
from eddy.ui.welcome import Welcome
from eddy.ui.workspace import WorkspaceDialog
# noinspection PyUnresolvedReferences
from eddy.ui import fonts_rc
# noinspection PyUnresolvedReferences
from eddy.ui import images_rc

_LINUX = sys.platform.startswith('linux')
_MACOS = sys.platform.startswith('darwin')
_WIN32 = sys.platform.startswith('win32')

LOGGER = getLogger()
app = None
msgbox = None


class Eddy(QtWidgets.QApplication):
    """
    This class implements the main QtCore.Qt application.
    """
    sgnCreateSession = QtCore.pyqtSignal(str)
    sgnSessionCreated = QtCore.pyqtSignal('QMainWindow')
    sgnSessionClosed = QtCore.pyqtSignal('QMainWindow')

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
        # CONFIGURE APPLICATION INFO
        #################################

        self.setOrganizationName(ORGANIZATION)
        self.setApplicationName(APPNAME)
        self.setApplicationDisplayName(APPNAME)
        self.setApplicationVersion(VERSION)

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

        style = EddyProxyStyle('Fusion')
        self.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
        self.setStyle(style)
        self.setStyleSheet(style.stylesheet)

        #############################################
        # LOOKUP PLUGINS
        #################################

        PluginManager.scan('@plugins/', '@home/plugins/')

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
                    self.sgnSessionCreated.emit(session)
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
    def doFocusSession(self):
        """
        Make the session specified in the action data the application active window.
        """
        action = self.sender()
        if isinstance(action, QtWidgets.QAction):
            session = action.data()
            if session in self.sessions:
                self.setActiveWindow(session)

    @QtCore.pyqtSlot()
    def doFocusNextSession(self):
        """
        Make the next session the application active window.
        """
        session = self.activeWindow()
        if session and session in self.sessions:
            nextSession = self.sessions[(self.sessions.index(session) + 1) % len(self.sessions)]
            self.setActiveWindow(nextSession)

    @QtCore.pyqtSlot()
    def doFocusPreviousSession(self):
        """
        Make the previous session the application active window.
        """
        session = self.activeWindow()
        if session and session in self.sessions:
            prevSession = self.sessions[(self.sessions.index(session) - 1) % len(self.sessions)]
            self.setActiveWindow(prevSession)

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
            self.sgnSessionClosed.emit(session)
        ## CLEANUP POSSIBLE LEFTOVERS
        self.sessions = DistinctList(filter(None, self.sessions))
        ## SWITCH TO AN ACTIVE WINDOW OR WELCOME PANEL
        if self.sessions:
            session = self.sessions[-1]
            session.show()
        else:
            self.welcome = Welcome(self)
            self.welcome.show()


def getArgumentParser():
    """
    Get an ArgumentParser that parses options accepted by this application.

    :rtype: ArgumentParser
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--nosplash', dest='nosplash', action='store_true')
    parser.add_argument('--tests', dest='tests', action='store_true')
    parser.add_argument('--open', dest='open', default=None)
    return parser


# noinspection PyArgumentList,PyUnusedLocal
def base_except_hook(exc_type, exc_value, exc_traceback):
    """
    Used to handle all uncaught exceptions.

    :type exc_type: class
    :type exc_value: Exception
    :type exc_traceback: Traceback
    """
    if issubclass(exc_type, KeyboardInterrupt):
        app.quit()
    else:
        global msgbox
        if not msgbox:
            LOGGER.critical(format_exception(exc_value))
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIconPixmap(QtGui.QPixmap(':/images/eddy-sad'))
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Fatal error!')
            msgbox.setText('This is embarrassing ...\n\n'
                           'A critical error has just occurred. {0} will continue to work, '
                           'however a reboot is highly recommended.'.format(APPNAME))
            msgbox.setInformativeText('If the problem persists you can '
                                      '<a href="{0}">submit a bug report</a>.'.format(BUG_TRACKER))
            msgbox.setDetailedText(format_exception(exc_value))
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Close | QtWidgets.QMessageBox.Ok)
            buttonOk = msgbox.button(QtWidgets.QMessageBox.Ok)
            buttonOk.setText('Close')
            buttonQuit = msgbox.button(QtWidgets.QMessageBox.Close)
            buttonQuit.setText('Quit {0}'.format(APPNAME))
            connect(buttonOk.clicked, msgbox.close)
            buttonQuit.clicked.connect(app.doQuit, QtCore.Qt.QueuedConnection)
            QtWidgets.QApplication.beep()
            msgbox.exec_()
            msgbox = None


# noinspection PyUnresolvedReferences,PyTypeChecker
def main():
    """
    Application entry point.
    """
    #############################################
    # PARSE ARGUMENTS AND CREATE THE APPLICATION
    #################################
    parser = getArgumentParser()
    sys.excepthook = base_except_hook
    options, _ = parser.parse_known_args(args=sys.argv)
    settings = QtCore.QSettings(ORGANIZATION, APPNAME)

    global app
    app = Eddy(options, sys.argv)
    if app.isRunning():
        sys.exit(0)

    #############################################
    # JVM SETUP
    #################################

    JAVA_HOME = findJavaHome()

    if not JAVA_HOME or not os.path.isdir(JAVA_HOME):
        shouldDisplayDialog = settings.value('dialogs/skipMissingJREWarning')
        if not shouldDisplayDialog:
            # CHECKBOX CALLBACK
            def checkboxStateChanged(state):
                settings.setValue('dialogs/missingJRE', state == QtCore.Qt.Checked)
                settings.sync()
            chkbox = QtWidgets.QCheckBox("Don't show this warning again.")
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIconPixmap(QtGui.QPixmap(':/images/eddy-sad'))
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Missing Java Runtime Environment')
            msgbox.setText('Unable to locate a valid Java installation on your system.')
            msgbox.setInformativeText('<p>Some features in {0} require access to a <br/>'
                                      '<a href="{1}">Java Runtime Environment</a> version 8 '
                                      'and will not be available if you continue.</p>'
                                      '<p>You can download a copy of the Java Runtime Environment '
                                      'from the <a href={2}>Java Downloads</a> page.</p>'
                                      .format(APPNAME, 'https://www.java.com/download',
                                              'https://www.oracle.com/technetwork/java/javase/downloads/index.html'))
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Abort | QtWidgets.QMessageBox.Ok)
            msgbox.setDefaultButton(QtWidgets.QMessageBox.Abort)
            msgbox.setCheckBox(chkbox)
            buttonOk = msgbox.button(QtWidgets.QMessageBox.Ok)
            buttonOk.setText('Continue without JRE')
            buttonQuit = msgbox.button(QtWidgets.QMessageBox.Abort)
            buttonQuit.setText('Quit {0}'.format(APPNAME))
            connect(chkbox.stateChanged, checkboxStateChanged)
            ret = msgbox.exec_()
            if ret == QtWidgets.QMessageBox.Abort:
                return 1

    os.environ['JAVA_HOME'] = JAVA_HOME or ''

    # ADD THE DIRECTORY CONTAINING JVM.DLL TO THE PATH VARIABLE ON WINDOWS
    if _WIN32:
        path = os.getenv('PATH', '')
        path = path.split(os.pathsep)
        path.insert(0, os.path.join(os.environ['JAVA_HOME'], 'jre', 'bin'))
        if platform.architecture()[0] == '32bit':
            path.insert(0, os.path.join(os.environ['JAVA_HOME'], 'jre', 'bin', 'client'))
        else:
            path.insert(0, os.path.join(os.environ['JAVA_HOME'], 'jre', 'bin', 'server'))
        os.environ['PATH'] = os.pathsep.join(path)

    # SET CLASSPATH AND OPTIONS
    if hasattr(sys, 'frozen'):
        resources = expandPath('@resources/lib/')
        if isdir(resources):
            for name in os.listdir(resources):
                path = os.path.join(resources, name)
                if os.path.isfile(path):
                    addJVMClasspath(path)
    for path in pkg_resources.resource_listdir(eddy.core.jvm.__name__, 'lib'):
        if File.forPath(path) is File.Jar:
            addJVMClasspath(pkg_resources.resource_filename(eddy.core.jvm.__name__, os.path.join('lib', path)))
    addJVMOptions('-Xmx512m', '-XX:+DisableExplicitGC', '-XX:+UseConcMarkSweepGC', '-XX:-UseAdaptiveSizePolicy')

    if hasattr(sys, 'frozen'):
        os.environ['REQUESTS_CA_BUNDLE'] = expandPath('@root/cacert.pem')

    #############################################
    # START THE APPLICATION
    #################################

    LOGGER.separator(separator='-')
    LOGGER.frame('%s v%s', APPNAME, VERSION, separator='|')
    LOGGER.frame(COPYRIGHT, separator='|')
    LOGGER.separator(separator='-')
    LOGGER.frame('OS: %s %s', platform.system(), platform.release(), separator='|')
    LOGGER.frame('Python version: %s', platform.python_version(), separator='|')
    LOGGER.frame('Qt version: %s', QtCore.QT_VERSION_STR, separator='|')
    LOGGER.frame('PyQt version: %s', QtCore.PYQT_VERSION_STR, separator='|')
    LOGGER.frame('SIP version: %s', sip.SIP_VERSION_STR, separator='|')
    LOGGER.separator(separator='-')

    app.configure(options)
    app.start(options)
    sys.exit(app.exec_())

