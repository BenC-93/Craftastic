# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

import logging

def index():
    """This is the main page of the wiki. You will find the title of the requested page in request.args(0).
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
                    redirect(URL('default','index',args=[form.vars.search]))
                return dict(display_title=display_title,content=content,form=form)
            else: # title is not 'main page'
                content = represent_wiki("This topic does not exist. Would you like to create it?")
                form = FORM.confirm('Yes',{'No':URL('default','index')})
                if form.accepted:
                    redirect(URL('default','index',args=[title],vars=dict(edit='y')))
                return dict(display_title=display_title,content=content,form=form)

def games():
    return

def recipes():
    return

def history():
    """This page lists all revisions of a given topic, and allows the user to revert a topic
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
