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

from PyQt5 import QtCore

from eddy.core.datatypes.system import (
    IS_FROZEN,
    IS_LINUX,
    IS_MACOS,
    IS_WIN,
)

if IS_FROZEN:
    __MODULE_PATH = os.path.normpath(os.path.expanduser(sys._MEIPASS))
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
__TEST_RESOURCES_PATH = os.path.join(__TESTS_PATH, 'test_resources')


def compressPath(path: str, maxchars: int, dots: int = 3) -> str:
    """
    Returns a visual representation of the given path showing up to 'marchars' characters.
    """
    if len(path) > maxchars:
        index = path.rfind(os.path.sep)
        if index > 0:
            suffix = path[index-1:]
            prefix = path[:maxchars-dots-len(suffix)]
            path = ''.join([prefix] + ['.' for _ in range(dots)] + [suffix])
    return path


def expandPath(path: str) -> str:
    """
    Return an absolute path by expanding the given relative one.
    The following tokens will be expanded:

        - @eddy => Eddy's directory
        - @home => Eddy's home directory (.eddy in $HOME)
        - @config => Eddy's config directory (platform-specific)
        - @cache => Eddy's cache directory (platform-specific)
        - @data => Eddy's data directory (platform-specific)
        - @temp => Eddy's temp directory (platform-specific)
        - @runtime => Eddy's runtime directory (platform-specific)
        - @root => Eddy's root (matches @eddy if running a frozen application)
        - @resources => Eddy's resources directory
        - @examples => Eddy's examples directory
        - @plugins => Eddy's plugins directory
        - @support => Eddy's support directory
        - @tests => Eddy's tests directory
        - @test_resources => Eddy's test resources directory
        - ~ => will be expanded to the user home directory ($HOME)

    """
    if path.startswith('@eddy/') or path.startswith('@eddy\\'):
        path = os.path.join(__MODULE_PATH, path[6:])
    elif path.startswith('@home/') or path.startswith('@home\\'):
        path = os.path.join(__HOME_PATH, path[6:])
    elif path.startswith('@config/') or path.startswith('@config\\'):
        confPath = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppConfigLocation)
        path = os.path.join(os.path.normpath(os.path.join(confPath, os.path.pardir)), path[8:])
    elif path.startswith('@cache/') or path.startswith('@cache\\'):
        cachePath = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.CacheLocation)
        path = os.path.join(os.path.normpath(os.path.join(cachePath, os.path.pardir)), path[7:])
    elif path.startswith('@data/') or path.startswith('@data\\'):
        dataPath = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppDataLocation)
        path = os.path.join(os.path.normpath(os.path.join(dataPath, os.path.pardir)), path[6:])
    elif path.startswith('@temp/') or path.startswith('@temp\\'):
        tempPath = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.TempLocation)
        path = os.path.join(tempPath, path[6:])
    elif path.startswith('@runtime/') or path.startswith('@runtime\\'):
        runPath = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.RuntimeLocation)
        path = os.path.join(runPath, path[9:])
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
    elif path.startswith('@test_resources/') or path.startswith('@test_resources\\'):
        path = os.path.join(__TEST_RESOURCES_PATH, path[16:])
    return os.path.abspath(os.path.normpath(os.path.expanduser(path)))


def isPathValid(path: str) -> bool:
    """
    Returns True if the given path is valid, False otherwise.
    """
    try:
        if not path or not isinstance(path, str):
            return False
        path = expandPath(path)
        path = os.path.splitdrive(path)[1]
        root = os.path.sep
        if IS_WIN:
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


def isSubPath(path1: str, path2: str) -> bool:
    """
    Check whether the given 'path1' is subpath of the given 'path2'.
    """
    return expandPath(path2).startswith(expandPath(path1))


def openPath(path: str) -> None:
    """
    Open the given path using the OS default program.
    """
    path = expandPath(path)
    if os.path.isfile(path) or os.path.isdir(path):
        if IS_WIN:
            os.startfile(path)
        elif IS_MACOS:
            os.system('open "{0}"'.format(path))
        elif IS_LINUX:
            os.system('xdg-open "{0}"'.format(path))


def shortPath(path: str) -> str:
    """
    Convert the given path into a short one.
    The following tokens will be reintroduced:

        - ~ => user home directory ($HOME)

    """
    for prefix in ('~',):
        absprefix = expandPath(prefix)
        if path.startswith(absprefix):
            return path.replace(absprefix, prefix)
    return path


def uniquePath(base: str, name: str, extension: str) -> str:
    """
    This function generates a unique filepath which ensure not to overwrite an existing file.
    """
    num = 0
    base = expandPath(base)
    dest = os.path.join(base, '{0}{1}'.format(name, extension))
    while os.path.isfile(dest):
        dest = os.path.join(base, '{0}_{1}{2}'.format(name, num, extension))
        num += 1
    return dest
