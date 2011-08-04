# ---*< /Users/st0w/Documents/Computy/coding/Roadie/models.py >*------------------------------------------------
# Copyright (C) 2011 st0w
# 
# This module is part of Roadie and is released under the MIT License.
# Please see the LICENSE file for details.

"""Models utilized by Roadie

Created on Aug 3, 2011


"""
# ---*< Standard imports >*---------------------------------------------------

# ---*< Third-party imports >*------------------------------------------------
from dictshield.document import Document
from dictshield.fields import DateTimeField, IntField, ListField, StringField

# ---*< Local imports >*------------------------------------------------------

# ---*< Initialization >*-----------------------------------------------------

# ---*< Code >*---------------------------------------------------------------
__all__ = ()

class iTunesTrack(Document):
    """iTunes Track model
    """
    md5 = StringField()
    path = StringField()
    rating = IntField(min_value=0, max_value=100, default=0)
    ids = ListField(IntField())
    date_added = DateTimeField()

