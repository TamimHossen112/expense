IMAGE_UPLOAD_API = "https://filestore.transcombd.com/upload_file_expense"
IMAGE_DOWNLOAD_API = "https://filestore.transcombd.com/uploadimage"
LOGIN_URL = "https://uat.alpha.transcombd.com/ams/login/api_login"
API_URL ="https://uat.alpha.transcombd.com/mytranscom_UAT"

from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash

def get_tr_types():

    sql=f"""
    SELECT DISTINCT tr_type
    FROM tr_config
    ORDER BY tr_order_sl asc
    """
    data = db.executesql(sql, as_dict=True)
    return data


# check for role access
def check_role(task_id):
    t_id=task_id    
    is_valid_role=False    
    task_listStr=session.get('task_list',[])
    if session.get('status')=='success' and task_listStr:
        for i in range(len(task_listStr)):
            taskid=task_listStr[i]
            if taskid==t_id:
                is_valid_role=True
                break
            else:
                continue    
        return is_valid_role
    else:
        return False
    
    
# EMP_CACHE = {
#     "loaded": False,
#     "timestamp": 0,
#     "data": []
# }

