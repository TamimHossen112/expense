"""
This file defines the database models
"""
from .common import db, Field, session,T
from pydal.validators import *
import os
from py4web import request

### Define your table below
#
# db.define_table('thing', Field('name'))
#
## always commit your models to avoid problems later
#
# db.commit()

from .common_cid import date_fixed

APP_FOLDER = os.path.dirname(__file__)

def get_user_id():
    return session.get('user_id', '101')

cid='SKF'
#---------------------start EXPENSE Tables---------------------
signature=db.Table(db,'signature',
                Field('field1','string',length=100,default=''), 
                Field('field2','integer',default=0),
                Field('note','string',length=255,default=''),  
                Field('created_on','datetime',default=date_fixed),
                Field('created_by',default=get_user_id),
                Field('updated_on','datetime',update=date_fixed),
                Field('updated_by',update=get_user_id),
                )

#################### Expense Tables Start #####################

# Vendor Table
db.define_table('vendor',
    Field('cid', 'string', length=20, default=cid),
    Field('vendor_name', 'string', length=255),
    Field('contact', 'string', length=255),
    Field('vendor_address', 'string', length=255),
    Field('trade_license_no', 'string', length=100),
    signature,
    migrate=False
)

# Requisition Table
db.define_table('requisition',
    Field('cid', 'string', length=20, default=cid),
    Field('asset_type', 'string', length=100),
    Field('emp_id', 'string', length=100),
    Field('emp_name', 'string', length=100),
    Field('designation', 'string', length=100),
    Field('tr_code', 'string', length=100),
    Field('head_office', 'string', length=100),
    Field('joining_date', 'date'),
    Field('license_issue_date', 'date'),
    Field('license_expire_date', 'date'),
    Field('license_number', 'string', length=100),
    Field('license_attach', 'string', length=255),
    Field('photo_attach', 'string', length=255),
    Field('fm_approval', 'string', default='no',requires=IS_IN_SET(['yes', 'no'])),
    Field('rsm_approval', 'string', default='no',requires=IS_IN_SET(['yes', 'no'])),
    Field('sm_approval', 'string', default='no',requires=IS_IN_SET(['yes', 'no'])),
    Field('agm_approval', 'string', default='no',requires=IS_IN_SET(['yes', 'no'])),
    Field('gm_approval', 'string', default='no',requires=IS_IN_SET(['yes', 'no'])),
    Field('hr_approval', 'string', default='no',requires=IS_IN_SET(['yes', 'no'])),
    Field('ed_approval', 'string', default='no',requires=IS_IN_SET(['yes', 'no'])),
    signature,
    migrate=False
)

# Purchase Head Table
db.define_table('purchase_head',
    Field('cid', 'string', length=20, default=cid),
    Field('req_id', 'integer', length=11,default=0),
    Field('purchase_id', 'integer', length=11,default=0),
    Field('vendor_id', 'integer',length=11,default=0),
    Field('vendor_name', 'string', length=255),
    Field('bill_no', 'string', length=100),
    Field('total_price', 'float'),
    Field('total_discount', 'float'),
    Field('payment_type', 'string', length=100),
    Field('recived_date', 'date'),
    Field('payment_status', 'string', length=100),
    Field('purchase_status', 'string', length=100),
    Field('remarks', 'string', length=500),
    signature,
    migrate=False
)

# Purchase Details Table
db.define_table('purchase_details',
    Field('cid', 'string', length=20, default=cid),
    Field('head_id', 'integer', length=11, default=0 ),
    Field('purchase_id', 'integer', length=11,default=0),
    Field('req_id', 'integer', length=11,default=0),
    Field('asset_type', 'string', length=100),
    Field('asset_name', 'string', length=255),
    Field('asset_desc', 'string', length=500),
    Field('purchase_date', 'date'),
    Field('recived_date', 'date'),
    Field('item_price', 'float'),
    Field('item_discount', 'float'),
    Field('payment_type', 'string', length=100),
    Field('payment_status', 'string', length=100),
    Field('purchase_status', 'string', length=100),
    signature,
    migrate=False
)

