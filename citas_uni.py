from playwright.sync_api import sync_playwright, TimeoutError
from dotenv import load_dotenv
import time
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import sys

# ========================
# Configuración y datos
# ========================

load_dotenv()  # Cargar variables del .env

# Datos de la cita
NOMBRE = "Gonzalo"
APELLIDO = "Ramirez Tucci"
NIE = "5555794V"
EMAIL = "gonzalo.ramirez.887@gmail.com"
TELEFONO = "643567688"

# Datos de notificación
EMAIL_ORIGEN = "agustin.jauregui2@gmail.com"
EMAIL_DESTINO = EMAIL  # Cliente
EMAIL_ME = "gonzalo.ramirez.887@gmail.com"  # Tu email
EMAIL_PASS = os.getenv("GMAIL_PASS")

# Carpeta para screenshots
os.makedirs("screenshots", exist_ok=True)


def log(msg):
    ts = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def enviar_notificacion(screenshot_path=None):
    if not EMAIL_PASS:
        log("❌ ERROR: No se encontró la variable de entorno GMAIL_PASS.")
        return

    mensaje = MIMEMultipart()
    mensaje["From"] = EMAIL_ORIGEN
    mensaje["To"] = f"{EMAIL_DESTINO}, {EMAIL_ME}"
    mensaje["Subject"] = "✅ Notificación: Cita reservada"

    # Cuerpo del mail
    cuerpo = f"¡Se ha reservado una cita para {NOMBRE} {APELLIDO}!"
    mensaje.attach(MIMEText(cuerpo, "plain"))

    # Adjuntar screenshot si existe
    if screenshot_path and os.path.exists(screenshot_path):
        with open(screenshot_path, "rb") as adjunto:
            mime_base = MIMEBase("application", "octet-stream")
            mime_base.set_payload(adjunto.read())
            encoders.encode_base64(mime_base)
            mime_base.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(screenshot_path)}"
            )
            mensaje.attach(mime_base)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            log("🔌 Conectando a Gmail...")
            server.login(EMAIL_ORIGEN, EMAIL_PASS)
            log("✅ Login correcto.")
            server.sendmail(EMAIL_ORIGEN, [EMAIL_DESTINO, EMAIL_ME], mensaje.as_string())
            log(f"📤 Email enviado a {EMAIL_DESTINO} y a {EMAIL_ME}")
    except Exception as e:
        log(f"⚠ Error al enviar el email: {e}")


def check_cita():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://citaprevia.ciencia.gob.es/qmaticwebbooking/#/")
        page.wait_for_timeout(1500)

        # Paso 1: Seleccionar trámite
        try:
            page.locator("input[aria-label*='Asistencia telefónica']").click(force=True)
            log("✔ Trámite seleccionado: Asistencia telefónica")
        except Exception as e:
            log(f"❌ No se pudo seleccionar el trámite: {e}")
            browser.close()
            return False, None

        # Paso 2: Seleccionar primer horario disponible
        try:
            primer_horario = page.locator("button.timeslot:not([disabled])").first
            primer_horario.wait_for(state="visible", timeout=3000)
            horario_seleccionado = primer_horario.inner_text()
            primer_horario.click()
            log(f"✔ Seleccionado el primer horario disponible: {horario_seleccionado}")
        except:
            log("❌ No hay horarios disponibles")
            browser.close()
            return False, None

        # Paso 3: Completar datos
        try:
            page.locator("#FirstName").wait_for(state="visible", timeout=5000)
            page.fill("#FirstName", NOMBRE)
            page.fill("#LastName", APELLIDO)
            page.fill("#CustRef", NIE)
            page.fill("#Email", EMAIL)
            page.fill("#ConfirmEmail", EMAIL)
            page.fill("#Phone", TELEFONO)
            page.fill("#ConfirmPhone", TELEFONO)
            log("✔ Datos personales completados")
        except TimeoutError:
            log("❌ El formulario no apareció en 5 segundos")
            browser.close()
            return False, None

        # Paso 4: Checkbox
        label_checkbox = page.locator('label:has-text("tratamiento de mis datos personales")')
        label_checkbox.wait_for(state="visible", timeout=5000)
        label_checkbox.scroll_into_view_if_needed()
        input_checkbox = page.locator('input[role="checkbox"][aria-labelledby="agreement"]')

        marcado = False
        start = time.time()
        while time.time() - start < 5:
            label_checkbox.click(force=True)
            time.sleep(0.2)
            if input_checkbox.get_attribute("aria-checked") == "true":
                marcado = True
                break
            input_checkbox.click(force=True)
            time.sleep(0.2)

        if marcado:
            log("✔ Checkbox marcado correctamente")
        else:
            log("❌ Checkbox no quedó marcado después de 5s.")
            browser.close()
            return False, None

        # Paso 5: Crear cita
        btn_crear = page.locator('#contactStepCreateAppointmentButton')
        btn_crear.wait_for(state="visible", timeout=5000)
        btn_crear.click(force=True)
        log("✔ Cita solicitada")

        # Esperar 2 segundos antes del screenshot
        page.wait_for_timeout(2000)

        # Paso 6: Captura
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/cita_confirmada_{timestamp}.png"
        page.screenshot(path=screenshot_path)
        log(f"📸 Screenshot de la cita confirmada: {screenshot_path}")

        return True, screenshot_path

# ========================
# Bucle principal
# ========================
while True:
    ahora = datetime.datetime.now()
    hora_inicio = datetime.time(12, 0)
    hora_fin = datetime.time(14, 15)

    if ahora.weekday() in [0, 1, 2, 3] and hora_inicio <= ahora.time() < hora_fin:
        try:
            ok, screenshot_path = check_cita()
            if ok:
                enviar_notificacion(screenshot_path)
                log(f"✅ Cita reservada correctamente. Proceso finalizado a las {datetime.datetime.now().strftime('%H:%M:%S')}")
                sys.exit(0)
        except Exception as e:
            log(f"⚠ Error durante el proceso de solicitud de cita: {e}")

        time.sleep(5)

    else:
        log("⏸ Hora límite alcanzada o fuera de horario (Lun-Jue, 12:00-14:15). Terminando script.")
        break
