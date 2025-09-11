import json
import datetime
from py4web import action, request, redirect, URL, response
from ..common import db, session, T, flash, auth
from ..common_fn import check_role
import requests

# -----------------------------
# Utility Functions
# -----------------------------
def generate_requisition_code(asset_type):
    prefix = 'R'
    asset_code = asset_type.strip()[0].upper() if asset_type else 'X'

    last_row = db(db.requisition.req_id != None).select(
        db.requisition.req_id,
        orderby=~db.requisition.id,
        limitby=(0, 1)
    ).first()

    if not last_row or not last_row.req_id:
        return f"{prefix}{asset_code}10000"

    last_req_id = last_row.req_id.strip()
    num_str = ''.join(filter(str.isdigit, reversed(last_req_id)))[::-1]
    new_number = int(num_str) + 1 if num_str else 10000

    return f"{prefix}{asset_code}{new_number}"


def get_combo_values(key):
    row = db(db.combo_settings.key == key).select(db.combo_settings.value).first()
    if row and row.value:
        return [v.strip() for v in row.value.split(",") if v.strip()]
    return []


def get_asset_types():
    rows = db(db.asset_master.asset_type != None).select(
        db.asset_master.asset_type,
        distinct=True
    )
    return [{"id": r.asset_type, "text": r.asset_type} for r in rows if r.asset_type]


# -----------------------------
# Views
# -----------------------------
@action('requisition_org/index')
@action.uses("requisition_org/index.html", session, flash)
def requisition_org_index():
    task_id='requisition_org_view'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    return locals()


@action('requisition_org/create')
@action.uses('requisition_org/create.html', db, session, flash)
def requisition_org_create():
    task_id='requisition_org_create'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    return dict(
        requisition_status_combos=get_combo_values("requisition_status"),
        asset_types=get_asset_types(),
        organizations=get_combo_values("organizations"),
    )


# -----------------------------
# Submit Endpoint
# -----------------------------
@action('requisition_org/submit', method=['POST'])
@action.uses(db, session, flash)
def requisition_org_submit():
    task_id='requisition_org_create'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    form = request.forms

    org_name = form.get('org_name')
    asset_type = form.get('asset_type')
    quantity = form.get('quantity')
    requisition_status = form.get('requisition_status')

    if not org_name or not asset_type or not requisition_status or not quantity:
        return dict(status="error", message="All required fields must be filled.")

    try:
        req_id = generate_requisition_code(asset_type)

        db.requisition.insert(
            req_id=req_id,
            org_name=org_name.strip(),
            asset_type=asset_type.strip(),
            quantity=int(quantity),
            req_status=requisition_status.strip()
        )
        db.commit()

        flash.set(f"Requisition {req_id} created successfully.", "success")
        redirect(URL('requisition_org', 'index'))
    except Exception as e:
        flash.set(f"Error creating requisition: {str(e)}", "error")
        redirect(URL('requisition_org', 'create'))


# -----------------------------
# Data Endpoint (For DataTable)
# -----------------------------
@action('requisition_org/get_data', method=['GET'])
@action.uses(db,session,flash)
def requisition_org_get_data():
    task_id='requisition_org_view'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    q = request.query
    start, length = int(q.get('start', 0)), int(q.get('length', 15))
    sort_col_index = q.get('order[0][column]')
    sort_dir = q.get('order[0][dir]', 'desc').lower()
    sort_dir = sort_dir if sort_dir in ['asc', 'desc'] else 'desc'
    sort_col = 'id'

    if sort_col_index is not None:
        sort_col_index = int(sort_col_index)
        sort_col = q.get(f'columns[{sort_col_index}][data]', 'id')

    # --- Filters ---
    filters = []
    if q.get('req_status'):
        filters.append(f"req_status='{q['req_status'].strip()}'")
    if q.get('asset_type'):
        filters.append(f"asset_type='{q['asset_type'].strip()}'")
    if q.get('org_name'):
        filters.append(f"org_name LIKE '%{q['org_name'].strip()}%'")

    where_sql = " AND ".join(filters) or "1=1"

    # --- Count total rows ---
    total_rows = db.executesql(
        f"SELECT COUNT(*) AS total FROM requisition WHERE {where_sql}",
        as_dict=True
    )[0]['total']

    base_sql = f"""
        SELECT id, req_id, req_status, org_name, asset_type, quantity
        FROM requisition
        WHERE {where_sql} AND org_name IS NOT NULL
        ORDER BY {sort_col} {sort_dir}
    """
    if length != -1:
        base_sql += f" LIMIT {length} OFFSET {start}"

    data = db.executesql(base_sql, as_dict=True)

    return dict(
        data=data,
        recordsTotal=total_rows,
        recordsFiltered=total_rows,
        draw=int(q.get('draw', 1))
    )


