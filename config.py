class Config(object):
    SECRET_KEY = 'Clave'

class DevelopmentConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://admin:sincontra1@db-siret.c1nv3t7xppqx.us-east-1.rds.amazonaws.com:3306/SIRET'
