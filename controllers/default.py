# -*- coding: utf-8 -*-
import logging
import os

def index():
    def generate_view_button(row):
        g = db(db.gametable.id == row.id).select().first()
        b = A('View',_class='btn',_href=URL('default','games',args=[g.title]))
        return b
    
    form = SQLFORM.factory(Field('search',label='Search Games'))
    if form.process().accepted:
        redirect(URL('default','games',args=[form.vars.search.lower()]))
    
    links = [dict(header='',body=generate_view_button)]
    grid = SQLFORM.grid(db.gametable,
                        fields=[db.gametable.title,
                                db.gametable.is_pc,
                                db.gametable.is_mc,
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
                        links=links,
                        )
    return dict(form=form,grid=grid)

# Individual game information (editable), grid of recipes for that game
def games():
    def generate_view_button(row):
        r = db(db.recipetable.id == row.id).select().first()
        b = A('View',_class='btn',_href=URL('default','recipes',args=[r.title],vars=dict(g_id=game_id)))
        return b
    
    def generate_item_desc(row):
        rt = db(db.recipetable.id == row.id).select().first()
        r = db(db.recipe.recip_id == rt.id).select(orderby=~db.recipe.creation_date).first()
        return r.body
    
    def generate_item_game_ver(row):
        rt = db(db.recipetable.id == row.id).select().first()
        r = db(db.recipe.recip_id == rt.id).select(orderby=~db.recipe.creation_date).first()
        return r.game_ver
    
    title = request.args(0) or 'unknown game'
    display_title = title.title()
    editing = True if request.vars.edit=='y' else False
    game = db(db.gametable.title == title).select().first()
    game_id = game.id if game is not None else None
    
    if editing:
        if game_id is None:
            game_id = db.gametable.insert(title=title)
        form = SQLFORM(db.gametable,record=db.gametable(game_id))
        form.add_button('Cancel',URL('default','games',args=[title]))
        if form.process().accepted:
            redirect(URL('default','games',args=[title]))
        return dict(display_title=display_title,content='',form=form,sform='',grid='')
    else: # not editing
        if game_id is not None:
            content = SQLFORM(db.gametable,record=db.gametable(game_id),readonly=True)
            rt = (db.recipetable.game_id == game_id)
            links = [dict(header='Description',body=generate_item_desc),
                     dict(header='Game Version',body=generate_item_game_ver),
                     dict(header='',body=generate_view_button)]
            grid = SQLFORM.grid(rt,
                                fields=[db.recipetable.title,
                                        ],
                                create=False,
                                details=False,
                                editable=False,
                                deletable=False,
                                user_signature=False,
                                csv=False,
                                searchable=False,
                                links=links,
                                )
            form = FORM.confirm('Edit',{'Games List':URL('default','index')})
            if form.accepted:
                if auth.user:
                    redirect(URL('default','games',args=[title],vars=dict(edit='y')))
                else:
                    session.flash = T("Please sign in to edit.")
                    redirect(URL('default','games',args=[title]))
            sform = SQLFORM.factory(Field('search',label='Search Recipes'))
            if sform.process().accepted:
                redirect(URL('default','recipes',args=[sform.vars.search.lower()],vars=dict(g_id=game_id)))
            return dict(display_title=display_title,content=content,form=form,sform=sform,grid=grid)
        else: # game_id is None
            if title == 'unknown game':
                content = represent_wiki("We couldn't find that game listing. Search for one here.")
                form = SQLFORM.factory(Field('search'))
                form.add_button('Games List',URL('default','index'))
                if form.process().accepted:
                    redirect(URL('default','games',args=[form.vars.search.lower()]))
                return dict(display_title=display_title,content=content,form=form,sform='',grid='')
            else: # title is not 'unknown game'
                content = represent_wiki("This game is not listed. Would you like to create it?")
                form = FORM.confirm('Yes',{'No':URL('default','index')})
                if form.accepted:
                    redirect(URL('default','games',args=[title],vars=dict(edit='y')))
                return dict(display_title=display_title,content=content,form=form,sform='',grid='')

def recipes():
    title = request.args(0) or 'unknown recipe'
    display_title = title.title()
    editing = True if request.vars.edit=='y' else False
    g_id = request.vars.g_id if request.vars.g_id is not None else None
    game_name = db.gametable(g_id).title
    recip = db((db.recipetable.game_id == g_id) & (db.recipetable.title == title)).select().first()
    recip_id = recip.id if recip is not None else None
    if editing:
        r = db(db.recipe.recip_id == recip_id).select(orderby=~db.recipe.creation_date).first() if recip_id is not None else None
        gv = r.game_ver if r is not None else ''
        de = r.body if r is not None else ''
        i_n = r.item_names if r is not None else None
        i_a = r.item_amount if r is not None else None
        ct = r.craft_time if r is not None else 0
        ra = r.result_amount if r is not None else 1
        pic = r.picture if r is not None else None
        form = SQLFORM.factory(Field('game_ver',label='Game Version',default=gv),
                               Field('body','text',label='Description',default=de),
                               Field('item_names','list:string',default=i_n),
                               Field('item_amount','list:integer',default=i_a),
                               Field('craft_time','double',default=ct),
                               Field('result_amount','double',default=ra),
                               Field('picture','upload',uploadfolder=os.path.join(request.folder,'uploads')),
                               )
        form.add_button('Cancel',URL('default','games',args=[game_name]))
        if form.process().accepted:
            if r is None:
                recip_id = db.recipetable.insert(title=title,game_id=g_id)
            db.recipe.insert(recip_id=int(recip_id),
                             game_ver=form.vars.game_ver,
                             body=form.vars.body,
                             item_names=form.vars.item_names,
                             item_amount=form.vars.item_amount,
                             craft_time=form.vars.craft_time,
                             result_amount=form.vars.result_amount,
                             picture=form.vars.picture,
                             )
            redirect(URL('default','recipes',args=[title],vars=dict(g_id=g_id)))
        return dict(game_name=game_name,display_title=display_title,content=form,form='')
    else: # not editing
        if recip_id is not None:
            r = db(db.recipe.recip_id == recip_id).select(orderby=~db.recipe.creation_date).first()
            content = SQLFORM(db.recipe,record=db.recipe(r.id),readonly=True)
            form = FORM.confirm('Edit',{'History':URL('default','history',args=[title],vars=dict(recip_id=recip_id,g_id=g_id))})
            if form.accepted:
                if auth.user:
                    redirect(URL('default','recipes',args=[title],vars=dict(g_id=g_id,edit='y')))
                else:
                    session.flash = T("Please sign in to edit.")
                    redirect(URL('default','recipes',args=[title],vars=dict(g_id=g_id)))
            return dict(game_name=game_name,display_title=display_title,content=content,form=form)
        else: # page_id is None
            if title == 'unknown recipe':
                content = represent_wiki("This is an unknown recipe! Create it.")
                form = SQLFORM.factory(Field('search',label='Search Recipes'))
                if form.process().accepted:
                    redirect(URL('default','recipes',args=[form.vars.search.lower()],vars=dict(g_id=g_id)))
                return dict(game_name=game_name,display_title=display_title,content=content,form=form)
            else: # title is not 'main page'
                content = represent_wiki("This recipe does not exist. Would you like to create it?")
                form = FORM.confirm('Yes',{'No':URL('default','games')})
                if form.accepted:
                    redirect(URL('default','recipes',args=[title],vars=dict(g_id=g_id,edit='y')))
                return dict(game_name=game_name,display_title=display_title,content=content,form=form)

def history():
    """This page lists all revisions of a given recipe, and allows the user to revert an recipe
    to one of its previous revisions."""
    
    def generate_revert_button(row):
        return A('Revert to this version',_class='btn',_href=URL('default','revert',args=[row.id]))
    
    links = [dict(header='Revert',body=generate_revert_button)]
    
    title = request.args(0)
    display_title = title.title()
    g_id = request.vars.g_id
    game_name = db.gametable(g_id).title
    recip_id = request.vars.recip_id if request.vars.recip_id is not None else None
    recip = (db.recipe.recip_id == recip_id)
    
    form = SQLFORM.grid(recip,
                        fields=[db.recipe.author,
                                db.recipe.game_ver,
                                db.recipe.body,
                                db.recipe.item_names,
                                db.recipe.item_amount,
                                db.recipe.craft_time,
                                db.recipe.result_amount,
                                ],
                        create=False,
                        details=False,
                        editable=False,
                        deletable=False,
                        user_signature=False,
                        csv=False,
                        searchable=False,
                        orderby=~db.recipe.creation_date,
                        links=links,
                        )
    return dict(game_name=game_name,g_id=g_id,display_title=display_title,form=form)
    
def revert():
    """This reverts a topic to a previous revision."""
    r = db.recipe[request.args(0)]
    db.recipe.insert(recip_id=r.recip_id,
                     game_ver=r.game_ver,
                     body=r.body,
                     item_names=r.item_names,
                     item_amount=r.item_amount,
                     craft_time=r.craft_time,
                     result_amount=r.result_amount,
                     picture=r.picture,
                     )
    redirect(URL('default','games',args=[db.gametable[db.recipetable[r.recip_id].game_id].title]))
    
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
