from py4web import action, request, abort, redirect, URL,response,Session
from py4web.utils.form import Form, FormStyleDefault
from yatl.helpers import A,TAG, XML
from pydal.validators import IS_IN_DB, IS_NOT_EMPTY
from ..common import db, session, T, auth,flash

@action("employees/index")
@action.uses("employees/index.html",session,flash,db)
def index(id=None):
    # if session['status']!='success':
    #     return 'Access Denied'
    emp_type_rows = db(db.combo_settings.key_name == 'emp_type').select()
    emp_types = str(emp_type_rows[0]['value']).split(',') if emp_type_rows else []
    return locals()

@action("employees/create", method=['GET', 'POST'])
@action.uses("employees/create.html", session,auth,T,db,flash)
def create(id=None): 
    emp_type_rows = db(db.combo_settings.key_name == 'emp_type').select()
    emp_types = str(emp_type_rows[0]['value']).split(',') if emp_type_rows else []
    
    designations=db(db.designation).select(db.designation.id,db.designation.desg_name)
    return locals()

@action("employees/submit", method=['POST'])
@action.uses("employees/index.html", session,auth,T,db,flash)
def submit(id=None): 
    emp_id=request.forms.get('emp_id')
    emp_name=request.forms.get('emp_name')
    email=request.forms.get('email')
    mobile=request.forms.get('mobile')
    designation=request.forms.get('designation')
    emp_type=request.forms.get('emp_type')
    general_manager=request.forms.get('general_manager')
    manager=request.forms.get('manager')
    
    status=request.forms.get('status')
    
    if str(status)!="1":
        status=0
    
    errors=[]
    if designation=='':
        errors.append('Enter Designation name') 
    # else:
    #     rows_check=db((db.designation.desg_name==desg_name)).select(db.designation.desg_name,limitby=(0,1))
    #     if rows_check:
    #         errors.append('Designation name already exist')
    if str(emp_name)=="" or emp_name is None:
        errors.append('Enter Employee Name') 
    if str(emp_type)=="" or emp_type is None:
        errors.append('Enter Employee Type') 
    if str(emp_type)=="Manager" and (general_manager=='' or general_manager is None):
        errors.append('Select General Manager')
    elif str(emp_type)=="Regional Manager"  and ((general_manager=='' or general_manager is None) or (manager=='' or manager is None)):
        errors.append('Select General Manager & Manager')
        
    if errors:
        msg = ''
        for item in errors:
            msg = msg + item + 'rdrdrd'
        flash.set(msg, 'warning')
        redirect(URL('employees','create')) 
        
    desg_id=0
    desg_name=''
    if designation:
        designations=str(designation).split('||')
        desg_id=designations[0]
        desg_name=designations[1]  
    
    gm_id=0
    mng_id=0
    if str(emp_type)=="Manager":
        gm_id=general_manager
    elif str(emp_type)=="Regional Manager":
        gm_id=general_manager
        mng_id=manager

    
    # insert function
    db.employee.insert(
        emp_id=emp_id,
        emp_name=emp_name,
        email=email,
        mobile=mobile,
        desg_id=desg_id,
        desg_name=desg_name,
        emp_type=emp_type,
        gm_id=gm_id,
        mng_id=mng_id,
        status=status
    )
        
    flash.set('Record added successfully', 'success')
    redirect(URL('employees','index'))   

@action("employees/edit", method=['GET', 'POST'])
@action.uses("employees/edit.html", session,auth,T,db,flash)
def edit(id=None): 
    request_id = request.query.get('id')
    if request_id:
        record = db(db.employee.id == request_id).select().first()
    emp_type_rows = db(db.combo_settings.key_name == 'emp_type').select()
    emp_types = str(emp_type_rows[0]['value']).split(',') if emp_type_rows else []
    
    designations=db(db.designation).select(db.designation.id,db.designation.desg_name)
    gm_employees=db((db.employee.emp_type=="General Manager")).select(db.employee.emp_id,db.employee.emp_name)
    mng_employees=db((db.employee.emp_type=="Manager")).select(db.employee.emp_id,db.employee.emp_name)
    return locals()

