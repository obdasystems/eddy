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

from PyQt5.QtCore import Qt, QEvent, QTextStream, pyqtSignal, pyqtSlot
from PyQt5.QtNetwork import QLocalSocket, QLocalServer
from PyQt5.QtWidgets import QApplication

from eddy import APPID
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
from eddy.ui.style import Clean


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

        self.inSocket = None
        self.inStream = None
        self.outSocket = QLocalSocket()
        self.outSocket.connectToServer(APPID)
        self.outStream = None
        self.isRunning = self.outSocket.waitForConnected()
        self.mainwindow = None
        self.pendingOpen = []
        self.server = None

        # We do not initialize a new instance of Eddy if there is a process running
        # and we are not executing the tests suite: we'll create a socket instead so we can
        # exchange messages between the 2 processes (this one and the already running one).
        if self.isRunning and not options.tests:
            self.outStream = QTextStream(self.outSocket)
            self.outStream.setCodec('UTF-8')
        else:
            self.server = QLocalServer()
            self.server.listen(APPID)
            self.outSocket = None
            self.outStream = None

            connect(self.server.newConnection, self.newConnection)
            connect(self.messageReceived, self.readMessage)

            ############################################################################################################
            #                                                                                                          #
            #   PERFORM EDDY INITIALIZATION                                                                            #
            #                                                                                                          #
            ############################################################################################################

            # Draw the splashscreen.
            self.splashscreen = None
            if not options.nosplash:
                self.splashscreen = SplashScreen(min_splash_time=4)
                self.splashscreen.show()

            # Setup layout.
            self.setStyle(Clean('Fusion'))
            with open(expandPath('@eddy/ui/clean.qss')) as sheet:
                self.setStyleSheet(sheet.read())

            # Create the main window.
            self.mainwindow = MainWindow()

            # Close the splashscreen.
            if self.splashscreen:
                self.splashscreen.wait(self.splashscreen.remaining)
                self.splashscreen.close()

            # Display the mainwindow.
            self.mainwindow.show()

            if Platform.identify() is Platform.Darwin:
                # On MacOS files being opened are handled as a QFileOpenEvent but since we don't
                # have a Main Window initialized we store them locally and we open them here.
                for filepath in self.pendingOpen:
                    self.openFile(filepath)
                self.pendingOpen = []
            else:
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
            self.pendingOpen = [event.file()]
            return True
        return super().event(event)

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def activate(self):
        """
        Activate the application by raising the main window.
        """
        if self.mainwindow:
            self.mainwindow.setWindowState((self.mainwindow.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
            self.mainwindow.activateWindow()
            self.mainwindow.raise_()

    def openFile(self, filepath):
        """
        Open the given file in the activation window.
        :type filepath: str
        :rtype: bool
        """
        if self.mainwindow:
            if not isEmpty(filepath) and os.path.isfile(filepath) and filepath.endswith(Filetype.Graphol.extension):
                self.mainwindow.openFile(filepath)
                return True
        return False

    def sendMessage(self, message):
        """
        Send a message to the other alive Eddy's process.
        :type message: str
        :rtype: bool
        """
        if self.outStream:
            self.outStream = self.outStream << message << '\n'
            self.outStream.flush()
            return self.outSocket.waitForBytesWritten()
        return False

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
        if self.inSocket:
            # Disconnect previously connected signal slot.
            disconnect(self.inSocket.readyRead, self.readyRead)

        # Create a new socket.
        self.inSocket = self.server.nextPendingConnection()

        if self.inSocket:
            self.inStream = QTextStream(self.inSocket)
            self.inStream.setCodec('UTF-8')
            connect(self.inSocket.readyRead, self.readyRead)
            self.activate()

    @pyqtSlot()
    def readyRead(self):
        """
        Executed whenever we need to read a message.
        """
        while True:
            message = self.inStream.readLine()
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