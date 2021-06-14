from flask import render_template, request, url_for, redirect
import nltk
from nltk.util import ngrams
import re
from nltk.tokenize import sent_tokenize, word_tokenize
from flask import jsonify
# from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import pandas as pd
from .model import db, pertanyaan, kbbi, akun
# from pandas.io import sql
from sqlalchemy import create_engine
from app import app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user

@app.route('/beranda_admin')
def beranda_admin():
  return render_template("admin/index.html")

@app.route('/kamus_kata')
def kamus_kata():
  # cur = mysql.connection.cursor()
  # cur.execute("SELECT * FROM kbbi")
  # data = cur.fetchall()
  # cur.close()
  listkata = kbbi.query.all()
  return render_template("admin/kamus_kata.html", kata=listkata)
  # return render_template("kamus_kata.html")

@app.route('/daftar_pertanyaan')
def daftar_pertanyaan():
  # cur = mysql.connection.cursor()
  # cur.execute("SELECT * FROM pertanyaan")
  # data = cur.fetchall()
  # cur.close()

  # return render_template("daftar_pertanyaan.html", tanya = data)
  listpertanyaan = pertanyaan.query.all()
  return render_template("admin/daftar_pertanyaan.html", tanya=listpertanyaan)

@app.route('/tambah_pertanyaan', methods = ['POST'])
def tambah_pertanyaan():
  if request.method == "POST":
    pertanyaans = request.form['pertanyaan']
    kunci_jawaban =  request.form['kunci_jawaban']
    # cur = mysql.connection.cursor()
    # cur.execute("INSERT INTO pertanyaan(pertanyaan, kunci_jawaban) VALUES (%s, %s)", (pertanyaan, kunci_jawaban))
    # mysql.connection.commit()
    tambah = pertanyaan(pertanyaan=pertanyaans, kunci_jawaban=kunci_jawaban)
    db.session.add(tambah)
    db.session.commit()
    return redirect(url_for('daftar_pertanyaan'))

@app.route('/lihat_pertanyaan')
def lihat_pertanyaan():
  return redirect(url_for('admin/daftar_pertanyaan'))

@app.route('/edit_pertanyaan', methods = ['POST'])
def edit_pertanyaan():
  if request.method == "POST":
    id_pertanyaan = request.form['id_pertanyaan']
    new_edit_pertanyaan = request.form['edit_pertanyaan']
    new_edit_kunci_jawaban = request.form['edit_kunci_jawaban']

    # cur = mysql.connection.cursor()
    # cur.execute("UPDATE pertanyaan SET pertanyaan=%s, kunci_jawaban=%s WHERE id_pertanyaan=%s", (edit_pertanyaan, edit_kunci_jawaban, id_pertanyaan))
    # mysql.connection.commit()
    edit = pertanyaan.query.filter_by(id_pertanyaan=id_pertanyaan).first()
    edit.pertanyaan = new_edit_pertanyaan
    edit.kunci_jawaban = new_edit_kunci_jawaban
    db.session.commit()
    return redirect(url_for('daftar_pertanyaan'))

@app.route('/hapus_pertanyaan/<string:id_pertanyaan>', methods = ['POST','GET'])
def hapus_pertanyaan(id_pertanyaan):
  # cur = mysql.connection.cursor()
  # cur.execute("DELETE FROM pertanyaan WHERE id_pertanyaan=%s", (id_pertanyaan,))
  # mysql.connection.commit()
  hapus = pertanyaan.query.filter_by(id_pertanyaan=id_pertanyaan).first()
  db.session.delete(hapus)
  db.session.commit()
  return redirect(url_for('daftar_pertanyaan'))

@app.route('/korpus_ngram')
def korpus_ngram():
  engine = create_engine("mysql+mysqlconnector://root@localhost:3306/tugas_akhir", echo=False)
  list_unigram = engine.execute("SELECT * FROM unigram").fetchall()
  list_bigram = engine.execute("SELECT * FROM bigram").fetchall()
  list_trigram = engine.execute("SELECT * FROM trigram").fetchall()
  return render_template("admin/korpus_ngram.html", unigram=list_unigram, bigram=list_bigram, trigram=list_trigram)

