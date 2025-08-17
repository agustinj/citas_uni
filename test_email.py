from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText

load_dotenv()  # Esto carga automáticamente el .env

NOMBRE = "Persona"
APELLIDO = "Apellido_1"

EMAIL_ORIGEN = "agustin.jauregui2@gmail.com"
EMAIL_DESTINO = "agus_jc@hotmail.com"
EMAIL_PASS = os.getenv("GMAIL_PASS")

def enviar_notificacion():
    if not EMAIL_PASS:
        print("❌ ERROR: No se encontró la variable de entorno GMAIL_PASS.")
        return

    msg = MIMEText(f"¡Se ha reservado una cita para {NOMBRE} {APELLIDO}!")
    msg["Subject"] = "Notificación: Cita reservada"
    msg["From"] = EMAIL_ORIGEN
    msg["To"] = EMAIL_DESTINO

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            print("🔌 Conectando a Gmail...")
            server.login(EMAIL_ORIGEN, EMAIL_PASS)
            print("✅ Login correcto.")
            server.send_message(msg)
            print(f"📤 Email enviado a {EMAIL_DESTINO}")
    except Exception as e:
        print("⚠ Error al enviar el email:", e)

if __name__ == "__main__":
    enviar_notificacion()
