import json
from py4web import action, request, URL
from py4web.core import redirect
from ..common import db, session, T, flash
from datetime import datetime

# ------------------ UTILS ------------------
def generate_asset_code(asset_type):
    prefix = 'A'
    code_char = asset_type.strip()[0].upper() if asset_type else 'X'
    last_row = db(db.asset.asset_id != None).select(
        db.asset.asset_id, orderby=~db.asset.id, limitby=(0, 1)
    ).first()
    if not last_row or not last_row.asset_id:
        return f"{prefix}{code_char}10000"

    last_id = last_row.asset_id.strip()
    number_part = ''.join(reversed([c for c in reversed(last_id) if c.isdigit()]))
    return f"{prefix}{code_char}{int(number_part)+1 if number_part else 10000}"

def get_combo_values(key, as_dict=False):
    row = db(db.combo_settings.key == key).select(db.combo_settings.value).first()
    if not row or not row.value:
        return []    
    values = [v.strip() for v in row.value.split(',') if v.strip()]
    if as_dict:
        return [{"value": v} for v in values]
    return values

def parse_employee(emp_val):
    parts = [x.strip() for x in (emp_val or '').split('|')]
    return (parts[0] if len(parts) > 0 else None, parts[1] if len(parts) > 1 else None)

def get_distinct_master_fields(fields):
    rows = db().select(*fields, distinct=True)
    results = {f.name: sorted({getattr(row, f.name) for row in rows if getattr(row, f.name)}) for f in fields}
    return results

# ------------------ ROUTES ------------------
@action('asset/index')
@action.uses("asset/index.html", session, flash)
def asset_index():
    return locals()

@action('asset/create')
@action.uses("asset/create.html", session, flash)
def asset_create():
    distinct_fields = get_distinct_master_fields([
        db.asset_master.asset_type, 
        db.asset_master.asset_brand, 
        db.asset_master.asset_model
    ])
    
    return dict(
        asset_type_list=distinct_fields.get('asset_type', []),
        asset_brand_list=distinct_fields.get('asset_brand', []),
        asset_model_list=distinct_fields.get('asset_model', []),
        asset_status_list=get_combo_values("asset_status"),
        asset_condition_list=get_combo_values("asset_condition"),
        owner_list=get_combo_values("organizations")
    )

@action('asset/submit', method=["POST"])
@action.uses(db, session, flash)
def asset_submit():
    try:
        form = request.forms

        # Collect form values
        asset_name = form.get("asset_name")
        asset_type = form.get("asset_type")
        asset_brand = form.get("asset_brand")
        asset_model = form.get("asset_model")
        purchase_price = form.get("purchase_price")
        asset_model_year = form.get("asset_model_year")
        asset_status = form.get("asset_status")
        asset_condition = form.get("asset_condition")
        registration_no = form.get("registration_no")
        engine_no = form.get("engine_no")
        engine_info = form.get("engine_info")
        chasis_no = form.get("chasis_no")
        current_location = form.get("current_location")
        first_issue_date = form.get("first_issue_date")
        owner = "SKF"

        # Hidden fields if imported from purchase
        req_id = form.get("req_id")
        purchase_head_id = form.get("purchase_head_id")
        purchase_details_id = form.get("purchase_details_id")

        # ✅ Required fields check
        required_fields = {
            "asset_type": asset_type,
            "asset_brand": asset_brand,
            "asset_model": asset_model,
            "purchase_price": purchase_price,
        }
        missing = [label for label, value in required_fields.items() if not value]

        if missing:
            flash.set(f"Missing required fields: {', '.join(missing)}", "warning", sanitize=True)
            redirect(URL("asset/index"))

        # ✅ Generate asset code automatically
        asset_code = generate_asset_code(asset_type)

        # ✅ Insert into DB
        asset_id = db.asset.insert(
            asset_type=asset_type,
            asset_brand=asset_brand,
            asset_model=asset_model,
            purchase_price=purchase_price,
            asset_name=asset_name,
            asset_id=asset_code,  # using generated asset code
            asset_model_year=asset_model_year,
            asset_status=asset_status,
            asset_condition=asset_condition,
            registration_no=registration_no,
            engine_no=engine_no,
            engine_info=engine_info,
            chasis_no=chasis_no,
            current_location=current_location,
            first_issue_date=first_issue_date,
            owner=owner,
            req_id=req_id,
            purchase_head_id=purchase_head_id,
            purchase_details_id=purchase_details_id,
        )

        flash.set(f"✅ Asset created successfully (Code: {asset_code})", "success", sanitize=True)
        redirect(URL("asset/index"))

    except Exception as e:
        flash.set(f"❌ Error creating asset: {str(e)}", "danger", sanitize=True)
        redirect(URL("asset/index"))


