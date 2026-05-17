from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from functools import wraps
from secrets import token_hex

app = Flask(__name__)

# ================= CONFIG ================= #

app.secret_key = token_hex(16)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'db_inventaris'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

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

# ================= SEEDER ADMIN ================= #

@app.route('/seeder_admin')
def seeder_admin():

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM admin WHERE username=%s",
        ('admin',)
    )

    cek_admin = cur.fetchone()

    if cek_admin:

        cur.close()

        return 'Admin sudah ada'

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

    cur.execute("""
        SELECT 
            barang.id_barang,
            barang.nomor_barang,
            barang.nama_barang,
            barang.kondisi_barang,
            transaksi.tanggal,
            transaksi.tipe
        FROM transaksi
        JOIN barang ON transaksi.id_barang = barang.id_barang
        ORDER BY transaksi.tanggal DESC
    """)

    laporan_gudang = cur.fetchall()

    cur.close()

    return render_template(
        'admin/dashboard_admin.html',
        laporan_gudang=laporan_gudang
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
        JOIN kategori
        ON barang.id_kategori = kategori.id_kategori
        JOIN lokasi
        ON barang.id_lokasi = lokasi.id_lokasi
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

    cur.execute("SELECT * FROM kategori")
    kategori = cur.fetchall()

    cur.execute("SELECT * FROM lokasi")
    lokasi = cur.fetchall()

    if request.method == 'POST':

        nomor_barang = request.form['nomor_barang']
        nama_barang = request.form['nama_barang']
        kondisi_barang = request.form['kondisi_barang']
        id_kategori = request.form['id_kategori']
        id_lokasi = request.form['id_lokasi']

        cur.execute("""
            INSERT INTO barang
            (
                nomor_barang,
                nama_barang,
                kondisi_barang,
                id_kategori,
                id_lokasi
            )
            VALUES (%s,%s,%s,%s,%s)
        """, (
            nomor_barang,
            nama_barang,
            kondisi_barang,
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
    kondisi_barang = request.form['kondisi_barang']
    id_kategori = request.form['id_kategori']
    id_lokasi = request.form['id_lokasi']

    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE barang
        SET
            nomor_barang=%s,
            nama_barang=%s,
            kondisi_barang=%s,
            id_kategori=%s,
            id_lokasi=%s
        WHERE id_barang=%s
    """, (
        nomor_barang,
        nama_barang,
        kondisi_barang,
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

# ================= EDIT LOKASI ================= #

@app.route('/edit_lokasi/<int:id>')
@login_required
def edit_lokasi(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM lokasi WHERE id_lokasi=%s",
        (id,)
    )

    lokasi = cur.fetchone()

    cur.close()

    return render_template(
        'admin/edit_data_lokasi.html',
        lokasi=lokasi
    )

# ================= UPDATE LOKASI ================= #

@app.route('/update_lokasi/<int:id>', methods=['POST'])
@login_required
def update_lokasi(id):

    nama_lokasi = request.form['nama_lokasi']

    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE lokasi
        SET nama_lokasi=%s
        WHERE id_lokasi=%s
    """, (
        nama_lokasi,
        id
    ))

    mysql.connection.commit()

    cur.close()

    flash('Lokasi berhasil diupdate')

    return redirect(url_for('data_lokasi'))

# ================= DATA PETUGAS ================= #

@app.route('/data_petugas')
@login_required
def data_petugas():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT 
            p.id_petugas,
            p.username,
            p.id_lokasi,
            l.nama_lokasi
        FROM petugas p
        JOIN lokasi l 
        ON p.id_lokasi = l.id_lokasi
        ORDER BY p.id_petugas DESC
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

        username = request.form['username']
        password = request.form['password']
        id_lokasi = request.form['id_lokasi']

        cur.execute("""
            INSERT INTO petugas
            (
                username,
                password,
                id_lokasi
            )
            VALUES (%s,%s,%s)
        """, (
            username,
            password,
            id_lokasi
        ))

        mysql.connection.commit()

        cur.close()

        flash('Petugas berhasil ditambahkan')

        return redirect(url_for('data_petugas'))

    return render_template(
        'admin/tambah_petugas.html',
        lokasi=lokasi
    )


# ================= EDIT PETUGAS ================= #

@app.route('/edit_petugas/<int:id>')
@login_required
def edit_petugas(id):

    cur = mysql.connection.cursor()

    # ambil data petugas
    cur.execute(
        "SELECT * FROM petugas WHERE id_petugas=%s",
        (id,)
    )
    petugas = cur.fetchone()

    # ambil lokasi
    cur.execute("SELECT * FROM lokasi")
    lokasi = cur.fetchall()

    cur.close()

    return render_template(
        'admin/edit_data_petugas.html',
        petugas=petugas,
        lokasi=lokasi
    )


# ================= UPDATE PETUGAS ================= #

@app.route('/update_petugas/<int:id>', methods=['POST'])
@login_required
def update_petugas(id):

    username = request.form['username']
    password = request.form['password']
    id_lokasi = request.form['id_lokasi']

    cur = mysql.connection.cursor()

    # jika password diisi → update semua
    if password:
        cur.execute("""
            UPDATE petugas
            SET 
                username=%s,
                password=%s,
                id_lokasi=%s
            WHERE id_petugas=%s
        """, (
            username,
            password,
            id_lokasi,
            id
        ))
    else:
        # kalau password kosong → jangan update password
        cur.execute("""
            UPDATE petugas
            SET 
                username=%s,
                id_lokasi=%s
            WHERE id_petugas=%s
        """, (
            username,
            id_lokasi,
            id
        ))

    mysql.connection.commit()

    cur.close()

    flash('Petugas berhasil diupdate')

    return redirect(url_for('data_petugas'))


# ================= HAPUS PETUGAS ================= #

@app.route('/hapus_petugas/<int:id>')
@login_required
def hapus_petugas(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM petugas WHERE id_petugas=%s",
        (id,)
    )

    mysql.connection.commit()

    cur.close()

    flash('Petugas berhasil dihapus')

    return redirect(url_for('data_petugas'))

# ================= DATA LAPORAN ================= #

@app.route('/data_laporan')
@login_required
def data_laporan():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            transaksi.id_transaksi,
            barang.nama_barang,
            barang.nomor_barang,
            barang.kondisi_barang,
            kategori.nama_kategori,
            lokasi.nama_lokasi,
            transaksi.tipe,
            transaksi.tanggal
        FROM transaksi
        JOIN barang
        ON transaksi.id_barang = barang.id_barang
        JOIN kategori
        ON barang.id_kategori = kategori.id_kategori
        JOIN lokasi
        ON barang.id_lokasi = lokasi.id_lokasi
        ORDER BY transaksi.id_transaksi DESC
    """)

    laporan = cur.fetchall()

    cur.close()

    return render_template(
        'admin/data_laporan.html',
        laporan=laporan
    )

# ================= DASHBOARD PETUGAS ================= #

@app.route('/dashboard_petugas')
def dashboard_petugas():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            barang.id_barang,
            barang.nomor_barang,
            barang.nama_barang,
            barang.kondisi_barang,
            transaksi.tanggal,
            transaksi.tipe
        FROM transaksi
        JOIN barang
        ON transaksi.id_barang = barang.id_barang
        ORDER BY transaksi.tanggal DESC
    """)

    laporan_gudang = cur.fetchall()

    cur.close()

    return render_template(
        'petugas/dashboard_petugas.html',
        laporan_gudang=laporan_gudang
    )

# ================= DATA LAPORAN PETUGAS ================= #

@app.route('/data_laporan_petugas')
def data_laporan_petugas():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            transaksi.id_transaksi,
            barang.nama_barang,
            barang.nomor_barang,
            barang.kondisi_barang,
            kategori.nama_kategori,
            lokasi.nama_lokasi,
            transaksi.tipe,
            transaksi.tanggal
        FROM transaksi
        JOIN barang
        ON transaksi.id_barang = barang.id_barang
        JOIN kategori
        ON barang.id_kategori = kategori.id_kategori
        JOIN lokasi
        ON barang.id_lokasi = lokasi.id_lokasi
        ORDER BY transaksi.id_transaksi DESC
    """)

    laporan = cur.fetchall()

    cur.close()

    return render_template(
        'petugas/data_laporan_petugas.html',
        laporan=laporan
    )

# ================= TAMBAH TRANSAKSI ================= #

@app.route('/tambah_transaksi', methods=['GET', 'POST'])
def tambah_transaksi():

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM barang")
    barang = cur.fetchall()

    if request.method == 'POST':

        id_barang = request.form['id_barang']
        tipe = request.form['tipe']

        id_petugas = session['petugas']

        cur.execute("""
            INSERT INTO transaksi
            (
                id_barang,
                tipe,
                id_petugas,
                tanggal
            )
            VALUES (%s,%s,%s,NOW())
        """, (
            id_barang,
            tipe,
            id_petugas
        ))

        mysql.connection.commit()

        flash('Transaksi berhasil ditambahkan')

        return redirect(url_for('data_laporan_petugas'))

    return render_template(
        'petugas/tambah_transaksi.html',
        barang=barang
    )

# ================= EDIT TRANSAKSI ================= #

@app.route('/edit_transaksi/<int:id>')
def edit_transaksi(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM transaksi WHERE id_transaksi=%s",
        (id,)
    )

    transaksi = cur.fetchone()

    cur.execute("SELECT * FROM barang")
    barang = cur.fetchall()

    cur.close()

    return render_template(
        'petugas/edit_transaksi.html',
        transaksi=transaksi,
        barang=barang
    )

# ================= UPDATE TRANSAKSI ================= #

@app.route('/update_transaksi/<int:id>', methods=['POST'])
def update_transaksi(id):

    id_barang = request.form['id_barang']
    tipe = request.form['tipe']

    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE transaksi
        SET
            id_barang=%s,
            tipe=%s
        WHERE id_transaksi=%s
    """, (
        id_barang,
        tipe,
        id
    ))

    mysql.connection.commit()

    cur.close()

    flash('Transaksi berhasil diupdate')

    return redirect(url_for('data_laporan_petugas'))

# ================= HAPUS TRANSAKSI ================= #

@app.route('/hapus_transaksi/<int:id>')
def hapus_transaksi(id):

    cur = mysql.connection.cursor()

    cur.execute(
        "DELETE FROM transaksi WHERE id_transaksi=%s",
        (id,)
    )

    mysql.connection.commit()

    cur.close()

    flash('Transaksi berhasil dihapus')

    return redirect(url_for('data_laporan_petugas'))

# ================= RUN ================= #

if __name__ == '__main__':
    app.run(debug=True)