import json
from py4web import action, request, URL
from py4web.core import redirect
from ..common import db, session, T, flash
from datetime import datetime
from ..common_fn import check_role

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

def get_date(key):
    """Parse date string from request.forms into a Python date object."""
    value = request.forms.get(key)
    if value and value.strip():
        value = value.strip()
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


# ------------------ ENDPOINTS ------------------

@action('asset/index')
@action.uses("asset/index.html", session, flash)
def asset_index():
    task_id='asset_view'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    return locals()

@action('asset/create')
@action.uses("asset/create.html", session, flash)
def asset_create():
    task_id='asset_create'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))

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
    task_id='asset_create'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    try:
        form = request.forms

        asset_name = (form.get("asset_name") or "").strip()
        asset_type = (form.get("asset_type") or "").strip()
        asset_brand = (form.get("asset_brand") or "").strip()
        asset_model = (form.get("asset_model") or "").strip()
        purchase_price_raw = (form.get("purchase_price") or "").strip()
        asset_model_year = (form.get("asset_model_year") or "").strip()
        asset_status = (form.get("asset_status") or "").strip()
        asset_condition = (form.get("asset_condition") or "").strip()
        reg_number = (form.get("registration_no") or "").strip()
        engine_number = (form.get("engine_no") or "").strip()
        engine_info = (form.get("engine_info") or "").strip()
        chassis_number = (form.get("chasis_no") or "").strip()
        current_location = (form.get("current_location") or "").strip()
        first_issue_date = get_date("first_issue_date")
        owner = (form.get("owner") or "SKF").strip()

        req_id = (form.get("req_id") or "").strip()
        purchase_head_id = (form.get("purchase_head_id") or "").strip()
        purchase_details_id = (form.get("purchase_details_id") or "").strip()

        # ---------- Basic Validation ----------
        errors = []
        if not asset_type: errors.append("Asset Type is required")
        if not asset_brand: errors.append("Asset Brand is required")
        if not asset_model: errors.append("Asset Model is required")
        if not purchase_price_raw: errors.append("Purchase Price is required")
        if errors:
            flash.set(" | ".join(errors), "warning", sanitize=True)
            redirect(URL("asset/create"))

        try:
            purchase_price = float(purchase_price_raw)
        except ValueError:
            flash.set("Purchase Price must be a number", "warning", sanitize=True)
            redirect(URL("asset/create"))

        # ---------- Check purchase_details availability ----------
        if purchase_details_id:
            pd_row = db(db.purchase_details.purchase_details_id == purchase_details_id).select().first()
            if not pd_row:
                flash.set(f"Purchase Details ID {purchase_details_id} not found.", "danger", sanitize=True)
                redirect(URL("asset/create"))

            pd_quantity = int(pd_row.quantity)
            existing_assets_count = db(db.asset.purchase_details_id == purchase_details_id).count()

            if existing_assets_count >= pd_quantity:
                flash.set(f"No remaining quantity to create asset for Purchase Details ID {purchase_details_id}.", "warning", sanitize=True)
                redirect(URL("asset/create"))
            elif existing_assets_count == pd_quantity - 1:
                db(db.purchase_details.purchase_details_id == purchase_details_id).update(asset_created=1)

        # ---------- Generate Asset Code ----------
        asset_code = generate_asset_code(asset_type)

        # ---------- Insert Asset ----------
        db.asset.insert(
            asset_type=asset_type,
            asset_brand=asset_brand,
            asset_model=asset_model,
            purchase_price=purchase_price,
            asset_name=asset_name,
            asset_id=asset_code,
            model_year=asset_model_year,
            asset_status=asset_status,
            asset_condition=asset_condition,
            reg_number=reg_number,
            engine_number=engine_number,
            engine_info=engine_info,
            chassis_number=chassis_number,
            current_location=current_location,
            first_issue_date=first_issue_date,
            owner=owner,
            req_id=req_id,
            purchase_head_id=purchase_head_id,
            purchase_details_id=purchase_details_id,
        )

        flash.set(f"Asset created successfully (Code: {asset_code})", "success", sanitize=True)
        redirect(URL("asset/index"))

    except Exception as e:
        flash.set(f"Error creating asset: {str(e)}", "warning", sanitize=True)
        redirect(URL("asset/index"))