@action('asset/get_brands_by_type')
@action.uses(db)
def get_brands_by_type():
    asset_type = request.params.get('asset_type', '')
    if not asset_type: 
        return dict(results=[])
    brands = db(db.asset_master.asset_type == asset_type).select(db.asset_master.asset_brand, distinct=True)
    return dict(results=[row.asset_brand for row in brands])

@action('asset/get_models_by_brand')
@action.uses(db)
def get_models_by_type_brand():
    asset_type = request.params.get('asset_type', '')
    asset_brand = request.params.get('asset_brand', '')
    if not asset_type or not asset_brand: 
        return dict(results=[])
    models = db((db.asset_master.asset_type==asset_type)&(db.asset_master.asset_brand==asset_brand))\
               .select(db.asset_master.asset_model, distinct=True)
    return dict(results=[row.asset_model for row in models])

@action('asset/edit')
@action.uses("asset/edit.html", db, session, flash)
def asset_edit():
    asset_id = request.query.get('id')
    if not asset_id: 
        return dict(error="Asset ID is required")
    
    main_row = db(db.asset.id == asset_id).select().first()
    if not main_row: 
        return dict(error="Asset not found")

    selected_emp = f"{main_row.user_id} | {main_row.user_name}" if main_row.user_id else ""
    
    distinct_fields = get_distinct_master_fields([
        db.asset_master.asset_type,
        db.asset_master.asset_brand,
        db.asset_master.asset_model
    ])

    return dict(
        selected_asset_type = main_row.asset_type or "",
        selected_asset_brand = main_row.asset_brand or "",
        selected_asset_model = main_row.asset_model or "",
        selected_emp = selected_emp,
        selected_asset_status = main_row.asset_status or "",
        selected_asset_condition = main_row.asset_condition or "",
        record = main_row,
        asset_type_list = distinct_fields.get('asset_type', []),
        asset_brand_list = distinct_fields.get('asset_brand', []),
        asset_model_list = distinct_fields.get('asset_model', []),
        asset_status_list = get_combo_values("asset_status",),
        asset_condition_list = get_combo_values("asset_condition"),
        owner_list = get_combo_values("organizations"),
        selected_owner = main_row.owner or ""
    )


@action('asset/update', method=['POST'])
@action.uses(db, session, flash)
def asset_update():
    asset_id_code = request.forms.get('id')
    if not asset_id_code:
        return dict(error='Missing asset ID.')
    
    asset_record = db(db.asset.id == asset_id_code).select().first()
    if not asset_record:
        return dict(error='Asset not found.')

    # Helpers
    def get_text(key):
        return (request.forms.get(key) or "").strip()
    def get_number(key):
        value = request.forms.get(key)
        return float(value) if value and value.strip() else None
    def get_date(key):
        value = request.forms.get(key)
        if value and value.strip():
            try:
                return datetime.datetime.strptime(value.strip(), "%Y-%m-%d").date()
            except Exception:
                return None   # fallback if invalid date format
        return None

    # Parse employee info
    emp_id, user_name = parse_employee(get_text('emp_id'))

    # Validation
    errors = []
    if not get_text('asset_type'):
        errors.append("Asset Type is required.")
    if errors:
        flash.set(' | '.join(errors), "warning")
        redirect(URL('asset/edit', vars=dict(id=asset_id_code)))

    # ✅ Update asset record (including new field `owner`)
    db(db.asset.id == asset_id_code).update(
        asset_type=get_text('asset_type'),
        asset_brand=get_text('asset_brand'),
        asset_model=get_text('asset_model'),
        asset_name=get_text('asset_name'),
        asset_desc=get_text('asset_desc'),
        asset_model_year=get_text('asset_model_year'),
        registration_no=get_text('registration_no'),
        engine_no=get_text('engine_no'),
        engine_info=get_text('engine_info'),
        chasis_no=get_text('chasis_no'),
        purchase_price=get_number('purchase_price'),
        user_id=emp_id,
        user_name=user_name,
        current_location=get_text('current_location'),
        asset_condition=get_text('asset_condition'),
        first_issue_date=get_text('first_issue_date'), 
        asset_status=get_text('asset_status'),
        owner=get_text('owner')
    )
    db.commit()

    flash.set("Asset updated successfully!", "success")
    redirect(URL('asset/index'))


