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
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import errno
import os
import sys

from eddy.core.datatypes.system import Platform
from eddy.core.functions.misc import cutR, clamp


def compressPath(path, maxchars, dots=3):
    """
    Returns a visual representation of the given path showing up to 'marchars' characters.
    :type path: str
    :type maxchars: int
    :type dots: int
    """
    if len(path) > maxchars:
        dots = clamp(dots, 2)
        index = path.rfind(os.path.sep)
        if index > 0:
            suffix = path[index-1:]
            prefix = path[:maxchars-dots-len(suffix)]
            path = ''.join([prefix] + ['.' for _ in range(dots)] + [suffix])
    return path


def examplesPath():
    """
    Returns the path to the examples directory.
    :rtype: str
    """
    return os.path.join(rootPath(), 'examples')


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

    :type path: str
    :rtype: str
    """
    if path.startswith('@eddy/') or path.startswith('@eddy\\'):
        path = os.path.join(modulePath(), path[6:])
    elif path.startswith('@home/') or path.startswith('@home\\'):
        path = os.path.join(homePath(), path[6:])
    elif path.startswith('@root/') or path.startswith('@root\\'):
        path = os.path.join(rootPath(), path[6:])
    elif path.startswith('@resources/') or path.startswith('@resources\\'):
        path = os.path.join(resourcesPath(), path[11:])
    elif path.startswith('@examples/') or path.startswith('@examples\\'):
        path = os.path.join(examplesPath(), path[10:])
    return os.path.normpath(os.path.expanduser(path))


def homePath():
    """
    Returns the path to Eddy's home directory.
    :rtype: str
    """
    homepath = os.path.normpath(os.path.expanduser('~/.eddy'))
    if not os.path.isdir(homepath):
        os.mkdir(homepath)
    return homepath


def isPathValid(path):
    """
    Returns True if the given path is valid for the current, False otherwise.
    :type path: str
    :rtype: bool
    """
    try:

        if not path or not isinstance(path, str):
            return False

        path = expandPath(path)
        path = os.path.splitdrive(path)[1]

        root = os.path.sep
        if Platform.identify() is Platform.Windows:
            root = os.environ.get('HOMEDRIVE', 'C:')
        root = '{0}{1}'.format(cutR(root, os.path.sep), os.path.sep)

        assert os.path.isdir(root)

        for part in path.split(os.path.sep):

            try:
                os.lstat(os.path.join(root, part))
            except OSError as exc:
                if hasattr(exc, 'winerror'):
                    # ERROR_INVALID_NAME = 123
                    if exc.winerror == 123:
                        return False
                if exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False

    except TypeError:
        return False
    else:
        return True


def isSubPath(path1, path2):
    """
    Check whether the given 'path1' is subpath of the given 'path2'.
    :param path1: str
    :param path2: str
    :rtype: bool
    """
    return expandPath(path2).startswith(expandPath(path1))


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


def openPath(path):
    """
    Open the given path using the OS default program.
    :type path: str
    """
    path = expandPath(path)
    if os.path.isfile(path) or os.path.isdir(path):
        platform = Platform.identify()
        if platform is Platform.Windows:
            os.system('start {0}'.format(path))
        elif platform is Platform.Darwin:
            os.system('open "{0}"'.format(path))
        elif platform is Platform.Linux:
            os.system('xdg-open "{0}"'.format(path))


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


def shortPath(path):
    """
    Convert the given path into a short one.
    The following tokens will be reintroduced:

        - ~ => will be expanded to the user home directory ($HOME)

    :type path: str
    :rtype: str
    """
    for prefix in ('~',):
        absprefix = expandPath(prefix)
        if path.startswith(absprefix):
            return path.replace(absprefix, prefix)
    return path


def uniquePath(base, name, extension):
    """
    This function generates a unique filepath which ensure not to overwrite an existing file.
    :type base: str
    :type name: str
    :type extension: str
    :rtype: str
    """
    num = 0
    base = expandPath(base)
    dest = os.path.join(base, '{0}{1}'.format(name, extension))
    while os.path.isfile(dest):
        dest = os.path.join(base, '{0}_{1}{2}'.format(name, num, extension))
        num += 1
    return dest