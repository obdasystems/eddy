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


import distutils
import os
import platform
import subprocess
import sys
import setuptools

from eddy import APPNAME, APPID, BUG_TRACKER, COPYRIGHT
from eddy import GRAPHOL_HOME, LICENSE, ORGANIZATION_URL
from eddy import ORGANIZATION, PROJECT_HOME, VERSION
from eddy.core.functions.fsystem import fexists, isdir
from eddy.core.functions.fsystem import rmdir
from eddy.core.functions.path import expandPath

###################################
# SETUP CONSTANTS DECLARATION
###########################

LINUX = sys.platform.startswith('linux')
MACOS = sys.platform.startswith('darwin')
WIN32 = sys.platform.startswith('win32')

EXEC_ARCH = None
EXEC_NAME = None

if LINUX:
    EXEC_ARCH = platform.machine().lower()
    EXEC_NAME = APPNAME

if MACOS:
    EXEC_ARCH = platform.machine().lower()
    EXEC_NAME = APPNAME

if WIN32:
    # On Windows use the PROCESSOR_ARCHITECTURE environment variable to detect if we
    # are running a 32-bit or 64-bit version of Python
    EXEC_ARCH = os.environ['PROCESSOR_ARCHITECTURE'].lower() if 'PROCESSOR_ARCHITECTURE' in os.environ else platform.machine().lower()
    EXEC_NAME = '%s.exe' % APPNAME

SPEC_FILE = os.path.join(expandPath(os.path.dirname(__file__)), '%s.spec' % APPNAME.lower())
BUILD_DIR = os.path.join(expandPath(os.path.dirname(__file__)), 'build')
DIST_DIR = os.path.join(expandPath(os.path.dirname(__file__)), 'dist')
DIST_NAME = '%s-%s-%s_%s' % (APPNAME, VERSION, platform.system().lower(), EXEC_ARCH)
DIST_PATH = BUILD_DIR
WORK_PATH = BUILD_DIR

###################################
# CUSTOM COMMANDS IMPLEMENTATION
###########################

cmdclass = {}


# noinspection PyAttributeOutsideInit
class CleanCommand(setuptools.Command):
    """
    Custom clean command to tidy up the project root.
    """
    description = "clean up temporary files from 'build' command"
    user_options = []

    def initialize_options(self):
        """Initialize command options."""
        pass

    def finalize_options(self):
        """Finalize command options."""
        pass

    def run(self):
        """Command execution."""
        rmdir(BUILD_DIR)
        rmdir(DIST_DIR)


cmdclass['clean'] = CleanCommand


# noinspection PyAttributeOutsideInit
class PyInstallerCommand(setuptools.Command):
    """
    Custom command to execute PyInstaller.
    """
    description = 'freeze the application using PyInstaller.'
    user_options = [
        ('workpath=', None,
         'where to put all the temporary work files (default: %s)' % os.path.relpath(WORK_PATH)),
        ('distpath=', None,
         'where to put the bundled app (default: %s)' % os.path.relpath(DIST_PATH)),
        ('specfile=', None,
         'name of the .spec file to use (default: %s)' % os.path.relpath(SPEC_FILE))
    ]

    def initialize_options(self):
        """Set default values for options."""
        self.workpath = None
        self.distpath = None
        self.specfile = None

    def finalize_options(self):
        """Finalize values for options."""
        if self.workpath is None:
            self.workpath = WORK_PATH
        if self.distpath is None:
            self.distpath = DIST_PATH
        if self.specfile is None:
            self.specfile = SPEC_FILE

    def post_install(self):
        """Perform post-install tasks."""
        # We rename OpenSSL libraries on Linux builds so that
        # Qt will pick the bundled one instead of those provided by the system
        # which may be using OpenSSL 1.1.
        # This issue seems to affect all binary releases of PyQt5 from PyPI
        # for version 5.11 and 5.12.
        # See: https://bugreports.qt.io/browse/QTBUG-68156
        build_dir = os.path.abspath(os.path.join(self.workpath, DIST_NAME))
        for lib in os.listdir(build_dir):
            if lib.startswith('libssl.so.1.0'):
                os.rename(os.path.join(build_dir, lib), os.path.join(build_dir, 'libssl.so'))
            elif lib.startswith('libcrypto.so.1.0'):
                os.rename(os.path.join(build_dir, lib), os.path.join(build_dir, 'libcrypto.so'))

    def run(self):
        """Command execution."""
        command = ['pyinstaller']
        if self.workpath:
            command.extend(['--workpath', '%s' % self.workpath])
        if self.distpath:
            command.extend(['--distpath', '%s' % self.distpath])
        command.extend(['--noconfirm', '--clean', self.specfile])
        distutils.log.info('Running PyInstaller: %s' % ' '.join(command))
        if not self.dry_run:
            subprocess.check_call(command)
        if LINUX:
            self.execute(self.post_install, (), msg='Performing post-install tasks...')


