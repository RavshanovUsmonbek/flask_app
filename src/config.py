import os
import datetime
from dotenv import load_dotenv

load_dotenv()
env = os.getenv


class Config(object):
    SECRET_KEY = env("SECRET_KEY")


class ProdConfig(Config):
    DEBUG = False


class DevConfig(Config):
    DEBUG = True
    PORT = env('APP_PORT')
    CELERY_BROKER_URL = f"amqp://{env('RABBIT_USER')}:{env('RABBIT_PASSWORD')}@{env('RABBIT_HOST')}//"
    CELERY_RESULT_BACKEND = f"rpc://{env('RABBIT_USER')}:{env('RABBIT_PASSWORD')}@{env('RABBIT_HOST')}//"
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{env('DB_USER')}:{env('DB_PASSWORD')}@{env('DB_HOST')}:{env('DB_PORT')}/{env('DB_NAME')}"
    

    CELERYBEAT_SCHEDULE = {
        'log-every-30-seconds': {
            'task': 'webapp.blog.tasks.log',
            'schedule': datetime.timedelta(seconds=30),
            'args': ("Message",)
        },
    }