# -----------------------------
# Edit Endpoint (GET)
# -----------------------------
@action('requisition_org/edit', method=['GET'])
@action.uses("requisition_org/edit.html", db, session, flash)
def requisition_org_edit():
    task_id = 'requisition_org_edit'
    access_permission = check_role(task_id)  
    if not access_permission:
        flash.set("Access is Denied !", 'warning')
        redirect(URL('dashboard', 'index'))

    req_id = request.query.get('id')
    if not req_id:
        flash.set("Missing requisition id!", 'warning')
        redirect(URL('requisition_org', 'index'))

    try:
        req_id = int(req_id)  # ✅ ensure it's safe
    except ValueError:
        flash.set("Invalid requisition id!", 'warning')
        redirect(URL('requisition_org', 'index'))

    rows = db.executesql(
        f"""SELECT * FROM requisition WHERE id = {req_id}""",
        as_dict=True
    )
    if not rows:
        flash.set("Requisition not found!", 'warning')
        redirect(URL('requisition_org', 'index'))

    requisition = rows[0]

    return dict(
        status="success",
        requisition=requisition,
        organizations=get_combo_values("organizations"),
        asset_type_list=[r['text'] for r in get_asset_types()],
        requisition_status_combos=get_combo_values("requisition_status"),
        selected_asset_type=requisition['asset_type'],
        selected_org=requisition['org_name'],
        org_list=get_combo_values("organizations"),
        selected_requisition_status=requisition['req_status']
    )


# -----------------------------
# Update Endpoint (POST)
# -----------------------------
@action('requisition_org/update', method=['POST'])
@action.uses(db, session, flash)  # <-- Added flash here
def requisition_org_update():

    task_id='requisition_org_edit'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))

    form = request.forms

    req_id = form.get('id')
    org_name = form.get('org_name')
    asset_type = form.get('asset_type')
    quantity = form.get('quantity')
    requisition_status = form.get('requisition_status')

    # Validation
    if not req_id or not org_name or not asset_type or not requisition_status or not quantity:
        flash.set("All required fields must be filled.", "error")
        redirect(URL('requisition_org', 'edit', vars=dict(id=req_id)))

    try:
        db(db.requisition.id == int(req_id)).update(
            org_name=org_name.strip(),
            asset_type=asset_type.strip(),
            quantity=int(quantity),
            req_status=requisition_status.strip()
        )
        db.commit()

        flash.set(f"Requisition {req_id} updated successfully.", "success")
        redirect(URL('requisition_org', 'index'))

    except Exception as e:
        db.rollback()
        flash.set(f"Error updating requisition: {str(e)}", "error")
        redirect(URL('requisition_org', 'edit', vars=dict(id=req_id)))


@action('requisition_org/delete', method=['GET', 'POST'])
@action.uses(db, session, flash)
def delete_requisition_org():
    task_id='requisition_org_delete'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    requisition_id = request.query.get('id')
    if not requisition_id:
        flash.set('Missing requisition ID.', 'danger')
        redirect(URL('requisition_org/index'))

    try:
        record = db(db.requisition.id == requisition_id).select().first()
        if not record:
            flash.set('Requisition not found.', 'warning')
            redirect(URL('requisition_org/index'))

        # Get the `req_id` from the record
        req_id = record.req_id

        # Check if the `req_id` is used in the purchase_details table
        used_count = db(db.purchase_details.req_id == req_id).count()
        if used_count > 0:
            flash.set(
                f"Cannot delete requisition '{req_id}' because it is used in {used_count} purchase(s).",
                'warning'
            )

            redirect(URL('requisition_org/edit', vars=dict(id=requisition_id)))

        db((db.doc_metadata.trans_type == 'requisition') & (db.doc_metadata.trans_id == requisition_id)).delete()
        db(db.requisition.id == requisition_id).delete()
        flash.set('Requisition deleted successfully.', 'success')

    except Exception as e:
        flash.set(f'Error while deleting requisition: {str(e)}', 'danger')

    redirect(URL('requisition_org/index'))


