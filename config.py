class Config(object):
    SECRET_KEY = 'Clave'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:sincontra1@localhost:3306/SIRET'
