import streamlit as st
import streamlit as st
import psycopg2
import urllib.parse
import os
import datetime
import re
from PIL import Image

# --- CONFIGURACIÓN DE RUTAS INSTITUCIONALES (LOCAL) ---
ARCHIVO_CLAVE = "clave_acceso.txt"
CARPETA_GESTION = r"C:\Users\Usuario\Desktop\GESTION"
CARPETA_FOTOS = os.path.join(CARPETA_GESTION, "FACHADAS")
CARPETA_EXPEDIENTES = os.path.join(CARPETA_GESTION, "EXPEDIENTES")

for c in [CARPETA_GESTION, CARPETA_FOTOS, CARPETA_EXPEDIENTES]:
    if not os.path.exists(c):
        try:
            os.makedirs(c)
        except Exception:
            pass

def leer_clave():
    if os.path.exists(ARCHIVO_CLAVE):
        with open(ARCHIVO_CLAVE, "r") as f:
            return f.read().strip()
    return "1234"

def guardar_clave(nueva_clave):
    with open(ARCHIVO_CLAVE, "w") as f:
        f.write(nueva_clave)

# Base de datos LOCAL (pgAdmin / localhost) para tu operación diaria
DB_HOST = "localhost"
DB_NAME = "Gestion_db"
DB_USER = "postgres"
DB_PASS = "cabo2026"

def obtener_conexion():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        client_encoding='utf8'
    )

st.set_page_config(page_title="Gestiones - Sistema Integral Local", layout="wide")

st.markdown("""
<style>
    div.stButton > button:first-child {
        background-color: #0b2d54;
        color: white;
        border-radius: 6px;
        font-weight: bold;
    }
    div.stButton > button:first-child:hover {
        background-color: #15457a;
    }
    .caja-bloque {
        background-color: #f4f6f9;
        border: 1px solid #dcdfe6;
        border-left: 5px solid #0b2d54;
        padding: 12px 16px;
        margin-top: 14px;
        margin-bottom: 12px;
        border-radius: 6px;
    }
    .titulo-caja {
        color: #0b2d54;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- SEGURIDAD ---
if "clave_actual" not in st.session_state:
    st.session_state.clave_actual = leer_clave()
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

def limpiar_formulario():
    for key in list(st.session_state.keys()):
        if key.startswith("k_") or key.startswith("chk_") or key.startswith("rad_"):
            del st.session_state[key]

# --- PANTALLA PRINCIPAL DE ACCESO: GESTIONES ---
if not st.session_state.autenticado:
    st.markdown("<br><br><h1 style='text-align: center; color: #0b2d54; font-size: 2.8rem;'>Gestiones</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555; font-size: 1.1rem;'>Plataforma de Control, Expedientes y Licencias</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        clave_input = st.text_input("Ingrese Clave de Acceso:", type="password")
        if st.button("🔐 Ingresar al Sistema", use_container_width=True):
            if clave_input == st.session_state.clave_actual and clave_input.isnumeric():
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("❌ Clave no válida.")
    st.stop()

# --- BARRA LATERAL (CONFIGURACIÓN LOCAL + SECCIÓN DE NUBE) ---
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    nueva_clave = st.text_input("Actualizar Clave (Numérica)", type="password")
    if st.button("Guardar Clave"):
        if nueva_clave.isnumeric():
            guardar_clave(nueva_clave)
            st.session_state.clave_actual = nueva_clave
            st.success("Clave actualizada.")
        else:
            st.error("Solo dígitos numéricos.")
            
    st.markdown("---")
    st.markdown("### ☁️ Panel de Nube / Enlaces")
    st.info("Aquí puedes integrar próximamente el estatus de conexión a tu base remota o los accesos directos al portal ciudadano en internet.")

st.markdown("<h1 style='color: #0b2d54;'>Gestiones - Sistema Integral de Licencias (Local)</h1>", unsafe_allow_html=True)

# (Aquí continúa todo tu sistema maestro local con sus pestañas de Panel Central y Archivero Histórico con normalidad...)