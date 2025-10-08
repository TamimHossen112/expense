import json
from py4web import action, request, redirect, URL, response
from ..common import db, session, T, flash
from ..common_fn import IMAGE_UPLOAD_API, IMAGE_DOWNLOAD_API
import requests


# ---------------------- Helper Functions ----------------------
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


def parse_uploaded_files():
    files = []
    index = 0
    while True:
        doc_type = request.forms.get(f'uploaded_files[{index}][doc_type]')
        file_name = request.forms.get(f'uploaded_files[{index}][file_name]')
        file_path = request.forms.get(f'uploaded_files[{index}][file_path]')
        if not any([doc_type, file_name, file_path]):
            break
        files.append({"doc_type": doc_type, "file_name": file_name, "file_path": file_path})
        index += 1
    return files


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

def fetch_uploaded_files(trans_type, trans_id):
    files = db(
        (db.doc_metadata.trans_type == trans_type) & 
        (db.doc_metadata.trans_id == trans_id)
    ).select(db.doc_metadata.doc_type, db.doc_metadata.file_name, db.doc_metadata.file_path)
    return [dict(doc_type=f.doc_type, file_name=f.file_name, file_path=f.file_path) for f in files]



# ---------------------- Requisition Views ----------------------
@action('requisition_field/index')
@action.uses('requisition_field/index.html', db, session, flash)
def requisition_field_index():
    return locals()


@action('requisition_field/create')
@action.uses('requisition_field/create.html', db, session, flash)
def requisition_individual_create():
    dummy_employee = dict(
        emp_id="EMP12345456 | John Dolarami",
        emp_category="Full-Time",
        designation="Sales Executive",
        tr_code="TR-001",
        head_office="Dhaka",
        joining_date="2022-07-23"
    )

    return dict(
        IMAGE_UPLOAD_API=IMAGE_UPLOAD_API,
        IMAGE_DOWNLOAD_API=IMAGE_DOWNLOAD_API,
        doc_type_combos=get_combo_values("requisition_doc_type"),
        record=dummy_employee,
        asset_types=get_asset_types(),
    )


@action('requisition_field/submit', method=['POST'])
@action.uses(db, session, flash)
def requisition_field_submit():
    # ---------- Extract form values ----------
    asset_type = request.forms.get('asset_type')
    emp_id_raw = request.forms.get('emp_id')
    designation = request.forms.get('designation')
    tr_code = request.forms.get('tr_code')
    head_office = request.forms.get('head_office')
    joining_date = request.forms.get('joining_date')
    license_issue_date = request.forms.get('license_issue_date')
    license_expire_date = request.forms.get('license_expire_date')
    license_number = request.forms.get('license_number')

    # ---------- Determine which button was clicked ----------
    submit_type = request.forms.get('submit_type', 'pending')  # 'draft' or 'pending'
    req_status = 'pending' if submit_type.lower() == 'pending' else 'draft'

    # ---------- Split emp_id and emp_name ----------
    emp_id = None
    emp_name = None
    if emp_id_raw:
        parts = [p.strip() for p in emp_id_raw.split("|", 1)]
        emp_id = parts[0] if len(parts) > 0 else None
        emp_name = parts[1] if len(parts) > 1 else None

    # ---------- Uploaded files ----------
    uploaded_files = parse_uploaded_files()

    # ---------- Validation ----------
    required_fields = {
        "Asset Type": asset_type,
        "Employee ID": emp_id,
        "Joining Date": joining_date,
        "Driving License Issue Date": license_issue_date,
        "Driving License Expire Date": license_expire_date,
        "Driving License Number": license_number,
    }
    missing_fields = [name for name, val in required_fields.items() if not val]
    if missing_fields:
        flash.set("The following fields are required: " + ", ".join(missing_fields), 'warning')
        redirect(URL('requisition_field/create'))

    # ---------- Extra Validation (if approved) ----------
    if req_status.strip().lower() == "approved":
        existing_asset = db(db.asset.user_id == emp_id).select().first()
        if existing_asset:
            flash.set(f"{emp_name or emp_id} already has an assigned Vehicle. Cannot create approved requisition.", "warning")
            redirect(URL('requisition_field/create'))

    # ---------- Insert Requisition ----------
    try:
        req_code = generate_requisition_code(asset_type)
        requisition_id = db.requisition.insert(
            cid="SKF",
            req_id=req_code,
            asset_type=asset_type,
            emp_id=emp_id,
            emp_name=emp_name,
            designation=designation,
            tr_code=tr_code,
            head_office=head_office,
            joining_date=joining_date or None,
            license_issue_date=license_issue_date or None,
            license_expire_date=license_expire_date or None,
            license_number=license_number,
            req_status=req_status,  # <-- use the button's value
            quantity=1
        )

        # Insert uploaded files metadata
        for f in uploaded_files:
            db.doc_metadata.insert(
                trans_type="requisition",
                trans_id=requisition_id,
                doc_type=f.get('doc_type'),
                file_name=f.get('file_name'),
                file_path=f.get('file_path'),
                ref_emp_id=emp_id
            )

        db.commit()
        flash.set(f"Requisition {req_status.capitalize()} created successfully!", 'success')
        redirect(URL('requisition_field/index'))

    except Exception as e:
        db.rollback()
        flash.set(f"An unexpected error occurred: {str(e)}", 'danger')
        redirect(URL('requisition_field/create'))



