from app import app
from flask import render_template, request, url_for, redirect
from flask_login import login_required,current_user
from flask import jsonify
from .model import db, pertanyaan, kbbi, kamus, responden
from .olah import *
from sqlalchemy import create_engine
from math import floor
from collections import namedtuple
from time import process_time
from itertools import chain

@app.route('/beranda_user')
@login_required
def beranda_user():
  return render_template("user/beranda.html", user=current_user)

def grup_kamus(kamus):
    # sort dan groupby => utk huruf depan token
    kms = {}
    util_func = lambda x: x[0]
    temp = sorted(kamus, key=util_func)
    for i, ele in groupby(temp, util_func):
        # print(ele)
        kms[i] = list(ele)
    return kms

@app.route('/deteksi_koreksi')
@login_required
def deteksi_koreksi():
    engine = create_engine("mysql+mysqlconnector://root@localhost:3306/tugas_akhir", echo=False)
    list_responden = engine.execute("SELECT * FROM responden").fetchall()
    listpertanyaan = pertanyaan.query.all()
    return render_template('user/deteksi_koreksi.html', tanya=listpertanyaan, list_responden=list_responden, user=current_user)

@app.route('/percobaan')
@login_required
def percobaan():
    engine = create_engine("mysql+mysqlconnector://root@localhost:3306/tugas_akhir", echo=False)
    listpertanyaan = engine.execute("SELECT * FROM pertanyaan").fetchall()
    # listpertanyaan = pertanyaan.query.all()
    return render_template('user/percobaan.html', tanyas=listpertanyaan, user=current_user)

# loop = asyncio.get_event_loop()
@app.route('/proses', methods = ['POST'])
@login_required
def proses():
    if request.method == "POST":
        start = process_time()

        responden = request.form['id_responden']
        pertanyaan = request.form['pertanyaan']
        jawaban = request.form['jawaban']

        proses_deteksi(responden, pertanyaan, jawaban)
        end = process_time()
        print(end - start)
        return redirect('percobaan')

@app.route('/simpan_jawaban', methods = ['POST'])
@login_required
def simpan_jawaban():
    if request.method == "POST":
        start = process_time()

        responden = request.form['id_responden']
        pertanyaan = request.form.getlist('id_tanya')
        jawaban = request.form.getlist('jawaban')

        for pertanyaan, jawaban in zip(pertanyaan, jawaban):
            proses_deteksi(responden, pertanyaan, jawaban)
        end = process_time()
        print(end - start)
        return redirect('deteksi_koreksi')

