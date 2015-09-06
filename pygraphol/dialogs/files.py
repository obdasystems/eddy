# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  pyGraphol: a python design tool for the Graphol language.             #
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
#  Dipartimento di Informatica e Sistemistica "A.Ruberti" at Sapienza    #
#  University of Rome: http://www.dis.uniroma1.it/~graphol/:             #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Marco Console <console@dis.uniroma1.it>                          #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#                                                                        #
##########################################################################


from pygraphol.functions import getPath
from PyQt5.QtWidgets import QFileDialog


class SaveFileDialog(QFileDialog):
    """
    This class is used to bring up the save file dialog modal window.
    """
    def __init__(self, path, parent=None):
        """
        Initialize the save file dialog.
        :param path: the start path where to open the file dialog.
        :param parent: the parent widget.
        """
        super().__init__(parent)
        self.setAcceptMode(QFileDialog.AcceptSave)
        self.setDirectory(getPath('~') if not path else getPath(path))
        self.setFileMode(QFileDialog.AnyFile)
        self.setViewMode(QFileDialog.Detail)


class OpenFileDialog(QFileDialog):
    """
    This class is used to bring up the open file dialog modal window.
    """
    def __init__(self, path, parent=None):
        """
        Initialize the open file dialog.
        :param path: the start path where to open the file dialog.
        :param parent: the parent widget.
        """
        super().__init__(parent)
        self.setAcceptMode(QFileDialog.AcceptOpen)
        self.setDirectory(getPath('~') if not path else getPath(path))
        self.setFileMode(QFileDialog.AnyFile)
        self.setViewMode(QFileDialog.Detail)