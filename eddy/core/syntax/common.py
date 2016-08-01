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


class SyntaxValidationResult(object):
    """
    This class can be used to store syntax validation results.
    """
    def __init__(self, source, edge, target, valid):
        """
        Initialize the syntax validation result.
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
        Returns the edgeof the validated triple.
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


class AbstractValidator(QObject):
    """
    Base syntax validator class.
    This class defines the base structure of syntax validators and enforce the implementation
    of the 'run' method which is responsible of validation graphol triples: NODE -> EDGE -> NODE.
    """
    __metaclass__ = ABCMeta

    def __init__(self, parent=None):
        """
        Initialize the validator.
        :type parent: QObject
        """
        self._result = None
        super().__init__(parent)

    #############################################
    #   INTERFACE
    #################################

    def clear(self):
        """
        Clear the validator by removing the latest validation result.
        """
        self._result = None

    def result(self):
        """
        Returns the last validation result entry.
        :rtype: SyntaxValidationResult
        """
        return self._result

    @abstractmethod
    def run(self, source, edge, target):
        """
        Run the validation algorithm on the given triple and generates the result instance.
        :type source: AbstractNode
        :type edge: AbstractEdge
        :type target: AbstractNode
        """
        pass

    def setResult(self, result):
        """
        Sets the validation result entry.
        :type result: SyntaxValidationResult
        """
        self._result = result

    def validate(self, source, edge, target):
        """
        Returns the result of the validation for the given triple.
        :type source: AbstractNode
        :type edge: AbstractEdge
        :type target: AbstractNode
        :rtype: SyntaxValidationResult
        """
        if not self._result or (source, edge, target) not in self._result:
            self.run(source, edge, target)
        return self._result