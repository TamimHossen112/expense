import json
from py4web import action, request, response, URL
from py4web.core import redirect
from ..common import db, session, T, flash


@action('vendor/index')
@action.uses("vendor/index.html",session, flash, )
def vendor_index():
    return locals()


@action('vendor/create')
@action.uses("vendor/create.html",session, flash)
def vendor_create():
    return locals()


@action('vendor/submit', method=['POST'])
@action.uses(db, session, T, flash)
def submit_vendor_data():
    vendor_name = request.forms.get('vendor_name')
    contact = request.forms.get('contact')
    vendor_address = request.forms.get('vendor_address')
    trade_license_no = request.forms.get('trade_license_no')

    errors = []

    if not vendor_name:
        errors.append("Vendor name is required.")
    if not contact:
        errors.append("Contact is required.")
    if not vendor_address:
        errors.append("Vendor Address is required")
    if not trade_license_no:
        errors.append("Trade License Number is required")

    if vendor_name and db(db.vendor.vendor_name == vendor_name).count() > 0:
        errors.append(f"Vendor '{vendor_name}' already exists.")

    if errors:
        flash.set(' | '.join(errors), 'warning')
        redirect(URL('vendor/create'))

    db.vendor.insert(
        vendor_name=vendor_name,
        contact=contact,
        vendor_address=vendor_address,
        trade_license_no=trade_license_no
    )

    flash.set("Vendor created successfully!", 'success')
    redirect(URL('vendor/index'))



@action('vendor/edit')
@action.uses('vendor/edit.html', db, session, flash)
def vendor_edit():
    vendor_id = request.query.get('id')
    if not vendor_id:
        flash.set("Invalid request. Vendor ID is required.", 'danger')
        redirect(URL('vendor/index'))

    record = db.vendor[ vendor_id ]
    if not record:
        flash.set("Vendor not found.", 'warning')
        redirect(URL('vendor/index'))

    return dict(record=record)



@action('vendor/update', method=['POST'])
@action.uses(db, session, flash)
def vendor_update():
    vendor_id = request.query.get('id')
    if not vendor_id:
        flash.set("Invalid request. Vendor ID is required.", 'danger')
        redirect(URL('vendor/index'))

    record = db.vendor[ vendor_id ]
    if not record:
        flash.set("Vendor not found.", 'warning')
        redirect(URL('vendor/index'))

    vendor_name = request.forms.get('vendor_name')
    contact = request.forms.get('contact')
    vendor_address = request.forms.get('vendor_address')
    trade_license_no = request.forms.get('trade_license_no')

    errors = []
    if not vendor_name:
        errors.append("Vendor name is required.")
    if not contact:
        errors.append("Contact is required.")
    if not vendor_address:
        errors.append("Vendor Address is required.")
    if not trade_license_no:
        errors.append("Trade License Number is required.")

    if vendor_name and db((db.vendor.vendor_name == vendor_name) & (db.vendor.id != vendor_id)).count() > 0:
        errors.append(f"Vendor '{vendor_name}' already exists.")

    if errors:
        flash.set(' | '.join(errors), 'warning')
        redirect(URL('vendor/edit', vars=dict(id=vendor_id)))

    record.update_record(
        vendor_name=vendor_name,
        contact=contact,
        vendor_address=vendor_address,
        trade_license_no=trade_license_no
    )

    flash.set("Vendor updated successfully!", 'success')
    redirect(URL('vendor/index'))



@action('vendor/get_data', method=['GET'])
@action.uses(db)
def get_vendor_data():
    vendor_name = request.query.get('vendor_name', '').strip()
    address = request.query.get('address', '').strip()

    where_clauses = ["1=1"]

    if vendor_name:
        where_clauses.append(f"vendor_name LIKE '%{vendor_name}%'")

    if address:
        where_clauses.append(f"vendor_address LIKE '%{address}%'")

    where_sql = " AND ".join(where_clauses)

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

    total_sql = f"""
        SELECT COUNT(*) AS total 
        FROM vendor
        WHERE {where_sql}
    """
    total_rows = db.executesql(total_sql, as_dict=True)[0]['total']

    base_sql = f"""
        SELECT id, cid, vendor_name, contact, vendor_address,
               trade_license_no
        FROM vendor
        WHERE {where_sql}
        ORDER BY {sort_col_name} {sort_dir}
    """

    if length != -1:
        base_sql += f" LIMIT {length} OFFSET {start}"

    data = db.executesql(base_sql, as_dict=True)

    return dict(
        data=data,
        recordsTotal=total_rows,
        recordsFiltered=total_rows,
        draw=int(request.query.get('draw') or 1)
    )


@action('vendor/delete', method=['POST', 'GET'])
@action.uses(db, session, T, flash)
def delete_vendor():
    vendor_id = request.query.get('id')

    if not vendor_id or not vendor_id.isdigit():
        flash.set('Invalid request: No ID provided.', 'danger')
        redirect(URL('vendor/index'))

    vendor = db.vendor(vendor_id)
    if not vendor:
        flash.set('Vendor not found.', 'danger')
        redirect(URL('vendor/index'))

    linked_purchases = db(db.purchase_head.vendor_id == int(vendor_id)).count()
    if linked_purchases > 0:
        flash.set(
            f"Cannot delete vendor (linked to {linked_purchases} purchase(s)).",
            'warning'
        )
        redirect(URL('vendor/edit', vars=dict(id=vendor_id)))

    vendor.delete_record()

    flash.set('Vendor deleted successfully.', 'success')
    redirect(URL('vendor/index'))




