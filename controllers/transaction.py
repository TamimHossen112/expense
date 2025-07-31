import json
from py4web import action, request, response, URL
from py4web.core import redirect
from ..common import db, session, T, flash


@action('transaction/index')
@action.uses("transaction/index.html",session, flash, )
def transaction_index():
    return locals()


