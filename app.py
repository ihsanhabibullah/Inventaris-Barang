from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from functools import wraps
from secrets import token_hex
from datetime import datetime

app = Flask(__name__)

# ================= CONFIG ================= #

app.secret_key = token_hex(16)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'db_inventaris'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# ================= SEEDER ADMIN ================= #

@app.route('/seeder_admin')
def seeder_admin():

    cur = mysql.connection.cursor()

    # cek apakah admin sudah ada
    cur.execute(
        "SELECT * FROM admin WHERE username=%s",
        ('admin',)
    )

    cek_admin = cur.fetchone()

    if cek_admin:

        cur.close()

        return 'Admin sudah ada'

    # insert admin default
    cur.execute("""
        INSERT INTO admin
        (
            username,
            password
        )
        VALUES (%s,%s)
    """, (
        'admin',
        'admin123'
    ))

    mysql.connection.commit()

    cur.close()

    return 'Seeder admin berhasil dibuat'


# ================= LOGIN REQUIRED ================= #

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):

        if 'admin' not in session:
            return redirect(url_for('login_admin'))

        return f(*args, **kwargs)

    return wrap

# ================= INDEX ================= #

@app.route('/')
def index():
    return render_template('index.html')

# ================= LOGIN ADMIN ================= #

@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT * FROM admin WHERE username=%s",
            (username,)
        )

        admin = cur.fetchone()

        cur.close()

        if admin:

            # sementara plain password dulu
            if password == admin['password']:

                session['admin'] = admin['id_admin']
                session['username'] = admin['username']

                flash('Login berhasil')

                return redirect(url_for('dashboard_admin'))

            else:
                flash('Password salah')

        else:
            flash('Username tidak ditemukan')

    return render_template('login_admin.html')

# ================= LOGIN PETUGAS ================= #

@app.route('/login_petugas', methods=['GET', 'POST'])
def login_petugas():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT * FROM petugas WHERE username=%s",
            (username,)
        )

        petugas = cur.fetchone()

        cur.close()

        if petugas:

            if password == petugas['password']:

                session['petugas'] = petugas['id_petugas']
                session['username'] = petugas['username']
                session['id_lokasi'] = petugas['id_lokasi']

                flash('Login berhasil')

                return redirect(url_for('dashboard_petugas'))

            else:
                flash('Password salah')

        else:
            flash('Username tidak ditemukan')

    return render_template('login_petugas.html')

# ================= LOGOUT ================= #

@app.route('/logout')
def logout():

    session.clear()

    flash('Logout berhasil')

    return redirect(url_for('index'))

# ================= DASHBOARD ADMIN ================= #

@app.route('/dashboard')
@login_required
def dashboard_admin():

    cur = mysql.connection.cursor()

    # total barang
    cur.execute("SELECT COUNT(*) as total FROM barang")
    total_barang = cur.fetchone()

    # total kategori
    cur.execute("SELECT COUNT(*) as total FROM kategori")
    total_kategori = cur.fetchone()

    # total petugas
    cur.execute("SELECT COUNT(*) as total FROM petugas")
    total_petugas = cur.fetchone()

    # total transaksi
    cur.execute("SELECT COUNT(*) as total FROM transaksi")
    total_transaksi = cur.fetchone()

    cur.close()

    return render_template(
        'admin/dashboard_admin.html',
        total_barang=total_barang,
        total_kategori=total_kategori,
        total_petugas=total_petugas,
        total_transaksi=total_transaksi
    )

# ================= DATA BARANG ================= #

