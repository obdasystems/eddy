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


import json

from PyQt5 import (
    QtCore,
    QtNetwork,
)

from eddy import VERSION
from eddy.core.datatypes.qt import VersionNumber
from eddy.core.datatypes.system import Channel
from eddy.core.functions.signals import connect
from eddy.core.output import getLogger

LOGGER = getLogger()


class NetworkManager(QtNetwork.QNetworkAccessManager):
    """
    Subclass of QNetworkAccessManager that provides extra functionalities such as checking for updates.
    Additionally to built-in signals, this class emits:
    * sgnNoUpdateAvailable: whenever there is no update available.
    * sgnNoUpdateDataAvailable: whenever update information cannot be retrieved.
    * sgnUpdateAvailable: whenever there is an update available.
    """
    sgnNoUpdateAvailable = QtCore.pyqtSignal()
    sgnNoUpdateDataAvailable = QtCore.pyqtSignal()
    sgnUpdateAvailable = QtCore.pyqtSignal(str, str)
    ChannelAttribute = QtNetwork.QNetworkRequest.Attribute(2001)
    VersionAttribute = QtNetwork.QNetworkRequest.Attribute(2002)
    UpdateUrl = 'https://api.github.com/repos/obdasystems/eddy/releases'

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onCheckForUpdateFinished(self):
        """
        Executed when a check for update request completes.
        """
        reply = self.sender()
        try:
            reply.deleteLater()
            if reply.isFinished() and reply.error() == QtNetwork.QNetworkReply.NoError:
                channel = reply.request().attribute(NetworkManager.ChannelAttribute)
                version = reply.request().attribute(NetworkManager.VersionAttribute)
                current_version = VersionNumber.fromString(version)
                update_name = None  # Store update name
                update_version = current_version # Store update version
                update_url = None  # Store update HTML url
                releases = json.loads(str(reply.readAll(), encoding='utf-8'))
                for release in releases:
                    if channel is Channel.Beta or not bool(release.get('prerelease')):
                        tag_name = release.get('tag_name', '')
                        tag_name = tag_name[1:] if tag_name.startswith('v') else tag_name
                        tag_version = VersionNumber.fromString(tag_name)
                        if tag_version > update_version:
                            update_name = release.get('name')
                            update_version = tag_version
                            update_url = release.get('html_url')
                if update_version != current_version:
                    LOGGER.info('Update available: %s', update_name)
                    self.sgnUpdateAvailable.emit(update_name, update_url)
                else:
                    LOGGER.info('No update available')
                    self.sgnNoUpdateAvailable.emit()
            else:
                LOGGER.warning('Failed to retrieve update data: %s', reply.errorString())
                self.sgnNoUpdateDataAvailable.emit()
        except Exception as e:
            LOGGER.warning('Failed to retrieve update data: %s', e)
            self.sgnNoUpdateDataAvailable.emit()

    #############################################
    #   INTERFACE
    #################################

    def checkForUpdate(self, channel=Channel.Stable, version=VERSION):
        """
        Start an update check for the specified channel and application version.
        :type channel: Channel
        :type version: str
        """
        LOGGER.info('Connecting to GitHub to retrieve update information (channel: %s)', channel.value)
        url = QtCore.QUrl(NetworkManager.UpdateUrl)
        request = QtNetwork.QNetworkRequest(url)
        # See: https://developer.github.com/v3/#current-version
        request.setRawHeader(b'Accept', b'application/vnd.github.v3+json')
        request.setAttribute(QtNetwork.QNetworkRequest.FollowRedirectsAttribute, True)
        request.setAttribute(NetworkManager.ChannelAttribute, channel)
        request.setAttribute(NetworkManager.VersionAttribute, version)
        reply = self.get(request)
        connect(reply.finished, self.onCheckForUpdateFinished)
        # TIMEOUT AFTER 10 SECONDS
        QtCore.QTimer.singleShot(10000, reply.abort)

    def getSync(self, url, timeout=10000):
        """
        Perform a synchronous HTTP GET request, returning the resulting code and content.
        :type url: str | QtCore.QUrl
        :type timeout: int
        :rtype: tuple
        """
        loop = QtCore.QEventLoop(self)
        timer = QtCore.QTimer(self)
        timer.setSingleShot(True)
        url = QtCore.QUrl(url)
        request = QtNetwork.QNetworkRequest(url)
        request.setAttribute(QtNetwork.QNetworkRequest.FollowRedirectsAttribute, True)
        reply = self.get(request)
        connect(reply.finished, loop.quit)
        connect(timer.timeout, loop.quit)
        timer.start(timeout)
        loop.exec_()
        reply.deleteLater()
        status = reply.attribute(QtNetwork.QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if reply.isFinished() and reply.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
            response = str(reply.readAll(), encoding='utf-8')
            return status, response
        elif timer.remainingTime() <= 0:
            return status, 'Operation timed out'
        else:
            return status, reply.errorString()