@action("employees/update", method=['POST'])
@action.uses("employees/index.html", session,auth,T,db,flash)
def update(id=None): 
    request_id = request.query.get('id')
    if request_id:
        record = db(db.employee.id == request_id).select().first()
        
    emp_id=request.forms.get('emp_id')
    emp_name=request.forms.get('emp_name')
    email=request.forms.get('email')
    mobile=request.forms.get('mobile')
    designation=request.forms.get('designation')
    emp_type=request.forms.get('emp_type')
    general_manager=request.forms.get('general_manager')
    manager=request.forms.get('manager')
    
    status=request.forms.get('status')
    
    if str(status)!="1":
        status=0
    
    errors=[]
    if designation=='':
        errors.append('Enter Designation name') 
    # else:
    #     rows_check=db((db.designation.desg_name==desg_name)).select(db.designation.desg_name,limitby=(0,1))
    #     if rows_check:
    #         errors.append('Designation name already exist')
    if str(emp_name)=="" or emp_name is None:
        errors.append('Enter Employee Name') 
    if str(emp_type)=="" or emp_type is None:
        errors.append('Enter Employee Type') 
    if str(emp_type)=="Manager" and (general_manager=='' or general_manager is None):
        errors.append('Select General Manager')
    elif str(emp_type)=="Regional Manager"  and ((general_manager=='' or general_manager is None) or (manager=='' or manager is None)):
        errors.append('Select General Manager & Manager')
    
    if errors:
        msg = ''
        for item in errors:
            msg = msg + item + 'rdrdrd'
        flash.set(msg, 'warning')
        redirect(URL('employees','edit',vars=dict(id=request_id))) 
    
    desg_id=0
    desg_name=''
    if designation:
        designations=str(designation).split('||')
        desg_id=designations[0]
        desg_name=designations[1]  
    
    gm_id=0
    mng_id=0
    if str(emp_type)=="Manager":
        gm_id=general_manager
    elif str(emp_type)=="Regional Manager":
        gm_id=general_manager
        mng_id=manager
        
    # insert function
    record.update_record(
        emp_id=emp_id,
        emp_name=emp_name,
        email=email,
        mobile=mobile,
        desg_id=desg_id,
        desg_name=desg_name,
        emp_type=emp_type,
        gm_id=gm_id,
        mng_id=mng_id,
        status=status
        )        
        
    flash.set('Record updated successfully', 'success')
    redirect(URL('employees','index'))  


@action("employees/delete")
@action.uses("employees/index.html",session,flash,db)
def delete(id=None):
    # if session['status']!='success':
    #     return 'Access Denied'
    request_id = request.query.get('id')
    if request_id:
        db(db.employee.id == request_id).delete()
        
        flash.set('Record Delete successfully', 'error')      
        return dict(redirect(URL('employees', 'index')))

    return locals()


@action("employees/get_data", method=['GET', 'POST'])
@action.uses(db)
def get_data():
    # if session.status=="" or session.status==None:
    #   redirect(URL(c='login',f='index'))
    #Search Start##
    conditions = ""
    # if  request.query.get('cid') != None and request.query.get('cid') !='':
    #     cid = str(request.query.get('cid'))
    #     conditions += " and cid = '"+cid+"'"
    
    if  request.query.get('emp_name') != None and request.query.get('emp_name') !='':
        conditions += " and emp.emp_id = '"+str(request.query.get('emp_name'))+"'"
        
    if  request.query.get('emp_type') != None and request.query.get('emp_type') !='':
        conditions += " and emp.emp_type = '"+str(request.query.get('emp_type'))+"'"
        
    if  request.query.get('desg_name') != None and request.query.get('desg_name') !='':
        conditions += " and emp.desg_id = '"+str(request.query.get('desg_name'))+"'"

    if  request.query.get('status') != None and request.query.get('status') !='':
        conditions += " and emp.status = '"+str(request.query.get('status'))+"'"
    #Search End## 
    
    ##Paginate Start##
    total_rows = len(db.executesql( "SELECT emp.* FROM employee emp where 1 "+conditions, as_dict=True))

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
        SELECT 
        emp.id as id,
        emp.emp_id as emp_id,
        emp.emp_name as emp_name,
        emp.emp_type as emp_type,
        emp.mobile as mobile,
        emp.desg_name as desg_name,
        emp.gm_id as gm_id,
        gm.emp_name AS gm_name,
        emp.mng_id as mng_id,
        mng.emp_name AS mng_name,
        emp.status
    FROM 
        employee emp
    LEFT JOIN 
        employee gm ON emp.gm_id = gm.emp_id
    LEFT JOIN 
        employee mng ON emp.mng_id = mng.emp_id where 1 """+conditions+""" ORDER BY emp."""+sort_column_name+""" """+sort_direction+""" LIMIT """+str(start)+""","""+str(end)+""";
    """

    data = db.executesql(sql, as_dict=True)
    
    return dict(data=data, total_rows=total_rows,recordsFiltered=total_rows,recordsTotal=total_rows,sort_column_name=sort_column_name)
    # return json.dumps(data)
