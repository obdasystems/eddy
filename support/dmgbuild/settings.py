# -*- coding: utf-8 -*-
#
# dmgbuild settings file
#
# See https://dmgbuild.readthedocs.io/en/latest/settings.html for a list of available options.

# The application name.
appname = defines.get('appname')
appdir = defines.get('appdir', '{}.app'.format(appname))

# If defined, overrides the output filename specified on the command line.
# The command line value is the default value.
#filename =

# If defined, overrides the volume name specified on the command line,
# which is the default value.
#volume_name =

# Specifies the format code for the final output disk image.
# Must be one of the types supported by hdiutil on the build system.
# See https://dmgbuild.readthedocs.io/en/latest/settings.html#format
# for a list of supported formats.
format = defines.get('format', 'UDBZ')

# If defined, specifies the size of the filesystem within the image.
# If this is not defined, dmgbuild will attempt to determine a reasonable
# size for the image.
size = defines.get('size', None)

# A list of files (or folders) to copy into the image.
# Each of these is copied to the root of the image; folders are copied recursively.
files = defines.get('files')

# A dictionary specifying symbolic links to create in the image.
symlinks = defines.get('symlinks', {'Applications': '/Applications'})

# Specifies the path of an icon file to copy to the volume.
# Either specify this, or as an alternative use the badge_icon setting.
icon = defines.get('icon', None)

# As an alternative to the above, if you set badge_icon to the path
# of an icon file or image, it will be used to badge the system’s standard
# external disk icon.
badge_icon = defines.get('badge_icon', None)

# If arrange_by is not set, a dictionary mapping the names of items
# in the root of the volume to an (x, y) tuple specifying their location in points.
icon_locations = defines.get('icon_locations', {
    appdir: (60, 50),
    'Applications': (60, 130),
})

# A string containing the window background color,
# or the path to an image.
background = defines.get('background', None)

# The position of the window in ((x, y), (w, h)) format, with y coordinates
# running from bottom to top. Values for x and y are clamped to fit
# within the display bounds.
window_rect = defines.get('window_rect', None)

# Specifies the point size of the label text.
# Default is 16pt.
text_size = defines.get('text_size', 12)

# Specifies the size of icon to use.
# Default is 128pt.
icon_size = defines.get('icon_size', 48)

# dmgbuild can attach license text to the disk image;
# this will be displayed automatically when the user
# tries to open the disk image.
license = {
    'default-language': 'en_US',
    'licenses': {
        'en_US': defines.get('license_file', None)
    }
}
