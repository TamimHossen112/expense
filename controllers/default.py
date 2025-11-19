from datetime import date, datetime
from py4web import action, request, abort, redirect, URL, response, Session
from py4web.utils.form import Form, FormStyleDefault
from yatl.helpers import A
from ..common import db, session, T, auth, flash
from ..common_fn import IMAGE_UPLOAD_API, IMAGE_DOWNLOAD_API, LOGIN_URL, API_URL,EMP_CACHE
import json


@action("index")
@action.uses("index.html", session, flash, db)
def index():
    if session.get('status')!='success':
        return dict(redirect(URL('login', 'index')))
    return dict(redirect(URL('dashboard', 'index')))


@action("default/get_vendors_filter")
@action.uses(db)
def get_vendors_filter():
    vendors = db(db.vendor.vendor_name != None).select(db.vendor.vendor_name, distinct=True).as_list()
    results = [{"id": a["vendor_name"], "text": a["vendor_name"]} for a in vendors if a["vendor_name"]]
    return dict(results=results)


@action("default/get_requisition_details_with_asset_details")
@action.uses(db)
def get_requisition_details_with_asset_details():
    sql = """
        SELECT r.id,
               r.req_id, 
               r.asset_type, 
               r.quantity,
               COALESCE(SUM(p.quantity), 0) AS purchased_quantity
        FROM requisition r
        LEFT JOIN purchase_details p ON r.req_id = p.req_id
        WHERE LOWER(r.req_status) = 'approved'
        GROUP BY r.req_id
        ORDER BY id DESC
    """
    rows = db.executesql(sql, as_dict=True)

    results = []
    for row in rows:
        asset_type = ""
        if row['asset_type']:
            parts = row['asset_type'].split(" | ")
            asset_type = parts[0] if len(parts) > 0 else ""

        max_quantity = row['quantity'] - row['purchased_quantity']

        # if max_quantity <= 0:
        #     continue

        results.append({
            "req_id": row['req_id'],
            "asset_type": asset_type,
            "max_quantity": max_quantity
        })

    return dict(results=results)



@action("default/get_asset_brands")
@action.uses(db)
def get_asset_brands():
    rows = db(db.asset_master).select(db.asset_master.asset_brand, distinct=True)
    results = [row.asset_brand for row in rows if row.asset_brand]
    return dict(results=results)

@action("default/get_asset_types")
@action.uses(db)
def get_asset_types():
    rows = db(db.asset_master).select(db.asset_master.asset_type, distinct=True)
    results = [row.asset_type for row in rows if row.asset_type]
    return dict(results=results)

@action("default/get_asset_models")
@action.uses(db)
def get_asset_models():
    rows = db(db.asset_master).select(db.asset_master.asset_model, distinct=True)
    results = [row.asset_model for row in rows if row.asset_model]
    return dict(results=results)



@action("default/get_vendors_dropdown")
@action.uses(db)
def get_vendors_filter():
    vendors = db(db.vendor.vendor_name != None).select(
        db.vendor.id, db.vendor.vendor_name, distinct=True).as_list()

    results = [
        {"id": vendor["id"], "text": vendor["vendor_name"]}
        for vendor in vendors if vendor["vendor_name"]
    ]
    return dict(results=results)


@action("default/get_asset_master_status")
@action.uses(db)
def get_asset_master_status():
    status = db(db.asset_master.asset_status != None).select(db.asset_master.asset_status, distinct=True).as_list()
    results = [{"id": row["asset_status"], "text": row["asset_status"]} for row in status if row["asset_status"]]
    return dict(results=results)


@action("default/get_asset_master_types")
@action.uses(db)
def get_asset_master_types():
    types = db(db.asset_master.asset_type != None).select(db.asset_master.asset_type, distinct=True).as_list()
    results = [{"id": row["asset_type"], "text": row["asset_type"]} for row in types if row["asset_type"]]
    return dict(results=results)


@action("default/get_asset_type_brand_models")
@action.uses(db)
def get_asset_type_brand_models():
    rows = db().select(
        db.asset_master.asset_type,
        db.asset_master.asset_brand,
        db.asset_master.asset_model,
        distinct=True
    )

    results = []
    for row in rows:
        results.append({
            "asset_type": row.asset_type,
            "asset_brand": row.asset_brand,
            "asset_model": row.asset_model
        })

    return dict(results=results)



