from py4web import action, request, abort, redirect, URL,response,Session
from py4web.utils.form import Form, FormStyleDefault
from yatl.helpers import A,TAG, XML
from pydal.validators import IS_IN_DB, IS_NOT_EMPTY
from ..common import db, session, T, auth,flash
from ..common_cid import date_time_list
import random

@action("order_entry/index")
@action.uses("order_entry/index.html",session,flash,db)
def index(id=None):
    # if session['status']!='success':
    #     return 'Access Denied'
    
    
    return locals()

@action("order_entry/create", method=['GET', 'POST'])
@action.uses("order_entry/create.html", session,auth,T,db,flash)
def create(id=None): 
    
    random_number = random.randint(1000, 9999)
    order_id=str(date_time_list['currentdate'])+str(random_number)

    categories=db(db.category).select()
    agents=db(db.agent).select()
    sub_routes=db(db.sub_route).select()
    vehicles=db(db.vehicle).select()
    
    sales_rows = db(db.combo_settings.key_name == 'sales_type').select()
    sales_types = str(sales_rows[0]['value']).split(',') if sales_rows else []
    
    edition_rows = db(db.combo_settings.key_name == 'edition').select()
    editions = str(edition_rows[0]['value']).split(',') if edition_rows else []
    
    pack_rows = db(db.combo_settings.key_name == 'station_pack_type').select()
    pack_types = str(pack_rows[0]['value']).split(',') if pack_rows else []
    
    return locals()

@action("order_entry/submit", method=['POST'])
@action.uses("order_entry/index.html", session,auth,T,db,flash)
def submit(id=None): 
    order_id=request.forms.get('order_id')
    order_date=request.forms.get('order_date')
    agent=request.forms.get('agent')
    category=request.forms.get('category')
    rate=request.forms.get('rate')
    sales_type=request.forms.get('sales_type')
    sub_route=request.forms.get('sub_route')
    vehicle=request.forms.get('vehicle')
    edition=request.forms.get('edition')
    sales_type_option=request.forms.get('sales_type_option')
    payment_type=request.forms.get('payment_type')
    station_list=request.forms.get('station')
    
    
    errors=[]
    if str(order_id)=='' or order_id is None:
        errors.append('Enter order id') 
    else:
        rows_check=db((db.order_head.order_id==order_id)).select(db.order_head.order_id,limitby=(0,1))
        if rows_check:
            errors.append('Order id already exist! please refresh the page.')
    if str(order_date)=='' or order_date is None:
        errors.append('Enter order date') 
    if str(agent)=="" or agent is None:
        errors.append('Enter agent') 
    if str(category)=="" or category is None:
        errors.append('Enter category') 
    if str(rate)=="" or rate is None:
        errors.append('Enter rate') 
    if str(sales_type)=="" or sales_type is None:
        errors.append('Enter sales_type') 
    if str(sub_route)=="" or sub_route is None:
        errors.append('Enter sub_route') 
        
    if str(vehicle)=="" or vehicle is None:
        errors.append('Enter vehicle') 
    if str(edition)=="" or edition is None:
        errors.append('Enter edition') 
    if str(station_list)=="" or station_list is None:
        errors.append('Station is required for this order') 
        
    if errors:
        msg = ''
        for item in errors:
            msg = msg + item + 'rdrdrd'
        flash.set(msg, 'warning')
        redirect(URL('order_entry','create')) 
    
    agent_id=0
    agent_name=''
    if agent:
        agents=str(agent).split('||')
        agent_id=agents[0]
        agent_name=agents[1] 
        
    category_id=0
    category_name=''
    if category:
        categorys=str(category).split('||')
        category_id=categorys[0]
        category_name=categorys[1] 
        
    sub_route_id=0
    sub_route_name=''
    if sub_route:
        sub_routes=str(sub_route).split('||')
        sub_route_id=sub_routes[0]
        sub_route_name=sub_routes[1] 
        
    vehicle_id=0
    vehicle_name=''
    if vehicle:
        vehicles=str(vehicle).split('||')
        vehicle_id=vehicles[0]
        vehicle_name=vehicles[1] 
        
        
    if payment_type is None or str(payment_type)=="None":
        payment_type = ""
    
    # insert function
    head_id=db.order_head.insert(
        order_id=order_id,
        order_date=order_date,
        category_id=category_id,
        rate=rate,
        agent_id=agent_id,
        sub_route_id=sub_route_id,
        vehicle_id=vehicle_id,
        edition=edition,
        sales_type=sales_type,
        sales_type_option=sales_type_option,
        payment_type=payment_type,
        status=0,
        post_status=0,
        sync_status=0,
        modify_status=0
    )
    
    details_list=[]
    if isinstance(station_list, str):
        station_list = [station_list]
    
    for station in station_list:
        station_id=str(station).split('||')[0]
        station_name=str(station).split('||')[1]
        quantity=request.forms.get('quantity_'+str(station_id))
        bonus_qty=request.forms.get('bonus_qty_'+str(station_id))
        complementary_qty=request.forms.get('complementary_qty_'+str(station_id))
        pack_type=request.forms.get('pack_type_'+str(station_id))
        details_list.append({
            'head_id':head_id,
            'order_id':order_id,
            'station_id':station_id,
            'station_name':station_name,
            'quantity':quantity,
            'bonus_qty':bonus_qty,
            'complementary_qty':complementary_qty,
            'pack_type':pack_type
            })
    db.order_details.bulk_insert(details_list)
        
    flash.set('Record added successfully', 'success')
    redirect(URL('order_entry','index'))   

