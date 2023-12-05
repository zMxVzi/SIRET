from flask import request
import qrcode
import base64
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.units import inch
from models import Tarifas, Boletos, db
from datetime import datetime


class Ticket:
    def gen_qr(id):
        host = request.url
        partes_url = host.split("/")  # Divide la cadena en partes usando "/" como delimitador
        url = "/".join(partes_url[:3])  # Toma las primeras tres partes y las une de nuevo con "/"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(str(url + "/calculoqr?id=" + str(id)))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img_bytes_io = BytesIO()
        img.save(img_bytes_io)
        img_data = img_bytes_io.getvalue()
        img_data = base64.b64encode(img_bytes_io.getvalue()).decode('utf-8')
        print(img_data)
        return img_data

    def gen_pdf(boleto):
        pdf_filename = "ticket.pdf"
        doc = SimpleDocTemplate(pdf_filename, pagesize=letter)

        # Generar el código QR
        qr_data = Ticket.gen_qr(boleto.id)
        qr_image = Image(BytesIO(base64.b64decode(qr_data)))

        # Datos para la tabla
        if boleto.estado == 'Pendiente':
            color = colors.red
        else:
            color = colors.green

        if boleto.salida is None:
            data_table = [
                ["ESTADO:", str(boleto.estado)],
                ["Nombre de Estacionamiento:", str(boleto.estacionamiento)],
                ["No. de Ticket:", str(boleto.id)],
                ["Fecha y Hora de Entrada:", str(boleto.entrada)],
                ["Fecha y Hora de Salida:","--"],
                ["Tarifa:","--"],
            ]
        else:
            data_table = [
                ["ESTADO:", str(boleto.estado)],
                ["Nombre de Estacionamiento:", str(boleto.estacionamiento)],
                ["No. de Ticket:", str(boleto.id)],
                ["Fecha y Hora de Entrada:", str(boleto.entrada)],
                ["Fecha y Hora de Salida:", str(boleto.salida)],
                ["Tarifa:", "$" + str(boleto.tarifa)],
            ]

        # Definir la tabla
        table = Table(data_table, colWidths=[2 * inch, 3 * inch])

        # Estilos de la tabla
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ]))

        # Datos para el código QR
        data_qr = [[qr_image]]

        # Definir la tabla para el código QR
        table_qr = Table(data_qr, colWidths=[2 * inch, 3 * inch])

        # Estilos de la tabla para el código QR
        table_qr.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))

        # Construir el PDF
        content = [table, table_qr]
        doc.build(content)
        return pdf_filename

    def calculo_t(boleto, salida, esta):
        Boletos.query.filter_by(id=boleto.id).update(
            dict(salida=salida))
        db.session.commit()
        boleto = Boletos.query.filter_by(id=boleto.id).first()
        fecha1_dt = datetime.strptime(str(boleto.entrada), '%Y-%m-%d %H:%M:%S')
        fecha2_dt = datetime.strptime(str(boleto.salida), '%Y-%m-%d %H:%M:%S')
        tiempo = fecha2_dt - fecha1_dt
        tiempo = tiempo.total_seconds() / 60
        tarifa = Tarifas.query.filter_by(estacionamiento=esta.estacionamiento).first()
        if tiempo <= 15:
            total = 0
        elif tiempo <= 120:
            total = tarifa.primeras_dos
        elif tiempo >= 121:
            tiempo = tiempo - 120
            if tiempo <= 59:
                total = tarifa.primeras_dos + tarifa.extra
            else:
                total = (tiempo // 60) * tarifa.extra + tarifa.primeras_dos
        return total
