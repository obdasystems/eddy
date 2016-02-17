# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: an editor for the Graphol ontology language.                    #
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
##########################################################################
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


from eddy.core.commands.common import CommandComposeAxiom
from eddy.core.commands.common import CommandItemsMultiAdd
from eddy.core.commands.common import CommandItemsMultiRemove
from eddy.core.commands.common import CommandItemsTranslate
from eddy.core.commands.common import CommandRefactor
from eddy.core.commands.common import CommandSetProperty

from eddy.core.commands.edges import CommandEdgeAdd
from eddy.core.commands.edges import CommandEdgeAnchorMove
from eddy.core.commands.edges import CommandEdgeBreakpointAdd
from eddy.core.commands.edges import CommandEdgeBreakpointDel
from eddy.core.commands.edges import CommandEdgeBreakpointMove
from eddy.core.commands.edges import CommandEdgeInclusionToggleComplete
from eddy.core.commands.edges import CommandEdgeSwap

from eddy.core.commands.nodes import CommandNodeAdd
from eddy.core.commands.nodes import CommandNodeSetBrush
from eddy.core.commands.nodes import CommandNodeChangeInputOrder
from eddy.core.commands.nodes import CommandNodeOperatorSwitchTo
from eddy.core.commands.nodes import CommandNodeLabelChange
from eddy.core.commands.nodes import CommandNodeLabelMove
from eddy.core.commands.nodes import CommandNodeMove
from eddy.core.commands.nodes import CommandNodeRezize
from eddy.core.commands.nodes import CommandNodeChangeMeta
from eddy.core.commands.nodes import CommandNodeSetZValue

from eddy.core.commands.scene import CommandSceneResize