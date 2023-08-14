class Config(object):
    SECRET_KEY = 'Clave'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql://admin:sincontra1@siret-db.cfnop33q4azw.us-east-1.rds.amazonaws.com/SIRET'