cmdclass['pyinstaller'] = PyInstallerCommand


# noinspection PyAttributeOutsideInit
class StandaloneCommand(setuptools.Command):
    """
    Create a standalone distribution archive using the given format.
    """
    description = 'create a standalone distribution archive (tarball, zip file, etc.)'
    user_options = PyInstallerCommand.user_options
    user_options.extend([
        ('dist-dir=', 'd',
         'where to put the built distribution archive (default: %s)' % os.path.relpath(DIST_DIR)),
        ('format=', 'f',
         'archive format to create (tar, gztar, bztar, xztar, ztar, zip)'),
        ('skip-build', None,
         'skip rebuilding everything (for testing/debugging)'),
        ('owner=', 'u',
         'owner name used when creating a tar file (default: current user)'),
        ('group=', 'g',
         'group name used when creating a tar file (default: current group)'),
    ])
    boolean_options = ['skip-build']

    # Default format by platform
    default_format = {'posix': 'gztar', 'nt': 'zip'}

    def initialize_options(self):
        """Set default values for options."""
        self.workpath = None
        self.distpath = None
        self.dist_dir = None
        self.format = None
        self.skip_build = 0
        self.owner = None
        self.group = None

    def finalize_options(self):
        """Finalize values for options."""
        if self.workpath is None:
            self.workpath = WORK_PATH
        if self.distpath is None:
            self.distpath = DIST_PATH
        if self.dist_dir is None:
            self.dist_dir = DIST_DIR
        if self.format is None:
            try:
                self.format = self.default_format[os.name]
            except KeyError:
                raise distutils.errors.DistutilsPlatformError(
                    "don't know how to create archive distribution on platform %s" % os.name)

    def run(self):
        """Run command."""
        if not self.skip_build:
            pyinstaller = self.reinitialize_command('pyinstaller', reinit_subcommands=1)
            pyinstaller.dry_run = self.dry_run
            pyinstaller.workpath = self.workpath
            pyinstaller.distpath = self.distpath
            self.run_command('pyinstaller')
        # Create the archive
        self.make_archive(os.path.join(self.dist_dir, DIST_NAME), self.format,
                          base_dir=DIST_NAME, root_dir=self.distpath,
                          owner=self.owner, group=self.group)


cmdclass['standalone'] = StandaloneCommand

