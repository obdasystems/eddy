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
from eddy.core.profiles.owl2 import OWL2Profile

from eddy.core.profiles.rules.owl2ql import EquivalenceBetweenConceptExpressionRule
from eddy.core.profiles.rules.owl2ql import InclusionBetweenConceptExpressionRule
from eddy.core.profiles.rules.owl2ql import InputConceptToRestrictionNodeRule
from eddy.core.profiles.rules.owl2ql import InputValueDomainToComplementNodeRule
from eddy.core.profiles.rules.owl2ql import InputValueDomainToIntersectionNodeRule
from eddy.core.profiles.rules.owl2ql import MembershipFromAttributeInstanceToComplementNodeRule
from eddy.core.profiles.rules.owl2ql import MembershipFromRoleInstanceToComplementNodeRule
from eddy.core.profiles.rules.owl2ql import MembershipFromPropertyAssertionToComplementNodeRule
from eddy.core.profiles.rules.owl2ql import UnsupportedDatatypeRule
from eddy.core.profiles.rules.owl2ql import UnsupportedOperatorRule
from eddy.core.profiles.rules.owl2ql import UnsupportedIndividualEqualityRule
from eddy.core.profiles.rules.owl2ql import FunctionalityUnsupported
from eddy.core.profiles.rules.owl2ql import InverseFunctionalityUnsupported
from eddy.core.profiles.rules.owl2ql import TransitivityUnsupported

class OWL2QLProfile(OWL2Profile):
    """
    Extends OWL2Profile implementing the OWL 2 QL profile.
    """
    def __init__(self, project=None):
        """
        Initialize the profile.
        :type project: Project
        """
        super().__init__(project)
        self.addNodeRule(UnsupportedDatatypeRule)
        self.addNodeRule(UnsupportedOperatorRule)
        self.addEdgeRule(UnsupportedIndividualEqualityRule)
        self.addNodeRule(FunctionalityUnsupported)
        self.addNodeRule(InverseFunctionalityUnsupported)
        self.addNodeRule(TransitivityUnsupported)
        self.addEdgeRule(EquivalenceBetweenConceptExpressionRule)
        self.addEdgeRule(InclusionBetweenConceptExpressionRule)
        self.addEdgeRule(InputConceptToRestrictionNodeRule)
        self.addEdgeRule(InputValueDomainToComplementNodeRule)
        self.addEdgeRule(InputValueDomainToIntersectionNodeRule)
        self.addEdgeRule(MembershipFromAttributeInstanceToComplementNodeRule)
        self.addEdgeRule(MembershipFromRoleInstanceToComplementNodeRule)
        self.addEdgeRule(MembershipFromPropertyAssertionToComplementNodeRule)

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def type(cls):
        """
        Returns the profile type.
        :rtype: OWLProfile
        """
        return OWLProfile.OWL2QL
