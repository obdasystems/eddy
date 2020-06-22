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


from eddy.core.datatypes.owl import OWLProfile
from eddy.core.profiles.common import AbstractProfile

from eddy.core.profiles.rules.owl2 import EquivalenceBetweenExpressionsRule, InputToHasKeyNodeRule
from eddy.core.profiles.rules.owl2 import EquivalenceBetweenCompatibleExpressionsRule
from eddy.core.profiles.rules.owl2 import EquivalenceBetweenValueDomainExpressionsRule
from eddy.core.profiles.rules.owl2 import EquivalenceBetweenRoleExpressionAndComplementRule
from eddy.core.profiles.rules.owl2 import EquivalenceBetweenAttributeExpressionAndComplementRule
from eddy.core.profiles.rules.owl2 import EquivalenceBetweenRoleExpressionAndRoleChainRule
from eddy.core.profiles.rules.owl2 import InclusionBetweenExpressionsRule
from eddy.core.profiles.rules.owl2 import InclusionBetweenCompatibleExpressionsRule
from eddy.core.profiles.rules.owl2 import InclusionBetweenValueDomainExpressionsRule
from eddy.core.profiles.rules.owl2 import InclusionBetweenRoleExpressionAndComplementNodeRule
from eddy.core.profiles.rules.owl2 import InclusionBetweenAttributeExpressionAndComplementNodeRule
from eddy.core.profiles.rules.owl2 import InclusionBetweenRoleExpressionAndRoleChainNodeRule
from eddy.core.profiles.rules.owl2 import InputToConstructorNodeRule
from eddy.core.profiles.rules.owl2 import InputToComplementNodeRule
from eddy.core.profiles.rules.owl2 import InputToIntersectionOrUnionNodeRule
from eddy.core.profiles.rules.owl2 import InputToEnumerationNodeRule
from eddy.core.profiles.rules.owl2 import InputToRoleInverseNodeRule
from eddy.core.profiles.rules.owl2 import InputToRoleChainNodeRule
from eddy.core.profiles.rules.owl2 import InputToDatatypeRestrictionNodeRule
from eddy.core.profiles.rules.owl2 import InputToPropertyAssertionNodeRule
from eddy.core.profiles.rules.owl2 import InputToDomainRestrictionNodeRule
from eddy.core.profiles.rules.owl2 import InputToRangeRestrictionNodeRule
from eddy.core.profiles.rules.owl2 import InputToFacetNodeRule
from eddy.core.profiles.rules.owl2 import MembershipFromAssertionCompatibleNodeRule
from eddy.core.profiles.rules.owl2 import MembershipFromIndividualRule
from eddy.core.profiles.rules.owl2 import MembershipFromRoleInstanceRule
from eddy.core.profiles.rules.owl2 import MembershipFromAttributeInstanceRule
from eddy.core.profiles.rules.owl2 import MembershipFromNeutralPropertyAssertionRule
from eddy.core.profiles.rules.owl2 import SameFromCompatibleNodeRule
from eddy.core.profiles.rules.owl2 import DifferentFromCompatibleNodeRule
from eddy.core.profiles.rules.owl2 import SelfConnectionRule
from eddy.core.profiles.rules.owl2 import CardinalityRestrictionNodeRule
from eddy.core.profiles.rules.owl2 import UnknownIdentityNodeRule


class OWL2Profile(AbstractProfile):
    """
    Extends AbstractProfile implementing the OWL 2 (full) profile.
    """
    def __init__(self, project=None):
        """
        Initialize the profile.
        :type project: Project
        """
        super().__init__(project)
        self.addNodeRule(CardinalityRestrictionNodeRule)
        self.addNodeRule(UnknownIdentityNodeRule)
        self.addEdgeRule(SelfConnectionRule)
        self.addEdgeRule(EquivalenceBetweenExpressionsRule)
        self.addEdgeRule(EquivalenceBetweenCompatibleExpressionsRule)
        self.addEdgeRule(EquivalenceBetweenValueDomainExpressionsRule)
        self.addEdgeRule(EquivalenceBetweenRoleExpressionAndComplementRule)
        self.addEdgeRule(EquivalenceBetweenAttributeExpressionAndComplementRule)
        self.addEdgeRule(EquivalenceBetweenRoleExpressionAndRoleChainRule)
        self.addEdgeRule(InclusionBetweenExpressionsRule)
        self.addEdgeRule(InclusionBetweenCompatibleExpressionsRule)
        self.addEdgeRule(InclusionBetweenValueDomainExpressionsRule)
        self.addEdgeRule(InclusionBetweenRoleExpressionAndComplementNodeRule)
        self.addEdgeRule(InclusionBetweenAttributeExpressionAndComplementNodeRule)
        self.addEdgeRule(InclusionBetweenRoleExpressionAndRoleChainNodeRule)
        self.addEdgeRule(InputToConstructorNodeRule)
        self.addEdgeRule(InputToComplementNodeRule)
        self.addEdgeRule(InputToIntersectionOrUnionNodeRule)
        self.addEdgeRule(InputToEnumerationNodeRule)
        self.addEdgeRule(InputToRoleInverseNodeRule)
        self.addEdgeRule(InputToRoleChainNodeRule)
        self.addEdgeRule(InputToDatatypeRestrictionNodeRule)
        self.addEdgeRule(InputToPropertyAssertionNodeRule)
        self.addEdgeRule(InputToDomainRestrictionNodeRule)
        self.addEdgeRule(InputToRangeRestrictionNodeRule)
        self.addEdgeRule(InputToFacetNodeRule)
        self.addEdgeRule(MembershipFromAssertionCompatibleNodeRule)
        self.addEdgeRule(MembershipFromIndividualRule)
        self.addEdgeRule(MembershipFromRoleInstanceRule)
        self.addEdgeRule(MembershipFromAttributeInstanceRule)
        self.addEdgeRule(MembershipFromNeutralPropertyAssertionRule)
        self.addEdgeRule(SameFromCompatibleNodeRule)
        self.addEdgeRule(DifferentFromCompatibleNodeRule)
        self.addEdgeRule(InputToHasKeyNodeRule)

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def type(cls):
        """
        Returns the profile type.
        :rtype: OWLProfile
        """
        return OWLProfile.OWL2
