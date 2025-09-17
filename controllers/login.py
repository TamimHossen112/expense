from py4web import action, request, abort, redirect, URL, Session, Cache, DAL, Field
from ..common import db, session, T, auth,flash
from ..common_fn import LOGIN_URL
import hashlib
import requests
import json


@action('login/index', method=['GET'])
@action.uses("login/index.html", session,T,db,flash)
def index(): 
    
    return locals()


@action('login/check_user', method=['GET', 'POST'])
@action.uses( session,T,db,flash,LOGIN_URL)
def check_user():   
    if request.forms:
        email = str(request.forms.get('email')).strip()
        username = str(request.forms.get('username')).strip()
        password = str(request.forms.get('password')).strip()

        if not email or not username:
            flash.set('Invalid Email or Username!', 'warning')
            redirect(URL('login', 'index'))
        elif not password:
            flash.set('Invalid Password!', 'warning')
            redirect(URL('login', 'index'))
        elif len(password) < 6:
            flash.set('Password must be at least 6 characters long!', 'warning')
            redirect(URL('login', 'index'))
        else:
            
            url = LOGIN_URL

            payload = json.dumps({
            "cid": "SKF",
            "project_id": "expense",
            "email": email,
            "username": username,
            "password": password
            })
            headers = {
            'Content-Type': 'application/json',
            'Cookie': 'session_id_ams=182.16.158.70-68ba7052-7e82-46ea-9b96-412fe207477d'
            }

            response = requests.request("GET", url, headers=headers, data=payload)
            if response.status_code == 200:
                res_data = response.json()
                if res_data.get('status') == 'success':
                    session['status'] = "success"
                    session['cid'] = res_data.get('cid')
                    session['user_id'] = res_data.get('user_id')
                    session['username'] = res_data.get('username')
                    session['email'] = res_data.get('email')
                    session['full_name'] = res_data.get('full_name')  
                    session['role'] = res_data.get('user_role') or res_data.get('role')
                    session['mobile'] = res_data.get('mobile') 
                    session['image_path'] = res_data.get('image_path')
                    session['user_ip'] = res_data.get('user_ip')
                    session['browser_name'] = res_data.get('browser_name')
                    session['user_type'] = res_data.get('user_type')
                    session['note'] = res_data.get('note')
                    session['task_list'] = res_data.get('task_listStr', [])
                    flash.set('Login Successful!', 'success')
                    redirect(URL('dashboard', 'index'))
                else:
                    flash.set('Login Failed! ' + res_data.get('msg', ''), 'danger')
                    redirect(URL('login', 'index'))
            else:
                flash.set('Login request failed with status code: ' + str(response.status_code), 'danger')
                redirect(URL('login', 'index'))
    else:
        session['status'] = ''
        redirect(URL('login', 'index'))

    return locals()


@action('logout')
@action.uses("login/index.html", session,db,flash)   
def logout():
    session.clear()  # Clears the session data
    redirect(URL('login', 'index'))  # Redirect to the homepage or login page

