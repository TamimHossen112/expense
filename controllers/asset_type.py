import json
from py4web import action, request, response, URL
from py4web.core import redirect
from ..common import db, session, T, flash


@action('asset_type/index')
@action.uses("asset_type/index.html",session, flash, )
def asset_type_index():
    return locals()


@action('asset_type/create')
@action.uses("asset_type/create.html", session, flash)
def asset_type_create():
    asset_types = [row.asset_type for row in db(db.asset_master).select(db.asset_master.asset_type, distinct=True)]
    asset_brands = [row.asset_brand for row in db(db.asset_master).select(db.asset_master.asset_brand, distinct=True)]
    asset_models = [row.asset_model for row in db(db.asset_master).select(db.asset_master.asset_model, distinct=True)]

    # Pass them to template
    return dict(
        asset_types=asset_types,
        asset_brands=asset_brands,
        asset_models=asset_models
    )



@action('asset_type/submit', method=['POST'])
@action.uses(db, session, flash)
def asset_type_submit():
    asset_type = (request.forms.get('asset_type') or '').strip()
    asset_brand = (request.forms.get('asset_brand') or '').strip()
    asset_model = (request.forms.get('asset_model') or '').strip()
    asset_desc = (request.forms.get('asset_desc') or '').strip()
    asset_status = request.forms.get('status')
    asset_status = 'active' if asset_status == 'active' else 'inactive'

    # Validation: must not be blank
    if not asset_type:
        flash.set("Asset Type is required.", 'warning')
        redirect(URL('asset_type/create'))
    if not asset_brand:
        flash.set("Asset Brand is required.", 'warning')
        redirect(URL('asset_type/create'))
    if not asset_model:
        flash.set("Asset Model is required.", 'warning')
        redirect(URL('asset_type/create'))

    try:
        # 🔎 Check if same type+brand+model already exists
        exists = db(
            (db.asset_master.asset_type == asset_type) &
            (db.asset_master.asset_brand == asset_brand) &
            (db.asset_master.asset_model == asset_model)
        ).select().first()

        if exists:
            flash.set("This Asset Type + Brand + Model already exists.", 'warning')
            redirect(URL('asset_type/create'))

        # Insert if not exists
        db.asset_master.insert(
            asset_type=asset_type.upper(),
            asset_brand=asset_brand,
            asset_model=asset_model,
            asset_desc=asset_desc,
            status=asset_status
        )

        flash.set("Asset successfully added.", 'success')
        redirect(URL('asset_type/index'))

    except Exception as e:
        flash.set(f"Error while submitting asset: {str(e)}", 'danger')
        redirect(URL('asset_type/create'))



@action('asset_type/get_data', method=['GET'])
@action.uses(db)
def get_asset_type_data():
    asset_type = request.query.get('asset_type', '').strip()
    asset_brand = request.query.get('asset_brand', '').strip()


    where_clauses = ["1=1"]
    if asset_type:
        where_clauses.append("asset_type LIKE '%{}%'".format(asset_type.replace("'", "''")))
    if asset_brand:
        where_clauses.append("asset_brand LIKE '%{}%'".format(asset_brand.replace("'", "''")))

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
        SELECT id, status, asset_type, asset_brand, asset_model, asset_desc
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



@action('asset_type/edit')
@action.uses(db, session, T, 'asset_type/edit.html')
def asset_edit():
    record_id = request.query.get('id')
    if not record_id:
        redirect(URL('asset_type/index'))

    record = db.asset_master(record_id)
    if not record:
        redirect(URL('asset_type/index'))

    return dict(record=record)

# Update form submission
@action('asset_type/update', method=['POST'])
@action.uses(db, session, flash)
def asset_update():
    record_id = request.query.get('id')
    if not record_id:
        flash.set('Missing ID', 'danger')
        redirect(URL('asset_type/index'))

    form_data = request.forms

    # Get status from form (default to 'inactive' if not provided)
    asset_type_status = request.forms.get('status', 'inactive').strip()
    if asset_type_status not in ['active', 'inactive']:
        asset_type_status = 'inactive'

    db(db.asset_master.id == record_id).update(
        asset_type=form_data.get('asset_type'),
        asset_brand=form_data.get('asset_brand'),
        asset_model=form_data.get('asset_model'),
        asset_desc=form_data.get('asset_desc'),
        status=asset_type_status
    )

    flash.set('Asset updated successfully.', 'success')
    redirect(URL('asset_type/index'))

@action('asset_type/delete', method=['GET', 'POST'])
@action.uses(db, session, flash)
def asset_delete():
    record_id = request.query.get('id')

    if not record_id:
        flash.set('Missing ID.', 'danger')
        redirect(URL('asset_type/index'))

    try:
        record = db.asset_master(record_id)
        if record:
            db(db.asset_master.id == record_id).delete()
            flash.set('Asset deleted successfully.', 'success')
        else:
            flash.set('Asset not found.', 'warning')
    except Exception as e:
        flash.set(f'Error while deleting asset: {str(e)}', 'danger')

    redirect(URL('asset_type/index'))

