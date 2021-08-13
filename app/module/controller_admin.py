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
  list_unigram = engine.execute("SELECT * FROM unigram").fetchall()
  list_bigram = engine.execute("SELECT * FROM bigram").fetchall()
  list_trigram = engine.execute("SELECT * FROM trigram").fetchall()
  return render_template("admin/korpus_ngram.html", unigram=list_unigram, bigram=list_bigram, trigram=list_trigram, admin=current_user)

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

@app.route('/tentang_admin')
@login_required
def tentang_admin():
  return render_template('admin/tentang.html', admin=current_user)

@app.route('/profil_admin' )
@login_required
def profil_admin():
    # pengguna = akun.query.filter_by(username=username).first()
    return render_template('admin/profil.html', admin=current_user)


