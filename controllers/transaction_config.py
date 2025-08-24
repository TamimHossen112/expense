import json
from py4web import action, request, redirect, URL
from ..common import db, session, T, flash

# -----------------------------
# Index Page
# -----------------------------
@action('transaction_config/index')
@action.uses("transaction_config/index.html", session, flash)
def transaction_config_index():
    return locals()


# -----------------------------
# Create Page
# -----------------------------
@action('transaction_config/create')
@action.uses("transaction_config/create.html", session, flash)
def transaction_config_create():
    # Example lists for dropdowns
    tr_type_list = ["Purchase", "Sale", "Adjustment"]
    value_type_list = ["String", "Number", "Date", "Boolean"]

    return dict(tr_type_list=tr_type_list, value_type_list=value_type_list)


# -----------------------------
# Submit / Insert
# -----------------------------
@action('transaction_config/submit', method=['POST'])
@action.uses(session, flash, db)
def transaction_config_submit():
    # Get form values
    tr_type = request.forms.get('tr_type', '').strip()
    sl = request.forms.get('sl') or None
    section = request.forms.get('section', '').strip()
    order = request.forms.get('order') or None
    key = request.forms.get('key', '').strip()
    caption = request.forms.get('caption', '').strip()
    value = request.forms.get('value', '').strip()
    value_type = request.forms.get('value_type', '').strip()
    source_api = request.forms.get('source_api', '').strip()
    value_list = request.forms.get('value_list', '').strip()
    default_value = request.forms.get('default_value', '').strip()

    # Validation: Transaction Type is required
    if not tr_type:
        flash.set("Transaction Type is required.", "danger")
        redirect(URL('transaction_config', 'create'))

    # Insert into database
    db.tr_config.insert(
        tr_type=tr_type,
        sl=sl,
        section=section,
        order=order,
        key=key,
        caption=caption,
        value=value,
        value_type=value_type,
        source_api=source_api,
        value_list=value_list,
        default_value=default_value
    )

    flash.set("Transaction Config saved successfully.", "success")
    redirect(URL('transaction_config', 'index'))


# -----------------------------
# Edit Page
# -----------------------------
@action('transaction_config/edit')
@action.uses('transaction_config/edit.html', db, session, flash)
def transaction_config_edit():
    row_id = request.query.get('id')
    if not row_id:
        return dict(error='Missing transaction config ID.')

    row = db(db.tr_config.id == row_id).select().first()
    if not row:
        return dict(error='Transaction Config not found.')

    # Example dropdown lists
    tr_type_list = ["Purchase", "Sale", "Adjustment"]
    value_type_list = ["String", "Number", "Date", "Boolean"]

    return dict(
        data=row.as_dict(),
        tr_type_list=tr_type_list,
        selected_tr_type=row.tr_type,
        value_type_list=value_type_list,
        selected_value_type=row.value_type
    )


# -----------------------------
# Update / Save Edit
# -----------------------------
@action('transaction_config/update', method=['POST'])
@action.uses(db, session, flash)
def transaction_config_update():
    row_id = request.forms.get('id')
    if not row_id:
        flash.set("Missing transaction config ID.", "danger")
        redirect(URL('transaction_config', 'index'))

    row = db(db.tr_config.id == row_id).select().first()
    if not row:
        flash.set("Transaction Config not found.", "danger")
        redirect(URL('transaction_config', 'index'))

    # Get form values
    tr_type = request.forms.get('tr_type', '').strip()
    sl = request.forms.get('sl') or None
    section = request.forms.get('section', '').strip()
    order = request.forms.get('order') or None
    key = request.forms.get('key', '').strip()
    caption = request.forms.get('caption', '').strip()
    value = request.forms.get('value', '').strip()
    value_type = request.forms.get('value_type', '').strip()
    source_api = request.forms.get('source_api', '').strip()
    value_list = request.forms.get('value_list', '').strip()
    default_value = request.forms.get('default_value', '').strip()

    if not tr_type:
        flash.set("Transaction Type is required.", "danger")
        redirect(URL('transaction_config', 'edit', vars={'id': row_id}))

    # Update the row
    row.update_record(
        tr_type=tr_type,
        sl=sl,
        section=section,
        order=order,
        key=key,
        caption=caption,
        value=value,
        value_type=value_type,
        source_api=source_api,
        value_list=value_list,
        default_value=default_value
    )

    flash.set("Transaction Config updated successfully.", "success")
    redirect(URL('transaction_config', 'index'))


# -----------------------------
# Get Data for Datatable
# -----------------------------
@action('transaction_config/get_data', method=['GET'])
@action.uses(db)
def transaction_config_get_data():
    q = request.query
    start, length = int(q.get('start', 0)), int(q.get('length', 15))
    sort_col_index = q.get('order[0][column]')
    sort_dir = q.get('order[0][dir]', 'desc').lower()
    sort_dir = sort_dir if sort_dir in ['asc', 'desc'] else 'desc'
    sort_col = 'id'  # default

    # Determine sort column safely
    if sort_col_index is not None:
        sort_col_index = int(sort_col_index)
        sort_col = q.get(f'columns[{sort_col_index}][data]', '') or 'id'
        if sort_col.lower() in ['order', 'key']:
            sort_col = f"`{sort_col}`"

    # Total rows
    total_rows = db.executesql('SELECT COUNT(*) AS total FROM tr_config', as_dict=True)[0]['total']

    # Fetch data
    base_sql = f'''
        SELECT id, tr_type, sl, section, `order`, `key`, caption, value,
               value_type, source_api, value_list, default_value
        FROM tr_config
        ORDER BY {sort_col} {sort_dir}
    '''
    if length != -1:
        base_sql += f' LIMIT {length} OFFSET {start}'

    data = db.executesql(base_sql, as_dict=True)

    return dict(
        data=data,
        recordsTotal=total_rows,
        recordsFiltered=total_rows,
        draw=int(q.get('draw', 1))
    )
