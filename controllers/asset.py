import json
from py4web import action, request, response, URL
from py4web.core import redirect
from ..common import db, session, T, flash


@action('asset/index')
@action.uses("asset/index.html",session, flash, )
def asset_index():
    return locals()


