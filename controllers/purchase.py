import json
from py4web import action, request, response, URL
from py4web.core import redirect
from ..common import db, session, T, flash
from datetime import datetime

# ---------- ID Generators ----------
def generate_id(table, field, prefix, type_char=None):
    last_row = db.executesql(
        f"SELECT {field} FROM {table} WHERE {field} IS NOT NULL ORDER BY id DESC LIMIT 1",
        as_dict=True
    )
    if not last_row:
        return f"{prefix}{type_char or ''}10000"
    last_id = last_row[0][field].strip()
    num = ''.join([c for c in last_id if c.isdigit()])
    return f"{prefix}{type_char or ''}{int(num) + 1 if num else 10000}"

def generate_purchase_head_id():
    return generate_id("purchase_head", "purchase_head_id", "P")

def generate_purchase_details_id(asset_type):
    type_char = asset_type.strip()[0].upper() if asset_type else "X"
    return generate_id("purchase_details", "purchase_details_id", "P", type_char)

# ---------- Helpers ----------
def get_combo_list(key):
    row = db(db.combo_settings.key == key).select(db.combo_settings.value).first()
    if not row or not row.value:
        return []
    return [{"id": val.strip(), "text": val.strip()} for val in row.value.split(",") if val.strip()]

def get_distinct_field_list(table_field):
    rows = db(table_field != None).select(table_field, distinct=True)
    return [{"id": r[table_field.name], "text": r[table_field.name]} for r in rows]

def parse_date(value):
    if value and str(value).strip():
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None
    return None

# ---------- Pages ----------
@action('purchase/index')
@action.uses("purchase/index.html", session, flash)
def purchase_index():
    return {}

@action('purchase/create')
@action.uses("purchase/create.html", db, session, flash)
def purchase_create():
    vendors = db(db.vendor.vendor_name != None).select(db.vendor.id, db.vendor.vendor_name, distinct=True).as_list()
    vendor_results = [{"id": v["id"], "text": v["vendor_name"]} for v in vendors if v["vendor_name"]]

    return dict(
        vendors=vendor_results,
        payment_status=get_combo_list("payment_status"),
        payment_type=get_combo_list("payment_type"),
        purchase_status=get_combo_list("purchase_status"),
        receive_status=get_combo_list("receive_status"),
        asset_types=get_distinct_field_list(db.asset_master.asset_type),
        asset_brands=get_distinct_field_list(db.asset_master.asset_brand),
        asset_models=get_distinct_field_list(db.asset_master.asset_model)
    )

@action('purchase/edit')
@action.uses("purchase/edit.html", db, session, flash)
def purchase_edit():
    purchase_head_id = request.query.get('id')
    if not purchase_head_id:
        return dict(error='Missing Purchase Head ID')

    row = db(db.purchase_head.id == purchase_head_id).select(limitby=(0,1)).first()
    if not row:
        return dict(error='Purchase Entry not found.')

    vendors = db(db.vendor.vendor_name != None).select(db.vendor.id, db.vendor.vendor_name, distinct=True).as_list()
    vendor_results = [{"id": v["id"], "text": v["vendor_name"]} for v in vendors]

    purchase_items = [
        dict(
            id=pi.id,
            req_id=pi.req_id,
            purchase_details_id=pi.purchase_details_id,
            asset_type=pi.asset_type,
            asset_brand=pi.asset_brand,
            asset_model=pi.asset_model,
            purchase_date=pi.purchase_date.isoformat() if pi.purchase_date else None,
            receive_status=pi.receive_status,
            received_date=pi.received_date.isoformat() if pi.received_date else None,
            item_price=pi.item_price,
            item_discount=pi.item_discount,
            item_asset_created=pi.asset_created
        )
        for pi in db(db.purchase_details.purchase_head_id == row.purchase_head_id).select()
    ]

    return dict(
        data=row.as_dict(),
        entrys_json=json.dumps(purchase_items),
        asset_types=get_distinct_field_list(db.asset_master.asset_type),
        asset_brands=get_distinct_field_list(db.asset_master.asset_brand),
        asset_models=get_distinct_field_list(db.asset_master.asset_model),
        payment_type_combos=get_combo_list("payment_type"),
        payment_status_combos=get_combo_list("payment_status"),
        purchase_status_combos=get_combo_list("purchase_status"),
        receive_status=get_combo_list("receive_status"),
        vendor_results=vendor_results,
        selected_vendor=f"{row.vendor_id} | {row.vendor_name}",
        selected_payment_type=row.payment_type,
        selected_payment_status=row.payment_status,
        selected_purchase_status=row.purchase_status
    )

