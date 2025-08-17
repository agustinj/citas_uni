from playwright.sync_api import sync_playwright, TimeoutError
from dotenv import load_dotenv
import time
import datetime
import smtplib
from email.mime.text import MIMEText
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
EMAIL_DESTINO = EMAIL
EMAIL_PASS = os.getenv("GMAIL_PASS")

# Carpeta para screenshots
os.makedirs("screenshots", exist_ok=True)


def log(msg):
    ts = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    print(f"[{ts}] {msg}")


def enviar_notificacion():
    if not EMAIL_PASS:
        log("❌ ERROR: No se encontró la variable de entorno GMAIL_PASS.")
        return

    msg = MIMEText(f"¡Se ha reservado una cita para {NOMBRE} {APELLIDO}!")
    msg["Subject"] = "Notificación: Cita reservada"
    msg["From"] = EMAIL_ORIGEN
    msg["To"] = EMAIL_DESTINO

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            log("🔌 Conectando a Gmail...")
            server.login(EMAIL_ORIGEN, EMAIL_PASS)
            log("✅ Login correcto.")
            server.send_message(msg)
            log(f"📤 Email enviado a {NOMBRE} {APELLIDO}")
    except Exception as e:
        log(f"⚠ Error al enviar el email: {e}")


def check_cita():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://citaprevia.ciencia.gob.es/qmaticwebbooking/#/")
        page.wait_for_timeout(1500)

        # Paso 1: Seleccionar trámite "Asistencia telefónica"
        try:
            page.locator("input[aria-label*='Asistencia telefónica']").click(force=True)
            log("✔ Trámite seleccionado: Asistencia telefónica")
        except Exception as e:
            log(f"❌ No se pudo seleccionar el trámite: {e}")
            browser.close()
            return False

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
            return False

        # Paso 3: Completar datos personales
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
            return False

        # Paso 4: Marcar checkbox de términos y condiciones
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
            log(f"❌ Checkbox no quedó marcado después de 5s.")
            browser.close()
            return False

        # Paso 5: Solicitar cita
        btn_crear = page.locator('#contactStepCreateAppointmentButton')
        btn_crear.wait_for(state="visible", timeout=5000)
        btn_crear.click(force=True)
        log("✔ Cita solicitada")

        # Paso 6: Captura de pantalla del formulario listo
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/cita_confirmada_{timestamp}.png"
        page.screenshot(path=screenshot_path)
        log(f"📸 Screenshot de formulario listo: {screenshot_path}")

        return True

# ========================
# Bucle principal
# ========================
while True:
    ahora = datetime.datetime.now()
    # Domingos (6) a jueves (3), de 12 a 15
    
    if ahora.weekday() in [6, 0, 1, 2, 3] and 12 <= ahora.hour < 15:
        try:
            if check_cita():
                # Paso 7: Notificación y cierre
                enviar_notificacion()
                log(f"✅ Cita reservada correctamente y mail enviado al cliente. Proceso finalizado a las {datetime.datetime.now().strftime('%H:%M:%S')}")
                
                # Pausa para que puedas ver Chromium manualmente
                input("💡 Presioná Enter cuando quieras cerrar el script y terminar la ejecución...")

                import sys
                sys.exit(0)  # Salir de todo el script

        except Exception as e:
            log(f"⚠ Error durante el proceso de solicity de cita: {e}")

        time.sleep(5)  # Reintento rápido

    else:
        log("⏸ Fuera de horario configurado (Dom-Jue, 12-15h)")
        time.sleep(300)  # Espera 5 minutos