@action("order_entry/edit", method=['GET', 'POST'])
@action.uses("order_entry/edit.html", session,auth,T,db,flash)
def edit(id=None): 
    request_id = request.query.get('id')
    if request_id:
        record = db(db.order_head.id == request_id).select().first()
        details_record = db((db.order_details.head_id == request_id) & (db.order_details.station_id == db.station.id)).select()
    
    order_id=record.order_id
    categories=db(db.category).select()
    agents=db(db.agent).select()
    sub_routes=db(db.sub_route).select()
    vehicles=db(db.vehicle).select()
    
    sales_rows = db(db.combo_settings.key_name == 'sales_type').select()
    sales_types = str(sales_rows[0]['value']).split(',') if sales_rows else []
    
    edition_rows = db(db.combo_settings.key_name == 'edition').select()
    editions = str(edition_rows[0]['value']).split(',') if edition_rows else []
    
    pack_rows = db(db.combo_settings.key_name == 'station_pack_type').select()
    pack_types = str(pack_rows[0]['value']).split(',') if pack_rows else []
            
    return locals()

@action("order_entry/update", method=['POST'])
@action.uses("order_entry/index.html", session,auth,T)
def update(id=None): 
    request_id = request.query.get('id')
    if request_id:
        record = db(db.order_head.id == request_id).select().first()
        details_record = db(db.order_details.head_id == request_id).select()
        head_id=record.id
        order_id=record.order_id
        
    order_date=request.forms.get('order_date')
    agent=request.forms.get('agent')
    category=request.forms.get('category')
    rate=request.forms.get('rate')
    sales_type=request.forms.get('sales_type')
    sub_route=request.forms.get('sub_route')
    vehicle=request.forms.get('vehicle')
    edition=request.forms.get('edition')
    sales_type_option=request.forms.get('sales_type_option')
    payment_type=request.forms.get('payment_type')
    station_list=request.forms.get('station')
    
    
    errors=[]
    if str(order_id)=='' or order_id is None:
        errors.append('Enter order id') 
    else:
        rows_check=db((db.order_head.order_id==order_id) & (db.order_head.id!=request_id)).select(db.order_head.order_id,limitby=(0,1))
        if rows_check:
            errors.append('Order id already exist! please refresh the page.')
    if str(order_date)=='' or order_date is None:
        errors.append('Enter order date') 
    if str(agent)=="" or agent is None:
        errors.append('Enter agent') 
    if str(category)=="" or category is None:
        errors.append('Enter category') 
    if str(rate)=="" or rate is None:
        errors.append('Enter rate') 
    if str(sales_type)=="" or sales_type is None:
        errors.append('Enter sales_type') 
    if str(sub_route)=="" or sub_route is None:
        errors.append('Enter sub_route') 
        
    if str(vehicle)=="" or vehicle is None:
        errors.append('Enter vehicle') 
    if str(edition)=="" or edition is None:
        errors.append('Enter edition') 
    if str(station_list)=="" or station_list is None:
        errors.append('Station is required for this order') 
    
    if errors:
        msg = ''
        for item in errors:
            msg = msg + item + 'rdrdrd'
        flash.set(msg, 'warning')
        redirect(URL('order_entry','edit',vars=dict(id=request_id))) 
    
    agent_id=0
    agent_name=''
    if agent:
        agents=str(agent).split('||')
        agent_id=agents[0]
        agent_name=agents[1] 
        
    category_id=0
    category_name=''
    if category:
        categorys=str(category).split('||')
        category_id=categorys[0]
        category_name=categorys[1] 
        
    sub_route_id=0
    sub_route_name=''
    if sub_route:
        sub_routes=str(sub_route).split('||')
        sub_route_id=sub_routes[0]
        sub_route_name=sub_routes[1] 
        
    vehicle_id=0
    vehicle_name=''
    if vehicle:
        vehicles=str(vehicle).split('||')
        vehicle_id=vehicles[0]
        vehicle_name=vehicles[1] 
        
        
    if payment_type is None or str(payment_type)=="None":
        payment_type = ""
        
    # insert function
    record.update_record(
        order_date=order_date,
        category_id=category_id,
        rate=rate,
        agent_id=agent_id,
        sub_route_id=sub_route_id,
        vehicle_id=vehicle_id,
        edition=edition,
        sales_type=sales_type,
        sales_type_option=sales_type_option,
        payment_type=payment_type
        )   
    
    details_list=[]
    if isinstance(station_list, str):
        station_list = [station_list]
    
    for station in station_list:
        station_id=str(station).split('||')[0]
        station_name=str(station).split('||')[1]
        quantity=request.forms.get('quantity_'+str(station_id))
        bonus_qty=request.forms.get('bonus_qty_'+str(station_id))
        complementary_qty=request.forms.get('complementary_qty_'+str(station_id))
        pack_type=request.forms.get('pack_type_'+str(station_id))
        details_list.append({
            'head_id':head_id,
            'order_id':order_id,
            'station_id':station_id,
            'station_name':station_name,
            'quantity':quantity,
            'bonus_qty':bonus_qty,
            'complementary_qty':complementary_qty,
            'pack_type':pack_type
            })
    
    
    db(db.order_details.head_id == head_id).delete()
    
    db.order_details.bulk_insert(details_list)
    
        
    flash.set('Record updated successfully', 'success')
    redirect(URL('order_entry','index'))  


