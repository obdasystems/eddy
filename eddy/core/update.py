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


from github3 import GitHub
from verlib import IrrationalVersionError, NormalizedVersion

from PyQt5 import QtCore

from eddy.core.datatypes.system import Channel
from eddy.core.output import getLogger
from eddy.core.worker import AbstractWorker


LOGGER = getLogger(__name__)


class UpdateCheckWorker(AbstractWorker):
    """
    Extends AbstractWorker providing a worker that will check for new software updates.
    """
    sgnNoUpdateAvailable = QtCore.pyqtSignal()
    sgnNoUpdateDataAvailable = QtCore.pyqtSignal()
    sgnUpdateAvailable = QtCore.pyqtSignal(str, str)

    def __init__(self, channel, current):
        """
        Initialize the syntax validation worker.
        :type channel: Channel
        :type current: str
        """
        super(UpdateCheckWorker, self).__init__()
        self.channel = channel # Current update channel
        self.current = current # Eddy current version

    @QtCore.pyqtSlot()
    def run(self):
        """
        Main worker.
        """
        update_name = None  # Store update name, i.e: Eddy v0.9.1
        update_version = self.current  # Store update version, i.e: 0.9.1
        update_url = None  # Store update HTML url, i.e: http://github.com/...
        try:
            LOGGER.info('Connecting to GitHub to retrieve update information (channel: %s)', self.channel.value)
            github = GitHub(token='6a417ccfe9a7c526598e77a74cbf1cba6e688f0e')
            repository = github.repository('danielepantaleone', 'eddy')
            for release in repository.releases():
                if self.channel is Channel.Beta or not release.prerelease:
                    try:
                        if NormalizedVersion(release.tag_name[1:]) > NormalizedVersion(update_version):
                            update_name = release.name
                            update_version = release.tag_name[1:]
                            update_url = release.html_url
                    except IrrationalVersionError as e:
                        LOGGER.warning('Failed to parse version number from TAG: %s', e)
            if update_version != self.current:
                LOGGER.info('Update available: %s', update_name)
                self.sgnUpdateAvailable.emit(update_name, update_url)
            else:
                LOGGER.info('No update available')
                self.sgnNoUpdateAvailable.emit()
        except Exception as e:
            LOGGER.warning('Failed to retrieve update data: %s', e)
            self.sgnNoUpdateDataAvailable.emit()
        self.finished.emit()