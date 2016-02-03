# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the construction of Graphol ontologies.  #
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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import os
import jnius_config

from argparse import ArgumentParser

from PyQt5.QtCore import QSettings, QEvent, pyqtSignal, pyqtSlot, QTextStream, Qt
from PyQt5.QtNetwork import QLocalSocket, QLocalServer
from PyQt5.QtWidgets import QApplication

from eddy.core.datatypes import Platform, Filetype
from eddy.core.functions import isEmpty, expandPath, connect, disconnect

########################################################
##         BEGIN JAVA VIRTUAL MACHINE SETUP           ##
########################################################

if os.path.isdir(expandPath('@resources/java/')):
    # If we are shipping the jvm then set the JAVA_HOME.
    os.environ['JAVA_HOME'] = expandPath('@resources/java/')

if Platform.identify() is Platform.Windows:
    # On windows we must add the jvm.dll to system path.
    path = os.getenv('Path', '')
    path = path.split(os.pathsep)
    path.insert(0, os.path.join(os.environ['JAVA_HOME'], 'bin', 'client'))
    os.environ['Path'] = os.pathsep.join(path)

classpath = []
resources = expandPath('@resources/lib/')
for name in os.listdir(resources):
    path = os.path.join(resources, name)
    if os.path.isfile(path):
        classpath.append(path)

jnius_config.add_options('-ea', '-Xmx512m')
jnius_config.set_classpath(*classpath)

########################################################
##          END JAVA VIRTUAL MACHINE SETUP            ##
########################################################


from eddy.ui.mainwindow import MainWindow
from eddy.ui.splash import SplashScreen
from eddy.ui.styles import Style