@action("order_entry/delete")
@action.uses("order_entry/index.html",session,flash,db)
def delete(id=None):
    # if session['status']!='success':
    #     return 'Access Denied'
    request_id = request.query.get('id')
    if request_id:
        db(db.order_head.id == request_id).delete()
        db(db.order_details.head_id == request_id).delete()
        
        flash.set('Record Delete successfully', 'error')      
        return dict(redirect(URL('order_entry', 'index')))

    return locals()


@action("order_entry/get_data", method=['GET', 'POST'])
@action.uses(db)
def get_data():
    # if session.status=="" or session.status==None:
    #   redirect(URL(c='login',f='index'))
    #Search Start##
    conditions = ""
    # if  request.query.get('cid') != None and request.query.get('cid') !='':
    #     cid = str(request.query.get('cid'))
    #     conditions += " and cid = '"+cid+"'"
    
    if  request.query.get('vehicle_name') != None and request.query.get('vehicle_name') !='':
        conditions += " and oh.vehicle_id = '"+str(request.query.get('vehicle_name'))+"'"
        
    if  request.query.get('agent_name') != None and request.query.get('agent_name') !='':
        conditions += " and oh.agent_id = '"+str(request.query.get('agent_name'))+"'"
        
    if  request.query.get('order_date') != None and request.query.get('order_date') !='':
        conditions += " and oh.order_date = '"+str(request.query.get('order_date'))+"'"
        
    if  request.query.get('category_name') != None and request.query.get('category_name') !='':
        conditions += " and oh.category_id = '"+str(request.query.get('category_name'))+"'"
        
    # if  request.query.get('owner_name') != None and request.query.get('owner_name') !='':
    #     conditions += " and owner_name like '%"+str(request.query.get('owner_name'))+"%'"
        
    # if  request.query.get('status') != None and request.query.get('status') !='':
    #     conditions += " and status = '"+str(request.query.get('status'))+"'"
    #Search End## 
    
    ##Paginate Start##
    total_rows = len(db.executesql( "SELECT oh.* FROM order_head oh where 1 "+conditions, as_dict=True))

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
        SELECT oh.* ,a.agent_id as agent_code,a.agent_name,c.category_name,sr.sub_route_code,sr.sub_route_name,v.vehicle_code,v.vehicle_name
        FROM order_head oh
        LEFT JOIN agent a on oh.agent_id=a.id
        LEFT JOIN category c on oh.category_id=c.id
        LEFT JOIN sub_route sr on oh.sub_route_id=sr.id
        LEFT JOIN vehicle v on oh.vehicle_id=v.id
        where 1 """+conditions+""" ORDER BY oh."""+sort_column_name+""" """+sort_direction+""" LIMIT """+str(start)+""","""+str(end)+""";
    """
    
    data = db.executesql(sql, as_dict=True)
    
    return dict(data=data, total_rows=total_rows,recordsFiltered=total_rows,recordsTotal=total_rows,sort_column_name=sort_column_name)

