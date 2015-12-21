# -*- coding: utf-8 -*-

##########################################################################
#                                                                        #
#  Eddy: an editor for the Graphol ontology language.                    #
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
#  Dipartimento di Ingegneria Informatica, Automatica e Gestionale       #
#  A.Ruberti at Sapienza University of Rome: http://www.dis.uniroma1.it/ #
#                                                                        #
#     - Domenico Lembo <lembo@dis.uniroma1.it>                           #
#     - Valerio Santarelli <santarelli@dis.uniroma1.it>                  #
#     - Domenico Fabio Savo <savo@dis.uniroma1.it>                       #
#     - Marco Console <console@dis.uniroma1.it>                          #
#                                                                        #
##########################################################################


import os
import platform
import re
import setuptools
import stat
import sys
import zipfile

from distutils import dir_util, log
from eddy import __appname__ as APPNAME, __license__ as LICENSE, __version__ as VERSION

from PyQt5 import QtCore


OPTS = {
    'PROJECT_DIR': os.path.abspath(os.path.dirname(__file__))
}

OPTS['BUILD_DIR'] = os.path.join(OPTS['PROJECT_DIR'], 'build')
OPTS['DIST_DIR'] = os.path.join(OPTS['PROJECT_DIR'], 'dist')

if sys.platform.startswith('darwin'):
    OPTS['EXEC_NAME'] = APPNAME
    OPTS['EXEC_ICON'] = os.path.join(OPTS['PROJECT_DIR'], 'eddy', 'artwork', 'eddy.icns')
    OPTS['DIST_NAME'] = '{}-{}-{}-darwin'.format(APPNAME, VERSION, LICENSE.lower())
    OPTS['APPEND_SCRIPT_TO_EXE'] = False # KEEP THIS FALSE: https://bitbucket.org/anthony_tuininga/cx_freeze/issues/118
elif sys.platform.startswith('win32'):
    OPTS['EXEC_NAME'] = '{}.exe'.format(APPNAME)
    OPTS['EXEC_ICON'] = os.path.join(OPTS['PROJECT_DIR'], 'eddy', 'artwork', 'eddy.ico')
    OPTS['DIST_NAME'] = '{}-{}-{}-win{}'.format(APPNAME, VERSION, LICENSE.lower(), platform.architecture()[0][:-3])
    OPTS['APPEND_SCRIPT_TO_EXE'] = True
else:
    OPTS['EXEC_NAME'] = APPNAME
    OPTS['EXEC_ICON'] = os.path.join(OPTS['PROJECT_DIR'], 'eddy', 'artwork', 'eddy.png')
    OPTS['DIST_NAME'] = '{}-{}-{}-linux{}'.format(APPNAME, VERSION, LICENSE.lower(), platform.architecture()[0][:-3])
    OPTS['APPEND_SCRIPT_TO_EXE'] = True


OPTS['BUILD_PATH'] = os.path.join(OPTS['BUILD_DIR'], OPTS['DIST_NAME'])


class CleanCommand(setuptools.Command):
    """Custom clean command to tidy up the project root"""
    user_options = []

    def initialize_options(self):
        """Initialize command options"""
        pass

    def finalize_options(self):
        """Finalize command options"""
        pass

    def run(self):
        """Command execution"""
        if os.path.isdir(OPTS['BUILD_DIR']):
            dir_util.remove_tree(OPTS['BUILD_DIR'], verbose=1)
        if os.path.isdir('eddy.egg-info'):
            dir_util.remove_tree('eddy.egg-info', verbose=1)

cmdclass = {
    'clean': CleanCommand
}

executables = None


if len(sys.argv) == len(set(sys.argv) - {'build_exe', 'bdist_mac', 'bdist_dmg'}):
    from setuptools import setup
