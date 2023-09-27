class Config(object):
    SECRET_KEY = 'Clave'

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://admin:Sincontra1@siret.cfnop33q4azw.us-east-1.rds.amazonaws.com/SIRET'
