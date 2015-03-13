# -*- coding: utf-8 -*-

import logging

def index():
    """This is the main page of the wiki. The title of the requested page is in request.args(0).
    If this is None, then serve "Main page"."""
    title = request.args(0) or 'main page'
    display_title = title.title()
    
    editing = True if request.vars.edit=='y' else False

    page = db(db.pagetable.title == title).select().first()
    page_id = page.id if page is not None else None
    
    if editing:
        if page_id is not None:
            r = db(db.revision.page_id == page_id).select(orderby=~db.revision.creation_date).first()
        else:
            r = None
        s = r.body if r is not None else ''
        form = SQLFORM.factory(Field('body','text',label='Content',default=s),
                               Field('comments'))
        form.add_button('Cancel',URL('default','index'))
        if form.process().accepted:
            if r is None:
                page_id = db.pagetable.insert(title=title)
                db.revision.insert(page_id=int(page_id),body=form.vars.body,comments=form.vars.comments)
                redirect(URL('default','index',args=[title]))
            else:
                db.revision.insert(page_id=page_id,body=form.vars.body,comments=form.vars.comments)
            redirect(URL('default','index',args=[title]))
        return dict(display_title=display_title,content=form,editing=editing,form='')
    else: # not editing
        if page_id is not None:
            r = db(db.revision.page_id == page_id).select(orderby=~db.revision.creation_date).first()
            s = r.body if r is not None else ''
            content = represent_wiki(s)
            form = FORM.confirm('Edit',{'History':URL('default','history',args=[title]),'Main Page':URL('default','index')})
            if form.accepted:
                if auth.user:
                    redirect(URL('default','index',args=[title],vars=dict(edit='y')))
                else:
                    session.flash = T("Please sign in to edit.")
                    redirect(URL('default','index',args=[title]))
            return dict(display_title=display_title,content=content,editing=editing,form=form)
        else: # page_id is None
            if title == 'main page':
                content = represent_wiki("Welcome to the main page! Search for games here.")
                form = SQLFORM.factory(Field('search'))
                if form.process().accepted:
                    redirect(URL('default','games',args=[form.vars.search]))
                return dict(display_title=display_title,content=content,form=form)
            else: # title is not 'main page'
                content = represent_wiki("This topic does not exist. Would you like to create it?")
                form = FORM.confirm('Yes',{'No':URL('default','index')})
                if form.accepted:
                    redirect(URL('default','index',args=[title],vars=dict(edit='y')))
                return dict(display_title=display_title,content=content,form=form)

# Searchbar for finding games, grid for known games
def index2():
    def generate_view_button(row):
        g = db(db.gametable.id == row.id).select().first()
        b = A('View',_class='btn',_href=URL('default','games2',args=[g.title]))
        return b
    
    form = SQLFORM.factory(Field('search'))
    if form.process().accepted:
        redirect(URL('default','games2',args=[form.vars.search.lower()]))
    
    links = [dict(header='',body=generate_view_button)]
    grid = SQLFORM.grid(db.gametable,
                        fields=[db.gametable.title,
                                db.gametable.is_pc,
                                db.gametable.is_xb,
                                db.gametable.is_ps,
                                db.gametable.amount,
                                ],
                        create=False,
                        details=False,
                        editable=False,
                        deletable=False,
                        user_signature=False,
                        csv=False,
                        searchable=False,
                        #onvalidation=check_search,
                        links=links,
                        )
    return dict(form=form,grid=grid)

