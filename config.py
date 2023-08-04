class Config(object):
    SECRET_KEY = 'Clave'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql://root:sincontra1@localhost/siret'
