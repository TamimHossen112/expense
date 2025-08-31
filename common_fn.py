IMAGE_UPLOAD_API = "https://filestore.transcombd.com/upload_file_expense"
IMAGE_DOWNLOAD_API = "https://filestore.transcombd.com/uploadimage"


from .common import db

def get_tr_types():

    sql=f"""
    SELECT DISTINCT tr_type
    FROM tr_config
    ORDER BY tr_type asc
    """
    data = db.executesql(sql, as_dict=True)
    return data