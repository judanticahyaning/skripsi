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
    token =  preprocessing(jawaban)

    # perhitungan jarak token dengan kata kamus dgn jaro winkler
    sql = engine.execute("SELECT DISTINCT kata FROM kamus").fetchall()
    hasil = tuple([row[0] for row in sql])

    # menambahkan underscore token
    for i in token:
        i.insert(0, "_")
        i.insert(len(i), "_")

    # jaro winkler
    hsl =  jaro_kamus(token, hasil)
    print(token)

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
    tot_bigram_kiri = tuple([ total_bigram_kiri(hsl[i], bigram_kiri[i]) for i, value in enumerate(bigram_kiri)])
    tot_bigram_kanan = tuple([ total_bigram_kanan(hsl[i], bigram_kanan[i]) for i, value in enumerate(bigram_kanan)])
    tot_trigram = tuple([ total_trigram(hsl[i], trigram[i]) for i, value in enumerate(trigram)])

    # hitung probabilitas
    pro_unigram = tuple([ probabilitas_unigram(hsl[i], tot_unigram[i], unigram[i]) for i, value in enumerate(unigram)])
    pro_bigram_kiri = tuple([ probabilitas_bigram_kiri(hsl[i], tot_bigram_kiri[i], bigram_kiri[i]) for i, value in enumerate(bigram_kiri)])
    pro_bigram_kanan = tuple([ probabilitas_bigram_kanan(hsl[i], tot_bigram_kanan[i], bigram_kanan[i]) for i, value in enumerate(bigram_kanan)])
    pro_trigram = tuple([ probabilitas_trigram(hsl[i], tot_trigram[i], trigram[i]) for i, value in enumerate(trigram)])

    # hitung smoothing jelinek mercer
    jelinek_kiri = tuple([ mercer_bigram_kiri(hsl[i], bigram_kiri[i], pro_unigram[i], pro_bigram_kiri[i]) for i, value in enumerate(bigram_kiri)])
    jelinek_kanan = tuple([ mercer_bigram_kanan(hsl[i], bigram_kanan[i], pro_unigram[i], pro_bigram_kanan[i]) for i, value in enumerate(bigram_kanan)])
    jelinek_trigram = tuple([ mercer_trigram(hsl[i], trigram[i], pro_bigram_kiri[i], pro_bigram_kanan[i], pro_trigram[i]) for i, value in enumerate(trigram)])

    # hitung skor
    skor_kata = tuple([ hitung_skor(hsl[i], jelinek_kiri[i], jelinek_kanan[i], jelinek_trigram[i]) for i, value in enumerate(hsl)])

    # peringkatan
    rank_skor = tuple([ skor_ranking(hsl[i], skor_kata[i]) for i, value in enumerate(hsl)])

    new = tuple([ ubah(rank_skor[i], token[i]) for i, value in enumerate(rank_skor)])

    list_str = tuple([ to_str(new[i]) for i, value in enumerate(new)])

    rekomendasi = '. '.join([str(val) for val in list_str])
    penilaian =  nilai(rekomendasi, kunci)

    end = process_time()
    waktu = end-start
    # await asyncio.sleep(1)
    # input semua hasil jawaban
    sql = "INSERT INTO jawaban(id_responden, id_pertanyaan, jawaban, rekomendasi, nilai, waktu_proses) VALUES (%s, %s, %s, %s, %s, %s)"
    data = (responden, pertanyaan, jawab, rekomendasi, penilaian, waktu)
    proses = engine.execute(sql, data)

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


