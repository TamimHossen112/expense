import json
from py4web import action, request, response, URL
from py4web.core import redirect
from ..common import db, session, T, flash


@action('purchase/index')
@action.uses("purchase/index.html",session, flash)
def purchase_index():
    return locals()


@action('purchase/create')
@action.uses("purchase/create.html",db,session,flash)
def purchase_create():
    return locals()

