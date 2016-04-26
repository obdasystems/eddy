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


from functools import partial


def connect(signal, slot, *args, **kwargs):
    """
    Connect the given signal to the specified slots passing all arguments
    to the slot. Note that this function make use of functools.partial to
    hand parameters over to the function slot. This is actually highly
    discouraged because the the function slot will be treated as a normal
    python callable, losing all the properties of PyQt slots. Whenever it's
    possible make use of self.sender() to retrieve the action executing the
    slot execution, and action.data() to retrieve function slot's parameters.
    :type signal: pyqtSignal
    :type slot: callable
    :type args: mixed
    :type kwargs: mixed
    """
    if not args and not kwargs:
        signal.connect(slot)
    else:
        signal.connect(partial(slot, *args, **kwargs))


def disconnect(signal, *args):
    """
    Disconnect the given signal.
    :type signal: pyqtSignal
    :type args: mixed
    """
    if args:
        for slot in args:
            try:
                signal.disconnect(slot)
            except (RuntimeError, TypeError, AttributeError):
                pass
    else:
        try:
            signal.disconnect()
        except (RuntimeError, TypeError, AttributeError):
            pass


def emit(signal, *args):
    """
    Emit the given signal passing the given arguments along.
    This function is actually just a wrapper around the pyqtSignal
    built-in, mostly needed to keep backwards compatibility in case
    PyQt changes the signal interface, like it happened already with
    the introduction of the new style for signals and slots introduced
    in PyQt4 v4.5.
    :type signal: pyqtSignal
    :type args: list
    """
    signal.emit(*args)