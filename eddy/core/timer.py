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


from PyQt5 import QtCore

from eddy.core.functions.signals import connect


class PausableTimer(QtCore.QTimer):
    """
    Extends QtCore.QTimer providing pause and resume functionalities.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the timer.
        """
        self._remaining = 0
        self._paused = False
        super().__init__(*args, **kwargs)
        connect(self.timeout, self.onTimeout)

    #############################################
    #   SLOTS
    #################################

    @QtCore.pyqtSlot()
    def onTimeout(self):
        """
        Executed when the timer expires.
        """
        self._paused = False

    #############################################
    #   INTERFACE
    #################################

    def isPaused(self):
        """
        Tells whether is timer is paused.
        :rtype: bool
        """
        return self._paused

    def pause(self):
        """
        Pause the timer.
        """
        if self.isActive():
            self._paused = True
            self._remaining = self.remainingTime()
            self.stop()

    def resume(self):
        """
        Resume a paused timer.
        """
        if not self.isActive():
            self._paused = False
            self.start(self._remaining)

    def reset(self):
        """
        Reset the timer.
        """
        self._paused = False
        self._remaining = 0
        if self.isActive():
            self.stop()

    def start(self, *args, **kwargs):
        """
        Start the timer.
        """
        super().start(*args, **kwargs)