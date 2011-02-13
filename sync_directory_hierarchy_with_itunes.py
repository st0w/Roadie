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

"""
# ---*< Standard imports >*----------------------------------------------------
import sys

# ---*< Third-party imports >*-------------------------------------------------
from appscript import k, CommandError

# ---*< Local imports >*-------------------------------------------------------
from itunes import ITunesManager

# ---*< Initialization >*------------------------------------------------------
DEFAULT_DIR = '/srv/multimedia/Music'

# ---*< Code >*----------------------------------------------------------------

def sync_dir(dirname, recursive=True):
    """Synchronizes a directory hierarchy with iTunes
    
    :param dirname: `string` of the root directory
    :param recursive: `bool` whether or not to recursively sync
    """
    itunes = ITunesManager()#IGNORE:C0103
    tracks = itunes.get_all_tracks()
#    tracks()[0].location()
#    print t.size()
    files = []
    i = 0
    count = len(tracks)

    print "Removing dead tracks"
    itunes.remove_dead_tracks()

    for t in tracks:
        i += 1
        sys.stderr.write('\rProcessing %s/%s' % (i, count))
        try:
            if t.location() != k.missing_value:
                files.append(t.location().path)
        except CommandError as e:
#            print t.name()
            sys.stderr.write('\nOops... Error getting location for %s: %s\n' %
                             (t.name(), str(e)))


    print "\n%s" % dirname
    print len(files)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        sync_dir(sys.argv[1])
    else:
        sync_dir(DEFAULT_DIR)
