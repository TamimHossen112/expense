import json
from py4web import action, request, redirect, URL
from ..common import db, session, T, flash
from ..common_fn import check_role
# -----------------------------
# Index Page
# -----------------------------
@action('transaction_config/index')
@action.uses("transaction_config/index.html", db, session, flash)
def transaction_config_index():
    task_id='transaction_config_view'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    return locals()


# -----------------------------
# Create Page
# -----------------------------
@action('transaction_config/create')
@action.uses("transaction_config/create.html", db, session, flash)
def transaction_config_create():
    task_id='transaction_config_create'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    # Example lists for dropdowns
    tr_type_list = ["Allocation", "Transfer", "Ownership Transfer", "Maintenance","Incident"]
    value_type_list = ["integer", "float", "string", "date", "dropdown","hidden"]
    tr_order_sl=db.executesql('SELECT MAX(tr_order_sl) AS max_order FROM tr_config',as_dict=True)[0]['max_order'] or 0
    tr_order_sl=tr_order_sl+1
    return dict(tr_type_list=tr_type_list, value_type_list=value_type_list, tr_order_sl=tr_order_sl)



# -----------------------------
# Create / Submit New Config
# -----------------------------

@action('transaction_config/submit', method=['POST'])
@action.uses(session, flash, db)
def transaction_config_submit():
    task_id='transaction_config_create'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    tr_type = (request.forms.get('tr_type') or '').strip()
    tr_order_sl = (request.forms.get('tr_order_sl') or '').strip()

    if not tr_type:
        flash.set("Transaction Type is required.", "danger")
        redirect(URL('transaction_config', 'create'))

    sections       = request.forms.get('section[]') or []
    orders         = request.forms.get('order[]') or []
    keys           = request.forms.get('key[]') or []
    captions       = request.forms.get('caption[]') or []
    values         = request.forms.get('value[]') or []
    value_types    = request.forms.get('value_type[]') or []
    source_apis    = request.forms.get('source_api[]') or []
    value_lists    = request.forms.get('value_list[]') or []
    default_values = request.forms.get('default_value[]') or []
    sls            = request.forms.get('sl[]') or []
    readonlys      = request.forms.get('readonly[]') or []
    dependent_fields = request.forms.get('dependent_fields[]') or []
    dependent_on = request.forms.get('dependent_on[]') or []


    wrap = lambda v: [v] if isinstance(v, str) else v
    sections, orders, keys, captions, values = map(wrap, [sections, orders, keys, captions, values])
    value_types, source_apis, value_lists, default_values = map(wrap, [value_types, source_apis, value_lists, default_values])
    sls, readonlys = map(wrap, [sls, readonlys,])

    try:
        for i in range(len(sections)):
            if not (sections[i] or keys[i] or captions[i]):
                continue

            db.tr_config.insert(
                tr_type=tr_type,
                tr_order_sl=int(tr_order_sl) if tr_order_sl else 0,
                section=sections[i].strip() if sections[i] else None,
                order=int(orders[i]) if orders[i] else None,
                key=keys[i].strip() if keys[i] else None,
                caption=captions[i].strip() if captions[i] else None,
                value=values[i].strip() if values[i] else None,
                value_type=value_types[i].strip() if value_types[i] else None,
                source_api=source_apis[i].strip() if source_apis[i] else None,
                value_list=value_lists[i].strip() if value_lists[i] else None,
                default_value=default_values[i].strip() if default_values[i] else None,
                sl=int(sls[i]) if i < len(sls) and sls[i] else None,
                readonly=readonlys[i].strip() if i < len(readonlys) and readonlys[i] else None,
                dependent_fields=dependent_fields[i].strip() if i < len(dependent_fields) and dependent_fields[i] else None,
                dependent_on=dependent_on[i].strip() if i < len(dependent_on) and dependent_on[i] else None
            )

        db.commit()
        flash.set("Transaction Config saved successfully.", "success")
    except Exception as e:
        db.rollback()
        flash.set(f"Error saving config: {str(e)}", "danger")

    redirect(URL('transaction_config', 'index'))


