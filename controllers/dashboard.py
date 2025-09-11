from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from ..common_fn import check_role
# this is tanmoy checking

@action("dashboard/index")
@action.uses("dashboard/index.html", db, session, flash)
def index():
    if session.get('status')!='success':
        return dict(redirect(URL('login', 'index')))

    return locals()
