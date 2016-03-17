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
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################
from eddy.core.datatypes import Item
from eddy.core.functions import expandPath

from tests import EddyTestCase


class Test_Index(EddyTestCase):

    def setUp(self):
        """
        Setup index specific test environment.
        """
        super().setUp()

    def init(self, path=None):
        """
        Additional specific test case initialiation tasks.
        :type path: str
        """
        if path:
            self.scene = self.mainwindow.createSceneFromGrapholFile(expandPath(path))
        else:
            self.scene = self.mainwindow.createScene(5000, 5000)

        self.mainview = self.mainwindow.createView(self.scene)
        self.subwindow = self.mainwindow.createSubWindow(self.mainview)
        self.subwindow.showMaximized()
        self.mainwindow.mdi.setActiveSubWindow(self.subwindow)
        self.mainwindow.mdi.update()

    ####################################################################################################################
    #                                                                                                                  #
    #   TEST PREDICATE SUBCLASS OF                                                                                     #
    #                                                                                                                  #
    ####################################################################################################################

    def test_predicate_role_subclass_of(self):
        # WHEN
        self.init('@examples/Family.graphol')
        # THEN
        self.assertSetEqual(self.scene.index.predicateSubClassOf(Item.RoleNode, 'hasSon'), {'hasChild'})
        self.assertSetEqual(self.scene.index.predicateSubClassOf(Item.RoleNode, 'hasDaughter'), {'hasChild'})
        self.assertSetEqual(self.scene.index.predicateSubClassOf(Item.RoleNode, 'hasMother'), {'hasParent'})
        self.assertSetEqual(self.scene.index.predicateSubClassOf(Item.RoleNode, 'hasFather'), {'hasParent'})
        self.assertSetEqual(self.scene.index.predicateSubClassOf(Item.RoleNode, 'hasParent'), {'hasAncestor'})
        self.assertSetEqual(self.scene.index.predicateSubClassOf(Item.RoleNode, 'hasSister'), {'hasSibling'})
        self.assertSetEqual(self.scene.index.predicateSubClassOf(Item.RoleNode, 'hasBrother'), {'hasSibling'})
        self.assertEmpty(self.scene.index.predicateSubClassOf(Item.RoleNode, 'hasSibling'))
        self.assertEmpty(self.scene.index.predicateSubClassOf(Item.RoleNode, 'hasAncestor'))
        self.assertEmpty(self.scene.index.predicateSubClassOf(Item.RoleNode, 'hasChild'))

    def test_predicate_concept_subclass_of(self):
        # WHEN
        self.init('@examples/Family.graphol')
        # THEN
        self.assertSetEqual(self.scene.index.predicateSubClassOf(Item.ConceptNode, 'Mother'), {'Female'})
        self.assertSetEqual(self.scene.index.predicateSubClassOf(Item.ConceptNode, 'Father'), {'Male'})
        self.assertEmpty(self.scene.index.predicateSubClassOf(Item.ConceptNode, 'Person'))