from flask_sqlalchemy import SQLAlchemy
from app import app

db = SQLAlchemy(app)

class pertanyaan(db.Model):
    id_pertanyaan = db.Column(db.Integer, unique=True, primary_key=True, nullable=False)
    pertanyaan = db.Column(db.String, nullable=False)
    kunci_jawaban = db.Column(db.String, nullable=False)

    def __repr__(self, id_pertanyaan, pertanyaan, kunci_jawaban):
        self.id_pertanyaan = id_pertanyaan
        self.pertanyaan = pertanyaan
        self.kunci_jawaban = kunci_jawaban

class kbbi(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True, nullable=False)
    kata = db.Column(db.String, nullable=False)

    def __repr__(self, id, kata):
        self.id = id
        self.kata = kata

class unigram(db.Model):
    id_unigram = db.Column(db.Integer, unique=True, primary_key=True, nullable=False)
    unigram = db.Column(db.Integer, nullable=False)
    jumlah_kemunculan = db.Column(db.String,nullable=False)

    def __repr__(self, id_unigram, unigram, jumlah_kemunculan):
        self.id_unigram = id_unigram
        self.unigram = unigram
        self.jumlah_kemunculan = jumlah_kemunculan

class bigram(db.Model):
    id_bigram = db.Column(db.Integer, unique=True, primary_key=True, nullable=False)
    bigram = db.Column(db.Integer, nullable=False)
    jumlah_kemunculan = db.Column(db.String,nullable=False)

    def __repr__(self, id_bigram, bigram, jumlah_kemunculan):
        self.id_bigram = id_bigram
        self.bigram = bigram
        self.jumlah_kemunculan = jumlah_kemunculan

class trigram(db.Model):
    id_trigram = db.Column(db.Integer, unique=True, primary_key=True, nullable=False)
    trigram = db.Column(db.Integer, nullable=False)
    jumlah_kemunculan = db.Column(db.String,nullable=False)

    def __repr__(self, id_trigram, trigram, jumlah_kemunculan):
        self.id_trigram = id_trigram
        self.trigram = trigram
        self.jumlah_kemunculan = jumlah_kemunculan

class akun(db.Model):
    id_akun = db.Column(db.Integer, unique=True, primary_key=True, nullable=False)
    nama = db.Column(db.String, nullable=False)
    username = db.Column(db.String, nullable = False, unique=True)
    password = db.Column(db.String, nullable=False)

    def __repr__(self, id_akun, nama, username, password):
        self.id_akun = id_akun
        self.nama = nama
        self.username = username
        self.password = password
