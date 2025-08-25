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
    tr_type_list = ["Allocation", "Transfer", "Ownership Transfer", "Maintenance","Incident"]
    value_type_list = ["integer", "string", "date", "dropdown"]

    return dict(tr_type_list=tr_type_list, value_type_list=value_type_list)




@action('transaction_config/submit', method=['POST'])
@action.uses(session, flash, db)
def transaction_config_submit():
    tr_type = (request.forms.get('tr_type') or '').strip()

    if not tr_type:
        flash.set("Transaction Type is required.", "danger")
        redirect(URL('transaction_config', 'create'))

    # Collect lists from POST (ensure always list)
    sections       = request.forms.get('section[]') or []
    orders         = request.forms.get('order[]') or []
    keys           = request.forms.get('key[]') or []
    captions       = request.forms.get('caption[]') or []
    values         = request.forms.get('value[]') or []
    value_types    = request.forms.get('value_type[]') or []
    source_apis    = request.forms.get('source_api[]') or []
    value_lists    = request.forms.get('value_list[]') or []
    default_values = request.forms.get('default_value[]') or []

    # If those come as strings, wrap into list
    if isinstance(sections, str): sections = [sections]
    if isinstance(orders, str): orders = [orders]
    if isinstance(keys, str): keys = [keys]
    if isinstance(captions, str): captions = [captions]
    if isinstance(values, str): values = [values]
    if isinstance(value_types, str): value_types = [value_types]
    if isinstance(source_apis, str): source_apis = [source_apis]
    if isinstance(value_lists, str): value_lists = [value_lists]
    if isinstance(default_values, str): default_values = [default_values]

    try:
        for i in range(len(sections)):
            # Skip empty rows
            if not (sections[i] or keys[i] or captions[i]):
                continue

            db.tr_config.insert(
                tr_type=tr_type,
                section=sections[i].strip() if sections[i] else None,
                order=int(orders[i]) if orders[i] else None,
                key=keys[i].strip() if keys[i] else None,
                caption=captions[i].strip() if captions[i] else None,
                value=values[i].strip() if values[i] else None,
                value_type=value_types[i].strip() if value_types[i] else None,
                source_api=source_apis[i].strip() if source_apis[i] else None,
                value_list=value_lists[i].strip() if value_lists[i] else None,
                default_value=default_values[i].strip() if default_values[i] else None
            )

        db.commit()
        flash.set("Transaction Config saved successfully.", "success")

    except Exception as e:
        db.rollback()
        flash.set(f"Error saving config: {str(e)}", "danger")

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