@action('asset/edit')
@action.uses("asset/edit.html", db, session, flash)
def asset_edit():
    task_id='asset_edit'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))

    asset_id = request.query.get('id')
    if not asset_id:
        flash.set("Asset ID is required", sanitize=True)
        redirect(URL('asset/index'))   # or wherever your list page is
    
    try:
        asset_id = int(asset_id)
    except ValueError:
        flash.set("Invalid Asset ID", sanitize=True)
        redirect(URL('asset/index'))

    sql_asset = f"""
        SELECT asset_type, asset_brand, asset_model, purchase_price,
               asset_name, asset_desc, model_year, asset_status, asset_condition,
               owner, reg_number, engine_number, engine_info, chassis_number,
               first_issue_date, current_location, user_id, user_name
        FROM asset
        WHERE id = {asset_id}
    """
    rows = db.executesql(sql_asset, as_dict=True)

    if not rows:
        flash.set("Asset not found", "warning", sanitize=True)
        redirect(URL('asset/index'))

    main_row = rows[0]
    selected_emp = f"{main_row['user_id']} | {main_row['user_name']}" if main_row['user_id'] else ""

    asset_type_list = [r['asset_type'] for r in db.executesql("SELECT DISTINCT asset_type FROM asset_master WHERE asset_type IS NOT NULL", as_dict=True)]
    asset_brand_list = [r['asset_brand'] for r in db.executesql("SELECT DISTINCT asset_brand FROM asset_master WHERE asset_brand IS NOT NULL", as_dict=True)]
    asset_model_list = [r['asset_model'] for r in db.executesql("SELECT DISTINCT asset_model FROM asset_master WHERE asset_model IS NOT NULL", as_dict=True)]

    return dict(
        selected_asset_type = main_row['asset_type'] or "",
        selected_asset_brand = main_row['asset_brand'] or "",
        selected_asset_model = main_row['asset_model'] or "",
        selected_emp = selected_emp,
        selected_asset_status = main_row['asset_status'] or "",
        selected_asset_condition = main_row['asset_condition'] or "",
        record = main_row,
        asset_type_list = asset_type_list,
        asset_brand_list = asset_brand_list,
        asset_model_list = asset_model_list,
        asset_status_list = get_combo_values("asset_status"),
        asset_condition_list = get_combo_values("asset_condition"),
        owner_list = get_combo_values("organizations"),
        selected_owner = main_row['owner'] or ""
    )


@action('asset/update', method=['POST'])
@action.uses(db, session, flash)
def asset_update():
    task_id='asset_edit'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))

    asset_id_code = request.forms.get('id')
    if not asset_id_code:
        return dict(error='Missing asset ID.')
    
    asset_record = db(db.asset.id == asset_id_code).select().first()
    if not asset_record:
        return dict(error='Asset not found.')

    def get_text(key):
        return (request.forms.get(key) or "").strip()

    def get_number(key):
        value = request.forms.get(key)
        if not value:
            return None
        value = value.strip()
        if value.lower() in ("none", "null", ""):
            return None
        try:
            return float(value)
        except ValueError:
            return None

    # Extract employee ID and name
    emp_id, user_name = parse_employee(get_text('emp_id'))

    # Validation
    errors = []
    if not get_text('asset_type'):
        errors.append("Asset Type is required.")
    if not get_text('asset_brand'):
        errors.append("Asset Brand is required.")
    if not get_text('asset_model'):
        errors.append("Asset Model is required.")
    if not get_text('purchase_price'):
        errors.append("Purchase Price is required.")    

    if errors:
        flash.set(' | '.join(errors), "warning")
        redirect(URL('asset/edit', vars=dict(id=asset_id_code)))

    # 🔹 Update Asset
    db(db.asset.id == asset_id_code).update(
        asset_type=get_text('asset_type'),
        asset_brand=get_text('asset_brand'),
        asset_model=get_text('asset_model'),
        asset_name=get_text('asset_name'),
        asset_desc=get_text('asset_desc'),
        model_year=get_text('asset_model_year'),
        reg_number=get_text('registration_no'),
        engine_number=get_text('engine_no'),
        engine_info=get_text('engine_info'),
        chassis_number=get_text('chasis_no'),
        purchase_price=get_number('purchase_price'),
        user_id=emp_id,
        user_name=user_name,
        current_location=get_text('current_location'),
        asset_condition=get_text('asset_condition'),
        first_issue_date=get_date('first_issue_date'),
        asset_status=get_text('asset_status'),
        owner=get_text('owner')
    )
    db.commit()

    flash.set("Asset updated successfully!", "success")
    redirect(URL('asset/index'))