# -----------------------------
# Edit Page (GET)
# -----------------------------
@action('transaction_config/edit', method=['GET'])
@action.uses(db, 'transaction_config/edit.html',flash,session)
def transaction_config_edit():
    task_id='transaction_config_edit'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    q = request.query
    tr_type = q.get('id')

    if not tr_type:
        redirect(URL('transaction_config', 'index'))

    value_type_list = ["integer", "float", "string", "date", "dropdown","hidden"]

    rows = db.executesql(f"""
        SELECT id, tr_type,tr_order_sl, section, `order`, `key`, caption, value,
            value_type, source_api, value_list, default_value,
            sl, readonly, dependent_fields, dependent_fields_source_api,
            dependent_on
        FROM tr_config
        WHERE tr_type = '{tr_type}'
        ORDER BY sl ASC, `order` ASC
    """, as_dict=True)

    return dict(
        tr_type=tr_type,
        tr_order_sl=int(rows[0]['tr_order_sl']) if rows else 0,
        rows=rows,
        value_type_list=value_type_list
    )


@action('transaction_config/update', method=['POST'])
@action.uses(db, session, flash)
def transaction_config_update():
    task_id='transaction_config_edit'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    tr_type = request.forms.get('tr_type','').strip()
    tr_order_sl = request.forms.get('tr_order_sl','').strip()
    if not tr_type:
        flash.set("Transaction Type is required.", "danger")
        redirect(URL('transaction_config','index'))

    fields = ['section','order','key','caption','value','value_type','dependent_fields',
              'readonly','source_api','dependent_fields_source_api','value_list','default_value','sl','dependent_on']

    data = {}
    for f in fields:
        value = request.forms.get(f"{f}[]")
        if value is None:
            data[f] = []
        elif isinstance(value, list):
            data[f] = value
        else:
            data[f] = [value]  # wrap single value into a list

    # Delete old config
    db(db.tr_config.tr_type==tr_type).delete()

    for i in range(len(data['key'])):
        db.tr_config.insert(
            tr_type=tr_type,
            tr_order_sl=int(tr_order_sl) if tr_order_sl else 0,
            section=data['section'][i].strip() if i<len(data['section']) else '',
            order=int(data['order'][i]) if i<len(data['order']) and data['order'][i] else None,
            key=data['key'][i].strip() if i<len(data['key']) else '',
            caption=data['caption'][i].strip() if i<len(data['caption']) else '',
            value=data['value'][i].strip() if i<len(data['value']) else '',
            value_type=data['value_type'][i].strip() if i<len(data['value_type']) else '',
            dependent_fields=data['dependent_fields'][i].strip() if i<len(data['dependent_fields']) else '',
            readonly=data['readonly'][i].strip() if i<len(data['readonly']) else '',
            source_api=data['source_api'][i].strip() if i<len(data['source_api']) else '',
            dependent_fields_source_api=data['dependent_fields_source_api'][i].strip() if i<len(data['dependent_fields_source_api']) else '',
            value_list=data['value_list'][i].strip() if i<len(data['value_list']) else '',
            default_value=data['default_value'][i].strip() if i<len(data['default_value']) else '',
            sl=int(data['sl'][i]) if i<len(data['sl']) and data['sl'][i] else None,
            dependent_on=data['dependent_on'][i].strip() if i<len(data['dependent_on']) else None
        )

    db.commit()
    flash.set("Transaction Config updated successfully.","success")
    redirect(URL('transaction_config','index'))


@action('transaction_config/get_data', method=['GET'])
@action.uses(db,session,flash)
def transaction_config_get_data():
    task_id='transaction_config_view'
    access_permission=check_role(task_id)  
    if ((access_permission==False)):
        flash.set("Access is Denied !", 'warning')
        redirect (URL('dashboard','index'))
    q = request.query
    start, length = int(q.get('start', 0)), int(q.get('length', 15))
    sort_dir = q.get('order[0][dir]', 'desc').lower()
    sort_dir = sort_dir if sort_dir in ['asc', 'desc'] else 'desc'

    # Total distinct tr_type count
    total_rows = db.executesql('SELECT COUNT(DISTINCT tr_type) AS total FROM tr_config', as_dict=True)[0]['total']

    # Fetch distinct tr_type values
    base_sql = f'''
        SELECT DISTINCT tr_type,tr_order_sl
        FROM tr_config
        ORDER BY tr_type {sort_dir}
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


