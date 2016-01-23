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


import os

from eddy import expandPath
from eddy.core.exceptions import JVMNotFoundException


class LocalJVMFinder(object):
    """
    JVM Finder mixin implementation which offers a method to lookup the JVM locally (under Eddy's path).
    """
    def _get_from_local_path(self):
        """
        Lookup the JVM locally under Eddy's path.
        :raise JVMNotFoundException: if no JVM can be found under Eddy's path.
        :rtype: str
        """
        for directory in os.listdir(expandPath('@resources/')):

            # List unsupported JVMs.
            non_supported_jvm = {'cacao', 'jamvm'}

            # Search the shared library file.
            for root, _, files in os.walk(os.path.join(expandPath('@resources/'), directory)):
                if self._libfile in files:
                    # Found it: check for non supported JVMs.
                    candidate = os.path.split(root)[1]
                    if candidate in non_supported_jvm:
                        # Found unsupported JVM, so keep searching.
                        continue
                    return os.path.join(root, self._libfile)

        raise JVMNotFoundException("No JVM shared library file ({0}) found inside Eddy's path.".format(self._libfile))