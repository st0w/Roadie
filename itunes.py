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
import sqlite3
import sys
import tempfile

# ---*< Third-party imports >*-------------------------------------------------
from appscript import app, k, CommandError #@UnresolvedImport

# ---*< Local imports >*-------------------------------------------------------

# ---*< Initialization >*------------------------------------------------------
"""The name of the playlist of files to kill.  Any type of playlist."""
PLAYLIST_NAME = 'Files to kill'

# ---*< Code >*----------------------------------------------------------------
def init_db_conn(persist=False, db_file=None):
    """Setups up the SQLite DB handle

    Sets up the necessary connection to the DB.  Note that this also
    runs setup_db to initialize it.  Defaults to using only memory.

    :param persist: (optional) `boolean` indicating whether SQLite
                    should use a persistent file (True) or should just
                    run in memory (False, and the default)
    :param db_file: (optional) `str` containing the path of the DB file
                    to use.  If None or blank, will generate a secure
                    temp file.
    :rtype: `sqlite3.Db` connection handle
    """
    if persist:
        if not db_file:
            db_file = tempfile.NamedTemporaryFile(delete=False).name

        print 'DB File: %s' % db_file

    else:
        db_file = ':memory:'
        print 'Using memory for SQLite DB'

    db_conn = sqlite3.connect(db_file,
                              detect_types=sqlite3.PARSE_DECLTYPES
                              | sqlite3.PARSE_COLNAMES)
    db_conn.row_factory = sqlite3.Row # fields by names
    setup_db(db_conn)

    return db_conn


def setup_db(db):
    """Initializes a database if empty

    The DB schema is keyed on the MD5 of the file, and the stored JSON
    contains the md5 and all data in the iTunesTrack object.  Indexing
    is also provided on file path, in case there are multiple reference
    to the same actual file.

    TODO: Should table creation be removed and done by caller?
    """
    db.execute('''DROP TABLE IF EXISTS dupe_finder;''')
    db.execute('''
        CREATE TABLE dupe_finder(
            md5 TEXT PRIMARY KEY,
            data json
        )
    ''')

    db.execute('''DROP TABLE IF EXISTS sync_hierarchy;''')
    db.execute('''
        CREATE TABLE sync_hierarchy(
            path TEXT PRIMARY KEY,
            data json
        )
    ''')


def smart_str(oldstr, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Returns a bytestring version of 'oldstr', encoded as specified in 'encoding'.
    
    If strings_only is True, don't convert (some) non-string-like objects.

    Stol....borrowed.... from Django.
    """
    try:
        return str(oldstr)
    except UnicodeEncodeError:
        if isinstance(oldstr, Exception):
            # An Exception subclass containing non-ASCII data that doesn't
            # know how to print itself properly. We shouldn't raise a
            # further exception.
            return ' '.join([smart_str(arg, encoding, strings_only,
                    errors) for arg in oldstr])
        return unicode(oldstr).encode(encoding, errors)


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

    def get_all_tracks(self):
        """Returns a list containing all the tracks in iTunes
        
        :rtype: An iterable that provides access to the library tracks 
        """
        self._connect_to_itunes()

        return self.itunes.tracks()

    def remove_dead_tracks(self):
        """Removes all dead items (entries without a corresponding file)
        from the iTunes library.
        
        DO NOT prompt for verification before removing tracks!  Does not
        attempt to remove from the file system, just removes the entry
        from the iTunes Library.
        """
        self._connect_to_itunes()
        count = 0

        for t in self.get_all_tracks():
            if t.location() == k.missing_value:
                sys.stderr.write('Deleting %s - %s\n' % (smart_str(t.artist()),
                                                         smart_str(t.name())))
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

        tracks_to_kill = []

        sys.stdout.write('Building list of tracks from playlist...')
        for t in self.get_all_tracks():
            if t.persistent_ID() in track_ids:
                tracks_to_kill.append(t)
        sys.stdout.write('done\n')

        return tracks_to_kill


def delete_tracks(tracks):
    """
    Deletes a list of tracks from iTunes, AS WELL AS the
    corresponding file.
    
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

