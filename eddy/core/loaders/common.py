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


from abc import ABCMeta, abstractmethod

from PyQt5 import QtCore


class AbstractLoader(QtCore.QObject):
    """
    Extends QObject providing the base class for all the loaders.
    """
    __metaclass__ = ABCMeta

    def __init__(self, path, session):
        """
        Initialize the AbstractLoader.
        :type path: str
        :type session: Session
        """
        super().__init__(session)
        self.path = path

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the active session (alias for AbstractLoader.parent()).
        :rtype: Session
        """
        return self.parent()

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    @abstractmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        pass

    @abstractmethod
    def run(self):
        """
        Perform the load.
        """
        pass


class AbstractDiagramLoader(AbstractLoader):
    """
    Extends AbstractLoader providing the base class for all the Diagram loaders.
    """
    __metaclass__ = ABCMeta

    def __init__(self, path, project, session):
        """
        Initialize the AbstractDiagramLoader.
        :type path: str
        :type project: Project
        :type session: Session
        """
        super().__init__(path, session)
        self.project = project

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    @abstractmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        pass

    @abstractmethod
    def run(self):
        """
        Perform the load of the diagram and add it to the project.
        """
        pass


class AbstractOntologyLoader(AbstractLoader):
    """
    Extends AbstractLoader providing the base class for all the Ontology loaders.
    """
    __metaclass__ = ABCMeta

    def __init__(self, path, project, session):
        """
        Initialize the AbstractOntologyLoader.
        :type path: str
        :type project: Project
        :type session: Session
        """
        super().__init__(path, session)
        self.project = project

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    @abstractmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        pass

    @abstractmethod
    def run(self):
        """
        Perform the load of the ontology and the merge with the current project.
        """
        pass


class AbstractProjectLoader(AbstractLoader):
    """
    Extends AbstractLoader providing the base class for all the Project loaders.
    """
    __metaclass__ = ABCMeta

    def __init__(self, path, session):
        """
        Initialize the AbstractProjectLoader.
        :type path: str
        :type session: Session
        """
        super().__init__(path, session)

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    @abstractmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the import.
        :return: File
        """
        pass

    @abstractmethod
    def run(self):
        """
        Perform the load of the project and set is as Session project
        """
        pass
