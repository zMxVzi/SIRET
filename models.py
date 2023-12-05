from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash,check_password_hash

db = SQLAlchemy()

class Estacionamientos(db.Model):
    __tablename__ = 'estacionamientos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50),unique=True,primary_key=True)
    codigo_postal = db.Column(db.Integer)
    telefono = db.Column(db.String(11))
    capacidad = db.Column(db.Integer)
    user = db.relationship('User')
    # boletos = db.relationship('Boletos')
    tarifas = db.relationship('Tarifas')


    def __init__(self, nombre, capacidad,codigo_postal,telefono):
        self.nombre = nombre
        self.capacidad = capacidad
        self.telefono = telefono
        self.codigo_postal = codigo_postal

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    estacionamiento = db.Column(db.ForeignKey('estacionamientos.nombre'))
    user = db.Column(db.String(50),unique=True)
    passsword = db.Column(db.String(102))
    rol = db.Column(db.String(50))
    # boletos = db.relationship('Boletos')

    def __init__(self, user, passsword,rol,estacionamiento):
        self.user = user
        self.passsword = self.create_password(passsword)
        self.rol = rol
        self.estacionamiento = estacionamiento

    def create_password(self,passsword):
        return generate_password_hash(passsword)
    
    def verify_password(self,passsword):
        return check_password_hash(self.passsword,passsword)

class Boletos(db.Model):
    __tablename__ = 'Boletos'
    id = db.Column(db.Integer, primary_key=True)
    estacionamiento = db.Column(db.ForeignKey('estacionamientos.nombre'))
    operador = db.Column(db.String(50))
    entrada = db.Column(db.DateTime)
    salida = db.Column(db.DateTime)
    tarifa = db.Column(db.Integer)
    estado = db.Column(db.String(15))


    def __init__(self, entrada,salida,tarifa,operador,estacionamiento,estado):
        self.entrada = entrada
        self.salida = salida
        self.tarifa = tarifa
        self.operador = operador
        self.estacionamiento = estacionamiento
        self.estado = estado

class Tarifas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estacionamiento = db.Column(db.ForeignKey('estacionamientos.nombre'))
    tolerancia = db.Column(db.Integer)
    primeras_dos = db.Column(db.Integer)
    extra = db.Column(db.Integer)
    pension_dia = db.Column(db.Integer)
    pension_sem = db.Column(db.Integer)
    pension_mes = db.Column(db.Integer)
    
    def __init__(self,primeras_dos,extra,pension_dia,pension_mes,pension_sem,tolerancia,estacionamiento):
        self.extra = extra
        self.pension_dia = pension_dia
        self.primeras_dos = primeras_dos
        self.pension_mes = pension_mes 
        self.pension_sem = pension_sem
        self.tolerancia = tolerancia
        self.estacionamiento = estacionamiento




