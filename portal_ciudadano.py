import streamlit as st
import psycopg2
import datetime

DATABASE_URL = "postgresql://neondb_owner:npg_Y6RvW8yqBGjH@ep-lingering-thunder-ar76lrca-pooler.c-4.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def obtener_conexion():
    return psycopg2.connect(DATABASE_URL, client_encoding='utf8')

st.set_page_config(page_title="Ventanilla Digital - Portal Ciudadano", layout="centered")

st.markdown("<h2 style='text-align: center; color: #0b2d54;'>XV Ayuntamiento de Los Cabos</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #555;'>Ventanilla Digital de Solicitud de Trámites y Licencias</p><br>", unsafe_allow_html=True)

with st.form("form_portal_ciudadano"):
    tipo_tramite = st.selectbox(
        "Tipo de Trámite / Solicitud",
        ["Licencia Nueva (Venta de Bebidas Alcohólicas)", "Refrendo Anual", "Cambio de Domicilio", "Cambio de Nombre Comercial", "Clausura"]
    )
    giro = st.selectbox("Giro Comercial", ["Minisuper / Abarrote", "Restaurante Bar", "Ultramarino", "Hotel"])
    
    contribuyente = st.text_input("Nombre del Propietario o Razón Social *")
    nombre_comercial = st.text_input("Nombre Comercial del Establecimiento *")
    direccion = st.text_input("Domicilio (Calle, Número, Colonia) *")
    telefono = st.text_input("Teléfono de Contacto (WhatsApp) *")
    enlace_mapa = st.text_input("Enlace de Google Maps o Waze con tu ubicación *")
    
    enviar = st.form_submit_button("📤 Enviar Solicitud", use_container_width=True)
    
    if enviar:
        if not contribuyente or not nombre_comercial or not direccion or not telefono or not enlace_mapa:
            st.error("⚠️ Por favor completa todos los campos obligatorios (*).")
        else:
            detalle = f"Tel: {telefono} | Dir: {direccion} | NomCom: {nombre_comercial} | Ubicación: {enlace_mapa} | ORIGEN: PORTAL CIUDADANO"
            try:
                con = obtener_conexion()
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO tramites (tipo, folio, contribuyente, dato_actualizado, observaciones) VALUES (%s, %s, %s, %s, %s)",
                    (f"{tipo_tramite} - {giro}", "EN REVISIÓN", contribuyente, detalle, "Enviado por ciudadano vía web.")
                )
                con.commit()
                cur.close()
                con.close()
                st.success("✅ ¡Su solicitud ha sido enviada con éxito al Ayuntamiento!")
            except Exception as e:
                st.error(f"Error al enviar: {e}")