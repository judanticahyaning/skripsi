from flask import render_template, request, url_for, redirect
import nltk
from nltk.util import ngrams
import re
from nltk.tokenize import sent_tokenize, word_tokenize
from flask import jsonify
# from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import pandas as pd
from .model import db, pertanyaan, kbbi, kamus
# from pandas.io import sql
from sqlalchemy import create_engine
from app import app
from flask_login import login_required,current_user

@app.route('/beranda_admin')
@login_required
def beranda_admin():
  return render_template("admin/index.html", admin=current_user)

@app.route('/daftar_pertanyaan')
@login_required
def daftar_pertanyaan():
  # cur = mysql.connection.cursor()
  # cur.execute("SELECT * FROM pertanyaan")
  # data = cur.fetchall()
  # cur.close()

  # return render_template("daftar_pertanyaan.html", tanya = data)
  listpertanyaan = pertanyaan.query.all()
  return render_template("admin/daftar_pertanyaan.html", tanya=listpertanyaan, admin=current_user)

@app.route('/tambah_pertanyaan', methods = ['POST'])
@login_required
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
@login_required
def lihat_pertanyaan():
  return redirect(url_for('daftar_pertanyaan'))

@app.route('/edit_pertanyaan', methods = ['POST'])
@login_required
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
@login_required
def hapus_pertanyaan(id_pertanyaan):
  # cur = mysql.connection.cursor()
  # cur.execute("DELETE FROM pertanyaan WHERE id_pertanyaan=%s", (id_pertanyaan,))
  # mysql.connection.commit()
  hapus = pertanyaan.query.filter_by(id_pertanyaan=id_pertanyaan).first()
  db.session.delete(hapus)
  db.session.commit()
  return redirect(url_for('daftar_pertanyaan'))

@app.route('/responden')
@login_required
def responden():
    # list_responden = responden.query.all()
    engine = create_engine("mysql+mysqlconnector://root@localhost:3306/tugas_akhir", echo=False)
    list_responden = engine.execute("SELECT * FROM akun WHERE NOT privileges='admin'").fetchall()
    list_jawaban = engine.execute(
        "SELECT jawaban.id_jawaban, akun.nama, pertanyaan.pertanyaan, jawaban.jawaban, jawaban.rekomendasi, jawaban.nilai FROM jawaban "
        "INNER JOIN akun ON akun.id=jawaban.id_responden "
        "INNER JOIN pertanyaan ON pertanyaan.id_pertanyaan=jawaban.id_pertanyaan").fetchall()
    return render_template('admin/responden.html', list_responden=list_responden, list_jawaban=list_jawaban, admin=current_user)

@app.route('/tambah_responden', methods = ['POST'])
@login_required
def tambah_responden():
  if request.method == "POST":
    nama = request.form['nama']
    jenis_kelamin =  request.form['optradio']
    engine = create_engine("mysql+mysqlconnector://root@localhost:3306/tugas_akhir", echo=False)
    sql = "INSERT INTO responden(nama, jenis_kelamin) VALUES (%s, %s)"
    data = (nama, jenis_kelamin)
    proses = engine.execute(sql,data)
    return redirect(url_for('responden'))

@app.route('/lihat_responden')
@login_required
def lihat_responden():
  return redirect(url_for('responden'))

@app.route('/edit_responden', methods = ['POST'])
@login_required
def edit_responden():
  if request.method == "POST":
    id = request.form['id']
    new_nama = request.form['edit_nama']
    new_jenis_kelamin = request.form['optradio']
    engine = create_engine("mysql+mysqlconnector://root@localhost:3306/tugas_akhir", echo=False)
    sql = engine.execute("UPDATE responden SET nama=%s, jenis_kelamin=%s WHERE id=%s",(new_nama, new_jenis_kelamin, id))
    return redirect(url_for('responden'))

@app.route('/hapus_responden/<string:id>', methods = ['POST','GET'])
@login_required
def hapus_responden(id):
  engine = create_engine("mysql+mysqlconnector://root@localhost:3306/tugas_akhir", echo=False)
  sql = engine.execute("DELETE FROM responden WHERE id="+id)
  return redirect(url_for('responden'))

@app.route('/kamus_kata')
@login_required
def kamus_kata():
  # cur = mysql.connection.cursor()
  # cur.execute("SELECT * FROM kbbi")
  # data = cur.fetchall()
  # cur.close()
  listkata = kamus.query.all()
  return render_template("admin/kamus_kata.html", kata=listkata, admin=current_user)
  # return render_template("kamus_kata.html")

@app.route('/korpus_ngram')
@login_required
def korpus_ngram():
  engine = create_engine("mysql+mysqlconnector://root@localhost:3306/tugas_akhir", echo=False)
  list_unigram = engine.execute("SELECT * FROM unigrams ").fetchall()
  list_bigram = engine.execute("SELECT * FROM bigrams ").fetchall()
  list_trigram = engine.execute("SELECT * FROM trigrams").fetchall()
  return render_template("admin/korpus_ngram.html", unigram=list_unigram, bigram=list_bigram, trigram=list_trigram, admin=current_user)

@app.route('/kbbi_ngram')
@login_required
def kbbi_ngram():
  engine = create_engine("mysql+mysqlconnector://root@localhost:3306/tugas_akhir", echo=False)
  list_unigram = engine.execute("SELECT * FROM unigram ").fetchall()
  list_bigram = engine.execute("SELECT * FROM bigram ").fetchall()
  list_trigram = engine.execute("SELECT * FROM trigram").fetchall()
  return render_template("admin/kbbi_ngram.html", unigram=list_unigram, bigram=list_bigram, trigram=list_trigram, admin=current_user)

@app.route('/tambah_korpus_ngram', methods=['POST'])
@login_required
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
      # teks = teks.strip()
      teks = " ".join(teks.split())
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
    df_unigram = pd.DataFrame(list(freq_unigram.items()), columns=["Unigrams", "Kemunculan"])
    df_unigram.to_sql(con=engine, name='unigrams', if_exists='append', index=False)

    #bigram
    bigram_db = []
    bigram_db.append(list(freq_bigram.items()))
    df_bigram = pd.DataFrame(list(freq_bigram.items()), columns=["Bigrams", "Kemunculan"])
    df_bigram.to_sql(con=engine, name='bigrams', if_exists='append', index=False)

    #trigram
    trigram_db = []
    trigram_db.append(list(freq_trigram.items()))
    df_trigram = pd.DataFrame(list(freq_trigram.items()), columns=["Trigrams", "Kemunculan"])
    df_trigram.to_sql(con=engine, name='trigrams', if_exists='append', index=False)

    # connect = db.raw_connection()
    # sql.write_frame(df_unigram, con=db, name='unigram', if_exists='append', flavor='mysql')
  # return jsonify("berhasil")
  #return render_template("korpus_ngram.html", data=unigram)
  return redirect(url_for('korpus_ngram'))

@app.route('/tentang_admin')
@login_required
def tentang_admin():
  return render_template('admin/tentang.html', admin=current_user)

@app.route('/profil_admin' )
@login_required
def profil_admin():
    # pengguna = akun.query.filter_by(username=username).first()
    return render_template('admin/profil.html', admin=current_user)


