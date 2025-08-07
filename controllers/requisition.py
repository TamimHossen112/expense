import json
from py4web import action, request, redirect, URL
from py4web.core import redirect
from ..common import db, session, T, flash
# ✅ Import API constants
from ..common_fn import IMAGE_UPLOAD_API, IMAGE_DOWNLOAD_API


@action('requisition/index')
@action.uses("requisition/index.html", session, flash)
def requisition_index():
    return locals()


@action('requisition/create')
@action.uses('requisition/create.html', db, session, flash)
def requisition_create():
    # ✅ Pass APIs to template
    return dict(
        IMAGE_UPLOAD_API=IMAGE_UPLOAD_API,
        IMAGE_DOWNLOAD_API=IMAGE_DOWNLOAD_API
    )

@action('requisition/edit')
@action.uses('requisition/edit.html', db, session, flash)
def requisition_edit():
    req_id = request.query.get('id')

    if not req_id:
        return dict(error='Missing requisition ID.')

    # Get requisition row
    row = db(db.requisition.id == req_id).select(
        db.requisition.id,
        db.requisition.asset_type,
        db.requisition.emp_id,
        db.requisition.emp_name,
        db.requisition.designation,
        db.requisition.tr_code,
        db.requisition.head_office,
        db.requisition.joining_date,
        db.requisition.license_issue_date,
        db.requisition.license_expire_date,
        db.requisition.license_number,
        limitby=(0, 1)
    ).first()

    if not row:
        return dict(error='Requisition not found.')

    # Get uploaded file metadata
    doc_files = db(
        (db.doc_metadata.trans_type == 'requisition') &
        (db.doc_metadata.trans_id == row.id)
    ).select(
        db.doc_metadata.doc_type,
        db.doc_metadata.file_name,
        db.doc_metadata.file_path
    )

    # Convert to array of dicts for JS
    file_metadata = [
        dict(
            doc_type=f.doc_type,
            file_name=f.file_name,
            file_path=f.file_path
        ) for f in doc_files
    ]

    return dict(
        data=row.as_dict(),
        docs=file_metadata,
        docs_json=json.dumps(file_metadata),
        IMAGE_UPLOAD_API=IMAGE_UPLOAD_API,
        IMAGE_DOWNLOAD_API=IMAGE_DOWNLOAD_API
    )



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

    uploaded_files = []
    index = 0

    while True:
        doc_type = request.forms.get(f'uploaded_files[{index}][doc_type]')
        file_name = request.forms.get(f'uploaded_files[{index}][file_name]')
        file_path = request.forms.get(f'uploaded_files[{index}][file_path]')

        if not doc_type and not file_name and not file_path:
            break

        uploaded_files.append({
            'doc_type': doc_type,
            'file_name': file_name,
            'file_path': file_path
        })
        index += 1

    errors = []
    if not asset_type:
        errors.append("Asset Type is required.")
    if not emp_id:
        errors.append("Employee ID is required.")
    if not joining_date:
        errors.append("Joining Date is required.")
    if not license_issue_date:
        errors.append("Driving License Issue Date is required.")
    if not license_expire_date:
        errors.append("Driving License Expire Date is required.")

    if errors:
        flash.set(' | '.join(errors), 'warning')
        redirect(URL('requisition/create'))

    try:
        requisition_id = db.requisition.insert(
            asset_type=asset_type,
            emp_id=emp_id,
            emp_name=emp_name,
            designation=designation,
            tr_code=tr_code,
            head_office=head_office,
            joining_date=joining_date or None,
            license_issue_date=license_issue_date or None,
            license_expire_date=license_expire_date or None,
            license_number=license_number
        )

        for file_data_dict in uploaded_files:
            db.doc_metadata.insert(
                trans_type="requisition",
                trans_id=requisition_id,
                doc_type=file_data_dict.get('doc_type'),
                file_name=file_data_dict.get('file_name'),
                file_path=file_data_dict.get('file_path'),
                ref_emp_id=emp_id
            )

        db.commit()
        flash.set("Requisition and associated documents created successfully!", 'success')
        redirect(URL('requisition/index'))

    except Exception as e:
        db.rollback()
        import sys
        import traceback
        traceback.print_exc(file=sys.stdout)
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
    except Exception:
        flash.set("Invalid requisition ID.", 'danger')
        redirect(URL('requisition/index'))

    # Validate required fields
    emp_id = request.forms.get('emp_id')
    emp_name = request.forms.get('emp_name')
    designation = request.forms.get('designation')
    tr_code = request.forms.get('tr_code')
    head_office = request.forms.get('head_office')
    joining_date = request.forms.get('joining_date')
    license_number = request.forms.get('license_number')
    license_issue_date = request.forms.get('license_issue_date')
    license_expire_date = request.forms.get('license_expire_date')
    asset_type = request.forms.get('asset_type')

    if not emp_id or not asset_type or not joining_date or not license_issue_date or not license_expire_date:
        flash.set("Missing required fields.", 'danger')
        redirect(URL('requisition/index'))

    # Make sure the record exists
    record = db(db.requisition.id == req_id).select().first()
    if not record:
        flash.set("Requisition ID not found.", 'danger')
        redirect(URL('requisition/index'))

    # Update the requisition record
    db(db.requisition.id == req_id).update(
        emp_id=emp_id,
        emp_name=emp_name,
        designation=designation,
        tr_code=tr_code,
        head_office=head_office,
        joining_date=joining_date,
        license_number=license_number,
        license_issue_date=license_issue_date,
        license_expire_date=license_expire_date,
        asset_type=asset_type,
    )

    # Delete existing doc metadata rows for this requisition
    db((db.doc_metadata.trans_id == req_id) & (db.doc_metadata.trans_type == 'requisition')).delete()

    # Insert uploaded files metadata
    index = 0
    while True:
        doc_type = request.forms.get(f'uploaded_files[{index}][doc_type]')
        file_name = request.forms.get(f'uploaded_files[{index}][file_name]')
        file_path = request.forms.get(f'uploaded_files[{index}][file_path]')

        if not doc_type:
            break

        db.doc_metadata.insert(
            trans_id=req_id,
            trans_type='requisition',
            doc_type=doc_type,
            file_name=file_name,
            file_path=file_path,
            ref_emp_id=emp_id
        )
        index += 1

    flash.set("Requisition updated successfully.", "success")
    redirect(URL('requisition/index'))