@app.route('/data_barang')
@login_required
def data_barang():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT 
            barang.*,
            kategori.nama_kategori,
            lokasi.nama_lokasi
        FROM barang
        JOIN kategori ON barang.id_kategori = kategori.id_kategori
        JOIN lokasi ON barang.id_lokasi = lokasi.id_lokasi
        ORDER BY barang.id_barang DESC
    """)

    barang = cur.fetchall()

    cur.close()

    return render_template(
        'admin/data_barang.html',
        barang=barang
    )

# ================= TAMBAH BARANG ================= #

@app.route('/tambah_barang', methods=['GET', 'POST'])
@login_required
def tambah_barang():

    cur = mysql.connection.cursor()

    # ambil kategori
    cur.execute("SELECT * FROM kategori")
    kategori = cur.fetchall()

    # ambil lokasi
    cur.execute("SELECT * FROM lokasi")
    lokasi = cur.fetchall()

    if request.method == 'POST':

        nomor_barang = request.form['nomor_barang']
        nama_barang = request.form['nama_barang']
        merk = request.form['merk']
        tahun = request.form['tahun']
        kondisi = request.form['kondisi']
        id_kategori = request.form['id_kategori']
        id_lokasi = request.form['id_lokasi']

        cur.execute("""
            INSERT INTO barang
            (
                nomor_barang,
                nama_barang,
                merk,
                tahun,
                kondisi,
                id_kategori,
                id_lokasi
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            nomor_barang,
            nama_barang,
            merk,
            tahun,
            kondisi,
            id_kategori,
            id_lokasi
        ))

        mysql.connection.commit()

        flash('Barang berhasil ditambahkan')

        return redirect(url_for('data_barang'))

    return render_template(
        'admin/tambah_barang.html',
        kategori=kategori,
        lokasi=lokasi
    )

# ================= EDIT BARANG ================= #

@app.route('/edit_barang/<int:id>')
@login_required
def edit_barang(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM barang WHERE id_barang=%s",
        (id,)
    )

    barang = cur.fetchone()

    cur.execute("SELECT * FROM kategori")
    kategori = cur.fetchall()

    cur.execute("SELECT * FROM lokasi")
    lokasi = cur.fetchall()

    cur.close()

    return render_template(
        'admin/edit_data_barang.html',
        barang=barang,
        kategori=kategori,
        lokasi=lokasi
    )

# ================= UPDATE BARANG ================= #

@app.route('/update_barang/<int:id>', methods=['POST'])
@login_required
def update_barang(id):

    nomor_barang = request.form['nomor_barang']
    nama_barang = request.form['nama_barang']
    merk = request.form['merk']
    tahun = request.form['tahun']
    kondisi = request.form['kondisi']
    id_kategori = request.form['id_kategori']
    id_lokasi = request.form['id_lokasi']

    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE barang
        SET
            nomor_barang=%s,
            nama_barang=%s,
            merk=%s,
            tahun=%s,
            kondisi=%s,
            id_kategori=%s,
            id_lokasi=%s
        WHERE id_barang=%s
    """, (
        nomor_barang,
        nama_barang,
        merk,
        tahun,
        kondisi,
        id_kategori,
        id_lokasi,
        id
    ))

    mysql.connection.commit()

    cur.close()

    flash('Barang berhasil diupdate')

    return redirect(url_for('data_barang'))

# ================= HAPUS BARANG ================= #

@app.route('/hapus_barang/<int:id>')
@login_required
def hapus_barang(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM barang WHERE id_barang=%s",
        (id,)
    )

    mysql.connection.commit()

    cur.close()

    flash('Barang berhasil dihapus')

    return redirect(url_for('data_barang'))

# ================= DATA KATEGORI ================= #

@app.route('/data_kategori')
@login_required
def data_kategori():

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM kategori")

    kategori = cur.fetchall()

    cur.close()

    return render_template(
        'admin/data_kategori.html',
        kategori=kategori
    )

# ================= TAMBAH KATEGORI ================= #

@app.route('/tambah_kategori', methods=['GET', 'POST'])
@login_required
def tambah_kategori():

    if request.method == 'POST':

        nama_kategori = request.form['nama_kategori']

        cur = mysql.connection.cursor()

        cur.execute(
            "INSERT INTO kategori (nama_kategori) VALUES (%s)",
            (nama_kategori,)
        )

        mysql.connection.commit()

        cur.close()

        flash('Kategori berhasil ditambahkan')

        return redirect(url_for('data_kategori'))

    return render_template('admin/tambah_kategori.html')

# ================= EDIT KATEGORI ================= #

@app.route('/edit_kategori/<int:id>')
@login_required
def edit_kategori(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM kategori WHERE id_kategori=%s",
        (id,)
    )

    kategori = cur.fetchone()

    cur.close()

    return render_template(
        'admin/edit_data_kategori.html',
        kategori=kategori
    )

# ================= UPDATE KATEGORI ================= #

@app.route('/update_kategori/<int:id>', methods=['POST'])
@login_required
def update_kategori(id):

    nama_kategori = request.form['nama_kategori']

    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE kategori
        SET nama_kategori=%s
        WHERE id_kategori=%s
    """, (
        nama_kategori,
        id
    ))

    mysql.connection.commit()

    cur.close()

    flash('Kategori berhasil diupdate')

    return redirect(url_for('data_kategori'))

