from py4web import action, request, abort, redirect, URL, response, Session
from py4web.utils.form import Form, FormStyleDefault
from yatl.helpers import A
from ..common import db, session, T, auth, flash
import json

@action("index")
@action.uses("index.html", session, flash,db)
def index():
    # return dict(redirect(URL('login', 'index')))
    return dict(redirect(URL('dashboard', 'index')))


# Category data
@action("default/get_category", method=['GET', 'POST'])
@action.uses(db)
def get_category():
    sql = """
    SELECT id as id, category_name as text FROM category
    """
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

# Pages data
@action("default/get_pages", method=['GET', 'POST'])
@action.uses(db)
def get_pages():
    sql = """
    SELECT id as id, page_name as text FROM page_setup
    """
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

# Papers data
@action("default/get_papers", method=['GET', 'POST'])
@action.uses(db)
def get_papers():
    sql = """
    SELECT id as id, paper_name as text FROM paper_list
    """
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

# Press data
@action("default/get_press", method=['GET', 'POST'])
@action.uses(db)
def get_press():
    sql = """
    SELECT id as id, press_name as text FROM press_setup
    """
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

@action("default/get_press_name", method=['GET', 'POST'])
@action.uses(db)
def get_press():
    sql = """
    SELECT press_name as id, press_name as text FROM press_setup
    """
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

# designation
@action("default/get_designation", method=['GET', 'POST'])
@action.uses(db)
def get_designation():
    sql = """
    SELECT id as id, desg_name as text FROM designation
    """
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

# Pages data
@action("default/get_reasons", method=['GET', 'POST'])
@action.uses(db)
def get_reasons():
    sql = """
    SELECT id as id, reason_name as text FROM unsold_reason
    """
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

# Division data
@action("default/get_division", method=['GET', 'POST'])
@action.uses(db)
def get_division():
    sql = """
    SELECT id as id, division as text FROM division
    """
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

# District data
@action("default/get_district", method=['GET', 'POST'])
@action.uses(db)
def get_district():
    sql = """
    SELECT id as id, district as text FROM district
    """
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)


# Division Wise District data
@action("default/get_division_wise_district", method=['GET', 'POST'])
@action.uses(db)
def get_division_wise_district():
    req_value = request.query.get('req_value')
    sql = """
    SELECT concat(id,'||',district) as id, district as text FROM district where status=1 and div_id="{req_value}"
    """.format(req_value=req_value)
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)


# Get Police Station
@action("default/get_police_station", method=['GET', 'POST'])
@action.uses(db)
def get_police_station():
    sql = """
    SELECT id as id, police_station as text FROM police_station
    """
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

# District Wise police station data
@action("default/get_district_wise_police_station", method=['GET', 'POST'])
@action.uses(db)
def get_district_wise_police_station():
    req_value = request.query.get('req_value')
    sql = """
    SELECT concat(id,'||',police_station) as id, police_station as text FROM police_station where status=1 and dist_id="{req_value}"
    """.format(req_value=req_value)
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)


# post office data
@action("default/get_post_office", method=['GET', 'POST'])
@action.uses(db)
def get_post_office():
    sql = """
    SELECT id as id, concat(post_code,' | ',post_office) as text FROM post_office
    """
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

# police station wise post office data
@action("default/get_policeStation_wise_postOffice", method=['GET', 'POST'])
@action.uses(db)
def get_policeStation_wise_postOffice():
    req_value = request.query.get('req_value')
    sql = """
    SELECT concat(id,' || ',post_code,' | ',post_office) as id, concat(post_code,' || ',post_office) as text FROM post_office where status=1 and pols_id="{req_value}"
    """.format(req_value=req_value)
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

# union data
@action("default/get_union", method=['GET', 'POST'])
@action.uses(db)
def get_union():
    sql = """
    SELECT id as id, union_name as text FROM unions
    """
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

# post office wise union data
@action("default/get_postOffice_wise_union", method=['GET', 'POST'])
@action.uses(db)
def get_postOffice_wise_union():
    req_value = request.query.get('req_value')
    sql = """
    SELECT concat(id,'||',union_name) as id, union_name as text FROM unions where status=1 and post_id="{req_value}"
    """.format(req_value=req_value)
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

