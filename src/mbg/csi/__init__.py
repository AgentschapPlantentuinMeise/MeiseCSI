import os
import base64
from io import BytesIO
import datetime
from flask import Flask, jsonify, request, render_template, redirect, abort
from flask_fefset import FEFset
from flask_uxfab import UXFab
from flask_sqlalchemy import SQLAlchemy
from flask_iam import IAM
# IX Form
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerRangeField, BooleanField, FloatField, IntegerField, HiddenField, SelectField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired, Optional
import urllib.parse
from shapely import wkt
import folium
from PIL import Image
import pandas as pd
from celery.result import AsyncResult

def create_app(config_filename=None):
    app = Flask(__name__)

    # Config
    #app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(app.instance_path,'db.sqlite')}"
    #app.config["SQLALCHEMY_DATABASE_URI"] = f"mariadb+pymysql://guardin:{os.environ.get('MARIADB_PASSWORD')}@db:3306/"
    app.config['SECRET_KEY'] = os.urandom(12).hex() # to allow csrf forms
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # max 50MB upload
    app.config.from_mapping(
        CELERY=dict(
            broker_url=os.environ.get("CELERY_BROKER_URL"),#'sqla+sqlite:////tmp/celery.db'
            result_backend=f"db+sqlite:///{os.path.join(app.instance_path,'shared/celery.db')}",
            #os.environ.get("CELERY_RESULT_BACKEND", "rpc://"),
            task_ignore_result=True,
        ),
    )
    if config_filename:
        app.config.from_pyfile(config_filename)

    # Flask extensions
    db = SQLAlchemy()
    fef = FEFset(frontend='bootstrap4')
    fef.nav_menu.append(
        {'name':'Home', 'url':'/'}
    )
    fef.settings['brand_name'] = 'MBG-CSI'
    #fef.settings['logo_url'] = '/static/images/mcsi_logo.png'
    fef.init_app(app)
    db.init_app(app)
    uxf = UXFab()
    uxf.init_app(app)
    iam = IAM(db)
    iam.init_app(app)
    celery_app = tasks.celery_init_app(app)

    with app.app_context():
        db.create_all()
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
    
    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html')
    
    return app