@action('requisition_field/edit')
@action.uses('requisition_field/edit.html', db, session, flash)
def requisition_field_edit():

    req_id = request.query.get('id')
    if not req_id:
        flash.set("Missing requisition ID!", 'warning')
        redirect(URL('requisition_field', 'index'))

    try:
        req_id = int(req_id)  # ✅ strong validation
    except ValueError:
        flash.set("Invalid requisition ID!", 'warning')
        redirect(URL('requisition_field', 'index'))

    row = db(db.requisition.id == req_id).select().first()
    if not row:
        flash.set("Requisition not found!", 'warning')
        redirect(URL('requisition_field', 'index'))

    # Already uploaded files
    file_metadata = fetch_uploaded_files('requisition', row.id)

    # Dropdown values
    doc_type_combos = get_combo_values("requisition_doc_type")
    asset_type_list = [r['text'] for r in get_asset_types()]

    return dict(
        record=row.as_dict(),
        docs=file_metadata,
        docs_json=json.dumps(file_metadata),
        IMAGE_UPLOAD_API=IMAGE_UPLOAD_API,
        IMAGE_DOWNLOAD_API=IMAGE_DOWNLOAD_API,
        doc_type_combos=doc_type_combos,
        asset_type_list=asset_type_list,
        selected_asset_type=row.asset_type
    )

@action('requisition_field/update', method=['POST'])
@action.uses(db, session, flash)
def requisition_field_update():
    req_id_raw = request.query.get('id')
    if not req_id_raw:
        flash.set("Missing requisition ID!", 'warning')
        redirect(URL('requisition_field/index'))

    try:
        req_id = int(req_id_raw)
    except ValueError:
        flash.set("Invalid requisition ID!", 'warning')
        redirect(URL('requisition_field/index'))

    row = db(db.requisition.id == req_id).select().first()
    if not row:
        flash.set("Requisition not found!", 'warning')
        redirect(URL('requisition_field/index'))

    # Prevent updates if already pending or approved
    if row.req_status.lower() in ['pending', 'approved']:
        flash.set(f"Cannot update requisition because its status is '{row.req_status}'. Only draft can be updated.", 'warning')
        redirect(URL('requisition_field/index'))

    # ---------- Extract form values ----------
    asset_type = request.forms.get('asset_type')
    emp_id_raw = request.forms.get('emp_id')
    designation = request.forms.get('designation')
    tr_code = request.forms.get('tr_code')
    head_office = request.forms.get('head_office')
    joining_date = request.forms.get('joining_date')
    license_issue_date = request.forms.get('license_issue_date')
    license_expire_date = request.forms.get('license_expire_date')
    license_number = request.forms.get('license_number')

    submit_type = request.forms.get('submit_type', 'pending')
    req_status = 'pending' if submit_type.lower() == 'pending' else 'draft'

    emp_id, emp_name = None, None
    if emp_id_raw:
        parts = [p.strip() for p in emp_id_raw.split("|", 1)]
        emp_id = parts[0] if len(parts) > 0 else None
        emp_name = parts[1] if len(parts) > 1 else None

    uploaded_files = parse_uploaded_files()  # [] if empty, None if untouched (depends on parser)

    # ---------- Validation ----------
    required_fields = {
        "Asset Type": asset_type,
        "Employee ID": emp_id,
        "Joining Date": joining_date,
        "Driving License Issue Date": license_issue_date,
        "Driving License Expire Date": license_expire_date,
        "Driving License Number": license_number,
    }
    missing_fields = [name for name, val in required_fields.items() if not val]
    if missing_fields:
        flash.set("The following fields are required: " + ", ".join(missing_fields), 'warning')
        redirect(URL('requisition_field/edit', vars=dict(id=req_id)))

    if req_status.strip().lower() == "approved":
        existing_asset = db((db.asset.user_id == emp_id) & (db.asset.requisition_id != req_id)).select().first()
        if existing_asset:
            flash.set(f"{emp_name or emp_id} already has an assigned Vehicle. Cannot approve this requisition.", "warning")
            redirect(URL('requisition_field/edit', vars=dict(id=req_id)))

    # ---------- Update ----------
    try:
        db(db.requisition.id == req_id).update(
            asset_type=asset_type,
            emp_id=emp_id,
            emp_name=emp_name,
            designation=designation,
            tr_code=tr_code,
            head_office=head_office,
            joining_date=joining_date or None,
            license_issue_date=license_issue_date or None,
            license_expire_date=license_expire_date or None,
            license_number=license_number,
            req_status=req_status,
        )

        # Handle attachments
        if uploaded_files is not None:
            db((db.doc_metadata.trans_type == "requisition") &
               (db.doc_metadata.trans_id == req_id)).delete()

            for f in uploaded_files:
                db.doc_metadata.insert(
                    trans_type="requisition",
                    trans_id=req_id,
                    doc_type=f.get('doc_type'),
                    file_name=f.get('file_name'),
                    file_path=f.get('file_path'),
                    ref_emp_id=emp_id
                )

        db.commit()
        flash.set(f"Requisition {req_status.capitalize()} updated successfully!", 'success')
        redirect(URL('requisition_field/index'))

    except Exception as e:
        db.rollback()
        flash.set(f"An unexpected error occurred: {str(e)}", 'danger')
        redirect(URL('requisition_field/edit', vars=dict(id=req_id)))