else:
    from cx_Freeze import setup
    from cx_Freeze import Executable
    from cx_Freeze import build_exe

    class my_build_exe(build_exe):
        """extends the build_exe command to:
           - add option 'dist_dir' (or --dist-dir as a command line parameter)
           - produce a zip file
        """
        dist_dir = None
        user_options = build_exe.user_options
        user_options.extend([('dist-dir=', 'd', "directory where to put final distributions in [default: dist]")])

        def initialize_options(self):
            """Initialize command options"""
            self.dist_dir = None
            super().initialize_options()

        def finalize_options(self):
            """Finalize command options"""
            if self.dist_dir is None:
                self.dist_dir = self.build_exe
            super().finalize_options()

        def run(self):
            """Command execution"""
            super().run()
            self.prepare_dist()
            self.copy_qt5_libraries()
            self.copy_qt5_plugins()
            self.clean_compiled_files()
            self.unix_2_dos()
            self.unix_exec()
            self.chmod_exec()
            self.make_zip()

        def prepare_dist(self):
            """Create 'dist' directory"""
            if not os.path.isdir(self.dist_dir):
                os.mkdir(self.dist_dir)

        def copy_qt5_libraries(self):
            """Copy necessary Qt5 libraries"""
            if sys.platform.startswith('linux'):
                log.info(">>> copy qt5 libraries")
                basepath = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.LibrariesPath)
                for lib in ['libQt5DBus.so.5', 'libQt5XcbQpa.so.5']:
                    self.copy_file(os.path.join(basepath, lib), self.build_exe )

        def copy_qt5_plugins(self):
            """Copy necessary Qt5 plugins"""
            log.info(">>> copy qt5 plugins")
            basepath = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.PluginsPath)
            for plugin in ['printsupport']:
                src = os.path.join(basepath, plugin)
                dst = os.path.join(self.build_exe, plugin)
                self.mkpath(dst)
                self.copy_tree(src, dst)

        def clean_compiled_files(self):
            """Remove python compiled files (if any got left in)"""
            log.info(">>> clean pyc/pyo")
            for root, dirs, files in os.walk(self.build_exe):
                for filename in files:
                    path = os.path.abspath(os.path.join(root, filename))
                    if path.endswith('.pyc') or path.endswith('.pyo'):
                        os.remove(path)

        def unix_2_dos(self):
            """Makes sure text files from directory have 'Windows style' end of lines"""
            if sys.platform == 'win32':
                log.info(">>> unix 2 dos")
                for root, dirs, files in os.walk(self.build_exe):
                    for filename in files:
                        path = os.path.abspath(os.path.join(root, filename))
                        if not os.path.isdir(path) and path.rsplit('.', 1)[-1] in ('txt', 'md'):
                            with open(path, mode='rb') as f:
                                data = f.read()
                            new_data = re.sub("\r?\n", "\r\n", data.decode(encoding='UTF-8'))
                            if new_data != data:
                                with open(path, mode='wb') as f:
                                    f.write(new_data.encode(encoding='UTF-8'))

        def unix_exec(self):
            """Create shell start script if on Linux"""
            if sys.platform.startswith('linux'):
                 log.info(">>> unix exec")
                 path = os.path.join(self.build_exe, '{}.sh'.format(APPNAME))
                 with open(path, mode='w') as f:
                    f.write("""#!/bin/sh
APP="{}"
EXEC="{}"
VERSION="{}"
DIRNAME=`dirname $0`
TMP="$DIRNAME#?"
if [ "$DIRNAME%$TMP" != "/" ]; then
DIRNAME=$PWD/$DIRNAME
fi
LD_LIBRARY_PATH=$DIRNAME
export LD_LIBRARY_PATH
echo "Starting $APP $VERSION ..."
$DIRNAME/$EXEC "$@"
echo "... bye!"
""".format(APPNAME, OPTS['EXEC_NAME'], VERSION))

        def chmod_exec(self):
            """Set +x flag on executable files"""
            if sys.platform.startswith('linux'):
                log.info(">>> chmod")
                for filename in [OPTS['EXEC_NAME'], '{}.sh'.format(APPNAME)]:
                    filepath = os.path.join(self.build_exe, filename)
                    st = os.stat(filepath)
                    os.chmod(filepath, st.st_mode | stat.S_IEXEC)

        def make_zip(self):
            """Create a ZIP distribution"""
            zip_file = os.path.join(self.dist_dir, '{}.zip'.format(OPTS['DIST_NAME']))
            log.info('>>> create zip {} from content of {}'.format(zip_file, self.build_exe))
            zipf = zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED)
            for root, dirs, files in os.walk(self.build_exe):
                for filename in files:
                    path = os.path.abspath(os.path.join(root, filename))
                    zipf.write(path, arcname=os.path.join(APPNAME, path[len(self.build_exe):]))
            zipf.close()

    cmdclass['build_exe'] = my_build_exe

    if sys.platform.startswith('darwin'):

        from cx_Freeze import bdist_mac
        from cx_Freeze import bdist_dmg

        class my_bdist_mac(bdist_mac):
            """
            Extends bdist_mac adding the following changes:
               - properly lookup build_exe path (using OPTS['BUILD_PATH'])
               - correctly generate Info.plist
            """
            binDir = None
            bundleDir = None
            bundle_executable = None
            contentsDir = None
            frameworksDir = None
            resourcesDir = None

            def find_qt_menu_nib(self):
                """
                Returns a location of a qt_menu.nib folder,
                or None if this is not a Qt application.
                """
                log.info(">>> searching for qt_menu.nib")

                if self.qt_menu_nib:
                    return self.qt_menu_nib

                # Qt5 library path
                base = os.path.join(str(QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.DataPath)), '..')
                file = 'Src/qtbase/src/plugins/platforms/cocoa/qt_menu.nib'
                path = os.path.join(base, file)
                if os.path.exists(path):
                    return path

                # Last resort: fixed paths (macports)
                for path in ['/opt/local/Library/Frameworks/QtGui.framework/Versions/5/Resources/qt_menu.nib']:
                    if os.path.exists(path):
                        return path

                print ("could not find qt_menu.nib")
                raise IOError("could not find qt_menu.nib")

            def run(self):
                """Command execution"""
                self.run_command('build')
                build = self.get_finalized_command('build')

                # define the paths within the application bundle
                self.bundleDir = os.path.join(build.build_base, self.bundle_name + ".app")
                self.contentsDir = os.path.join(self.bundleDir, 'Contents')
                self.resourcesDir = os.path.join(self.contentsDir, 'Resources')
                self.binDir = os.path.join(self.contentsDir, 'MacOS')
                self.frameworksDir = os.path.join(self.contentsDir, 'Frameworks')

                # find the executable name
                executable = self.distribution.executables[0].targetName
                _, self.bundle_executable = os.path.split(executable)

                # build the app directory structure
                self.mkpath(self.resourcesDir)
                self.mkpath(self.binDir)
                self.mkpath(self.frameworksDir)

                self.copy_tree(OPTS['BUILD_PATH'], self.binDir)

                # copy the icon
                if self.iconfile:
                    self.copy_file(self.iconfile, os.path.join(self.resourcesDir, 'icon.icns'))

                # copy in Frameworks
                for framework in self.include_frameworks:
                    self.copy_tree(framework, os.path.join(self.frameworksDir, os.path.basename(framework)))

                # create the Info.plist file
                self.execute(self.create_plist, ())

                # make all references to libraries relative
                self.execute(self.setRelativeReferencePaths, ())

                # for a Qt application, run some tweaks
                self.execute(self.prepare_qt_app, ())

                # sign the app bundle if a key is specified
                if self.codesign_identity:
                    signargs = ['codesign', '-s', self.codesign_identity]

                    if self.codesign_entitlements:
                        signargs.append('--entitlements')
                        signargs.append(self.codesign_entitlements)

                    if self.codesign_deep:
                        signargs.insert(1, '--deep')

                    if self.codesign_resource_rules:
                        signargs.insert(1, '--resource-rules=' + self.codesign_resource_rules)

                    signargs.append(self.bundleDir)

                    if os.spawnvp(os.P_WAIT, 'codesign', signargs) != 0:
                        raise OSError('Code signing of app bundle failed')

            def create_plist(self):
                """Create the Contents/Info.plist file"""
                import plistlib
                contents = {
                    'CFBundleName': '{} {}'.format(APPNAME, VERSION),
                    'CFBundleGetInfoString': VERSION,
                    'CFBundleShortVersionString': VERSION,
                    'CFBundleVersion': VERSION,
                    'CFBundlePackageType': 'APPL',
                    'CFBundleIconFile': 'icon.icns',
                    'CFBundleIdentifier': 'it.uniroma1.eddy',
                    'CFBundleInfoDictionaryVersion': '6.0',
                    'CFBundleDevelopmentRegion': 'English',
                    'CFBundleSpokenName': APPNAME,
                    'CFBundleExecutable': self.bundle_executable
                }

                plist = open(os.path.join(self.contentsDir, 'Info.plist'), 'wb')
                plistlib.dump(contents, plist)
                plist.close()

        class my_bdist_dmg(bdist_dmg):
            """extends bdist_dmg adding the following changes:
               - correctly package app bundle instead of app bundle content
            """
            dist_dir = None
            user_options = bdist_dmg.user_options
            user_options.extend([('dist-dir=', 'd', "directory where to put final distributions in [default: dist]")])

            bundleDir = None
            buildDir = None
            dmgName = None

            def initialize_options(self):
                self.dist_dir = None
                bdist_dmg.initialize_options(self)

            def finalize_options(self):
                if self.dist_dir is None:
                    self.dist_dir = 'dist'
                bdist_dmg.finalize_options(self)

            def buildDMG(self):
                # remove DMG if it already exists
                if os.path.exists(self.dmgName):
                    os.unlink(self.dmgName)

                tmpDir = os.path.join(self.buildDir, 'tmp')
                if os.path.exists(tmpDir):
                    dir_util.remove_tree(tmpDir, verbose=1)

                self.mkpath(tmpDir)

                # move the app bundle into a separate folder since hdutil copies in the dmg
                # the content of the folder specified in the -srcfolder folder parameter, and if we
                # specify as input the app bundle itself, its content will be copied and not the bundle
                if os.spawnvp(os.P_WAIT, 'cp', ['cp', '-R', self.bundleDir, tmpDir]):
                    raise OSError('could not move app bundle in staging directory')

                if self.applications_shortcut:
                    log.info(">>> creating /Applications shortcut")
                    if os.spawnvp(os.P_WAIT, 'ln', ['ln', '-s', '/Applications', tmpDir]):
                        raise OSError('creation of Applications shortcut failed')

                createargs = [
                    'hdiutil', 'create', '-fs', 'HFSX', '-format', 'UDBZ',
                    self.dmgName, '-imagekey', 'zlib-level=9', '-srcfolder',
                    tmpDir, '-volname', self.volume_label
                ]

                # create the dmg
                if os.spawnvp(os.P_WAIT, 'hdiutil', createargs) != 0:
                    raise OSError('creation of the dmg failed')

                # remove the temporary folder
                dir_util.remove_tree(tmpDir, verbose=1)

            def run(self):
                # create dist directory if needed
                if not os.path.isdir(self.dist_dir):
                    os.mkdir(self.dist_dir)

                # create the application bundle
                self.run_command('bdist_mac')

                # find the location of the application bundle and the build dir
                self.bundleDir = self.get_finalized_command('bdist_mac').bundleDir
                self.buildDir = self.get_finalized_command('build').build_base

                # set the file name of the DMG to be built
                self.dmgName = os.path.join(self.buildDir, OPTS['DIST_NAME'] + '.dmg')

                self.execute(self.buildDMG, ())

                # move the file into the dist directory
                self.move_file(self.dmgName, self.dist_dir)

        cmdclass['bdist_mac'] = my_bdist_mac
        cmdclass['bdist_dmg'] = my_bdist_dmg

    executables = [
        Executable(
            script='run.py',
            base='Win32GUI' if sys.platform.startswith('win32') else None,
            compress=True,
            copyDependentFiles=True,
            targetName=OPTS['EXEC_NAME'],
            icon=OPTS['EXEC_ICON'],
        )
    ]


