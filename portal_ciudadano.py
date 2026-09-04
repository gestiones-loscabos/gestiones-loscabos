import streamlit as st
import psycopg2
import urllib.parse
import re
import datetime

# Conexión a la base de datos central en la nube
DATABASE_URL = "postgresql://neondb_owner:npg_Y6RvW8yqBGjH@ep-lingering-thunder-ar76lrca-pooler.c-4.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def obtener_conexion():
    return psycopg2.connect(DATABASE_URL, client_encoding='utf8')

st.set_page_config(page_title="Registro de Trámites - Los Cabos", layout="centered")

st.markdown("""
<style>
    div.stButton > button:first-child {
        background-color: #0b2d54;
        color: white;
        border-radius: 6px;
        font-weight: bold;
        width: 100%;
        padding: 10px;
    }
    div.stButton > button:first-child:hover {
        background-color: #15457a;
    }
    .header-box {
        background-color: #f8f9fa;
        border-left: 5px solid #0b2d54;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='header-box'><h2 style='color:#0b2d54; margin:0;'>Ventanilla Digital de Registro</h2><p style='margin:0; color:#555;'>Ingreso de datos preliminares para apertura de expediente de licencia comercial</p></div>", unsafe_allow_html=True)

with st.form("form_ciudadano", clear_on_submit=True):
    st.subheader("1. Datos del Solicitante y Establecimiento")
    contribuyente = st.text_input("Nombre completo del Propietario o Razón Social *")
    nombre_comercial = st.text_input("Nombre Comercial del Establecimiento (como aparece en fachada) *")
    telefono = st.text_input("Teléfono de Contacto WhatsApp (10 dígitos) *")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        tipo_tramite = st.selectbox("Trámite a realizar", [
            "Solicitud de Licencia Nueva con Venta de Bebidas Alcohólicas",
            "Licencia Nueva Comercial (Sin Alcohol)",
            "Refrendo de Licencia",
            "Cambio de Domicilio",
            "Cambio de Giro o Actividad"
        ])
    with col_t2:
        giro = st.selectbox("Giro Comercial", [
            "Minisuper / Abarrote",
            "Ultramarino / Licorería",
            "Restaurante Bar",
            "Restaurante Simultáneo",
            "Comercio General / Servicios",
            "Otro"
        ])

    st.subheader("2. Ubicación del Inmueble")
    direccion = st.text_input("Calle, Número exterior/interior y Colonia *")
    
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        mz = st.text_input("Manzana")
    with col_c2:
        lt = st.text_input("Lote")
    with col_c3:
        clave_cat = st.text_input("Clave Catastral (si cuenta con ella)")

    link_mapa = st.text_input("📍 Enlace de ubicación de Google Maps o Waze (opcional)")
    notas = st.text_area("Observaciones o especificaciones adicionales del local")

    enviado = st.form_submit_button("📤 Enviar Registro para Apertura de Expediente")

if enviado:
    if not contribuyente or not telefono or not nombre_comercial:
        st.error("Por favor complete los campos obligatorios marcados con (*).")
    else:
        # Extracción automática de coordenadas si pegaron link
        lat_res, lon_res = "", ""
        if link_mapa:
            limpio = urllib.parse.unquote(link_mapa)
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

        fecha_hoy = datetime.date.today().strftime('%d/%m/%Y')
        cat_str = f"Mz: {mz} | Lt: {lt} | Clave: {clave_cat}"
        
        # Generar folio preliminar de registro externo
        folio_temporal = f"REG-{datetime.datetime.now().strftime('%m%d%H%M')}"
        
        detalle_compuesto = (
            f"Fecha: {fecha_hoy} | Tel: {telefono} | Dir: {direccion} | NomCom: {nombre_comercial} | "
            f"TipoEst: Único | Cat: {cat_str} | Propiedad: Pendiente | Lat: {lat_res} | Lon: {lon_res} | Link: {link_mapa} | Foto:  | "
            f"Origen: Registro_Ciudadano_Web"
        )
        
        try:
            con = obtener_conexion()
            cur = con.cursor()
            cur.execute(
                "INSERT INTO tramites (tipo, folio, contribuyente, dato_actualizado, observaciones) VALUES (%s, %s, %s, %s, %s)",
                (f"{tipo_tramite} - {giro}", folio_temporal, contribuyente, detalle_compuesto, f"Ingresado vía portal web. Notas: {notas}")
            )
            con.commit()
            cur.close()
            con.close()
            st.success(f"✅ Su información ha sido enviada correctamente. Se ha generado el folio de recepción preliminar: **{folio_temporal}**. Un gestor se comunicará vía WhatsApp.")
        except Exception as e:
            st.error(f"Error al enviar registro: {e}")