import json
from py4web import action, request, response, URL
from py4web.core import redirect
from ..common import db, session, T, flash
from ..common_fn import check_role

# ---------------- Helper Functions ---------------- #

def flash_redirect(message, type_, endpoint, vars=None):

    flash.set(message, type_)
    redirect(URL(endpoint, vars=vars or {}))


def validate_vendor_data(vendor_name, contact, vendor_address, trade_license_no):
    errors = []
    if not vendor_name:
        errors.append("Vendor name is required.")
    if not contact:
        errors.append("Contact is required.")
    if not vendor_address:
        errors.append("Vendor Address is required.")
    if not trade_license_no:
        errors.append("Trade License Number is required.")
    return errors


def vendor_exists(vendor_name, vendor_address, exclude_id=None):
    query = (db.vendor.vendor_name == vendor_name) & (db.vendor.vendor_address == vendor_address)
    if exclude_id:
        query &= (db.vendor.id != exclude_id)
    return db(query).count() > 0


def get_vendor_or_redirect(vendor_id):
    if not vendor_id or not str(vendor_id).isdigit():
        flash_redirect("Invalid request. Vendor ID is required.", "danger", "vendor/index")
    record = db.vendor[vendor_id]
    if not record:
        flash_redirect("Vendor not found.", "warning", "vendor/index")
    return record

# ---------------- Vendor Actions ---------------- #

@action('vendor/index')
@action.uses("vendor/index.html", db, session, flash)
def vendor_index():
    task_id='vendor_view'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('login','index'))

    return locals()


@action('vendor/create')
@action.uses("vendor/create.html", db, session, flash)
def vendor_create():
    task_id='vendor_create'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))

    return locals()


@action('vendor/submit', method=['POST'])
@action.uses(db, session, flash)
def submit_vendor_data():
    task_id='vendor_create'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))

    vendor_name = (request.forms.get('vendor_name') or '').strip()
    contact = (request.forms.get('contact') or '').strip()
    vendor_address = (request.forms.get('vendor_address') or '').strip()
    trade_license_no = (request.forms.get('trade_license_no') or '').strip()
    status = request.forms.get('status', 'inactive').strip()

    errors = validate_vendor_data(vendor_name, contact, vendor_address, trade_license_no)

    if vendor_exists(vendor_name, vendor_address):
        errors.append(f"Vendor '{vendor_name}' with the same address already exists.")

    if errors:
        flash_redirect(' | '.join(errors), 'warning', 'vendor/create')

    db.vendor.insert(
        vendor_name=vendor_name,
        contact=contact,
        vendor_address=vendor_address,
        trade_license_no=trade_license_no,
        status=status
    )

    flash_redirect("Vendor created successfully!", 'success', 'vendor/index')


@action('vendor/edit')
@action.uses('vendor/edit.html', db, session, flash)
def vendor_edit():
    task_id='vendor_edit'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    vendor_id = request.query.get('id')
    record = get_vendor_or_redirect(vendor_id)
    return dict(record=record,access_permission=check_role('vendor_edit'))


@action('vendor/update', method=['POST'])
@action.uses(db, session, flash)
def vendor_update():
    vendor_id = request.query.get('id')
    record = get_vendor_or_redirect(vendor_id)

    vendor_name = (request.forms.get('vendor_name') or '').strip()
    contact = (request.forms.get('contact') or '').strip()
    vendor_address = (request.forms.get('vendor_address') or '').strip()
    trade_license_no = (request.forms.get('trade_license_no') or '').strip()
    status = request.forms.get('status', 'inactive').strip()

    errors = validate_vendor_data(vendor_name, contact, vendor_address, trade_license_no)

    if vendor_exists(vendor_name, vendor_address, exclude_id=vendor_id):
        errors.append(f"Vendor '{vendor_name}' with the same address already exists.")

    if errors:
        flash_redirect(' | '.join(errors), 'warning', 'vendor/edit', vars=dict(id=vendor_id))

    record.update_record(
        vendor_name=vendor_name,
        contact=contact,
        vendor_address=vendor_address,
        trade_license_no=trade_license_no,
        status=status
    )

    flash_redirect("Vendor updated successfully!", 'success', 'vendor/index')


@action('vendor/get_data', method=['GET'])
@action.uses(db,session,flash)
def get_vendor_data():
    task_id='vendor_view'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    vendor_name = (request.query.get('vendor_name') or '').strip()
    address = (request.query.get('address') or '').strip()
    start = int(request.query.get('start') or 0)
    length = int(request.query.get('length') or 15)

    sort_col_index = request.query.get('order[0][column]')
    if sort_col_index is None:
        sort_col_name = 'id'
        sort_dir = 'desc'
    else:
        sort_col_index = int(sort_col_index)
        sort_col_name = request.query.get(f'columns[{sort_col_index}][data]') or 'id'
        sort_dir = request.query.get('order[0][dir]', 'desc').lower()
        if sort_dir not in ['asc', 'desc']:
            sort_dir = 'desc'

    where_clauses = ["1=1"]
    if vendor_name:
        where_clauses.append(f"vendor_name LIKE '%{vendor_name}%'")
    if address:
        where_clauses.append(f"vendor_address LIKE '%{address}%'")
    where_sql = " AND ".join(where_clauses)

    total_sql = f"SELECT COUNT(*) AS total FROM vendor WHERE {where_sql}"
    total_rows = db.executesql(total_sql, as_dict=True)[0]['total']

    base_sql = f"""
        SELECT id, vendor_name, contact, vendor_address, trade_license_no, status
        FROM vendor
        WHERE {where_sql}
        ORDER BY {sort_col_name} {sort_dir}
        LIMIT {length} OFFSET {start}
    """
    data = db.executesql(base_sql, as_dict=True)

    return dict(
        data=data,
        recordsTotal=total_rows,
        recordsFiltered=total_rows,
        draw=int(request.query.get('draw') or 1)
    )


@action('vendor/delete', method=['POST', 'GET'])
@action.uses(db, session, flash)
def delete_vendor():
    task_id='vendor_delete'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    vendor_id = request.query.get('id')
    vendor = get_vendor_or_redirect(vendor_id)

    linked_purchases = db(db.purchase_head.vendor_id == int(vendor_id)).count()
    if linked_purchases > 0:
        flash_redirect(
            f"Cannot delete vendor (linked to {linked_purchases} purchase).",
            'warning',
            'vendor/edit',
            vars=dict(id=vendor_id)
        )

    vendor.delete_record()
    flash_redirect('Vendor deleted successfully.', 'success', 'vendor/index')


