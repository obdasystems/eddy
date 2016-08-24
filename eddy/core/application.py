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

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtCore import Qt, QEvent, QTextStream, QSettings
from PyQt5.QtGui import QIcon
from PyQt5.QtNetwork import QLocalSocket, QLocalServer
from PyQt5.QtWidgets import QApplication, QMessageBox

from eddy import APPID, APPNAME, ORGANIZATION, WORKSPACE
from eddy.core.exceptions import ProjectNotFoundError
from eddy.core.exceptions import ProjectNotValidError
from eddy.core.functions.fsystem import is_dir
from eddy.core.functions.misc import isEmpty, format_exception
from eddy.core.functions.path import expandPath
from eddy.core.functions.signals import connect, disconnect
from eddy.core.output import getLogger

from eddy.ui.progress import BusyProgressDialog
from eddy.ui.session import Session
from eddy.ui.splash import Splash
from eddy.ui.style import Clean
from eddy.ui.workspace import WorkspaceDialog
from eddy.ui.welcome import Welcome


LOGGER = getLogger(__name__)


class Eddy(QApplication):
    """
    This class implements the main Qt application.
    """
    sgnMessageReceived = pyqtSignal(str)

    def __init__(self, options, argv):
        """
        Initialize Eddy.
        :type options: Namespace
        :type argv: list
        """
        super().__init__(argv)

        self.localServer = None
        self.inputSocket = None
        self.inputStream = None
        self.outputSocket = QLocalSocket()
        self.outputSocket.connectToServer(APPID)
        self.outputStream = None

        self.pending = []
        self.running = self.outputSocket.waitForConnected()
        self.session = None
        self.welcome = None

        if self.isAlreadyRunning() and not options.tests:
            # We allow to initialize multiple processes of Eddy only if we
            # are running the test suite to speed up tests execution time,
            # else we configure an output stream on which to route outgoing
            # messages to the alive Eddy process that will handle them.
            self.outputStream = QTextStream(self.outputSocket)
            self.outputStream.setCodec('UTF-8')
        else:
            # We are not running Eddy yet, so we initialize a QLocalServer
            # to intercept incoming messages from future instances of Eddy
            # not to spawn multiple process.
            self.localServer = QLocalServer()
            self.localServer.listen(APPID)
            self.outputStream = None
            self.outputSocket = None

            connect(self.localServer.newConnection, self.doAcceptConnection)
            connect(self.sgnMessageReceived, self.doReadMessage)

    #############################################
    #   EVENTS
    #################################

    def event(self, event):
        """
        Executed when an event is received.
        :type event: T <= QEvent | QFileOpenEvent
        """
        if event.type() == QEvent.FileOpen:
            self.pending = [event.file()]
            return True
        return super().event(event)

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
            splash = Splash(self, mtime=4)
            splash.show()

        #############################################
        # CONFIGURE DEFAULTS
        #################################

        settings = QSettings(ORGANIZATION, APPNAME)
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
            recentList = []
            for path in map(expandPath, settings.value('project/recent')):
                if is_dir(path):
                    recentList.append(path)

            settings.setValue('project/recent', recentList or examples)
            settings.sync()

        #############################################
        # CONFIGURE LAYOUT
        #################################

        clean = Clean('Fusion')
        self.setStyle(clean)
        self.setStyleSheet(clean.stylesheet)

        self.setAttribute(Qt.AA_UseHighDpiPixmaps)

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
        if not is_dir(workspace):
            window = WorkspaceDialog()
            if window.exec_() == WorkspaceDialog.Rejected:
                raise SystemExit

    def isAlreadyRunning(self):
        """
        Returns True if there is already another instance of Eddy which is running, False otherwise.
        :rtype: bool
        """
        return self.running

    def routePacket(self, argv):
        """
        Route input arguments to the already running Eddy process.
        :type argv: list
        :rtype: bool
        """
        if self.outputStream:
            self.outputStream = self.outputStream << ' '.join(argv) << '\n'
            self.outputStream.flush()
            return self.outputSocket.waitForBytesWritten()
        return False

    def save(self):
        """
        Save the state of the current active session.
        """
        if self.session:
            settings = QSettings(ORGANIZATION, APPNAME)
            settings.setValue('session/geometry', self.session.saveGeometry())
            settings.setValue('session/state', self.session.saveState())
            settings.sync()

    def start(self, options):
        """
        Run the application by showing the welcome dialog.
        :type options: Namespace
        """
        self.welcome = Welcome(self)
        self.welcome.show()
        if options.open and is_dir(options.open):
            self.doCreateSession(options.open)

    #############################################
    #   SLOTS
    #################################

    @pyqtSlot()
    def doAcceptConnection(self):
        """
        Executed whenever a new connection needs to be established.
        """
        if self.inputSocket:
            # If the input socket is already connected, disconnecting
            # so we can set it to listen on the new pending connection.
            disconnect(self.inputSocket.readyRead, self.onReadyRead)
        # Accept a new connectiong pending on the local server.
        self.inputSocket = self.localServer.nextPendingConnection()
        if self.inputSocket:
            # If we have a connection, setup the stream to accept packets.
            self.inputStream = QTextStream(self.inputSocket)
            self.inputStream.setCodec('UTF-8')
            connect(self.inputSocket.onReadyRead, self.onReadyRead)

    @pyqtSlot(str)
    def doCreateSession(self, path):
        """
        Create a session using the given project path.
        :type path: str
        """
        with BusyProgressDialog('Loading project: {0}'.format(os.path.basename(path))):

            try:
                self.session = Session(path)
            except ProjectNotFoundError as e:
                LOGGER.warning('Failed to create session for %s: %s', path, e)
                msgbox = QMessageBox()
                msgbox.setIconPixmap(QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
                msgbox.setText('Project <b>{0}</b> not found!'.format(os.path.basename(path)))
                msgbox.setStandardButtons(QMessageBox.Close)
                msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
                msgbox.setWindowTitle('Project not found!')
                msgbox.exec_()
            except ProjectNotValidError as e:
                LOGGER.warning('Failed to create session for %s: %s', path, e)
                msgbox = QMessageBox()
                msgbox.setIconPixmap(QIcon(':/icons/48/ic_error_outline_black').pixmap(48))
                msgbox.setText('Project <b>{0}</b> is not valid!'.format(os.path.basename(path)))
                msgbox.setTextFormat(Qt.RichText)
                msgbox.setDetailedText(format_exception(e))
                msgbox.setStandardButtons(QMessageBox.Close)
                msgbox.setWindowIcon(QIcon(':/icons/128/ic_eddy'))
                msgbox.setWindowTitle('Project not valid!')
                msgbox.exec_()
            except Exception as e:
                raise e
            else:
                connect(self.session.sgnQuit, self.doQuit)
                connect(self.session.sgnClosed, self.onSessionClosed)

                settings = QSettings(ORGANIZATION, APPNAME)
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

                if self.welcome:
                    self.welcome.close()
                self.session.show()

    
    @pyqtSlot()
    def doQuit(self):
        """
        Quit Eddy.
        """
        self.save()
        self.quit()

    @pyqtSlot(str)
    def doReadMessage(self, message):
        """
        Read a received message.
        :type message: str
        """
        pass

    @pyqtSlot()
    def onReadyRead(self):
        """
        Executed whenever we need to read a message.
        """
        while True:
            message = self.inputStream.readLine()
            if isEmpty(message):
                break
            self.sgnMessageReceived.emit(message)

    @pyqtSlot()
    def onSessionClosed(self):
        """
        Quit Eddy.
        """
        self.save()
        self.welcome = Welcome(self)
        self.welcome.show()