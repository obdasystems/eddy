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
import platform
import subprocess
import sys
from types import TracebackType
from typing import (
    cast,
    Any,
    List,
    Optional,
    Type,
)

from PyQt5 import (
    QtCore,
    QtGui,
    QtNetwork,
    QtWidgets,
)

import eddy
from eddy import (
    APPID,
    APPNAME,
    BUG_TRACKER,
    COPYRIGHT,
    ORGANIZATION,
    ORGANIZATION_DOMAIN,
    ORGANIZATION_REVERSE_DOMAIN,
    VERSION,
)
from eddy.core.commandline import CommandLineParser
from eddy.core.datatypes.collections import DistinctList
from eddy.core.datatypes.qt import Font
from eddy.core.datatypes.system import (
    File,
    IS_WIN,
    IS_FROZEN,
    IS_XDG,
)
from eddy.core.functions.fsystem import (
    fexists,
    faccess,
    isdir,
)
from eddy.core.functions.misc import format_exception
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect
from eddy.core.jvm import (
    addJVMClasspath,
    addJVMOptions,
    findJavaHome,
)
from eddy.core.output import getLogger
from eddy.core.plugin import PluginManager
from eddy.core.project import (
    ProjectNotFoundError,
    ProjectNotValidError,
    ProjectStopLoadingError,
    ProjectVersionError,
)
from eddy.core.qt import sip
# noinspection PyUnresolvedReferences
from eddy.ui import fonts_rc
# noinspection PyUnresolvedReferences
from eddy.ui import images_rc
from eddy.ui.progress import BusyProgressDialog
from eddy.ui.session import Session
from eddy.ui.splash import Splash
from eddy.ui.style import EddyProxyStyle
from eddy.ui.welcome import Welcome

#############################################
#   GLOBALS
#################################

LOGGER = getLogger()
app = None
msgbox = None


