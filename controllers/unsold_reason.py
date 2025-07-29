from py4web import action, request, abort, redirect, URL,response,Session
from py4web.utils.form import Form, FormStyleDefault
from yatl.helpers import A,TAG, XML
from pydal.validators import IS_IN_DB, IS_NOT_EMPTY
from ..common import db, session, T, auth,flash

@action("unsold_reason/index")
@action.uses("unsold_reason/index.html",flash,session,auth,T,db)
def index(id=None):
    # if session['status']!='success':
    #     return 'Access Denied'
    reason_rows = db(db.combo_settings.key_name == 'reason_type').select()
    reason_types = str(reason_rows[0]['value']).split(',') if reason_rows else []
    return locals()

@action("unsold_reason/create", method=['GET', 'POST'])
@action.uses("unsold_reason/create.html", flash,session,auth,T,db)
def create(id=None): 
    reason_rows = db(db.combo_settings.key_name == 'reason_type').select()
    reason_types = str(reason_rows[0]['value']).split(',') if reason_rows else []
    return locals()

@action("unsold_reason/submit", method=['POST'])
@action.uses("unsold_reason/index.html", flash,session,auth,T,db)
def submit(id=None): 
    reason_type=request.forms.get('reason_type')
    reason_name=request.forms.get('reason_name')
    status=request.forms.get('status')
    
    if str(status)!="1":
        status=0
    
    errors=[]
    if reason_type=='' or reason_type is None:
        errors.append('Enter Reason Type') 
    if reason_name=='' or reason_name is None:
        errors.append('Enter Reason name') 
    else:
        rows_check=db((db.unsold_reason.reason_name==reason_name) & (db.unsold_reason.reason_type==reason_type)).select(db.unsold_reason.reason_name,limitby=(0,1))
        if rows_check:
            errors.append('Reason name already exist for this type')
    
    if errors:
        msg = ''
        for item in errors:
            msg = msg + item + 'rdrdrd'
        flash.set(msg, 'warning')
        redirect(URL('unsold_reason','create')) 
    # insert function
    db.unsold_reason.insert(
        reason_type=reason_type,
        reason_name=reason_name,
        status=status
        )        
        
    flash.set('Record added successfully', 'success')
    redirect(URL('unsold_reason','index'))   

@action("unsold_reason/edit", method=['GET', 'POST'])
@action.uses("unsold_reason/edit.html", flash,session,auth,T,db)
def edit(id=None): 
    request_id = request.query.get('id')
    reason_rows = db(db.combo_settings.key_name == 'reason_type').select()
    reason_types = str(reason_rows[0]['value']).split(',') if reason_rows else []
    if request_id:
        record = db(db.unsold_reason.id == request_id).select().first()
    
    return locals()

@action("unsold_reason/update", method=['POST'])
@action.uses("unsold_reason/index.html", flash,session,auth,T,db)
def update(id=None): 
    request_id = request.query.get('id')
    if request_id:
        record = db(db.unsold_reason.id == request_id).select().first()
        
    reason_type=request.forms.get('reason_type')
    reason_name=request.forms.get('reason_name')
    status=request.forms.get('status')
    
    
    if str(status)!="1":
        status=0
    
    errors=[]
    if reason_type=='' or reason_type is None:
        errors.append('Enter Reason Type') 
    if reason_name=='' or reason_name is None:
        errors.append('Enter Reason name') 
    else:
        rows_check=db((db.unsold_reason.reason_type==reason_type) & (db.unsold_reason.reason_name==reason_name) & (db.unsold_reason.id!=request_id)).select(db.unsold_reason.reason_name,limitby=(0,1))
        if rows_check:
            errors.append('Reason name already exist for this type')
    
    if errors:
        msg = ''
        for item in errors:
            msg = msg + item + 'rdrdrd'
        flash.set(msg, 'warning')
        redirect(URL('unsold_reason','edit',vars=dict(id=request_id))) 
        
    # insert function
    record.update_record(
        reason_type=reason_type,
        reason_name=reason_name,
        status=status
        )        
        
    flash.set('Record updated successfully', 'success')
    redirect(URL('unsold_reason','index'))  


@action("unsold_reason/delete")
@action.uses("unsold_reason/index.html",flash,session,auth,T,db)
def delete(id=None):
    # if session['status']!='success':
    #     return 'Access Denied'
    request_id = request.query.get('id')
    if request_id:
        db(db.unsold_reason.id == request_id).delete()
        
        flash.set('Record Delete successfully', 'error')      
        return dict(redirect(URL('unsold_reason', 'index')))

    return locals()


@action("unsold_reason/get_data", method=['GET', 'POST'])
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
        
    if  request.query.get('reason_type') != None and request.query.get('reason_type') !='':
        conditions += " and reason_type = '"+str(request.query.get('reason_type'))+"'"

    if  request.query.get('status') != None and request.query.get('status') !='':
        conditions += " and status = '"+str(request.query.get('status'))+"'"
    #Search End## 
    
    ##Paginate Start##
    total_rows = len(db.executesql( "SELECT * FROM unsold_reason where 1 "+conditions, as_dict=True))

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
    SELECT * FROM `unsold_reason` where 1"""+conditions+""" ORDER BY """+sort_column_name+""" """+sort_direction+""" LIMIT """+str(start)+""","""+str(end)+""";
    """

    data = db.executesql(sql, as_dict=True)
    
    return dict(data=data, total_rows=total_rows,recordsFiltered=total_rows,recordsTotal=total_rows,sort_column_name=sort_column_name)
    # return json.dumps(data)
