from wtforms import Form
from wtforms import StringField, PasswordField, IntegerField,TelField
from wtforms import validators
from wtforms import HiddenField
from models import User,Estacionamientos

def tam_honey(form, valor):
    if len(valor.data) > 0:
        raise validators.ValidationError('Caiste pay')
class formu(Form):
    user = StringField('Usuario',[
                                    validators.DataRequired(message='Es obligatorio pay'),
                                  validators.length(min=4,max=35,message='No jala pay')
                                  ])
    password = PasswordField('Contraseña')
        
    honeypot = HiddenField('',[])

class createuser(Form):
    user = StringField('Usuario')
    password = PasswordField('Contraseña')
    rol = StringField('Rol')

    def validate_user(form,valor):
        username = valor.data
        user = User.query.filter_by(user=username).first()
        if user is not None:
            raise validators.ValidationError('Ya esta en la base pay')

class registrar_estacionamiento(Form):
    nombre = StringField('Nombre', [validators.data_required()])
    capacidad = IntegerField('Capacidad', [validators.data_required()])
    codigo_postal=IntegerField('Coodigo Postal', [validators.data_required()])
    telefono = TelField('Telefono', [validators.length(min=10),validators.data_required()])
    user = StringField('Usuario', [validators.length(min=4,max=15),validators.data_required()])
    password = PasswordField('Contraseña',[validators.length(min=8, max=15),validators.Regexp(r'^(?=.*[a-z])(?=.*[A-Z]).+$', message='Debe contener al menos una letra Mayuscula'),validators.DataRequired()])

    def validate_user(form,valor):
        username = valor.data
        user = User.query.filter_by(user=username).first()
        if user is not None:
            raise validators.ValidationError('Ya esta en la base pay')
    
    def validate_nombre(form,valor):
        name = valor.data
        est = Estacionamientos.query.filter_by(nombre=name).first()
        if est is not None:
            raise validators.ValidationError('Ya esta en la base pay')   

