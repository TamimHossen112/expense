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
    Field('status', 'string', length=20, default='active', requires=IS_IN_SET(['active', 'inactive'])),
    signature,
    migrate=False
)

db.define_table('asset_master',
    Field('cid', 'string', length=20, default=cid),
    Field('asset_type', 'string',length=100),
    Field('asset_brand', 'string',length=100),
    Field('asset_model', 'string',length=100),
    Field('asset_color','string',length=100),
    Field('asset_desc','string', length=1000),
    Field('status', 'string', length=20, default='active', requires=IS_IN_SET(['active', 'inactive'])),
    signature,
    migrate=False
)

db.define_table('combo_settings',
    Field('cid', 'string', length=20, default=cid),
    Field('key', 'string',length=100),
    Field('value', 'string',length=1000),
    signature,
    migrate=False
)

# Requisition Table
db.define_table('requisition',
    Field('cid', 'string', length=20, default=cid),
    Field('req_id', 'string', length=100),
    Field('asset_type', 'string', length=100),
    Field('asset_brand', 'string', length=100),
    Field('asset_model', 'string', length=100),
    Field('org_name', 'string', length=100),
    Field('emp_id', 'string', length=100),
    Field('emp_category', 'string', length=100),
    Field('quantity', 'integer', length=11,default=0),
    Field('emp_name', 'string', length=100),
    Field('designation', 'string', length=100),
    Field('tr_code', 'string', length=100),
    Field('head_office', 'string', length=100),
    Field('req_desc','string',length=500),
    Field('joining_date', 'date'),
    Field('license_issue_date', 'date'),
    Field('license_expire_date', 'date'),
    Field('license_number', 'string', length=100),
    Field('fm_approval', 'string', default='no',requires=IS_IN_SET(['yes', 'no'])),
    Field('rsm_approval', 'string', default='no',requires=IS_IN_SET(['yes', 'no'])),
    Field('sm_approval', 'string', default='no',requires=IS_IN_SET(['yes', 'no'])),
    Field('agm_approval', 'string', default='no',requires=IS_IN_SET(['yes', 'no'])),
    Field('gm_approval', 'string', default='no',requires=IS_IN_SET(['yes', 'no'])),
    Field('hr_approval', 'string', default='no',requires=IS_IN_SET(['yes', 'no'])),
    Field('ed_approval', 'string', default='no',requires=IS_IN_SET(['yes', 'no'])),
    Field('req_status', 'string', default='pending', requires=IS_IN_SET(['pending', 'approved'])),
    signature,
    migrate=False
)

# Purchase Head Table
db.define_table('purchase_head',
    Field('cid', 'string', length=20, default=cid),
    Field('purchase_head_id', 'string', length=100),
    Field('req_id', 'integer', length=11,default=0),
    Field('vendor_id', 'integer',length=11,default=0),
    Field('vendor_name', 'string', length=255),
    Field('bill_no', 'string', length=100),
    Field('total_price', 'float'),
    Field('total_discount', 'float'),
    Field('total_payable', 'float'),
    Field('payment_type', 'string', length=100),
    Field('purchase_date', 'date'),
    Field('received_date', 'date'),
    Field('payment_status', 'string', length=100),
    Field('purchase_status', 'string', length=100),
    Field('remarks', 'string', length=500),
    signature,
    migrate=False
)


# Purchase Details Table
db.define_table('purchase_details',
    Field('cid', 'string', length=20, default=cid),
    Field('purchase_head_id', 'string', length=100),
    Field('purchase_details_id', 'string', length=100),
    Field('req_id', 'string', length=100),
    Field('asset_type', 'string', length=100),
    Field('asset_brand', 'string', length=255),
    Field('asset_model', 'string', length=500),
    Field('asset_color', 'string',length=100),
    Field('purchase_date', 'date'),
    Field('receive_status', 'string', length=100),
    Field('received_date', 'date'),
    Field('item_price', 'float'),
    Field('item_gross_total', 'float'),
    Field('item_discount', 'float'),
    Field('item_net_total', 'float'),
    Field('asset_created', 'integer', default=0),
    Field('quantity', 'integer', default=0),
    signature,
    migrate= False
)

# Asset Table
db.define_table('asset',
    Field('cid', 'string', length=20, default=cid),
    Field('asset_id', 'string', length=100),
    Field('purchase_head_id', 'string', length=100),
    Field('purchase_details_id', 'string', length=100),
    Field('req_id', 'string', length=100),
    Field('asset_type', 'string', length=100),
    Field('asset_model', 'string', length=255),
    Field('asset_brand', 'string', length=255),
    Field('asset_color','string',length=100),
    Field('asset_name', 'string', length=255),
    Field('asset_desc', 'string',length=500),
    Field('model_year', 'string', length=100),
    Field('reg_number', 'string', length=100),
    Field('engine_number', 'string', length=100),
    Field('engine_info', 'string', length=500),
    Field('chassis_number', 'string', length=100),
    Field('purchase_price', 'double'),
    Field('user_id', 'string', length=100),
    Field('user_name', 'string', length=200),
    Field('owner', 'string', length=200),
    Field('current_location', 'string', length=255),
    Field('asset_condition', 'string', length=100),
    Field('first_issue_date', 'date'),
    Field('registration_date','date'),
    Field('asset_status', 'string', length=100),
    signature,
    migrate=False
)


db.define_table('doc_metadata',
    Field('cid', 'string', length=20, default=cid),
    Field('asset_id', 'integer',length=11, default=0),
    Field('trans_type', 'string', length=100),
    Field('trans_id', 'integer', length=100),
    Field('doc_type','string',length=255),
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
    Field('section', 'string', length=100),
    Field('order', 'integer'),
    Field('key', 'string', length=255),
    Field('caption', 'string', length=255),
    Field('value', 'string', length=255),
    Field('value_type', 'string', length=100),
    Field('source_api', 'string', length=255),
    Field('dependent_fields', 'string', length=255),
    Field('dependent_on', 'string', length=255),
    Field('dependent_fields_source_api', 'string', length=255),
    Field('value_list', 'string', length=500),
    Field('default_value', 'string', length=255),
    Field('readonly', 'string', length=3, default='no', requires=IS_IN_SET(['yes', 'no'])),

    signature,
    migrate=False
)

# Transaction Head Table
db.define_table('tr_head',
    Field('cid', 'string', length=20, default=cid),
    Field('trans_type', 'string', length=100),
    Field('asset_id', 'string',length=100),
    Field('asset_type', 'string', length=100),
    Field('status', 'string', length=100),
    Field('tr_date', 'date'),
    signature,
    migrate=False
)

# Transaction Details Table
db.define_table('tr_details',
    Field('cid', 'string', length=20, default=cid),
    Field('tr_head_id', 'integer', length=11, default=0),
    Field('sl', 'integer'),
    Field('key', 'string', length=255),
    Field('caption', 'string', length=255),
    Field('value', 'string', length=255),
    signature,
    migrate=False
)







