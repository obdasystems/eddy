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


from eddy.core.datatypes.graphol import Item, Identity, Special
from eddy.core.datatypes.owl import Datatype, OWLProfile
from eddy.core.functions.graph import bfs
from eddy.core.profiles.common import ProfileError
from eddy.core.profiles.rules.common import ProfileNodeRule
from eddy.core.profiles.rules.common import ProfileEdgeRule


class UnsupportedDatatypeRule(ProfileNodeRule):
    """
    Prevents from using datatypes which are outside of the OWL 2 RL profile.
    """
    def __call__(self, node):
        if node.type() is Item.ValueDomainNode:
            if node.datatype not in Datatype.forProfile(OWLProfile.OWL2RL):
                raise ProfileError('Datatype {} is forbidden in OWL 2 RL'.format(node.datatype.value))


class UnsupportedOperatorRule(ProfileNodeRule):
    """
    Prevents from using operator nodes which are not supported by the OWL 2 RL profile.
    """
    def __call__(self, node):
        if node.type() in {Item.DatatypeRestrictionNode, Item.FacetNode}:
            raise ProfileError('Usage of {} operator is forbidden in OWL 2 RL'.format(node.shortName))


class UnsupportedSpecialOnRoleAndAttributeNode(ProfileNodeRule):
    """
    Make sure that TOP and BOTTOM are not used in Role and Attribute nodes.
    """
    def __call__(self, node):
        if node.type() in {Item.AttributeNode, Item.RoleNode}:
            if Special.forValue(node.text()) is not None:
                raise ProfileError('Usage of {} {} is forbidden in OWL 2 RL'.format(node.text(), node.shortName))


class InputValueToEnumerationNodeRule(ProfileEdgeRule):
    """
    Prevent the construction of value-domain expression composed of a oneOf of values.
    """
    def __call__(self, source, edge, target):
        if edge.type() is Item.InputEdge:
            if target.type() is Item.EnumerationNode:
                if source.identity() is Identity.Value:
                    raise ProfileError('Enumeration of values is forbidden in OWL 2 RL')


class InputValueDomainToUnionNodeRule(ProfileEdgeRule):
    """
    Prevent the construction of union of value domain expressions.
    """
    def __call__(self, source, edge, target):
        if edge.type() is Item.InputEdge:
            if target.type() in {Item.DisjointUnionNode, Item.UnionNode}:
                if Identity.ValueDomain in {source.identity(), target.identity()}:
                    raise ProfileError('{} of value-domain expressions is forbidden in OWL 2 RL'.format(target.shortName.capitalize()))