if WIN32:
    # noinspection PyAttributeOutsideInit
    class InnosetupCommand(setuptools.Command):
        """
        Generate a Windows installer using InnoSetup.
        """
        description = 'create a MS Windows installer using InnoSetup'
        user_options = PyInstallerCommand.user_options
        user_options.extend([
            ('dist-dir=', 'd',
             'where to store the generated installer (default: %s)' % os.path.relpath(DIST_DIR)),
            ('skip-build', None,
             'skip rebuilding everything (for testing/debugging)'),
        ])
        boolean_options = ['skip-build']

        def initialize_options(self):
            """Set default values for options."""
            self.workpath = None
            self.distpath = None
            self.dist_dir = None
            self.skip_build = 0

        def finalize_options(self):
            """Finalize values for options."""
            if self.workpath is None:
                self.workpath = WORK_PATH
            if self.distpath is None:
                self.distpath = DIST_PATH
            if self.dist_dir is None:
                self.dist_dir = DIST_DIR
            if self.skip_build is None:
                self.skip_build = 0

        def run(self):
            """Command execution."""
            if not self.skip_build:
                pyinstaller = self.reinitialize_command('pyinstaller', reinit_subcommands=1)
                pyinstaller.dry_run = self.dry_run
                pyinstaller.workpath = self.workpath
                pyinstaller.distpath = self.distpath
                self.run_command('pyinstaller')
            self.mkpath(self.dist_dir)
            self.execute(self.make_installer, (), msg='Creating InnoSetup installer...')

        def make_installer(self):
            """Create a Windows installer using InnoSetup."""
            import yaml

            with open(os.path.join('support', 'innosetup', 'build.yaml'), 'r') as f:
                config = yaml.safe_load(f)
            if 'scripts' not in config:
                print("ERROR: invalid config file: could not find 'scripts' section")
                sys.exit(1)
            if not len(config['scripts']):
                print("ERROR: invalid config file: no entry found in 'scripts' section")
                sys.exit(1)

            # Location of the InnoSetup Compiler program taken from environment.
            config['iscc'] = os.environ.get('ISCC_EXE', config['iscc'])

            if 'iscc' not in config:
                print("ERROR: invalid config file: could not find 'iscc' entry")
                sys.exit(1)
            if not config['iscc'].lower().endswith('iscc.exe'):
                print("ERROR: invalid location for the ISCC.exe program: %s" % config['iscc'])
                sys.exit(1)
            if not fexists(os.path.join('support', 'innosetup', config['iscc'])):
                print("ERROR: invalid config file: '%s' is not a file" % config['iscc'])
                sys.exit(1)

            # Disable installation of 64 bit executables on 32 bit Windows
            architecturesAllowed = 'x64' if platform.architecture()[0] == '64bit' else ''

            # Build each given innosetup script
            for filename in config['scripts']:
                script_file = os.path.join('support', 'innosetup', filename)
                distutils.log.info("building: %s" % script_file)

                try:
                    cmd = [
                        config['iscc'],
                        script_file,
                        '/Q',
                        '/O{0}'.format(self.dist_dir),
                        '/dEDDY_APPID={0}'.format(APPID),
                        '/dEDDY_APPNAME={0}'.format(APPNAME),
                        '/dEDDY_ARCHITECTURE={0}'.format(EXEC_ARCH),
                        '/dEDDY_ARCHITECTURES_ALLOWED={0}'.format(architecturesAllowed),
                        '/dEDDY_BUGTRACKER={0}'.format(BUG_TRACKER),
                        '/dEDDY_BUILD_PATH={0}'.format(os.path.join(self.distpath, DIST_NAME)),
                        '/dEDDY_COPYRIGHT={0}'.format(COPYRIGHT),
                        '/dEDDY_DOWNLOAD_URL={0}'.format(GRAPHOL_HOME),
                        '/dEDDY_EXECUTABLE={0}'.format(EXEC_NAME),
                        '/dEDDY_GRAPHOL_URL={0}'.format(GRAPHOL_HOME),
                        '/dEDDY_LICENSE={0}'.format(LICENSE.lower()),
                        '/dEDDY_ORGANIZATION={0}'.format(ORGANIZATION),
                        '/dEDDY_ORGANIZATION_URL={0}'.format(ORGANIZATION_URL),
                        '/dEDDY_PROJECT_HOME={0}'.format(PROJECT_HOME),
                        '/dEDDY_VERSION={0}'.format(VERSION),
                    ]
                    subprocess.call(cmd)
                except Exception as e:
                    distutils.log.error('Failed to build {0}: {1}'.format(script_file, e))

    cmdclass['innosetup'] = InnosetupCommand

