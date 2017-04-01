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


import errno
import os
import sys


__LINUX = sys.platform.startswith('linux')
__MACOS = sys.platform.startswith('darwin')
__WIN32 = sys.platform.startswith('win32')


if hasattr(sys, 'frozen'):
    __MODULE_PATH = os.path.normpath(os.path.expanduser(os.path.dirname(sys.executable)))
    __ROOT_PATH = __MODULE_PATH
else:
    __MODULE_PATH = os.path.normpath(os.path.expanduser(os.path.dirname(sys.modules['eddy'].__file__)))
    __ROOT_PATH = os.path.join(__MODULE_PATH, '..')


__EXAMPLES_PATH = os.path.join(__ROOT_PATH, 'examples')
__HOME_PATH = os.path.normpath(os.path.expanduser('~/.eddy'))
__PLUGINS_PATH = os.path.join(__MODULE_PATH, 'plugins')
__RESOURCES_PATH = os.path.join(__ROOT_PATH, 'resources')
__SUPPORT_PATH = os.path.join(__ROOT_PATH, 'support')
__TESTS_PATH = os.path.join(__ROOT_PATH, 'tests')


if not os.path.isdir(__HOME_PATH):
    os.mkdir(__HOME_PATH)


def compressPath(path, maxchars, dots=3):
    """
    Returns a visual representation of the given path showing up to 'marchars' characters.
    :type path: str
    :type maxchars: int
    :type dots: int
    """
    if len(path) > maxchars:
        index = path.rfind(os.path.sep)
        if index > 0:
            suffix = path[index-1:]
            prefix = path[:maxchars-dots-len(suffix)]
            path = ''.join([prefix] + ['.' for _ in range(dots)] + [suffix])
    return path


def expandPath(path):
    """
    Return an absolute path by expanding the given relative one.
    The following tokens will be expanded:

        - @eddy => Eddy's directory
        - @home => Eddy's home directory (.eddy in $HOME)
        - @root => Eddy's root (matches @eddy if running a frozen application)
        - @resources => Eddy's resources directory
        - @examples => Eddy's examples directory
        - @plugins => Eddy's plugins directory
        - @support => Eddy's support directory
        - @tests => Eddy's tests directory
        - ~ => will be expanded to the user home directory ($HOME)

    :type path: str
    :rtype: str
    """
    if path.startswith('@eddy/') or path.startswith('@eddy\\'):
        path = os.path.join(__MODULE_PATH, path[6:])
    elif path.startswith('@home/') or path.startswith('@home\\'):
        path = os.path.join(__HOME_PATH, path[6:])
    elif path.startswith('@root/') or path.startswith('@root\\'):
        path = os.path.join(__ROOT_PATH, path[6:])
    elif path.startswith('@resources/') or path.startswith('@resources\\'):
        path = os.path.join(__RESOURCES_PATH, path[11:])
    elif path.startswith('@examples/') or path.startswith('@examples\\'):
        path = os.path.join(__EXAMPLES_PATH, path[10:])
    elif path.startswith('@plugins/') or path.startswith('@plugins\\'):
        path = os.path.join(__PLUGINS_PATH, path[9:])
    elif path.startswith('@support/') or path.startswith('@support\\'):
        path = os.path.join(__SUPPORT_PATH, path[9:])
    elif path.startswith('@tests/') or path.startswith('@tests\\'):
        path = os.path.join(__TESTS_PATH, path[7:])
    return os.path.abspath(os.path.normpath(os.path.expanduser(path)))


def isPathValid(path):
    """
    Returns True if the given path is valid, False otherwise.
    :type path: str
    :rtype: bool
    """
    try:
        if not path or not isinstance(path, str):
            return False
        path = expandPath(path)
        path = os.path.splitdrive(path)[1]
        root = os.path.sep
        if __WIN32:
            root = os.environ.get('HOMEDRIVE', 'C:')
        root = '{0}{1}'.format(root.rstrip(os.path.sep), os.path.sep)
        assert os.path.isdir(root)
        for part in path.split(os.path.sep):
            try:
                os.lstat(os.path.join(root, part))
            except OSError as exc:
                if hasattr(exc, 'winerror'):
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


def openPath(path):
    """
    Open the given path using the OS default program.
    :type path: str
    """
    path = expandPath(path)
    if os.path.isfile(path) or os.path.isdir(path):
        if __WIN32:
            os.system('start {0}'.format(path))
        elif __MACOS:
            os.system('open "{0}"'.format(path))
        elif __LINUX:
            os.system('xdg-open "{0}"'.format(path))


def shortPath(path):
    """
    Convert the given path into a short one.
    The following tokens will be reintroduced:

        - ~ => user home directory ($HOME)

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