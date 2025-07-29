from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash

@action("users/index")
@action.uses("users/index.html", flash,session,auth,T,db)
def index():
    sql = """
    SELECT * from users
    """
    users = db.executesql(sql, as_dict=True)

    msge = "Users"
    flash = session.get('flash_msg') 
    session['flash_msg']=''
    ########
    return locals()
