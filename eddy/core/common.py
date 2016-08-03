# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: a graphical editor for the specification of Graphol ontologies  #
#  Copyright (C) 2015 Daniele Pantaleone <pantaleone@dis.uniroma1.it>    #
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


from PyQt5.QtWidgets import QAction

from eddy.core.functions.misc import isEmpty
from eddy.core.output import getLogger


LOGGER = getLogger(__name__)


class HasActionSystem(object):
    """
    Mixin which adds the ability to store and retrieve actions.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self._actionDict = {}
        self._actionList = []

    def action(self, objectName):
        """
        Returns the reference to a QAction or to a QActionGroup given it's objectName.
        :type objectName: str
        :rtype: T <= QAction|QActionGroup
        """
        return self._actionDict.get(objectName, None)

    def actions(self):
        """
        Returns the list of QAction.
        :rtype: list
        """
        return self._actionList

    def addAction(self, action):
        """
        Add a QAction or a QActionGroup to the set.
        :type action: T <= QAction|QActionGroup
        :rtype: T <= QAction|QActionGroup
        """
        if isEmpty(action.objectName()):
            raise ValueError("missing objectName in %s" % action.__class__.__name__)
        if action.objectName() in self._actionDict:
            raise ValueError("duplicate action found: %s" % action.objectName())
        self._actionList.append(action)
        self._actionDict[action.objectName()] = action
        # LOGGER.debug("Added %s(%s)", action.__class__.__name__, action.objectName())
        return action

    def addActions(self, actions):
        """
        Add the given group of QAction or a QActionGroup to the set.
        :type actions: T <= list|tuple
        """
        for action in actions:
            self.addAction(action)

    def insertAction(self, action, before):
        """
        Insert the given QAction or QActionGroup before the given one.
        :type action: T <= QAction|QActionGroup
        :type before: T <= QAction|QActionGroup
        :rtype: T <= QAction|QActionGroup
        """
        if isEmpty(action.objectName()):
            raise ValueError("missing objectName in %s" % action.__class__.__name__)
        if action.objectName() in self._actionDict:
            raise ValueError("duplicate action found: %s" % action.objectName())
        self._actionList.insert(self._actionList.index(before), action)
        self._actionDict[action.objectName()] = action
        # LOGGER.debug("Added %s(%s) before %s(%s)",
        #              action.__class__.__name__, action.objectName(),
        #              before.__class__.__name__, before.objectName())
        return action

    def insertActions(self, actions, before):
        """
        Insert the given group of QAction or QActionGroup before the given one.
        :type actions: T <= list|tuple
        :type before: T <= QAction|QActionGroup
        """
        for action in actions:
            self.insertAction(action, before)

    def removeAction(self, action):
        """
        Removes the given QAction or QActionGroup from the set.
        :type action: T <= QAction|QActionGroup
        :rtype: T <= QAction|QActionGroup
        """
        self._actionList.remove(action)
        del self._actionDict[action.objectName()]
        return action


class HasMenuSystem(object):
    """
    Mixin which adds the ability to store and retrieve menus.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self._menuDict = {}
        self._menuList = []

    def addMenu(self, menu):
        """
        Add a QMenu to the set.
        :type menu: QMenu
        :rtype: QMenu
        """
        if isEmpty(menu.objectName()):
            raise ValueError("missing objectName in %s" % menu.__class__.__name__)
        if menu.objectName() in self._menuDict:
            raise ValueError("duplicate menu found: %s" % menu.objectName())
        self._menuList.append(menu)
        self._menuDict[menu.objectName()] = menu
        # LOGGER.debug("Added %s(%s)", menu.__class__.__name__, menu.objectName())
        return menu

    def addMenus(self, menus):
        """
        Add the given group of QMenu to the set.
        :type menus: T <= list|tuple
        """
        for menu in menus:
            self.addMenu(menu)

    def insertMenu(self, menu, before):
        """
        Insert the given QMenu before the given one.
        :type menu: QMenu
        :type before: QMenu
        :rtype: QMenu
        """
        if isEmpty(menu.objectName()):
            raise ValueError("missing objectName in %s" % menu.__class__.__name__)
        if menu.objectName() in self._menuDict:
            raise ValueError("duplicate menu found: %s" % menu.objectName())
        self._menuList.insert(self._menuList.index(before), menu)
        self._menuDict[menu.objectName()] = menu
        # LOGGER.debug("Added %s(%s) before %s(%s)",
        #              menu.__class__.__name__, menu.objectName(),
        #              before.__class__.__name__, before.objectName())
        return menu

    def insertMenus(self, menus, before):
        """
        Insert the given group of QMenu before the given one.
        :type menus: T <= list|tuple
        :type before: QMenu
        """
        for menu in menus:
            self.insertMenu(menu, before)
            
    def menu(self, objectName):
        """
        Returns the reference to a QMenu given it's objectName.
        :type objectName: str
        :rtype: QMenu
        """
        return self._menuDict.get(objectName, None)

    def menus(self):
        """
        Returns the list of QMenu.
        :rtype: list
        """
        return self._menuList

    def removeMenu(self, menu):
        """
        Removes the given QMenu from the set.
        :type menu: QMenu
        :rtype: QMenu
        """
        self._menuList.remove(menu)
        del self._menuDict[menu.objectName()]
        return menu


