import json
from py4web import action, request, redirect, URL, response
from ..common import db, session, T, flash
from ..common_fn import IMAGE_UPLOAD_API, IMAGE_DOWNLOAD_API
import datetime

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


def fetch_uploaded_files(trans_type, trans_id):
    files = db(
        (db.doc_metadata.trans_type == trans_type) & 
        (db.doc_metadata.trans_id == trans_id)
    ).select(db.doc_metadata.doc_type, db.doc_metadata.file_name, db.doc_metadata.file_path)
    return [dict(doc_type=f.doc_type, file_name=f.file_name, file_path=f.file_path) for f in files]


# -----------------------------
# Views
# -----------------------------
@action('requisition/index')
@action.uses("requisition/index.html", session, flash)
def requisition_index():
    return locals()


@action('requisition/create')
@action.uses('requisition/create.html', db, session, flash)
def requisition_create():
    return dict(
        IMAGE_UPLOAD_API=IMAGE_UPLOAD_API,
        IMAGE_DOWNLOAD_API=IMAGE_DOWNLOAD_API,
        doc_type_combos=get_combo_values("requisition"),
        requisition_status_combos=get_combo_values("requisition_status"),
        asset_types=get_asset_types()
    )


@action('requisition/edit')
@action.uses('requisition/edit.html', db, session, flash)
def requisition_edit():
    req_id = request.query.get('id')
    if not req_id:
        return dict(error='Missing requisition ID.')

    row = db(db.requisition.id == req_id).select().first()
    if not row:
        return dict(error='Requisition not found.')

    file_metadata = fetch_uploaded_files('requisition', row.id)
    combo_results = get_combo_values("requisition")
    asset_type_list = [r['text'] for r in get_asset_types()]

    return dict(
        data=row.as_dict(),
        docs=file_metadata,
        docs_json=json.dumps(file_metadata),
        IMAGE_UPLOAD_API=IMAGE_UPLOAD_API,
        IMAGE_DOWNLOAD_API=IMAGE_DOWNLOAD_API,
        requisition_status_combos=get_combo_values("requisition_status"),
        selected_requisition_status = row.req_status,
        doc_type_combos=combo_results,
        asset_type_list=asset_type_list,
        selected_asset_type=row.asset_type
    )


# -----------------------------
# Submit / Update
# -----------------------------
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


@action('requisition/submit', method=['POST'])
@action.uses(db, session, flash)
def requisition_submit():
    asset_type = request.forms.get('asset_type')
    emp_id = request.forms.get('emp_id')
    emp_name = request.forms.get('emp_name')
    designation = request.forms.get('designation')
    tr_code = request.forms.get('tr_code')
    head_office = request.forms.get('head_office')
    joining_date = request.forms.get('joining_date')
    license_issue_date = request.forms.get('license_issue_date')
    license_expire_date = request.forms.get('license_expire_date')
    license_number = request.forms.get('license_number')
    requisition_status = request.forms.get('requisition_status')  # New field

    uploaded_files = parse_uploaded_files()

    # Validation
    required_fields = {
        "Asset Type": asset_type,
        "Employee ID": emp_id,
        "Joining Date": joining_date,
        "Driving License Issue Date": license_issue_date,
        "Driving License Expire Date": license_expire_date,
        "Driving License Number": license_number,
        "Requisition Status": requisition_status  # validate new field
    }
    missing_fields = [name for name, val in required_fields.items() if not val]
    if missing_fields:
        flash.set("The following fields are required: " + ", ".join(missing_fields), 'warning')
        redirect(URL('requisition/create'))

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
            req_status=requisition_status  # store in DB
        )

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
        flash.set("Requisition and associated documents created successfully!", 'success')
        redirect(URL('requisition/index'))

    except Exception as e:
        db.rollback()
        flash.set(f"An unexpected error occurred: {str(e)}", 'danger')
        redirect(URL('requisition/create'))


