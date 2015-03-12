# coding: utf8
from datetime import datetime
import re
import unittest

def get_first_name():
    name = 'Nobody'
    if auth.user:
        name = auth.user.first_name
    return name

# Format for wiki links.
RE_LINKS = re.compile('(<<)(.*?)(>>)')

db.define_table('pagetable',
                Field('title'),
                )

# This table holds the names of different games that have recipe entries.
db.define_table('gametable',
                Field('title'),
                )

# This table holds information about specific item recipes.
db.define_table('recipe',
                Field('game_id'),
                Field('game_ver'),
                Field('author',default=get_first_name()),
                Field('user_id',db.auth_user,default=auth.user_id),
                Field('description','text'),
                Field('item_names','list:string'),
                Field('item_amount','list:integer'),
                Field('picture','upload'),
                )
# 'recipe' table settings
db.recipe.description.represent = represent_content
db.recipe.author.writeable = False
db.recipe.user_id.readable = False
db.recipe.user_id.writeable = False

db.define_table('revision',
                Field('page_id'),
                Field('author',default=get_first_name()),
                Field('user_id',db.auth_user,default=auth.user_id),
                Field('creation_date','datetime',default=datetime.utcnow()),
                Field('body','text'),
                Field('comments'), # 'comment' is a reserved keyword
                )

def create_wiki_links(s):
    """This function replaces occurrences of '<<polar bear>>' in the 
    wikitext s with links to default/page/polar%20bear, so the name of the 
    page will be urlencoded and passed as argument 1."""
    def makelink(match):
        # The tile is what the user puts in
        title = match.group(2).strip()
        # The page, instead, is a normalized lowercase version.
        page = title.lower()
        return '[[%s %s]]' % (title, URL('default', 'index', args=[page]))
    return re.sub(RE_LINKS, makelink, s)

def represent_wiki(s):
    """Representation function for wiki pages.  This takes a string s
    containing markup language, and renders it in HTML, also transforming
    the <<page>> links to links to /default/index/page"""
    return MARKMIN(create_wiki_links(s))

def represent_content(v, r):
    """In case you need it: this is similar to represent_wiki, 
    but can be used in db.table.field.represent = represent_content"""
    return represent_wiki(v)

# We associate the wiki representation with the body of a revision.
db.revision.body.represent = represent_content
db.revision.id.readable = False
db.revision.author.writeable = False
db.revision.user_id.readable = False
db.revision.user_id.writeable = False
db.revision.creation_date.writeable = False
