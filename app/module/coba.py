import math
from sqlalchemy.dialects.sqlite import json
from sqlalchemy.orm import sessionmaker
from app import app
from flask import render_template, request, url_for, redirect
from nltk.tokenize import sent_tokenize, word_tokenize
import re
from flask_login import login_required,current_user
from flask import jsonify
from .model import db, pertanyaan, kbbi, akun, kamus, unigram, bigram, trigram
from sqlalchemy import literal, select
from sqlalchemy import create_engine
from .model import db, pertanyaan, kbbi, akun
from math import floor
from collections import namedtuple
import pandas as pd
import json
from operator import itemgetter
import nltk
nltk.download('stopwords')
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory, StopWordRemover, ArrayDictionary


@app.route('/beranda_user')
@login_required
def beranda_user():
  return render_template("user/beranda.html", user=current_user)

def jaro_distance(s1, s2):
    # apabila s1 sama dengan s2, similarity =1
    if (s1 == s2):
      return 1.0

    # hitung panjang di setiap stringnya
    len_s1 = len(s1)
    len_s2 = len(s2)

    if (len_s1 == 0 or len_s2 == 0):
      return 0.0

    # jarak teoritis, dibulatkan ke bawah
    jarak_teoritis = (max(len_s1, len_s2) // 2) - 1

    # deklarasi array hash untuk persamaan string
    m_s1 = [0] * len_s1
    m_s2 = [0] * len_s2

    # menghitung karakter yang sama
    m = 0
    for i in range(len_s1):
      mulai = max(0, i - jarak_teoritis)
      selesai = min(i + jarak_teoritis + 1, len_s2)
      for j in range(mulai, selesai):
        if (s1[i] == s2[j] and m_s2[j] == 0):
          m_s1[i] = 1
          m_s2[j] = 1
          m += 1
          break

    # jika tidak ada kesamaan
    if (m == 0):  # contohnya kayak moving dengan ab
      return 0.0

    # perhitungan transposisi
    t = 0
    k = 0
    for i in range(len_s1):
      # apabila nilai hash string 1 bernilai true maka kondisi di if dikerjakan
      # jika tidak, lewati if
      if (m_s1[i]):
        # apabila hash di s2 bernilai false maka k++ utk geser ke k selanjutnya
        while (m_s2[k] == 0):
          k += 1
        # apabila nilai hash s2 tidak sama dengan 0 atau bernilai true
        # maka dilanjutkan dengan mencari kesamaan di string 1 dan beda posisi
        if (s1[i] != s2[k]):
          k += 1
          t += 1
        else:
          k += 1
    dj = (m / len_s1 + m / len_s2 + (m - (t / 2)) / m) / 3.0
    return dj

def jaro_winkler(s1, s2):
  jaro_dist = jaro_distance(s1, s2)
  prefix = 0
  # untuk mencari nilai prefix
  for i in range(min(len(s1), len(s2))):
    if (s1[i] == s2[i]):
      prefix += 1
    else:
      break

  # maksimum prefix yaitu 4 karakter
  prefix = min(4, prefix)

  jaro_dist += 0.1 * prefix * (1 - jaro_dist)
  return jaro_dist

def preprocessing (jawaban):
    # case folding
    jawaban = jawaban.lower()
    # tokenisasi kalimat
    jawaban = sent_tokenize(jawaban)
    # filtering
    str = []
    for i in jawaban:
        jawaban = re.sub(r'\d+', '', i)
        jawaban = re.sub(r'[^\w\s]', '', jawaban)
        # jawaban = jawaban.strip()
        jawaban = " ".join(jawaban.split())
        str.append(jawaban)
    # tokenisasi kata
    token = []
    for kalimat in str:
        token_kata = word_tokenize(kalimat)
        token_kata.insert(0, "_")
        token_kata.insert(len(kalimat), "_")
        for kata in token_kata:
            token.append(kata)
    return token

def buat_unigram(result):
    unigram = []
    for i in range(len(result)):
        # key = result[i+1]
        for j in result[i]:
            if (j == "_"):
                continue
            unigram.append([j, 0])
    return unigram

def buat_bigram_kiri(token, result):
    bigram_kiri = []
    for i in range(len(token) - 1):
        #     print(token[i])
        for k in result[i + 1]:
            if (k == "_"):
                continue
            key = token[i] + " " + k
            bigram_kiri.append([key, 0])
    return bigram_kiri

def buat_bigram_kanan(token, result):
    bigram_kanan = []
    for i in range(2, len(token)):
        for j in result[i - 1]:
            if (token[i] == "_" and j == "_"):
                continue
            if (j == "_"):
                continue
            key = j + " " + token[i]
            bigram_kanan.append([key, 0])
    return bigram_kanan

def buat_trigram(token, result):
    trigram = []
    for i in range(len(token) - 2):
        for k in result[i + 1]:
            if (token[i] == "_" and k == "_"):
                continue
            if (k == "_" and token[i + 2] == "_"):
                continue
            key = token[i] + " " + k + " " + token[i + 2]
            trigram.append([key, 0])
    return trigram

def kemunculan_unigram(r_unigram, unigram):
    muncul_unigram = []
    for i in r_unigram:
        kata = i[0]
        for j in unigram:
            if kata==j[0]:
                j[1]=i[1]
    return unigram

def kemunculan_bigram_kiri(r_bigram_kiri, bigram_kiri):
    for i in r_bigram_kiri:
        kata = i[0]
        if kata in bigram_kiri:
            bigram_kiri[kata] = i[1]
    return bigram_kiri

def kemunculan_bigram_kanan(r_bigram_kiri, bigram_kanan):
    for i in r_bigram_kiri:
        kata = i[0]
        if kata in bigram_kanan:
            bigram_kanan[kata] = i[1]
    return bigram_kanan

def kemunculan_trigram(r_trigram, trigram):
    for i in r_trigram:
        kata = i[0]
        if kata in trigram:
            trigram[kata] = i[1]
    return trigram

def total_unigram(result, unigram):
    index_token = 1
    total = 0
    length = len(result[index_token])
    list_total = []
    for index, (kata, value) in enumerate(unigram):
        # print(index, kata, value)
        if index == 0:
            continue
        if index == len(unigram) - 1:
            break
        if index == length:
            total += value
            list_total.append(total)
            index_token += 1
            length += len(result[index_token])
            total = 0
            continue
            # print(total)

        total += value
        # print(total)
    return list_total

def total_bigram_kiri(result, bigram_kiri):
    index_token = 1
    total = 0
    length = len(result[index_token])
    list_total = []

    for index, (key, value) in enumerate(bigram_kiri.items()):
        if index == len(bigram_kiri) - 1:
            # print(key, value)
            list_total.append(total)

        if index == length:
            # print(key,value)
            list_total.append(total)
            index_token += 1
            length += len(result[index_token])
            total = 0

        total += value
    return list_total

def total_bigram_kanan(result, bigram_kanan):
    index_token = 1
    total = 0
    length = len(result[index_token])
    list_total = []

    for index, (key, value) in enumerate(bigram_kanan.items()):
        print(key, value)
        if index == len(bigram_kanan) - 1:
            list_total.append(total)

        if index == length:
            list_total.append(total)
            index_token += 1
            length += len(result[index_token])
            total = 0

        total += value
    return list_total

def total_trigram(result,trigram):
    index_token = 1
    total = 0
    length = len(result[index_token])
    list_total = []

    for index, (key, value) in enumerate(trigram.items()):
        if index == len(trigram) - 1:
            list_total.append(total)

        if index == length:
            list_total.append(total)
            index_token += 1
            length += len(result[index_token])
            total = 0

        total += value

    return list_total

def probabilitas_unigram(result, tot_unigram, unigram):
    index_token = 1
    length = len(result[index_token])
    list_pro = []
    index_tot = 0
    for index, (key, value) in enumerate(unigram):
        probabilitas = 0
        if index==0:
            continue
        elif index == len(unigram)-1:
            break
        elif index == length:
            total = tot_unigram[index_tot]
            if total == 0:
                probabilitas = 0.0
            else:
                probabilitas += value / total
            # list_pro.append([key, probabilitas])
            list_pro.append(probabilitas)
            index_token += 1
            index_tot += 1
            length += len(result[index_token])
            # print(index_tot)
        else:
            total = tot_unigram[index_tot]
            if total == 0:
                probabilitas = 0.0
            else:
                probabilitas += value / total
            # list_pro.append([key, probabilitas])
            list_pro.append(probabilitas)
            # print(key, value)
        # print(type(probabilitas))
    return list_pro

def probabilitas_bigram_kiri (result, tot_bigram_kiri, bigram_kiri):
    index_token = 1
    length = len(result[index_token])
    list_pro = []
    index_tot = 0
    for index, (key, value) in enumerate(bigram_kiri.items()):
        probabilitas = 0
        total = tot_bigram_kiri[index_tot]
        if index == length - 1:
            if total == 0:
                probabilitas = 0.0
            else:
                probabilitas += value / total
            list_pro.append(probabilitas)
            index_token += 1
            index_tot += 1
            length += len(result[index_token])
            # print(index_tot)
        else:
            if total == 0:
                probabilitas = 0.0
            else:
                probabilitas += value / total
            list_pro.append(probabilitas)
            # print(key, value)
    return list_pro

def probabilitas_bigram_kanan(result, tot_bigram_kanan, bigram_kanan):
    index_token = 1
    length = len(result[index_token])
    list_pro = []
    index_tot = 0
    for index, (key, value) in enumerate(bigram_kanan.items()):
        probabilitas = 0
        total = tot_bigram_kanan[index_tot]
        if index == length - 1:
            if total == 0:
                probabilitas = 0.0
            else:
                probabilitas += value / total
            list_pro.append(probabilitas)
            index_token += 1
            index_tot += 1
            length += len(result[index_token])
            # print(index_tot)
        else:
            if total == 0:
                probabilitas = 0.0
            else:
                probabilitas += value / total
            list_pro.append(probabilitas)
            # print(key, value)
    return list_pro

def probabilitas_trigram(result,tot_trigram, trigram):
    index_token = 1
    length = len(result[index_token])
    list_pro = []
    index_tot = 0
    for index, (key, value) in enumerate(trigram.items()):
        probabilitas = 0
        total = tot_trigram[index_tot]
        if index == length - 1:
            if total == 0:
                probabilitas = 0.0
            else:
                probabilitas += value / total
            list_pro.append(probabilitas)
            index_token += 1
            index_tot += 1
            length += len(result[index_token])
            # print(index_tot)
        else:
            if total == 0:
                probabilitas = 0.0
            else:
                probabilitas += value / total
            list_pro.append(probabilitas)
            # print(key, value)
    return list_pro

def mercer_bigram_kiri (result, bigram_kiri, pro_unigram, pro_bigram_kiri):
    index_token = 1
    length = len(result[index_token])
    list_smooth = []
    index_uni = 0
    index_bi_ki = 0
    for index, (key, value) in enumerate(bigram_kiri.items()):
        val_lambda = 0.1
        smooth = 0.0
        prob_uni = pro_unigram[index_uni]
        prob_bi_ki = pro_bigram_kiri[index_bi_ki]
        # if index == 0:
        #     continue
        if index == length - 1:
            # print(key, prob_uni)
            # print(key, prob_bi_ki)
            smooth += (val_lambda * prob_bi_ki) + (1 - val_lambda) * prob_uni
            # list_smooth.append([key, smooth])
            list_smooth.append(smooth)
            index_token += 1
            length += len(result[index_token])
            # print(list_smooth)
        else:
            # print(key, prob_bi_ki)
            smooth += (val_lambda * prob_bi_ki) + (1 - val_lambda) * prob_uni
            list_smooth.append(smooth)
            # list_smooth.append([key, smooth])
            # print(key, value)
        index_uni += 1
        index_bi_ki += 1
    return list_smooth

def mercer_bigram_kanan(result, bigram_kanan, pro_unigram, pro_bigram_kanan):
    index_token = 1
    length = len(result[index_token])
    list_smooth = []
    index_uni = 0
    index_bi_ka = 0
    for index, (key, value) in enumerate(bigram_kanan.items()):
        val_lambda = 0.1
        smooth = 0.0
        prob_uni = pro_unigram[index_uni]
        prob_bi_ka = pro_bigram_kanan[index_bi_ka]
        # if index == 0:
        #     continue
        if index == length - 1:
            # print(key, prob_uni)
            # print(key, prob_bi_ki)
            smooth += (val_lambda * prob_bi_ka) + (1 - val_lambda) * prob_uni
            list_smooth.append(smooth)
            index_token += 1
            length += len(result[index_token])
            # print(list_smooth)
        else:
            # print(key, prob_bi_ki)
            smooth += (val_lambda * prob_bi_ka) + (1 - val_lambda) * prob_uni
            list_smooth.append(smooth)
            # print(key, value)
        index_uni += 1
        index_bi_ka += 1
    return list_smooth

def mercer_trigram(result, trigram, pro_bigram_kiri, pro_bigram_kanan, pro_trigram):
    index_token = 1
    length = len(result[index_token])
    list_smooth = []
    index_bi_ka = 0
    index_bi_ki = 0
    index_tri = 0
    for index, (key, value) in enumerate(trigram.items()):
        val_lambda = 0.1
        smooth = 0.0
        prob_bi_ki = pro_bigram_kiri[index_bi_ki]
        prob_bi_ka = pro_bigram_kanan[index_bi_ka]
        prob_trigram = pro_trigram[index_tri]
        if index == length:
            print(key, value)
            smooth += (val_lambda * prob_trigram) + ((1 - val_lambda) * ((prob_bi_ki + prob_bi_ka) / 2))
            list_smooth.append(smooth)
        elif index == length - 1:
            print(key, value)
            smooth += (val_lambda * prob_trigram) + ((1 - val_lambda) * ((prob_bi_ki + prob_bi_ka) / 2))
            list_smooth.append(smooth)
            index_token += 1
            length += len(result[index_token])
            # print(list_smooth)
        else:
            # print(key, prob_bi_ki)
            smooth += (val_lambda * prob_trigram) + ((1 - val_lambda) * ((prob_bi_ki + prob_bi_ka) / 2))
            list_smooth.append(smooth)
            # print(key, value)
        index_bi_ki += 1
        index_bi_ka += 1
        index_tri += 1
    return list_smooth

def hitung_skor(result, jelinek_kiri, jelinek_kanan, jelinek_trigram):
    index_mer_ki = 0
    index_mer_ka = 0
    index_tri = 0
    list_skor = []
    for i in result:
        if i == 0:
            continue
        if i == len(result) - 1:
            break
        for j, value in enumerate(result[i]):
            lam_satu_dua = 0.25
            lam_tiga = 0.5
            skor = 0.0
            prob_mer_ki = jelinek_kiri[index_mer_ki]
            prob_mer_ka = jelinek_kanan[index_mer_ka]
            prob_mer_tri = jelinek_trigram[index_tri]
            skor += ((lam_satu_dua * prob_mer_ki) + (lam_satu_dua * prob_mer_ka) + (lam_tiga * prob_mer_tri))
            list_skor.append([value, skor])
            index_mer_ki += 1
            index_mer_ka += 1
            index_tri += 1
    return list_skor

def skor_ranking(result, skor_kata):
    index_skor = 0
    ranking = []
    temp = []
    for i in result:
        if i == 0:
            continue
        if i == len(result) - 1:
            break
        for j, value in enumerate(result[i]):
            skor = skor_kata[index_skor]
            temp.append(skor)
            if (j == len(result[i]) - 1):
                rank = sorted(temp, key=itemgetter(1), reverse=True)
                # maks =max(temp, key=itemgetter(1))
                ranking.append(rank)
                temp.clear()
            index_skor += 1
            # print(ranking[1])

    # rekomen = []
    # for i in ranking:
    #     rekomen.append(i[0])
    return ranking

@app.route('/deteksi_koreksi')
@login_required
def deteksi_koreksi():
    listpertanyaan = pertanyaan.query.all()
    return render_template('user/deteksi_koreksi.html', tanya=listpertanyaan,user=current_user)

@app.route('/proses_deteksi_koreksi', methods = ['POST'])
@login_required
def proses_deteksi_koreksi():
    if request.method == "POST":
        # ambil nilai dari form html
        jawaban = request.form['jawaban']
        # preprocessing
        token = preprocessing(jawaban)

        # ubah list token_kata ke dict
        # token = {v: k for v, k in enumerate(token_kata)}

        # perhitungan jarak token dengan kata kamus dgn jaro winkler
        engine = create_engine("mysql+mysqlconnector://root@localhost:3306/tugas_akhir", echo=False)
        result = {0: "_"}
        # result = {}
        sql = engine.execute("SELECT DISTINCT kata FROM kamus").fetchall()
        hasil = [row[0] for row in sql]
        for i in range(len(token)):
            temp = []
            s1 = token[i]
            for j in hasil:
                jaro = jaro_winkler(s1, j)
                if (jaro >= 0.9):
                    temp.append(j)
                    result[i] = temp
        # panjang result 167
        result[i] = "_"
        # return jsonify(token, result)

        # pembuatan korpus n-gram
        unigram = buat_unigram(result) # panjang 164
        bigram_kiri = buat_bigram_kiri(token, result)
        # bigram_kanan = buat_bigram_kanan(token, result)
        trigram = buat_trigram(token, result)
        bigram_kanan = {}
        return jsonify(unigram, bigram_kiri, bigram_kanan)


        # hitung jumlah kemunculan masing-masing n-gram
        r_unigram = []
        uni = engine.execute("SELECT unigram, CAST(SUM(jumlah_kemunculan) AS int) FROM unigram GROUP BY unigram")
        for row in uni:
            r_unigram.append(list(row))
        unigram = kemunculan_unigram(r_unigram, unigram)

        # bigram kiri
        r_bigram_kiri = []
        kiri = engine.execute("SELECT bigram, CAST(SUM(jumlah_kemunculan) AS int) FROM bigram GROUP BY bigram")
        for row in kiri:
            r_bigram_kiri.append(list(row))
        bigram_kiri = kemunculan_bigram_kiri(r_bigram_kiri,bigram_kiri)

        # bigram kanan
        bigram_kanan = kemunculan_bigram_kanan(r_bigram_kiri, bigram_kanan)

        # trigram
        r_trigram = []
        tri = engine.execute("SELECT trigram, CAST(SUM(jumlah_kemunculan) AS int) FROM trigram GROUP BY trigram")
        for row in tri:
            r_trigram.append(list(row))

        trigram = kemunculan_trigram(r_trigram, trigram)
        # return jsonify(unigram, bigram_kiri, bigram_kanan, trigram)

        # hitung total kemunculan
        tot_unigram = total_unigram(result, unigram)
        tot_bigram_kiri = total_bigram_kiri(result, bigram_kiri)
        tot_bigram_kanan = total_bigram_kanan(result, bigram_kanan)
        tot_trigram = total_trigram(result, trigram)
        # print(len(tot_unigram))

        # print(len(result),len(unigram), len(bigram_kiri), len(bigram_kanan), len(trigram))

        # return jsonify(tot_unigram, tot_bigram_kiri, tot_bigram_kanan, tot_trigram)
        # hitung probabilitas
        pro_unigram = probabilitas_unigram(result, tot_unigram, unigram)
        pro_bigram_kiri = probabilitas_bigram_kiri(result, tot_bigram_kiri, bigram_kiri)
        pro_bigram_kanan = probabilitas_bigram_kanan(result, tot_bigram_kanan, bigram_kanan)
        pro_trigram = probabilitas_trigram (result, tot_trigram, trigram)
        # print(len(pro_unigram), len(pro_bigram_kiri), len(pro_bigram_kanan), len(pro_trigram))
        # return jsonify(tot_bigram_kanan,pro_bigram_kanan)

        # hitung smoothing jelinek mercer
        jelinek_kiri = mercer_bigram_kiri(result, bigram_kiri, pro_unigram, pro_bigram_kiri)
        jelinek_kanan = mercer_bigram_kanan (result, bigram_kanan, pro_unigram, pro_bigram_kanan)
        jelinek_trigram = mercer_trigram (result, trigram, pro_bigram_kiri, pro_bigram_kanan, pro_trigram)
        # print(len(jelinek_kiri), len(jelinek_kanan), len(jelinek_trigram))

        # hitung skor
        skor_kata = hitung_skor(result, jelinek_kiri, jelinek_kanan, jelinek_trigram)

        # peringkatan
        rank_skor = skor_ranking(result, skor_kata)

        # ubah jawaban jadi token tanpa underscore
        list_jawab = list(jawaban.split())

        # replace input jawaban dengan rekomendasi
        new = []
        index_rekomen = 0
        for i in list_jawab:
            if (i!=rank_skor[index_rekomen]):
                new.append(i.replace(i,rank_skor[index_rekomen]))
            else:
                new.append(rank_skor[index_rekomen])
            index_rekomen += 1
        # ubah rekomendasi ke str
        listtostr = ' '.join([str(elem) for elem in new])

        # return jsonify(listtostr)
        # return redirect(url_for('deteksi_koreksi', jawaban=jawaban))
        # return render_template('user/hasil.html', jawaban=jawaban, rekomendasi=listtostr)

@app.route('/hasil')
@login_required
def hasil():
  return render_template('user/hasil.html', user=current_user)

@app.route('/tentang_user')
@login_required
def tentang_user():
  return render_template('user/tentang.html', user=current_user)

@app.route('/profil_user' )
@login_required
def profil_user():
    # pengguna = akun.query.filter_by(username=username).first()
    return render_template('user/profil.html', user=current_user)

def prepro_scoring(a):
    stopwords = nltk.corpus.stopwords.words('indonesian')
    new_words = ('lagipula', 'akibatnya', 'biar', 'biarpun', 'dll', 'dsb', 'dst', 'kecuali'
                 , 'selagi', 'dimana')
    for i in new_words:
        stopwords.append(i)

    token = []
    a = sent_tokenize(a)
    for i in a:
        a = re.sub(r'[^\w\s]', '', i)
        a = word_tokenize(a)
        for kata in a:
            if kata not in stopwords:
                token.append(kata)
    return token

@app.route('/proses_coba_penilaian', methods = ['POST'])
@login_required
def proses_coba_penilaian():
    if request.method == "POST":
        # ambil nilai dari form html
        pertanyaan = request.form['pertanyaan']
        jawab_old = request.form['jawab']
        engine = create_engine("mysql+mysqlconnector://root@localhost:3306/tugas_akhir", echo=False)
        sql = engine.execute("SELECT kunci_jawaban FROM pertanyaan WHERE id_pertanyaan="+pertanyaan).fetchall()
        kunci = [row[0] for row in sql]
        n = len([kunci, jawab_old])

        # case folding
        jawaban = jawab_old.lower()
        for i in kunci:
            kunci = i.lower()

        prepro_kunci = prepro_scoring(kunci)
        prepro_jawaban = prepro_scoring(jawaban)

        # menggabungkan + isi default 0
        set_kata = set(prepro_kunci).union(set(prepro_jawaban))
        katadictkunci = dict.fromkeys(set_kata, 0)
        katadictjawaban = dict.fromkeys(set_kata, 0)

        # jika term terdapat di dokumen beri nilai 1, jika tidak beri nilai 0
        for i in prepro_kunci:
            katadictkunci[i] = 1
        for kata in prepro_jawaban:
            katadictjawaban[kata] = 1

        # hitung df
        df = {}
        for key, value in katadictkunci.items():
            if key in df:
                df[key] += value
            else:
                df[key] = value

        for key, value in katadictjawaban.items():
            if key in df:
                df[key] += value
            else:
                df[key] = value

        # hitung idfi
        idfi = {}
        for key, value in df.items():
            idfi[key] = math.log10(n/value)+1

        # hitung bobot
        bobot_kunci = {}
        for key, value in katadictkunci.items():
            if key in idfi:
                bobot_kunci[key] = value * idfi[key]

        bobot_jawab = {}
        for key, value in katadictjawaban.items():
            #     print(key, value)
            if key in idfi:
                bobot_jawab[key] = value * idfi[key]

        # hitung jarak
        list_jarak_kunci = []
        jarak = 0
        for index, (key, value) in enumerate(bobot_kunci.items()):
            jarak += pow(value, 2)
            print(index, value, jarak)
            if (index == len(bobot_kunci) - 1):
                hasil = math.sqrt(jarak)
                list_jarak_kunci.append(hasil)

        list_jarak_jawab = []
        jarak = 0
        for index, (key, value) in enumerate(bobot_jawab.items()):
            jarak += pow(value, 2)
            print(value, jarak)
            if (index == len(bobot_jawab) - 1):
                hasil = math.sqrt(jarak)
                list_jarak_jawab.append(hasil)

        # kunci*jawab
        list_total = []
        total = 0
        kali_bobot = {key: value * bobot_jawab[key] for key, value in bobot_kunci.items()}
        for index, (key, value) in enumerate(kali_bobot.items()):
            total += value
            if (index == len(kali_bobot) - 1):
                list_total.append(total)

        # similaritas + konversi nilai
        for total, kunci, jawab in zip(list_total, list_jarak_kunci, list_jarak_jawab):
            similaritas = total / (kunci * jawab)
            if (similaritas >= 0.01 and similaritas <= 0.10):
                value = 10
            elif (similaritas >= 0.11 and similaritas <= 0.20):
                value = 20
            elif (similaritas >= 0.21 and similaritas <= 0.30):
                value = 30
            elif (similaritas >= 0.31 and similaritas <= 0.40):
                value = 40
            elif (similaritas >= 0.41 and similaritas <= 0.50):
                value = 50
            elif (similaritas >= 0.51 and similaritas <= 0.60):
                value = 60
            elif (similaritas >= 0.61 and similaritas <= 0.70):
                value = 70
            elif (similaritas >= 0.71 and similaritas <= 0.80):
                value = 80
            elif (similaritas >= 0.81 and similaritas <= 0.90):
                value = 90
            else:
                value = 100

    # return jsonify(similaritas)
    return render_template('user/deteksi_koreksi.html', similaritas=similaritas, jawaban=jawab_old, value=value)