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


class AbstractExporter(QtCore.QObject):
    """
    Extends QObject providing the base class for all the exporters.
    """
    __metaclass__ = ABCMeta

    def __init__(self, session):
        """
        Initialize the AbstractExporter.
        :type session: Session
        """
        super().__init__(session)

    #############################################
    #   PROPERTIES
    #################################

    @property
    def session(self):
        """
        Returns the active session (alias for AbstractExporter.parent()).
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
        Returns the type of the file that will be used for the export.
        :rtype: File
        """
        pass

    @abstractmethod
    def run(self, path):
        """
        Perform the export.
        :type path: str
        """
        pass


class AbstractDiagramExporter(AbstractExporter):
    """
    Extends AbstractExporter providing the base class for all the Diagram exporters.
    """
    __metaclass__ = ABCMeta

    def __init__(self, diagram, session):
        """
        Initialize the AbstractDiagramExporter.
        :type diagram: Diagram
        :type session: Session
        """
        super().__init__(session)
        self.diagram = diagram

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    @abstractmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        :rtype: File
        """
        pass

    @abstractmethod
    def run(self, path):
        """
        Perform the export.
        :type path: str
        """
        pass


class AbstractOntologyExporter(AbstractExporter):
    """
    Extends AbstractExporter providing the base class for all the Ontology exporters.
    """
    __metaclass__ = ABCMeta

    def __init__(self, project, session):
        """
        Initialize the AbstractOntologyExporter.
        :type project: Project
        :type session: Session
        """
        super().__init__(session)
        self.project = project

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    @abstractmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        :rtype: File
        """
        pass

    @abstractmethod
    def run(self, path):
        """
        Perform the export.
        :type path: str
        """
        pass


class AbstractProjectExporter(AbstractExporter):
    """
    Extends AbstractExporter providing the base class for all the Project exporters.
    """
    __metaclass__ = ABCMeta

    def __init__(self, project, session, exportPath=None, selectDiagrams=False):
        """
        Initialize the AbstractProjectExporter.
        :type project: Project
        :type session: Session
        """
        super().__init__(session)
        self.project = project
        self.exportPath = exportPath
        self.selectDiagrams = selectDiagrams

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    @abstractmethod
    def filetype(cls):
        """
        Returns the type of the file that will be used for the export.
        :rtype: File
        """
        pass

    @abstractmethod
    def run(self, path):
        """
        Perform the export.
        :type path: str
        """
        pass
