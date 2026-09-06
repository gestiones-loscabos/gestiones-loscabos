import streamlit as st
import psycopg2
import os
import datetime

DATABASE_URL = "postgresql://neondb_owner:npg_Y6RvW8yqBGjH@ep-lingering-thunder-ar76lrca-pooler.c-4.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
ARCHIVO_CLAVE = "clave_acceso.txt"

def leer_clave():
    if os.path.exists(ARCHIVO_CLAVE):
        with open(ARCHIVO_CLAVE, "r") as f:
            return f.read().strip()
    return "1234"

def obtener_conexion():
    return psycopg2.connect(DATABASE_URL, client_encoding='utf8')

st.set_page_config(page_title="Sistema Integral - Panel Maestro", layout="wide")

if "clave_actual" not in st.session_state:
    st.session_state.clave_actual = leer_clave()
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<br><br><h1 style='text-align: center; color: #0b2d54;'>Panel Maestro de Oficina</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555;'>XV Ayuntamiento de Los Cabos - Acceso Restringido</p>", unsafe_allow_html=True)
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

st.markdown("<h1 style='color: #0b2d54;'>Sistema Integral de Licencias (Panel Maestro en Nube)</h1>", unsafe_allow_html=True)

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
        st.success(f"Conexión exitosa a Neon.tech. Se encontraron {len(registros)} registros en el sistema.")
        for r in registros:
            with st.expander(f"📁 Folio: {r[2]} — {r[3]} ({r[1]})"):
                st.write(f"**Gestión:** {r[1]}")
                st.markdown(f"**Datos:** {r[4]}")
                st.write(f"**Notas:** {r[5]}")
except Exception as ex:
    st.error(f"Error al conectar con la base de datos en la nube: {ex}")