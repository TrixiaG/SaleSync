from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from .models import User, prodInventory
from . import db
from werkzeug.security import check_password_hash
from flask_login import login_user, login_required, current_user, logout_user
import sqlite3, smtplib, datetime

login = Blueprint('login', __name__)

def fetch_email(eid):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM users WHERE eid = ?', (eid,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None

def send_otp(email, otp):
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('qtdgregorio@tip.edu.ph', '@Shxxbi131!!')
        message = f'Subject: TCFM SaleSync OTP\n\nYour OTP is {otp}'
        server.sendmail('your_email@example.com', email, message)

@login.route('/login', methods=['GET', 'POST'])
def userLogin():

    if request.method == 'POST':
        eid = request.form.get('eid')
        password = request.form.get('password')
        
        user = User.query.filter_by(eid=eid).first()

        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully.', category='success')
                login_user(user, remember=True)
                
                session['username'] = request.form.get('username')
                return render_template("OTP.html", boolean=True)
            else:
                flash('Invalid login information.', category='error')
        else:
            flash('EID does not exist', category='error')
    return render_template("login.html", boolean=True)



@login.route('/logout')
@login_required
def userLogout():
    logout_user()
    return redirect(url_for('login.userLogin'))

# Blueprint for inventory
inventory = Blueprint('inventory', __name__)

@inventory.route('/inventory', methods=['GET', 'POST'])
@login_required
def productInventory():
    if request.method == 'POST':
        ptype = request.form.get('pType')
        pcode = request.form.get('pCode')
        pname = request.form.get('pName')
        pstock = request.form.get('pStock')

        # Log the current time and the logged-in user
        ptimelog = datetime.utcnow()
        puserlog = current_user.eid

        new_product = prodInventory(
            pType=ptype,
            pCode=pcode,
            pName=pname,
            pStock=pstock,
            pTimeLog=ptimelog,
            pUserLog=puserlog
        )
        db.session.add(new_product)
        db.session.commit()

        flash('Inventory Updated.', 'success')
        return redirect(url_for('inventory.productInventory'))