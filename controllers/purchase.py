import json
from py4web import action, request, URL
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
def parse_date(value):
    if value and str(value).strip():
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None
    return None

def get_combo_list(key):
    row = db(db.combo_settings.key == key).select(db.combo_settings.value).first()
    if not row or not row.value:
        return []
    return [{"id": val.strip(), "text": val.strip()} for val in row.value.split(",") if val.strip()]

def get_distinct_field_list(table_field):
    rows = db(table_field != None).select(table_field, distinct=True)
    return [{"id": r[table_field.name], "text": r[table_field.name]} for r in rows]

def parse_vendor(vendor_value):
    if "|" in vendor_value:
        vid, vname = vendor_value.split("|", 1)
        return vid.strip(), vname.strip()
    return vendor_value, ""

def calculate_item_totals(item):
    qty = int(item.get('quantity') or 0)
    price = float(item.get('item_price') or 0)
    discount = float(item.get('item_discount') or 0)
    gross = qty * price
    net = gross - discount
    item.update({
        "quantity": qty,
        "item_price": price,
        "item_discount": discount,
        "item_gross_total": gross,
        "item_net_total": net
    })
    return gross, discount, net

def validate_items(items):
    errors = []
    if not items:
        errors.append("At least one purchase item is required.")
        return errors

    for i, item in enumerate(items, start=1):
        if not item.get('req_id'): errors.append(f"Item {i}: req_id is required.")
        if not item.get('asset_type'): errors.append(f"Item {i}: asset_type is required.")
        if not item.get('asset_brand'): errors.append(f"Item {i}: asset_brand is required.")
        if not item.get('asset_model'): errors.append(f"Item {i}: asset_model is required.")
        if item.get('quantity') is None or int(item.get('quantity') or 0) <= 0:
            errors.append(f"Item {i}: quantity must be greater than 0.")
        if item.get('item_price') is None or float(item.get('item_price') or 0) < 0:
            errors.append(f"Item {i}: item_price must be >= 0.")
    return errors

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

# ---------- Submit ----------
@action('purchase/submit')
@action.uses(db, session, flash)
def purchase_submit():
    # ---------- Form Data ----------
    vendor_value   = request.forms.get('vendor_id', '').strip()
    bill_no        = request.forms.get('bill_no', '').strip()
    purchase_date  = request.forms.get('purchase_date', '').strip()
    payment_type   = request.forms.get('payment_type', '').strip()
    payment_status = request.forms.get('payment_status', '').strip()
    remarks        = request.forms.get('remarks', '').strip()
    purchase_items_json = request.forms.get('purchase_items_json', '').strip()

    # ---------- Validation ----------
    errors = []
    if not vendor_value:   errors.append("Vendor is required.")
    if not bill_no:        errors.append("Bill number is required.")
    if not purchase_date:  errors.append("Purchase date is required.")
    if not payment_type:   errors.append("Payment type is required.")
    if not payment_status: errors.append("Payment status is required.")

    try:
        purchase_items = json.loads(purchase_items_json) if purchase_items_json else []
    except Exception as e:
        flash.set(f"Bad purchase items JSON: {e}", "danger")
        redirect(URL('purchase/create'))

    errors += validate_items(purchase_items)
    if errors:
        flash.set(" ".join(errors), "danger")
        redirect(URL('purchase/create'))

    vendor_id, vendor_name = parse_vendor(vendor_value)

    try:
        # ------------------------------------------------------
        # Step 1: Aggregate requisition quantities
        # ------------------------------------------------------
        req_totals = {}
        for item in purchase_items:
            req_id = item['req_id']
            req_totals[req_id] = req_totals.get(req_id, 0) + int(item['quantity'])

        # ------------------------------------------------------
        # Step 2: Validate against requisition table
        # ------------------------------------------------------
        req_ids = list(req_totals.keys())
        placeholders = ",".join(["%s"] * len(req_ids))

        rows = db.executesql(
            f"""
            SELECT r.req_id,
                   r.quantity AS req_quantity,
                   COALESCE(SUM(p.quantity), 0) AS purchased_qty
            FROM requisition r
            LEFT JOIN purchase_details p
              ON r.req_id = p.req_id
            WHERE r.req_id IN ({placeholders})
            GROUP BY r.req_id
            """,
            req_ids,
            as_dict=True
        )

        db_data = {row['req_id']: row for row in rows}

        for req_id, total_qty in req_totals.items():
            if req_id not in db_data:
                raise Exception(f"Invalid requisition ID: {req_id}")

            req_qty = int(db_data[req_id]['req_quantity'])
            already_purchased = int(db_data[req_id]['purchased_qty'])
            max_allowed = req_qty - already_purchased

            if total_qty > max_allowed:
                raise Exception(
                    f"Cannot purchase {total_qty} units for ReqID {req_id}. "
                    f"Max allowed is {max_allowed}."
                )

        # ------------------------------------------------------
        # Step 3: Insert purchase head
        # ------------------------------------------------------
        total_gross = total_discount = total_payable = 0
        for item in purchase_items:
            gross, discount, net = calculate_item_totals(item)
            total_gross    += gross
            total_discount += discount
            total_payable  += net

        purchase_head_id = generate_purchase_head_id()
        db.purchase_head.insert(
            cid="SKF",
            purchase_head_id=purchase_head_id,
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            bill_no=bill_no,
            total_price=total_gross,
            total_discount=total_discount,
            total_payable=total_payable,
            purchase_date=parse_date(purchase_date),
            payment_type=payment_type,
            payment_status=payment_status,
            purchase_status="pending",
            remarks=remarks,
        )

        # ------------------------------------------------------
        # Step 4: Insert purchase details
        # ------------------------------------------------------
        all_statuses = []
        purchase_details = []
        for i, item in enumerate(purchase_items, start=1):
            status = (item.get('receive_status') or "pending").lower()
            all_statuses.append(status)

            purchase_details.append({
                'cid': "SKF",
                'purchase_head_id': purchase_head_id,
                'purchase_details_id': f"{purchase_head_id}{i:03d}",
                'req_id': item['req_id'],
                'asset_type': item.get('asset_type'),
                'asset_brand': item.get('asset_brand'),
                'asset_model': item.get('asset_model'),
                'receive_status': status,
                'purchase_date': parse_date(item.get('purchase_date')),
                'received_date': parse_date(item.get('received_date')),
                'item_price': item['item_price'],
                'item_gross_total': item['item_gross_total'],
                'item_discount': item['item_discount'],
                'item_net_total': item['item_net_total'],
                'quantity': item['quantity'],
                'asset_created': int(item.get('item_asset_created') or 0),
            })

        db.purchase_details.bulk_insert(purchase_details)

        # ------------------------------------------------------
        # Step 5: Finalize purchase head status
        # ------------------------------------------------------
        final_status = all_statuses[0] if all(all_statuses[0] == s for s in all_statuses) else "pending"
        db(db.purchase_head.purchase_head_id == purchase_head_id).update(
            purchase_status=final_status
        )

        db.commit()
        flash.set("Purchase submitted successfully!", "success")

    except Exception as e:
        db.rollback()
        flash.set(str(e), "danger")
        redirect(URL('purchase/create'))

    redirect(URL('purchase/index'))



