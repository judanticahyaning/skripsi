from sqlalchemy import create_engine
from nltk.tokenize import sent_tokenize, word_tokenize
import re
import jaro
from itertools import groupby
from operator import itemgetter
import nltk
nltk.download('stopwords')
import math

def kemunculan_ngram(db, ngram, jenis=None):
    if jenis=="unigram":
        for i in db:
            kata = i[0]
            for j in ngram:
                if kata == j[0]:
                    j[1] = i[1]
                # else:
                #     j[1]=0
        # print("muncul_uni:", len(unigram))
        # print(unigram)
        # return ngram

    for i in db:
        kata = i[0]
        for j in ngram:
            if kata==j[0]:
                j[1]=i[1]
    # print("muncul_bi_ki:", len(bigram_kiri))
    # print(bigram_kiri)
    # return ngram

def hitung_ngram(depan, merge, ngram, jenis):
    engine = create_engine("mysql+mysqlconnector://root@localhost:3306/tugas_akhir", echo=False)
    # print(f"SELECT unigram, CAST(SUM(jumlah_kemunculan) AS int) FROM unigram GROUP BY unigram UNION SELECT unigrams, CAST(SUM(kemunculan) AS int) FROM unigrams GROUP BY unigrams WHERE IN {merge}")
    # kata = [n[0][:] for n  in ngram]
    # print(f"shape: {[a[:] for a in ngram]}")
    # print(merge)
    merge = tuple(set(merge))
    kata = ', '.join(list(map(lambda x: '%s', merge)))
    if jenis == "unigram":
        # hitung jumlah kemunculan masing-masing n-gram
        sql = engine.execute("SELECT * FROM (SELECT unigram, CAST(SUM(jumlah_kemunculan) AS int) FROM unigram GROUP BY unigram UNION SELECT unigrams as unigram, CAST(SUM(kemunculan) AS int) FROM unigrams GROUP BY unigram ) AS U WHERE U.unigram IN (%s)" % kata, merge)
        # sql = engine.execute(
        #     f"SELECT unigram, CAST(SUM(jumlah_kemunculan) AS int) FROM unigram GROUP BY unigram UNION SELECT unigrams, CAST(SUM(kemunculan) AS int) FROM unigrams GROUP BY unigrams WHERE unigram IN {merge}")
    elif jenis=="bigram_kiri" or jenis=="bigram_kanan":
        # bigram kiri
        sql = engine.execute(
            "SELECT * FROM (SELECT bigram, CAST(SUM(jumlah_kemunculan) AS int) FROM bigram GROUP BY bigram UNION SELECT bigrams as bigram, CAST(SUM(kemunculan) AS int) FROM bigrams GROUP BY bigram ) AS U WHERE U.bigram IN  (%s)" % kata, merge)
    elif jenis=="trigram":
        sql = engine.execute(
            "SELECT * FROM (SELECT trigram, CAST(SUM(jumlah_kemunculan) AS int) FROM trigram GROUP BY trigram UNION SELECT trigrams as trigram, CAST(SUM(kemunculan) AS int) FROM trigrams GROUP BY trigram ) AS U WHERE U.trigram IN  (%s)" % kata, merge)
    db = tuple([list(row) for row in sql])
    kata = tuple([n for n in db if n[0][0] in depan])
    for i, value in enumerate(ngram):
        kemunculan_ngram(kata, ngram[i], "unigram")
    # tuple([kemunculan_ngram(kata, ngram[i], "unigram") for i, value in enumerate(ngram)])
    # return muncul
    # for i in ngram:

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
        # token_kata.insert(0, "_")
        # token_kata.insert(len(kalimat), "_")
        token.append(token_kata)
    return token

def buat_unigram(result):
    unigram = []
    for i in range(len(result)):
        # key = result[i+1]
        for j in result[i]:
            unigram.append([j,0])
    print("unigram:", len(unigram))
    return unigram

def buat_bigram_kiri(token, result):
    bigram_kiri = []
    for i in range(len(token) - 1):
        for k in result[i + 1]:
            if (k == "_"):
                break
            key = token[i] + " " + k
            bigram_kiri.append([key,0])
    print("bi_ki:", len(bigram_kiri))
    # print(bigram_kiri)
    return bigram_kiri

def buat_bigram_kanan(token, result):
    bigram_kanan = []
    for i in range(2, len(token)):
        for j in result[i - 1]:
            key = j + " " + token[i]
            bigram_kanan.append([key,0])
    print("bi_ka:", len(bigram_kanan))
    return bigram_kanan