# ---------- Submit / Update ----------
@action('purchase/submit')
@action.uses(db, session, flash)
def purchase_submit():
    vendor_value = request.forms.get('vendor_id', '').strip()
    bill_no = request.forms.get('bill_no', '').strip()
    purchase_date = request.forms.get('purchase_date', '').strip()
    payment_type = request.forms.get('payment_type', '').strip()
    payment_status = request.forms.get('payment_status', '').strip()
    purchase_status = request.forms.get('purchase_status', '').strip()
    remarks = request.forms.get('remarks', '').strip()
    purchase_items_json = request.forms.get('purchase_items_json', '').strip()

    vendor_id, vendor_name = (vendor_value.split('|',1)[0].strip(), vendor_value.split('|',1)[1].strip()) if '|' in vendor_value else (vendor_value, '')

    try:
        purchase_items = json.loads(purchase_items_json) if purchase_items_json else []
    except Exception as e:
        flash.set(f"Invalid purchase items JSON: {e}", "danger")
        redirect(URL('purchase/create'))

    # Check if purchase_status is 'received', all items must have receive_status 'received'
    if purchase_status.lower() == 'received':
        not_received_items = [item for item in purchase_items if (item.get('receive_status') or '').lower() != 'received']
        if not_received_items:
            flash.set("Cannot mark purchase as 'Received'. All purchase items must have status 'Received'.", "warning")
            redirect(URL('purchase/create'))

    total_price = sum(float(item.get('item_price') or 0) for item in purchase_items)
    total_discount = sum(float(item.get('item_discount') or 0) for item in purchase_items)
    total_payable = total_price - total_discount

    purchase_head_id = generate_purchase_head_id()
    db.purchase_head.insert(
        cid="SKF",
        purchase_head_id=purchase_head_id,
        vendor_id=vendor_id,
        vendor_name=vendor_name,
        bill_no=bill_no,
        total_price=total_price,
        total_discount=total_discount,
        total_payable=total_payable,
        purchase_date=parse_date(purchase_date),
        payment_type=payment_type,
        payment_status=payment_status,
        purchase_status=purchase_status,
        remarks=remarks,
    )

    for index, item in enumerate(purchase_items, start=1):
        db.purchase_details.insert(
            cid="SKF",
            purchase_head_id=purchase_head_id,
            purchase_details_id=f"{purchase_head_id}{index:03d}",
            req_id=item.get('req_id'),
            asset_type=item.get('asset_type'),
            asset_brand=item.get('asset_brand'),
            asset_model=item.get('asset_model'),
            receive_status=item.get('receive_status'),
            purchase_date=parse_date(item.get('purchase_date')),
            received_date=parse_date(item.get('received_date')),
            item_price=item.get('item_price'),
            item_discount=item.get('item_discount'),
            asset_created=0
        )
    db.commit()
    flash.set("Purchase submitted successfully!", "success")
    redirect(URL('purchase/index'))



