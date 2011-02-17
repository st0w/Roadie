#!/usr/bin/env python -u
# ---*< sync_directory_hierarchy_with_itunes.py >*-----------------------------
# Adds files 
#
# Copyright (C) 2011 st0w <st0w@st0w.com>
#
# This is released under the MIT License.
"""Adds all files to iTunes that aren't already in library.

Created on Feb 12, 2011

Note that this only looks at the actual filename/path.  It doesn't check
for duplicate status or anything like that.  Just finds files below a
given directory and adds them to iTunes.

Certain files are excluded based upon their extension.  Change the
definition of IGNORE_EXTENSIONS to alter this.

If you have a lot of files to add.... this take a LOONNNNNNNGGGG time.
But it works.  I used it to add over 8,000 missing files to my library,
and while it ran for the better part of maybe 36 hours, it did 
eventually complete successfully.

Thoughts for the future:
  * Possibly add ability to use locate db instead of find.  Would have
    to check age of locate DB.  Maybe we store last run locate db 
    date/time and warn of need to use find if locate db hasn't been 
    updated?

"""
# ---*< Standard imports >*----------------------------------------------------
import os
import re
import sys

# ---*< Third-party imports >*-------------------------------------------------
from appscript import k, CommandError
from mactypes import Alias

# ---*< Local imports >*-------------------------------------------------------
from itunes import ITunesManager, smart_str

# ---*< Initialization >*------------------------------------------------------
DEFAULT_DIR = '/srv/multimedia/Music'
EXCLUDE_DIRS = ['/srv/multimedia/Music/Production',
                '/srv/multimedia/Music/iTunes/Previous iTunes Libraries',
                ]
IGNORE_EXTENSIONS = re.compile('^.+\.('
                               '(accurip)'
                               '|(asd)'
                               '|(avi)'
                               '|(cue)'
                               '|(dctmp)'
                               '|(dmg)'
                               '|(dylib)'
                               '|(epub)'
                               '|(exe)'
                               '|(flac)'
                               '|(gif)'
                               '|(gz)'
                               '|(htm)'
                               '|(html)'
                               '|(ipa)'
                               '|(iso)'
                               '|(itc)'
                               '|(itdb)'
                               '|(jpeg)'
                               '|(jpg)'
                               '|(log)'
                               '|(m3u)'
                               '|(m4v)'
                               '|(md5)'
                               '|(mov)'
                               '|(nfo)'
                               '|(pls)'
                               '|(rar)'
                               '|(r\d\d)'
                               '|(rtf)'
                               '|(sfv)'
                               '|(pdf)'
                               '|(plist)'
                               '|(png)'
                               '|(rss)'
                               '|(so)'
                               '|(tgz)'
                               '|(tif)'
                               '|(tiff)'
                               '|(tmp)'
                               '|(torrent)'
                               '|(txt)'
                               '|(url)'
                               '|(xml)'
                               '|(zip)'
                               ')$', re.IGNORECASE)
INCLUDE_EXTENSIONS = re.compile('^.+\.('
                               '(m4a)|(m4p)|(mp2)|(mp3)|(mp4)|(wav)'
                               ')$', re.IGNORECASE)

# ---*< Code >*----------------------------------------------------------------

def sync_dir(dirname):
    """Recursively synchronizes a directory hierarchy with iTunes
    
    :param dirname: `string` of the root directory
    """
    itunes = ITunesManager()#IGNORE:C0103
    tracks = itunes.get_all_tracks()

    itunes_files = []
    new_files = []
#    unused_new_files = []
    i = 0
    count = len(tracks)

    """Now traverse the desired file hierarchy and add files"""
    sys.stdout.write("Walking dir tree(s)...")
    for root, dirs, files in os.walk(dirname):
        skipping = False
        for skipdir in EXCLUDE_DIRS:
            if root.find(skipdir) == 0:
                skipping = True

        if skipping:
            continue

        if '.DS_Store' in files:
            files.remove('.DS_Store')

#        """This will add files using a blacklist - every extension not
#        in the IGNORE_EXTENSIONS regex
#        """ 
#        unused_new_files += ['%s/%s' % (root, f) for f in files if not
#                      re.match(IGNORE_EXTENSIONS, f)]

        """This adds files using a whitelist - only known extensions set
        in the INCLUDE_EXTENSIONS regex
        """
        new_files += ['%s/%s' % (root, f) for f in files if
                      re.match(INCLUDE_EXTENSIONS, f)]

    sys.stdout.write("done.  Identified %d files.\n" % len(new_files))
#    print len(new_files)
#    print new_files
#    for f in new_files:
##        if not re.match(INCLUDE_EXTENSIONS, f):
#        print f
#    sys.exit(0)


    """Build a list containing full paths to all files in iTunes library"""
    sys.stdout.write("Examining existing iTunes Library...\n")
    for t in tracks:
        i += 1
        sys.stderr.write('\rProcessing %s/%s' % (i, count))
        try:
            if t.location() != k.missing_value:
                itunes_files.append(t.location().path)
        except CommandError as e:
#            print t.name()
            sys.stderr.write('\nOops... Error getting location for %s: %s\n' %
                             (t.name(), str(e)))

    sys.stdout.write("\nDone.  Now removing existing entries from list of "
                     "files to add...\n")

    """I thought about the best way to preen the results, analyzing the
    two lists and such.  Then I decided that more often than not, the
    hierarchy would contain more files than the iTunes library.  The
    assumption being, the script is being run to sync the new files in
    the hierarchy and thus includes all of the iTunes library plus more.
    
    Note that I just try to remove it and then catch any exceptions...
    rather than doing a lookup and only removing existing elements.  I
    don't know for sure if this is faster, but, it seems like it would be.  
    """
    for f in itunes_files:
        try:
            new_files.remove(f)
        except ValueError:
            pass

    sys.stdout.write('Post processing, preparing to add %d new files to '
                     'existing library of %d files...\n'
                     % (len(new_files), len(itunes_files)))

    """This is where the files are actually added to iTunes
    
    With a large import... this is SSLLLLLOOOOOOWWWWWWW... First tried
    to add one at a time, but that came to a grinding halt around 100.
    Then tried all at once, and that resulted in a timeout.
    """
    aliases = []
    for f in new_files:
#        itunes.itunes.add(Alias(f))
        try:
            aliases.append(Alias(smart_str(f)))
        except UnicodeDecodeError:
            sys.stderr.write('Error trying to Alias/append %s\n' % smart_str(f))

    sys.stdout.write('Now adding %d files to iTunes library...' % len(aliases))
    try:
        itunes.itunes.add(aliases)
    except CommandError as e:
        sys.stderr.write('Warning: An error occurred trying to add the files.'
                         '\nPlease note that if the error is "Apple event '
                         'timed out" that iTunes may very well still be '
                         '\nprocessing.  Continue to check iTunes and see if '
                         'this is the case.  If all your files are added, the '
                         '\nerror can be safely ignored.\n%s' % str(e))

    sys.stdout.write('Done.\n')


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sync_dir(sys.argv[1])
    else:
        sync_dir(DEFAULT_DIR)
