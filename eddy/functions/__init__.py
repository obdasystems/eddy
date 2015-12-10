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


from eddy.functions.fsystem import getHomePath
from eddy.functions.fsystem import getModulePath
from eddy.functions.fsystem import getPath

from eddy.functions.geometry import angleP
from eddy.functions.geometry import distanceL
from eddy.functions.geometry import distanceP
from eddy.functions.geometry import intersectionL
from eddy.functions.geometry import midpoint

from eddy.functions.graph import bfs
from eddy.functions.graph import identify

from eddy.functions.misc import clamp
from eddy.functions.misc import isEmpty
from eddy.functions.misc import isQuoted
from eddy.functions.misc import make_colored_icon
from eddy.functions.misc import make_shaded_icon
from eddy.functions.misc import QSS
from eddy.functions.misc import partition
from eddy.functions.misc import rangeF
from eddy.functions.misc import shaded
from eddy.functions.misc import snapF

from eddy.functions.signals import connect
from eddy.functions.signals import disconnect