# ---------- Edit ----------
@action('purchase/edit')
@action.uses("purchase/edit.html", db, session, flash)
def purchase_edit():
    purchase_head_id = request.query.get('id')
    if not purchase_head_id:
        return dict(error='Missing Purchase Head ID')

    row = db(db.purchase_head.id == purchase_head_id).select().first()
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
            quantity=pi.quantity,
            item_price=pi.item_price,
            item_gross_total=pi.item_gross_total,
            item_discount=pi.item_discount,
            item_net_total=pi.item_net_total,
            item_asset_created=pi.asset_created,
        )
        for pi in db(db.purchase_details.purchase_head_id == row.purchase_head_id).select()
    ]

    return dict(
        notdata=row,
        entrys_json=json.dumps(purchase_items),
        asset_types=get_distinct_field_list(db.asset_master.asset_type),
        asset_brands=get_distinct_field_list(db.asset_master.asset_brand),
        asset_models=get_distinct_field_list(db.asset_master.asset_model),
        payment_type_combos=get_combo_list("payment_type"),
        payment_status_combos=get_combo_list("payment_status"),
        receive_status=get_combo_list("purchase_status"),
        vendor_results=vendor_results,
        selected_vendor=f"{row.vendor_id} | {row.vendor_name}",
        selected_payment_type=row.payment_type,
        selected_payment_status=row.payment_status,
    )

