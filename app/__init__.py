from flask import Flask
from flask_login import LoginManager
app = Flask(__name__)

from app.module.model import *
from app.module.controller_admin import *
from app.module.controller_user import *
# from app.module.auth import *
app.secret_key = "judanticahyaning"

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://root@localhost:3306/tugas_akhir"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# # login
# login_manager = LoginManager()
# login_manager.login_view = 'controller.masuk'
# login_manager.init_app(app)
#
# @login_manager.user_loader
# def load_user(id_akun):
#     return akun.query.get(int(id_akun))