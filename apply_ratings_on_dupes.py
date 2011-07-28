#!/usr/bin/env python
# ---*< apply_ratings_on_dupes.py >*-------------------------------------------
# Looks for duplicates and syncs info
#
# Copyright (C) 2011 st0w <st0w@st0w.com>
#
# This is released under the MIT License.
"""Synchronizes ratings and date added to identical tracks

Created on Jul 26, 2011

Does not prompt for verification

This is slow.  It has to hash every file, which on a large library
takes quite some time.  This is because iTunes provides no hash value
stored in the DB to use as a basis.  But it also ensure that only tracks
that are EXACT duplicates are altered.

Uses its own non-persistent SQLite DB for data storage/retrieval.  The
contents of this DB are reset every time it starts.

As currently written, this finds duplicates based on track MD5 hashes.
If dupes are found and one lacks ratings, then ratings are set.  If
multiple are found and they have different ratings, the difference is
reported but no changes are made.

Also, this sets the date added to be the oldest date added on all files
found.

"""
# ---*< Standard imports >*----------------------------------------------------
from datetime import datetime
from hashlib import md5
import json
import sqlite3
import time

# ---*< Third-party imports >*-------------------------------------------------

# ---*< Local imports >*-------------------------------------------------------
from itunes import ITunesManager, iTunesTrack

# ---*< Initialization >*------------------------------------------------------
def init_db_conn():
    db_conn = sqlite3.connect('itunes-dupes.db',
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
    """
    db.execute('''DROP TABLE IF EXISTS dupe_finder;''')
    db.execute('''
        CREATE TABLE dupe_finder(
            md5 TEXT PRIMARY KEY,
            data json
        )
    ''')


def gen_hash(track):
    m = md5()
    body = '%s - %s - %s - %s - %s' % (track.artist(),
                                       track.album(),
                                       track.name(),
                                       track.duration(),
                                       track.comment())

    m.update(body.encode('utf-8'))

    return m.hexdigest()


def get_track_by_hash(db, md5hash):
    print "retrieving hash from db"

def track_datetime_to_python(dt):
    """Makes sure microseconds are set to 000001

    This is kinda hackish, but necessary.. Otherwise the values fail
    validation upon pulling from DB.

    Note that it doesn't check anytihng. :p
    """
    return datetime.strptime(str(dt)+'.000001', 
                             '%Y-%m-%d %H:%M:%S.%f')

def save_track(tunes, db, track):
    """Saves a track to the DB, keyed on a hash of ID3 tags and duration

    Effectively, the stored object acts as the master record for info.
    This looks at various fields and sets the stored data to be what is
    relevant.
    """
    track_hash = gen_hash(track)
    track_entry = iTunesTrack()

    curs = db.cursor()

    # Get any existing record and do some stuff with it
    curs.execute('''
        SELECT data FROM dupe_finder WHERE md5=?
    ''', (track_hash,))

    rows = curs.fetchall()
    if len(rows) == 0:
        # Nothing found, so use track will be the new entry
        track_entry.md5 = track_hash
        track_entry.ids = [track.id(),]
        track_entry.rating = track.rating()

        # Have to convert to ISO format
        track_entry.date_added = track_datetime_to_python(track.date_added())
        #print track_entry.date_added

    elif len(rows) == 1:
        data = json.loads(rows[0]['data'])
        track_entry = iTunesTrack(**data)
        #print track_entry.date_added

        if track.id() not in track_entry.ids:
            track_entry.ids.append(track.id())

        # Compare values and save appropriate ones in the db
        # First, compare the date added and set it to the older one
        dt = track_datetime_to_python(track.date_added())
        if dt < track_entry.date_added:
            track_entry.date_added = dt

        if track_entry.rating == 0:
            """If there's no rating there and we have one, just set it
            """
            if track.rating() > 0:
                track_entry.rating = track.rating()
        elif track_entry.rating > 0:
            """If they differ, default to the higher value
            """
            print "Existing rating: %d Track rating: %d" % (track_entry.rating,
                                                            track.rating())
            if track.rating() > track_entry.rating:
                track_entry.rating = track.rating()

    else:
        raise ValueError('Unexpected results (%d) found for track %s' % 
                         track.name())

    track_entry.validate()

    curs.execute('''
        INSERT OR REPLACE INTO dupe_finder (md5, data) VALUES (?, ?)
    ''', (track_hash, track_entry.to_json()))

    db.commit()

    """
    Now, if there is more than one value in the ID field, go ahead and
    update all the entires with the new rating.

    Here's the thing.  iTunes doesn't provide a way to search by track
    or database ID.  Really.  So rather than iterate over the entire
    playlist, I let iTunes search for track title and iterate over those
    results.  Not great, but a TON faster than the alternative.
    """
    if len(track_entry.ids) > 1:
        import appscript
        lib = itunes.itunes.library_playlists[1]
        tracks = lib.tracks[appscript.its.name.contains(track.name())]
        for t in tracks.get():
            """Update entries if their id is also in track_entry.ids"""
            if t.id() in track_entry.ids:
                #print 'Got one!  %s\t%s' % (t.id(), t.artist())

                # Update the rating 
                t.rating.set(track_entry.rating)


# ---*< Code >*----------------------------------------------------------------
def update_ratings(itunes):
    """Handles synchronizing ratings and addition dates in iTunes

    :param itunes: `iTunesManager` used for communicating with iTunes.
                   This should already be setup and connected.
    """

    # Setup DB connection
    db = init_db_conn()

    # Loop over tracks building the db.  Note that prior tracks with
    # matching MD5 data will all be updated each time a subsequent track
    # is found.  This obviates the need to re-review the data after
    # processing all tracks.
    for t in itunes.itunes.tracks():
        #if t.artist() == 'Ehren Stowers':
        track_hash = gen_hash(t)
        print '%s\t%d\t%d\t%s' % (track_hash, t.id(), t.rating(), t.name())
        save_track(itunes, db, t)

    print itunes.itunes.library_playlists[1]

if __name__ == "__main__":

    itunes = ITunesManager()#IGNORE:C0103
    update_ratings(itunes)