# Individual game information (editable), grid of recipes for that game
def games():
    def generate_view_button(row):
        vr = db(db.recipe.id == row.id).select().first()
        b = A('View',_class='btn',_href=URL('default','recipes',args=[vr.title]))
        return b
    
    title = request.args(0) or 'Unknown Game'
    display_title = title.title()
    editing = True if request.vars.edit=='y' else False
    game = db(db.gametable.title == title).select().first()
    game_id = game.id if game is not None else None
    
    if ((game_id is None) or (title is 'Unknown Game')):
        content = represent_wiki("No game is listed. Would you like to add one?")
        form = FORM.confirm('Yes',{'No':URL('default','index2')})
        if form.accepted:
            if title is 'Unknown Game':
                form = SQLFORM.factory(Field('name'))
                if form.process().accepted:
                    db.gametable.insert(title=form.vars.name.lower())
                    redirect(URL('default','games',args=[form.vars.name.lower()],vars=dict(edit='y')))
            else:
                db.gametable.insert(title=title)
                redirect(URL('default','games',args=[title],vars=dict(edit='y')))
        return dict(display_title=display_title,content=content,form=form,grid='')
    else:
        if editing:
            form = SQLFORM(db.gametable,record=db.gametable(game_id))
            if form.process().accepted:
                session.flash = T('Game Edited')
                redirect(URL('default','games',args=[title]))
            return dict(display_title=display_title,content='',form=form,grid='')
        else:
            form = SQLFORM(db.gametable,record=db.gametable(game_id),readonly=True)
            grid = ''
            search_form = SQLFORM.factory(Field('search'))
            if search_form.process().accepted:
                db.recipe.insert(title=search_form.vars.search.lower(),game_id=game_id)
                session.flash = T('Game Page Created')
                redirect(URL('default','recipes',args=[search_form.vars.search.lower()],vars=dict(game_name=game_id)))
            try:
                r = db(db.recipe.game_id == game_id).select(orderby=~db.recipe.game_ver).first()
                links = [dict(header='',body=generate_view_button)]
                grid = SQLFORM.grid(r,
                                    fields=[db.recipe.author,
                                            db.recipe.game_ver,
                                            ],
                                    #create=False,
                                    details=False,
                                    editable=False,
                                    deletable=False,
                                    user_signature=False,
                                    csv=False,
                                    searchable=False,
                                    links=links,
                                    )
            except:
                grid = 'There are no crafting recipes yet. Create some!'
            return dict(display_title=display_title,content=form,form=search_form,grid=grid)

def games2():
    title = request.args(0) or 'unknown game'
    display_title = title.title()
    editing = True if request.vars.edit=='y' else False
    game = db(db.gametable.title == title).select().first()
    game_id = game.id if game is not None else None
    
    if editing:
        if game_id is None:
            game_id = db.gametable.insert(title=title)
        form = SQLFORM(db.gametable,record=db.gametable(game_id))
        form.add_button('Cancel',URL('default','games2',args=[title]))
        if form.process().accepted:
            redirect(URL('default','games2',args=[title]))
        return dict(display_title=display_title,content='',form=form)
    else: # not editing
        if game_id is not None:
            content = SQLFORM(db.gametable,record=db.gametable(game_id),readonly=True)
            # add SQLFORM.grid for recipetable
            form = FORM.confirm('Edit',{'Games List':URL('default','index2')})
            if form.accepted:
                if auth.user:
                    redirect(URL('default','games2',args=[title],vars=dict(edit='y')))
                else:
                    session.flash = T("Please sign in to edit.")
                    redirect(URL('default','games2',args=[title]))
            return dict(display_title=display_title,content=content,form=form)
        else: # game_id is None
            if title == 'unknown game':
                content = represent_wiki("Welcome to the main page! Search for games here.")
                form = SQLFORM.factory(Field('search'))
                if form.process().accepted:
                    redirect(URL('default','recipes2',args=[form.vars.search]))
                return dict(display_title=display_title,content=content,form=form)
            else: # title is not 'unknown game'
                content = represent_wiki("This game does is not listed. Would you like to create it?")
                form = FORM.confirm('Yes',{'No':URL('default','index')})
                if form.accepted:
                    redirect(URL('default','games2',args=[title],vars=dict(edit='y')))
                return dict(display_title=display_title,content=content,form=form)

