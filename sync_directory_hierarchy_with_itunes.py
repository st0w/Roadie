#!/usr/bin/env python -u
# ---*< sync_directory_hierarchy_with_itunes.py >*-----------------------------
# Adds files 
#
# Copyright (C) 2011 st0w <st0w@st0w.com>
#
# This is released under the MIT License.
"""Adds all files to iTunes that aren't already in library.

Rewritten on Jul 28, 2011
Created on Feb 12, 2011

I manage my music stores manually, as I am very particular about how
they are organized.  The problem is, there's no easy way to have iTunes
import new content without getting a ton of random duplicates.  I'm sure
it is finding some tiny detail different about the files, but I'm not
about to try to determine what every time I want to add music.

This works by creating a temporary local SQLite filed-based database,
populating it with the path to all the files in your iTunes library, and
then walking the directory hierarchy to find any files that aren't in
the SQLite DB.  If it finds a file, it tells iTunes to add it.

I'm a little unsure about the handling of unicode in here - so let me
know if you run into issues.

This doesn't try to do any kind of smart duplicate checking based on ID3
tags or anything, it strictly looks at the file path.  Note that if you
have something in iTunes that currently is 'missing' (i.e., it has that
circled exclamation mark by it) that iTunes will report that file's path
as a missing value - so this script will add it again because iTunes
didn't report it as existing.).

As a bonus, it also reports duplicate tracks in your Library that
currently have the same path!  I haven't thought about trying to handle
these dupes automatically yet, but that might come in the future.

"""
# ---*< Standard imports >*----------------------------------------------------
import json
import re
import sys
import os

# ---*< Third-party imports >*-------------------------------------------------
from appscript import k
from mactypes import Alias

# ---*< Local imports >*-------------------------------------------------------
from itunes import init_db_conn, ITunesManager, iTunesTrack

# ---*< Initialization >*------------------------------------------------------
# Dir to start in.  If you don't pasa a unicode-encoded string here and
# your file system contains any files that aren't simple ASCII, the
# script will croak.
DEFAULT_DIR = u'.'
INCLUDE_EXTENSIONS = re.compile('^.+\.('
                                '(aiff)|(m4a)|(m4p)|(mp2)|(mp3)|(mp4)|(wav)'
                                ')$', re.IGNORECASE)

# Used to exclude files below a certain path, matches on start of path
EXCLUDE_DIR_REGEX = re.compile('^('
    '/Volumes/multimedia/Music/(incoming|Production|iTunes)'
')')

table_name = 'sync_hierarchy'

def add_track(db, track, commit=True):
    """Adds a track from iTunes to the sync temporary DB

    The sync DB is volatile, and is erased with every instantiation of
    init_db_conn() in the ITunesManager.

    :param db: `sqlite3.Db` handle to the working DB
    :param track: `iTunes track` as returned from iTunes via appscript
    :param commit: `boolean` indicating whether add_track() should call
                   `db.commit()` after generating the INSERT operation.
                   If you are going to update a lot of tracks in a
                   batch, it is MUCH faster to set `commit` to false -
                   but if you do, be sure you call `db.commit()` once
                   you've done all the batch operations.  Otherwise,
                   your changes won't be saved.
    
    """
    track_entry = iTunesTrack()
    curs = db.cursor()

    # Check if already exists - if it does, add the id of this track to
    # the list
    curs.execute('''
        SELECT data FROM %s WHERE path = ?
    ''' % table_name, (track.location().path,))

    rows = curs.fetchall()
    if len(rows) == 0:
        # Nothing found, so just add track as new
        track_entry.path = track.location().path
        track_entry.ids = [track.id(),]

    elif len(rows) == 1:
        # Found an entry, so add the id to the list and report it
        data = json.loads(rows[0]['data'])
        track_entry = iTunesTrack(**data)

        # Data integrity check
        if track_entry.path != track.location().path:
            raise ValueError('Path for saved track index and stored JSON '
                             'object don\'t match.\nJSON: %s\nIndex: %s' %
                             (track_entry.path, track.location.path()))

        if track.id() not in track_entry.ids:
            track_entry.ids.append(track.id())

        print ('Duplicate entries found for %s: %s' % 
               (track_entry.path, ','.join([str(x) for x in track_entry.ids])))

    track_entry.validate()

    curs.execute('''
        INSERT OR REPLACE INTO %s (path, data) VALUES (?, ?)
    ''' % table_name, (track_entry.path, track_entry.to_json()))

    if commit:
        db.commit()

