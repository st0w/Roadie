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
    t = itunes.itunes.tracks()[0]
    print t.size()

    print dirname

if __name__ == "__main__":
    if len(sys.argv) > 1:
        sync_dir(sys.argv[1])
    else:
        sync_dir(DEFAULT_DIR)
