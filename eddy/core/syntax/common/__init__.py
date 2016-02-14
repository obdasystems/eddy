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


from abc import ABCMeta, abstractmethod

from PyQt5.QtCore import QObject


class ValidationResult(object):
    """
    This class can be used to store validation results.
    """
    def __init__(self, source, edge, target, valid, message=''):
        """
        Initialize the validation result.
        :type source: AbstractNode
        :type edge: AbstractEdge
        :type target: AbstractNode
        :type valid: bool
        :type message: str
        """
        self.source = source
        self.edge = edge
        self.target = target
        self.message = message
        self.valid = valid

    def __contains__(self, item):
        """
        Implement membership operator 'in'.
        :type item: tuple
        :rtype: bool
        """
        try:
            return self.source is item[0] and self.edge is item[1] and self.target is item[2]
        except IndexError:
            return False


class AbstractValidator(QObject):
    """
    Base syntax validator class.
    This class defines the base structure of syntax validators and enforce the implementation
    of the 'run' method which is responsible of validation Graphol triples: NODE -> EDGE -> NODE.
    The method MUST generate the ValidationResult instance that can later be queried using the validator interface.
    """
    __metaclass__ = ABCMeta

    def __init__(self, parent=None):
        """
        Initialize the validator.
        :type parent:  QObject
        """
        super().__init__(parent)
        self._result = None

    ####################################################################################################################
    #                                                                                                                  #
    #   INTERFACE                                                                                                      #
    #                                                                                                                  #
    ####################################################################################################################

    def clear(self):
        """
        Clear the validator by removing the latest validation result.
        """
        self._result = None

    def result(self, source, edge, target):
        """
        Returns the validation result for the given triple.
        :type source: AbstractNode
        :type edge: AbstractEdge
        :type target: AbstractNode
        :rtype: ValidationResult
        """
        if not self._result or (source, edge, target) not in self._result:
            self.run(source, edge, target)
        return self._result

    @abstractmethod
    def run(self, source, edge, target):
        """
        Run the validation algorithm on the given triple and generates the ValidationResult instance.
        :type source: AbstractNode
        :type edge: AbstractEdge
        :type target: AbstractNode
        """
        pass

    def valid(self, source, edge, target):
        """
        Tells whether the given triple is a valid one.
        :type source: AbstractNode
        :type edge: AbstractEdge
        :type target: AbstractNode
        :rtype: bool
        """
        if not self._result or (source, edge, target) not in self._result:
            self.run(source, edge, target)
        return self._result.valid