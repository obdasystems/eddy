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

from PyQt5.QtCore import QObject


class AbstractProfile(QObject):
    """
    Extends QObject providing the base class for all the ontology profiles.
    """
    __metaclass__ = ABCMeta

    def __init__(self, project):
        """
        Initialize the profile.
        :type project: Project
        """
        super().__init__(project)
        self._pvr = None

    #############################################
    #   PROPERTIES
    #################################

    @property
    def project(self):
        """
        Returns the reference to the active project (alias for AbstractProfile.parent()).
        :rtype: Project
        """
        return self.parent()

    @property
    def session(self):
        """
        Returns the reference to the active session (alias for AbstractProfile.project.parent()).
        :rtype: Session
        """
        return self.project.parent()

    #############################################
    #   INTERFACE
    #################################

    def check(self, source, edge, target):
        """
        Perform the validation of the given triple according to the current profile (if necessary).
        :param source: AbstractNode
        :param edge: AbstractEdge
        :param target: AbstractNode
        :rtype: ProfileValidationResult
        """
        if not self.pvr() or (source, edge, target) not in self.pvr():
            self.validate(source, edge, target)
        return self.pvr()

    @classmethod
    @abstractmethod
    def name(cls):
        """
        Returns the name of the profile, i.e: OWL2, OWL2EL, OWL2QL, OWL2RL.
        :rtype: str
        """
        pass

    def objectName(self):
        """
        Returns the system name of the plugin.
        :rtype: str
        """
        return self.name()

    def pvr(self):
        """
        Returns the last profile validation result.
        :rtype: ProfileValidationResult
        """
        return self._pvr

    def reset(self):
        """
        Resets the profile in all its aspects.
        """
        self._pvr = None

    def setPvr(self, pvr):
        """
        Set the profile validation result.
        :type pvr: ProfileValidationResult
        """
        self._pvr = pvr

    @abstractmethod
    def validate(self, source, edge, target):
        """
        Perform the validation of the given triple and generate the ProfileValidationResult.
        :param source: AbstractNode
        :param edge: AbstractEdge
        :param target: AbstractNode
        """
        pass


class ProfileValidationResult(object):
    """
    This class can be used to store profile validation results.
    """
    def __init__(self, source, edge, target, valid):
        """
        Initialize the profile validation result.
        :type source: AbstractNode
        :type edge: AbstractEdge
        :type target: AbstractNode
        :type valid: bool
        """
        self._edge = edge
        self._source = source
        self._target = target
        self._valid = valid
        self._message = ''

    def edge(self):
        """
        Returns the edge of the validated triple.
        :rtype: AbstractEdge
        """
        return self._edge

    def isValid(self):
        """
        Tells whether the result is valid.
        :rtype: bool
        """
        return self._valid

    def message(self):
        """
        Returns the message used as result for the validated triple.
        :rtype: str
        """
        return self._message or ''

    def setMessage(self, message):
        """
        Sets the message used as result for the validated triple.
        :type: str
        """
        self._message = message

    def source(self):
        """
        Returns the source node of the validated triple.
        :rtype: AbstractNode
        """
        return self._source

    def target(self):
        """
        Returns the target node of the validated triple.
        :rtype: AbstractNode
        """
        return self._target

    def __contains__(self, item):
        """
        Implement membership operator 'in'.
        :type item: tuple
        :rtype: bool
        """
        try:
            return self._source is item[0] and self._edge is item[1] and self._target is item[2]
        except IndexError:
            return False