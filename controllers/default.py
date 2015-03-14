# -*- coding: utf-8 -*-

import logging

def index():
    def generate_view_button(row):
        g = db(db.gametable.id == row.id).select().first()
        b = A('View',_class='btn',_href=URL('default','games2',args=[g.title]))
        return b
    
    form = SQLFORM.factory(Field('search',label='Search Games'))
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
                r = db(db.recipe.game_id == game_id).select(orderby=~db.recipe.creation_date).first()
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
        return dict(display_title=display_title,content='',form=form,sform='',grid='')
    else: # not editing
        if game_id is not None:
            content = SQLFORM(db.gametable,record=db.gametable(game_id),readonly=True)
            try:
                rt = db(db.recipetable.game_id == game_id).select().first()
                q = (db.recipe.recip_id == rt.id)
                grid = SQLFORM.grid(db.recipe,
                                    fields=[#db.recipetable.title,
                                            db.recipe.author,
                                            ],
                                    )
            except:
                grid = 'There are no crafting recipes yet. Create some!'
            form = FORM.confirm('Edit',{'Games List':URL('default','index')})
            if form.accepted:
                if auth.user:
                    redirect(URL('default','games2',args=[title],vars=dict(edit='y')))
                else:
                    session.flash = T("Please sign in to edit.")
                    redirect(URL('default','games2',args=[title]))
            sform = SQLFORM.factory(Field('search',label='Search Recipes'))
            if sform.process().accepted:
                redirect(URL('default','recipes2',args=[sform.vars.search.lower()],vars=dict(g_id=game_id)))
            return dict(display_title=display_title,content=content,form=form,sform=sform,grid=grid)
        else: # game_id is None
            if title == 'unknown game':
                content = represent_wiki("We couldn't find that game listing. Search for one here.")
                form = SQLFORM.factory(Field('search'))
                form.add_button('Games List',URL('default','index'))
                if form.process().accepted:
                    redirect(URL('default','games2',args=[form.vars.search]))
                return dict(display_title=display_title,content=content,form=form,sform='',grid='')
            else: # title is not 'unknown game'
                content = represent_wiki("This game is not listed. Would you like to create it?")
                form = FORM.confirm('Yes',{'No':URL('default','index')})
                if form.accepted:
                    redirect(URL('default','games2',args=[title],vars=dict(edit='y')))
                return dict(display_title=display_title,content=content,form=form,sform='',grid='')

def recipes2():
    title = request.args(0) or 'unknown recipe'
    display_title = title.title()
    editing = True if request.vars.edit=='y' else False
    g_id = request.vars.g_id if request.vars.g_id is not None else None
    recip = db((db.recipetable.game_id == g_id) & (db.recipetable.title == title)).select().first()
    recip_id = recip.id if recip is not None else None
    if editing:
        r = db(db.recipe.recip_id == recip_id).select(orderby=~db.recipe.creation_date).first() if recip_id is not None else None
        # get the recipe fields
        gv = r.game_ver if r is not None else ''
        de = r.body if r is not None else ''
        i_n = r.item_names if r is not None else None
        i_a = r.item_amount if r is not None else None
        ct = r.craft_time if r is not None else 0
        pic = r.picture if r is not None else None
        form = SQLFORM.factory(Field('game_ver',label='Game Version',default=gv),
                               Field('body','text',label='Description',default=de),
                               Field('item_names','list:string',label='Item Names',default=i_n),
                               Field('item_amount','list:integer',label='Item Amounts',default=i_a),
                               Field('craft_time','double',default=ct),
                               Field('picture','upload',default=pic),
                               )
        form.add_button('Cancel',URL('default','games2'))
        if form.process().accepted:
            if r is None:
                recip_id = db.recipetable.insert(title=title,game_id=g_id)
            db.recipe.insert(recip_id=int(recip_id),
                             game_ver=form.vars.game_ver,
                             body=form.vars.body,
                             item_names=form.vars.item_names,
                             item_amount=form.vars.item_amount,
                             craft_time=form.vars.craft_time,
                             picture=form.vars.picture,
                             )
            redirect(URL('default','recipes2',args=[title],vars=dict(g_id=g_id)))
        return dict(display_title=display_title,content=form,form='')
    else: # not editing
        if recip_id is not None:
            r = db(db.recipe.recip_id == recip_id).select(orderby=~db.recipe.game_ver).first()
            s = r.body if r is not None else ''
            content = represent_wiki(s)
            form = FORM.confirm('Edit',{'History':URL('default','history2',args=[title]),'Games List':URL('default','index')})
            if form.accepted:
                if auth.user:
                    redirect(URL('default','recipes2',args=[title],vars=dict(g_id=g_id,edit='y')))
                else:
                    session.flash = T("Please sign in to edit.")
                    redirect(URL('default','recipes2',args=[title],vars=dict(g_id=g_id)))
            return dict(display_title=display_title,content=content,form=form)
        else: # page_id is None
            if title == 'unknown recipe':
                content = represent_wiki("This is an unknown recipe! Create it.")
                form = SQLFORM.factory(Field('search',label='Search Recipes'))
                if form.process().accepted:
                    redirect(URL('default','recipes2',args=[form.vars.search],vars=dict(g_id=g_id)))
                return dict(display_title=display_title,content=content,form=form)
            else: # title is not 'main page'
                content = represent_wiki("This recipe does not exist. Would you like to create it?")
                form = FORM.confirm('Yes',{'No':URL('default','games2')})
                if form.accepted:
                    redirect(URL('default','recipes2',args=[title],vars=dict(g_id=g_id,edit='y')))
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
