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


import os
import sys


def getHomePath():
    """
    Returns the path to the eddy home directory.
    :rtype: str
    """
    homepath = os.path.normpath(os.path.expanduser('~/.eddy'))
    if not os.path.isdir(homepath):
        os.mkdir(homepath)
    return homepath


def getModulePath():
    """
    Returns the path to the eddy directory.
    :rtype: str
    """
    if hasattr(sys, 'frozen'):
        path = os.path.dirname(sys.executable)
    else:
        path = os.path.dirname(sys.modules['eddy'].__file__)
    return os.path.normpath(os.path.expanduser(path))


def getPath(path):
    """
    Return an absolute path by expanding the given relative one.
    The following tokens will be expanded:

        - @eddy => will be expanded to the eddy directory path
        - @home => will be expanded to the eddy home directory path (.eddy in $HOME)
        - ~ => will be expanded to the user home directory ($HOME)

    :type path: T <= bytes | unicode
    :rtype: str
    """
    if path.startswith('@eddy\\') or path.startswith('@eddy/'):
        path = os.path.join(getModulePath(), path[6:])
    elif path.startswith('@home\\') or path.startswith('@home/'):
        path = os.path.join(getHomePath(), path[6:])
    return os.path.normpath(os.path.expanduser(path))