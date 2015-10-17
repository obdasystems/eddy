# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Grapholed: a diagramming software for the Graphol language.           #
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


from functools import partial


# noinspection PyCallByClass
# noinspection PyUnresolvedReferences,PyTypeChecker
class memoized(object):
    """
    Cache the return value of a method/function.
    This class is meant to be used as a decorator of methods. The return value from a given method invocation
    will be cached on the instance whose method was invoked. All arguments passed to a method decorated with
    memoize must be hashable.
    If a memoized method is invoked directly on its class the result will not be cached.
    Instead the method will be invoked like a static method:

    >>>class Obj(object):
    >>>    @memoized
    >>>    def add_to(self, arg):
    >>>        return self + arg
    >>>Obj.add_to(1) # not enough arguments
    >>>Obj.add_to(1, 2) # returns 3, result is not cached

    See http://code.activestate.com/recipes/577452-a-memoize-decorator-for-instance-methods/
    """
    def __init__(self, func):
        """
        Object constructor.
        :param func: The decorated callable
        """
        self.func = func

    def __get__(self, obj, _):
        """
        Return cached result (if already computed) or the result returned by the cached function.
        """
        if obj is None:
            return self.func
        return partial(self, obj)

    def __call__(self, *args, **kw):
        """
        Cache function return value.
        """
        obj = args[0]
        try:
            cache = obj.__cache
        except AttributeError:
            cache = obj.__cache = {}
        key = (self.func, args[1:], frozenset(kw.items()))
        try:
            res = cache[key]
        except KeyError:
            res = cache[key] = self.func(*args, **kw)
        return res

    def __repr__(self):
         """
         Return the function's docstring.
         """
         return self.func.__doc__