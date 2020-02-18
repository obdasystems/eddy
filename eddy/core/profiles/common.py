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

from eddy.core.profiles.rules.common import ProfileEdgeRule
from eddy.core.profiles.rules.common import ProfileNodeRule


class AbstractProfile(QtCore.QObject):
    """
    Extends QObject providing the base class for all the ontology profiles.
    """
    __metaclass__ = ABCMeta

    def __init__(self, project=None):
        """
        Initialize the profile.
        :type project: Project
        """
        super().__init__(project)
        self._edgeRules = []
        self._nodeRules = []
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

    def addEdgeRule(self, rule, *args, **kwargs):
        """
        Add an edge validation rule to this Profile.
        :type rule: class
        """
        if issubclass(rule, ProfileEdgeRule):
            self._edgeRules.append(rule(*args, **kwargs))

    def addNodeRule(self, rule, *args, **kwargs):
        """
        Add a node validation rule to this Profile.
        :type rule: class
        """
        if issubclass(rule, ProfileNodeRule):
            self._nodeRules.append(rule(*args, **kwargs))

    def checkEdge(self, source, edge, target):
        """
        Perform the validation of the given triple (source -> edge -> target):
        *   1) Perform the validation on the source node.
        *   2) Perform the validation on the target node.
        *   3) Perform the validation on the given edge.
        :type source: AbstractNode
        :type edge: AbstractEdge
        :type target: AbstractNode
        :rtype: AbstractProfileValidationResult
        """
        if not self.pvr() or (source, edge, target) not in self.pvr():

            try:
                for node in (source, target):
                    for r in self.nodeRules():
                        r(node)
                for r in self.edgeRules():
                    r(source, edge, target)
            except ProfileError as e:
                print(e.msg)
                self.setPvr(ProfileValidationResult((source, edge, target), False, e.msg))
            else:
                self.setPvr(ProfileValidationResult((source, edge, target), True))

        return self.pvr()

    def checkNode(self, node):
        """
        Perform the validation of the given node.
        :type node: AbstractNode
        :rtype: ProfileValidationResult
        """
        if not self.pvr() or node not in self.pvr():

            try:
                for r in self.nodeRules():
                    r(node)
            except ProfileError as e:
                self.setPvr(ProfileValidationResult(node, False, e.msg))
            else:
                self.setPvr(ProfileValidationResult(node, True))

        return self.pvr()

    def edgeRules(self):
        """
        Returns the list of edge rules in this Profile.
        :rtype: list
        """
        return self._edgeRules

    @classmethod
    def name(cls):
        """
        Returns the name of the profile, i.e: OWL 2, OWL 2 EL, OWL 2 QL, OWL 2 RL.
        :rtype: str
        """
        profile = cls.type()
        return profile.value

    def nodeRules(self):
        """
        Returns the list of node rules in this Profile.
        :rtype: list
        """
        return self._nodeRules

    def objectName(self):
        """
        Returns the system name of the profile.
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
        Reset the profile by removing the latest validation result.
        """
        self._pvr = None

    def setPvr(self, pvr):
        """
        Set the profile validation result.
        :type pvr: ProfileValidationResult
        """
        self._pvr = pvr

    @classmethod
    @abstractmethod
    def type(cls):
        """
        Returns the profile type.
        :rtype: OWLProfile
        """
        pass


class ProfileValidationResult(object):
    """
    This class can be used to store profile validation results.
    """
    def __init__(self, item, valid, message=''):
        """
        Initialize the profile validation result.
        :type item: T <= tuple|AbstractNode
        :type valid: bool
        :type message: str
        """
        self._item = item
        self._valid = valid
        self._message = message

    def item(self):
        """
        Returns the item (or set of items) being validated.
        :rtype: T <= tuple|AbstractNode
        """
        return self._item

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

    def __contains__(self, item):
        """
        Implement membership operator 'in'.
        :type item: T <= tuple|AbstractNode
        :rtype: bool
        """
        try:
            return self._item[0] is item[0] and self._item[1] is item[1] and self._item[2] is item[2]
        except (TypeError, IndexError):
            return self._item is item


class ProfileError(SyntaxError):
    """
    Extends SyntaxError and denotes Profile constraint violations.
    """
    pass