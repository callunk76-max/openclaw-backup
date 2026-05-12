import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'aramedica_apotek_2026_secret'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'aramedica.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    APP_NAME = 'Apotik Aramedica'
    APP_LOGO = '/static/logo.svg'
    PER_PAGE = 25

PREFIX = '/mk'