# Asset Table
db.define_table('asset',
    Field('cid', 'string', length=20, default=cid),
    Field('asset_id', 'integer', length=11, default=0),
    Field('purchase_id', 'integer', length=11, default=0),
    Field('asset_type', 'string', length=100),
    Field('asset_name', 'string', length=255),
    Field('asset_desc', 'string',length=500),
    Field('asset_model', 'string', length=255),
    Field('model_year', 'string', length=100),
    Field('reg_number', 'string', length=100),
    Field('engine_number', 'string', length=100),
    Field('engine_info', 'string', length=500),
    Field('chassis_number', 'string', length=100),
    Field('purchase_price', 'float'),
    Field('user_id', 'string', length=100),
    Field('user_name', 'string', length=100),
    Field('current_location', 'string', length=255),
    Field('asset_condition', 'string', length=100),
    Field('first_issue_date', 'date'),
    Field('asset_status', 'string', length=100),
    signature,
    migrate=False
)

# # Asset Details Table      ----------------LATERRRRRRRRRRRRRRR----------------
# db.define_table('asset_details',
#     Field('cid', 'string', length=20, default=cid),
#     Field('asset_id', 'integer', length=11, default=0),
#     Field('sl', 'integer'),
#     Field('key', 'string', length=255),
#     Field('caption', 'string', length=255),
#     Field('value', 'string', length=255),
#     signature,
#     migrate=False
# )

# Asset Document Table
db.define_table('asset_doc',
    Field('cid', 'string', length=20, default=cid),
    Field('asset_id', 'integer',length=11, default=0),
    Field('doc_id', 'integer', length=11, default=0),
    Field('doc_type', 'string', length=100),
    Field('file_name', 'string', length=255),
    Field('file_path', 'string', length=255),
    Field('doc_expire_date', 'date'),
    Field('ref_emp_id', 'string', length=11, default=0),
    Field('status', 'string', length=100),
    signature,
    migrate=False
)

# Transaction Config Table
db.define_table('tr_config',
    Field('cid', 'string', length=20, default=cid),
    Field('tr_type', 'string', length=100),
    Field('sl', 'integer'),
    Field('section', 'string',length=100),
    Field('key', 'string', length=255),
    Field('caption', 'string', length=255),
    Field('value', 'string', length=255),
    Field('value_type', 'string', length=100),
    Field('source_api', 'string', length=255),
    Field('value_list', 'string',length=500),
    Field('default_value', 'string', length=255),
    signature,
    migrate=False
)

# Transaction Head Table
db.define_table('tr_head',
    Field('cid', 'string', length=20, default=cid),
    Field('tr_id', 'integer', length=11, default=0),
    Field('trans_type', 'string', length=100),
    Field('asset_id', 'integer',length=11, default=0),
    Field('asset_type', 'string', length=100),
    Field('tr_date', 'date'),
    signature,
    migrate=False
)

# Transaction Details Table
db.define_table('tr_details',
    Field('cid', 'string', length=20, default=cid),
    Field('tr_id', 'integer', length=11, default=0),
    Field('sl', 'integer'),
    Field('key', 'string', length=255),
    Field('caption', 'string', length=255),
    Field('value', 'string', length=255),
    signature,
    migrate=False
)


#*******************start combo_settings Tables*******************
# db.define_table('combo_settings',
#                 Field('cid','string',length=20,default=cid),
#                 Field('key_name','string',length=100),
#                 Field('value','string',length=500),
#                 migrate=False
#                 )
# #*******************end combo_settings Tables*********************


# #*******************start Category Tables*******************
# db.define_table('category',
#                 Field('cid','string',length=20,default=cid),
#                 Field('category_name','string',length=100),
#                 Field('sat_no_page','string',length=5),
#                 Field('sat_price','string',length=5),
#                 Field('sun_no_page','string',length=5),
#                 Field('sun_price','string',length=5),
#                 Field('mon_no_page','string',length=5),
#                 Field('mon_price','string',length=5),
#                 Field('tue_no_page','string',length=5),
#                 Field('tue_price','string',length=5),
#                 Field('wed_no_page','string',length=5),
#                 Field('wed_price','string',length=5),
#                 Field('thu_no_page','string',length=5),
#                 Field('thu_price','string',length=5),
#                 Field('fri_no_page','string',length=5),
#                 Field('fri_price','string',length=5),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )

