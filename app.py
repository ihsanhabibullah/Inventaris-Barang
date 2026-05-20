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
# ================= LOGIN REQUIRED PETUGAS ================= #

def petugas_login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'petugas' not in session:
            return redirect(url_for('login_petugas'))
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

    username = ''

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

                flash('Login berhasil', 'success')

                return redirect(url_for('dashboard_admin'))

            else:
                flash('Password salah', 'danger')

        else:
            flash('Username tidak ditemukan', 'danger')

    return render_template('login_admin.html', username=username)


@app.route('/login_petugas', methods=['GET', 'POST'])
def login_petugas():
    username = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # DEBUG PRINT
        print("=" * 50)
        print(f"[DEBUG] Login attempt — Username: '{username}', Password: '{password}'")

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM petugas WHERE username=%s", (username,))
            petugas = cur.fetchone()
            cur.close()

            print(f"[DEBUG] Query result: {petugas}")

            if petugas:
                print(f"[DEBUG] Found user — DB password: '{petugas['password']}'")
                if password == petugas['password']:
                    session['petugas'] = petugas['id_petugas']
                    session['username'] = petugas['username']
                    session['id_lokasi'] = petugas['id_lokasi']
                    flash('Login berhasil', 'success')
                    print(f"[DEBUG] Login SUCCESS — Redirect to dashboard_petugas")
                    print("=" * 50)
                    return redirect(url_for('dashboard_petugas'))
                else:
                    flash('Password salah', 'danger')
                    print(f"[DEBUG] Password mismatch — Input: '{password}' vs DB: '{petugas['password']}'")
            else:
                flash('Username tidak ditemukan', 'danger')
                print(f"[DEBUG] Username '{username}' not found in database")

        except Exception as e:
            print(f"[DEBUG] ERROR: {str(e)}")
            flash(f'Terjadi kesalahan: {str(e)}', 'danger')

        print("=" * 50)

    return render_template('login_petugas.html', username=username)

# ================= LOGOUT ================= #

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout berhasil', 'success')
    return redirect(url_for('index'))

# ================= DASHBOARD ADMIN ================= #

@app.route('/dashboard')
@login_required
def dashboard_admin():

    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) AS total_transaksi FROM transaksi")
    total_transaksi = cur.fetchone()['total_transaksi']

    cur.execute("SELECT COUNT(*) AS total_lokasi FROM lokasi")
    total_lokasi = cur.fetchone()['total_lokasi']

    cur.execute("SELECT COUNT(*) AS total_petugas FROM petugas")
    total_petugas = cur.fetchone()['total_petugas']

    cur.execute("SELECT COUNT(*) AS total_kategori FROM kategori")
    total_kategori = cur.fetchone()['total_kategori']

    cur.execute("""
        SELECT
            t.id_transaksi,
            l.nama_lokasi,
            b.nama_barang,
            k.nama_kategori,
            t.tanggal,
            p.username AS nama_petugas,
            t.tipe
        FROM transaksi t
        JOIN barang b ON t.id_barang = b.id_barang
        JOIN kategori k ON b.id_kategori = k.id_kategori
        JOIN lokasi l ON b.id_lokasi = l.id_lokasi
        JOIN petugas p ON t.id_petugas = p.id_petugas
        ORDER BY t.tanggal DESC, t.id_transaksi DESC
    """)

    laporan_gudang = cur.fetchall()

    cur.close()

    return render_template(
        'admin/dashboard_admin.html',
        laporan_gudang=laporan_gudang,
        total_transaksi=total_transaksi,
        total_lokasi=total_lokasi,
        total_petugas=total_petugas,
        total_kategori=total_kategori
    )

# ================= DATA BARANG ================= #