def buat_trigram(token, result):
    trigram = []
    for i in range(len(token) - 2):
        for k in result[i + 1]:
            key = token[i] + " " + k + " " + token[i + 2]
            trigram.append([key,0])
    print("trigram:", len(trigram))
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
    print("total_uni : ", list_total)
    return list_total

def total_bigram_kiri(result, bigram_kiri):
    index_token = 1
    total = 0
    length = len(result[index_token])
    # print(result[i])
    list_total = []
    for index, (key, value) in enumerate(bigram_kiri):
        if index == len(bigram_kiri) - 1:
            list_total.append(total)
        if index == length:
            # print(key,value)
            list_total.append(total)
            index_token += 1
            length += len(result[index_token])
            total = 0

        total += value
    print("total_bi_ki : ", list_total)
    return list_total

def total_bigram_kanan(result, bigram_kanan):
    index_token = 1
    total = 0
    length = len(result[index_token])
    list_total = []

    for index, (key, value) in enumerate(bigram_kanan):
        # print(key, value)
        if index == len(bigram_kanan) - 1:
            list_total.append(total)

        if index == length:
            list_total.append(total)
            index_token += 1
            length += len(result[index_token])
            total = 0

        total += value
    print("tot_bi_ka:", list_total)
    return list_total

def total_trigram(result,trigram):
    index_token = 1
    total = 0
    length = len(result[index_token])
    list_total = []

    for index, (key, value) in enumerate(trigram):
        if index == len(trigram) - 1:
            list_total.append(total)

        if index == length:
            list_total.append(total)
            index_token += 1
            length += len(result[index_token])
            total = 0

        total += value
    print("total_tri : ", list_total)
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
            # list_pro.append([key, probabilitas, total])
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
            # list_pro.append([key, probabilitas, total])
            list_pro.append(probabilitas)
            # print(key, value)
        # print(type(probabilitas))
    print("pro_uni:" , len(list_pro))
    return list_pro

def probabilitas_bigram_kiri (result, tot_bigram_kiri, bigram_kiri):
    index_token = 1
    length = len(result[index_token])
    list_pro = []
    index_tot = 0
    for index, (key, value) in enumerate(bigram_kiri):
        probabilitas = 0
        total = tot_bigram_kiri[index_tot]
        # if index==len(bigram_kiri)-1:
        #     break
        if index == length - 1:
            if total == 0:
                probabilitas = 0.0
            else:
                probabilitas += value / total
            # list_pro.append([key, probabilitas, total])
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
            # list_pro.append([key, probabilitas, total])
            list_pro.append(probabilitas)
            # print(key, value)
    print("pro_bi_ki:", len(list_pro))
    return list_pro

def probabilitas_bigram_kanan(result, tot_bigram_kanan, bigram_kanan):
    index_token = 1
    length = len(result[index_token])
    list_pro = []
    index_tot = 0
    for index, (key, value) in enumerate(bigram_kanan):
        probabilitas = 0
        total = tot_bigram_kanan[index_tot]
        if index == length - 1:
            if total == 0:
                probabilitas = 0.0
            else:
                probabilitas += value / total
            # list_pro.append([key, probabilitas, total])
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
            # list_pro.append([key, probabilitas, total])
            list_pro.append(probabilitas)
            # print(key, value)
    print("pro_bi_ka", len(list_pro))
    return list_pro

def probabilitas_trigram(result,tot_trigram, trigram):
    index_token = 1
    length = len(result[index_token])
    list_pro = []
    index_tot = 0
    for index, (key, value) in enumerate(trigram):
        probabilitas = 0
        total = tot_trigram[index_tot]
        if index == length - 1:
            if total == 0:
                probabilitas = 0.0
            else:
                probabilitas += value / total
            # list_pro.append([key, probabilitas, total])
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
            # list_pro.append([key, probabilitas, total])
            list_pro.append(probabilitas)
            # print(key, value)
    print("pro_bi_tri:", len(list_pro))
    return list_pro

def mercer_bigram_kiri (result, bigram_kiri, pro_unigram, pro_bigram_kiri):
    index_token = 1
    length = len(result[index_token])
    list_smooth = []
    index_uni = 0
    index_bi_ki = 0
    for index, (key, value) in enumerate(bigram_kiri):
        val_lambda = 0.1
        smooth = 0.0
        prob_uni = pro_unigram[index_uni]
        prob_bi_ki = pro_bigram_kiri[index_bi_ki]
        # if index==len(result)-1:
        #     break
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
    print("mercer_kiri:", len(list_smooth))
    return list_smooth

