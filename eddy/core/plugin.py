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


from abc import ABCMeta, abstractmethod

from PyQt5.QtCore import QObject, pyqtSignal

from eddy.core.common import HasActionSystem, HasMenuSystem, HasWidgetSystem
from eddy.core.output import getLogger


LOGGER = getLogger(__name__)


class AbstractPlugin(QObject, HasActionSystem, HasMenuSystem, HasWidgetSystem):
    """
    Extension QObject which implements a plugin.
    Additionally to built-in signals, this class emits:

    * sgnStarted(str): whenever the plugin complete its startup sequence.
    * sgnDisposed(str): whenever the plugin is destroyed.
    """
    __metaclass__ = ABCMeta

    sgnDisposed = pyqtSignal(str)
    sgnStarted = pyqtSignal(str)

    def __init__(self, session):
        """
        Initialize the plugin.
        :type session: session
        """
        super().__init__(session)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self):
        """
        Returns the reference to the active project.
        :rtype: Project
        """
        return self.session.project

    @property
    def session(self):
        """
        Returns the reference to the main session (alias for AbstractPlugin.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   INTERFACE
    #################################

    def dispose(self):
        """
        Executed whenever the plugin is going to be destroyed. Plugins overriding
        this method have to either emit the sgnDisposed signal their own or call
        the super method.
        """
        self.sgnDisposed.emit(self.objectName())

    @classmethod
    @abstractmethod
    def name(cls):
        """
        Returns the readable name of the plugin.
        :rtype: str
        """
        pass

    @abstractmethod
    def objectName(self):
        """
        Returns the system name of the plugin.
        :rtype: str
        """
        pass

    def startup(self):
        """
        Executed whenever the plugin is to be started, after all the plugins
        have been loaded. Plugins overriding this method have to either emit
        the sgnStarted signal their own or call the super method.
        """
        self.sgnStarted.emit(self.objectName())

    @classmethod
    def requirements(cls):
        """
        Returns a list of plugins that are required by this one in order to work.
        :rtype: list
        """
        return []

    @classmethod
    def subclasses(cls):
        """
        Returns the list of subclasses subclassing this very class.
        :rtype: list
        """
        return cls.__subclasses__() + [c for i in cls.__subclasses__() for c in i.subclasses()]

    @classmethod
    @abstractmethod
    def version(cls):
        """
        Returns the version of the plugin.
        :rtype: NormalizedVersion
        """
        pass

    #############################################
    #   LOGGING CAPABILITIES
    #################################

    def critical(self, message, *args, **kwargs):
        """
        Log a 'CRITICAL' message.
        To pass exception information, use the keyword argument 'exc_info=True'.
        :type message: str
        """
        LOGGER.critical('{0}: {1}'.format(self.name(), message), *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        """
        Log a 'DEBUG' message.
        To pass exception information, use the keyword argument 'exc_info=True'.
        :type message: str
        """
        LOGGER.debug('{0}: {1}'.format(self.name(), message), *args, **kwargs)

    def error(self, message, *args, **kwargs):
        """
        Log a 'ERROR' message.
        To pass exception information, use the keyword argument 'exc_info=True'.
        :type message: str
        """
        LOGGER.error('{0}: {1}'.format(self.name(), message), *args, **kwargs)

    def info(self, message, *args, **kwargs):
        """
        Log a 'INFO' message.
        To pass exception information, use the keyword argument 'exc_info=True'.
        :type message: str
        """
        LOGGER.info('{0}: {1}'.format(self.name(), message), *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        """
        Log a 'WARNING' message.
        To pass exception information, use the keyword argument 'exc_info=True'.
        :type message: str
        """
        LOGGER.warning('{0}: {1}'.format(self.name(), message), *args, **kwargs)