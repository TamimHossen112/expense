import json
import requests
from py4web import action, request, redirect, URL
from ..common import db, session, T, flash
from ..common_fn import check_role
from datetime import date  

@action('transaction/index')
@action.uses("transaction/index.html",db, session, flash)
def transaction_index():
    task_id='transaction_view'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    tr_type = request.query.get('type')
    return locals()


def fetch_from_api(endpoint, params=None):
    """Generic API fetcher for dropdown source_api."""
    base_url = "http://localhost:8010/expense/default/"
    url = f"{base_url}{endpoint}"
    try:
        resp = requests.get(url, params=params or {}, timeout=5)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"API {url} returned {resp.status_code}")
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
    return []

@action("transaction/create")
@action.uses("transaction/create.html", db, session, flash)
def transaction_create():
    task_id='transaction_create'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    tr_type = request.query.get("type", "").strip()

    if not tr_type:
        return dict(fields=[], fields_json="[]")

    rows = db.executesql(
        f"""
        SELECT sl, section, `order`, `key`, caption, value_type, 
               value_list, source_api, default_value, readonly, 
               hidden, dependent_fields, dependent_fields_source_api, 
               dependent_on
        FROM tr_config
        WHERE tr_type = '{tr_type}'
        ORDER BY sl, `order`
        """,
        as_dict=True
    )

    fields = []
    for row in rows:
        value_list = None
        if row["value_list"]:
            values = [v.strip() for v in row["value_list"].split(",") if v.strip()]
            if row.get("dependent_fields"):
                value_list = {v: {} for v in values}
            else:
                value_list = values

        fields.append({
            "sl": row["sl"] or "",
            "section": row["section"] or "",
            "order": row["order"] or "",
            "key": row["key"] or "",
            "caption": row["caption"] or "",
            "value_type": row["value_type"] or "",
            "value_list": value_list or "",
            "default_value": row["default_value"] or "",
            "source_api": row["source_api"] or "",
            "dependent_fields_source_api": row["dependent_fields_source_api"] or "",
            "readonly": row["readonly"] or "",
            "hidden": row["hidden"] or "",
            "dependent_fields": row["dependent_fields"] or "",
            "dependent_on": row.get("dependent_on") or "",
        })

    return dict(
        fields=fields,
        fields_json=json.dumps(fields, default=str)
    )


@action("transaction/submit", method=["POST"])
@action.uses(db, session, flash)
def transaction_submit():
    task_id='transaction_create'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    cid = "SKF"
    form = request.forms

    trans_type = request.query.get("type")
    asset_id, asset_type, status = form.get("asset_id"), form.get("asset_type"), form.get("approve_status")
    if not asset_id or not asset_type:
        flash.set("Missing asset_id or asset_type")
        redirect(URL("transaction/index"))

    db.executesql(
        f"""
        INSERT INTO tr_head (cid, trans_type, asset_id, asset_type, status, tr_date)
        VALUES ('{cid}', '{trans_type}', '{asset_id}', '{asset_type}', '{status}', '{date.today()}')
        """
    )
    head_id = db.executesql("SELECT LAST_INSERT_ID() AS id", as_dict=True)[0]['id']

    details_list = []
    approval_flag = False
    employee_id = ""
    employee_name = ""
    using_from=None

    for key in form.keys():
        value = form.get(key)

        if str(trans_type).lower() in ("allocation", "transfer"):
            if str(key).lower() in ("allocation_status", "approve_status") and str(value).lower() == "approved":
                approval_flag = True
            if str(key).lower() == "emp_id" or str(key).lower() == "to_emp_id":
                employee_id = value
            if str(key).lower() == "to_name":
                employee_name = value
            if str(key).lower() == "applied_date":
                using_from=value

        details_list.append({
            "cid": cid,
            "tr_head_id": head_id,
            "key": key,
            "value": value
        })

    tr_head_fields = {
        "cid": cid,
        "trans_type": trans_type,
        "asset_id": asset_id,
        "asset_type": asset_type,
        "status": "pending",
        "tr_date": str(date.today())
    }
    for key, value in tr_head_fields.items():
        details_list.append({
            "cid": cid,
            "tr_head_id": head_id,
            "key": key,
            "value": value
        })

    db.tr_details.bulk_insert(details_list)

    if approval_flag and employee_id and employee_name and asset_id and using_from:
        db.executesql(
            f"""
            UPDATE asset
            SET user_id = {employee_id},
                user_name = '{employee_name}',
                using_from='{using_from}'
            WHERE asset_id = '{asset_id}'
            """
        )

    flash.set("Transfer submitted successfully!", "success")
    redirect(URL("transaction/index", vars=dict(type=trans_type)))


