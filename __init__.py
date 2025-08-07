# check compatibility
import py4web

assert py4web.check_compatible("0.1.20190709.1")

# by importing db you expose it to the _dashboard/dbadmin
from .models import db

# by importing controllers you expose the actions defined in it
from .controllers import asset_master, login,default,dashboard,page_setup,unsold_reason,district,employees,order_entry,vendor,purchase,requisition,asset,transaction

# optional parameters
__version__ = "0.0.0"
__author__ = "you <you@example.com>"
__license__ = "anything you want"

# from threading import Timer

# def keep_db_alive():
#     try:
#         db.executesql("SELECT 1")
#     except:
#         db._adapter.close()  # close dead connection
#     Timer(300, keep_db_alive).start()  # ping every 5 minutes

# keep_db_alive()
