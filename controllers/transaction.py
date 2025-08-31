import json
import requests
from py4web import action, request, redirect, URL
from ..common import db, session, T, flash

from datetime import date  

@action('transaction/index')
@action.uses("transaction/index.html", session, flash)
def transaction_index():
    tr_type = request.query.get('type')
    return locals()


def fetch_from_api(endpoint, params=None):
    """Generic API fetcher for dropdown source_api."""
    base_url = "http://localhost:8010/expense/default/"
    url = f"{base_url}{endpoint}"
    try:
        resp = requests.get(url, params=params or {}, timeout=5)
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"⚠️ API {url} returned {resp.status_code}")
    except Exception as e:
        print(f"⚠️ Failed to fetch {url}: {e}")
    return []

@action("transaction/create")
@action.uses("transaction/create.html", session, flash)
def transaction_initiate():
    tr_type = request.query.get("type", "").strip()

    if not tr_type:
        return dict(fields=[], fields_json="[]")

    rows = db.executesql(
        f"""
        SELECT sl, section, `order`, `key`, caption, value_type, 
               value_list, source_api, default_value, readonly, 
               hidden, dependent_fields, dependent_fields_source_api
        FROM tr_config
        WHERE tr_type = '{tr_type}'
        ORDER BY sl, `order`
        """,
        as_dict=True
    )

    fields = []
    for row in rows:
        value_list = None
        if row["value_list"]:
            values = [v.strip() for v in row["value_list"].split(",") if v.strip()]
            if row.get("dependent_fields"):
                value_list = {v: {} for v in values}
            else:
                value_list = values

        fields.append({
            "sl": row["sl"] or "",
            "section": row["section"] or "",
            "order": row["order"] or "",
            "key": row["key"] or "",
            "caption": row["caption"] or "",
            "value_type": row["value_type"] or "",
            "value_list": value_list or "",
            "default_value": row["default_value"] or "",
            "source_api": row["source_api"] or "",
            "dependent_fields_source_api": row["dependent_fields_source_api"] or "",
            "readonly": row["readonly"] or "",
            "hidden": row["hidden"] or "",
            "dependent_fields": row["dependent_fields"] or "",
        })

    return dict(
        fields=fields,
        fields_json=json.dumps(fields, default=str)
    )


@action("transaction/submit", method=["POST"])
@action.uses(db, flash)
def transaction_submit():
    cid = "SKF"
    form = request.forms

    trans_type = request.query.get("type")
    asset_id, asset_type = form.get("asset_id"), form.get("asset_type")
    if not asset_id or not asset_type:
        flash.set("❌ Missing asset_id or asset_type")
        redirect(URL("transaction/index"))

    db.executesql(
        f"""
        INSERT INTO tr_head (cid, trans_type, asset_id, asset_type, status, tr_date)
        VALUES ('{cid}', '{trans_type}', '{asset_id}', '{asset_type}', 'pending', '{date.today()}')
        """
    )
    head_id = db.executesql("SELECT LAST_INSERT_ID() AS id", as_dict=True)[0]['id']

    for key in form.keys():
        if key not in ("asset_id", "asset_type"):
            db.executesql(
                f"""
                INSERT INTO tr_details (cid, tr_head_id, `key`, value)
                VALUES ('{cid}', {head_id}, '{key}', '{form.get(key)}')
                """
            )

    flash.set("Transfer submitted successfully!", "success")
    redirect(URL("transaction/index", vars=dict(type=trans_type)))




# # ------------------------------
# # Edit Page
# # ------------------------------
# @action('transfer/edit', method=['GET'])
# @action.uses("transfer/edit.html", db)
# def transfer_edit():
#     tr_head_id = request.query.get('id')
#     if not tr_head_id:
#         return dict(status="error", message="Missing transaction id")

#     head_rows = db.executesql(
#         f"SELECT * FROM tr_head WHERE id = {tr_head_id}",
#         as_dict=True
#     )
#     if not head_rows:
#         return dict(status="error", message="Transaction not found")
#     head_row = head_rows[0]

#     configs = db.executesql(
#         f"SELECT * FROM tr_config WHERE tr_type = '{head_row['trans_type']}' ORDER BY sl",
#         as_dict=True
#     )

#     details = db.executesql(
#         f"SELECT * FROM tr_details WHERE tr_head_id = {tr_head_id}",
#         as_dict=True
#     )
#     details_map = {d["key"]: d["value"] for d in details}

#     merged, asset_ids = [], []
#     for cfg in configs:
#         value_list = None
#         if cfg["value_type"] == "dropdown" and cfg["key"] == "asset_id":
#             assets = db.executesql(
#                 f"SELECT asset_id FROM asset WHERE cid = '{head_row['cid']}' ORDER BY asset_id",
#                 as_dict=True
#             )
#             asset_ids = [a["asset_id"] for a in assets]
#             value_list = asset_ids
#         elif cfg["value_type"] == "dropdown":
#             value_list = cfg["value_list"].split(",") if cfg["value_list"] else None