if MACOS:
    # noinspection PyAttributeOutsideInit
    class CreateDmgCommand(setuptools.Command):
        """
        Create a macOS distributable disk image (.dmg).
        """
        description = "create a Mac DMG disk image containing the Mac application bundle"
        user_options = PyInstallerCommand.user_options
        user_options.extend([
            ('dist-dir=', 'd',
             'where to put the generated disk image (default: %s)' % os.path.relpath(DIST_DIR)),
            ('skip-build', None,
             'skip rebuilding everything (for testing/debugging)'),
            ('applications-shortcut=', None,
             'whether to include shortcut to Applications in the disk image'),
            ('volume-background=', None,
             'the path to use as background of the generated volume'),
            ('volume-icon=', None,
             'the icon for the generated volume'),
            ('volume-label=', None,
             'the disk image volume label'),
        ])
        boolean_options = ['skip-build', 'applications-shortcut']

        def initialize_options(self):
            """Initialize command options."""
            self.workpath = None
            self.distpath = None
            self.dist_dir = None
            self.skip_build = 0
            self.applications_shortcut = 1
            self.volume_background = None
            self.volume_icon = None
            self.volume_label = None

        def finalize_options(self):
            """Finalize command options."""
            if self.workpath is None:
                self.workpath = WORK_PATH
            if self.distpath is None:
                self.distpath = DIST_PATH
            if self.dist_dir is None:
                self.dist_dir = DIST_DIR
            if self.applications_shortcut is None:
                self.applications_shortcut = 1
            if self.volume_label is None:
                self.volume_label = '%s %s' % (APPNAME, VERSION)
            if self.volume_background is None:
                self.volume_background = expandPath('@resources/images/macos_background_dmg.png')
            if self.volume_icon is None:
                self.volume_icon = expandPath('@resources/images/macos_icon_dmg.icns')
            if self.skip_build is None:
                self.skip_build = 0

        def buildDmg(self):
            """Build the DMG image."""
            try:
                import dmgbuild
            except ImportError:
                raise OSError('Unable to import dmgbuild: please install the dmgbuild package.')

            if fexists(self.dmgName):
                os.unlink(self.dmgName)

            defines = {
                'appname': APPNAME,
                'files': [self.bundleDir],
                'license_file': expandPath('@root/LICENSE'),
                'icon_locations': {'{}.app'.format(APPNAME): (60, 50)},
            }

            if self.applications_shortcut:
                defines['symlinks'] = {'Applications': '/Applications'}
                defines['icon_locations']['Applications'] = (60, 130)

            if self.volume_background:
                if not fexists(self.volume_background):
                    raise OSError('DMG volume background image not found at {0}'
                                  .format(self.volume_background))
                print('Using DMG volume background: {0}'.format(self.volume_background))
                from PIL import Image
                w, h = Image.open(self.volume_background).size
                defines['background'] = self.volume_background
                defines['window_rect'] = ((100, 500), (str(w), (str(h))))

            if self.volume_icon:
                if not fexists(self.volume_icon):
                    raise OSError('DMG volume icon not found at {0}'.format(self.volume_icon))
                print('Using DMG volume icon: {0}'.format(self.volume_icon))
                defines['icon'] = self.volume_icon

            # Create the disk image using dmgbuild package.
            dmgbuild.build_dmg(
                self.dmgName,
                self.volume_label,
                settings_file=expandPath('@support/dmgbuild/settings.py'),
                defines=defines,
            )

        def run(self):
            """Command execution."""
            if not self.skip_build:
                pyinstaller = self.reinitialize_command('pyinstaller', reinit_subcommands=1)
                pyinstaller.dry_run = self.dry_run
                pyinstaller.workpath = self.workpath
                pyinstaller.distpath = self.distpath
                self.run_command('pyinstaller')
            self.bundleName = APPNAME
            self.bundleDir = os.path.join(self.distpath, self.bundleName + ".app")
            self.buildDir = self.workpath
            self.dmgName = os.path.join(self.buildDir, DIST_NAME + '.dmg')
            self.execute(self.buildDmg, (), msg='Building disk image...')
            self.mkpath(self.dist_dir)
            self.move_file(self.dmgName, self.dist_dir)

    cmdclass['createdmg'] = CreateDmgCommand

