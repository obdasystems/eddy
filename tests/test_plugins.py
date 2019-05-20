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


import unittest

from eddy.core.functions.path import expandPath
from eddy.core.plugin import PluginManager


class PluginManagerTestCase(unittest.TestCase):
    """
    Tests for the PluginManager.
    """
    def setUp(self):
        """
        Initialize test case environment.
        """
        PluginManager.info = {}

    def test_import_single_module_plugin_from_directory(self):
        # GIVEN
        plugin_path = expandPath('@tests/test_plugins/dir/testplugin1')
        # WHEN
        spec, plugin_path, plugin_class = PluginManager.import_plugin_from_path(plugin_path)
        # THEN
        self.assertIsNotNone(spec)
        self.assertIsNotNone(plugin_path)
        self.assertIsNone(plugin_class)
        self.assertEqual('testplugin1', spec.get('plugin', 'id'))

    def test_import_single_module_plugin_from_zip(self):
        # GIVEN
        plugin_path = expandPath('@tests/test_plugins/zip/testplugin1.zip')
        # WHEN
        spec, plugin_path, plugin_class = PluginManager.import_plugin_from_path(plugin_path)
        # THEN
        self.assertIsNotNone(spec)
        self.assertIsNotNone(plugin_path)
        self.assertIsNone(plugin_class)
        self.assertEqual('testplugin1', spec.get('plugin', 'id'))

    def test_import_multi_module_plugin_from_directory(self):
        # GIVEN
        plugin_path = expandPath('@tests/test_plugins/dir/testplugin2')
        # WHEN
        spec, plugin_path, plugin_class = PluginManager.import_plugin_from_path(plugin_path)
        # THEN
        self.assertIsNotNone(spec)
        self.assertIsNotNone(plugin_path)
        self.assertIsNone(plugin_class)
        self.assertEqual('testplugin2', spec.get('plugin', 'id'))

    def test_import_multi_module_plugin_from_zip(self):
        # GIVEN
        plugin_path = expandPath('@tests/test_plugins/zip/testplugin2.zip')
        # WHEN
        spec, plugin_path, plugin_class = PluginManager.import_plugin_from_path(plugin_path)
        # THEN
        self.assertIsNotNone(spec)
        self.assertIsNotNone(plugin_path)
        self.assertIsNone(plugin_class)
        self.assertEqual('testplugin2', spec.get('plugin', 'id'))

    # noinspection PyUnresolvedReferences
    def test_scan_plugins_from_directory(self):
        # GIVEN
        plugin_dir = expandPath('@tests/test_plugins/dir')
        # WHEN
        PluginManager.scan(plugin_dir)
        # THEN
        self.assertEqual(2, len(PluginManager.info))
        self.assertIn('testplugin1', PluginManager.info)
        self.assertIn('testplugin2', PluginManager.info)
        # WHEN
        from eddy.plugins.testplugin1 import TestPlugin1
        from eddy.plugins.testplugin2 import TestPlugin2
        # THEN
        self.assertIsNotNone(TestPlugin1(PluginManager.info.get('testplugin1')[0], None))
        self.assertIsNotNone(TestPlugin2(PluginManager.info.get('testplugin2')[0], None))

    # noinspection PyUnresolvedReferences
    def test_scan_plugins_from_zip(self):
        # GIVEN
        plugin_dir = expandPath('@tests/test_plugins/zip')
        # WHEN
        PluginManager.scan(plugin_dir)
        # THEN
        self.assertEqual(2, len(PluginManager.info))
        self.assertIn('testplugin1', PluginManager.info)
        self.assertIn('testplugin2', PluginManager.info)
        # WHEN
        from eddy.plugins.testplugin1 import TestPlugin1
        from eddy.plugins.testplugin2 import TestPlugin2
        # THEN
        self.assertIsNotNone(TestPlugin1(PluginManager.info.get('testplugin1')[0], None))
        self.assertIsNotNone(TestPlugin2(PluginManager.info.get('testplugin2')[0], None))
