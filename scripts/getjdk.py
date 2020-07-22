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

"""Utility script to download a JRE from adoptopenjdk.net."""


import argparse
import json
import logging
import platform
import sys
import urllib.request

API_ENDPOINT = 'https://api.adoptopenjdk.net/v2'
ARCH = platform.machine()
IS_64BIT = sys.maxsize > 2**32
IS_CROSS = False
IS_FREEBSD = sys.platform.startswith('freebsd')
IS_LINUX = sys.platform.startswith('linux')
IS_MACOS = sys.platform.startswith('darwing')
IS_WIN = sys.platform.startswith('win') or sys.platform.startswith('cygwin')
USER_AGENT='curl/7.66.0'

LOGGER = logging.getLogger('getjdk')
LOGGER.setLevel(logging.DEBUG)
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s'))
LOGGER.addHandler(_handler)


def param_arch(sysarch):
    """
    Returns the architecture's identifier string suitable for requests to api.adoptopenjdk.net.
    :type sysarch: str
    :rtype: str
    """
    return {
        'i386': 'x86',
        'i486': 'x86',
        'i586': 'x86',
        'i686': 'x86',
        'amd64': 'x64',
        'x86_64': 'x64',
        'armvhf': 'arm',
        'armv6l': 'arm',
        'armv7l': 'arm',
        'armv8l': 'arm',
    }.get(sysarch, sysarch)


def param_os(osname):
    """
    Returns the os name suitable for requests to api.adoptopenjdk.net.
    :type osname: str
    :rtype: str
    """
    if osname.startswith('aix'):
        return 'aix'
    elif osname.startswith('darwin'):
        return 'mac'
    elif osname.startswith('linux'):
        return 'linux'
    elif osname.startswith('solaris'):
        return 'solaris'
    elif osname.startswith('win'):
        return 'windows'
    else:
        return osname


def main(args):
    """
    Entry point.
    :type args: list
    """
    # PARSE COMMAND LINE ARGUMENTS
    parser = argparse.ArgumentParser(
        description='Client to interact with api.adoptopenjdk.net.',
        epilog='example {} TODO')
    # MAIN QUERY PARAMETERS
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--binary', action='store_true',
        help='Download the JDK binary that matches the specified parameters.')
    group.add_argument(
        '--info', action='store_true',
        help='Query info about available JDKs matching the specified parameters.')
    group.add_argument(
        '--assets', action='store_true',
        help='Query for latest assets that match the specified parameters.')
    # QUERY PARAMETERS
    parser.add_argument('--arch', help='Query for the specified cpu architecture.')
    parser.add_argument('--heap-size', help='Heap size.')
    parser.add_argument('--impl', help='JVM implementation (e.g. hotspot).')
    parser.add_argument('--jdkver', required=True, help='The JDK version to query for (e.g. openjdk11)')
    parser.add_argument('--type', choices=('jdk', 'jre'), help='Query for binary type (default jdk).')
    parser.add_argument('--nightly', action='store_true', help='Query for nightly builds instead of releases.')
    parser.add_argument('--os', help='Query for the specified os (defaults to the current os).')
    parser.add_argument('--output-file', type=argparse.FileType('w'), help='The file name to use for output.')
    parser.add_argument('--release', help='Query for the specified release (defaults to latest).')
    options = parser.parse_args(args)

    # PROCESS REQUEST
    if options.binary:
        request_type = 'binary'
    elif options.assets:
        request_type = 'latestAssets'
    elif options.info:
        request_type = 'info'
    else:
        LOGGER.error('Unknown request type')
        return 2

    # BUILD REQUEST OBJECT
    url = '{}/{}/{}/{}'.format(
        API_ENDPOINT,
        'latestAssets',
        'releases' if not options.nightly else 'nightly',
        options.jdkver
    )
    params = list(filter(lambda param: param, [
        'openjdk_impl={}'.format(options.impl) if options.impl else '',
        'os={}'.format(param_os(options.os)) if options.os else '',
        'arch={}'.format(param_arch(options.arch)) if options.arch else '',
        'type={}'.format(options.type) if options.type else '',
        'release={}'.format(options.release) if options.release else '',
    ]))
    if len(params) > 0:
        url = '{}?{}'.format(url, '&'.join(params))
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})

    # PERFORM REQUEST
    try:
        LOGGER.info('API request: %s', url)
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read())
            LOGGER.debug('Response: \n%s', json.dumps(data, indent=2))
            if options.binary:
                if len(data) == 0:
                    LOGGER.error('No binaries for current selection, exiting...')
                    return 4
                elif len(data) > 1:
                    LOGGER.warning('Multiple binaries for current selection, downloading latest...')
                binary_link = data[0]['binary_link']
                binary_name = data[0]['binary_name']
                LOGGER.info('Downloading %s', binary_name)
                urllib.request.urlretrieve(binary_link, binary_name)
    except Exception as e:
        LOGGER.exception('Error during request: %s', e)
    else:
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(1)
