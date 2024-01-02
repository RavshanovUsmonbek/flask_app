import os
from dotenv import load_dotenv

load_dotenv()
env = os.getenv


class Config(object):
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{env('DB_USER')}:{env('DB_PASSWORD')}@{env('DB_HOST')}:{env('DB_PORT')}/{env('DB_NAME')}"
    SECRET_KEY = env("SECRET_KEY")


class ProdConfig(Config):
    pass


class DevConfig(Config):
    DEBUG = True
    PORT = env('APP_PORT')