def db_track_exists(db, path):
    """Checks for existence of a given path in the DB

    :param db: `sqlite3.Db` handle to the working DB
    :param path: `string` of path to check
    :rtype: `boolean` indicating whether the track exists in the DB
    """
    res = db.execute('''
        SELECT path FROM %s WHERE path = ?
    ''' % table_name, (path,))

    count = len(res.fetchall()) # even sqlite3 says the .rowcount is "quirky"

    if count > 0:
        return True
    elif count == 0:
        return False
    else:
        raise ValueError('Got %d results for SELECT query in db_track_exists()'
                         'while looking for %s' % (count, path))


def sync_dir(db, path):
    """Recursively synchronizes a directory hierarchy with iTunes
    
    :param dirname: `string` of the root directory
    """
    sys.stdout.write('Connecting to iTunes...')
    itunes_manager = ITunesManager()#IGNORE:C0103
    sys.stdout.write('done\n')

    # Toss iTunes Library into temp DB
    print 'Extracting file paths from iTunes library...'
    count = itunes_manager.itunes.tracks.count(each=k.item)
    for (i, t) in enumerate(itunes_manager.itunes.tracks()):
        """If it's missing, add the track name and id to a list"""
        sys.stdout.write('[%d/%d (%.02f%%)]\r' % (i, count, (100 * float(i)/count)))
        if t.location() == k.missing_value:
            print "***** MISSING: %d - %s - %s" % (t.id(), t.artist(), t.name())
        else:
            add_track(db, t, False)

    # Commit here after all have been added, for speed
    db.commit()

    # Now that everything is in the DB, begin walking the file system
    total_found = 0
    new_found = 0
    lib = itunes_manager.itunes.library_playlists[1]
    sys.stdout.write('Traversing file system from current directory...\n')

    # Try to work with unicode
    if not isinstance(path, unicode):
        path = unicode(path)

    for root, dirs, files in os.walk(path):
        root = os.path.abspath(root)

        # Skip entries that match the regex
        if EXCLUDE_DIR_REGEX.match(root):
            print 'SKIPPING ',
            print root
            continue

        # Only work with files we care about
        prune_juice = [x for x in files if INCLUDE_EXTENSIONS.match(x)]
        total_found += len(prune_juice)

        #excluded = [x for x in files if not INCLUDE_EXTENSIONS.match(x)]
        #print '******ALL: %s\-------------' % files
        #print '------EXCLUDED: %s\-------------' % excluded
        #print '++++++inCLUDED: %s\-------------' % prune_juice
        #for x in prune_juice:
            #try:
                #print root + os.sep + x
            #except UnicodeEncodeError:
                #print root.encode('utf-16') + os.sep + x.encode('utf-16')

        # As each file is encountered, check for it in the DB
        # if not found, tell iTunes to add it and then add it to the DB
        for f in prune_juice:
            #print '------'
            #f = root + os.sep + f
            #f = u'%s/%s' % (unicode(root, errors='replace'), f)
            #print f.encode("utf-16")
            #print type(f)
            #f = unicode(f, 'utf-16')
            #print f.encode('utf-16')
            #print type(root)
            #print type(os.sep)
            #print type(f)
            f = root + os.sep + f
            #print type(f)
            #f = u'/%s' % f #(unicode(f, errors='replace'))

            #try:
                #print f
            #except UnicodeEncodeError:
                #"""
                #HFS+ (OSX) uses UTF-16 encoding for filenames.  So if 
                #we get an encoding here, try to force UTF-16
                #"""
                #print f.encode('utf-16')

            #f = unicode('%s/%s' % (root, f), errors='replace')

            if not db_track_exists(db, f):
                new_found += 1
                print ' +++ Adding:',
                try:
                    print f,
                except UnicodeEncodeError:
                    print f.encode('utf-16'),

                print '...',

                # Add to iTunes
                f_alias = Alias(f)
                #f_alias = File(f).hfspath

                #itunes_track = itunes_manager.itunes.add([f_alias,])
                itunes_track = lib.add([f_alias,])

                if not itunes_track:
                    print 'Failed'
                    #ValueError('Failed while trying to add %s' % f_alias.path)
                else:
                    # Add to DB
                    add_track(db, itunes_track)
                    print 'Success!'

            sys.stdout.write('[Total found: %d New: %d]\r' % (total_found, new_found))

    print '\n'

if __name__ == '__main__':
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0) # TEMP DEBUG
    db = init_db_conn()
    sync_dir(db, DEFAULT_DIR)
