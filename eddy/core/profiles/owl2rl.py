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
from eddy.core.profiles.rules.owl2rl import UnsupportedDatatypeRule
from eddy.core.profiles.rules.owl2rl import UnsupportedOperatorRule
from eddy.core.profiles.rules.owl2rl import UnsupportedSpecialOnRoleAndAttributeNode
from eddy.core.profiles.rules.owl2rl import InclusionBetweenConceptExpressionRule
from eddy.core.profiles.rules.owl2rl import InputValueToEnumerationNodeRule
from eddy.core.profiles.rules.owl2rl import InputValueDomainToUnionNodeRule

from eddy.core.profiles.rules.owl2rl import ReflexivityUnsupported


class OWL2RLProfile(OWL2Profile):
    """
    Extends OWL2Profile implementing the OWL 2 RL profile.
    """
    def __init__(self, project=None):
        """
        Initialize the profile.
        :type project: Project
        """
        super().__init__(project)
        self.addNodeRule(UnsupportedDatatypeRule)
        self.addNodeRule(UnsupportedOperatorRule)
        self.addNodeRule(UnsupportedSpecialOnRoleAndAttributeNode)
        self.addEdgeRule(InclusionBetweenConceptExpressionRule)
        self.addEdgeRule(InputValueToEnumerationNodeRule)
        self.addEdgeRule(InputValueDomainToUnionNodeRule)

        self.addNodeRule(ReflexivityUnsupported)

    #############################################
    #   INTERFACE
    #################################

    @classmethod
    def type(cls):
        """
        Returns the profile type.
        :rtype: OWLProfile
        """
        return OWLProfile.OWL2RL
