from flask import redirect,flash,g
from flask import Flask,request,render_template,make_response,session,redirect,url_for,send_file
from flask_wtf import CSRFProtect
from config import DevelopmentConfig
from models import User,db,Estacionamientos,Boletos,Tarifas
import form
import json
import  os
from datetime import datetime, timedelta
from tickets import Ticket
from reportlab.pdfgen import canvas
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch
import pytz
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
db.init_app(app)
with app.app_context():
    db.create_all()
csrf = CSRFProtect(app)
csrf.init_app(app)

@app.before_request
def before_request():
    missing = User.query.filter_by(user='admin').first()
    if missing is None:
        estacionamiento = Estacionamientos(nombre = 'SIRET',
                    capacidad=None,
                    codigo_postal=None,
                    telefono=None)
        db.session.add(estacionamiento)
        db.session.commit()
        user = User(user = 'admin',
                    passsword='admin',
                    estacionamiento= 'SIRET',
                    rol='CREADOR')
        db.session.add(user)
        db.session.commit()
    if 'cliente' not in session and request.endpoint in ['lusers','admin','fadmin','eliminar','boletos','creador','create','tarifas','actualizar','llegada','salida','c_usuarios','c_listau','c_boletos']:
        return redirect(url_for('login'))

@app.after_request
def after_request(response):
    return response

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404

@app.route('/',methods = ['GET','POST'] )
@app.route('/login', methods = ['GET','POST'])
def login():
    hform = form.formu(request.form)
    if request.method == 'POST' and hform.validate():
        username = hform.user.data
        passwordd = hform.password.data
        user = User.query.filter_by(user = username).first()
        if user is not None and user.verify_password(passwordd):
            session['cliente'] = username
            session['rol'] = user.rol
            session['estacionamiento'] = user.estacionamiento
            if user.rol == 'CREADOR':
                return redirect(url_for('creador'))
            else:
                return redirect(url_for('admin'))
        else:
            error_message = 'Usuario y/o contraseña invalidos'
            flash(error_message)
    return render_template('signin.html', form = hform)

@app.route('/create-e', methods = ['GET','POST'])
def createe():
    hform = form.registrar_estacionamiento(request.form)
    if request.method == 'POST' and hform.validate():
        estacionamiento = Estacionamientos(nombre = hform.nombre.data,
                    capacidad=hform.capacidad.data,
                    codigo_postal=hform.codigo_postal.data,
                    telefono=hform.telefono.data)

        #db.session.commit()
        user = User(estacionamiento=hform.nombre.data,user=hform.user.data,passsword=hform.password.data,rol="Administrador")
        db.session.add(estacionamiento)
        db.session.add(user)
        db.session.commit()
        precios = Tarifas(tolerancia=15,primeras_dos=20,extra=20,pension_dia=200,pension_sem=1000,pension_mes=4000,estacionamiento=hform.nombre.data)
        db.session.add(precios)
        db.session.commit()
        success_message = 'Estacionamiento Registrado'
        flash(success_message)
    return render_template('signup.html',form = hform)

@app.route('/logout')
def logout(): 
    if 'user' in session:
        session.pop('user')
        session.pop('rol')
        session.pop('estacionamiento')
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'cliente' in session:
        nombre_user = session['cliente']
    esta = User.query.filter_by(user=nombre_user).first()
    pagina = int(request.args.get('page', 1))
    boletos_por_pagina = 10  
    total_boletos = Boletos.query.filter_by(estacionamiento=esta.estacionamiento).count()
    total_paginas = (total_boletos + boletos_por_pagina - 1) // boletos_por_pagina

    boletos = Boletos.query.filter_by(estacionamiento=esta.estacionamiento) \
                           .limit(boletos_por_pagina) \
                           .offset((pagina - 1) * boletos_por_pagina) \
                           .all()
    query = text("SELECT calcularSumaTarifas() as suma")
    with db.engine.connect() as connection:
        result = connection.execute(query)
        suma = result.scalar()
    return render_template('adminpage.html', est=esta, usuario=nombre_user, boletos=boletos, pagina_actual=pagina, total_paginas=total_paginas,ingresos=suma)