@action('purchase/update')
@action.uses(db, session, flash)
def purchase_update():
    purchase_head_id = request.query.get('id') or request.forms.get('id')
    if not purchase_head_id:
        flash.set("Missing purchase_head_id.", "danger")
        redirect(URL('purchase/index'))

    head_record = db(db.purchase_head.id == purchase_head_id).select().first()
    if not head_record:
        flash.set("Purchase head not found.", "danger")
        redirect(URL('purchase/index'))

    vendor_value = request.forms.get('vendor_id', '').strip()
    vendor_id, vendor_name = (vendor_value.split('|',1)[0].strip(), vendor_value.split('|',1)[1].strip()) if '|' in vendor_value else (vendor_value, '')

    bill_no = request.forms.get('bill_no', '').strip()
    purchase_date = parse_date(request.forms.get('purchase_date', '').strip())
    payment_type = request.forms.get('payment_type', '').strip()
    payment_status = request.forms.get('payment_status', '').strip()
    purchase_status = request.forms.get('purchase_status', '').strip()
    remarks = request.forms.get('remarks', '').strip()
    purchase_items_json = request.forms.get('purchase_items_json', '').strip()

    try:
        purchase_items = json.loads(purchase_items_json) if purchase_items_json else []
    except Exception as e:
        flash.set(f"Invalid purchase items JSON: {e}", "danger")
        redirect(URL('purchase/index'))

    # Validation: if purchase_status is 'received', all items must be 'received'
    if purchase_status.lower() == 'received':
        not_received_items = [item for item in purchase_items if (item.get('receive_status') or '').lower() != 'received']
        if not_received_items:
            flash.set("Cannot mark purchase as 'Received'. All purchase items must have receive status 'Received'.", "warning")
            redirect(URL('purchase/edit', vars=dict(id=purchase_head_id)))

    total_price = sum(float(item.get('item_price') or 0) for item in purchase_items)
    total_discount = sum(float(item.get('item_discount') or 0) for item in purchase_items)
    total_payable = total_price - total_discount

    db(db.purchase_head.id == purchase_head_id).update(
        vendor_id=vendor_id,
        vendor_name=vendor_name,
        bill_no=bill_no,
        total_price=total_price,
        total_discount=total_discount,
        total_payable=total_payable,
        purchase_date=purchase_date,
        payment_type=payment_type,
        payment_status=payment_status,
        purchase_status=purchase_status,
        remarks=remarks,
    )

    # Replace purchase details
    db(db.purchase_details.purchase_head_id == head_record.purchase_head_id).delete()
    for idx, item in enumerate(purchase_items, start=1):
        db.purchase_details.insert(
            cid="SKF",
            purchase_head_id=head_record.purchase_head_id,
            purchase_details_id=f"{head_record.purchase_head_id}{idx:03d}",
            req_id=item.get('req_id'),
            asset_type=item.get('asset_type'),
            asset_brand=item.get('asset_brand'),
            asset_model=item.get('asset_model'),
            purchase_date=parse_date(item.get('purchase_date')),
            receive_status=item.get('receive_status') or "Pending",
            received_date=parse_date(item.get('received_date')),
            item_price=item.get('item_price'),
            item_discount=item.get('item_discount'),
            asset_created=int(item.get('item_asset_created') or 0)
        )

    db.commit()
    flash.set("Purchase updated successfully!", "success")
    redirect(URL('purchase/index'))


# ---------- Data Fetch ----------
@action('purchase/get_data', method=['GET'])
@action.uses(db)
def purchase_get_data():
    filters = {
        'vendor_name': request.query.get('vendor_name', '').strip(),
        'payment_status': request.query.get('payment_status', '').strip(),
        'purchase_status': request.query.get('purchase_status', '').strip(),
        'payment_type': request.query.get('payment_type', '').strip()
    }

    where_clauses = ["1=1"]
    params = []
    for k,v in filters.items():
        if v:
            where_clauses.append(f"{k} = %s")
            params.append(v)

    where_sql = " AND ".join(where_clauses)

    start = int(request.query.get('start') or 0)
    length = int(request.query.get('length') or 15)

    sort_col_index = request.query.get('order[0][column]')
    if sort_col_index is None:
        sort_col_name, sort_dir = 'id', 'desc'
    else:
        sort_col_index = int(sort_col_index)
        sort_col_name = request.query.get(f'columns[{sort_col_index}][data]') or 'id'
        sort_dir = request.query.get('order[0][dir]', 'desc').lower()
        sort_dir = sort_dir if sort_dir in ['asc', 'desc'] else 'desc'

    total_sql = f"SELECT COUNT(*) AS total FROM purchase_head WHERE {where_sql}"
    total_rows = db.executesql(total_sql, params, as_dict=True)[0]['total']

    base_sql = f"""
        SELECT id, purchase_head_id, vendor_name, bill_no, total_payable, purchase_date,
               payment_type, payment_status, purchase_status
        FROM purchase_head
        WHERE {where_sql}
        ORDER BY {sort_col_name} {sort_dir}
        {"LIMIT %s OFFSET %s" % (length, start) if length != -1 else ""}
    """

    data = db.executesql(base_sql, params, as_dict=True)
    return dict(
        data=data,
        recordsTotal=total_rows,
        recordsFiltered=total_rows,
        draw=int(request.query.get('draw') or 1)
    )
