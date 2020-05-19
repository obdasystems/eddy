#!/bin/bash
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

# Terminate in case of errors
#set -e

if [[ "$TRAVIS_OS_NAME" == "linux" ]] && [[ ! -z "$VIRTUAL_ENV" ]]; then
    # On Linux we remove Gtk platform theme from PyQt5 before running
    # PyInstaller since it causes a lot of clutter to be included in
    # the packaged application.

    # Remove Gtk3 platform theme.
    rm -rf "$VIRTUAL_ENV/lib/python3.5/site-packages/PyQt5/Qt/plugins/platformthemes/libqgtk3.so"
    rm -rf "$VIRTUAL_ENV/lib/python3.6/site-packages/PyQt5/Qt/plugins/platformthemes/libqgtk3.so"
    rm -rf "$VIRTUAL_ENV/lib/python3.7/site-packages/PyQt5/Qt/plugins/platformthemes/libqgtk3.so"
    rm -rf "$VIRTUAL_ENV/lib/python3.8/site-packages/PyQt5/Qt/plugins/platformthemes/libqgtk3.so"
fi