def mercer_bigram_kanan(result, bigram_kanan, pro_unigram, pro_bigram_kanan):
    index_token = 1
    length = len(result[index_token])
    list_smooth = []
    index_uni = 0
    index_bi_ka = 0
    for index, (key, value) in enumerate(bigram_kanan):
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
    print("mercer_kanan:", len(list_smooth))
    return list_smooth

def mercer_trigram(result, trigram, pro_bigram_kiri, pro_bigram_kanan, pro_trigram):
    index_token = 1
    length = len(result[index_token])
    list_smooth = []
    index_bi_ka = 0
    index_bi_ki = 0
    index_tri = 0
    for index, (key, value) in enumerate(trigram):
        val_lambda = 0.1
        smooth = 0.0
        prob_bi_ki = pro_bigram_kiri[index_bi_ki]
        prob_bi_ka = pro_bigram_kanan[index_bi_ka]
        prob_trigram = pro_trigram[index_tri]
        if index == length:
            # print(key, value)
            smooth += (val_lambda * prob_trigram) + ((1 - val_lambda) * ((prob_bi_ki + prob_bi_ka) / 2))
            list_smooth.append(smooth)
        elif index == length - 1:
            # print(key, value)
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
            # if j == len(jelinek_kiri) - 1:
            #     break
            skor += ((lam_satu_dua * prob_mer_ki) + (lam_satu_dua * prob_mer_ka) + (lam_tiga * prob_mer_tri))
            list_skor.append([value, skor])
            index_mer_ki += 1
            index_mer_ka += 1
            index_tri += 1
    # print(list_skor)
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
                # rank = sorted(temp, key=itemgetter(1), reverse=True)
                maks =max(temp, key=itemgetter(1))
                # ranking.append(rank[:3])
                ranking.append(maks)
                temp.clear()
            index_skor += 1
            # print(value)
            # print(ranking[1])

    rekomen = []
    for i in ranking:
        rekomen.append(i[0])
    return rekomen

def ubah(rank_skor, list_jawab):
    new = []
    index_rank = 0
    for i, value in enumerate(list_jawab):
        rank = rank_skor[index_rank]
        if (i==0):
            continue
        elif (i==len(rank_skor)):
            if (value != rank):
                new.append(value.replace(value, rank))
            else:
                new.append(rank)
            break
        else:
            if (value != rank):
                new.append(value.replace(value, rank))
            else:
                new.append(rank)
            index_rank += 1
    return new

def to_str(new):
    listtostr = ' '.join([str(val) for val in new])
    return listtostr

def satu_dimensi_token(token):
    list = []
    for i in token:
        list.extend(i)
    return list

def huruf_depan(a):
    # sort dan groupby => utk huruf depan token
    util_func = lambda x: x[0]
    temp = sorted(a, key=util_func)
    res = [list(ele) for i, ele in groupby(temp, util_func)]
    # utk nentuin huruf depan token
    filter = [n[0] for j in res for n in j]
    # filter = [j[0] for j in res]
    return filter

def jaro_kamus(token, hasil):
    hsl = []
    for i in token:
        result = {0: "_"}
        for j in range(len(i)):
            temp = []
            s1 = i[j]
            if s1 == "yg":
                temp.append("yang")
                result[j] = temp
                continue
            if s1 == "cpt":
                temp.append("cepat")
                result[j] = temp
                continue
            if s1 == "tdk":
                temp.append("tidak")
                result[j] = temp
                continue
            for k in hasil:
                jaro_wink = jaro.jaro_winkler_metric(s1, k)
                # jaro = jaro_winkler(s1, k)
                if (jaro_wink >= 0.7):
                    temp.append(k)
                    result[j] = temp
        result[j] = "_"
        hsl.append(result)
        # q.put(hsl)
    return hsl

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

def nilai (rekomendasi, kunci):
    n = len([kunci, rekomendasi])
    # case folding
    jawaban = rekomendasi.lower()
    for i in kunci:
        kunci = i.lower()

    prepro_kunci =  prepro_scoring(kunci)
    prepro_jawaban =  prepro_scoring(jawaban)

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
        idfi[key] = math.log10(n / value) + 1

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
        # print(index, value, jarak)
        if (index == len(bobot_kunci) - 1):
            hasil = math.sqrt(jarak)
            list_jarak_kunci.append(hasil)

    list_jarak_jawab = []
    jarak = 0
    for index, (key, value) in enumerate(bobot_jawab.items()):
        jarak += pow(value, 2)
        # print(value, jarak)
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
        if kunci == 0 or jawab == 0:
            similaritas = 0.0
        else:
            similaritas = total / (kunci * jawab)

        if (similaritas == 0.0):
            value=0
        elif (similaritas >= 0.01 and similaritas <= 0.10):
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
    return value
