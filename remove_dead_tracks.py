#!/usr/bin/env python -u
# ---*< clean_itunes_library.py >*---------------------------------------------
# Deletes files from iTunes library on a specific playlist
#
# Copyright (C) 2011 st0w <st0w@st0w.com>
#
# This is released under the MIT License.
"""Removes all files from disk and iTunes library on a specific playlist

Created on Feb 12, 2011

Prompts for verification before actually deleting all files

At first, I was going to iterate over the whole library and just grab
all the tracks with one star.  But that's slow on large libraries, so I
decided to keep that logic in iTunes by creating a smart playlist named
'Files to kill' that contains only files with one star.  Then I just
grab all the tracks in that playlist.  Keeps the script faster, although
it still needs to grab the entire library once to get access to the root
track object.

"""
# ---*< Standard imports >*----------------------------------------------------

# ---*< Third-party imports >*-------------------------------------------------

# ---*< Local imports >*-------------------------------------------------------
from itunes import ITunesManager

# ---*< Initialization >*------------------------------------------------------

# ---*< Code >*----------------------------------------------------------------
if __name__ == "__main__":
    itunes = ITunesManager()#IGNORE:C0103
    itunes.remove_dead_tracks()