def recipes2():
    title = request.args(0) or 'unknown recipe'
    display_title = title.title()
    editing = True if request.vars.edit=='y' else False
    recip = db(db.recipetable.title == title).select().first()
    recip_id = recip.id if page is not None else None
    
    if editing:
        if recip_id is not None:
            r = db(db.recipe.recip_id == recip_id).select(orderby=~db.recipe.game_ver).first()
        else:
            r = None
        s = r.body if r is not None else ''
        form = SQLFORM.factory(Field('body','text',label='Content',default=s),
                               Field('game_ver',label='Game Version'))
        form.add_button('Cancel',URL('default','games2'))
        if form.process().accepted:
            if r is None:
                recip_id = db.recipetable.insert(title=title)
                db.recipe.insert(recip_id=int(recip_id),body=form.vars.body,game_ver=form.vars.game_ver)
                redirect(URL('default','games2',args=[title]))
            else:
                db.recipe.insert(recip_id=recip_id,body=form.vars.body,game_ver=form.vars.game_ver)
            redirect(URL('default','games2',args=[title]))
        return dict(display_title=display_title,content=form,form='')
    else: # not editing
        if recip_id is not None:
            r = db(db.recipe.recip_id == recip_id).select(orderby=~db.recipe.game_ver).first()
            s = r.body if r is not None else ''
            content = represent_wiki(s)
            form = FORM.confirm('Edit',{'History':URL('default','history2',args=[title]),'Games List':URL('default','games2')})
            if form.accepted:
                if auth.user:
                    redirect(URL('default','games2',args=[title],vars=dict(edit='y')))
                else:
                    session.flash = T("Please sign in to edit.")
                    redirect(URL('default','games2',args=[title]))
            return dict(display_title=display_title,content=content,form=form)
        else: # page_id is None
            if title == 'unknown recipe':
                content = represent_wiki("This is an unknown recipe! Create it.")
                form = SQLFORM.factory(Field('search'))
                if form.process().accepted:
                    redirect(URL('default','recipes2',args=[form.vars.search]))
                return dict(display_title=display_title,content=content,form=form)
            else: # title is not 'main page'
                content = represent_wiki("This topic does not exist. Would you like to create it?")
                form = FORM.confirm('Yes',{'No':URL('default','games2')})
                if form.accepted:
                    redirect(URL('default','games2',args=[title],vars=dict(edit='y')))
                return dict(display_title=display_title,content=content,form=form)
    
def recipes():
    title = request.args(0) or 'unknown recipe'
    display_title = title.title()
    game_name = request.vars.game_name if request.vars.game_name is not None else None
    
    recip = db(db.recipe.title == title and db.recipe.game_id == game_name).select().first()
    recip_id = recip.id if recip is not None else None
    
    form = SQLFORM(db.recipe,record=db.recipe(recip_id))
    
    return dict(display_title=display_title,form=form)

def history():
    """This page lists all revisions of a given recipe, and allows the user to revert an recipe
    to one of its previous revisions."""
    
    def generate_revert_button(row):
        return A('Revert to this version',_class='btn',_href=URL('default','revert',args=[row.id]))
    
    links = [dict(header='Revert',body=generate_revert_button)]
    
    title = request.args(0)
    display_title = title.title()
    page = db(db.pagetable.title == title).select().first()
    r = (db.revision.page_id == page.id)
    
    form = SQLFORM.grid(r,
                        fields=[db.revision.author,
                                db.revision.creation_date,
                                db.revision.comments],
                        create=False,
                        details=False,
                        editable=False,
                        deletable=False,
                        user_signature=False,
                        csv=False,
                        searchable=False,
                        orderby=~db.revision.creation_date,
                        links=links)
    
    return dict(display_title=display_title,form=form)
    
def revert():
    """This reverts a topic to a previous revision."""
    r = db.revision[request.args(0)]
    db.revision.insert(page_id=r.page_id,
                       body=r.body,
                       comments='Revert to '+r.creation_date.strftime("%Y-%m-%d %H:%M:%S")+' UTC')
    redirect(URL('default','index'))
    

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_login() 
def api():
    """
    this is example of API with access control
    WEB2PY provides Hypermedia API (Collection+JSON) Experimental
    """
    from gluon.contrib.hypermedia import Collection
    rules = {
        '<tablename>': {'GET':{},'POST':{},'PUT':{},'DELETE':{}},
        }
    return Collection(db).process(request,response,rules)