@action('purchase/update')
@action.uses(db, session, flash)
def purchase_update():
    record_id = request.query.get('id') or request.forms.get('id')
    if not record_id:
        flash.set("Missing purchase ID.", "danger")
        redirect(URL('purchase/index'))

    head_record = db(db.purchase_head.id == record_id).select().first()
    if not head_record:
        flash.set("Purchase head not found.", "danger")
        redirect(URL('purchase/index'))

    purchase_head_id = head_record.purchase_head_id

    vendor_value   = request.forms.get('vendor_id', '').strip()
    bill_no        = request.forms.get('bill_no', '').strip()
    purchase_date  = request.forms.get('purchase_date', '').strip()
    payment_type   = request.forms.get('payment_type', '').strip()
    payment_status = request.forms.get('payment_status', '').strip()
    remarks        = request.forms.get('remarks', '').strip()
    purchase_items_json = request.forms.get('purchase_items_json', '').strip()

    errors = []
    if not vendor_value:   errors.append("Vendor is required.")
    if not bill_no:        errors.append("Bill number is required.")
    if not purchase_date:  errors.append("Purchase date is required.")
    if not payment_type:   errors.append("Payment type is required.")
    if not payment_status: errors.append("Payment status is required.")

    try:
        purchase_items = json.loads(purchase_items_json) if purchase_items_json else []
    except Exception as e:
        flash.set(f"Bad purchase items JSON: {e}", "danger")
        redirect(URL('purchase/edit', vars=dict(id=record_id)))

    errors += validate_items(purchase_items)
    if errors:
        flash.set(" ".join(errors), "danger")
        redirect(URL('purchase/edit', vars=dict(id=record_id)))

    vendor_id, vendor_name = parse_vendor(vendor_value)

    try:

        req_totals = {}
        for item in purchase_items:
            req_id = item['req_id']
            req_totals[req_id] = req_totals.get(req_id, 0) + int(item['quantity'])

        rows = db.executesql(
            f"""
            SELECT r.req_id,
                   r.quantity AS req_quantity,
                   COALESCE(SUM(p.quantity), 0) AS purchased_qty
            FROM requisition r
            LEFT JOIN purchase_details p
              ON r.req_id = p.req_id
             -- exclude current purchase head to avoid double counting during edit
             AND p.purchase_head_id != %(head_id)s
            WHERE r.req_id IN %(req_ids)s
            GROUP BY r.req_id
            """,
            dict(head_id=purchase_head_id, req_ids=tuple(req_totals.keys())),
            as_dict=True
        )

        req_lookup = {row['req_id']: row for row in rows}

        validation_errors = []
        for req_id, total_qty in req_totals.items():
            row = req_lookup.get(req_id)
            if not row:
                validation_errors.append(f"Invalid requisition ID: {req_id}")
                continue

            req_qty = int(row['req_quantity'])
            already_purchased = int(row['purchased_qty'])
            max_allowed = req_qty - already_purchased

            if total_qty > max_allowed:
                validation_errors.append(
                    f"Requisition ID {req_id}: requested {total_qty} quantity, {max_allowed} is max allowed "
                )

        if validation_errors:
            flash.set(" ; ".join(validation_errors), "danger")
            redirect(URL('purchase/edit', vars=dict(id=record_id)))

        total_gross = total_discount = total_payable = 0
        all_statuses = []
        purchase_details = []

        for i, item in enumerate(purchase_items, start=1):
            gross, discount, net = calculate_item_totals(item)
            total_gross    += gross
            total_discount += discount
            total_payable  += net

            status = (item.get('receive_status') or "pending").lower()
            all_statuses.append(status)

            purchase_details.append({
                'cid': "SKF",
                'purchase_head_id': purchase_head_id,
                'purchase_details_id': f"{purchase_head_id}{i:03d}",
                'req_id': item['req_id'],
                'asset_type': item.get('asset_type'),
                'asset_brand': item.get('asset_brand'),
                'asset_model': item.get('asset_model'),
                'receive_status': status,
                'purchase_date': parse_date(item.get('purchase_date')),
                'received_date': parse_date(item.get('received_date')),
                'item_price': item['item_price'],
                'item_gross_total': item['item_gross_total'],
                'item_discount': item['item_discount'],
                'item_net_total': item['item_net_total'],
                'quantity': item['quantity'],
                'asset_created': int(item.get('item_asset_created') or 0)
            })

        final_status = all_statuses[0] if all(all_statuses[0] == s for s in all_statuses) else "pending"

        db(db.purchase_details.purchase_head_id == purchase_head_id).delete()

        db(db.purchase_head.purchase_head_id == purchase_head_id).update(
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            bill_no=bill_no,
            total_price=total_gross,
            total_discount=total_discount,
            total_payable=total_payable,
            purchase_date=parse_date(purchase_date),
            payment_type=payment_type,
            payment_status=payment_status,
            remarks=remarks,
            purchase_status=final_status
        )

        db.purchase_details.bulk_insert(purchase_details)
        db.commit()
        flash.set("Purchase updated successfully!", "success")

    except Exception as e:
        db.rollback()
        flash.set(str(e), "danger")
        redirect(URL('purchase/edit', vars=dict(id=record_id)))

    redirect(URL('purchase/index'))



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


@action('purchase/delete', method=['GET', 'POST'])
@action.uses(db, session, flash)
def purchase_delete():
    purchase_id = request.query.get('id')
    if not purchase_id:
        flash.set('Missing purchase ID.', 'danger')
        redirect(URL('purchase/index'))

    try:
        head_record = db(db.purchase_head.id == purchase_id).select().first()
        if not head_record:
            flash.set('Purchase not found.', 'warning')
            redirect(URL('purchase/index'))

        purchase_head_id = head_record.purchase_head_id

        asset_count = db(db.asset.purchase_head_id == purchase_head_id).count()
        if asset_count > 0:
            flash.set(
                f"Cannot delete purchase '{purchase_head_id}' because it is used in {asset_count} asset(s).",
                'warning'
            )
            redirect(URL('purchase/edit', vars=dict(id=purchase_id)))

        db(db.purchase_details.purchase_head_id == purchase_head_id).delete()

        db(db.purchase_head.id == purchase_id).delete()

        flash.set('Purchase deleted successfully.', 'success')

    except Exception as e:
        flash.set(f'Error while deleting purchase: {str(e)}', 'danger')

    redirect(URL('purchase/index'))
