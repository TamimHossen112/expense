import json
from py4web import action, request, response, URL
from py4web.core import redirect
from ..common import db, session, T, flash


@action('requisition/index')
@action.uses("requisition/index.html",session, flash, )
def requisition_index():
    return locals()