@app.route('/fadmin', methods = ['GET','POST'])
def fadmin():
    nombre_user = session['cliente']
    esta = User.query.filter_by(user=nombre_user).first()
    hform = form.createuser(request.form)
    if request.method == 'POST':
        user = User(user = request.form['usuario'],
                    passsword=request.form['contraseña'],
                    estacionamiento= session['estacionamiento'],
                    rol= request.form['roll'])
        db.session.add(user)
        db.session.commit()
        success_message = 'Usuario Registrado'
        flash(success_message)
    
    return render_template('form.html',est = esta,usuario = nombre_user,form = hform)

@app.route('/lusers')
def lusers():
    nombre_user = session['cliente']
    esta = User.query.filter_by(user=nombre_user).first()
    lista = User.query.filter(User.estacionamiento.endswith(esta.estacionamiento)).all()
    return render_template('usuarios.html',est = esta,usuario = nombre_user, lista = lista)

@app.route('/eliminar', methods = ['POST'])
def eliminar():
    idd = request.form['id']
    usuario = User.query.filter_by(id=idd).first()
    if request.form['opcion'] == "1":
        db.session.delete(usuario)
        db.session.commit()
        if session['rol'] == 'CREADOR':
            return redirect(url_for('c_listau'))
        else:
            return redirect(url_for('lusers'))
    else:
        password = request.form['new_password']
        print(password)
        sha = User.create_password(password,password)
        print(sha)
        stmt = text("CALL actualizar_contrasena(:id, :nueva_contrasena)")
        db.session.execute(stmt, {'id': idd, 'nueva_contrasena': sha})
        db.session.commit()

        if session['rol'] == 'CREADOR':
            return redirect(url_for('c_listau'))
        else:
            return redirect(url_for('lusers'))

def upadteuser():
    if request.method == 'POST':
        nombre_user = session['cliente']
        usermod = request.form('')
        esta = User.query.filter_by(user=nombre_user).first()
        Tarifas.query.filter_by(estacionamiento=esta.estacionamiento).update(
            dict(tolerancia=request.form['l1'],
                 primeras_dos=request.form['l2'],extra=request.form['l3'],pension_dia=request.form['l4'],pension_sem=request.form['l6'],pension_mes=request.form['l6']))
        db.session.commit()
        success_message = 'Tarifas Actualizadas Correctamente'
        flash(success_message)
    return redirect(url_for('tarifas'))

@app.route('/create', methods = ['GET','POST'])
def create():
    hform = form.createform(request.form)
    if request.method == 'POST' and hform.validate():
        user = User(user = hform.user.data,
                    password=hform.password.data,
                    estacionamiento= hform.estacionamiento.data,
                    rol= hform.rol.data)
        db.session.add(user)
        db.session.commit()
        success_message = 'Usuario registrado pay'
        flash(success_message)
        if session['rol'] == 'CREADOR':
            return render_template('create.html',form = hform)
        else:
            return render_template('create.html',form = hform)

@app.route('/boletos')
def boletos():
    nombre_user = session['cliente']
    esta = User.query.filter_by(user=nombre_user).first()
    muestra=""
    return render_template('boletos.html',est = esta,usuario = nombre_user,bandera=False,bandera2=False,muestra1=muestra,muestra2=muestra)

@app.route('/tarifas') #Finish
def tarifas():
    nombre_user = session['cliente']
    esta = User.query.filter_by(user=nombre_user).first()
    t = Tarifas.query.filter_by(estacionamiento=esta.estacionamiento).first()
    return render_template('tarifas.html',est = esta,usuario = nombre_user,t=t)