@action('transaction/view', method=['GET'])
@action.uses("transaction/view.html", db, session, flash)
def transaction_view():
    task_id='transaction_view'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
        
    tr_head_id = request.query.get('id')
    if not tr_head_id:
        return dict(status="error", message="Missing transaction id", details=[], fields_json="[]")

    try:
        tr_head_id = int(tr_head_id)
    except ValueError:
        return dict(status="error", message="Invalid transaction id", details=[], fields_json="[]")

    head_rows = db.executesql(f"SELECT * FROM tr_head WHERE id = {tr_head_id}", as_dict=True)
    if not head_rows:
        return dict(status="error", message="Transaction not found", details=[], fields_json="[]")
    
    head_row = head_rows[0]

    configs = db.executesql(f"""
        SELECT * FROM tr_config 
        WHERE tr_type = '{head_row['trans_type']}' 
        ORDER BY sl, `order`
    """, as_dict=True)

    details = db.executesql(f"SELECT * FROM tr_details WHERE tr_head_id = {tr_head_id}", as_dict=True)
    details_map = {d['key']: d['value'] for d in details}


    merged = []
    for cfg in configs:
        if cfg.get("hidden") in ("yes", "true", True):
            continue
        
        if cfg['key'] not in details_map:
            continue

        value = details_map.get(cfg['key'], cfg.get('value') or cfg.get('default_value') or "")
        merged.append({
            "key": cfg['key'],
            "caption": cfg['caption'],
            "section": cfg.get('section', ''),
            "value": str(value),
            "readonly": "yes",
            "value_type": "string",
            "sl": cfg.get('sl', 0),   
            "order": cfg.get('order', 0)
        })
        

    return dict(
        status="success",
        head=head_row,
        details=merged,
        fields_json=json.dumps(merged, default=str)
    )


# # # ------------------------------
# # # Edit Page
# # # ------------------------------


@action("transaction/edit")
@action.uses("transaction/edit.html", db, session, flash)  
def transaction_edit():
    task_id = 'transaction_edit'
    access_permission = check_role(task_id)  
    if access_permission==False:
        flash.set("Access is Denied !", 'warning')
        redirect(URL('dashboard', 'index'))

    tr_id = request.query.get("id", "").strip()
    tr_type_param = request.query.get("type", "").strip()

    if not tr_id:
        flash.set("Missing transaction ID.", "warning")
        redirect(URL("transaction", "index", vars=dict(type=tr_type_param)))

    # Get the transaction header
    tr_head = db(db.tr_head.id == tr_id).select().first()
    if not tr_head:
        flash.set("Transaction not found.", "warning")
        redirect(URL("transaction", "index", vars=dict(type=tr_type_param)))

    tr_type = tr_head.trans_type

    # Fetch transaction configuration
    rows = db(db.tr_config.tr_type == tr_type).select(orderby=[db.tr_config.sl, db.tr_config.order])

    # Fetch transaction details
    details_rows = db(db.tr_details.tr_head_id == tr_id).select()
    details_map = {d.key: d.value for d in details_rows}  # key -> value

    fields = []
    for row in rows:
        # Prepare value_list
        value_list = None
        if row.value_list:
            values = [v.strip() for v in row.value_list.split(",") if v.strip()]
            if row.dependent_fields:
                value_list = {v: {"value": "", "dependent_values": {}} for v in values}
            else:
                value_list = values

        # Determine current value
        current_value = getattr(tr_head, row.key, None) or details_map.get(row.key) or row.default_value or ""

        fields.append({
            "sl": row.sl or "",
            "section": row.section or "",
            "order": row.order or "",
            "key": row.key or "",
            "caption": row.caption or "",
            "value_type": row.value_type or "",
            "value_list": value_list or "",
            "value": current_value,
            "source_api": row.source_api or "",
            "dependent_fields_source_api": row.dependent_fields_source_api or "",
            "readonly": row.readonly or "no",
            "hidden": "",
            "dependent_fields": row.dependent_fields or "",
            "dependent_on": row.dependent_on or "",
        })

    return dict(
        fields=fields,
        fields_json=json.dumps(fields, default=str)
    )