# db.define_table('category_log',
#                 Field('cid','string',length=20,default=cid),
#                 Field('category_name','string',length=100),
#                 Field('old_category','text'),
#                 Field('new_category','text'),
                
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )

# #*******************end Category Tables*******************

# #*******************start page Tables*******************
# db.define_table('page_setup',
#                 Field('cid','string',length=20,default=cid),
#                 Field('page_name','string',length=100),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end page Tables*******************

# #*******************start press Tables*******************
# db.define_table('press_setup',
#                 Field('cid','string',length=20,default=cid),
#                 Field('press_name','string',length=100),
#                 Field('location','string',length=200),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end press Tables*******************

# #*******************start ctp setup Tables*******************
# db.define_table('ctp_setup',
#                 Field('cid','string',length=20,default=cid),
#                 Field('press_id','string',length=10),
#                 Field('press_name','string',length=100),
#                 Field('page_id','string',length=100),
#                 Field('page_name','string',length=200),
#                 Field('default_time','time'),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end ctp setup Tables*******************


# #*******************start paper_list Tables*******************
# db.define_table('paper_list',
#                 Field('cid','string',length=20,default=cid),
#                 Field('paper_name','string',length=200),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end paper_list Tables*******************

# #*******************start division Tables*******************
# db.define_table('division',
#                 Field('cid','string',length=20,default=cid),
#                 Field('division','string',length=100),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end division Tables*******************

# #*******************start district Tables*******************
# db.define_table('district',
#                 Field('cid','string',length=20,default=cid),
#                 Field('district','string',length=100),
#                 Field('div_id','integer',length=11,default=0),
#                 Field('division','string',length=100),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end district Tables*******************

# #*******************start police_station Tables*******************
# db.define_table('police_station',
#                 Field('cid','string',length=20,default=cid),
#                 Field('police_station','string',length=100),
#                 Field('dist_id','integer',length=11,default=0),
#                 Field('district','string',length=100),
#                 Field('div_id','integer',length=11,default=0),
#                 Field('division','string',length=100),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end distrpolice_stationict Tables*******************

# #*******************start post_office Tables*******************
# db.define_table('post_office',
#                 Field('cid','string',length=20,default=cid),
#                 Field('post_code','string',length=50),
#                 Field('post_office','string',length=100),
#                 Field('pols_id','integer',length=11,default=0),
#                 Field('police_station','string',length=100),
#                 Field('dist_id','integer',length=11,default=0),
#                 Field('district','string',length=100),
#                 Field('div_id','integer',length=11,default=0),
#                 Field('division','string',length=100),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end post_office Tables*******************

# #*******************start unions Tables*******************
# db.define_table('unions',
#                 Field('cid','string',length=20,default=cid),
#                 Field('union_name','string',length=200),
#                 Field('post_id','string',length=50),
#                 Field('post_office','string',length=100),
#                 Field('pols_id','integer',length=11,default=0),
#                 Field('police_station','string',length=100),
#                 Field('dist_id','integer',length=11,default=0),
#                 Field('district','string',length=100),
#                 Field('div_id','integer',length=11,default=0),
#                 Field('division','string',length=100),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end unions Tables*******************

# #*******************start station Tables*******************
# db.define_table('station',
#                 Field('cid','string',length=20,default=cid),
#                 Field('station_code','string',length=10),
#                 Field('station','string',length=200),
#                 Field('station_bangla','string',length=200),
#                 Field('union_id','string',length=50),
#                 Field('union_name','string',length=200),
#                 Field('post_id','string',length=50),
#                 Field('post_office','string',length=100),
#                 Field('pols_id','integer',length=11,default=0),
#                 Field('police_station','string',length=100),
#                 Field('dist_id','integer',length=11,default=0),
#                 Field('district','string',length=100),
#                 Field('div_id','integer',length=11,default=0),
#                 Field('division','string',length=100),
#                 Field('def_copy','integer'),
#                 Field('pack_type','string',length=100),
#                 Field('sorting_order','float'),
                
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end station Tables*******************