@action('asset/get_data', method=['GET'])
@action.uses(db,session,flash)
def asset_get_data():
    task_id='asset_view'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
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
            pd.quantity
        FROM purchase_details pd
        WHERE pd.purchase_head_id = %s
          AND LOWER(pd.receive_status) LIKE '%%received%%'
          AND pd.asset_created = 0
    """
    purchase_rows = db.executesql(sql, [purchase_head_id], as_dict=True)

    if not purchase_rows:
        return dict(results=[])

    # Step 2: Get counts of assets already created per purchase_details_id
    purchase_detail_ids = [row['purchase_details_id'] for row in purchase_rows]
    placeholders = ",".join(["%s"] * len(purchase_detail_ids))
    asset_counts = db.executesql(
        f"""
        SELECT purchase_details_id, COUNT(*) AS created_count
        FROM asset
        WHERE purchase_details_id IN ({placeholders})
        GROUP BY purchase_details_id
        """,
        purchase_detail_ids,
        as_dict=True
    )
    asset_count_map = {row['purchase_details_id']: int(row['created_count']) for row in asset_counts}

    # Step 3: Build results, only include rows with available_to_create > 0
    results = []
    for row in purchase_rows:
        created_count = asset_count_map.get(row['purchase_details_id'], 0)
        available_to_create = row['quantity'] - created_count
        if available_to_create > 0:
            results.append({
                'purchase_details_id': row['purchase_details_id'],
                'req_id': row['req_id'],
                'purchase_head_id': row['purchase_head_id'],
                'asset_type': row['asset_type'],
                'asset_brand': row['asset_brand'],
                'asset_model': row['asset_model'],
                'item_price': row['item_price'],
                'available_to_create': available_to_create
            })

    return dict(results=results)



# 1. Get brands by asset type
@action('asset/get_brands_by_type')
@action.uses(db)
def get_brands_by_type():
    task_id='asset_edit'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    asset_type = request.query.get('asset_type')
    if not asset_type:
        return {"results": []}

    rows = db(db.asset_master.asset_type == asset_type).select(
        db.asset_master.asset_brand, distinct=True
    )
    brands = [row.asset_brand for row in rows if row.asset_brand]
    return {"results": brands}


# 2. Get models by brand + type
@action('asset/get_models_by_brand')
@action.uses(db)
def get_models_by_brand():
    task_id='asset_edit'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
        
    asset_type = request.query.get('asset_type')
    asset_brand = request.query.get('asset_brand')
    if not asset_type or not asset_brand:
        return {"results": []}

    rows = db(
        (db.asset_master.asset_type == asset_type) &
        (db.asset_master.asset_brand == asset_brand)
    ).select(db.asset_master.asset_model, distinct=True)

    models = [row.asset_model for row in rows if row.asset_model]
    return {"results": models}