# station data
@action("default/get_station", method=['GET', 'POST'])
@action.uses(db)
def get_station():
    sql = """
    SELECT id as id, concat(station_code,' | ',station) as text FROM station
    """
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

# Route data
@action("default/get_route", method=['GET', 'POST'])
@action.uses(db)
def get_station():
    sql = """
    SELECT id as id, concat(route_code,' | ',route_name) as text FROM route_setup
    """
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)
# Sub - Route data
@action("default/get_sub_route", method=['GET', 'POST'])
@action.uses(db)
def get_sub_route():
    sql = """
    SELECT id as id, concat(sub_route_code,' | ',sub_route_name) as text FROM sub_route
    """
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)


@action("default/get_general_manager", method=['GET', 'POST'])
@action.uses(db)
def get_general_manager():
    req_value = request.query.get('req_value')
    if str(req_value)=='Manager':
        req_value='General Manager'
    elif str(req_value)=="Regional Manager":
        req_value='General Manager'
    sql = """
    SELECT emp_id as id, concat(emp_id,' | ',emp_name) as text FROM employee  where 1 and emp_type="{req_value}"
    """.format(req_value=req_value)
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

# @action("default/get_manager", method=['GET', 'POST'])
# def get_manager():
#     req_value = request.query.get('req_value')
#     if str(req_value)=='Regional Manager':
#         req_value='Manager'
#     sql = """
#     SELECT emp_id as id, concat(emp_id,' | ',emp_name) as text FROM employee  where status=1 and emp_type="{req_value}"
#     """.format(req_value=req_value)
#     data = db.executesql(sql, as_dict=True)
#     return dict(results=data)

@action("default/get_gm_wise_manager", method=['GET', 'POST'])
@action.uses(db)
def get_manager():
    req_value = request.query.get('req_value')
    sql = """
    SELECT emp_id as id, concat(emp_id,' | ',emp_name) as text FROM employee  where 1 and gm_id="{req_value}"
    """.format(req_value=req_value)
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

@action("default/get_employees", method=['GET', 'POST'])
@action.uses(db)
def get_employees():
    req_value = request.query.get('req_value')
    con=''
    if str(req_value)=="regional_manager":
        con=" and emp_type='Regional Manager'"
    
    sql = """
    SELECT emp_id as id, concat(emp_id,' | ',emp_name) as text FROM employee  where 1 {con}
    """.format(con=con)
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

@action("default/get_agents", method=['GET', 'POST'])
@action.uses(db)
def get_agents():
    sql = """
    SELECT id as id, concat(agent_id,' | ',agent_name) as text FROM agent  where 1
    """
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

@action("default/get_vehicles", method=['GET', 'POST'])
@action.uses(db)
def get_vehicles():
    sql = """
    SELECT id as id, concat(vehicle_code,' | ',vehicle_name) as text FROM vehicle  where 1
    """
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

@action("default/get_agent_wise_station", method=['GET', 'POST'])
@action.uses(db)
def get_agent_wise_station():
    req_value = request.query.get('req_value')
    sql = """
    SELECT ea.*,s.station_code,s.def_copy,s.pack_type FROM employee_agent ea,station s  where ea.station_id=s.id and ea.agent_id="{req_value}"
    """.format(req_value=req_value)
    data = db.executesql(sql, as_dict=True)
    return dict(results=data)

@action("default/get_category_id_wise", method=['GET', 'POST'])
@action.uses(db)
def get_category_id_wise():
    req_value = request.query.get('req_value')
    sql = """
    SELECT * FROM category where id="{req_value}"
    """.format(req_value=req_value)
    data = db.executesql(sql, as_dict=True)
    cat_list=[]
    for rec in data:
        cat_list={
            'saturday': rec['sat_price'],
            'sunday': rec['sun_price'],
            'monday': rec['mon_price'],
            'tuesday': rec['tue_price'],
            'wednesday': rec['wed_price'],
            'thursday': rec['thu_price'],
            'friday': rec['fri_price']
        }
        
    return dict(results=cat_list)


