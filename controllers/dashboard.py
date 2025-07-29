
from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash

#this is tanmoy checking

@action("dashboard/index")
@action.uses("dashboard/index.html",session,flash,db)
def index():

    session['user_id'] = '101'
    
    return  locals()