@app.route('/data_barang')
@login_required
def data_barang():

    cur = mysql.connection.cursor()

    # ambil daftar kategori dan lokasi untuk select filter
    cur.execute("SELECT * FROM kategori ORDER BY nama_kategori ASC")
    kategori = cur.fetchall()
    cur.execute("SELECT * FROM lokasi ORDER BY nama_lokasi ASC")
    lokasi = cur.fetchall()

    # ambil filter dari query params
    id_kategori = request.args.get('id_kategori')
    id_lokasi = request.args.get('id_lokasi')

    # bangun query dinamis
    base_query = """
        SELECT 
            barang.*,
            kategori.nama_kategori,
            lokasi.nama_lokasi
        FROM barang
        JOIN kategori ON barang.id_kategori = kategori.id_kategori
        JOIN lokasi ON barang.id_lokasi = lokasi.id_lokasi
    """

    filters = []
    params = []

    if id_kategori:
        filters.append("barang.id_kategori = %s")
        params.append(id_kategori)

    if id_lokasi:
        filters.append("barang.id_lokasi = %s")
        params.append(id_lokasi)

    if filters:
        base_query += " WHERE " + " AND ".join(filters)

    base_query += " ORDER BY barang.id_barang DESC"

    cur.execute(base_query, tuple(params))
    barang = cur.fetchall()

    cur.close()

    return render_template('admin/data_barang.html', barang=barang, kategori=kategori, lokasi=lokasi, selected_kategori=id_kategori, selected_lokasi=id_lokasi)

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

    search_query = request.args.get('q', '').strip()

    cur = mysql.connection.cursor()

    if search_query:
        cur.execute("""
            SELECT 
                p.id_petugas,
                p.username,
                p.id_lokasi,
                l.nama_lokasi
            FROM petugas p
            JOIN lokasi l 
            ON p.id_lokasi = l.id_lokasi
            WHERE p.username LIKE %s
            ORDER BY p.id_petugas DESC
        """, ('%' + search_query + '%',))
    else:
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
        petugas=petugas,
        search_query=search_query
    )

