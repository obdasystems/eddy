# -*- mode: python -*-

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

"""This is the PyInstaller .spec file that is used to produce distribution releases."""


import os
import pkgutil
import platform
import py_compile
import sys
import zipfile

from PyInstaller.compat import is_linux, is_darwin, is_win
from PyInstaller.config import CONF
from PyInstaller.log import logger

sys.path.insert(0, os.getcwd())
import eddy
from eddy import APPNAME, VERSION

###################################
# CONSTANTS DECLARATION
###########################

LINUX = is_linux
MACOS = is_darwin
WIN32 = is_win

EXEC_ARCH = None
EXEC_ICON = None
EXEC_NAME = None

if LINUX:
    EXEC_ARCH = platform.machine().lower()
    EXEC_ICON = 'resources/images/eddy.png'
    EXEC_NAME = APPNAME

if MACOS:
    EXEC_ARCH = platform.machine().lower()
    EXEC_ICON = 'resources/images/eddy.icns'
    EXEC_NAME = APPNAME

if WIN32:
    # On Windows use the PROCESSOR_ARCHITECTURE environment variable
    # to detect if we are running a 32-bit or 64-bit version of Python
    EXEC_ARCH = os.environ['PROCESSOR_ARCHITECTURE'].lower() if 'PROCESSOR_ARCHITECTURE' in os.environ else platform.machine().lower()
    EXEC_ICON = 'resources/images/eddy.ico'
    EXEC_NAME = APPNAME

WORK_PATH = CONF['workpath']
DIST_PATH = CONF['distpath']
DIST_NAME = '%s-%s-%s_%s' % (APPNAME, VERSION, platform.system().lower(), EXEC_ARCH)
JRE_DIR = os.path.join('resources', 'java')
ICON_FMT = 'ico' if WIN32 else 'icns' if MACOS else 'png'
GRAPHOL_ICON = '{}.{}'.format(os.path.join('resources', 'images', 'graphol'), ICON_FMT)

excludes = [
    # PYTHON BUILTINS
    'tkinter',
    # PyInstaller does not support pkg_resources
    'pkg_resources',
]

datas = [
    (os.path.relpath(os.path.join(WORK_PATH, 'plugins')), 'plugins'),
    ('eddy/core/jvm/lib/*.jar', 'resources/lib'),
    ('eddy/ui/style/*.qss', 'resources/styles'),
    ('examples', 'examples'),
    ('LICENSE', '.'),
    (GRAPHOL_ICON, '.'),
]

if LINUX:
    datas.extend([
        # BUNDLE ICON
        (EXEC_ICON, '.'),
        # COPY FONTCONFIG CONFIGURATION
        ('/etc/fonts', 'etc/fonts'),
    ])

# BUNDLE JVM IF AVAILABLE
if os.path.isdir(JRE_DIR):
    logger.info('Packaging JRE in %s' % JRE_DIR)
    datas.append((JRE_DIR, JRE_DIR))


def get_hidden_imports():
    """
    Returns the list of hidden imports.
    Walks the entire eddy package tree and lists all its sub-modules.
    """
    imports = []
    for finder, name, ispkg in pkgutil.walk_packages(eddy.__path__, eddy.__name__ + '.'):
        if not ispkg:
            imports.append(name)
    # PLUGIN HIDDEN IMPORTS AND EXTRA MODULES TO BUNDLE
    imports.extend([
        'eddy.plugins',  # PLUGINS PACKAGE
        'ast',  # Required by: ontology_importer
        'sqlite3',  # Required by: ontology_importer
    ])
    return imports


def get_runtime_hooks():
    """
    Returns the list of runtime hooks.
    """
    runtime_hooks = []
    if LINUX:
        runtime_hooks.append('scripts/hooks/runtime/rt_fontconfig.py')
    return runtime_hooks


