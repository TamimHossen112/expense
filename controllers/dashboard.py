import json
from py4web import action, request, response, URL
from py4web.core import redirect
from ..common import db, session, T, flash
from ..common_fn import check_role
# this is tanmoy checking

@action("dashboard/index")
@action.uses("dashboard/index.html", db, session, flash)
def index():
    if session.get('status')!='success':
        return dict(redirect(URL('login', 'index')))

    return locals()
