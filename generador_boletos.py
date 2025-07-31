import qrcode
import pandas as pd
from fpdf import FPDF
import os

# Leer datos desde archivo CSV
df = pd.read_csv("base_boletos.csv")

# Crear carpeta de salida si no existe
os.makedirs("boletos", exist_ok=True)

for index, row in df.iterrows():
    id_boleto = row['ID único']
    nombre = row['Nombre del comprador']
    tipo = row['Tipo de entrada']

    # Crear QR
    qr = qrcode.make(id_boleto)
    qr_filename = f"boletos/{id_boleto}.png"
    qr.save(qr_filename)

    # Crear PDF
    pdf = FPDF()
    pdf.add_page()

    # Insertar imagen de portada (si existe)
    if os.path.exists("portada.jpg"):
        pdf.image("portada.jpg", x=10, y=10, w=190)
        y_text = 80
    else:
        y_text = 20

    # Agregar texto al boleto
    pdf.set_font("Arial", size=14)
    pdf.set_y(y_text)
    pdf.cell(200, 10, txt="Boleto - Evento Radio EPE", ln=1, align="C")
    pdf.cell(200, 10, txt=f"Nombre: {nombre}", ln=2, align="L")
    pdf.cell(200, 10, txt=f"Tipo de entrada: {tipo}", ln=3, align="L")

    # Agregar QR
    pdf.image(qr_filename, x=70, y=pdf.get_y() + 10, w=60, h=60)

    # Crear nombre del archivo sin acentos ni caracteres especiales
    nombre_archivo = nombre.encode('ascii', 'ignore').decode().replace(' ', '_')
    pdf.output(f"boletos/{nombre_archivo}_boleto.pdf")

print("✅ Boletos generados correctamente.")