def package_plugins():
    """
    Package built-in plugins into ZIP archives.
    """
    from eddy.core.functions.fsystem import isdir, mkdir, fremove
    from eddy.core.functions.path import expandPath
    from eddy.core.functions.misc import rstrip
    if isdir('@plugins/'):
        mkdir(os.path.join(WORK_PATH, 'plugins'))
        for file_or_directory in os.listdir(expandPath('@plugins/')):
            plugin = os.path.join(expandPath('@plugins/'), file_or_directory)
            if isdir(plugin) and not plugin.endswith('__pycache__'):
                logger.info('packaging plugin: %s', file_or_directory)
                zippath = os.path.join(WORK_PATH, 'plugins', '%s.zip' % file_or_directory)
                with zipfile.ZipFile(zippath, 'w', zipfile.ZIP_STORED) as zipf:
                    for root, dirs, files in os.walk(plugin):
                        if not root.endswith('__pycache__'):
                            for filename in files:
                                path = expandPath(os.path.join(root, filename))
                                if path.endswith('.py'):
                                    new_path = '%s.pyc' % rstrip(path, '.py')
                                    py_compile.compile(path, new_path)
                                    arcname = os.path.relpath(new_path, plugin)
                                    zipf.write(new_path, arcname)
                                    fremove(new_path)
                                else:
                                    arcname = os.path.relpath(path, plugin)
                                    zipf.write(path, arcname)


# PACKAGE BUILTIN PLUGINS
package_plugins()

###################################
# ANALYSIS
###########################

block_cipher = None

a = Analysis(['run.py'],
             pathex=[os.getcwd()],
             binaries=[],
             datas=datas,
             hiddenimports=get_hidden_imports(),
             hookspath=['scripts/hooks'],
             runtime_hooks=get_runtime_hooks(),
             excludes=excludes,
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

###################################
# PYZ
###########################

pyz = PYZ(a.pure,
          a.zipped_data,
          cipher=block_cipher)

###################################
# EXE
###########################

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name=APPNAME,
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=False,
          icon=EXEC_ICON)

###################################
# COLLECT
###########################

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name=DIST_NAME)

###################################
# BUNDLE
###########################

info_plist = {
    'CFBundleName': APPNAME,
    'CFBundleGetInfoString': VERSION,
    'CFBundleShortVersionString': VERSION,
    'CFBundleVersion': VERSION,
    'CFBundlePackageType': 'APPL',
    'CFBundleIconFile': os.path.basename(EXEC_ICON),
    'CFBundleIdentifier': 'com.obdasystems.eddy',
    'CFBundleInfoDictionaryVersion': '6.0',
    'CFBundleDevelopmentRegion': 'English',
    'CFBundleSpokenName': APPNAME,
    'CFBundleExecutable': APPNAME,
    'NSPrincipalClass': 'NSApplication',
    'NSHighResolutionCapable': 'True',
    'NSRequiresAquaSystemAppearance': 'True',
    'CFBundleDocumentTypes': [{
        'CFBundleTypeName': 'Graphol File',
        'CFBundleTypeRole': 'Editor',
        'CFBundleTypeIconFile': 'graphol',
        'CFBundleTypeExtensions': ['graphol'],
        'LSHandlerRank': 'Owner',
        'LSIsAppleDefaultForFile': True,
        'LSItemContentTypes': ['it.uniroma1.graphol'],
    }],
    'UTExportedTypeDeclarations': [{
        'UTTypeConformsTo': ['public.data'],
        'UTTypeDescription': 'Graphol File',
        'UTTypeIdentifier': 'it.uniroma1.graphol',
        'UTTypeTagSpecification': {
            'public.filename-extension': 'graphol',
            'public.mime-type': 'application/octet-stream',
        }
    }]
}

app = BUNDLE(coll,
         name='{}.app'.format(APPNAME.title()),
         icon=EXEC_ICON,
         info_plist=info_plist,
         bundle_identifier=None)
