import streamlit as st
import psycopg2
import urllib.parse
import os
import datetime
import re

# --- CONEXIÓN A LA NUBE (NEON.TECH) ---
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

st.set_page_config(page_title="Gestiones - Sistema Integral Nube", layout="wide")

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

# --- PANTALLA PRINCIPAL DE ACCESO ---
if not st.session_state.autenticado:
    st.markdown("<br><br><h1 style='text-align: center; color: #0b2d54; font-size: 2.8rem;'>Gestiones (Nube)</h1>", unsafe_allow_html=True)
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

st.markdown("<h1 style='color: #0b2d54;'>Gestiones - Sistema Integral de Licencias (Nube)</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📋 Panel Central de Gestión", "🗂️ Archivero Histórico"])

with tab1:
    col_izq, col_der = st.columns([2, 1])
    with col_izq:
        c_head1, c_head2 = st.columns([3, 1])
        with c_head1:
            st.markdown("<div class='caja-bloque'><div class='titulo-caja'>1. Ficha del Contribuyente</div></div>", unsafe_allow_html=True)
        with c_head2:
            if st.button("➕ Nuevo Registro", use_container_width=True):
                limpiar_formulario()
                st.rerun()

        fecha_ingreso = st.date_input("Fecha de Registro", datetime.date.today(), key="k_fecha")
        
        c_tram, c_gir = st.columns(2)
        with c_tram:
            tipo_tramite = st.selectbox(
                "Tipo de Trámite",
                ["Alta de Nuevo Contribuyente", "Aviso de Actividad", "Aviso de Inactividad", "Cambio de Uso de Suelo", "Cambio de Domicilio", "Actualización Nombre Comercial", "Refrendo", "Anexo (Exclusivo Hotelería)"],
                key="k_tram"
            )
        with c_gir:
            giro = st.selectbox(
                "Giro Comercial Solicitado",
                ["Minisuper / Abarrote", "Ultramarino / Licorería", "Restaurante Bar", "Restaurante Simultáneo", "Centro Nocturno / Cabaret", "Hotel (Solo Anexos)"],
                key="k_giro"
            )
            
        c_fol, c_nom = st.columns([1, 2])
        with c_fol:
            folio = st.text_input("Folio / Expediente (Número de Licencia)", key="k_folio")
        with c_nom:
            contribuyente = st.text_input("Nombre del Contribuyente o Razón Social", key="k_cont")
            
        nombre_comercial = st.text_input("Nombre Comercial del Establecimiento:", key="k_nom_com")
        direccion_escrita = st.text_input("Dirección Escrita del Establecimiento:", key="k_dir")
        
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>2. Enlace Territorial y Georreferencia</div></div>", unsafe_allow_html=True)
        enlace_mapa = st.text_input("📍 Enlace de Google Maps o Waze:", key="k_link")
        
        c_tel, c_lat, c_lon = st.columns([2, 1, 1])
        with c_tel:
            telefono = st.text_input("Teléfono de Contacto", key="k_tel")
        with c_lat:
            latitud = st.text_input("Latitud", key="k_lat")
        with c_lon:
            longitud = st.text_input("Longitud", key="k_lon")

        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>3. Auditoría de Requisitos</div></div>", unsafe_allow_html=True)
        c_ine = st.checkbox("Identificación Oficial (INE)", key="chk_ine")
        c_rfc = st.checkbox("Constancia de Situación Fiscal (RFC)", key="chk_rfc")
        c_dom = st.checkbox("Comprobante de Domicilio", key="chk_dom")
        
        observaciones = st.text_area("Bitácora de Observaciones y Faltantes:", key="k_obs")
        
        if st.button("💾 REGISTRAR EXPEDIENTE EN LA NUBE", use_container_width=True):
            if not folio or not contribuyente:
                st.warning("⚠️ Debes registrar al menos el Folio y el Contribuyente.")
            else:
                detalle_compuesto = (
                    f"Fecha: {fecha_ingreso.strftime('%d/%m/%Y')} | Tel: {telefono} | Dir: {direccion_escrita} | NomCom: {nombre_comercial} | "
                    f"Lat: {latitud} | Lon: {longitud} | Link: {enlace_mapa} | INE:{c_ine} RFC:{c_rfc} Dom:{c_dom}"
                )
                try:
                    con = obtener_conexion()
                    cur = con.cursor()
                    cur.execute(
                        "INSERT INTO tramites (tipo, folio, contribuyente, dato_actualizado, observaciones) VALUES (%s, %s, %s, %s, %s)",
                        (f"{tipo_tramite} - {giro}", folio, contribuyente, detalle_compuesto, observaciones)
                    )
                    con.commit()
                    cur.close()
                    con.close()
                    st.success("✅ Expediente almacenado correctamente en la base de datos de la nube.")
                except Exception as err:
                    st.error(f"Error al registrar: {err}")

    with col_der:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📍 Visor Satelital</div></div>", unsafe_allow_html=True)
        st.info("Ingresa latitud y longitud para previsualizar la ubicación.")

with tab2:
    st.markdown("<h2 style='color: #0b2d54;'>🗂️ Control de Registros Históricos (Nube)</h2>", unsafe_allow_html=True)
    try:
        con = obtener_conexion()
        cur = con.cursor()
        cur.execute("SELECT id, tipo, folio, contribuyente, dato_actualizado, observaciones FROM tramites ORDER BY id DESC")
        registros = cur.fetchall()
        cur.close()
        con.close()

        if not registros:
            st.info("No hay registros en el archivero histórico de la nube.")
        else:
            for r in registros:
                with st.expander(f"📁 Folio: {r[2]} — {r[3]} ({r[1]})"):
                    st.write(f"**Gestión / Giro:** {r[1]}")
                    st.markdown(f"**Datos del Trámite:** {r[4]}")
                    st.write(f"**Notas de Bitácora:** {r[5]}")
    except Exception as ex:
        st.error(f"Error al consultar el archivero: {ex}")