@app.route('/actualizar', methods = ['POST']) #Finish
def actializar():
    nombre_user = session['cliente']
    esta = User.query.filter_by(user=nombre_user).first()
    if request.method == 'POST':
        Tarifas.query.filter_by(estacionamiento=esta.estacionamiento).update(
            dict(tolerancia=request.form['l1'],
                 primeras_dos=request.form['l2'],extra=request.form['l3'],pension_dia=request.form['l4'],pension_sem=request.form['l6'],pension_mes=request.form['l6']))
        db.session.commit()
        success_message = 'Tarifas Actualizadas Correctamente'
        flash(success_message)
    return redirect(url_for('tarifas'))

@app.route('/llegada', methods = ['POST']) #Finish
def llegada():
    nombre_user = session.get('cliente')
    esta = User.query.filter_by(user=nombre_user).first()
    estacionamiento  = Estacionamientos.query.filter_by(nombre=esta.estacionamiento).first()
    muestra = "show" #bandera
    espacio = Boletos.query.filter_by(estado='Pendiente').count()
    if espacio <= estacionamiento.capacidad :
        boleto = None  # Inicializa boleto fuera del bloque 'POST'

        if request.method == 'POST':
            boleto = Boletos(entrada=request.form['fecha'], salida=None, tarifa=None, operador=nombre_user,
                             estacionamiento=esta.estacionamiento,estado= "Pendiente")
            db.session.add(boleto)
            db.session.commit()
        img_data = Ticket.gen_qr(boleto.id)
    else:
        success_message = 'Estacionamiento lleno'
        flash(success_message)
        return redirect(url_for('boletos'))
    return render_template('boletos.html', est=esta, usuario=nombre_user, bandera=True, boleto=boleto, muestra1=muestra, qr_code=img_data)

@app.route('/pdf')
def get_pdf():
    idd = request.args.get('id','null')
    boleto = Boletos.query.filter_by(id=idd).first()
    pdf = Ticket.gen_pdf(boleto)
    return send_file(pdf, as_attachment=True)

@app.route('/calculoqr')
def precal():
    idd = request.args.get('id')
    if idd is not None:
        boleto = Boletos.query.filter_by(id=idd).first()
        hora_actual_utc = datetime.utcnow()
        # Ajusta la hora según UTC-06:00
        zona_horaria_utc_06 = pytz.timezone('America/Mexico_City')
        hora_actual_utc_06 = hora_actual_utc.replace(tzinfo=pytz.utc).astimezone(zona_horaria_utc_06)
        # Formatea la hora actual
        hora_formateada = hora_actual_utc_06.strftime('%Y-%m-%dT%H:%M')
        sal = hora_formateada
        nombre_user = session['cliente']
        esta = User.query.filter_by(user=nombre_user).first()
        muestra2 = "show"  # bandera para mostrar
        if session['estacionamiento'] == boleto.estacionamiento:
            if boleto.estado == "Pendiente":
                tarifa = Ticket.calculo_t(boleto, sal, esta)
                bandera = True
            else:
                tarifa = 0
                bandera = False
                success_message = 'Este boleto ya no es vigente'
                flash(success_message)
        else:
            tarifa = 0
            bandera = False
            success_message = 'Este boleto no es de este estacionamiento'
            flash(success_message)
        return render_template('boletos.html', est=esta, usuario=nombre_user, bandera2=bandera, boleto=boleto,
                               total=tarifa, salida=boleto.salida, muestra2=muestra2)


@app.route('/calculo', methods = ['POST'])
def calculo():
    boleto = Boletos.query.filter_by(id=request.form['codigo']).first()
    sal = request.form['salida']
    nombre_user = session['cliente']
    esta = User.query.filter_by(user=nombre_user).first()
    muestra2 = "show"  # bandera para mostrar
    if session['estacionamiento'] == boleto.estacionamiento:
        if boleto.estado == "Pendiente":
                tarifa = Ticket.calculo_t(boleto,sal,esta)
                bandera = True
        else:
            tarifa = 0
            bandera=False
            success_message = 'Este boleto ya no es vigente'
            flash(success_message)
    else:
        tarifa = 0
        bandera = False
        success_message = 'Este boleto no es de este estacionamiento'
        flash(success_message)
    return render_template('boletos.html',est = esta,usuario = nombre_user,bandera2=bandera,boleto=boleto,total=tarifa,salida=boleto.salida, muestra2=muestra2)