# ================= lihat barang lokasi ================= #
@app.route('/barang_lokasi/<int:id>')
def barang_lokasi(id):
    cur = mysql.connection.cursor()

    cur.execute(
        "SELECT * FROM lokasi WHERE id_lokasi = %s",
        (id,)
    )
    lokasi = cur.fetchone()

    cur.execute("""
        SELECT
            k.id_kategori,
            k.nama_kategori,
            COUNT(b.id_barang) AS jumlah
        FROM barang b
        JOIN kategori k ON b.id_kategori = k.id_kategori
        WHERE b.id_lokasi = %s
        GROUP BY k.id_kategori, k.nama_kategori
        ORDER BY jumlah DESC, k.nama_kategori
    """, (id,))
    kategori_counts = cur.fetchall()

    cur.close()

    return render_template(
        'admin/barang_lokasi.html',
        lokasi=lokasi,
        kategori_counts=kategori_counts
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
def data_laporan():

    cur = mysql.connection.cursor()
    # ambil daftar kategori dan lokasi untuk filter
    cur.execute("SELECT * FROM kategori ORDER BY nama_kategori ASC")
    kategori = cur.fetchall()
    cur.execute("SELECT * FROM lokasi ORDER BY nama_lokasi ASC")
    lokasi = cur.fetchall()

    # ambil filter dari query params
    id_kategori = request.args.get('id_kategori')
    id_lokasi = request.args.get('id_lokasi')

    base_query = """
        SELECT 
            l.nama_lokasi,
            b.nama_barang,
            k.nama_kategori,
            b.kondisi_barang,
            t.tanggal,
            p.username,
            t.tipe
        FROM transaksi t

        INNER JOIN barang b 
            ON t.id_barang = b.id_barang

        INNER JOIN kategori k 
            ON b.id_kategori = k.id_kategori

        INNER JOIN lokasi l 
            ON b.id_lokasi = l.id_lokasi

        INNER JOIN petugas p 
            ON t.id_petugas = p.id_petugas
    """

    filters = []
    params = []

    if id_kategori:
        filters.append("b.id_kategori = %s")
        params.append(id_kategori)
    if id_lokasi:
        filters.append("b.id_lokasi = %s")
        params.append(id_lokasi)

    if filters:
        base_query += " WHERE " + " AND ".join(filters)

    base_query += " ORDER BY t.tanggal DESC"

    cur.execute(base_query, tuple(params))
    laporan = cur.fetchall()

    cur.close()

    return render_template('admin/data_laporan.html', laporan=laporan, kategori=kategori, lokasi=lokasi, selected_kategori=id_kategori, selected_lokasi=id_lokasi)
# ================= DASHBOARD PETUGAS ================= #

@app.route('/dashboard_petugas')
@petugas_login_required
def dashboard_petugas():
    id_petugas = session['petugas']
    cur = mysql.connection.cursor()

    # Total barang di lokasi petugas
    cur.execute("""
        SELECT COUNT(*) as total FROM barang
        WHERE id_lokasi = (SELECT id_lokasi FROM petugas WHERE id_petugas = %s)
    """, (id_petugas,))
    total_barang = cur.fetchone()['total']

    # Barang masuk
    cur.execute("""
        SELECT COUNT(*) as total FROM transaksi
        WHERE tipe = 'masuk' AND id_petugas = %s
    """, (id_petugas,))
    barang_masuk = cur.fetchone()['total']

    # Barang keluar
    cur.execute("""
        SELECT COUNT(*) as total FROM transaksi
        WHERE tipe = 'keluar' AND id_petugas = %s
    """, (id_petugas,))
    barang_keluar = cur.fetchone()['total']

    # Total transaksi
    cur.execute("""
        SELECT COUNT(*) as total FROM transaksi WHERE id_petugas = %s
    """, (id_petugas,))
    total_transaksi = cur.fetchone()['total']

    # Data transaksi terbaru
    cur.execute("""
        SELECT
            transaksi.id_transaksi,
            barang.nama_barang,
            kategori.nama_kategori,
            barang.nomor_barang,
            transaksi.tanggal,
            transaksi.tipe
        FROM transaksi
        JOIN barang ON transaksi.id_barang = barang.id_barang
        JOIN kategori ON barang.id_kategori = kategori.id_kategori
        WHERE transaksi.id_petugas = %s
        ORDER BY transaksi.tanggal DESC
        LIMIT 5
    """, (id_petugas,))
    transaksi_terbaru = cur.fetchall()

    cur.close()
    return render_template(
        'petugas/dashboard_petugas.html',
        total_barang=total_barang,
        barang_masuk=barang_masuk,
        barang_keluar=barang_keluar,
        total_transaksi=total_transaksi,
        transaksi_terbaru=transaksi_terbaru
    )

# ================= DATA LAPORAN PETUGAS ================= #

@app.route('/data_laporan_petugas')
@petugas_login_required
def data_laporan_petugas():
    id_petugas = session['petugas']
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
            transaksi.tanggal,
            petugas.username as nama_petugas
        FROM transaksi
        JOIN barang ON transaksi.id_barang = barang.id_barang
        JOIN kategori ON barang.id_kategori = kategori.id_kategori
        JOIN lokasi ON barang.id_lokasi = lokasi.id_lokasi
        JOIN petugas ON transaksi.id_petugas = petugas.id_petugas
        WHERE transaksi.id_petugas = %s
        ORDER BY transaksi.id_transaksi DESC
    """, (id_petugas,))
    laporan = cur.fetchall()
    cur.close()
    return render_template('petugas/data_laporan_petugas.html', laporan=laporan)

# ================= DATA LOKASI PETUGAS ================= #

@app.route('/data_lokasi_petugas')
@petugas_login_required
def data_lokasi_petugas():
    cur = mysql.connection.cursor()

    # ambil id lokasi dari session petugas
    id_lokasi_petugas = session.get('id_lokasi')

    # ambil data lokasi petugas
    cur.execute("SELECT * FROM lokasi WHERE id_lokasi=%s", (id_lokasi_petugas,))
    lokasi = cur.fetchone()

    # ambil seluruh kategori dan jumlah barang di lokasi petugas (termasuk kategori dengan 0)
    cur.execute("""
        SELECT
            k.id_kategori,
            k.nama_kategori,
            COALESCE(COUNT(b.id_barang), 0) AS jumlah
        FROM kategori k
        LEFT JOIN barang b
            ON b.id_kategori = k.id_kategori
            AND b.id_lokasi = %s
        GROUP BY k.id_kategori, k.nama_kategori
        ORDER BY jumlah DESC, k.nama_kategori
    """, (id_lokasi_petugas,))
    kategori_counts = cur.fetchall()

    cur.close()

    return render_template('petugas/data_lokasi_petugas.html', lokasi=lokasi, kategori_counts=kategori_counts)

# ================= TAMBAH TRANSAKSI ================= #

@app.route('/tambah_transaksi', methods=['GET', 'POST'])
@petugas_login_required
def tambah_transaksi():
    cur = mysql.connection.cursor()

    cur.execute("SELECT id_lokasi FROM lokasi WHERE nama_lokasi LIKE %s LIMIT 1", ("%Gudang%",))
    gudang_row = cur.fetchone()
    id_lokasi_gudang = gudang_row['id_lokasi'] if gudang_row else None

    cur.execute("SELECT * FROM barang WHERE id_lokasi=%s ORDER BY nama_barang ASC", (id_lokasi_gudang,))
    barang = cur.fetchall()

    if request.method == 'POST':
        id_barang = request.form['id_barang']
        tipe = request.form['tipe']
        tanggal = request.form.get('tanggal') or None
        id_petugas = session['petugas']

        cur.execute("SELECT id_lokasi FROM barang WHERE id_barang=%s", (id_barang,))
        barang_row = cur.fetchone()
        if not barang_row or barang_row['id_lokasi'] != id_lokasi_gudang:
            flash('Barang hanya dapat dipilih dari gudang instansi.', 'danger')
            return redirect(url_for('tambah_transaksi'))

        if tanggal:
            cur.execute("""
                INSERT INTO transaksi (id_barang, tipe, id_petugas, tanggal)
                VALUES (%s, %s, %s, %s)
            """, (id_barang, tipe, id_petugas, tanggal))
        else:
            cur.execute("""
                INSERT INTO transaksi (id_barang, tipe, id_petugas, tanggal)
                VALUES (%s, %s, %s, CURDATE())
            """, (id_barang, tipe, id_petugas))
        mysql.connection.commit()

        if tipe.lower() == 'masuk' and session.get('id_lokasi'):
            cur.execute("UPDATE barang SET id_lokasi=%s WHERE id_barang=%s", (session['id_lokasi'], id_barang))
            mysql.connection.commit()
        elif tipe.lower() == 'keluar' and id_lokasi_gudang:
            cur.execute("UPDATE barang SET id_lokasi=%s WHERE id_barang=%s", (id_lokasi_gudang, id_barang))
            mysql.connection.commit()

        flash('Transaksi berhasil ditambahkan', 'success')
        return redirect(url_for('data_laporan_petugas'))

    return render_template('petugas/tambah_transaksi.html', barang=barang)

# ================= EDIT TRANSAKSI ================= #

@app.route('/edit_transaksi/<int:id>')
@petugas_login_required
def edit_transaksi(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_lokasi FROM lokasi WHERE nama_lokasi LIKE %s LIMIT 1", ("%Gudang%",))
    gudang_row = cur.fetchone()
    id_lokasi_gudang = gudang_row['id_lokasi'] if gudang_row else None

    cur.execute("SELECT * FROM transaksi WHERE id_transaksi=%s", (id,))
    transaksi = cur.fetchone()
    current_barang_id = transaksi['id_barang'] if transaksi else 0
    cur.execute(
        "SELECT * FROM barang WHERE id_lokasi=%s OR id_barang=%s ORDER BY nama_barang ASC",
        (id_lokasi_gudang, current_barang_id)
    )
    barang = cur.fetchall()
    cur.close()
    return render_template('petugas/edit_transaksi.html', transaksi=transaksi, barang=barang)

# ================= UPDATE TRANSAKSI ================= #

@app.route('/update_transaksi/<int:id>', methods=['POST'])
@petugas_login_required
def update_transaksi(id):
    id_barang = request.form['id_barang']
    tipe = request.form['tipe']
    tanggal = request.form.get('tanggal') or None
    id_petugas = session['petugas']
    id_lokasi_petugas = session.get('id_lokasi')

    cur = mysql.connection.cursor()
    if not id_lokasi_petugas:
        cur.execute("SELECT id_lokasi FROM petugas WHERE id_petugas=%s", (id_petugas,))
        petugas_row = cur.fetchone()
        id_lokasi_petugas = petugas_row['id_lokasi'] if petugas_row else None

    cur.execute("SELECT id_lokasi FROM lokasi WHERE nama_lokasi LIKE %s LIMIT 1", ("%Gudang%",))
    gudang_row = cur.fetchone()
    id_lokasi_gudang = gudang_row['id_lokasi'] if gudang_row else None

    cur.execute("SELECT id_lokasi FROM barang WHERE id_barang=%s", (id_barang,))
    barang_row = cur.fetchone()
    if not barang_row or barang_row['id_lokasi'] != id_lokasi_gudang:
        flash('Barang hanya dapat dipilih dari gudang instansi.', 'danger')
        return redirect(url_for('edit_transaksi', id=id))

    if tanggal:
        cur.execute("""
            UPDATE transaksi SET id_barang=%s, tipe=%s, tanggal=%s WHERE id_transaksi=%s
        """, (id_barang, tipe, tanggal, id))
    else:
        cur.execute("""
            UPDATE transaksi SET id_barang=%s, tipe=%s WHERE id_transaksi=%s
        """, (id_barang, tipe, id))
    mysql.connection.commit()

    if tipe.lower() == 'masuk' and id_lokasi_petugas:
        cur.execute("UPDATE barang SET id_lokasi=%s WHERE id_barang=%s", (id_lokasi_petugas, id_barang))
    elif tipe.lower() == 'keluar' and id_lokasi_gudang:
        cur.execute("UPDATE barang SET id_lokasi=%s WHERE id_barang=%s", (id_lokasi_gudang, id_barang))
    mysql.connection.commit()

    cur.close()
    flash('Transaksi berhasil diupdate', 'success')
    return redirect(url_for('data_laporan_petugas'))

# ================= HAPUS TRANSAKSI ================= #

@app.route('/hapus_transaksi/<int:id>')
@petugas_login_required
def hapus_transaksi(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM transaksi WHERE id_transaksi=%s", (id,))
    mysql.connection.commit()
    cur.close()
    flash('Transaksi berhasil dihapus', 'success')
    return redirect(url_for('data_laporan_petugas'))
# ================= RUN ================= #

if __name__ == '__main__':
    app.run(debug=True)