class HasPluginSystem(object):
    """
    Mixin which adds the ability to store and retrieve plugins.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self._pluginDict = {}
        self._pluginList = []

    def addPlugin(self, plugin):
        """
        Add a plugin to the set.
        :type plugin: AbstractPlugin
        :rtype: AbstractPlugin
        """
        if isEmpty(plugin.objectName()):
            raise ValueError("missing objectName in %s" % plugin.__class__.__name__)
        if plugin.objectName() in self._pluginDict:
            raise ValueError("duplicate plugin found: %s" % plugin.objectName())
        self._pluginList.append(plugin)
        self._pluginDict[plugin.objectName()] = plugin
        # LOGGER.debug("Added %s(%s)", plugin.__class__.__name__, plugin.objectName())
        return plugin

    def addPlugins(self, plugins):
        """
        Add the given group of plugins to the set.
        :type plugins: T <= list|tuple
        """
        for plugin in plugins:
            self.addPlugin(plugin)

    def insertPlugin(self, widget, before):
        """
        Insert the given plugin before the given one.
        :type widget: AbstractPlugin
        :type before: AbstractPlugin
        :rtype: AbstractPlugin
        """
        if isEmpty(widget.objectName()):
            raise ValueError("missing objectName in %s" % widget.__class__.__name__)
        if widget.objectName() in self._pluginDict:
            raise ValueError("duplicate plugin found: %s" % widget.objectName())
        self._pluginList.insert(self._pluginList.index(before), widget)
        self._pluginDict[widget.objectName()] = widget
        # LOGGER.debug("Added %s(%s) before %s(%s)",
        #              plugin.__class__.__name__, plugin.objectName(),
        #              before.__class__.__name__, before.objectName())
        return widget

    def insertPlugins(self, plugins, before):
        """
        Insert the given group of plugins before the given one.
        :type plugins: T <= list|tuple
        :type before: AbstractPlugin
        """
        for plugin in plugins:
            self.insertPlugin(plugin, before)

    def plugin(self, objectName):
        """
        Returns the reference to a plugin given it's objectName.
        :type objectName: str
        :rtype: AbstractPlugin
        """
        return self._pluginDict.get(objectName, None)

    def plugins(self):
        """
        Returns the list of plugins.
        :rtype: list
        """
        return self._pluginList

    def removePlugin(self, plugin):
        """
        Removes the given plugin from the set.
        :type plugin: AbstractPlugin
        :rtype: AbstractPlugin
        """
        self._pluginList.remove(plugin)
        del self._pluginDict[plugin.objectName()]
        return plugin


class HasWidgetSystem(object):
    """
    Mixin which adds the ability to store and retrieve widgets.
    """
    def __init__(self, **kwargs):
        """
        Initialize the object with default parameters.
        :type kwargs: dict
        """
        super().__init__(**kwargs)
        self._widgetDict = {}
        self._widgetList = []

    def addWidget(self, widget):
        """
        Add a QWidget to the set.
        :type widget: QWidget
        :rtype: QWidget
        """
        if isEmpty(widget.objectName()):
            raise ValueError("missing objectName in %s" % widget.__class__.__name__)
        if widget.objectName() in self._widgetDict:
            raise ValueError("duplicate widget found: %s" % widget.objectName())
        self._widgetList.append(widget)
        self._widgetDict[widget.objectName()] = widget
        # LOGGER.debug("Added %s(%s)", widget.__class__.__name__, widget.objectName())
        return widget

    def addWidgets(self, widgets):
        """
        Add the given group of QWidget to the set.
        :type widgets: T <= list|tuple
        """
        for widget in widgets:
            self.addWidget(widget)

    def insertWidget(self, widget, before):
        """
        Insert the given QWidget before the given one.
        :type widget: QWidget
        :type before: QWidget
        :rtype: QWidget
        """
        if isEmpty(widget.objectName()):
            raise ValueError("missing objectName in %s" % widget.__class__.__name__)
        if widget.objectName() in self._widgetDict:
            raise ValueError("duplicate widget found: %s" % widget.objectName())
        self._widgetList.insert(self._widgetList.index(before), widget)
        self._widgetDict[widget.objectName()] = widget
        # LOGGER.debug("Added %s(%s) before %s(%s)",
        #              widget.__class__.__name__, widget.objectName(),
        #              before.__class__.__name__, before.objectName())
        return widget

    def insertWidgets(self, widgets, before):
        """
        Insert the given group of QWidget before the given one.
        :type widgets: T <= list|tuple
        :type before: QWidget
        """
        for widget in widgets:
            self.insertWidget(widget, before)

    def widget(self, objectName):
        """
        Returns the reference to a QWidget given it's objectName.
        :type objectName: str
        :rtype: QWidget
        """
        return self._widgetDict.get(objectName, None)

    def widgets(self):
        """
        Returns the list of QWidget.
        :rtype: list
        """
        return self._widgetList

    def removeWidget(self, widget):
        """
        Removes the given QWidget from the set.
        :type widget: QWidget
        :rtype: QWidget
        """
        self._widgetList.remove(widget)
        del self._widgetDict[widget.objectName()]
        return widget