@app.route('/salida', methods = ['POST']) #Finish
def salida():
    muestra2="show"
    nombre_user = session['cliente']
    esta = User.query.filter_by(user=nombre_user).first()
    boleto = Boletos.query.filter_by(id=request.form['codigo']).first()
    if request.method == 'POST':
        tarifa = Ticket.calculo_t(boleto, boleto.salida, esta)
        bandera=True
        Boletos.query.filter_by(id=request.form['codigo']).update(
            dict(tarifa=tarifa))
        Boletos.query.filter_by(id=request.form['codigo']).update(
            dict(estado="Pagado"))
        db.session.commit()
        success_message = 'Transaccion correcta'
        flash(success_message)
    return render_template('boletos.html',est = esta,usuario = nombre_user,bandera2=bandera,boleto=boleto,total=tarifa,salida=boleto.salida, muestra2=muestra2)

@app.route('/creador')
def creador():
    if 'cliente' in session:
        nombre_user = session['cliente']
    usuario = User.query.filter_by(user=nombre_user).first()
    pagina = int(request.args.get('page', 1))
    mostrar = 10
    total_estacionamientos = db.session.query(Estacionamientos).count()
    total_paginas = (total_estacionamientos + mostrar - 1) // mostrar
    l_estacionamietos = db.session.query(Estacionamientos) \
                           .limit(mostrar) \
                           .offset((pagina - 1) * mostrar) \
                           .all()
    return render_template('creador.html',est=usuario,usuario=nombre_user,estacionamientos = l_estacionamietos, pagina_actual=pagina, total_paginas=total_paginas)

@app.route('/c_usuarios', methods = ['GET','POST'])
def c_usuarios():
    listaEstacionamientos = db.session.query(Estacionamientos).all()
    esta = User.query.filter_by(user=session['cliente']).first()
    if request.method == 'POST':
        user = User(user = request.form['usuario'],
                    password=request.form['contraseña'],
                    estacionamiento= request.form['estacionamiento'],
                    rol= request.form['roll'])
        db.session.add(user)
        db.session.commit()
        success_message = 'Usuario registrado pay'
        flash(success_message)
    return render_template('c_usuarios.html',est = esta,usuario = session['cliente'],lista = listaEstacionamientos)

@app.route('/c_listau', methods = ['GET','POST'])
def c_listau():
    esta = User.query.filter_by(user=session['cliente']).first()
    pagina = int(request.args.get('page', 1))
    mostrar = 10
    total_estacionamientos = db.session.query(User).count()
    total_paginas = (total_estacionamientos + mostrar - 1) // mostrar
    listaUsuarios = db.session.query(User) \
                           .limit(mostrar) \
                           .offset((pagina - 1) * mostrar) \
                           .all()
    return render_template('c_listau.html',est = esta,usuario = session['cliente'],lista = listaUsuarios, pagina_actual=pagina, total_paginas=total_paginas)

@app.route('/c_boletos', methods = ['GET'])
def c_boletos():
    esta = User.query.filter_by(user=session['cliente']).first()
    pagina = int(request.args.get('page', 1))
    mostrar = 10
    total_estacionamientos = db.session.query(Boletos).count()
    total_paginas = (total_estacionamientos + mostrar - 1) // mostrar
    listaBoletos = db.session.query(Boletos) \
                           .limit(mostrar) \
                           .offset((pagina - 1) * mostrar) \
                           .all()
    return render_template('c_boletos.html',est = esta,usuario = session['cliente'],lista = listaBoletos, pagina_actual=pagina, total_paginas=total_paginas)

@app.route('/ajax-login', methods=['POST'])
def ajax_login():
    print (request.form)
    user = request.form['user']
    response = {'satus':200,'user':user,'id':1}
    return json.dumps(response) 

if __name__ == '__main__':
    app.run(port=80)
   
