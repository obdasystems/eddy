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
import sys


def expandPath(path):
    """
    Return an absolute path by expanding the given relative one.
    The following tokens will be expanded:

        - @eddy => Eddy's directory
        - @home => Eddy's home directory (.eddy in $HOME)
        - @root => Eddy's root (matches @eddy if running a frozen application)
        - @resources => Eddy's resources directory
        - @examples => Eddy's examples directory
        - ~ => will be expanded to the user home directory ($HOME)

    :type path: T <= bytes | unicode
    :rtype: str
    """
    if path.startswith('@eddy\\') or path.startswith('@eddy/'):
        path = os.path.join(modulePath(), path[6:])
    elif path.startswith('@home\\') or path.startswith('@home/'):
        path = os.path.join(homePath(), path[6:])
    elif path.startswith('@root\\') or path.startswith('@root/'):
        path = os.path.join(rootPath(), path[6:])
    elif path.startswith('@resources\\') or path.startswith('@resources/'):
        path = os.path.join(resourcesPath(), path[11:])
    elif path.startswith('@examples\\') or path.startswith('@examples/'):
        path = os.path.join(examplesPath(), path[10:])
    return os.path.normpath(os.path.expanduser(path))


def examplesPath():
    """
    Returns the path to the examples directory.
    :rtype: str
    """
    return os.path.join(rootPath(), 'examples')


def homePath():
    """
    Returns the path to Eddy's home directory.
    :rtype: str
    """
    homepath = os.path.normpath(os.path.expanduser('~/.eddy'))
    if not os.path.isdir(homepath):
        os.mkdir(homepath)
    return homepath


def modulePath():
    """
    Returns the path to Eddy's directory.
    :rtype: str
    """
    if hasattr(sys, 'frozen'):
        path = os.path.dirname(sys.executable)
    else:
        path = os.path.dirname(sys.modules['eddy'].__file__)
    return os.path.normpath(os.path.expanduser(path))


def resourcesPath():
    """
    Returns the path to the resources directory.
    :rtype: str
    """
    return os.path.join(rootPath(), 'resources')


def rootPath():
    """
    Returns the path to Eddy's root directory.
    :rtype: str
    """
    path = modulePath()
    if not hasattr(sys, 'frozen'):
        path = os.path.join(path, '..')
    return os.path.normpath(os.path.expanduser(path))