@action("default/get_asset_type_brand_models_test_combined")
@action.uses(db)
def get_asset_type_brand_models():
    rows = db().select(
        db.asset_master.asset_type,
        db.asset_master.asset_brand,
        db.asset_master.asset_model,
        distinct=True
    )

    combined_list = [f"{row.asset_type} | {row.asset_brand} | {row.asset_model}" for row in rows]

    return combined_list


# Dropdown: asset brands
@action("default/get_asset_master_brands")
@action.uses(db)
def get_asset_master_brands():
    brands = db(db.asset_master.asset_brand != None).select(db.asset_master.asset_brand, distinct=True).as_list()
    results = [{"id": row["asset_brand"], "text": row["asset_brand"]} for row in brands if row["asset_brand"]]
    return dict(results=results)



@action("default/get_distinct_asset_ids")
@action.uses(db)
def get_distinct_asset_ids():
    rows = db(db.asset.asset_id != None).select(db.asset.asset_id, distinct=True).as_list()
    results = [{"id": row["asset_id"], "text": row["asset_id"]} for row in rows if row["asset_id"]]
    return dict(results=results)


@action("default/get_asset_master_colors")
@action.uses(db)
def get_asset_master_colors():
    colors = db(db.asset_master.asset_color != None).select(db.asset_master.asset_color, distinct=True).as_list()
    results = [{"id": row["asset_color"], "text": row["asset_color"]} for row in colors if row["asset_color"]]
    return dict(results=results)




def safe_date(val):
    """Format date into YYYY-MM-DD or return empty string."""
    if not val:
        return ""
    if isinstance(val, (date,)):
        return val.strftime("%Y-%m-%d")
    try:
        return str(val)
    except:
        return ""

# ---------------------------
# API Endpoint (Single Asset)
# ---------------------------
# @action("default/get_asset_detail")
# def get_asset_detail_api():

#     asset_id = request.query.get("asset_id")
#     if not asset_id:
#         return json.dumps({"error": "asset_id required"}, default=str)

#     details = get_transfer_asset_details([asset_id])
#     response.headers["Content-Type"] = "application/json"
#     return json.dumps(details.get(asset_id, {}), default=str)  





def get_transfer_asset_details(asset_id=None):
    """
    Fetch asset details from DB and enrich with employee info (via API).
    Returns a flat dict of asset details if single asset_id is provided.
    """
    if not asset_id:
        return {}

    # Convert to list to reuse SQL
    asset_ids = [asset_id]

    placeholders = ",".join(["%s"] * len(asset_ids))
    rows = db.executesql(
        f"""
        SELECT asset_id, asset_type, asset_model, asset_brand, asset_name, user_id, 
            first_issue_date,asset_color,reg_number, engine_number, chassis_number
        FROM asset
        WHERE asset_id IN ({placeholders})
        """,
        asset_ids,
        as_dict=True
    )

    if not rows:
        return {}

    row = rows[0]  # only one asset expected
    emp_id = row.get("user_id")

    asset_info = {
        "asset_type": row.get("asset_type") or "",
        "asset_name": row.get("asset_name") or "",
        "asset_model": row.get("asset_model") or "",
        "asset_brand": row.get("asset_brand") or "",
        "asset_color": row.get("asset_color") or "",
        "asset_eng_no": row.get("engine_number") or "",
        "asset_chassis_no": row.get("chassis_number") or "",
        "asset_reg_no": row.get("reg_number") or "",
        "first_issue_date": safe_date(row.get("first_issue_date")),
        "using_from": row.get("using_from") or "",
        "from_emp_id": "",
        "from_emp_tr_code": "",
        "from_desg": "",
        "from_emp_base_hq": ""
    }

    if emp_id:
        try:
            url = f"https://uat.beta.transcombd.com/expense/default/get_employee_details?employee_id={emp_id}"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                emp_data = resp.json()
                emp = emp_data[0] if isinstance(emp_data, list) else emp_data
                asset_info.update({
                    "from_emp_id": f"{emp.get('employee_id', '')} | {emp.get('employee_name', '')}",
                    "from_emp_tr_code": emp.get("territory_code", ""),
                    "from_desg": emp.get("designation", ""),
                    "from_emp_base_hq": emp.get("head_office", "")
                })
        except Exception as e:
            print(f"⚠️ Failed to fetch employee {emp_id}: {e}")

    return asset_info




