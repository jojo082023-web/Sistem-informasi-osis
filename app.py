from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "rahasia-super-rahasia"

# ---------- DB ----------
def get_db_connection():
    conn = sqlite3.connect("todo.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # users
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    # anggota
    conn.execute("""
        CREATE TABLE IF NOT EXISTS anggota (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            jabatan TEXT NOT NULL
        )
    """)
    # kegiatan
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kegiatan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_kegiatan TEXT NOT NULL,
            tanggal TEXT NOT NULL
        )
    """)
    # surat
    conn.execute("""
        CREATE TABLE IF NOT EXISTS surat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            perihal TEXT NOT NULL,
            tanggal TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("home.html")

# ---------- Helpers ----------
def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

# ---------- Routes umum ----------
@app.route("/")
def index():
    return render_template("index.html")

# ---------- Auth ----------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        if not username or not password:
            flash("Username dan password wajib diisi.", "danger")
            return render_template("register.html")
        pw_hash = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, pw_hash))
            conn.commit()
            flash("Registrasi berhasil. Silakan login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username sudah digunakan.", "danger")
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Login berhasil!", "success")
            return redirect(url_for("dashboard"))
        flash("Username atau password salah.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Anda telah logout.", "info")
    return redirect(url_for("login"))

# ---------- Dashboard ----------
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_connection()
    anggota_count = conn.execute("SELECT COUNT(*) AS c FROM anggota").fetchone()["c"]
    kegiatan_count = conn.execute("SELECT COUNT(*) AS c FROM kegiatan").fetchone()["c"]
    surat_count = conn.execute("SELECT COUNT(*) AS c FROM surat").fetchone()["c"]
    conn.close()
    return render_template(
        "dashboard.html",
        username=session.get("username"),
        anggota_count=anggota_count,
        kegiatan_count=kegiatan_count,
        surat_count=surat_count
    )