class Eddy(QtWidgets.QApplication):
    """
    This class implements the main QtCore.Qt application.
    """
    RestartCode = 8
    sgnCreateSession = QtCore.pyqtSignal(str)
    sgnSessionCreated = QtCore.pyqtSignal(QtWidgets.QMainWindow)
    sgnSessionClosed = QtCore.pyqtSignal(QtWidgets.QMainWindow)

    def __init__(self, argv: List[str]) -> None:
        """
        Initialize Eddy.

        :param argv: Command line arguments
        """
        super().__init__(argv)

        self.openFilePath = None
        self.server = None
        self.sessions = DistinctList()
        self.started = False
        self.welcome = None

        # APPLICATION INFO
        self.setDesktopFileName('{}.{}'.format(ORGANIZATION_REVERSE_DOMAIN, APPNAME))
        self.setOrganizationName(ORGANIZATION.lower() if IS_XDG else ORGANIZATION)
        self.setOrganizationDomain(ORGANIZATION_DOMAIN)
        self.setApplicationName(APPNAME.lower())
        self.setApplicationDisplayName(APPNAME)
        self.setApplicationVersion(VERSION)

        # PARSE COMMAND LINE ARGUMENTS
        self.options = CommandLineParser()
        self.options.process(argv)

        # CHECK FOR A RUNNING INSTANCE
        self.socket = QtNetwork.QLocalSocket()
        self.socket.connectToServer(APPID)
        self.running = self.socket.waitForConnected()
        if not self.isRunning():
            QtNetwork.QLocalServer.removeServer(APPID)
            self.server = QtNetwork.QLocalServer()
            self.server.listen(APPID)
            self.socket = None
            connect(self.sgnCreateSession, self.doCreateSession)

        connect(self.aboutToQuit, self.onAboutToQuit)

    #############################################
    #   EVENTS
    #################################

    def event(self, event: QtCore.QEvent) -> bool:
        """
        Executed when an event is received.
        """
        # HANDLE FILEOPEN EVENT (TRIGGERED BY MACOS WHEN DOUBLE CLICKING A FILE)
        if event.type() == QtCore.QEvent.FileOpen:
            path = expandPath(cast(QtGui.QFileOpenEvent, event).file())
            type = File.forPath(path)
            if fexists(path) and type is File.Graphol:
                if self.started:
                    self.sgnCreateSession.emit(path)
                else:
                    # CACHE PATH UNTIL APPLICATION STARTUP HAS COMPLETED
                    self.openFilePath = path

        return super().event(event)

    #############################################
    #   INTERFACE
    #################################

    def configure(self) -> None:
        """
        Perform initial configuration tasks for Eddy to work properly.
        """
        #############################################
        # CONFIGURE FONTS
        #################################

        fontDB = QtGui.QFontDatabase()
        fonts = QtCore.QDirIterator(':/fonts/')
        while fonts.hasNext():
            fontDB.addApplicationFont(fonts.next())

        # FONT SUBSTITUTIONS
        QtGui.QFont.insertSubstitution('Sans Serif', 'Roboto')
        QtGui.QFont.insertSubstitution('Monospace', 'Roboto Mono')

        # APPLICATION DEFAULT FONT
        self.setFont(Font('Roboto', pixelSize=12))

        #############################################
        # CONFIGURE LAYOUT
        #################################

        style = EddyProxyStyle('Fusion')
        self.setStyle(style)
        self.setStyleSheet(style.stylesheet)

        #############################################
        # DRAW THE SPLASH SCREEN
        #################################

        splash = None
        if not self.options.isSet(CommandLineParser.NO_SPLASH):
            splash = Splash(mtime=2)
            splash.show()

        #############################################
        # CONFIGURE RECENT PROJECTS
        #################################

        settings = QtCore.QSettings()

        if not settings.contains('project/recent'):
            # From PyQt5 documentation: if the value of the setting is a container (corresponding
            # to either QVariantList, QVariantMap or QVariantHash) then the type is applied to the
            # contents of the container. So we can't use an empty list as default value because
            # PyQt5 needs to know the type of the contents added to the collection: we avoid
            # this problem by placing the list of example projects as recent project list.
            examples = list(filter(lambda path: fexists(path) and faccess(path), [
                expandPath('@examples/Animals{}'.format(File.Graphol.extension)),
                expandPath('@examples/Diet{}'.format(File.Graphol.extension)),
                expandPath('@examples/Family{}'.format(File.Graphol.extension)),
                expandPath('@examples/LUBM{}'.format(File.Graphol.extension)),
                expandPath('@examples/Pizza{}'.format(File.Graphol.extension)),
            ]))
            settings.setValue('project/recent', examples)
        else:
            # If we have some projects in our recent list, check whether they exists on the
            # filesystem. If they do not exists we remove them from our recent list.
            projects = []
            for path in map(expandPath, settings.value('project/recent', None, str) or []):
                if fexists(path) and path not in projects:
                    projects.append(path)
            settings.setValue('project/recent', projects)
            settings.sync()

        #############################################
        # LOOKUP PLUGINS
        #################################

        PluginManager.scan('@plugins/', '@data/plugins/')

        #############################################
        # CLOSE THE SPLASH SCREEN
        #################################

        if splash and not self.options.isSet(CommandLineParser.NO_SPLASH):
            splash.sleep()
            splash.close()

    def isRunning(self) -> bool:
        """
        Returns `True` if there is already another instance
        of Eddy which is running, `False` otherwise.
        """
        return self.running

    def start(self) -> None:
        """
        Run the application by showing the welcome dialog.
        """
        # PROCESS COMMAND LINE ARGUMENTS
        args = self.options.positionalArguments()

        if self.openFilePath:
            args.append(self.openFilePath)
            self.openFilePath = None
        # SHOW WELCOME DIALOG
        self.welcome = Welcome(self)
        self.welcome.show()
        # PROCESS ADDITIONAL COMMAND LINE OPTIONS
        if self.options.isSet(CommandLineParser.JVM_CLASSPATH):
            value = self.options.value(CommandLineParser.JVM_CLASSPATH)
            addJVMClasspath(*value.split(os.pathsep))
        if self.options.isSet(CommandLineParser.JVM_OPTS):
            value = self.options.value(CommandLineParser.JVM_OPTS)
            addJVMOptions(*value.split())
        # POSITIONAL ARGUMENTS
        for path in filter(None, map(os.path.abspath, args)):
            if fexists(path) and faccess(path):
                self.sgnCreateSession.emit(path)
            else:
                LOGGER.warning('Unable to open project file: %s', path)
        # COMPLETE STARTUP
        self.started = True

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot(str)
    @QtCore.pyqtSlot(str, str, str, str)
    @QtCore.pyqtSlot(str, str, str, str, str)
    def doCreateSession(
        self,
        path: Optional[str] = None,
        name: Optional[str] = None,
        iri: Optional[str] = None,
        prefix: Optional[str] = None,
        owl_path: Optional[str] = None
    ) -> None:
        """
        Create a session using the given project path.

        :param path: Path to the project file, if opening an existing project
        :param name: Name, only when creating a new project
        :param iri: Ontology IRI, only when creating a new project
        :param prefix: IRI prefix, when creating a new project
        """
        for session in self.sessions:
            # Look among the active sessions and see if we already have
            # a session loaded for the given project: if so, focus it.
            if session.project.path == path:
                session.show()
                break
        else:
            # If we do not have a session for the given project we'll create one.
            with BusyProgressDialog('Loading project: {0}'.format(path)):
                try:
                    session = Session(self, path, name=name, iri=iri, prefix=prefix, owl_path=owl_path)
                except ProjectStopLoadingError:
                    pass
                except (ProjectNotFoundError, ProjectNotValidError, ProjectVersionError) as e:
                    LOGGER.warning('Failed to create session for project %s: %s', path, e)
                    msgbox = QtWidgets.QMessageBox()
                    msgbox.setIconPixmap(QtGui.QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
                    msgbox.setText('Failed to create session for project: <b>{0}</b>!'.format(path))
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

                    settings = QtCore.QSettings()
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

                    if self.welcome:
                        self.welcome.close()
                        self.welcome = None

                    #############################################
                    # STARTUP THE SESSION
                    #################################

                    connect(session.sgnQuit, self.doQuit)
                    connect(session.sgnClosed, self.onSessionClosed)
                    self.sessions.append(session)
                    self.sgnSessionCreated.emit(session)
                    session.show()
                    if owl_path:
                        session.sgnStartOwlImport[str].emit(owl_path)

    @QtCore.pyqtSlot()
    def doQuit(self) -> None:
        """
        Quit Eddy.
        """
        for session in self.sessions:
            if not session.close():
                return
        self.quit()

    @QtCore.pyqtSlot()
    def doRestart(self) -> None:
        """
        Restart Eddy.
        """
        for session in self.sessions:
            if not session.close():
                return
        self.exit(Eddy.RestartCode)

    @QtCore.pyqtSlot()
    def doFocusSession(self) -> None:
        """
        Make the session specified in the action data the application active window.
        """
        action = self.sender()
        if isinstance(action, QtWidgets.QAction):
            session = action.data()
            if session in self.sessions:
                self.setActiveWindow(session)

    @QtCore.pyqtSlot()
    def doFocusNextSession(self) -> None:
        """
        Make the next session the application active window.
        """
        session = self.activeWindow()
        if session and session in self.sessions:
            nextSession = self.sessions[(self.sessions.index(session) + 1) % len(self.sessions)]
            self.setActiveWindow(nextSession)

    @QtCore.pyqtSlot()
    def doFocusPreviousSession(self) -> None:
        """
        Make the previous session the application active window.
        """
        session = self.activeWindow()
        if session and session in self.sessions:
            prevSession = self.sessions[(self.sessions.index(session) - 1) % len(self.sessions)]
            self.setActiveWindow(prevSession)

    @QtCore.pyqtSlot()
    def onAboutToQuit(self) -> None:
        """
        Executed when the application is about to quit.
        """
        if self.server:
            self.server.close()

    @QtCore.pyqtSlot()
    def onSessionClosed(self) -> None:
        """
        Quit Eddy.
        """
        # SAVE SESSION STATE
        session = self.sender()
        if session:
            # noinspection PyUnresolvedReferences
            session.save()
            self.sessions.remove(session)
            self.sgnSessionClosed.emit(session)
        # CLEANUP POSSIBLE LEFTOVERS
        self.sessions = DistinctList(filter(None, self.sessions))
        # SWITCH TO AN ACTIVE WINDOW OR WELCOME PANEL
        if self.sessions:
            session = self.sessions[-1]
            session.show()
        else:
            self.welcome = Welcome(self)
            self.welcome.show()


# noinspection PyUnusedLocal
def base_except_hook(
    exc_type: Type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType,
) -> Any:
    """
    Used to handle all uncaught exceptions.

    :param exc_type: The exception type
    :param exc_value: The exception instance
    :param exc_traceback: The exception traceback
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
def main() -> int:
    """
    Application entry point.
    """
    #############################################
    # SETUP EXCEPTION HOOK
    #################################
    sys.excepthook = base_except_hook

    #############################################
    # PARSE ARGUMENTS AND CREATE THE APPLICATION
    #################################

    # ENABLE HIGH-DPI SUPPORT
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_Use96Dpi)

    global app
    app = Eddy(sys.argv)
    if app.isRunning():
        return 0

    #############################################
    # JVM SETUP
    #################################

    JAVA_HOME = findJavaHome()

    if not JAVA_HOME or not os.path.isdir(JAVA_HOME):
        settings = QtCore.QSettings()
        shouldDisplayDialog = settings.value('dialogs/noJVM')
        if not shouldDisplayDialog:
            # CHECKBOX CALLBACK
            def checkboxStateChanged(state):
                settings.setValue('dialogs/noJVM', state == QtCore.Qt.Checked)
                settings.sync()
            global msgbox
            chkbox = QtWidgets.QCheckBox("Don't show this warning again.")
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIconPixmap(QtGui.QPixmap(':/images/eddy-sad'))
            msgbox.setWindowIcon(QtGui.QIcon(':/icons/128/ic_eddy'))
            msgbox.setWindowTitle('Missing Java Runtime Environment')
            msgbox.setText('Unable to locate a valid Java installation on your system.')
            msgbox.setInformativeText('<p>Some features in {0} require access to a <br/>'
                                      '<a href="{1}">Java Runtime Environment</a> '
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
            buttonQuit.clicked.connect(app.doQuit, QtCore.Qt.QueuedConnection)
            connect(chkbox.stateChanged, checkboxStateChanged)
            ret = msgbox.exec_()
            if ret == QtWidgets.QMessageBox.Abort:
                return 1

    #############################################
    # BEGIN ENVIRONMENT SPECIFIC SETUP
    #################################

    os.environ['JAVA_HOME'] = JAVA_HOME or ''

    # ADD THE DIRECTORY CONTAINING JVM.DLL TO THE PATH VARIABLE ON WINDOWS
    if IS_WIN:
        path = os.getenv('PATH', '')
        path = path.split(os.pathsep)
        # FOR JAVA 8
        if isdir(os.path.join(os.environ['JAVA_HOME'], 'jre', 'bin')):
            bindir = os.path.join(os.environ['JAVA_HOME'], 'jre', 'bin')
        # FOR JAVA 9+
        else:
            bindir = os.path.join(os.environ['JAVA_HOME'], 'bin')
        path.insert(0, bindir)
        if platform.architecture()[0] == '32bit':
            path.insert(0, os.path.join(bindir, 'client'))
        else:
            path.insert(0, os.path.join(bindir, 'server'))
        os.environ['PATH'] = os.pathsep.join(path)

    # SET CLASSPATH AND OPTIONS
    if IS_FROZEN:
        resources = expandPath('@resources/lib/')
        if isdir(resources):
            for name in os.listdir(resources):
                path = os.path.join(resources, name)
                if os.path.isfile(path):
                    addJVMClasspath(path)
    else:
        from importlib.resources import files
        for path in files(eddy.core.jvm.__name__).iterdir():
            if File.forPath(path.as_posix()) is File.Jar:
                addJVMClasspath(path.as_posix())

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

    app.configure()
    app.start()
    ret = app.exec_()
    if ret == Eddy.RestartCode:
        nargs = []
        if os.path.basename(sys.argv[0]) == 'eddy':
            # LAUNCHED VIA LAUNCHER SCRIPT
            nargs.append(sys.argv[0])
        elif IS_FROZEN:
            # LAUNCHED FROM DISTRIBUTION EXECUTABLE
            nargs.append(sys.executable)
        else:
            # LAUNCHED VIA THE INTERPRETER
            nargs.extend([sys.executable, sys.argv[0]])
        nargs.extend(sys.argv[1:])
        subprocess.Popen(nargs)
    return ret