@action('requisition/get_data', method=['GET'])
@action.uses(db)
def requisition_get_data():
    asset_type = request.query.get('asset_type', '').strip()
    emp_id = request.query.get('emp_id', '').strip()
    head_office = request.query.get('head_office', '').strip()

    where_clauses = ["1=1"]

    if asset_type:
        asset_type_norm = "|".join(part.strip() for part in asset_type.split("|"))
        where_clauses.append(f"asset_type = '{asset_type_norm}'")

    if emp_id and emp_id.isdigit():
        where_clauses.append(f"emp_id = {int(emp_id)}")

    if head_office:
        where_clauses.append(f"head_office LIKE '%{head_office}%'")

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
        FROM requisition
        WHERE {where_sql}
    """
    total_rows = db.executesql(total_sql, as_dict=True)[0]['total']

    base_sql = f"""
        SELECT id, cid, asset_type, emp_id, emp_name, designation,
               tr_code, head_office, joining_date, license_number
        FROM requisition
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


@action('requisition/delete', method=['GET', 'POST'])
@action.uses(db, session, flash)
def delete_requisition():
    req_id = request.query.get('id')

    if not req_id:
        flash.set('Missing requisition ID.', 'danger')
        redirect(URL('requisition/index'))

    try:
        # First, check if requisition exists
        record = db.requisition(req_id)
        if record:
            # Delete associated doc_metadata first
            db((db.doc_metadata.trans_type == 'requisition') & 
               (db.doc_metadata.trans_id == req_id)).delete()

            # Delete the requisition
            db(db.requisition.id == req_id).delete()

            flash.set('Requisition deleted successfully.', 'success')
        else:
            flash.set('Requisition not found.', 'warning')
    except Exception as e:
        flash.set(f'Error while deleting requisition: {str(e)}', 'danger')

    redirect(URL('requisition/index'))




