from py4web import action, request, abort, redirect, URL,response,Session
from py4web.utils.form import Form, FormStyleDefault
from yatl.helpers import A,TAG, XML
from pydal.validators import IS_IN_DB, IS_NOT_EMPTY
from ..common import db, session, T, auth,flash

@action("page_setup/index")
@action.uses("page_setup/index.html",session,flash,db)
def index(id=None):
    # if session['status']!='success':
    #     return 'Access Denied'

    return locals()

@action("page_setup/create", method=['GET', 'POST'])
@action.uses("page_setup/create.html", session,auth,T,db,flash)
def create(id=None): 
    return locals()

@action("page_setup/submit", method=['POST'])
@action.uses("page_setup/index.html", session,auth,T,db,flash)
def submit(id=None): 
    page_name=request.forms.get('page_name')
    status=request.forms.get('status')
    
    if str(status)!="1":
        status=0
    
    errors=[]
    if page_name=='':
        errors.append('Enter Page name') 
    else:
        rows_check=db((db.page_setup.page_name==page_name)).select(db.page_setup.page_name,limitby=(0,1))
        if rows_check:
            errors.append('Page name already exist')
    
    if errors:
        msg = ''
        for item in errors:
            msg = msg + item + 'rdrdrd'
        flash.set(msg, 'warning')
        redirect(URL('page_setup','create')) 
    # insert function
    db.page_setup.insert(
        page_name=page_name,
        status=status
        )        
        
    flash.set('Record added successfully', 'success')
    redirect(URL('page_setup','index'))   

@action("page_setup/edit", method=['GET', 'POST'])
@action.uses("page_setup/edit.html", session,auth,T,db,flash)
def edit(id=None): 
    request_id = request.query.get('id')
    if request_id:
        record = db(db.page_setup.id == request_id).select().first()
    
    return locals()

@action("page_setup/update", method=['POST'])
@action.uses("page_setup/index.html", session,auth,T,db,flash)
def update(id=None): 
    request_id = request.query.get('id')
    if request_id:
        record = db(db.page_setup.id == request_id).select().first()
        
    page_name=request.forms.get('page_name')
    status=request.forms.get('status')
    
    
    if str(status)!="1":
        status=0
    
    errors=[]
    if page_name=='':
        errors.append('Enter Page name') 
    else:
        rows_check=db((db.page_setup.page_name==page_name) & (db.page_setup.id!=request_id)).select(db.page_setup.page_name,limitby=(0,1))
        if rows_check:
            errors.append('Page name already exist')
    
    if errors:
        msg = ''
        for item in errors:
            msg = msg + item + 'rdrdrd'
        flash.set(msg, 'warning')
        redirect(URL('page_setup','edit',vars=dict(id=request_id))) 
        
    # insert function
    record.update_record(
        page_name=page_name,
        status=status
        )        
        
    flash.set('Record updated successfully', 'success')
    redirect(URL('page_setup','index'))  


@action("page_setup/delete")
@action.uses("page_setup/index.html",session,flash,db)
def delete(id=None):
    # if session['status']!='success':
    #     return 'Access Denied'
    request_id = request.query.get('id')
    if request_id:
        db(db.page_setup.id == request_id).delete()
        
        flash.set('Record Delete successfully', 'error')      
        return dict(redirect(URL('page_setup', 'index')))

    return locals()


@action("page_setup/get_data", method=['GET', 'POST'])
@action.uses(db)
def get_data():
    # if session.status=="" or session.status==None:
    #   redirect(URL(c='login',f='index'))
    #Search Start##
    conditions = ""
    # if  request.query.get('cid') != None and request.query.get('cid') !='':
    #     cid = str(request.query.get('cid'))
    #     conditions += " and cid = '"+cid+"'"
    
    if  request.query.get('name') != None and request.query.get('name') !='':
        conditions += " and id = '"+str(request.query.get('name'))+"'"

    if  request.query.get('status') != None and request.query.get('status') !='':
        conditions += " and status = '"+str(request.query.get('status'))+"'"
    #Search End## 
    
    ##Paginate Start##
    total_rows = len(db.executesql( "SELECT * FROM page_setup where 1 "+conditions, as_dict=True))

    page = int(int(request.query.get('start'))/int(request.query.get('length')) +1 or 1)
    rows_per_page = int(request.query.get('length') or 15)
    if rows_per_page == -1:
        rows_per_page = total_rows
    start = (page - 1) * rows_per_page         
    end = rows_per_page
    ##Paginate End##

    #Ordering Start##
    sort_column_index = int(request.query.get('order[0][column]') or 0)
    sort_column_name = request.query.get('columns[' + str(sort_column_index) + '][data]') or 'id'
    sort_direction = request.query.get('order[0][dir]') or 'desc'
    #Ordering End##

    ##Querry Start##
    sql = """
    SELECT * FROM `page_setup` where 1"""+conditions+""" ORDER BY """+sort_column_name+""" """+sort_direction+""" LIMIT """+str(start)+""","""+str(end)+""";
    """

    data = db.executesql(sql, as_dict=True)
    
    return dict(data=data, total_rows=total_rows,recordsFiltered=total_rows,recordsTotal=total_rows,sort_column_name=sort_column_name)
    # return json.dumps(data)
