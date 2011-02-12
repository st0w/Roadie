#!/usr/bin/env python -u
# ---*< clean_itunes_library.py >*---------------------------------------------
# Deletes files from iTunes library and disk with one star
#
# Copyright (C) 2011 st0w <st0w@st0w.com>
#
# This is released under the MIT License.
"""Removes all files from disk and iTunes library with one-star rating

Created on Feb 12, 2011

Prompts for verification before actually deleting all files

At first, I was going to iterate over the whole library and just grab
all the tracks with one star.  But that's slow on large libraries, so I
decided to keep that logic in iTunes by creating a smart playlist named
'Files to kill' that contains only files with one star.  Then I just
grab all the tracks in that playlist.  Keeps the script faster, although
it still needs to grab the entire library once to get access to the root
track object.

--> BE CAREFUL WITH THIS!!!! <--

Note that I don't prompt for verification before each file.  I make no
warranty or guarantee that this won't completely destroy your entire
library.  USE AT YOUR OWN RISK!

Overall steps
    * Connect to iTunes
    * Get list of all files with one star
    * Present list of files, get verification (allow toggling by number/
      range)
    * Display amount of disk space to be reclaimed
    * Remove files from iTunes library w/ progress indicator
    * Upon success, delete files that have been selected

"""
# ---*< Standard imports >*----------------------------------------------------
import os
import sys

# ---*< Third-party imports >*-------------------------------------------------
from appscript import app, k, CommandError #@UnresolvedImport

# ---*< Local imports >*-------------------------------------------------------

# ---*< Initialization >*------------------------------------------------------
"""The name of the playlist of files to kill.  Any type of playlist."""
PLAYLIST_NAME = 'Files to kill'

"""Unbuffer stdout"""


# ---*< Code >*----------------------------------------------------------------
class ITunesManager(object):
    """Handles connecting to and sending operations to iTunes
    """
    itunes = None

    def __init__(self):
        """__init__ method.  Takes no options."""
        self._connect_to_itunes()
        super(ITunesManager, self).__init__()

    def _connect_to_itunes(self):
        """Establishes a connection to iTunes.  You won't need to use this."""
        if not self.itunes:
            self.itunes = app('iTunes')
        else:
            print "already connected to iTunes"

    def get_tracks_from_playlist(self, playlist=PLAYLIST_NAME):
        """Returns a list of all the tracks in a given playlist
        
        :param playlist: (optional) :string:name of playlist to use as
                         source of files to delete
        
        """

        if not self.itunes.exists(self.itunes.user_playlists[playlist]):
            raise ValueError('Playlist %s does not exist.' % playlist)

        sys.stdout.write('Obtaining playlist of files to kill...')
        tracks = self.itunes.user_playlists[playlist].tracks()
        track_ids = [t.persistent_ID() for t in tracks]
        sys.stdout.write('done\n')

        if len(tracks) <= 0:
            sys.stdout.write('''Playlist '%s' is empty! Don't be silly.\n''' %
                             playlist)
            return []

        sys.stdout.write('Obtaining copy of iTunes library...')
        library_tracks = self.itunes.tracks()
        sys.stdout.write('done\n')

        tracks_to_kill = []

        sys.stdout.write('Building list of tracks from playlist...')
        for t in library_tracks:
            if t.persistent_ID() in track_ids:
                tracks_to_kill.append(t)
        sys.stdout.write('done\n')

        return tracks_to_kill

    def delete_tracks(self, tracks):
        """Deletes a list of tracks from iTunes.
        
        :param tracks: :list: of iTunes tracks, NOT track IDs.  They
                       will be deleted from disk and from the library. 
        
        """

        for t in tracks:
            print t.name()

        print "\nThe above %d tracks will be deleted." % len(tracks)
        x = raw_input('Continue? [y/N] ')

        if x.lower() == 'y':
            for i, t in enumerate(tracks):
                sys.stdout.write('\rProcessed %d/%d' % (i + 1, len(tracks)))

                try:
                    if t.location() != k.missing_value:
                        """If the location is missing, the file has
                        already been deleted from disk.  So only try to
                        remove a file if it actually exists.
                        """
                        os.unlink(t.location().path)

                    """Now delete the track from iTunes"""
                    t.delete()

                except CommandError as e:
                    sys.stderr.write('\nError deleting %s from iTunes '
                                     'library: %s\n' % (t.name(), str(e)))

            sys.stdout.write('\nDone!\n')

if __name__ == "__main__":
    itunes = ITunesManager()#IGNORE:C0103

    t = itunes.itunes.tracks()[0]
    print t.size()
    sys.exit(0)

    target_playlist = (sys.argv[1] if len(sys.argv) > 1#IGNORE:C0103
                       else PLAYLIST_NAME)

    dyingtracks = itunes.get_tracks_from_playlist(target_playlist)#IGNORE:C0103
    if len(dyingtracks) > 0:
        itunes.delete_tracks(dyingtracks)