# #*******************start Route Tables*******************
# db.define_table('route_setup',
#                 Field('cid','string',length=20,default=cid),
#                 Field('route_code','string',length=10),
#                 Field('route_name','string',length=200),
#                 Field('route_bangla','string',length=200),
#                 Field('sp_id','string',length=50),
#                 Field('start_point','string',length=200),
#                 Field('ep_id','string',length=50),
#                 Field('end_point','string',length=100),
#                 Field('sorting_order','float'),
#                 Field('distance_km','float'),
#                 Field('departure_time','time'),
#                 Field('arrive_time','time'),
                
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end Route Tables*******************

# #*******************start SUB Route Tables*******************
# db.define_table('sub_route',
#                 Field('cid','string',length=20,default=cid),
#                 Field('sub_route_code','string',length=10),
#                 Field('sub_route_name','string',length=200),
#                 Field('sub_route_bangla','string',length=200),
#                 Field('route_id','string',length=50),
#                 Field('route_name','string',length=200),
#                 Field('sp_id','string',length=50),
#                 Field('start_point','string',length=200),
#                 Field('ep_id','string',length=50),
#                 Field('end_point','string',length=100),
#                 Field('sorting_order','float'),
#                 Field('departure_time','time'),
#                 Field('arrive_time','time'),
#                 Field('press','string',length=100),
#                 Field('location','string',length=100),
                
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end sub Route Tables*******************

# #*******************start unsold_reason Tables*******************
# db.define_table('unsold_reason',
#                 Field('cid','string',length=20,default=cid),
#                 Field('reason_type','string',length=200),
#                 Field('reason_name','string',length=200),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end unsold_reason Tables*******************

# #*******************start population Tables*******************
# db.define_table('population',
#                 Field('cid','string',length=20,default=cid),
#                 Field('station_id','string',length=10),
#                 Field('station_name','string',length=200),
#                 Field('population','string',length=10),
#                 Field('literacy','string',length=10),
#                 Field('total_subscriber','string',length=10),
#                 Field('reguler_subscriber','string',length=10),
#                 Field('floating_subscriber','string',length=10),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end population Tables*******************


# #*******************start designation Tables*******************
# db.define_table('designation',
#                 Field('cid','string',length=20,default=cid),
#                 Field('desg_name','string',length=100),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end designation Tables*******************


# #*******************start employee Tables*******************
# db.define_table('employee',
#                 Field('cid','string',length=20,default=cid),
#                 Field('emp_id','string',length=10),
#                 Field('emp_name','string',length=200),
#                 Field('email','string',length=100),
#                 Field('mobile','string',length=14),
#                 Field('desg_id','string',length=10),
#                 Field('desg_name','string',length=200),
#                 Field('emp_type','string',length=50),
#                 Field('gm_id','string',length=10),
#                 Field('mng_id','string',length=10),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end employee Tables*******************

# #*******************start agent Tables*******************
# db.define_table('agent',
#                 Field('cid','string',length=20,default=cid),
#                 Field('agent_id','string',length=10),
#                 Field('agent_name','string',length=200),
#                 Field('agent_bangla','string',length=200),
#                 Field('billing_accpac_code','string',length=50),
#                 Field('sub_route_id','string',length=100),
#                 Field('sub_route_name','string',length=100),
#                 Field('mobile','string',length=14),
#                 Field('sorting_order','integer'),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end agent Tables*******************

# #*******************start agent_sales_info Tables*******************
# db.define_table('agent_sales_info',
#                 Field('cid','string',length=20,default=cid),
#                 Field('agent_id','string',length=10),
#                 Field('agent_name','string',length=200),
#                 Field('paper_id','string',length=10),
#                 Field('paper_name','string',length=200),
#                 Field('quantity','integer'),
#                 signature,
#                 migrate=False
#                 )
# #*******************end agent_sales_info Tables*******************


