from py4web import action, request, abort, redirect, URL, response, Session
from py4web.utils.form import Form, FormStyleDefault
from yatl.helpers import A
from ..common import db, session, T, auth, flash
import json


@action("index")
@action.uses("index.html", session, flash, db)
def index():
    return dict(redirect(URL('dashboard', 'index')))


# Vendors
@action("default/get_vendors_filter")
@action.uses(db)
def get_vendors_filter():
    vendors = db(db.vendor.vendor_name != None).select(db.vendor.vendor_name, distinct=True).as_list()
    results = [{"id": a["vendor_name"], "text": a["vendor_name"]} for a in vendors if a["vendor_name"]]
    return dict(results=results)


@action("default/get_requisition_details_with_asset_details")
@action.uses(db)
def get_requisition_details_with_asset_details():
    rows = db(db.requisition).select(db.requisition.req_id, db.requisition.emp_id, db.requisition.asset_type)
    results = []

    for row in rows:
        asset_type = asset_brand = asset_model = ""
        if row.asset_type:
            parts = row.asset_type.split(" | ")
            # Safely assign parts if they exist
            asset_type = parts[0] if len(parts) > 0 else ""
            asset_brand = parts[1] if len(parts) > 1 else ""
            asset_model = parts[2] if len(parts) > 2 else ""

        results.append({
            "req_id": row.req_id,
            "emp_id": row.emp_id,
            "asset_type": asset_type,
            "asset_brand": asset_brand,
            "asset_model": asset_model
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


import requests
import json

# Employee details (static data)
@action("default/get_employee_details")
def get_employee_details():
    # employee_data = [
    #     {
    #         "employee_id": 1234,
    #         "employee_name" : "HelloKitty",
    #         "designation": "Sales Manager",
    #         "territory_code": "T-102",
    #         "head_office": "Dhaka",
    #         "joining_date": "2022-05-10"
    #     },
    #     {
    #         "employee_id": 1235,
    #         "employee_name" : "Supaman",
    #         "designation": "Marketing Executive",
    #         "territory_code": "T-103",
    #         "head_office": "Chittagong",
    #         "joining_date": "2021-08-15"
    #     },
    #     {
    #         "employee_id": 1236,
    #         "employee_name" : "Botman",
    #         "designation": "HR Officer",
    #         "territory_code": "T-104",
    #         "head_office": "Khulna",
    #         "joining_date": "2020-02-01"
    #     },
    #     {
    #         "employee_id": 1237,
    #         "employee_name" : "Onana",
    #         "designation": "Finance Analyst",
    #         "territory_code": "T-105",
    #         "head_office": "Sylhet",
    #         "joining_date": "2023-01-20"
    #     },
    #     {
    #         "employee_id": 1239,
    #         "employee_name" : "Valentina",
    #         "designation": "Project Coordinator",
    #         "territory_code": "T-107",
    #         "head_office": "Barishal",
    #         "joining_date": "2022-07-30"
    #     }
    # ]
    

    url = "https://uat.alpha.transcombd.com/mytranscom_UAT/test/get_employee_data_expense"

    payload = json.dumps({
    "cid": "SKF"
    })
    headers = {
    'Content-Type': 'application/json',
    'Cookie': 'session_id_mytranscom_uat=182.16.158.70-388e4b4b-3c3b-4adb-9358-4fbe0cda140d'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    response.headers['Content-Type'] = 'application/json'
    return json.loads(response.text)


















































