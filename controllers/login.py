from py4web import action, request, abort, redirect, URL, Session, Cache, DAL, Field
from py4web.utils.form import Form, FormStyleBulma
from ..common import db, session, T, auth,flash
import hashlib

# Define session, cache, and database (this should be configured as per your setup)

def encrypt_password(password):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(password.encode('utf-8'))
    hashed_password = sha256_hash.hexdigest()
    return hashed_password

@action('login/index', method=['GET', 'POST'])
@action.uses("login/index.html", session,auth,T,db,flash)
def index():   
    if request.forms:
        email = str(request.forms.get('email')).strip()
        password = encrypt_password(str(request.forms.get('password')).strip())

        if not email:
            flash.set('Invalid Email!', 'warning')
            redirect(URL('login', 'index'))
        else:
            sqlQuery = """
            SELECT * from users where email ='{email}' and password='{password}' and active=1 limit 1;
            """.format(email=email,password=password)           
            employeeRecords = db.executesql(sqlQuery, as_dict=True)
            
            if not employeeRecords:
                flash.set('Wrong username or password!', 'warning')
                redirect(URL('login', 'index'))            
            elif employeeRecords[0]['active'] == 0:
                flash.set('Your account is currently inactive!', 'warning')
                redirect(URL('login', 'index'))
            else:             
                
                session['status'] = 'success'
                session['errors'] = ''

                for record in employeeRecords:
                    session['cid'] = str(record['cid'])
                    session['id'] = str(record['id'])
                    session['username'] = str(record['username'])
                    session['email'] = str(record['email'])
                
                redirect(URL('dashboard', 'index'))
    else:
        session['status'] = ''
    
    return locals()

@action('logout')
@action.uses("login/index.html", session,db,flash)   
def logout():
    session.clear()  # Clears the session data
    redirect(URL('index'))  # Redirect to the homepage or login page

