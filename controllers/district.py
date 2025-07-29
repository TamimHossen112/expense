from py4web import action, request, abort, redirect, URL,response,Session
from py4web.utils.form import Form, FormStyleDefault
from yatl.helpers import A,TAG, XML
from pydal.validators import IS_IN_DB, IS_NOT_EMPTY
from ..common import db, session, T, auth,flash

@action("district/index")
@action.uses("district/index.html",session,flash,db)
def index(id=None):
    # if session['status']!='success':
    #     return 'Access Denied'

    
    return locals()

@action("district/create", method=['GET', 'POST'])
@action.uses("district/create.html", session,auth,T,db,flash)
def create(id=None): 
    divisions=db(db.division).select(db.division.id,db.division.division)
    return locals()

@action("district/submit", method=['POST'])
@action.uses("district/index.html", session,auth,T,db,flash)
def submit(id=None): 
    district=request.forms.get('district')
    status=request.forms.get('status')
    division=request.forms.get('division')
    
    if str(status)!="1":
        status=0
    
    errors=[]
    if district=='':
        errors.append('Enter District Name') 
    if division=='':
        errors.append('Enter Division Name') 
    else:
        rows_check=db((db.district.district==district)).select(db.district.district,limitby=(0,1))
        if rows_check:
            errors.append('District name already exist')
    
    if errors:
        msg = ''
        for item in errors:
            msg = msg + item + 'rdrdrd'
        flash.set(msg, 'warning')
        redirect(URL('district','create')) 
        
    # split section
    div_id=0
    division_name=''
    if division:
        divisions=str(division).split('||')
        div_id=divisions[0]
        division_name=divisions[1]
    
    
    # insert function
    db.district.insert(
        district=district,
        div_id=div_id,
        division=division_name,
        status=status
        )        
        
    flash.set('Record added successfully', 'success')
    redirect(URL('district','index'))   

@action("district/edit", method=['GET', 'POST'])
@action.uses("district/edit.html", session,auth,T,db,flash)
def edit(id=None): 
    request_id = request.query.get('id')
    divisions=db(db.division).select(db.division.id,db.division.division)
    
    if request_id:
        record = db(db.district.id == request_id).select().first()
        
    return locals()

@action("district/update", method=['POST'])
@action.uses("district/index.html", session,auth,T,db,flash)
def update(id=None): 
    request_id = request.query.get('id')
    if request_id:
        record = db(db.district.id == request_id).select().first()
        
    district=request.forms.get('district')
    division=request.forms.get('division')
    status=request.forms.get('status')
    
    
    if str(status)!="1":
        status=0
    
    errors=[]
    if district=='' or district is None:
        errors.append('Enter District Name') 
    if division=='' or division is None:
        errors.append('Enter Division Name') 
    else:
        rows_check=db((db.district.district==district) & (db.district.id!=request_id)).select(db.district.district,limitby=(0,1))
        if rows_check:
            errors.append('District name already exist')
    
    if errors:
        msg = ''
        for item in errors:
            msg = msg + item + 'rdrdrd'
        flash.set(msg, 'warning')
        redirect(URL('district','edit',vars=dict(id=request_id))) 
    
    # split section
    div_id=0
    division_name=''
    if division:
        divisions=str(division).split('||')
        div_id=divisions[0]
        division_name=divisions[1]
    
    
    # insert function
    record.update_record(
        district=district,
        div_id=div_id,
        division=division_name,
        status=status
        )        
        
    flash.set('Record updated successfully', 'success')
    redirect(URL('district','index'))  


@action("district/delete")
@action.uses("district/index.html",session,flash,db)
def delete(id=None):
    # if session['status']!='success':
    #     return 'Access Denied'
    request_id = request.query.get('id')
    if request_id:
        db(db.district.id == request_id).delete()
        
        flash.set('Record Delete successfully', 'error')      
        return dict(redirect(URL('district', 'index')))

    return locals()


@action("district/get_data", method=['GET', 'POST'])
@action.uses(db)
def get_data():
    # if session.status=="" or session.status==None:
    #   redirect(URL(c='login',f='index'))
    #Search Start##
    conditions = ""
    # if  request.query.get('cid') != None and request.query.get('cid') !='':
    #     cid = str(request.query.get('cid'))
    #     conditions += " and cid = '"+cid+"'"
    
    if  request.query.get('district') != None and request.query.get('district') !='':
        conditions += " and id = '"+str(request.query.get('district'))+"'"
        
    if  request.query.get('division') != None and request.query.get('division') !='':
        conditions += " and div_id = '"+str(request.query.get('division'))+"'"

    if  request.query.get('status') != None and request.query.get('status') !='':
        conditions += " and status = '"+str(request.query.get('status'))+"'"
    #Search End## 
    
    ##Paginate Start##
    total_rows = len(db.executesql( "SELECT * FROM district where 1 "+conditions, as_dict=True))

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
    SELECT * FROM `district` where 1"""+conditions+""" ORDER BY """+sort_column_name+""" """+sort_direction+""" LIMIT """+str(start)+""","""+str(end)+""";
    """

    data = db.executesql(sql, as_dict=True)
    
    return dict(data=data, total_rows=total_rows,recordsFiltered=total_rows,recordsTotal=total_rows,sort_column_name=sort_column_name)
    # return json.dumps(data)