# ---------- Anggota (CRUD) ----------
@app.route("/anggota", methods=["GET","POST"])
@login_required
def anggota():
    conn = get_db_connection()
    if request.method == "POST":
        nama = request.form["nama"].strip()
        jabatan = request.form["jabatan"].strip()
        if nama and jabatan:
            conn.execute("INSERT INTO anggota (nama, jabatan) VALUES (?,?)", (nama, jabatan))
            conn.commit()
            flash("Anggota ditambahkan.", "success")
        else:
            flash("Nama dan jabatan wajib diisi.", "danger")
    anggota_list = conn.execute("SELECT * FROM anggota ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("anggota.html", anggota_list=anggota_list)

@app.route("/anggota/tambah", methods=["GET", "POST"])
@login_required
def anggota_tambah():
    if request.method == "POST":
        nama = request.form["nama"].strip()
        jabatan = request.form["jabatan"].strip()
        if nama and jabatan:
            conn = get_db_connection()
            conn.execute("INSERT INTO anggota (nama, jabatan) VALUES (?, ?)", (nama, jabatan))
            conn.commit()
            conn.close()
            flash("Anggota baru berhasil ditambahkan.", "success")
            return redirect(url_for("anggota"))
        else:
            flash("Nama dan jabatan wajib diisi.", "danger")
    return render_template("anggota_tambah.html")

@app.route("/anggota/<int:id>/edit", methods=["GET", "POST"])
@login_required
def anggota_edit(id):
    conn = get_db_connection()
    anggota = conn.execute("SELECT * FROM anggota WHERE id=?", (id,)).fetchone()

    if not anggota:
        flash("Anggota tidak ditemukan.", "danger")
        return redirect(url_for("anggota"))

    if request.method == "POST":
        nama = request.form["nama"].strip()
        kelas = request.form["kelas"].strip()
        jabatan = request.form["jabatan"].strip()

        if nama and kelas and jabatan:
            conn.execute(
                "UPDATE anggota SET nama=?, kelas=?, jabatan=? WHERE id=?",
                (nama, kelas, jabatan, id)
            )
            conn.commit()
            conn.close()
            flash("Data anggota berhasil diperbarui.", "success")
            return redirect(url_for("anggota"))
        else:
            flash("Semua field wajib diisi.", "danger")

    conn.close()
    return render_template("anggota_edit.html", data=anggota)

@app.route("/anggota/<int:id>/hapus", methods=["GET", "POST"])
@login_required
def anggota_hapus(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM anggota WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Anggota dihapus.", "info")
    return redirect(url_for("anggota"))

@app.route("/anggota")
@login_required
def anggota_list():
    conn = get_db_connection()
    anggota_list = conn.execute("SELECT * FROM anggota").fetchall()
    conn.close()
    return redirect(url_for("anggota_list"))

@app.route("/anggota/<int:id>/kehadiran/<status>")
@login_required
def set_kehadiran(id, status):
    conn = get_db_connection()
    conn.execute("UPDATE anggota SET kehadiran = ? WHERE id = ?", (status, id))
    conn.commit()
    conn.close()
    flash(f"Kehadiran anggota diubah menjadi {status}.", "success")
    return redirect(url_for("anggota_list"))

# ---------- Kegiatan (CRUD) ----------
@app.route("/kegiatan", methods=["GET","POST"])
@login_required
def kegiatan():
    conn = get_db_connection()
    if request.method == "POST":
        nama_kegiatan = request.form["nama_kegiatan"].strip()
        tanggal = request.form["tanggal"].strip()
        if nama_kegiatan and tanggal:
            conn.execute("INSERT INTO kegiatan (nama_kegiatan, tanggal) VALUES (?,?)", (nama_kegiatan, tanggal))
            conn.commit()
            flash("Kegiatan ditambahkan.", "success")
        else:
            flash("Nama kegiatan dan tanggal wajib diisi.", "danger")
    kegiatan_list = conn.execute("SELECT * FROM kegiatan ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("kegiatan.html", kegiatan_list=kegiatan_list)

@app.route("/tambah_kegiatan", methods=["GET", "POST"])
def tambah_kegiatan():
    if request.method == "POST":
        nama = request.form["nama"]
        tanggal = request.form["tanggal"]
        keterangan = request.form["keterangan"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO kegiatan (nama, tanggal, keterangan) VALUES (?, ?, ?)",
            (nama, tanggal, keterangan)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("kegiatan"))

    return render_template("tambah_kegiatan.html")

@app.route("/edit_kegiatan/<int:id>", methods=["GET", "POST"])
def edit_kegiatan(id):
    conn = get_db_connection()
    k = conn.execute("SELECT * FROM kegiatan WHERE id = ?", (id,)).fetchone()
    if request.method == "POST":
        nama = request.form["nama"]
        tanggal = request.form["tanggal"]
        keterangan = request.form["keterangan"]
        conn.execute(
            "UPDATE kegiatan SET nama = ?, tanggal = ?, keterangan = ? WHERE id = ?",
            (nama, tanggal, keterangan, id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("kegiatan"))
    conn.close()
    return render_template("edit_kegiatan.html", kegiatan=k)

@app.route("/kegiatan/<int:id>/hapus", methods=["POST"])
@login_required
def kegiatan_hapus(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM kegiatan WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Kegiatan dihapus.", "info")
    return redirect(url_for("kegiatan"))

# ---------- Surat (CRUD) ----------
@app.route("/surat", methods=["GET","POST"])
@login_required
def surat():
    conn = get_db_connection()
    if request.method == "POST":
        perihal = request.form["perihal"].strip()
        tanggal = request.form["tanggal"].strip()
        if perihal and tanggal:
            conn.execute("INSERT INTO surat (perihal, tanggal) VALUES (?,?)", (perihal, tanggal))
            conn.commit()
            flash("Surat ditambahkan.", "success")
        else:
            flash("Perihal dan tanggal wajib diisi.", "danger")
    surat_list = conn.execute("SELECT * FROM surat ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("surat.html", surat_list=surat_list)

@app.route("/tambah_surat", methods=["GET", "POST"])
def tambah_surat():
    if request.method == "POST":
        nomor_surat = request.form["nomor_surat"]
        tanggal = request.form["tanggal"]
        perihal = request.form["perihal"]
        keterangan = request.form["keterangan"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO surat (nomor_surat, tanggal, perihal, keterangan) VALUES (?, ?, ?, ?)",
            (nomor_surat, tanggal, perihal, keterangan))
        conn.commit()
        conn.close()
        return redirect(url_for("surat"))
    return render_template("tambah_surat.html")

@app.route("/surat/<int:id>/edit", methods=["GET","POST"])
@login_required
def surat_edit(id):
    conn = get_db_connection()
    data = conn.execute("SELECT * FROM surat WHERE id=?", (id,)).fetchone()
    if not data:
        conn.close()
        flash("Data surat tidak ditemukan.", "danger")
        return redirect(url_for("surat"))
    if request.method == "POST":
        perihal = request.form["perihal"].strip()
        tanggal = request.form["tanggal"].strip()
        if perihal and tanggal:
            conn.execute("UPDATE surat SET perihal=?, tanggal=? WHERE id=?", (perihal, tanggal, id))
            conn.commit()
            conn.close()
            flash("Surat diperbarui.", "success")
            return redirect(url_for("surat"))
        flash("Perihal dan tanggal wajib diisi.", "danger")
    conn.close()
    return render_template("surat_edit.html", data=data)

@app.route("/surat/<int:id>/hapus", methods=["POST"])
@login_required
def surat_hapus(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM surat WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Surat dihapus.", "info")
    return redirect(url_for("surat"))

# ---------- Run ----------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8035, debug=True)
