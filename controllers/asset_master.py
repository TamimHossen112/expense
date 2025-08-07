import json
from py4web import action, request, response, URL
from py4web.core import redirect
from ..common import db, session, T, flash


@action('asset_master/index')
@action.uses("asset_master/index.html",session, flash, )
def asset_master_index():
    return locals()


@action('asset_master/create')
@action.uses("asset_master/create.html",session, flash, )
def asset_master_create():
    return locals()


@action('asset_master/submit', method=['POST'])
@action.uses(db, session, flash)
def asset_master_submit():
    asset_type = request.forms.get('asset_type', '').strip()
    asset_brand = request.forms.get('asset_brand', '').strip()
    asset_model = request.forms.get('asset_model', '').strip()
    asset_desc = request.forms.get('asset_desc', '').strip()
    asset_status = request.forms.get('asset_status', '').strip()

    # Validation (basic example — customize as needed)
    if not asset_type or not asset_brand or not asset_model or not asset_status:
        flash.set("Asset Type, Brand, Model, Status are required.", 'warning')
        redirect(URL('asset_master/create'))

    try:
        db.asset_master.insert(
            asset_type=asset_type,
            asset_brand=asset_brand,
            asset_model=asset_model,
            asset_desc=asset_desc,
            asset_status = asset_status
        )
        flash.set("Asset successfully added.", 'success')
        redirect(URL('asset_master/index'))

    except Exception as e:
        flash.set(f"Error while submitting asset: {str(e)}", 'danger')
        redirect(URL('asset_master/create'))

@action('asset_master/get_data', method=['GET'])
@action.uses(db)
def get_asset_master_data():
    asset_type = request.query.get('asset_type', '').strip()
    asset_brand = request.query.get('asset_brand', '').strip()
    asset_status = request.query.get('asset_status', '').strip()

    where_clauses = ["1=1"]
    if asset_type:
        where_clauses.append("asset_type LIKE '%{}%'".format(asset_type.replace("'", "''")))
    if asset_brand:
        where_clauses.append("asset_brand LIKE '%{}%'".format(asset_brand.replace("'", "''")))
    if asset_status:
        where_clauses.append("asset_status LIKE '%{}%'".format(asset_status.replace("'", "''")))

    where_sql = " AND ".join(where_clauses)

    start = int(request.query.get('start') or 0)
    length = int(request.query.get('length') or 15)

    sort_col_index = request.query.get('order[0][column]')
    sort_col_name = request.query.get(f'columns[{sort_col_index}][data]') if sort_col_index else 'id'
    sort_dir = request.query.get('order[0][dir]', 'desc').lower()
    if sort_dir not in ['asc', 'desc']:
        sort_dir = 'desc'

    total_sql = f"SELECT COUNT(*) AS total FROM asset_master WHERE {where_sql}"
    total_rows = db.executesql(total_sql, as_dict=True)[0]['total']

    base_sql = f"""
        SELECT id, cid, asset_type, asset_brand, asset_model, asset_desc, asset_status
        FROM asset_master
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



@action('asset_master/edit')
@action.uses(db, session, T, 'asset_master/edit.html')
def asset_edit():
    record_id = request.query.get('id')
    if not record_id:
        redirect(URL('asset_master/index'))

    record = db.asset_master(record_id)
    if not record:
        redirect(URL('asset_master/index'))

    return dict(record=record)

# Update form submission
@action('asset_master/update', method=['POST'])
@action.uses(db, session, flash)
def asset_update():
    record_id = request.query.get('id')
    if not record_id:
        flash.set('Missing ID', 'danger')
        redirect(URL('asset_master/index'))

    form_data = request.forms

    db(db.asset_master.id == record_id).update(
        asset_type=form_data.get('asset_type'),
        asset_brand=form_data.get('asset_brand'),
        asset_model=form_data.get('asset_model'),
        asset_desc=form_data.get('asset_desc')
    )

    flash.set('Asset updated successfully.', 'success')
    redirect(URL('asset_master/index'))

@action('asset_master/delete', method=['GET', 'POST'])
@action.uses(db, session, flash)
def asset_delete():
    record_id = request.query.get('id')

    if not record_id:
        flash.set('Missing ID.', 'danger')
        redirect(URL('asset_master/index'))

    try:
        record = db.asset_master(record_id)
        if record:
            db(db.asset_master.id == record_id).delete()
            flash.set('Asset deleted successfully.', 'success')
        else:
            flash.set('Asset not found.', 'warning')
    except Exception as e:
        flash.set(f'Error while deleting asset: {str(e)}', 'danger')

    redirect(URL('asset_master/index'))