# ---------------------- Data API ----------------------
@action('requisition_field/get_data', method=['GET'])
@action.uses(db, session, flash)
def requisition_field_get_data():
    q = request.query
    start, length = int(q.get('start', 0)), int(q.get('length', 10))
    draw = int(q.get('draw', 1))

    sort_col_index = q.get('order[0][column]')
    sort_dir = q.get('order[0][dir]', 'desc').lower()
    sort_dir = sort_dir if sort_dir in ['asc', 'desc'] else 'desc'
    sort_col = 'id'

    if sort_col_index is not None:
        sort_col_index = int(sort_col_index)
        sort_col = q.get(f'columns[{sort_col_index}][data]', 'id')

    # Build filters
    filters = ["org_name IS NULL"]  # always filter org_name
    if q.get('req_status'):
        filters.append(f"req_status='{q['req_status'].strip()}'")
    if q.get('asset_type'):
        filters.append(f"asset_type='{q['asset_type'].strip()}'")
    if q.get('emp_id') and q['emp_id'].isdigit():
        filters.append(f"emp_id={int(q['emp_id'].strip())}")
    if q.get('head_office'):
        filters.append(f"head_office LIKE '%{q['head_office'].strip()}%'")

    where_sql = " AND ".join(filters)

    # Total records (before filtering)
    total_records = db.executesql(
        "SELECT COUNT(*) AS total FROM requisition",
        as_dict=True
    )[0]['total']

    # Total filtered records
    total_filtered = db.executesql(
        f"SELECT COUNT(*) AS total FROM requisition WHERE {where_sql}",
        as_dict=True
    )[0]['total']

    # Fetch paginated data
    base_sql = f"""
        SELECT id, req_id, asset_type, emp_id, emp_name, designation,
               tr_code, head_office, joining_date, license_number,
               req_status, quantity
        FROM requisition
        WHERE {where_sql}
        ORDER BY {sort_col} {sort_dir}
        LIMIT {length} OFFSET {start}
    """
    data = db.executesql(base_sql, as_dict=True)

    return dict(
        draw=draw,
        recordsTotal=total_records,
        recordsFiltered=total_filtered,
        data=data
    )

@action("requisition_field/upload_expense_proxy", method=["POST"])
@action.uses(IMAGE_UPLOAD_API)
def upload_expense_proxy():
    upload_file = request.files.get("upload_file")
    if not upload_file:
        response.status = 400
        return {"error": "No file uploaded."}
    files = {"upload_file": (upload_file.filename, upload_file.file, upload_file.content_type)}
    r = requests.post(IMAGE_UPLOAD_API, files=files)
    response.status = r.status_code
    try:
        return json.dumps(r.json())
    except Exception:
        return {"error": "Failed to parse response (not valid JSON)", "status_code": r.status_code, "raw_response": r.text}