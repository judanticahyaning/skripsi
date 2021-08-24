from app import app
from flask import render_template, request, url_for, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from .model import akun,db
from flask_login import login_user, login_required, logout_user,current_user
from flask_admin import Admin
from flask import jsonify


@app.route('/', methods = ['GET', 'POST'])
def index():
  if request.method == "POST":
    nama_pengguna = request.form['nama_pengguna']
    kata_sandi = request.form['kata_sandi']
    cek = akun.query.filter_by(username=nama_pengguna).first()
    admin = akun.query.filter_by(username="admin").first()
    # if cek and akun.username=="admin":
    #   # login_user(admin, remember=True)
    #   return redirect(url_for('beranda_admin'))
    if cek:
      if check_password_hash(cek.password, kata_sandi):
        # flash("Berhasil Masuk", category='success')
        if cek.privileges == "admin":
          login_user(cek, remember=True)
          return redirect(url_for('beranda_admin'))
        else:
          login_user(cek, remember=True)
          return redirect(url_for('beranda_user'))
      else:
        flash("Kata Sandi Salah", category='error')
    else:
      flash('Nama Pengguna Belum Terdaftar', category='error')
    # return jsonify(login)
  return render_template('akun/index.html')

@app.route('/daftar')
def daftar():
  return render_template('akun/daftar.html')

@app.route('/daftar_akun', methods = ['POST'])
def daftar_akun():
  if request.method == "POST":
    nama_lengkap = request.form['nama_lengkap']
    jenis = request.form['optradio']
    nama_pengguna = request.form['nama_pengguna']
    kata_sandi = request.form['kata_sandi']
    privileges = request.form['privileges']
    cek_akun = akun.query.filter_by(username=nama_pengguna).first()
    if cek_akun:
      flash("Nama Pengguna sudah ada", category='error')
      return redirect(url_for('daftar'))
    elif len(nama_pengguna) < 4 :
      flash("Nama Pengguna harus lebih dari 4 karakter", category='error')
      return redirect(url_for('daftar'))
    elif len(nama_lengkap) < 2:
      flash("Nama lengkap harus lebih dari 2 karakter", category='error')
      return redirect(url_for('daftar'))
    elif len(kata_sandi) < 7:
      flash("Kata sandi minimal 7 karakter", category='error')
      return redirect(url_for('daftar'))
    else:
      #add user to database
      daftar_akun = akun(nama=nama_lengkap, jenis_kelamin=jenis, username=nama_pengguna, password=generate_password_hash(kata_sandi, method="sha256"), privileges=privileges)
      db.session.add(daftar_akun)
      db.session.commit()
      cek_akun = akun.query.filter_by(username=nama_pengguna).first()
      login_user(cek_akun, remember=True)
      # flash("Account created", category='success')
      return redirect(url_for('beranda_user'))
  return render_template('akun/daftar.html')

@app.route('/keluar')
@login_required
def keluar():
  logout_user()
  return redirect(url_for('index'))