# ================= HAPUS KATEGORI ================= #

@app.route('/hapus_kategori/<int:id>')
@login_required
def hapus_kategori(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM kategori WHERE id_kategori=%s",
        (id,)
    )

    mysql.connection.commit()

    cur.close()

    flash('Kategori berhasil dihapus')

    return redirect(url_for('data_kategori'))

# ================= DATA LOKASI ================= #

@app.route('/data_lokasi')
@login_required
def data_lokasi():

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM lokasi")

    lokasi = cur.fetchall()

    cur.close()

    return render_template(
        'admin/data_lokasi.html',
        lokasi=lokasi
    )

# ================= TAMBAH LOKASI ================= #

@app.route('/tambah_data_lokasi', methods=['GET', 'POST'])
@login_required
def tambah_lokasi():

    if request.method == 'POST':

        nama_lokasi = request.form['nama_lokasi']

        cur = mysql.connection.cursor()

        cur.execute(
            "INSERT INTO lokasi (nama_lokasi) VALUES (%s)",
            (nama_lokasi,)
        )

        mysql.connection.commit()

        cur.close()

        flash('Lokasi berhasil ditambahkan')

        return redirect(url_for('data_lokasi'))

    return render_template('admin/tambah_lokasi.html')

# ================= HAPUS LOKASI ================= #

@app.route('/hapus_lokasi/<int:id>')
@login_required
def hapus_lokasi(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM lokasi WHERE id_lokasi=%s",
        (id,)
    )

    mysql.connection.commit()

    cur.close()

    flash('Lokasi berhasil dihapus')

    return redirect(url_for('data_lokasi'))

# ================= DATA PETUGAS ================= #

@app.route('/data_petugas')
@login_required
def data_petugas():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT 
            petugas.*,
            lokasi.nama_lokasi
        FROM petugas
        JOIN lokasi ON petugas.id_lokasi = lokasi.id_lokasi
    """)

    petugas = cur.fetchall()

    cur.close()

    return render_template(
        'admin/data_petugas.html',
        petugas=petugas
    )

# ================= TAMBAH PETUGAS ================= #

@app.route('/tambah_data_petugas', methods=['GET', 'POST'])
@login_required
def tambah_petugas():

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM lokasi")

    lokasi = cur.fetchall()

    if request.method == 'POST':

        nama_petugas = request.form['nama_petugas']
        username = request.form['username']
        password = request.form['password']
        id_lokasi = request.form['id_lokasi']

        cur.execute("""
            INSERT INTO petugas
            (
                nama_petugas,
                username,
                password,
                id_lokasi
            )
            VALUES (%s,%s,%s,%s)
        """, (
            nama_petugas,
            username,
            password,
            id_lokasi
        ))

        mysql.connection.commit()

        flash('Petugas berhasil ditambahkan')

        return redirect(url_for('data_petugas'))

    return render_template(
        'admin/tambah_petugas.html',
        lokasi=lokasi
    )

# ================= DASHBOARD PETUGAS ================= #

@app.route('/dashboard_petugas')
def dashboard_petugas():
    return render_template('petugas/dashboard_petugas.html')

# ================= LAPORAN PETUGAS ================= #

@app.route('/data_laporan_petugas')
def data_laporan_petugas():
    return render_template('petugas/data_laporan_petugas.html')

# ================= TRANSAKSI ================= #

@app.route('/tambah_transaksi')
def tambah_transaksi():
    return render_template('petugas/tambah_transaksi.html')

if __name__ == '__main__':
    app.run(debug=True)