@action('requisition/update', method=["POST"])
@action.uses(db, session, flash)
def requisition_update():
    req_id = request.query.get('id') or request.forms.get('id')
    if not req_id:
        flash.set("Missing requisition ID.", 'danger')
        redirect(URL('requisition/index'))

    try:
        req_id = int(req_id)
    except:
        flash.set("Invalid requisition ID.", 'danger')
        redirect(URL('requisition/index'))

    requisition_status = request.forms.get('requisition_status')  # New field

    # Validate required fields
    required_fields = {
        "Employee ID": request.forms.get('emp_id'),
        "Asset Type": request.forms.get('asset_type'),
        "Joining Date": request.forms.get('joining_date'),
        "License Issue Date": request.forms.get('license_issue_date'),
        "License Expire Date": request.forms.get('license_expire_date'),
        "Driving License Number": request.forms.get('license_number'),
        "Requisition Status": requisition_status  # validate new field
    }
    missing_fields = [name for name, val in required_fields.items() if not val]
    if missing_fields:
        flash.set("The following fields are required: " + ", ".join(missing_fields), 'warning')
        redirect(URL('requisition/index'))

    record = db(db.requisition.id == req_id).select().first()
    if not record:
        flash.set("Requisition ID not found.", 'danger')
        redirect(URL('requisition/index'))

    # Update requisition
    db(db.requisition.id == req_id).update(
        emp_id=request.forms.get('emp_id'),
        emp_name=request.forms.get('emp_name'),
        designation=request.forms.get('designation'),
        tr_code=request.forms.get('tr_code'),
        head_office=request.forms.get('head_office'),
        joining_date=request.forms.get('joining_date'),
        license_number=request.forms.get('license_number'),
        license_issue_date=request.forms.get('license_issue_date'),
        license_expire_date=request.forms.get('license_expire_date'),
        asset_type=request.forms.get('asset_type'),
        req_status=requisition_status  # update new field
    )

    # Replace uploaded files
    db((db.doc_metadata.trans_type == 'requisition') & (db.doc_metadata.trans_id == req_id)).delete()
    for f in parse_uploaded_files():
        db.doc_metadata.insert(
            trans_type='requisition',
            trans_id=req_id,
            doc_type=f.get('doc_type'),
            file_name=f.get('file_name'),
            file_path=f.get('file_path'),
            ref_emp_id=request.forms.get('emp_id')
        )

    flash.set("Requisition updated successfully.", "success")
    redirect(URL('requisition/index'))




# -----------------------------
# Fetch / Delete
# -----------------------------
@action('requisition/get_data', method=['GET'])
@action.uses(db)
def requisition_get_data():
    q = request.query
    start, length = int(q.get('start', 0)), int(q.get('length', 15))
    sort_col_index = q.get('order[0][column]')
    sort_dir = q.get('order[0][dir]', 'desc').lower()
    sort_dir = sort_dir if sort_dir in ['asc', 'desc'] else 'desc'
    sort_col = 'id'

    if sort_col_index is not None:
        sort_col_index = int(sort_col_index)
        sort_col = q.get(f'columns[{sort_col_index}][data]', 'id')

    filters = []
    if q.get('req_status'):
        filters.append(f"req_status='{q['req_status'].strip()}'")
    if q.get('asset_type'):
        filters.append(f"asset_type='{q['asset_type'].strip()}'")
    if q.get('emp_id') and q['emp_id'].isdigit():
        filters.append(f"emp_id={int(q['emp_id'].strip())}")
    if q.get('head_office'):
        filters.append(f"head_office LIKE '%{q['head_office'].strip()}%'")

    where_sql = " AND ".join(filters) or "1=1"

    total_rows = db.executesql(f"SELECT COUNT(*) AS total FROM requisition WHERE {where_sql}", as_dict=True)[0]['total']
    base_sql = f"""
        SELECT id, req_id, asset_type, emp_id, emp_name, designation,
               tr_code, head_office, joining_date, license_number,
               req_status
        FROM requisition
        WHERE {where_sql}
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


@action('requisition/delete', method=['GET', 'POST'])
@action.uses(db, session, flash)
def delete_requisition():
    req_id = request.query.get('id')
    if not req_id:
        flash.set('Missing requisition ID.', 'danger')
        redirect(URL('requisition/index'))

    try:
        record = db(db.requisition.id == req_id).select().first()
        if record:
            db((db.doc_metadata.trans_type == 'requisition') & (db.doc_metadata.trans_id == req_id)).delete()
            db(db.requisition.id == req_id).delete()
            flash.set('Requisition deleted successfully.', 'success')
        else:
            flash.set('Requisition not found.', 'warning')
    except Exception as e:
        flash.set(f'Error while deleting requisition: {str(e)}', 'danger')

    redirect(URL('requisition/index'))

import requests
@action("requisition/upload_expense_proxy", method=["POST"])
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