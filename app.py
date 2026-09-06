import streamlit as st
import psycopg2
import urllib.parse
import os
import datetime
import re
from PIL import Image

# --- CONFIGURACIÓN DE RUTAS Y CONEXIÓN A LA NUBE (NEON.TECH) ---
DATABASE_URL = "postgresql://neondb_owner:npg_Y6RvW8yqBGjH@ep-lingering-thunder-ar76lrca-pooler.c-4.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
ARCHIVO_CLAVE = "clave_acceso.txt"

def leer_clave():
    if os.path.exists(ARCHIVO_CLAVE):
        with open(ARCHIVO_CLAVE, "r") as f:
            return f.read().strip()
    return "1234"

def guardar_clave(nueva_clave):
    with open(ARCHIVO_CLAVE, "w") as f:
        f.write(nueva_clave)

def obtener_conexion():
    return psycopg2.connect(DATABASE_URL, client_encoding='utf8')

# Inicializar tabla en la nube si no existe
try:
    con_init = obtener_conexion()
    cur_init = con_init.cursor()
    cur_init.execute("""
        CREATE TABLE IF NOT EXISTS tramites (
            id SERIAL PRIMARY KEY,
            tipo VARCHAR(255),
            folio VARCHAR(100),
            contribuyente VARCHAR(255),
            dato_actualizado TEXT,
            observaciones TEXT
        )
    """)
    con_init.commit()
    cur_init.close()
    con_init.close()
except Exception:
    pass

st.set_page_config(page_title="Sistema Integral - Panel Maestro", layout="wide")

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

# --- PANTALLA DE ACCESO MAESTRO ---
if not st.session_state.autenticado:
    st.markdown("<br><br><h1 style='text-align: center; color: #0b2d54; font-size: 2.8rem;'>Panel Maestro de Oficina</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555; font-size: 1.1rem;'>XV Ayuntamiento de Los Cabos - Acceso Restringido</p>", unsafe_allow_html=True)
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

st.markdown("<h1 style='color: #0b2d54;'>Sistema Integral de Licencias (Panel Maestro)</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📋 Panel Central de Gestión", "🗂️ Archivero Histórico"])

with tab1:
    st.info("👋 Panel maestro activo en la nube conectado a Neon.tech. Aquí puedes registrar trámites, consultar el mapa y revisar el archivo histórico.")
    # Aquí puedes integrar el resto de tus campos de captura del maestro si lo deseas, o usar la base sincronizada.

with tab2:
    st.markdown("<h2 style='color: #0b2d54;'>🗂️ Control de Registros en la Nube</h2>", unsafe_allow_html=True)
    try:
        con = obtener_conexion()
        cur = con.cursor()
        cur.execute("SELECT id, tipo, folio, contribuyente, dato_actualizado, observaciones FROM tramites ORDER BY id DESC")
        registros = cur.fetchall()
        cur.close()
        con.close()

        if not registros:
            st.info("No hay trámites registrados todavía en la base de datos de la nube.")
        else:
            for r in registros:
                with st.expander(f"📁 Folio: {r[2]} — {r[3]} ({r[1]})"):
                    st.write(f"**Gestión:** {r[1]}")
                    st.markdown(f"**Datos:** {r[4]}")
                    st.write(f"**Notas:** {r[5]}")
    except Exception as ex:
        st.error(f"Error al consultar la base de datos: {ex}")