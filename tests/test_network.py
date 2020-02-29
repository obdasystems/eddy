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


from PyQt5 import (
    QtCore,
    QtNetwork,
    QtTest,
)

from eddy.core.datatypes.system import Channel
from eddy.core.functions.fsystem import fread
from eddy.core.functions.path import expandPath
from eddy.core.network import NetworkManager


#############################################
# NETWORK MANAGER TESTS
#################################

def test_check_for_update_release_update_available(qtbot):
    # GIVEN
    response_content = fread(expandPath('@tests/test_resources/network/release_update_available.json')).encode('utf-8')
    response_data = b'application/json'
    update_provider = UpdateContentProvider(response_content, response_data)
    nmanager = NetworkManagerMock(None, content_provider=update_provider)
    # WHEN
    with qtbot.waitSignals([nmanager.sgnUpdateAvailable]) as blocker, \
            qtbot.assertNotEmitted(nmanager.sgnNoUpdateDataAvailable), \
            qtbot.assertNotEmitted(nmanager.sgnNoUpdateAvailable):
        nmanager.checkForUpdate(Channel.Stable, '1.0.0')
    # THEN
    assert 1 == len(blocker.all_signals_and_args)


def test_check_for_update_prerelease_update_available(qtbot):
    # GIVEN
    response_content = fread(expandPath('@tests/test_resources/network/prerelease_update_available.json')).encode('utf-8')
    response_data = b'application/json'
    update_provider = UpdateContentProvider(response_content, response_data)
    nmanager = NetworkManagerMock(None, content_provider=update_provider)
    # WHEN
    with qtbot.waitSignals([nmanager.sgnUpdateAvailable]) as blocker, \
            qtbot.assertNotEmitted(nmanager.sgnNoUpdateDataAvailable), \
            qtbot.assertNotEmitted(nmanager.sgnNoUpdateAvailable):
        nmanager.checkForUpdate(Channel.Beta, '1.0.0')
    # THEN
    assert 1 == len(blocker.all_signals_and_args)


def test_check_for_update_no_update_available(qtbot):
    # GIVEN
    response_content = fread(expandPath('@tests/test_resources/network/no_update_available.json')).encode('utf-8')
    response_data = b'application/json'
    update_provider = UpdateContentProvider(response_content, response_data)
    nmanager = NetworkManagerMock(None, content_provider=update_provider)
    # WHEN
    with qtbot.waitSignals([nmanager.sgnNoUpdateAvailable]) as blocker, \
            qtbot.assertNotEmitted(nmanager.sgnNoUpdateDataAvailable), \
            qtbot.assertNotEmitted(nmanager.sgnUpdateAvailable):
        nmanager.checkForUpdate(Channel.Stable, '1.0.0')
    # THEN
    assert 1 == len(blocker.all_signals_and_args)


class NetworkManagerMock(NetworkManager):
    """
    Subclass of NetworkManager that can be used to mock network replies.
    """
    def __init__(self, parent=None, **kwargs):
        """
        Initialize the mock network manager.
        """
        super().__init__(parent)
        self.contentProvider = kwargs.get('content_provider')

    # noinspection PyMethodOverriding
    def createRequest(self, operation, request, device):
        """
        Overrides protected createRequest to provide a mocked network reply.
        :type operation:
        :type request:
        :type device:
        :rtype: QNetworkReply
        """
        if self.contentProvider:
            return NetworkReplyMock(self, operation, request, self.contentProvider)
        else:
            return super().createRequest(operation, request, device)


class NetworkReplyMock(QtNetwork.QNetworkReply):
    """
    Subclass of QNetworkReply that can provide mock network responses.
    """
    def __init__(self, parent, operation, request, contentProvider):
        super().__init__(parent)
        self.setRequest(request)
        self.setOperation(operation)
        self.setUrl(request.url())
        self.bytesRead = 0
        self.content = b''
        self.data = b''
        self.offset = 0
        self.contentProvider = contentProvider
        # PRETEND SOME NETWORK DELAY
        QtCore.QTimer.singleShot(500, self.loadContent)

    def loadContent(self):
        self.content, self.data = self.contentProvider(self.operation(), self.request())
        self.offset = 0
        self.open(QtCore.QIODevice.ReadOnly | QtCore.QIODevice.Unbuffered)
        self.setHeader(QtNetwork.QNetworkRequest.ContentTypeHeader, QtCore.QByteArray(self.data))
        self.setHeader(QtNetwork.QNetworkRequest.ContentLengthHeader, len(self.content))
        self.setFinished(True)
        QtCore.QTimer.singleShot(0, self.readyRead)
        QtCore.QTimer.singleShot(0, self.finished)

    def manager(self):
        return self.parent()

    def abort(self):
        pass

    def isSequential(self):
        return True

    def bytesAvailable(self):
        available = len(self.content) - self.bytesRead + super().bytesAvailable()
        return available

    def readData(self, size):
        if self.bytesRead >= len(self.content):
            return None
        data = self.content[self.bytesRead:self.bytesRead + size]
        self.bytesRead += len(data)
        return data


class UpdateContentProvider(object):
    """
    Content provider for update requests
    """
    def __init__(self, content=None, data=None, **kwargs):
        self.content = content
        self.data = data
        self.delay = kwargs.get('delay', None)

    def __call__(self, operation, request, **kwargs):
        if self.delay:
            QtTest.QTest.qWait(int(self.delay))
        return self.content, self.data