@action('asset/get_data', method=['GET'])
@action.uses(db)
def asset_get_data():
    params = request.query
    asset_name = params.get('asset_name', '').strip()
    asset_type = params.get('asset_type', '').strip()
    asset_status = params.get('asset_status', '').strip()
    user_name = params.get('user_name', '').strip()

    filters = []
    placeholders = {}
    if asset_name: 
        filters.append("asset_name = :asset_name")
        placeholders["asset_name"] = asset_name
    if asset_type: 
        filters.append("asset_type = :asset_type")
        placeholders["asset_type"] = asset_type
    if asset_status: 
        filters.append("asset_status = :asset_status")
        placeholders["asset_status"] = asset_status
    if user_name: 
        filters.append("user_name = :user_name")
        placeholders["user_name"] = user_name

    where_sql = " AND ".join(filters) if filters else "1=1"

    start = int(params.get('start') or 0)
    length = int(params.get('length') or 15)

    sort_col_index = params.get('order[0][column]')
    if sort_col_index is None:
        sort_col_name, sort_dir = 'id', 'desc'
    else:
        sort_col_index = int(sort_col_index)
        sort_col_name = params.get(f'columns[{sort_col_index}][data]') or 'id'
        sort_dir = params.get('order[0][dir]', 'desc').lower()
        if sort_dir not in ['asc','desc']: sort_dir = 'desc'

    total_sql = f"SELECT COUNT(*) AS total FROM asset WHERE {where_sql}"
    total_rows = db.executesql(total_sql, placeholders=placeholders, as_dict=True)[0]['total']

    base_sql = f"""
        SELECT id, asset_id, asset_type, asset_brand, asset_model,
               user_id, user_name, purchase_price, current_location,
               asset_condition, first_issue_date, asset_status
        FROM asset
        WHERE {where_sql}
        ORDER BY {sort_col_name} {sort_dir}
    """
    if length != -1:
        base_sql += f" LIMIT {length} OFFSET {start}"

    data = db.executesql(base_sql, placeholders=placeholders, as_dict=True)

    return dict(
        data=data,
        recordsTotal=total_rows,
        recordsFiltered=total_rows,
        draw=int(params.get('draw') or 1)
    )

@action('asset/get_purchase_map')
@action.uses(db)
def get_purchase_map():
    sql = """
        SELECT 
            ph.id, 
            ph.purchase_head_id, 
            ph.vendor_id, 
            ph.vendor_name, 
            ph.bill_no 
        FROM purchase_head ph
        WHERE EXISTS (
            SELECT 1 
            FROM purchase_details pd
            WHERE pd.purchase_head_id = ph.purchase_head_id
              AND pd.receive_status = 'received'
              AND pd.asset_created = 0
        )
    """
    rows = db.executesql(sql, as_dict=True)
    return dict(results=rows)

@action('asset/get_purchase_details_map')
@action.uses(db)
def get_purchase_details_map():
    purchase_head_id = str(request.params.get('purchase_head_id'))
    sql = """
        SELECT 
            pd.purchase_details_id, 
            pd.req_id, 
            pd.purchase_head_id, 
            pd.asset_type, 
            pd.asset_brand, 
            pd.asset_model, 
            pd.item_price, 
            r.emp_id, 
            r.emp_name
        FROM purchase_details pd
        LEFT JOIN requisition r ON pd.req_id = r.req_id
        WHERE pd.purchase_head_id = :phid
          AND LOWER(pd.receive_status) LIKE '%received%'
          AND pd.asset_created = 0
    """
    rows = db.executesql(sql, placeholders={"phid": purchase_head_id}, as_dict=True)
    return dict(results=rows)