@action("default/get_transaction_assets")
def get_transaction_assets():
    asset_id = request.query.get("id")

    if asset_id:
        details = get_transfer_asset_details(asset_id)
        response.headers["Content-Type"] = "application/json"
        return json.dumps(details, default=str)

    rows = db.executesql(
        "SELECT asset_id, asset_type, asset_brand, asset_model, asset_color FROM asset ORDER BY asset_id",
        as_dict=True
    )
    assets = [
        {
            "id": row['asset_id'],
            "text": f"{row['asset_id']} | {row['asset_type'] or ''} | {row['asset_brand'] or ''} | {row['asset_model'] or ''} | {row['asset_color'] or ''}"
        }
        for row in rows
    ]


    response.headers["Content-Type"] = "application/json"
    return json.dumps(assets, default=str)



@action("default/get_combo_values")
@action.uses(db)
def get_combo_values():
    key = request.query.get("key")

    if not key:
        return dict(results=[])

    row = db(db.combo_settings.key == key).select(db.combo_settings.value).first()

    if not row or not row.value:
        return dict(results=[])

    values = [item.strip() for item in row.value.split(",") if item.strip()]
    results = [{"id": val, "text": val} for val in values]

    return dict(results=results)

import time
import requests
import json

CACHE_EXPIRY = 600  # 10 minutes (600 sec)

@action.uses(API_URL)
def load_employee_cache():
    now = time.time()

    # refresh if not loaded OR expired
    if (not EMP_CACHE["loaded"]) or (now - EMP_CACHE["timestamp"] > CACHE_EXPIRY):

        url = f"{API_URL}/api_expense_employee_list/get_employee_data_expense"

        employee_id = request.query.get("employee_id")

        payload = json.dumps({
            "cid": "SKF",
            "emp_id": employee_id
        })

        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'session_id_mytranscom_uat=182.16.158.70-388e4b4b-3c3b-4adb-9358-4fbe0cda140d'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        EMP_CACHE["data"] = json.loads(response.text)
        EMP_CACHE["timestamp"] = now
        EMP_CACHE["loaded"] = True

    return EMP_CACHE["data"]


@action("default/get_employee_details")
@action.uses(API_URL)
def get_employee_details():
    data = load_employee_cache()
    return json.dumps(data)


# @action("default/get_employee_details")
# @action.uses(API_URL)
# def get_employee_details():
#     url = f"{API_URL}/api_expense_employee_list/get_employee_data_expense"

#     employee_id = request.query.get("employee_id")

#     payload = json.dumps({
#     "cid": "SKF",
#     "emp_id": employee_id
#     })
#     headers = {
#     'Content-Type': 'application/json',
#     'Cookie': 'session_id_mytranscom_uat=182.16.158.70-388e4b4b-3c3b-4adb-9358-4fbe0cda140d'
#     }

#     response = requests.request("GET", url, headers=headers, data=payload)

#     response.headers['Content-Type'] = 'application/json'
#     return json.loads(response.text)




@action("default/get_transaction_employee_details")
@action.uses(API_URL)
def get_transaction_employee_details():
    emp_id = request.query.get("id")
    cid = request.query.get("cid", "SKF") 

    try:
        url = f"{API_URL}/api_expense_employee_list/get_employee_data_expense"
        headers = {
            "Content-Type": "application/json",
            "Cookie": "session_id_mytranscom_uat=182.16.158.70-388e4b4b-3c3b-4adb-9358-4fbe0cda140d"
        }

        payload = {"cid": cid}
        if emp_id:
            # Single employee → pass emp_id to API
            payload["emp_id"] = emp_id

        resp = requests.get(url, headers=headers, data=json.dumps(payload), timeout=10)
        if resp.status_code != 200:
            raise Exception(f"Status {resp.status_code}")

        employees = resp.json()

        if emp_id:
            # Single employee requested → return mapped fields
            if not employees:
                return json.dumps({}, default=str)
            emp = employees[0] if isinstance(employees, list) else employees
            result = {
                "to_name": emp.get("employee_name", ""),
                "to_desg": emp.get("designation", ""),
                "to_mobile": emp.get("mobile", ""),
                "to_joining_date": safe_date(emp.get("joining_date")),
                "to_tr_code": emp.get("territory_code", ""),
                "to_base_hq": emp.get("head_office", ""),
            }
        else:
            # No emp_id → return all for Select2
            result = [
                {
                    "id": e.get("employee_id") or "",
                    "text": f"{e.get('employee_id','')} | {e.get('employee_name','')}"
                }
                for e in employees if e.get("employee_id")
            ]

        response.headers["Content-Type"] = "application/json"
        return json.dumps(result, default=str)

    except Exception as e:
        print(f"⚠️ Failed to fetch employee data: {e}")
        response.headers["Content-Type"] = "application/json"
        return json.dumps({}, default=str)





















































