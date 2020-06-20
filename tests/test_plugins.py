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


import pytest

from eddy.core.functions.path import expandPath
from eddy.core.plugin import PluginManager


#############################################
# PLUGIN MANAGER TESTS
#################################

@pytest.fixture(autouse=True)
def reset_plugin_list(monkeypatch):
    """
    Fixture to reset plugin list at each test run.
    """
    monkeypatch.setattr('eddy.core.plugin.PluginManager.info', {})


def test_import_single_module_plugin_from_directory():
    # GIVEN
    plugin_path = expandPath('@tests/test_resources/plugins/dir/testplugin1')
    # WHEN
    spec, plugin_path, plugin_class = PluginManager.import_plugin_from_path(plugin_path)
    # THEN
    assert spec is not None
    assert plugin_path is not None
    assert plugin_class is None
    assert 'testplugin1' == spec.get('plugin', 'id')


def test_import_single_module_plugin_from_zip():
    # GIVEN
    plugin_path = expandPath('@tests/test_resources/plugins/zip/testplugin1.zip')
    # WHEN
    spec, plugin_path, plugin_class = PluginManager.import_plugin_from_path(plugin_path)
    # THEN
    assert spec is not None
    assert plugin_path is not None
    assert plugin_class is None
    assert 'testplugin1' == spec.get('plugin', 'id')


def test_import_multi_module_plugin_from_directory():
    # GIVEN
    plugin_path = expandPath('@tests/test_resources/plugins/dir/testplugin2')
    # WHEN
    spec, plugin_path, plugin_class = PluginManager.import_plugin_from_path(plugin_path)
    # THEN
    assert spec is not None
    assert plugin_path is not None
    assert plugin_class is None
    assert 'testplugin2' == spec.get('plugin', 'id')


def test_import_multi_module_plugin_from_zip():
    # GIVEN
    plugin_path = expandPath('@tests/test_resources/plugins/zip/testplugin2.zip')
    # WHEN
    spec, plugin_path, plugin_class = PluginManager.import_plugin_from_path(plugin_path)
    # THEN
    assert spec is not None
    assert plugin_path is not None
    assert plugin_class is None
    assert 'testplugin2' == spec.get('plugin', 'id')


# noinspection PyUnresolvedReferences
def test_scan_plugins_from_directory():
    # GIVEN
    plugin_dir = expandPath('@tests/test_resources/plugins/dir')
    # WHEN
    PluginManager.scan(plugin_dir)
    # THEN
    assert 2 == len(PluginManager.info)
    assert 'testplugin1' in PluginManager.info
    assert 'testplugin2' in PluginManager.info
    # WHEN
    from eddy.plugins.testplugin1 import TestPlugin1
    from eddy.plugins.testplugin2 import TestPlugin2
    # THEN
    assert TestPlugin1(PluginManager.info.get('testplugin1')[0], None) is not None
    assert TestPlugin2(PluginManager.info.get('testplugin2')[0], None) is not None


# noinspection PyUnresolvedReferences
def test_scan_plugins_from_zip():
    # GIVEN
    plugin_dir = expandPath('@tests/test_resources/plugins/zip')
    # WHEN
    PluginManager.scan(plugin_dir)
    # THEN
    assert 2 == len(PluginManager.info)
    assert 'testplugin1' in PluginManager.info
    assert 'testplugin2' in PluginManager.info
    # WHEN
    from eddy.plugins.testplugin1 import TestPlugin1
    from eddy.plugins.testplugin2 import TestPlugin2
    # THEN
    assert TestPlugin1(PluginManager.info.get('testplugin1')[0], None) is not None
    assert TestPlugin2(PluginManager.info.get('testplugin2')[0], None) is not None
