from flask import Flask, render_template, request
from datetime import datetime
import os
import csv
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import white
import smtplib
from email.message import EmailMessage
import pandas as pd
from dotenv import load_dotenv

# Cargar variables del entorno .env
load_dotenv()

app = Flask(__name__)

# Rutas globales
CSV_FILE = 'base_boletos.csv'
CARPETA_BOLETAS = 'boletas'
IMAGEN_FONDO = os.path.join('static', 'portada.jpg')

# ======================
# Rutas
# ======================

@app.route('/comprar', methods=['GET', 'POST'])
def comprar():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        telefono = request.form['telefono']
        tipo = request.form['tipo']

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        id_unico = f'BOL{timestamp}'

        # Asegurar carpeta
        if not os.path.exists(CARPETA_BOLETAS):
            os.makedirs(CARPETA_BOLETAS)

        # Crear encabezado si no existe
        existe_csv = os.path.isfile(CSV_FILE)
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not existe_csv:
                writer.writerow(['ID único', 'Nombre del comprador', 'Correo', 'Teléfono', 'Estado', 'Tipo de entrada'])
            writer.writerow([id_unico, nombre, correo, telefono, 'no usado', tipo])

        # Crear boleta PDF
        ruta_pdf = os.path.join(CARPETA_BOLETAS, f'{id_unico}.pdf')
        generar_qr_pdf(id_unico, nombre, tipo, ruta_pdf)

        # Enviar al correo
        enviar_boleta(nombre, correo, ruta_pdf)

        return render_template('exito.html', nombre=nombre, correo=correo)

    return render_template('comprar.html')


@app.route('/escanear')
def escanear():
    return render_template('escanear.html')


@app.route('/verificar', methods=['POST'])
def verificar():
    codigo = request.form.get('codigo', '').strip()

    if not os.path.exists(CSV_FILE):
        return render_template('resultado.html', mensaje="⚠️ No hay base de datos.")

    try:
        df = pd.read_csv(CSV_FILE, encoding='utf-8')
    except Exception as e:
        return render_template('resultado.html', mensaje=f"❌ Error al leer base de datos: {e}")

    boleta = df[df['ID único'].astype(str).str.strip() == codigo]

    if boleta.empty:
        mensaje = f"❌ Código {codigo} no encontrado."
    else:
        estado = boleta.iloc[0]['Estado'].strip().lower()
        if estado == 'usado':
            mensaje = f"⚠️ La boleta {codigo} ya fue usada."
        else:
            df.loc[df['ID único'] == codigo, 'Estado'] = 'usado'
            df.to_csv(CSV_FILE, index=False, encoding='utf-8')
            mensaje = f"✅ Boleta {codigo} verificada correctamente."

    return render_template('resultado.html', mensaje=mensaje)


# ======================
# Generar QR + PDF
# ======================

def generar_qr_pdf(id_unico, nombre, tipo, ruta_pdf):
    data_qr = f'{id_unico};{nombre};{tipo}'
    qr = qrcode.make(data_qr)
    ruta_qr = os.path.join(CARPETA_BOLETAS, f'{id_unico}_qr.png')
    qr.save(ruta_qr)

    c = canvas.Canvas(ruta_pdf, pagesize=letter)
    width, height = letter

    if os.path.exists(IMAGEN_FONDO):
        c.drawImage(IMAGEN_FONDO, 0, 0, width=width, height=height)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2, 720, f"🎫 Boleta para: {nombre}")
    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2, 690, f"ID: {id_unico}")
    c.drawCentredString(width / 2, 660, f"Tipo de entrada: {tipo}")
    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, 630, "📅 Apertura: 20 de agosto de 2025")
    c.drawCentredString(width / 2, 610, "🎉 Evento: 22 de agosto de 2025")
    c.drawCentredString(width / 2, 590, "📍 Teatro Universidad ECCI")

    qr_x = (width - 150) / 2
    c.drawImage(ruta_qr, qr_x, 400, width=150, height=150)

    c.setFont("Helvetica-Oblique", 14)
    c.drawCentredString(width / 2, 370, f"Gracias por tu compra, {nombre}. ¡Nos vemos pronto!")

    c.save()
    os.remove(ruta_qr)


# ======================
# Enviar correo
# ======================

def enviar_boleta(nombre, correo_destino, pdf_path):
    remitente = os.getenv("GMAIL_USER")
    contrasena = os.getenv("GMAIL_PASS")

    msg = EmailMessage()
    msg['Subject'] = '🎟️ Tu boleta para el evento'
    msg['From'] = remitente
    msg['To'] = correo_destino
    msg.set_content(f"Hola {nombre},\n\nGracias por tu compra. Adjuntamos tu boleta en PDF.\n\nNos vemos en el evento.")

    with open(pdf_path, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=os.path.basename(pdf_path))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(remitente, contrasena)
        smtp.send_message(msg)


# ======================
# Iniciar
# ======================

if __name__ == '__main__':
    app.run(debug=True, port=5000)