########################################################################################################################
#                                                                                                                      #
#   SETUP                                                                                                              #
#                                                                                                                      #
########################################################################################################################


setup(
    cmdclass=cmdclass,
    name=APPNAME,
    version=VERSION,
    author="Daniele Pantaleone",
    author_email="danielepantaleone@me.com",
    description="Eddy is an editor for the Graphol ontology language.",
    long_description="Eddy is a graphical editor for the construction of Graphol ontologies. Eddy features a "
                     "design environment specifically thought out for generating Graphol ontologies through ad-hoc "
                     "functionalities. Drawing features allow designers to comfortably edit ontologies in a central "
                     "viewport area, while two lateral docking areas contains specifically-tailored widgets for "
                     "editing, navigation and inspection of the diagram. Eddy is written in [Python 3] and the GUI is "
                     "implemented through the PyQt5 bindings for the Qt5 framework. Eddy is licensed under the GNU "
                     "General Public License v3.",
    keywords = "eddy graphol sapienza",
    license=LICENSE,
    maintainer="Daniele Pantaleone",
    maintainer_email="danielepantaleone@me.com",
    url="https://github.com/danielepantaleone/eddy",
    classifiers=[
        'Development Status :: 1 - Planning',
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: MacOS X :: Cocoa',
        'Environment :: Win32 (MS Windows)'
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.4',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Utilities'
    ],
    packages=setuptools.find_packages(),
    package_data={'': [
            'styles/*.qss',
        ]
    },
    entry_points={
        'console_scripts': [
            'run = run:main',
        ]
    },
    options={
        'sdist': {
            'dist_dir': OPTS['DIST_DIR'],
        },
        'bdist_egg': {
            'dist_dir': OPTS['DIST_DIR'],
        },
        'bdist_mac': {
            'iconfile': OPTS['EXEC_ICON'],
            'bundle_name': '{} {}'.format(APPNAME, VERSION),
        },
        'bdist_dmg': {
            'dist_dir': OPTS['DIST_DIR'],
            'volume_label': '{} {}'.format(APPNAME, VERSION),
            'applications_shortcut': True,
        },
        'build_exe': {
            'dist_dir': OPTS['DIST_DIR'],
            'build_exe': OPTS['BUILD_PATH'],
            'silent': False,
            'optimize': 1,
            'compressed': True,
            'create_shared_zip': False,
            'append_script_to_exe': OPTS['APPEND_SCRIPT_TO_EXE'],
            'packages': [
                'eddy.commands',
                'eddy.dialogs',
                'eddy.functions',
                'eddy.items',
                'eddy.styles',
                'eddy.widgets',
            ],
            'excludes': ['tcl', 'ttk', 'tkinter', 'Tkinter'],
            'includes': [
                'PyQt5.QtCore',
                'PyQt5.QtGui',
                'PyQt5.QtPrintSupport',
                'PyQt5.QtWidgets',
                'PyQt5.QtXml',
            ],
            'include_files': [
                ('docs', 'docs'),
                ('examples', 'examples'),
                ('eddy/styles/light.qss', 'styles/light.qss'),
                ('LICENSE', 'LICENSE'),
                ('CONTRIBUTING.md', 'CONTRIBUTING.md'),
                ('PACKAGING.md', 'PACKAGING.md'),
                ('README.md', 'README.md'),
            ],
        }
    },
    executables=executables
)