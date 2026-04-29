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
    
@app.route('/data_barang')
def data_barang():
    return render_template('admin/data_barang.html')

@app.route('/data_kategori')
def data_kategori():
    return render_template('admin/data_kategori.html')

@app.route('/data_laporan')
def data_laporan():
    return render_template('admin/data_laporan.html')

@app.route('/data_lokasi')
def data_lokasi():
    return render_template('admin/data_lokasi.html')

@app.route('/data_petugas')
def data_petugas():
    return render_template('admin/data_petugas.html')

@app.route('/edit_data_barang')
def edit_data_barang():
    return render_template('admin/edit_data_barang.html')

@app.route('/edit_data_kategori')
def edit_data_kategori():
    return render_template('admin/edit_data_kategori.html')

@app.route('/edit_data_lokasi')
def edit_data_lokasi():
    return render_template('admin/edit_data_lokasi.html')

@app.route('/edit_data_petugas')
def edit_data_petugas():
    return render_template('admin/edit_data_petugas.html')

@app.route('/login_admin')
def login_admin():
    return render_template('admin/login_admin.html')

@app.route('/tambah_barang')
def tambah_barang():
    return render_template('admin/tambah_barang.html')

@app.route('/tambah_data_lokasi')
def tambah_data_lokasi():
    return render_template('admin/tambah_data_lokasi.html')

@app.route('/tambah_data_petugas')
def tambah_data_petugas():
    return render_template('admin/tambah_data_petugas.html')

@app.route('/tambah_kategori')
def tambah_kategori():
    return render_template('admin/tambah_kategori.html')

if __name__ == '__main__':
    app.run(debug=True)