@app.route('/tambah_korpus_ngram', methods=['POST'])
def tambah_korpus_ngram():
  if request.method == "POST":
    # factory = StemmerFactory()
    # stemmer = factory.create_stemmer()
    teks = request.form['teks']
    teks = teks.lower()  # case folding
    # teks = stemmer.stem(teks)
    teks = sent_tokenize(teks)  # tokenisasi kalimat
    str = []
    for i in teks:  # filtering
      teks = re.sub(r'\d+', '', i)
      teks = re.sub(r'[^\w\s]', '', teks)
      teks = teks.strip()
      str.append(teks)
    unigram = []
    bigram = []
    trigram = []
    for kalimat in str: #tokenisasi kata
      teks = word_tokenize(kalimat)
      teks.insert(0, "_")
      teks.insert(len(kalimat), "_")
      for kata in teks:
        unigram.append(kata)
      bigram.extend(list(ngrams(teks, 2)))
      trigram.extend(list(ngrams(teks, 3)))
    bigram = [' '.join(gram) for gram in bigram]
    trigram = [' '.join(gram) for gram in trigram]
    freq_unigram = nltk.FreqDist(unigram) #hitung jumlah kemunculan
    freq_bigram = nltk.FreqDist(bigram)
    freq_trigram = nltk.FreqDist(trigram)

    engine = create_engine("mysql+mysqlconnector://root@localhost:3306/tugas_akhir", echo=False)
    #unigram
    unigram_db = []
    unigram_db.append(list(freq_unigram.items()))
    df_unigram = pd.DataFrame(list(freq_unigram.items()), columns=["Unigram", "Jumlah_Kemunculan"])
    df_unigram.to_sql(con=engine, name='unigram', if_exists='append', index=False)

    #bigram
    bigram_db = []
    bigram_db.append(list(freq_bigram.items()))
    df_bigram = pd.DataFrame(list(freq_bigram.items()), columns=["Bigram", "Jumlah_Kemunculan"])
    df_bigram.to_sql(con=engine, name='bigram', if_exists='append', index=False)

    #trigram
    trigram_db = []
    trigram_db.append(list(freq_trigram.items()))
    df_trigram = pd.DataFrame(list(freq_trigram.items()), columns=["Trigram", "Jumlah_Kemunculan"])
    df_trigram.to_sql(con=engine, name='trigram', if_exists='append', index=False)

    # connect = db.raw_connection()
    # sql.write_frame(df_unigram, con=db, name='unigram', if_exists='append', flavor='mysql')
  # return jsonify("berhasil")
  #return render_template("korpus_ngram.html", data=unigram)
  return redirect(url_for('korpus_ngram'))

@app.route('/masuk', methods = ['GET', 'POST'])
def masuk():
  if request.method == "POST":
    username = request.form['username']
    password = request.form['password']
    cek = akun.query.filter_by(username=username).first()
    if username == "admin":
      return redirect(url_for('index'))
    elif not cek:
      return redirect(url_for('daftar'))
    elif check_password_hash(cek.password, password):
      login_user(cek,remember=True)
      return redirect(url_for('index'))
    # elif not check_password_hash(cek.password, password):
    #     return jsonify("incorrect password")
    else:
      return jsonify("username doesn't exist")
  return render_template('akun/masuk.html')

@app.route('/daftar')
def daftar():
  return render_template('akun/daftar.html')

@app.route('/daftar_akun', methods = ['POST'])
def daftar_akun():
  if request.method == "POST":
    nama = request.form['nama']
    username = request.form['username']
    password = request.form['password1']
    cek_akun = akun.query.filter_by(username=username).first()
    if cek_akun:
      return redirect(url_for('daftar'))
    elif len(username) < 4 and len(username) > 15:
      pass
    elif len(nama) < 2:
      pass
    else:
      daftar_akun = akun(nama=nama, username=username, password=generate_password_hash(password, method="sha256"))
      db.session.add(daftar_akun)
      db.session.commit()
      return redirect(url_for('masuk'))

@app.route('/keluar')
def keluar():
  logout_user()
  return redirect(url_for('masuk'))

@app.route('/tentang_admin')
def tentang_admin():
  return render_template('admin/tentang.html')

