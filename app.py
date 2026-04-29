from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
import bcrypt
from functools import wraps
from datetime import datetime, date
from secrets import token_hex


app = Flask(__name__)
app.secret_key=token_hex(16)
app.config['MYSQL_CURSORCLASS']='DictCursor'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='db_inventaris'
app.config['UPLOAD_FOLDER']='static/uploads'
mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('admin/dashboard_admin.html')

if __name__ == '__main__':
    app.run(debug=True)