if LINUX:
    # noinspection PyAttributeOutsideInit
    class AppImageCommand(setuptools.Command):
        """
        Generate a Linux AppImage using appimage-builder.
        """
        description = 'create a Linux AppImage using appimage-builder'
        user_options = PyInstallerCommand.user_options
        user_options.extend([
            ('dist-dir=', None,
             'where to store the generated AppImage (default: %s)' % os.path.relpath(DIST_DIR)),
            ('skip-build', None,
             'skip rebuilding the AppDir'),
            ('skip-appimage', None,
             'skip building the final AppImage'),
            ('skip-tests', None,
             'skip testing the AppImage'),
        ])
        boolean_options = ['skip-build', 'skip-tests', 'skip-appimage']

        def initialize_options(self):
            """Set default values for options."""
            self.workpath = None
            self.distpath = None
            self.dist_dir = None
            self.skip_appimage = None
            self.skip_build = None
            self.skip_tests = None

        def finalize_options(self):
            """Finalize values for options."""
            if self.workpath is None:
                self.workpath = WORK_PATH
            if self.distpath is None:
                self.distpath = DIST_PATH
            if self.dist_dir is None:
                self.dist_dir = DIST_DIR
            if self.skip_build is None:
                self.skip_build = 0
            if self.skip_appimage is None:
                self.skip_appimage = 0
            if self.skip_tests is None:
                self.skip_tests = 0

        def run(self):
            """Command execution."""
            self.appImageName = '{}-{}-{}.AppImage'.format(APPNAME, VERSION, EXEC_ARCH)
            self.mkpath(self.dist_dir)
            self.execute(self.build_appimage, (), msg='Creating AppImage...')
            if fexists(self.appImageName):
                self.move_file(self.appImageName,
                               os.path.join(self.dist_dir, DIST_NAME + '.AppImage'))

        def build_appimage(self):
            """Create a Linux AppImage using appimage-builder."""
            import shutil

            # Check that appimage-builder is installed
            if not shutil.which('appimage-builder'):
                print("ERROR: unable to locate appimage-builder executable in PATH.\n"
                      "  please install packaging requirements.")
                sys.exit(1)
            # Check that appimagetool is installed
            if not shutil.which('appimagetool'):
                print("ERROR: unable to locate appimagetool executable in PATH.\n"
                      "  refer to https://appimage.github.io/appimagetool for instructions\n"
                      "  on how to install it.")
                sys.exit(1)
            # Check that apt-get is available, appimage-builder needs it
            if not shutil.which('apt-get'):
                print("ERROR: unable to locate apt-get executable in PATH.\n"
                      "  appimage-builder currently needs to be run on a Debian-based distro\n"
                      "  in order to build the AppDir folder.")
                sys.exit(1)

            # Run appimage-builder with appropriate variables
            cmd = [
                shutil.which('appimage-builder'),
                '--recipe', os.path.join('support', 'appimage', 'AppImageBuilder.yml'),
            ]
            if self.skip_appimage:
                cmd.append('--skip-appimage')
            if self.skip_build:
                cmd.extend(['--skip-script', '--skip-build'])
            if self.skip_tests:
                cmd.append('--skip-tests')
            try:
                subprocess.call(cmd, env={**os.environ, **{
                    'EDDY_APPIMAGE_ID': APPNAME,
                    'EDDY_APPIMAGE_ICON': APPNAME.lower(),
                    'EDDY_APPIMAGE_NAME': APPNAME,
                    'EDDY_APPIMAGE_VERSION': VERSION,
                }})
            except Exception as e:
                distutils.log.error('Failed to build AppImage: {}'.format(e))

    cmdclass['appimage'] = AppImageCommand

#############################################
# SETUP
#################################

setuptools.setup(
    cmdclass=cmdclass,
    name=APPNAME,
    version=VERSION,
    author="Daniele Pantaleone",
    author_email="pantaleone@dis.uniroma1.it",
    maintainer="Manuel Namici",
    maintainer_email="namici@diag.uniroma1.it",
    description="Eddy is a graphical editor for the specification and visualization of Graphol ontologies.",
    long_description="Eddy is a graphical editor for the construction of Graphol ontologies. Eddy features a "
                     "design environment specifically thought out for generating Graphol ontologies through ad-hoc "
                     "functionalities. Drawing features allow designers to comfortably edit ontologies in a central "
                     "viewport area, while lateral docking areas contains specifically-tailored widgets for "
                     "editing, navigation and inspection of the diagram. Eddy is written in [Python 3] and the UI is "
                     "implemented through the PyQt5 bindings for the Qt5 framework. Eddy is licensed under the GNU "
                     "General Public License v3.",
    keywords = "eddy graphol sapienza",
    license=LICENSE,
    url="https://github.com/obdasystems/eddy",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: MacOS X :: Cocoa',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: BSD',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Utilities',
    ],
    python_requires='>=3.9',
    install_requires=[
        'jpype1>=1.4.1',
        'rdflib>=6.2.0',
        'rfc3987',
        'openpyxl',
    ],
    packages=setuptools.find_packages(exclude=['tests', 'scripts', 'support']),
    include_package_data=True,
    entry_points={
        'gui_scripts': [
            'eddy = eddy.core.application:main'
        ]
    },
    zip_safe=False
)
