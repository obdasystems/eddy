# -*- mode: python -*-

"""
Runtime hook used to set the FONTCONFIG_PATH on Linux.

During the analysis phase we add the fontconfig configuration
of the local machine and bundle them with the application.
This fixes the splash screen not showing and other font-related
problems when running on distrubutions that provide a more
recent version of fontconfig.
"""

import os
import sys

if sys.platform.startswith('linux'):
    # Set FONTCONFIG_PATH environment variable so that
    # fontconfig loads the bundled configuration.
    os.environ['FONTCONFIG_PATH'] = sys._MEIPASS + '/etc/fonts'