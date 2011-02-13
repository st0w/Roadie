# ---*< itunes.py >*-----------------------------------------------------------
# Deletes files from iTunes library and disk with one star
#
# Copyright (C) 2011 st0w <st0w@st0w.com>
#
# This is released under the MIT License.
"""Provides limited access to iTunes via py-appscript

Created on Feb 12, 2011

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

# ---*< Code >*----------------------------------------------------------------
def smart_str(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Returns a bytestring version of 's', encoded as specified in 'encoding'.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    try:
        return str(s)
    except UnicodeEncodeError:
        if isinstance(s, Exception):
            # An Exception subclass containing non-ASCII data that doesn't
            # know how to print itself properly. We shouldn't raise a
            # further exception.
            return ' '.join([smart_str(arg, encoding, strings_only,
                    errors) for arg in s])
        return unicode(s).encode(encoding, errors)


class ITunesManager(object):
    """Handles connecting to and sending operations to iTunes
    """
    itunes = None
    audio_types = ['AAC audio file',
                   'MPEG audio file',
                   'Protected AAC audio file',
                   'Purchased AAC audio file',
                   'WAV audio file',
                   ]
    video_type = ['MPEG-4 video file',
                  'QuickTime movie file',
                  ]

    def __init__(self):
        """__init__ method.  Takes no options."""
        self._connect_to_itunes()
        super(ITunesManager, self).__init__()

    def _connect_to_itunes(self):
        """Establishes a connection to iTunes.  You won't need to use this."""
        if not self.itunes:
            self.itunes = app('iTunes')
#        else:
#            print "already connected to iTunes"

    def get_all_tracks(self, only_audio=True):
        """Returns a list containing all the tracks in iTunes
        
        :param only_audio: `bool` indicating if only audio tracks should be
                            returned, or if all items should be returned.
        """
        self._connect_to_itunes()

        if not only_audio:
            return self.itunes.tracks()

        all_tracks = []

        for t in self.itunes.tracks():
            if t.kind() in self.audio_types:
                all_tracks.append(t)
#            else:
#                print 'UNKNOWN KIND: %s' % t.kind()

        return all_tracks

    def remove_dead_tracks(self, only_audio=True):
        """Removes all dead items (entries without a corresponding file)
        from the iTunes music library
        """
        self._connect_to_itunes()
        tracks = self.get_all_tracks(only_audio)

        count = 0

        for t in tracks:
            if t.location() == k.missing_value:
                sys.stderr.write('Deleting %s - %s\n' % (smart_str(t.artist()), smart_str(t.name())))
                t.delete()
                count += 1

        sys.stdout.write('Found and deleted %d dead tracks\n' % count)

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
        library_tracks = self.get_all_tracks()
        sys.stdout.write('done\n')

        tracks_to_kill = []

        sys.stdout.write('Building list of tracks from playlist...')
        for t in library_tracks:
            if t.persistent_ID() in track_ids:
                tracks_to_kill.append(t)
        sys.stdout.write('done\n')

        return tracks_to_kill

def delete_tracks(tracks):
    """Deletes a list of tracks from iTunes.
    
    --> BE CAREFUL WITH THIS!!!! <--

    Note that I don't prompt for verification before each file.  I make no
    warranty or guarantee that this won't completely destroy your entire
    library.  USE AT YOUR OWN RISK!
    
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