def proses_deteksi(responden, pertanyaan, jawab):
    start = process_time()
    engine = create_engine("mysql+mysqlconnector://root@localhost:3306/tugas_akhir", echo=False)
    # simpan nilai utk scoring
    sql = engine.execute("SELECT kunci_jawaban FROM pertanyaan WHERE id_pertanyaan=" + pertanyaan).fetchall()
    kunci = tuple([row[0] for row in sql])

    # preprocessing
    jawaban = jawab.lower()
    kal, clean, token =  preprocessing(jawaban)

    # perhitungan jarak token dengan kata kamus dgn jaro winkler
    sql = engine.execute("SELECT DISTINCT kata FROM kamus").fetchall()
    hasil = tuple([row[0] for row in sql])

    # menambahkan underscore token
    for i in token:
        i.insert(0, "_")
        i.insert(len(i), "_")
    # print("case_folding" + jawaban)
    # print("token_kal" + kal)
    # print("filter" + clean)
    # print("token" + token)

    # jaro winkler
    hsl =  jaro_kamus(token, hasil)
    # print(token)

    # pemodelan n-gram
    unigram = tuple([ buat_unigram(hsl[i]) for i, value in enumerate(token)])
    bigram_kiri = tuple([ buat_bigram_kiri(token[i], hsl[i]) for i, value in enumerate(token)])
    bigram_kanan = tuple([ buat_bigram_kanan(token[i], hsl[i]) for i, value in enumerate(token)])
    trigram = tuple([ buat_trigram(token[i], hsl[i]) for i, value in enumerate(token)])
    # print(len((hsl)), len(token), len([unigram]), len(bigram_kanan), len(bigram_kiri), len(trigram))

    # # merge
    merge_uni =  satu_dimensi_token(unigram)
    merge_kiri =  satu_dimensi_token(bigram_kiri)
    merge_kanan =  satu_dimensi_token(bigram_kanan)
    merge_trigram =  satu_dimensi_token(trigram)
    # hapus underscore uni
    merge_uni_new = tuple([x[0] for x in merge_uni if not x[0] == "_"])
    merge_kiri_new = tuple([x[0] for x in merge_kiri])
    merge_kanan_new = tuple([x[0] for x in merge_kanan])
    merge_tri_new = tuple([x[0] for x in merge_trigram])
    # print(merge_uni_new)

    # mencari kata depan masing2 (uni masih blm bisa kata depan)
    depan_uni =  huruf_depan(merge_uni_new)
    depan_kiri =  huruf_depan(merge_kiri_new)
    depan_kanan =  huruf_depan(merge_kanan_new)
    depan_trigram =  huruf_depan(merge_tri_new)
    # print(depan_uni)

    uni = hitung_ngram(depan_uni, merge_uni_new, unigram,"unigram")
    bi_ki = hitung_ngram(depan_kiri, merge_kiri_new, bigram_kiri, "bigram_kiri")
    bi_ka = hitung_ngram(depan_kanan, merge_kanan_new, bigram_kanan, "bigram_kanan")
    tri = hitung_ngram(depan_trigram, merge_tri_new, trigram, "trigram")

    # hitung total kemunculan
    tot_unigram = tuple([ total_unigram(hsl[i], unigram[i]) for i, value in enumerate(unigram)])
    tot_bigram_kiri = tuple([ total_bigram_trigram(hsl[i], bigram_kiri[i]) for i, value in enumerate(bigram_kiri)])
    tot_bigram_kanan = tuple([ total_bigram_trigram(hsl[i], bigram_kanan[i]) for i, value in enumerate(bigram_kanan)])
    tot_trigram = tuple([ total_bigram_trigram(hsl[i], trigram[i]) for i, value in enumerate(trigram)])

    # db
    pro_uni = tuple([ probabilitas_unigram(hsl[i], tot_unigram[i], unigram[i]) for i, value in enumerate(unigram)])
    pro_bi_ki = tuple([ probabilitas_bigram_trigram(hsl[i], tot_bigram_kiri[i], bigram_kiri[i]) for i, value in enumerate(bigram_kiri)])
    pro_bi_ka = tuple([ probabilitas_bigram_trigram(hsl[i], tot_bigram_kanan[i], bigram_kanan[i]) for i, value in enumerate(bigram_kanan)])
    pro_tri = tuple([ probabilitas_bigram_trigram(hsl[i], tot_trigram[i], trigram[i]) for i, value in enumerate(trigram)])

    # perhitungan
    pro_unigram =  tuple([ubah_db(pro_uni[j]) for j, value in enumerate(pro_uni)])
    pro_bigram_kiri = tuple([ubah_db(pro_bi_ki[j]) for j, value in enumerate(pro_bi_ki)])
    pro_bigram_kanan = tuple([ubah_db(pro_bi_ka[j]) for j, value in enumerate(pro_bi_ka)])
    pro_trigram = tuple([ubah_db(pro_tri[j]) for j, value in enumerate(pro_tri)])

    # utk db
    jel_kiri = tuple([ mercer_bi_ki_ka(hsl[i], bigram_kiri[i], pro_unigram[i], pro_bigram_kiri[i]) for i, value in enumerate(bigram_kiri)])
    jel_kanan = tuple([ mercer_bi_ki_ka(hsl[i], bigram_kanan[i], pro_unigram[i], pro_bigram_kanan[i]) for i, value in enumerate(bigram_kanan)])
    jel_tri = tuple([ mercer_trigram(hsl[i], trigram[i], pro_bigram_kiri[i], pro_bigram_kanan[i], pro_trigram[i]) for i, value in enumerate(trigram)])

    # utk perhitungan
    jelinek_kiri = tuple([ubah_db(jel_kiri[j]) for j, value in enumerate(jel_kiri)])
    jelinek_kanan = tuple([ubah_db(jel_kanan[j]) for j, value in enumerate(jel_kanan)])
    jelinek_trigram = tuple([ubah_db(jel_tri[j]) for j, value in enumerate(jel_tri)])

    # hitung skor
    skor_kata = tuple([ hitung_skor(hsl[i], jelinek_kiri[i], jelinek_kanan[i], jelinek_trigram[i]) for i, value in enumerate(hsl)])

    # peringkatan
    rank_skor = tuple([ skor_ranking(hsl[i], skor_kata[i]) for i, value in enumerate(hsl)])
    tri_rank = tuple([ rank_tri(hsl[i], skor_kata[i]) for i, value in enumerate(hsl)])
    print(tri_rank)

    new = tuple([ ubah(rank_skor[i], token[i]) for i, value in enumerate(rank_skor)])

    list_str = tuple([ to_str(new[i]) for i, value in enumerate(new)])

    rekomendasi = '. '.join([str(val) for val in list_str])
    penilaian, dictkunci, dictjawaban, df, idfi, bobot_kunci, bobot_jawab, similaritas =  nilai(rekomendasi, kunci)

    end = process_time()
    waktu = end-start

    # ubah string utk db
    db_token_kal = ','.join(kal)
    db_clean = ','.join(clean)
    db_token = ','.join(chain.from_iterable(token))
    db_hsl = '%s' % (hsl)
    db_uni = '%s' % ([value for i, value in enumerate(unigram)])
    db_bi_ki = '%s' % ([value for i, value in enumerate(bigram_kiri)])
    db_bi_ka = '%s' % ([value for i, value in enumerate(bigram_kanan)])
    db_tri = '%s' % ([value for i, value in enumerate(trigram)])
    db_pro_uni = '%s' % ([value for i, value in enumerate(pro_uni)])
    db_pro_bi_ki = '%s' % ([value for i, value in enumerate(pro_bi_ki)])
    db_pro_bi_ka = '%s' % ([value for i, value in enumerate(pro_bi_ka)])
    db_pro_tri = '%s' % ([value for i, value in enumerate(pro_tri)])
    db_jel_bi_ki = '%s' % ([value for i, value in enumerate(jel_kiri)])
    db_jel_bi_ka = '%s' % ([value for i, value in enumerate(jel_kanan)])
    db_jel_tri = '%s' % ([value for i, value in enumerate(jel_tri)])
    db_skor_kata = '%s' % ([value for i, value in enumerate(skor_kata)])
    db_rank = '%s' % ([value for i, value in enumerate(tri_rank)])
    db_dict_kunci = '%s' % (dictkunci)
    db_dict_jawaban = '%s' % (dictjawaban)
    db_df = '%s' % (df)
    db_idfi = '%s' % (idfi)
    db_bobot_kunci = '%s' % (bobot_kunci)
    db_bobot_jawab = '%s' % (bobot_jawab)

    # input semua hasil jawaban
    sql = "INSERT INTO jawaban(id_responden, id_pertanyaan, jawaban, case_folding, token_kal, filter, token, jaro_wink, unigram, bigram_kiri, bigram_kanan, trigram, pro_uni, pro_bi_ki, pro_bi_ka, pro_tri, jelinek_kiri, jelinek_kanan, jelinek_trigram, " \
          "skor_kata, rank, rekomendasi, tf_kunci, tf_jawaban, df, idfi, bobot_kunci, bobot_jawab,  similaritas, nilai, waktu_proses)" \
          " VALUES (%s, %s, %s,%s,%s, %s,%s,%s,%s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    data = (responden, pertanyaan, jawab, jawaban, db_token_kal, db_clean, db_token, db_hsl, db_uni, db_bi_ki, db_bi_ka, db_tri, db_pro_uni, db_pro_bi_ki, db_pro_bi_ka, db_pro_tri, db_jel_bi_ki, db_jel_bi_ka, db_jel_tri, db_skor_kata, db_rank, rekomendasi, db_dict_kunci, db_dict_jawaban, db_df, db_idfi, db_bobot_kunci, db_bobot_jawab, similaritas, penilaian, waktu)
    proses = engine.execute(sql, data)
    # sql = engine.execute("UPDATE responden SET rekomendasi=%s, nilai=%s, waktu_proses=%s WHERE id=%s",(new_nama, new_jenis_kelamin, id))
    print(waktu)
    print(rekomendasi, penilaian)

    return (rekomendasi, penilaian)


@app.route('/hasil')
@login_required
def hasil():
  return render_template('user/hasil.html', user=current_user)

@app.route('/simpan_hasil', methods = ['POST'])
@login_required
def simpan_hasil():
    if request.method == "POST":
        responden = request.form['id']
        pertanyaan = request.form['id_tanya']
        jawaban = request.form['jawaban']
        rekomendasi = request.form['rekomendasi']
        nilai = request.form['nilai']
        engine = create_engine("mysql+mysqlconnector://root@localhost:3306/tugas_akhir", echo=False)
        sql = "INSERT INTO jawaban(id_responden, id_pertanyaan, jawaban, rekomendasi, nilai) VALUES (%s, %s, %s, %s, %s)"
        data = (responden, pertanyaan, jawaban, rekomendasi, nilai)
        proses = engine.execute(sql, data)
        return redirect('deteksi_koreksi')

@app.route('/tentang_user')
@login_required
def tentang_user():
  return render_template('user/tentang.html', user=current_user)

@app.route('/profil_user' )
@login_required
def profil_user():
    # pengguna = akun.query.filter_by(username=username).first()
    return render_template('user/profil.html', user=current_user)


