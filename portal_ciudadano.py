import streamlit as st
import psycopg2
import urllib.parse
import os
import datetime
import re

# --- CONEXIÓN A LA BASE DE DATOS EN LA NUBE (NEON.TECH) ---
DATABASE_URL = "postgresql://neondb_owner:npg_Y6RvW8yqBGjH@ep-lingering-thunder-ar76lrca-pooler.c-4.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def obtener_conexion():
    return psycopg2.connect(DATABASE_URL, client_encoding='utf8')

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

st.set_page_config(page_title="Ventanilla Digital - Portal Ciudadano", layout="wide")

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
        background-color: #f8f9fa;
        border: 1px solid #e5e7eb;
        border-left: 4px solid #0b2d54;
        padding: 10px 14px;
        margin-top: 10px;
        margin-bottom: 10px;
        border-radius: 4px;
    }
    .titulo-caja {
        color: #0b2d54;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<br><h1 style='text-align: center; color: #0b2d54;'>XV Ayuntamiento de Los Cabos</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #555; font-size: 1.2rem;'>Ventanilla Digital de Registro de Trámites y Licencias</p><br>", unsafe_allow_html=True)

with st.form("form_ciudadano"):
    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>1. Datos Generales del Solicitante y Establecimiento</div></div>", unsafe_allow_html=True)
    
    c_tram, c_gir = st.columns(2)
    with c_tram:
        tipo_tramite = st.selectbox(
            "Tipo de Trámite / Solicitud",
            [
                "Solicitud de Licencia Nueva con Venta de Bebidas Alcohólicas",
                "01.- Clausura Definitiva",
                "02.- Cambio de Propietario / Traspaso",
                "03.- Cambio de Denominación o Razón Social",
                "04.- Cambio de Domicilio",
                "05.- Cambio de Actividad / Giro Comercial",
                "Refrendo de Licencia de Alcohol",
                "Anexo de Bebidas Alcohólicas (Exclusivo Hotelería)"
            ]
        )
    with c_gir:
        giro = st.selectbox(
            "Giro o Actividad",
            ["Minisuper / Abarrote", "Ultramarino / Licorería", "Restaurante Bar", "Restaurante Simultáneo", "Centro Nocturno / Cabaret", "Hotel (Solo Anexos)"]
        )

    c_fol, c_nom = st.columns([1, 2])
    with c_fol:
        folio = st.text_input("Número de Folio (Si ya cuenta con uno o dejar en trámite):", value="S/F")
    with c_nom:
        contribuyente = st.text_input("Nombre del Propietario o Razón Social *")

    c_com1, c_com2 = st.columns([2, 1])
    with c_com1:
        nombre_comercial = st.text_input("Nombre Comercial del Establecimiento *")
    with c_com2:
        tipo_establecimiento = st.selectbox("Característica:", ["Único", "Matriz", "Sucursal"])

    direccion_escrita = st.text_input("Domicilio del Establecimiento (Calle, Número, Colonia) *")
    
    c_mz, c_lt, c_cve = st.columns(3)
    with c_mz:
        manzana_cat = st.text_input("Manzana:")
    with c_lt:
        lote_cat = st.text_input("Lote:")
    with c_cve:
        clave_catastral = st.text_input("Clave Catastral (Opcional):")
        
    cat_str = f"Mz: {manzana_cat} | Lt: {lote_cat} | Clave: {clave_catastral}"

    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>2. Ubicación del Establecimiento</div></div>", unsafe_allow_html=True)
    
    st.markdown("""
        <div style="background-color: #eef2f7; padding: 12px; border-radius: 6px; margin-bottom: 10px;">
            <p style="margin: 0; font-size: 0.95rem; color: #0b2d54; font-weight: bold;">
                💡 Instrucción de Ubicación:
            </p>
            <p style="margin: 4px 0 0 0; font-size: 0.85rem; color: #555;">
                Escribe las coordenadas de tu ubicación (Ej. 23.05, -109.70) o pega el enlace largo de Google Maps del navegador.
            </p>
        </div>
    """, unsafe_allow_html=True)

    c_lat, c_lon = st.columns(2)
    with c_lat:
        lat_input = st.text_input("Latitud:", value="")
    with c_lon:
        lon_input = st.text_input("Longitud:", value="")

    enlace_mapa = st.text_input("O pega aquí el enlace de Google Maps:")
    telefono = st.text_input("Teléfono de Contacto (WhatsApp) *")

    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>3. Requisitos y Carga de Documentos Digitales</div></div>", unsafe_allow_html=True)
    st.write("Marca los documentos con los que cuentas y adjúntalos (PDF o fotografía clara):")
    
    c_sol_giros = st.checkbox("Solicitud Oficial debidamente llenada")
    c_ine = st.checkbox("Identificación Oficial (INE)")
    c_rfc = st.checkbox("Constancia de Situación Fiscal (RFC)")
    c_dom = st.checkbox("Comprobante de Domicilio")
    c_agua = st.checkbox("Comprobante de Agua Potable al corriente (OOMSAPAS)")
    c_predial = st.checkbox("Recibo de Impuesto Predial Vigente")
    c_croquis = st.checkbox("Croquis de Localización")

    st.markdown("<p style='font-weight: bold; color: #0b2d54; margin-top: 15px;'>📁 Adjuntar Documentación Requerida:</p>", unsafe_allow_html=True)
    
    archivo_ine = st.file_uploader("Subir INE / Identificación Oficial (PDF o Imagen)", type=["pdf", "png", "jpg", "jpeg"])
    archivo_rfc = st.file_uploader("Subir Constancia Fiscal / RFC (PDF o Imagen)", type=["pdf", "png", "jpg", "jpeg"])
    archivo_domicilio = st.file_uploader("Subir Comprobante de Domicilio / Predial / Agua (PDF o Imagen)", type=["pdf", "png", "jpg", "jpeg"])
    archivo_croquis = st.file_uploader("Subir Croquis o Documentos Adicionales (PDF o Imagen)", type=["pdf", "png", "jpg", "jpeg"])

    observaciones = st.text_area("Comentarios adicionales o dudas sobre tu trámite:")

    enviar_btn = st.form_submit_button("🚀 Enviar Registro y Documentos a la Ventanilla", use_container_width=True)

    if enviar_btn:
        if not contribuyente or not nombre_comercial or not direccion_escrita or not telefono:
            st.error("⚠️ Por favor completa los campos obligatorios (*): Propietario, Nombre Comercial, Domicilio y Teléfono.")
        else:
            lat_res, lon_res = lat_input, lon_input
            
            if enlace_mapa:
                limpio = urllib.parse.unquote(enlace_mapa)
                m1 = re.search(r"@([-\d.]+),([-\d.]+)", limpio)
                m2 = re.search(r"ll=([-\d.]+),([-\d.]+)", limpio)
                m3 = re.search(r"[?&]q=([-\d.]+)[,%](?:2C)?([-\d.]+)", limpio)
                m4 = re.search(r"q=([-\d.]+),([-\d.]+)", limpio)
                m5 = re.search(r"([-\d]{2,3}\.\d+)[,\s]+([-\d]{2,4}\.\d+)", limpio)
                
                if m1: lat_res, lon_res = m1.group(1), m1.group(2)
                elif m2: lat_res, lon_res = m2.group(1), m2.group(2)
                elif m3: lat_res, lon_res = m3.group(1), m3.group(2)
                elif m4: lat_res, lon_res = m4.group(1), m4.group(2)
                elif m5: lat_res, lon_res = m5.group(1), m5.group(2)

            nombres_archivos = []
            if archivo_ine: nombres_archivos.append(f"INE:{archivo_ine.name}")
            if archivo_rfc: nombres_archivos.append(f"RFC:{archivo_rfc.name}")
            if archivo_domicilio: nombres_archivos.append(f"Dom:{archivo_domicilio.name}")
            if archivo_croquis: nombres_archivos.append(f"Croquis/Extra:{archivo_croquis.name}")
            
            str_archivos = " | Archivos: " + (", ".join(nombres_archivos) if nombres_archivos else "Ninguno adjunto")

            detalle_compuesto = (
                f"Fecha: {datetime.date.today().strftime('%d/%m/%Y')} | Tel: {telefono} | Dir: {direccion_escrita} | NomCom: {nombre_comercial} | "
                f"TipoEst: {tipo_establecimiento} | Cat: {cat_str} | Lat: {lat_res} | Lon: {lon_res} | LinkMaps: {enlace_mapa} | "
                f"SolGiros:{c_sol_giros} INE:{c_ine} RFC:{c_rfc} Dom:{c_dom} Agua:{c_agua} Predial:{c_predial} Croquis:{c_croquis}"
                f"{str_archivos}"
            )
            
            try:
                con = obtener_conexion()
                cur = con.cursor()
                cur.execute(
                    "INSERT INTO tramites (tipo, folio, contribuyente, dato_actualizado, observaciones) VALUES (%s, %s, %s, %s, %s)",
                    (f"{tipo_tramite} - {giro}", folio if folio else "S/F", contribuyente, detalle_compuesto, observaciones)
                )
                con.commit()
                cur.close()
                con.close()
                st.success("✅ ¡Su registro y documentación han sido enviados exitosamente al XV Ayuntamiento de Los Cabos!")
            except Exception as err:
                st.error(f"Error al registrar su trámite: {err}")