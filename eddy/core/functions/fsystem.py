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


import os

from eddy.core.functions.path import expandPath


def fexists(path):
    """
    Returns True if the given path identifies a regular file, False otherwise.
    :type path: str
    :rtype: bool
    """
    return os.path.isfile(expandPath(path))


def fread(path):
    """
    Read the file identified by the given 'path' and returns its content.
    :type path: str
    :rtype: str
    """
    path = expandPath(path)
    with open(path, 'r') as ptr:
        return ptr.read()


def fremove(path):
    """
    Removes the file identified by the given 'path'.
    :type path: str
    """
    if fexists(path):
        os.remove(expandPath(path))


def fwrite(content, path):
    """
    Safely write the given 'content' in the file identified by the given 'path'.
    If the given path identifies an already existing file, its content is not
    truncated unless the writing operation is completed successfully.
    :type content: str
    :type path: str
    """
    path = expandPath(path)
    components = os.path.split(path)
    stage = os.path.join(components[0], '.{0}'.format(components[1]))
    with open(stage, mode='wb') as ptr:
        ptr.write(content.encode(encoding='UTF-8'))
    if os.path.isfile(path):
        os.remove(path)
    os.rename(stage, path)


def isdir(path):
    """
    Returns True if the given path identifies a directory, False otherwise.
    :type path: str
    :rtype: bool
    """
    return os.path.isdir(expandPath(path))


def mkdir(path):
    """
    Create the directory identified by the given path if it doesn't exists.
    :type path: str
    """
    if not isdir(path):
        os.mkdir(expandPath(path))