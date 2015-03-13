# coding: utf8
from datetime import datetime
import re
import unittest

def get_first_name():
    name = 'Anon User'
    if auth.user:
        name = auth.user.first_name
    return name

# Format for wiki links.
RE_LINKS = re.compile('(<<)(.*?)(>>)')

db.define_table('pagetable',
                Field('title'),
                )

# This table holds information about games that have recipe entries.
db.define_table('gametable',
                Field('title'),           # name of game
                Field('body','text'),     # description of game
                Field('amount','integer'),# number of recipes entered
                Field('picture','upload'),# game box art
                Field('is_pc','boolean'), # is game on personal computer?
                Field('is_xb','boolean'), # is game on xbox?
                Field('is_ps','boolean'), # is game on playstation?
                )

# This table holds information about specific item recipes.
db.define_table('recipe',
                Field('title'),                                    # name of recipe item
                Field('game_id'),                                  # index in 'gametable' of game that this recipe belongs to
                Field('game_ver'),                                 # version of game where recipe works (numerical)
                Field('author',default=get_first_name()),          # *used to track how many posts a user makes
                Field('user_id',db.auth_user,default=auth.user_id),# original author's user_id
                Field('body','text'),                              # description of the item created from this recipe
                Field('item_names','list:string'),                 # list of item names used in crafting recipe
                Field('item_amount','list:integer'),               # list of item amounts used in crafting recipe
                Field('craft_time','double'),                      # amount of time used in crafting recipe, if game uses time
                Field('picture','upload'),                         # picture of the item crafted from recipe
                )

### REMOVE THIS AT SOME POINT!!! ###
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

### REMOVE THIS AT SOME POINT!!! ###
db.revision.body.represent = represent_content
db.revision.id.readable = False
db.revision.author.writeable = False
db.revision.user_id.readable = False
db.revision.user_id.writeable = False
db.revision.creation_date.writeable = False

# 'gametable' table settings
db.gametable.id.readable = False
db.gametable.id.writable = False
db.gametable.title.requires = IS_NOT_IN_DB(db,'gametable.title')
db.gametable.title.writable = False
db.gametable.body.label = 'Description'
db.gametable.amount.readable = False
db.gametable.amount.writable = False
db.gametable.amount.label = 'Recipes'
db.gametable.picture.requires = IS_EMPTY_OR(IS_IMAGE(maxsize=(400,400)))
db.gametable.is_pc.default = False
db.gametable.is_pc.label = 'PC'
db.gametable.is_xb.default = False
db.gametable.is_xb.label = 'xbox'
db.gametable.is_ps.default = False
db.gametable.is_ps.label = 'PlayStation'

# 'recipe' table settings
db.recipe.game_id.readable = False
db.recipe.game_id.writable = False
db.recipe.author.writeable = False
db.recipe.user_id.readable = False
db.recipe.user_id.writeable = False
db.recipe.body.represent = represent_content
db.recipe.body.label = 'Description'
db.recipe.craft_time.default = 0
db.recipe.picture.requires = IS_EMPTY_OR(IS_IMAGE(maxsize=(200,200)))