# #*******************start employee_agent Tables*******************
# db.define_table('employee_agent',
#                 Field('cid','string',length=20,default=cid),
#                 Field('rm_id','string',length=10),
#                 Field('rm_name','string',length=200),
#                 Field('agent_id','string',length=10),
#                 Field('agent_name','string',length=200),
#                 Field('station_id','string',length=10),
#                 Field('station_name','string',length=200),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end employee_agent Tables*******************

# #*******************start vehicle Tables*******************
# db.define_table('vehicle',
#                 Field('cid','string',length=20,default=cid),
#                 Field('vehicle_code','string',length=10),
#                 Field('vehicle_name','string',length=200),
#                 Field('vehicle_bangla','string',length=200),
#                 Field('vehicle_reg_no','string',length=100),
#                 Field('capacity','integer'),
#                 Field('rate_per_trip','float'),
#                 Field('owner_name','string',length=200),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end vehicle Tables*******************

# #*******************start vehicle_route Tables*******************
# db.define_table('vehicle_route',
#                 Field('cid','string',length=20,default=cid),
#                 Field('vehicle_id','string',length=10),
#                 Field('vehicle_name','string',length=200),
#                 Field('driver_name','string',length=200),
#                 Field('license_no','string',length=100),
#                 Field('route_id','string',length=10),
#                 Field('route_name','string',length=200),
#                 Field('sub_route_id','string',length=10),
#                 Field('sub_route_name','string',length=200),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end vehicle_route Tables*******************

# #*******************start transport_maintenance_head Tables*******************
# db.define_table('transport_maintenance_head',
#                 Field('cid','string',length=20,default=cid),
#                 Field('trans_id','string',length=20),
#                 Field('trans_date','date'),
#                 Field('station_id','string',length=10),
#                 Field('station_name','string',length=100),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end transport_maintenance_head Tables*******************

# #*******************start transport_maintenance_details Tables*******************
# db.define_table('transport_maintenance_details',
#                 Field('cid','string',length=20,default=cid),
#                 Field('head_id','string',length=20),
#                 Field('trans_id','string',length=20),
#                 Field('paper_id','string',length=10),
#                 Field('paper_name','string',length=200),
#                 Field('departure_time','time'),
#                 Field('arrive_time','time'),
#                 Field('reason_of_delay','string',length=200),
#                 Field('status','integer',length=1,default=1),
#                 signature,
#                 migrate=False
#                 )
# #*******************end transport_maintenance_details Tables*******************


# #*******************start order_head Tables*******************
# db.define_table('order_head',
#                 Field('cid','string',length=20,default=cid),
#                 Field('order_id','string',length=20),
#                 Field('order_date','date'),
#                 Field('category_id','string',length=10),
#                 Field('rate','float'),
#                 Field('agent_id','string',length=10),
#                 Field('sub_route_id','string',length=10),
#                 Field('vehicle_id','string',length=10),
#                 Field('edition','string',length=100),
#                 Field('sales_type','string',length=100),
#                 Field('sales_type_option','string',length=100),
#                 Field('payment_type','string',length=100,default=""),
#                 Field('status','integer',length=1,default=1),
#                 Field('post_status','integer',length=1,default=1),
#                 Field('sync_status','integer',length=1,default=1),
#                 Field('modify_status','integer',length=1,default=1),
#                 Field('modify_reason','string',length=200,default=""),            
#                 signature,
#                 migrate=False
#                 )
# #*******************end order_head Tables*******************

# #*******************start order_details Tables*******************
# db.define_table('order_details',
#                 Field('cid','string',length=20,default=cid),
#                 Field('head_id','string',length=20),
#                 Field('order_id','string',length=20),
#                 Field('station_id','string',length=10),
#                 Field('station_name','string',length=200),
#                 Field('quantity','integer'),
#                 Field('bonus_qty','integer'),
#                 Field('complementary_qty','integer'),
#                 Field('pack_type','string',length=200),
#                 Field('day_def_qty','integer',default=0),
#                 Field('day_change_qty','integer',default=0),
#                 signature,
#                 migrate=False
#                 )
# #*******************end order_details Tables*******************

# #---------------------End Circulation Tables---------------------





