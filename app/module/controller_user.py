from app import app
from flask import render_template, request, url_for, redirect
from .model import db, pertanyaan, kbbi, akun

@app.route('/beranda_user')
def beranda_user():
  return render_template("user/beranda.html")

@app.route('/deteksi_koreksi')
def deteksi_koreksi():
  return render_template('user/deteksi_koreksi.html')

@app.route('/tentang_user')
def tentang_user():
  return render_template('user/tentang.html')
