#Routes
from flask import Blueprint, render_template

views = Blueprint('views', __name__)

@views.route('/login')
def loginPage():
    return render_template("login.html")