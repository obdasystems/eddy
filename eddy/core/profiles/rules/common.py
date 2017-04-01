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


from abc import abstractmethod, ABCMeta


class ProfileRule(object):
    """
    Extends built-in object providing the base class for all the validation rules.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __call__(self, *args):
        """
        Run the validation rule.
        """
        pass


class ProfileEdgeRule(ProfileRule):
    """
    Extends built-in object providing the base class for all the edge validation rules.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __call__(self, source, edge, target):
        """
        Run the validation rule on the given triple.
        :type source: AbstractNode
        :type edge: AbstractEdge
        :type target: AbstractNode
        """
        pass


class ProfileNodeRule(ProfileRule):
    """
    Extends built-in object providing the base class for all the node validation rules.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __call__(self, node):
        """
        Run the validation rule on the given node.
        :type node: AbstractNode
        """
        pass