#         value = details_map.get(cfg["key"], head_row.get(cfg["key"], cfg["default_value"]))
#         merged.append(dict(
#             id=cfg["id"],
#             sl=cfg["sl"],
#             section=cfg["section"],
#             key=cfg["key"],
#             caption=cfg["caption"],
#             value=value,
#             readonly=cfg["readonly"],
#             hidden=cfg["hidden"],
#             value_type=cfg["value_type"],
#             value_list=value_list,
#             default_value=cfg["default_value"]
#         ))

#     return dict(
#         status="success",
#         head=head_row,
#         details=merged,
#         asset_details=json.dumps(get_transfer_asset_details(asset_ids)) if asset_ids else "{}",
#         # transfer_employees=get_mock_employees(),
#         asset_ids=asset_ids
#     )


# ------------------------------
# Update (POST)
# ------------------------------
# @action('transfer/update', method=['POST'])
# @action.uses(db, flash)
# def transfer_update():
#     tr_head_id = request.query.get('id')
#     if not tr_head_id:
#         flash.set("❌ Missing transfer id", "error")
#         redirect(URL('transfer/index'))

#     head_rows = db.executesql(f"SELECT * FROM tr_head WHERE id = {tr_head_id}", as_dict=True)
#     if not head_rows:
#         flash.set("❌ Transfer not found", "error")
#         redirect(URL('transfer/index'))
#     head_row = head_rows[0]

#     form = request.forms
#     cid, trans_type = head_row['cid'], head_row['trans_type']

#     # --- update tr_head
#     tr_date_val = form.get('tr_date') or head_row['tr_date']
#     try:
#         tr_date_val = datetime.datetime.strptime(tr_date_val, "%Y-%m-%d").date()
#     except Exception:
#         tr_date_val = head_row['tr_date']

#     db.executesql(
#         f"""
#         UPDATE tr_head
#         SET asset_id = '{form.get('asset_id') or head_row['asset_id']}',
#             asset_type = '{form.get('asset_type') or head_row['asset_type']}',
#             tr_date = '{tr_date_val}'
#         WHERE id = {tr_head_id}
#         """
#     )

#     # --- configs
#     configs = db.executesql(
#         f"SELECT * FROM tr_config WHERE tr_type = '{trans_type}' ORDER BY sl",
#         as_dict=True
#     )

#     existing = db.executesql(
#         f"SELECT * FROM tr_details WHERE tr_head_id = {tr_head_id}",
#         as_dict=True
#     )
#     details_map = {r["key"]: r for r in existing}

#     for cfg in configs:
#         if cfg["key"] in {"asset_id", "asset_type"} or cfg["key"] not in form:
#             continue
#         value = form.get(cfg["key"])
#         if cfg["value_type"] == "date" and value:
#             try:
#                 value = datetime.datetime.strptime(value, "%Y-%m-%d").date().isoformat()
#             except Exception:
#                 pass

#         if cfg["key"] in details_map:
#             db.executesql(
#                 f"""
#                 UPDATE tr_details
#                 SET value = '{value}'
#                 WHERE tr_head_id = {tr_head_id} AND `key` = '{cfg["key"]}'
#                 """
#             )
#         else:
#             db.executesql(
#                 f"""
#                 INSERT INTO tr_details (cid, tr_head_id, `key`, value)
#                 VALUES ('{cid}', {tr_head_id}, '{cfg["key"]}', '{value}')
#                 """
#             )

#     flash.set("Transfer updated successfully!", "success")
#     redirect(URL("transfer/index"))


# ------------------------------
# Get Distinct Transactions for Datatable
# ------------------------------
@action('transfer/get_data', method=['GET'])
@action.uses(db)
def transfer_get_data():
    q = request.query
    type = q.get('type')
    start, length = int(q.get('start', 0)), int(q.get('length', 15))
    sort_dir = q.get('order[0][dir]', 'desc').lower()
    sort_dir = sort_dir if sort_dir in ['asc', 'desc'] else 'desc'

    type_filter = f"WHERE trans_type = '{type}'" if type else ""
    total_rows = db.executesql(f"""SELECT COUNT(*) AS total FROM tr_head {type_filter}""", as_dict=True)[0]['total']

    sql = f"""
        SELECT id, asset_id, asset_type, trans_type, status, tr_date
        FROM tr_head
        {type_filter}
        ORDER BY tr_date {sort_dir}
    """
    if length != -1:
        sql += f" LIMIT {length} OFFSET {start}"

    data = db.executesql(sql, as_dict=True)

    return dict(
        data=data,
        recordsTotal=total_rows,
        recordsFiltered=total_rows,
        draw=int(q.get('draw', 1))
    )