class Eddy(QApplication):
    """
    This class implements the main Qt application.
    """
    messageReceived = pyqtSignal(str)

    def __init__(self, argv):
        """
        Initialize Eddy.
        :type argv: list
        """
        super().__init__(argv)

        parser = ArgumentParser()
        parser.add_argument('--nosplash', dest='nosplash', action='store_true')
        parser.add_argument('--tests', dest='tests', action='store_true')

        options, args = parser.parse_known_args(args=argv)

        self._id = '60119D28-5488-4663-879E-34FCD9C5C38C'
        self._activationWindow = None
        self._activateOnMessage = False
        self._localServer = None
        self._inSocket = None
        self._inStream = None
        self._outSocket = QLocalSocket()
        self._outSocket.connectToServer(self._id)
        self._outStream = None
        self._isRunning = self._outSocket.waitForConnected()

        # We do not initialize a new instance of Eddy if there is a process running
        # and we are not executing the tests suite: we'll create a socket instead so we can
        # exchange messages between the 2 processes (this one and the already running one).
        if self._isRunning and not options.tests:
            self._outStream = QTextStream(self._outSocket)
            self._outStream.setCodec('UTF-8')
        else:
            self._localServer = QLocalServer()
            self._localServer.listen(self._id)
            self._outSocket = None
            self._outStream = None

            connect(self._localServer.newConnection, self.newConnection)
            connect(self.messageReceived, self.readMessage)

            ############################################################################################################
            #                                                                                                          #
            #   PERFORM EDDY INITIALIZATION                                                                            #
            #                                                                                                          #
            ############################################################################################################

            # Draw the splashscreen.
            self._splashScreen = None
            if not options.nosplash:
                self._splashScreen = SplashScreen(min_splash_time=4)
                self._splashScreen.show()

            # Initialize application settings.
            self._appSettings = QSettings(expandPath('@home/Eddy.ini'), QSettings.IniFormat)

            # Setup layout.
            style = Style.forName(self._appSettings.value('appearance/style', 'light', str))
            self.setStyle(style)
            self.setStyleSheet(style.qss())

            # Initialize recent documents.
            if not self._appSettings.contains('document/recent_documents'):
                # From PyQt5 documentation: if the value of the setting is a container (corresponding to either
                # QVariantList, QVariantMap or QVariantHash) then the type is applied to the contents of the
                # container. So according to this we can't use an empty list as default value because PyQt5 needs
                # to know the type of the contents added to the collection: we avoid this problem by placing
                # the list of examples file in the recentDocumentList (only if there is no list defined already).
                self._appSettings.setValue('document/recent_documents', [
                    expandPath('@examples/Animals.graphol'),
                    expandPath('@examples/Diet.graphol'),
                    expandPath('@examples/Family.graphol'),
                    expandPath('@examples/Pizza.graphol'),
                ])

            # Create the main window.
            self.setActivationWindow(activationWindow=MainWindow(), activateOnMessage=True)

            # Close the splashscreen.
            if self._splashScreen:
                self._splashScreen.wait(self._splashScreen.remaining)
                self._splashScreen.close()

            # Display the mainwindow.
            window = self.activationWindow()
            window.show()

            if Platform.identify() is not Platform.Darwin:
                # Perform document opening if files have been added to sys.argv. This is not
                # executed on Mac OS since this is already handled as a QFileOpenEvent instance.
                for filepath in argv:
                    self.openFile(filepath)

    ####################################################################################################################
    #                                                                                                                  #
    #   EVENTS                                                                                                         #
    #                                                                                                                  #
    ####################################################################################################################

    def event(self, event):
        """
        Executed when an event is received.
        :type event: T <= QEvent | QFileOpenEvent
        """
        if event.type() == QEvent.FileOpen:
            return self.openFile(event.file())
        return super().event(event)

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def activateWindow(self):
        """
        Activate the activation window.
        """
        if self._activationWindow:
            self._activationWindow.setWindowState((self._activationWindow.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
            self._activationWindow.activateWindow()
            self._activationWindow.raise_()

    def activationWindow(self):
        """
        Returns the reference to the window that needs to be activated when the process is already running.
        :type: MainWindow
        """
        return self._activationWindow

    def id(self):
        """
        Returns the application id.
        :rtype: str
        """
        return self._id

    def isRunning(self):
        """
        Tells whether this application is already running by checking the AppId.
        :rtype: bool
        """
        return self._isRunning

    def openFile(self, filepath):
        """
        Open the given file in the activation window.
        :type filepath: str
        :rtype: bool
        """
        if self._activationWindow:
            if not isEmpty(filepath) and os.path.isfile(filepath) and filepath.endswith(Filetype.Graphol.suffix):
                self._activationWindow.openFile(filepath)
                return True
        return False

    def sendMessage(self, message):
        """
        Send a message to the other alive Eddy's process.
        :type message: str
        :rtype: bool
        """
        if self._outStream:
            self._outStream = self._outStream << message << '\n'
            self._outStream.flush()
            return self._outSocket.waitForBytesWritten()
        return False

    def setActivationWindow(self, activationWindow, activateOnMessage=True):
        """
        Set the activation window.
        :type activationWindow: MainWindow
        :type activateOnMessage: bool
        """
        self._activationWindow = activationWindow
        self._activateOnMessage = activateOnMessage

    ####################################################################################################################
    #                                                                                                                  #
    #   SLOTS                                                                                                          #
    #                                                                                                                  #
    ####################################################################################################################

    @pyqtSlot()
    def newConnection(self):
        """
        Executed whenever a message is received.
        """
        if self._inSocket:
            # Disconnect previously connected signal slot.
            disconnect(self._inSocket.readyRead, self.readyRead)

        # Create a new socket.
        self._inSocket = self._localServer.nextPendingConnection()

        if self._inSocket:
            self._inStream = QTextStream(self._inSocket)
            self._inStream.setCodec('UTF-8')
            connect(self._inSocket.readyRead, self.readyRead)

            self._inSocket.readyRead.connect(self.readyRead)
            if self._activateOnMessage:
                self.activateWindow()

    @pyqtSlot()
    def readyRead(self):
        """
        Executed whenever we need to read a message.
        """
        while True:
            # QTextStream.readLine() blocks so we don't loop indefinitely here.
            message = self._inStream.readLine()

            # Exit the loop if we get an empty message.
            if isEmpty(message):
                break

            self.messageReceived.emit(message)

    @pyqtSlot(str)
    def readMessage(self, message):
        """
        Read a received message.
        :type message: str
        """
        for filepath in message.split(' '):
            self.openFile(filepath)