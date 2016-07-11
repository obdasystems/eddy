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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


from abc import ABCMeta, abstractmethod

from PyQt5.QtCore import QObject


class SyntaxValidationResult(object):
    """
    This class can be used to store syntax validation results.
    """
    def __init__(self, source, edge, target, valid, message=''):
        """
        Initialize the syntax validation result.
        :type source: AbstractNode
        :type edge: AbstractEdge
        :type target: AbstractNode
        :type valid: bool
        :type message: str
        """
        self.edge = edge
        self.source = source
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
    of the 'run' method which is responsible of validation graphol triples: NODE -> EDGE -> NODE.
    """
    __metaclass__ = ABCMeta

    def __init__(self, parent=None):
        """
        Initialize the validator.
        :type parent: QObject
        """
        super().__init__(parent)
        self.result = None

    #############################################
    #   INTERFACE
    #################################

    def clear(self):
        """
        Clear the validator by removing the latest validation result.
        """
        self.result = None

    @abstractmethod
    def run(self, source, edge, target):
        """
        Run the validation algorithm on the given triple and generates the SyntaxValidationResult instance.
        :type source: AbstractNode
        :type edge: AbstractEdge
        :type target: AbstractNode
        """
        pass

    def validate(self, source, edge, target):
        """
        Returns the SyntaxValidationResult for the given triple.
        :type source: AbstractNode
        :type edge: AbstractEdge
        :type target: AbstractNode
        :rtype: SyntaxValidationResult
        """
        if not self.result or (source, edge, target) not in self.result:
            self.run(source, edge, target)
        return self.result