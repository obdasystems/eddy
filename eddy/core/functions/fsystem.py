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


import io
import os
import shutil

from eddy.core.functions.path import expandPath


def cpdir(src, dst):
    """
    Recursively copy a directory tree.
    :type src: str
    :type dst: str
    """
    shutil.copytree(expandPath(src), expandPath(dst), copy_function=shutil.copy)


def faccess(path, mode=os.R_OK):
    """
    Returns whether the given path is accessible with the given mode.
    :type path:  str
    :type mode: int
    :rtype: bool
    """
    return os.access(expandPath(path), mode)


def fcopy(src, dst):
    """
    Copy the contents of the file named src to a file named dst.
    If dst specifies a directory, the file will be copied into
    dst using the base filename from src.
    :type src: str
    :type dst: str
    :rtype: str
    """
    return shutil.copy(expandPath(src), expandPath(dst))


def fexists(path):
    """
    Returns True if the given path identifies a regular file, False otherwise.
    :type path: str
    :rtype: bool
    """
    return os.path.isfile(expandPath(path))


def fread(path, newline=None):
    """
    Read the file identified by the given 'path' and returns its content.
    Optional newline parameter has the same role as `newline` in :func:`io.open`.
    :type path: str
    :type newline: str, optional
    :rtype: str
    """
    path = expandPath(path)
    with io.open(path, 'r', encoding='utf8', newline=newline) as ptr:
        return ptr.read()


def fremove(path):
    """
    Removes the file identified by the given 'path'.
    :type path: str
    """
    if fexists(path):
        os.remove(expandPath(path))


def frename(src, dst):
    """
    Rename a file or director
    :type src: str
    :type dst: str
    """
    os.rename(expandPath(src), expandPath(dst))


def fwrite(content, path, newline=None):
    """
    Safely write the given 'content' in the file identified by the given 'path'.
    If the given path identifies an already existing file, its content is not
    truncated unless the writing operation is completed successfully.
    Optional newline parameter has the same role as `newline` in :func:`io.open`.
    :type content: T <= bytes|str|unicode
    :type path: str
    :type newline: str, optional
    """
    components = os.path.split(expandPath(path))
    stage = os.path.join(components[0], '.{0}'.format(components[1]))
    with io.open(stage, 'w', encoding='utf8', newline=newline) as ptr:
        ptr.write(content)
    fremove(path)
    frename(stage, path)


def isdir(path):
    """
    Returns True if the given path identifies a directory, False otherwise.
    :type path: str
    :rtype: bool
    """
    return os.path.isdir(expandPath(path))


def make_archive(path, dst, base_dir=None, format='zip'):
    """
    Create an archive file (such as zip or tar) and return its name.

    'path' is the root directory to archive.

    'dst' is the name of the archive file to create, without the file extension.

    'base_dir' will be the common prefix of all the files and directories in the archive.

    'format' is the archive format; Valid values are 'zip', 'tar', 'gztar'
    (if the zlib module is available), 'bztar' (if the bz2 module is available),
    'xztar' (if the lzma module is available, requires Python >= 3.5).

    :type path: str
    :type dst: str
    :type base_dir: str
    :type format: str
    :rtype: str
    """
    return shutil.make_archive(expandPath(dst), format, expandPath(path), base_dir)


def mkdir(path):
    """
    Create the directory identified by the given path if it doesn't exists.
    This method will create all intermediate-level directories if needed.
    :type path: str
    """
    if not isdir(path):
        os.makedirs(expandPath(path))


def rmdir(path):
    """
    Removes the directory identified by given path if it exists.
    :type path: str
    """
    if isdir(path):
        shutil.rmtree(expandPath(path))
