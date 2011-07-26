#!/usr/bin/env python -u
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
import sqlite3

# ---*< Third-party imports >*-------------------------------------------------
from dictshield.document import Document
from dictshield.fields import IntField, ListField, StringField

# ---*< Local imports >*-------------------------------------------------------
from itunes import ITunesManager

# ---*< Initialization >*------------------------------------------------------
class iTunesTrack(Document):
    """iTunes Track model
    """
    name = StringField()
    md5 = StringField()
    ids = ListField(IntField())

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
    contains the md5 and all data in the iTunesTrack object
    """
    db.execute('''
        DROP TABLE IF EXISTS dupe_finder;
        CREATE TABLE dupe_finder(
            md5 TEXT PRIMARY KEY,
            data json
    ''')

def save_track(db, track):
    """Saves a track to the DB, keyed on file hash.

    Effectively, the stored object acts as the master record for info.
    This looks at various fields and sets the stored data to be what is
    relevant.
    """

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
        if t.artist() == 'Ehren Stowers':
            print '%s\t%s' % (t.id(), t.name())



if __name__ == "__main__":

    itunes = ITunesManager()#IGNORE:C0103
    update_ratings(itunes)