@action("transaction/update", method=["POST"])
@action.uses(db, session, flash)
def transaction_update():
    task_id='transaction_edit'
    access_permission=check_role(task_id)  
    if (access_permission==False):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
        
    cid = "SKF"
    form = request.forms
    tr_head_id = request.query.get("id")
    trans_type = request.query.get("type")

    if not tr_head_id:
        flash.set("Missing transaction ID", "danger")
        redirect(URL("transaction/index", vars=dict(type=trans_type)))

    asset_id = form.get("asset_id")
    asset_type = form.get("asset_type")
    status = form.get("approve_status")
    if not asset_id or not asset_type:
        flash.set("Missing asset_id or asset_type", "danger")
        redirect(URL("transaction/index", vars=dict(type=trans_type)))

    # Delete existing tr_details for this transaction
    tr_head_record = db(db.tr_head.id == tr_head_id).select().first()
    db(db.tr_details.tr_head_id == tr_head_id).delete()


    details_list = []
    approval_flag = False
    employee_id = ""
    employee_name = ""
    using_from=None

    # Collect new details from form
    for key in form.keys():
        value = form.get(key)

        if str(trans_type).lower() in ("allocation", "transfer"):
            if str(key).lower() in ("allocation_status", "approve_status") and str(value).lower() == "approved":
                approval_flag = True
            if str(key).lower() == "emp_id" or str(key).lower() == "to_emp_id":
                employee_id = value
            if str(key).lower() == "to_name":
                employee_name = value
            if str(key).lower() == "applied_date":
                using_from=value

        details_list.append({
            "cid": cid,
            "tr_head_id": tr_head_id,
            "key": key,
            "value": value
        })

    # store main tr_head fields in details
    tr_head_fields = {
        "cid": cid,
        "trans_type": trans_type,
        "asset_id": asset_id,
        "asset_type": asset_type,
        "status": status,
        "tr_date": str(date.today())
    }
    for key, value in tr_head_fields.items():
        details_list.append({
            "cid": cid,
            "tr_head_id": tr_head_id,
            "key": key,
            "value": value
        })

    # Bulk insert new details
    db.tr_details.bulk_insert(details_list)
    tr_head_record.update_record(
        status=status
    )

    # Update asset assignment if approved
    if approval_flag and employee_id and employee_name and asset_id and using_from:
        db.executesql(
            f"""
            UPDATE asset
            SET user_id = {employee_id},
                user_name = '{employee_name}',
                using_from = '{using_from}'
            WHERE asset_id = '{asset_id}'
            """
        )

    flash.set("Transaction updated successfully!", "success")
    redirect(URL("transaction/index", vars=dict(type=trans_type)))



# ------------------------------
# Get Distinct Transactions for Datatable
# ------------------------------

@action('transaction/get_data', method=['GET'])
@action.uses(db, session, flash)
def transaction_get_data():
    task_id = 'transaction_view'
    access_permission = check_role(task_id)
    if access_permission is False:
        flash.set("Access is Denied !", 'warning')
        redirect(URL('dashboard', 'index'))

    # Collect filters from query
    filters = {
        'trans_type': request.query.get('type', '').strip(),
        'asset_type': request.query.get('asset_type', '').strip(),
        'asset_id': request.query.get('asset_id', '').strip()
    }

    # Build WHERE conditions safely
    where_clauses = ["1=1"]
    params = []
    for k, v in filters.items():
        if v:
            where_clauses.append(f"{k} = %s")
            params.append(v)

    where_sql = " AND ".join(where_clauses)

    # Pagination
    start = int(request.query.get('start') or 0)
    length = int(request.query.get('length') or 15)

    # Sorting
    sort_col_index = request.query.get('order[0][column]')
    if sort_col_index is None:
        sort_col_name, sort_dir = 'tr_date', 'desc'
    else:
        sort_col_index = int(sort_col_index)
        sort_col_name = request.query.get(f'columns[{sort_col_index}][data]') or 'tr_date'
        sort_dir = request.query.get('order[0][dir]', 'desc').lower()
        sort_dir = sort_dir if sort_dir in ['asc', 'desc'] else 'desc'

    # Count total
    total_sql = f"SELECT COUNT(*) AS total FROM tr_head WHERE {where_sql}"
    total_rows = db.executesql(total_sql, params, as_dict=True)[0]['total']

    # Main data query
    base_sql = f"""
        SELECT id, asset_id, asset_type, trans_type, status, tr_date
        FROM tr_head
        WHERE {where_sql}
        ORDER BY {sort_col_name} {sort_dir}
        {"LIMIT %s OFFSET %s" if length != -1 else ""}
    """

    # Add pagination params if needed
    if length != -1:
        params += [length, start]

    data = db.executesql(base_sql, params, as_dict=True)

    return dict(
        data=data,
        recordsTotal=total_rows,
        recordsFiltered=total_rows,
        draw=int(request.query.get('draw') or 1)
    )

