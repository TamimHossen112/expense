import json
from py4web import action, response, request
from ..common import db, session

@action("transfer/configs", method=["GET"])
@action.uses(db, session)
def transfer_configs():
    cid = "SKF"  # company id

    sql = """
        SELECT section, `order`, `key`, caption, value_type, value_list, default_value
        FROM tr_config
        WHERE cid = %s AND tr_type = 'Transfer'
        ORDER BY section, `order`
    """
    rows = db.executesql(sql, placeholders=(cid,), as_dict=True)

    fields = []
    for row in rows:
        value_list = None

        if row["value_type"] == "dropdown":
            if row["key"] == "asset_id":   # ✅ correct match
                # fetch asset IDs dynamically
                asset_rows = db.executesql(
                    "SELECT asset_id FROM asset WHERE cid = %s ORDER BY asset_id",
                    placeholders=(cid,),
                    as_dict=True
                )
                value_list = [r["asset_id"] for r in asset_rows]

            else:
                # fallback if value_list column is defined
                value_list = row["value_list"].split(",") if row["value_list"] else None

        fields.append({
            "section": row["section"],
            "order": row["order"],
            "key": row["key"],
            "caption": row["caption"],
            "value_type": row["value_type"],
            "value_list": value_list,
            "default_value": row["default_value"]
        })

    response.headers["Content-Type"] = "application/json"
    return json.dumps({"fields": fields})


# Page endpoint: renders HTML
@action("transfer/create", method=["GET"])
@action.uses("transfer/create.html", db, session)
def transfer_create():
    return locals()
