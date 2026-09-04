import streamlit as st
import psycopg2
import urllib.parse
import os
import datetime
import re
from PIL import Image

# --- CONFIGURACIÓN DE RUTAS INSTITUCIONALES ---
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

# --- CONEXIÓN A LA BASE DE DATOS EN LA NUBE (NEON.TECH) ---
DATABASE_URL = "postgresql://neondb_owner:npg_Y6RvW8yqBGjH@ep-lingering-thunder-ar76lrca-pooler.c-4.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

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

st.set_page_config(page_title="Gestiones - Sistema Integral", layout="wide")

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
        padding: 8px 12px;
        margin-top: 8px;
        margin-bottom: 8px;
        border-radius: 4px;
    }
    .titulo-caja {
        color: #0b2d54;
        font-weight: bold;
        font-size: 1.05rem;
        margin-bottom: 4px;
    }
    .sub-caja {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-left: 4px solid #1a5276;
        padding: 6px 10px;
        margin-top: 12px;
        margin-bottom: 6px;
        border-radius: 4px;
        font-weight: bold;
        color: #1a5276;
        font-size: 0.95rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
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

# --- ACCESO INSTITUCIONAL ---
if not st.session_state.autenticado:
    st.markdown("<br><br><h1 style='text-align: center; color: #0b2d54; font-size: 2.8rem;'>Gestiones</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555; font-size: 1.1rem;'>Plataforma de Control, Expedientes y Licencias (Nube)</p>", unsafe_allow_html=True)
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

# Función generadora del formato oficial administrativo imprimible
def generar_impresion_expediente(folio_p, cont_p, nom_com_p, tram_p, giro_p, fecha_p, dir_p, cat_datos_p, tel_p, lat_p, lon_p, prop_p, req_dict, obs_p, ruta_foto_p=""):
    def marca(valor):
        return "<span style='color:green; font-weight:bold;'>[ CUMPLE ]</span>" if valor else "<span style='color:red; font-weight:bold;'>[ PENDIENTE ]</span>"

    foto_html = ""
    if ruta_foto_p and os.path.exists(ruta_foto_p):
        import base64
        with open(ruta_foto_p, "rb") as img_f:
            b64_foto = base64.b64encode(img_f.read()).decode()
            foto_html = f"""
            <div style='margin-top: 12px; text-align: center;'>
                <h4>EVIDENCIA FOTOGRÁFICA DEL ESTABLECIMIENTO</h4>
                <img src='data:image/jpeg;base64,{b64_foto}' style='max-width: 420px; max-height: 260px; border: 1px solid #333; border-radius: 4px;'/>
            </div>
            """

    contenido_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset='utf-8'>
        <title>Expediente Oficial - {folio_p}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 25px; color: #111; font-size: 11px; line-height: 1.3; }}
            .header {{ text-align: center; border-bottom: 2px solid #0b2d54; padding-bottom: 6px; margin-bottom: 10px; }}
            .header h2 {{ margin: 0; color: #0b2d54; font-size: 15px; text-transform: uppercase; }}
            .header h3 {{ margin: 3px 0; color: #444; font-size: 12px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 5px; margin-bottom: 5px; }}
            th, td {{ border: 1px solid #999; padding: 4px 6px; text-align: left; vertical-align: middle; }}
            th {{ background-color: #f0f3f6; color: #0b2d54; font-size: 10.5px; }}
            .seccion {{ background-color: #0b2d54; color: white; padding: 4px 6px; font-weight: bold; margin-top: 8px; font-size: 11px; }}
            .bitacora {{ border: 1px solid #999; padding: 6px; min-height: 40px; background-color: #fafafa; margin-top: 4px; }}
        </style>
    </head>
    <body>
        <div class='header'>
            <h2>Cédula de Auditoría y Trámite - Gestiones</h2>
            <h3>Dirección Municipal de Ingresos | Departamento de Giros Comerciales</h3>
            <p style='margin: 0; font-size: 10.5px;'><b>EXPEDIENTE TÉCNICO OFICIAL DE REGULACIÓN DE LICENCIAS DE FUNCIONAMIENTO</b></p>
        </div>

        <table>
            <tr>
                <th style='width: 20%;'>Folio de Licencia:</th>
                <td style='width: 30%; font-weight: bold; font-size: 12px;'>{folio_p}</td>
                <th style='width: 20%;'>Fecha de Trámite:</th>
                <td style='width: 30%;'>{fecha_p}</td>
            </tr>
            <tr>
                <th>Nombre Comercial:</th>
                <td colspan='3' style='font-weight: bold; color: #0b2d54; font-size: 12px;'>{nom_com_p if nom_com_p else "NO ESPECIFICADO"}</td>
            </tr>
            <tr>
                <th>Contribuyente / Razón Social:</th>
                <td colspan='3'>{cont_p}</td>
            </tr>
            <tr>
                <th>Trámite Solicitado:</th>
                <td>{tram_p}</td>
                <th>Giro o Actividad:</th>
                <td><b>{giro_p}</b></td>
            </tr>
            <tr>
                <th>Dirección del Inmueble:</th>
                <td colspan='3'>{dir_p}</td>
            </tr>
            <tr>
                <th>Datos Catastrales:</th>
                <td>{cat_datos_p}</td>
                <th>Coordenadas Satelitales:</th>
                <td>{lat_p}, {lon_p}</td>
            </tr>
            <tr>
                <th>Teléfono de Contacto:</th>
                <td>{tel_p}</td>
                <th>Régimen del Inmueble:</th>
                <td>{prop_p}</td>
            </tr>
        </table>

        <div class='seccion'>1. BASE DOCUMENTAL, PERSONALIDAD Y GIROS COMERCIALES</div>
        <table>
            <tr><td>Solicitud Oficial de Giros Comerciales / Restringidos (Nueva o Multitrámite)</td><td style='width: 22%; text-align:center;'>{marca(req_dict.get('sol_giros'))}</td></tr>
            <tr><td>Copia de Identificación Oficial del Solicitante o Representante Legal</td><td style='text-align:center;'>{marca(req_dict.get('ine'))}</td></tr>
            <tr><td>Copia del Acta Constitutiva (Persona Moral) y/o Poder Notarial</td><td style='text-align:center;'>{marca(req_dict.get('acta_poder'))}</td></tr>
            <tr><td>Copia de Constancia de Situación Fiscal ante el SAT (RFC)</td><td style='text-align:center;'>{marca(req_dict.get('rfc'))}</td></tr>
            <tr><td>Comprobante de Domicilio Oficial Vigente</td><td style='text-align:center;'>{marca(req_dict.get('dom'))}</td></tr>
            <tr><td>Copia de Comprobante de Agua Potable Pagado al Corriente (OOMSAPAS)</td><td style='text-align:center;'>{marca(req_dict.get('agua'))}</td></tr>
            <tr><td>Copia del Recibo Oficial de Pago del Impuesto Predial del Ejercicio Vigente</td><td style='text-align:center;'>{marca(req_dict.get('predial'))}</td></tr>
            <tr><td>Copia del Registro Oficial ante Cámara Empresarial (SIEM)</td><td style='text-align:center;'>{marca(req_dict.get('siem'))}</td></tr>
            <tr><td>Pago Oficial de Derechos de Licencia o Recepción ante Tesorería</td><td style='text-align:center;'>{marca(req_dict.get('pago_der'))}</td></tr>
        </table>

        <div class='seccion'>2. ACREDITACIÓN LEGAL DEL INMUEBLE Y DEL ARRENDADOR</div>
        <table>
            <tr><td>Contrato Catastrado, Título/Escritura, Comodato o Carta de Préstamo Vigente</td><td style='width: 22%; text-align:center;'>{marca(req_dict.get('prop_legal'))}</td></tr>
            <tr><td>Copia de la Identificación Oficial del Arrendador / Propietario del Inmueble</td><td style='text-align:center;'>{marca(req_dict.get('ine_arr'))}</td></tr>
        </table>

        <div class='seccion'>3. PLANIMETRÍA Y EVIDENCIA FÍSICA</div>
        <table>
            <tr><td>Croquis de Localización indicando Manzana, Lote y Clave Catastral</td><td style='width: 22%; text-align:center;'>{marca(req_dict.get('croquis'))}</td></tr>
            <tr><td>Fotografías del Exterior e Interior (Totalidad del local e instalaciones sanitarias)</td><td style='text-align:center;'>{marca(req_dict.get('fotos'))}</td></tr>
        </table>

        <div class='seccion'>4. DICTÁMENES TÉCNICOS Y ANUENCIAS POR DEPENDENCIA</div>
        <table>
            <tr><th colspan='2'>Desarrollo Urbano (Licencia de Uso de Suelo)</th></tr>
            <tr><td>Solicitud Oficial de Uso de Suelo Firmada</td><td style='width: 22%; text-align:center;'>{marca(req_dict.get('suelo_sol'))}</td></tr>
            <tr><td>Copia de Escrituras Completas con Sello de Registro Público (RPP)</td><td style='text-align:center;'>{marca(req_dict.get('suelo_rpp'))}</td></tr>
            <tr><td>Dictamen de Uso de Suelo Favorable o Recibo de Pago de Derechos</td><td style='text-align:center;'>{marca(req_dict.get('suelo_der'))}</td></tr>

            <tr><th colspan='2'>Protección Civil Municipal</th></tr>
            <tr><td>Solicitud Oficial de Inspección Firmada (Original y 2 copias) y Expediente PDF</td><td style='width: 22%; text-align:center;'>{marca(req_dict.get('pc_sol'))}</td></tr>
            <tr><td>Recibo Oficial de Pago de Derechos de Inspección Municipal</td><td style='text-align:center;'>{marca(req_dict.get('pc_pago'))}</td></tr>
            <tr><td>Extintores vigentes, Detectores de Humo y Señalética Normativa</td><td style='text-align:center;'>{marca(req_dict.get('pc_ext'))}</td></tr>
            <tr><td>Bitácoras de Mantenimiento de Instalaciones Eléctricas y Gas LP</td><td style='text-align:center;'>{marca(req_dict.get('pc_inst'))}</td></tr>

            <tr><th colspan='2'>Ecología y Medio Ambiente (Dictamen Ambiental)</th></tr>
            <tr><td>Solicitud Oficial Ambiental Firmada y Pago de Derechos de Trámite</td><td style='width: 22%; text-align:center;'>{marca(req_dict.get('eco_sol'))}</td></tr>
            <tr><td>Factibilidad / Recibo de Agua OOMSAPAS (Vigencia menor a 2 meses)</td><td style='text-align:center;'>{marca(req_dict.get('eco_agua'))}</td></tr>
            <tr><td>Contrato y Factura de Recolección de RSU y Residuos Especiales (< 3 meses)</td><td style='text-align:center;'>{marca(req_dict.get('eco_rsu'))}</td></tr>
            <tr><td>Póliza y Certificado Vigente de Fumigación (< 3 meses)</td><td style='text-align:center;'>{marca(req_dict.get('eco_fum'))}</td></tr>
            <tr><td>Contrato / Manifiesto de Residuos Peligrosos y Aceites Usados</td><td style='text-align:center;'>{marca(req_dict.get('eco_pel'))}</td></tr>
            <tr><td>Memoria Descriptiva del Proceso Operativo y Croquis Interior</td><td style='text-align:center;'>{marca(req_dict.get('eco_mem'))}</td></tr>

            <tr><th colspan='2'>OOMSAPAS (Descarga de Aguas Residuales y Trampas de Grasa)</th></tr>
            <tr><td>Solicitud de Permiso de Descarga Residual a la Red y Pago Oficial</td><td style='width: 22%; text-align:center;'>{marca(req_dict.get('ooms_sol'))}</td></tr>
            <tr><td>Plano / Croquis Hidrosanitario y Pluvial del Establecimiento</td><td style='text-align:center;'>{marca(req_dict.get('ooms_plan'))}</td></tr>
            <tr><td>Trampas de Grasa con Mantenimiento y Bitácora OOMSAPASLC Semanal</td><td style='text-align:center;'>{marca(req_dict.get('ooms_tramp'))}</td></tr>
            <tr><td>Estudio de Calidad de Agua bajo NOM-002-SEMARNAT-1996</td><td style='text-align:center;'>{marca(req_dict.get('ooms_nom'))}</td></tr>
            <tr><td>Registro de Muestreo Exterior al Límite del Predio (Foto)</td><td style='text-align:center;'>{marca(req_dict.get('ooms_reg'))}</td></tr>

            <tr><th colspan='2'>Imagen Urbana (Licencia de Anuncio y Número Oficial)</th></tr>
            <tr><td>Solicitud de Anuncio, Memoria de Dimensiones, Croquis de Diseño y Fotos Color</td><td style='text-align:center;'>{marca(req_dict.get('img_urbana'))}</td></tr>
            <tr><td>Recibo Oficial de Pago de Número Oficial (Liquidado en Imagen Urbana San José)</td><td style='text-align:center;'>{marca(req_dict.get('img_numof'))}</td></tr>

            <tr><th colspan='2'>Salud (COEPRIS) y Gobernación</th></tr>
            <tr><td>COEPRIS (Salud): Aviso de Funcionamiento Sanitario Sellado</td><td style='text-align:center;'>{marca(req_dict.get('coepris'))}</td></tr>
            <tr><td>Gobernación / Delegación: Anuencia Ciudadana Vecinal y Constancia Delegacional</td><td style='text-align:center;'>{marca(req_dict.get('delegacion'))}</td></tr>
        </table>

        <div class='seccion'>5. OBSERVACIONES Y DICTAMEN DE REVISIÓN</div>
        <div class='bitacora'>{obs_p if obs_p else "Sin observaciones registradas."}</div>

        {foto_html}

        <br><br>
        <table style='border: none; margin-top: 20px;'>
            <tr style='border: none;'>
                <td style='border: none; text-align: center; width: 50%;'>
                    ___________________________________________<br>
                    <b>Firma del Contribuyente o Rep. Legal</b>
                </td>
                <td style='border: none; text-align: center; width: 50%;'>
                    ___________________________________________<br>
                    <b>Roberto Hernández</b><br>
                    Coordinador de Gestiones y Licencias
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    nombre_carpeta_expediente = re.sub(r'[^a-zA-Z0-9]', '_', f"{folio_p}_{cont_p}")
    ruta_carpeta_contribuyente = os.path.join(CARPETA_EXPEDIENTES, nombre_carpeta_expediente)
    if not os.path.exists(ruta_carpeta_contribuyente):
        try: os.makedirs(ruta_carpeta_contribuyente)
        except Exception: pass
    
    try:
        ruta_archivo_expediente = os.path.join(ruta_carpeta_contribuyente, f"Expediente_{folio_p}.html")
        with open(ruta_archivo_expediente, "w", encoding="utf-8") as f_exp:
            f_exp.write(contenido_html)
    except Exception:
        pass

    html_b64 = urllib.parse.quote(contenido_html)
    script_impresion = f"""
    <script>
    function abrirExpedienteImpresion() {{
        var ventana = window.open("", "_blank");
        ventana.document.write(decodeURIComponent("{html_b64}"));
        ventana.document.close();
        ventana.focus();
        setTimeout(function() {{ ventana.print(); }}, 400);
    }}
    </script>
    <button onclick="abrirExpedienteImpresion()" style="background-color:#0b2d54; color:white; padding:10px 18px; border:none; border-radius:4px; font-weight:bold; cursor:pointer; width:100%;">
        🖨️ Mandar a Imprimir Expediente Completo (Cédula Oficial)
    </button>
    """
    return script_impresion

tab1, tab2 = st.tabs(["📋 Panel Central de Gestión", "🗂️ Archivero Histórico"])

# ==========================================================
# PESTAÑA 1: PANEL CENTRAL DE GESTIÓN (REGISTRO ÁGIL)
# ==========================================================
with tab1:
    col_izq, col_der = st.columns([2, 1])
    
    with col_izq:
        c_head1, c_head2 = st.columns([3, 1])
        with c_head1:
            st.markdown("<div class='caja-bloque'><div class='titulo-caja'>1. Ficha del Contribuyente y Trámite Municipal</div></div>", unsafe_allow_html=True)
        with c_head2:
            if st.button("➕ Nuevo Registro", use_container_width=True):
                limpiar_formulario()
                st.rerun()

        fecha_ingreso = st.date_input("Fecha de Registro / Recepción", datetime.date.today(), key="k_fecha")
        
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
                ],
                key="k_tram"
            )
        with c_gir:
            giro = st.selectbox(
                "Giro o Actividad Solicitada",
                ["Minisuper / Abarrote", "Ultramarino / Licorería", "Restaurante Bar", "Restaurante Simultáneo", "Centro Nocturno / Cabaret", "Hotel (Solo Anexos)"],
                key="k_giro"
            )
            
        c_fol, c_nom = st.columns([1, 2])
        with c_fol:
            folio = st.text_input("Folio de Licencia / Expediente:", key="k_folio")
        with c_nom:
            contribuyente = st.text_input("Nombre del Propietario o Razón Social:", key="k_cont")

        c_com1, c_com2 = st.columns([2, 1])
        with c_com1:
            nombre_comercial = st.text_input("Nombre Comercial del Establecimiento (Ej. Minisúper El Aldo):", key="k_nom_com")
        with c_com2:
            tipo_establecimiento = st.selectbox("Característica:", ["Único", "Matriz", "Sucursal"], key="k_tipo_est")

        direccion_escrita = st.text_input("Domicilio del Establecimiento (Calle, Número, Colonia, Localidad):", key="k_dir")
        
        c_mz, c_lt, c_cve = st.columns(3)
        with c_mz:
            manzana_cat = st.text_input("Manzana:", key="k_mz")
        with c_lt:
            lote_cat = st.text_input("Lote:", key="k_lt")
        with c_cve:
            clave_catastral = st.text_input("Clave Catastral:", key="k_cve")
            
        cat_str = f"Mz: {manzana_cat} | Lt: {lote_cat} | Clave: {clave_catastral}"
        
        # --- 2. ENLACE Y UBICACIÓN ---
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>2. Enlace Territorial y Georreferencia</div></div>", unsafe_allow_html=True)
        
        c_link_in, c_link_btn = st.columns([3, 1])
        with c_link_in:
            enlace_mapa = st.text_input("📍 Enlace de Google Maps o Waze:", key="k_link")
        with c_link_btn:
            st.write("")
            st.write("")
            btn_localizar = st.button("📍 Localizar en Mapa", use_container_width=True)
        
        if btn_localizar and enlace_mapa:
            limpio = urllib.parse.unquote(enlace_mapa)
            m1 = re.search(r"@([-\d.]+),([-\d.]+)", limpio)
            m2 = re.search(r"ll=([-\d.]+),([-\d.]+)", limpio)
            m3 = re.search(r"[?&]q=([-\d.]+)[,%](?:2C)?([-\d.]+)", limpio)
            m4 = re.search(r"q=([-\d.]+),([-\d.]+)", limpio)
            m5 = re.search(r"([-\d]{2,3}\.\d+)[,\s]+([-\d]{2,4}\.\d+)", limpio)
            
            lat_res, lon_res = "", ""
            if m1: lat_res, lon_res = m1.group(1), m1.group(2)
            elif m2: lat_res, lon_res = m2.group(1), m2.group(2)
            elif m3: lat_res, lon_res = m3.group(1), m3.group(2)
            elif m4: lat_res, lon_res = m4.group(1), m4.group(2)
            elif m5: lat_res, lon_res = m5.group(1), m5.group(2)

            if lat_res and lon_res:
                st.session_state["k_lat"] = lat_res
                st.session_state["k_lon"] = lon_res
                st.rerun()

        c_tel, c_lat, c_lon = st.columns([2, 1, 1])
        with c_tel:
            telefono = st.text_input("Teléfono de Contacto (Ej. 521624...)", key="k_tel")
        with c_lat:
            latitud = st.text_input("Latitud", key="k_lat")
        with c_lon:
            longitud = st.text_input("Longitud", key="k_lon")
        
        if telefono:
            nombre_destino = contribuyente if contribuyente else "Estimado Contribuyente"
            msg1 = f"Hola {nombre_destino}, mi nombre es Roberto Hernández, seré tu contacto para el seguimiento de tu trámite de licencia; ¿podrías tomarme una llamada? Saludos."
            
            c_com1, c_com2, c_com3 = st.columns([1, 1, 2])
            with c_com1:
                st.markdown(f'<a href="https://wa.me/{telefono}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; border:none; padding:6px; border-radius:4px; width:100%; font-weight:bold; cursor:pointer;">💬 WhatsApp</button></a>', unsafe_allow_html=True)
            with c_com2:
                st.markdown(f'<a href="tel:{telefono}" style="text-decoration:none;"><button style="background-color:#34B7F1; color:white; border:none; padding:6px; border-radius:4px; width:100%; font-weight:bold; cursor:pointer;">📞 Llamar</button></a>', unsafe_allow_html=True)
            with c_com3:
                st.markdown(f'<a href="https://wa.me/{telefono}?text={urllib.parse.quote(msg1)}" target="_blank" style="text-decoration:none;"><button style="background-color:#075E54; color:white; border:none; padding:6px; border-radius:4px; width:100%; font-weight:bold; cursor:pointer;">👋 1. Enviar Saludo Inicial</button></a>', unsafe_allow_html=True)

        if st.button("📂 ABRIR CARPETA DE FORMATOS EN PC", use_container_width=True):
            try: os.startfile(CARPETA_GESTION)
            except Exception: st.error("No se localizó la carpeta GESTION.")

        # --- 3. AUDITORÍA DE REQUISITOS EN BLOQUES DESGLOSADOS ---
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>3. Auditoría de Requisitos Oficiales por Dependencia</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='sub-caja'>🏢 Bloque 1: Base Documental, Personalidad y Giros Comerciales</div>", unsafe_allow_html=True)
        c_sol_giros = st.checkbox("Solicitud Oficial de Giros Comerciales / Restringidos debidamente llenada y firmada", key="chk_sol_giros")
        b1_c1, b1_c2 = st.columns(2)
        with b1_c1:
            c_ine = st.checkbox("Copia de Identificación Oficial del Solicitante o Representante Legal (INE)", key="chk_ine")
            c_acta = st.checkbox("Copia de Acta Constitutiva (Persona Moral) y/o Copia del Poder Notarial", key="chk_acta")
            c_rfc = st.checkbox("Copia de Constancia de Situación Fiscal ante el SAT (RFC Vigente)", key="chk_rfc")
            c_dom = st.checkbox("Comprobante de Domicilio Oficial Vigente", key="chk_dom")
        with b1_c2:
            c_agua = st.checkbox("Copia de Comprobante de Agua Potable Pagado al Corriente (OOMSAPAS)", key="chk_agua")
            c_predial = st.checkbox("Copia de Recibo Oficial de Pago de Impuesto Predial del Ejercicio Vigente", key="chk_predial")
            c_siem = st.checkbox("Copia de Registro Oficial ante Cámara Empresarial (SIEM)", key="chk_siem")
            c_pago_der = st.checkbox("Pago Oficial de Derechos de Licencia o Recepción ante Tesorería Municipal", key="chk_pago_der")

        st.markdown("<div class='sub-caja'>📄 Bloque 2: Acreditación Legal del Inmueble y del Arrendador</div>", unsafe_allow_html=True)
        tipo_propiedad = st.radio(
            "Antecedentes del Inmueble / Título Legal:",
            ["Propio (Título / Escritura)", "Renta (Contrato de Arrendamiento Catastrado)", "Comodato Vigente", "Carta de Préstamo Vigente", "Otro"],
            horizontal=True,
            key="rad_prop"
        )
        propiedad_final = st.text_input("Especifique (si seleccionó 'Otro'):", key="k_prop_otro") if tipo_propiedad == "Otro" else tipo_propiedad
        c_ine_arr = st.checkbox("Copia de Identificación Oficial del Arrendador / Propietario del Inmueble", key="chk_ine_arr")

        st.markdown("<div class='sub-caja'>📐 Bloque 3: Evidencia Gráfica y Planimetría</div>", unsafe_allow_html=True)
        b3_c1, b3_c2 = st.columns(2)
        with b3_c1:
            c_croquis = st.checkbox("Croquis de Localización indicando Manzana, Lote y Clave Catastral", key="chk_croquis")
        with b3_c2:
            c_fotos = st.checkbox("Fotografías del Exterior e Interior (Totalidad del local e instalaciones sanitarias)", key="chk_fotos")

        st.markdown("<div class='sub-caja'>🏛️ Desarrollo Urbano (Licencia de Uso de Suelo)</div>", unsafe_allow_html=True)
        c_suelo_sol = st.checkbox("Solicitud Oficial de Licencia de Uso de Suelo debidamente firmada", key="chk_suelo_sol")
        c_suelo_rpp = st.checkbox("Copia de Escrituras de Propiedad Completas con Sello del Registro Público (RPP)", key="chk_suelo_rpp")
        c_suelo_der = st.checkbox("Dictamen de Uso de Suelo Favorable o Recibo Oficial de Pago de Derechos", key="chk_suelo_der")

        st.markdown("<div class='sub-caja'>🚨 Protección Civil Municipal</div>", unsafe_allow_html=True)
        c_pc_sol = st.checkbox("Solicitud Oficial de Inspección Firmada (Original y 2 copias) y Expediente PDF", key="chk_pc_sol")
        c_pc_pago = st.checkbox("Factura / Recibo Oficial de Pago del Servicio de Inspección Municipal", key="chk_pc_pago")
        c_pc_ext = st.checkbox("Extintores vigentes, Detectores de Humo y Señalética Normativa de Emergencia", key="chk_pc_ext")
        c_pc_inst = st.checkbox("Bitácoras de Mantenimiento de Instalaciones Eléctricas y Gas LP (con Dictamen)", key="chk_pc_inst")

        st.markdown("<div class='sub-caja'>🌿 Ecología y Medio Ambiente (Dictamen Ambiental)</div>", unsafe_allow_html=True)
        c_eco_sol = st.checkbox("Solicitud Oficial de Dictamen Ambiental Firmada y Pago de Derechos Oficial", key="chk_eco_sol")
        c_eco_agua = st.checkbox("Factibilidad / Contrato / Recibo de Agua OOMSAPAS vigente (< 2 meses)", key="chk_eco_agua")
        c_eco_rsu = st.checkbox("Contrato y Factura de Recolección de Residuos Sólidos y de Manejo Especial (< 3 meses)", key="chk_eco_rsu")
        c_eco_fum = st.checkbox("Contrato y Póliza/Certificado Vigente de Fumigación y Plagas (< 3 meses)", key="chk_eco_fum")
        c_eco_pel = st.checkbox("Contrato / Manifiesto de Recolección de Residuos Peligrosos y Grasas", key="chk_eco_pel")
        c_eco_mem = st.checkbox("Memoria Descriptiva del Proceso Operativo y Croquis Interior de Distribución", key="chk_eco_mem")

        st.markdown("<div class='sub-caja'>💧 OOMSAPAS (Descarga de Aguas Residuales y Trampas de Grasa)</div>", unsafe_allow_html=True)
        c_ooms_sol = st.checkbox("Solicitud Oficial de Permiso de Descarga a la Red (PDAR) y Pago de Derechos", key="chk_ooms_sol")
        c_ooms_plan = st.checkbox("Plano / Croquis de Instalaciones de la Red Sanitaria y Pluvial del Local", key="chk_ooms_plan")
        c_ooms_tramp = st.checkbox("Trampas de Grasa Instaladas con Bitácora OOMSAPASLC de Limpieza Semanal", key="chk_ooms_tramp")
        c_ooms_nom = st.checkbox("Estudio de Laboratorio Acreditado de Calidad de Agua (NOM-002-SEMARNAT-1996)", key="chk_ooms_nom")
        c_ooms_reg = st.checkbox("Registro Exterior de Muestreo al Límite del Predio Accesible (Foto)", key="chk_ooms_reg")

        st.markdown("<div class='sub-caja'>🎨 Imagen Urbana (Licencia de Anuncio y Número Oficial)</div>", unsafe_allow_html=True)
        c_img_urbana = st.checkbox("Solicitud de Anuncio, Memoria de Dimensiones, Croquis de Diseño y Fotos Color", key="chk_img_urbana")
        c_img_numof = st.checkbox("Recibo Oficial de Pago de Número Oficial (Liquidado en Imagen Urbana San José)", key="chk_img_numof")

        st.markdown("<div class='sub-caja'>🩺 Salud (COEPRIS) y 📜 Gobernación</div>", unsafe_allow_html=True)
        c_coepris = st.checkbox("Copia del Aviso de Funcionamiento Sanitario Sellado y Cumplimiento Higiénico", key="chk_coepris")
        c_delegacion = st.checkbox("Acta de Anuencia Ciudadana Vecinal y Constancia Delegacional (En caso de aplicar)", key="chk_delegacion")
        
        st.markdown("</div>", unsafe_allow_html=True)

        observaciones = st.text_area("Bitácora de Observaciones y Faltantes:", key="k_obs")
        
        # GUARDAR EN BD EN LA NUBE
        if st.button("💾 REGISTRAR EXPEDIENTE EN BASE DE DATOS", use_container_width=True):
            if not folio or not contribuyente:
                st.warning("⚠️ Debes registrar al menos el Folio y el Contribuyente.")
            else:
                nombre_archivo_foto = ""
                if "foto_cargada" in st.session_state and st.session_state.foto_cargada is not None:
                    try:
                        nombre_limpio = re.sub(r'[^a-zA-Z0-9]', '_', folio) + ".jpg"
                        ruta_destino = os.path.join(CARPETA_FOTOS, nombre_limpio)
                        img_salvada = Image.open(st.session_state.foto_cargada)
                        img_salvada.convert('RGB').save(ruta_destino, "JPEG")
                        nombre_archivo_foto = nombre_limpio
                    except Exception:
                        nombre_archivo_foto = ""

                detalle_compuesto = (
                    f"Fecha: {fecha_ingreso.strftime('%d/%m/%Y')} | Tel: {telefono} | Dir: {direccion_escrita} | NomCom: {nombre_comercial} | "
                    f"TipoEst: {tipo_establecimiento} | Cat: {cat_str} | Propiedad: {propiedad_final} | Lat: {latitud} | Lon: {longitud} | Link: {enlace_mapa} | Foto: {nombre_archivo_foto} | "
                    f"SolGiros:{c_sol_giros} INE:{c_ine} Acta:{c_acta} RFC:{c_rfc} Dom:{c_dom} Agua:{c_agua} Predial:{c_predial} SIEM:{c_siem} PagoDer:{c_pago_der} | "
                    f"INEArr:{c_ine_arr} | "
                    f"Croquis:{c_croquis} Fotos:{c_fotos} | "
                    f"SueloSol:{c_suelo_sol} SueloRPP:{c_suelo_rpp} SueloDer:{c_suelo_der} | "
                    f"PCSol:{c_pc_sol} PCPago:{c_pc_pago} PCExt:{c_pc_ext} PCInst:{c_pc_inst} | "
                    f"EcoSol:{c_eco_sol} EcoAgua:{c_eco_agua} EcoRSU:{c_eco_rsu} EcoFum:{c_eco_fum} EcoPel:{c_eco_pel} EcoMem:{c_eco_mem} | "
                    f"OomsSol:{c_ooms_sol} OomsPlan:{c_ooms_plan} OomsTramp:{c_ooms_tramp} OomsNom:{c_ooms_nom} OomsReg:{c_ooms_reg} | "
                    f"ImgUrb:{c_img_urbana} ImgNumOf:{c_img_numof} COEPRIS:{c_coepris} Delegacion:{c_delegacion}"
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
                    st.success("✅ Expediente almacenado correctamente en la Base de Datos (Nube).")
                except Exception as err:
                    st.error(f"Error al registrar en nube: {err}")

    # --- COLUMNA DERECHA: FOTO Y MAPA ---
    with col_der:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📸 Fachada Principal (Fotografía)</div></div>", unsafe_allow_html=True)
        foto_archivo = st.file_uploader("Cargar Fotografía de la Fachada", type=["jpg", "png", "jpeg"], key="k_up_foto")
        if foto_archivo is not None:
            st.session_state.foto_cargada = foto_archivo
            try:
                img_ver = Image.open(foto_archivo)
                st.image(img_ver, caption="Fotografía Registrada", use_container_width=True)
            except Exception:
                st.error("Archivo de imagen no legible.")
        else:
            st.session_state.foto_cargada = None

        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📍 Visor Satelital de Precisión</div></div>", unsafe_allow_html=True)
        try:
            import folium
            from streamlit_folium import st_folium
            
            c_lat = 22.8905
            c_lon = -109.9167
            zoom_n = 12
            
            if latitud and longitud:
                try:
                    c_lat = float(latitud)
                    c_lon = float(longitud)
                    zoom_n = 16
                except Exception:
                    pass
                    
            mapa_p = folium.Map(location=[c_lat, c_lon], zoom_start=zoom_n, tiles=None)
            
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Esri',
                name='Satélite',
                overlay=False,
                control=True
            ).add_to(mapa_p)
            
            folium.TileLayer(
                tiles='https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
                attr='Labels',
                name='Vialidades',
                overlay=True,
                control=True
            ).add_to(mapa_p)

            nombre_pin = nombre_comercial if nombre_comercial else (contribuyente if contribuyente else "Establecimiento")

            if latitud and longitud:
                try:
                    folium.Marker(
                        [float(latitud), float(longitud)],
                        popup=f"<b>{nombre_pin}</b><br>{giro}<br>Folio: {folio}",
                        tooltip=nombre_pin,
                        icon=folium.Icon(color="red" if "Minisuper" in giro else "blue", icon="info-sign")
                    ).add_to(mapa_p)
                except Exception:
                    pass
                    
            st_folium(mapa_p, width=400, height=380, returned_objects=[], key=f"panel_map_{latitud}_{longitud}")
        except Exception:
            st.info("Visor cartográfico en preparación.")

    # --- SALIDA FÍSICA E IMPRESIÓN DEL PANEL CENTRAL ---
    st.markdown("---")
    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>🖨️ Expediente Documental Oficial</div></div>", unsafe_allow_html=True)
    
    dict_actual = {
        'sol_giros': c_sol_giros, 'ine': c_ine, 'acta_poder': c_acta, 'rfc': c_rfc, 'dom': c_dom, 'agua': c_agua, 'predial': c_predial, 'siem': c_siem, 'pago_der': c_pago_der,
        'prop_legal': bool(propiedad_final), 'ine_arr': c_ine_arr,
        'croquis': c_croquis, 'fotos': c_fotos,
        'suelo_sol': c_suelo_sol, 'suelo_rpp': c_suelo_rpp, 'suelo_der': c_suelo_der,
        'pc_sol': c_pc_sol, 'pc_pago': c_pc_pago, 'pc_ext': c_pc_ext, 'pc_inst': c_pc_inst,
        'eco_sol': c_eco_sol, 'eco_agua': c_eco_agua, 'eco_rsu': c_eco_rsu, 'eco_fum': c_eco_fum, 'eco_pel': c_eco_pel, 'eco_mem': c_eco_mem,
        'ooms_sol': c_ooms_sol, 'ooms_plan': c_ooms_plan, 'ooms_tramp': c_ooms_tramp, 'ooms_nom': c_ooms_nom, 'ooms_reg': c_ooms_reg,
        'img_urbana': c_img_urbana, 'img_numof': c_img_numof, 'coepris': c_coepris, 'delegacion': c_delegacion
    }
    
    ruta_f_actual = ""
    if folio:
        nombre_f_act = re.sub(r'[^a-zA-Z0-9]', '_', folio) + ".jpg"
        p_act = os.path.join(CARPETA_FOTOS, nombre_f_act)
        if os.path.exists(p_act):
            ruta_f_actual = p_act

    html_btn_imprimir_panel = generar_impresion_expediente(
        folio_p=folio if folio else "S/F",
        cont_p=contribuyente if contribuyente else "SIN NOMBRE",
        nom_com_p=nombre_comercial,
        tram_p=tipo_tramite,
        giro_p=giro,
        fecha_p=fecha_ingreso.strftime('%d/%m/%Y'),
        dir_p=direccion_escrita,
        cat_datos_p=cat_str,
        tel_p=telefono,
        lat_p=latitud,
        lon_p=longitud,
        prop_p=propiedad_final,
        req_dict=dict_actual,
        obs_p=observaciones,
        ruta_foto_p=ruta_f_actual
    )
    st.components.v1.html(html_btn_imprimir_panel, height=50)

# ==========================================================
# PESTAÑA 2: ARCHIVERO HISTÓRICO (SEGUIMIENTO Y EDICIÓN EN VIVO)
# ==========================================================
with tab2:
    st.markdown("<h2 style='color: #0b2d54;'>🗂️ Control de Registros Históricos (Nube)</h2>", unsafe_allow_html=True)

    try:
        con = obtener_conexion()
        cur = con.cursor()
        cur.execute("SELECT id, tipo, folio, contribuyente, dato_actualizado, observaciones FROM tramites ORDER BY id DESC")
        registros_todos = cur.fetchall()
        cur.close()
        con.close()

        c_busq1, c_busq2 = st.columns([8, 2])
        with c_busq1:
            texto_busqueda = st.text_input("🔍 Buscar expediente (Nombre Comercial, Contribuyente, Folio o Giro):", key="k_busqueda").strip().lower()
        with c_busq2:
            st.write("")
            st.write("")
            st.caption(f"Total en Archivo: **{len(registros_todos)}**")

        registros = []
        for reg in registros_todos:
            r_id_b, r_tipo_b, r_folio_b, r_cont_b, r_datos_b, r_obs_b = reg
            m_nom_b = re.search(r"NomCom:\s*([^|]+)", r_datos_b or "")
            val_nom_com_b = m_nom_b.group(1).strip() if m_nom_b else ""

            bolsa_busqueda = f"{r_folio_b} {r_cont_b} {val_nom_com_b} {r_tipo_b}".lower()

            if not texto_busqueda or texto_busqueda in bolsa_busqueda:
                registros.append(reg)

        if not registros:
            if texto_busqueda:
                st.warning(f"No se encontraron expedientes que coincidan con: '{texto_busqueda}'")
            else:
                st.info("No hay registros en el archivero histórico.")

        for r in registros:
            r_id, r_tipo, r_folio, r_cont, r_datos, r_obs = r
            r_datos = r_datos or ""

            m_fecha = re.search(r"Fecha:\s*([^|]+)", r_datos)
            m_lat = re.search(r"Lat:\s*([-\d.]+)", r_datos)
            m_lon = re.search(r"Lon:\s*([-\d.]+)", r_datos)
            m_tel = re.search(r"Tel:\s*([^|]+)", r_datos)
            m_dir = re.search(r"Dir:\s*([^|]+)", r_datos)
            m_nom_com = re.search(r"NomCom:\s*([^|]+)", r_datos)
            m_cat = re.search(r"Cat:\s*([^|]+)", r_datos)
            m_prop = re.search(r"Propiedad:\s*([^|]+)", r_datos)
            m_link = re.search(r"Link:\s*([^|]+)", r_datos)
            m_foto = re.search(r"Foto:\s*([^|]+)", r_datos)
            
            val_fecha = m_fecha.group(1).strip() if m_fecha else ""
            val_lat = m_lat.group(1) if m_lat else ""
            val_lon = m_lon.group(1) if m_lon else ""
            val_tel = m_tel.group(1).strip() if m_tel else ""
            val_dir = m_dir.group(1).strip() if m_dir else ""
            val_nom_com = m_nom_com.group(1).strip() if m_nom_com else ""
            val_cat = m_cat.group(1).strip() if m_cat else "Mz: - | Lt: - | Clave: -"
            val_prop = m_prop.group(1).strip() if m_prop else ""
            val_link = m_link.group(1).strip() if m_link else ""
            val_foto = m_foto.group(1).strip() if m_foto else ""

            etiqueta_expander = f"📁 {val_nom_com} — Folio: {r_folio} ({r_tipo})" if val_nom_com else f"📁 Expediente: {r_folio} — {r_cont} ({r_tipo})"

            with st.expander(etiqueta_expander):
                h_col_izq, h_col_der = st.columns([2, 1])

                with h_col_izq:
                    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>1. Ficha del Contribuyente (Edición / Actualización)</div></div>", unsafe_allow_html=True)
                    ch1, ch2 = st.columns(2)
                    h_tipo_actual = ch1.text_input("Trámite / Solicitud", value=str(r_tipo), key=f"ht_{r_id}")
                    h_folio_actual = ch2.text_input("Folio / Licencia", value=str(r_folio), key=f"hf_{r_id}")
                    h_cont_actual = st.text_input("Propietario / Razón Social", value=str(r_cont), key=f"hc_{r_id}")
                    h_nomcom_actual = st.text_input("Nombre Comercial", value=val_nom_com, key=f"hnomcom_{r_id}")
                    h_dir_actual = st.text_input("Domicilio Registrado", value=val_dir, key=f"hdir_{r_id}")
                    h_cat_actual = st.text_input("Datos Catastrales (Mz, Lt, Clave)", value=val_cat, key=f"hcat_{r_id}")

                    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>2. Ubicación y Centro de Comunicación con el Contribuyente</div></div>", unsafe_allow_html=True)
                    ch_t, ch_la, ch_lo = st.columns([2, 1, 1])
                    h_tel_actual = ch_t.text_input("Teléfono", value=val_tel, key=f"htel_{r_id}")
                    h_lat_actual = ch_la.text_input("Latitud", value=val_lat, key=f"hlat_{r_id}")
                    h_lon_actual = ch_lo.text_input("Longitud", value=val_lon, key=f"hlon_{r_id}")
                    h_link_actual = st.text_input("Enlace Cartográfico", value=val_link, key=f"hlnk_{r_id}")

                    if h_tel_actual:
                        nom_wa = h_cont_actual if h_cont_actual else "Contribuyente"
                        msg_req = f"Buen día {nom_wa}, te escribe Roberto Hernández. Te comparto la lista oficial de requisitos para tu expediente de {h_tipo_actual}."
                        msg_rec = f"Buen día {nom_wa}, te contacta Roberto Hernández. Al revisar tu expediente en sistema detectamos documentos pendientes por subsanar. Agradecemos tu valioso apoyo para enviárnoslos a la brevedad."

                        c_wh1, c_wh2, c_wh3, c_wh4 = st.columns(4)
                        with c_wh1:
                            st.markdown(f'<a href="https://wa.me/{h_tel_actual}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:6px; border-radius:4px; width:100%; font-size:12px; font-weight:bold; cursor:pointer;">💬 WhatsApp</button></a>', unsafe_allow_html=True)
                        with c_wh2:
                            st.markdown(f'<a href="tel:{h_tel_actual}"><button style="background-color:#34B7F1; color:white; border:none; padding:6px; border-radius:4px; width:100%; font-size:12px; font-weight:bold; cursor:pointer;">📞 Llamar</button></a>', unsafe_allow_html=True)
                        with c_wh3:
                            st.markdown(f'<a href="https://wa.me/{h_tel_actual}?text={urllib.parse.quote(msg_req)}" target="_blank"><button style="background-color:#128C7E; color:white; border:none; padding:6px; border-radius:4px; width:100%; font-size:12px; font-weight:bold; cursor:pointer;">📋 2. Requisitos</button></a>', unsafe_allow_html=True)
                        with c_wh4:
                            st.markdown(f'<a href="https://wa.me/{h_tel_actual}?text={urllib.parse.quote(msg_rec)}" target="_blank"><button style="background-color:#c0392b; color:white; border:none; padding:6px; border-radius:4px; width:100%; font-size:12px; font-weight:bold; cursor:pointer;">⚠️ 3. Reclamar</button></a>', unsafe_allow_html=True)

                    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>3. Auditoría de Requisitos Oficiales (Palomear Conforme Entreguen)</div>", unsafe_allow_html=True)
                    
                    st.markdown("<div class='sub-caja'>🏢 Bloque 1: Base Documental, Personalidad y Giros Comerciales</div>", unsafe_allow_html=True)
                    u_sol_giros = st.checkbox("Solicitud Oficial de Giros Comerciales / Restringidos", value=("SolGiros:True" in r_datos), key=f"hsol_g_{r_id}")
                    ha1, ha2 = st.columns(2)
                    with ha1:
                        u_ine = st.checkbox("Identificación Oficial del Solicitante / Rep. Legal (INE)", value=("INE:True" in r_datos or "INE (✓)" in r_datos), key=f"hine_{r_id}")
                        u_acta = st.checkbox("Acta Constitutiva y/o Poder Notarial", value=("Acta:True" in r_datos or "Poder:True" in r_datos), key=f"hacta_{r_id}")
                        u_rfc = st.checkbox("Copia del Registro SAT / RFC Vigente", value=("RFC:True" in r_datos or "RFC (✓)" in r_datos), key=f"hrfc_{r_id}")
                        u_dom = st.checkbox("Comprobante de Domicilio Oficial", value=("Dom:True" in r_datos), key=f"hdom_{r_id}")
                    with ha2:
                        u_agua = st.checkbox("Comprobante de Agua Potable Pagado (OOMSAPAS)", value=("Agua:True" in r_datos), key=f"hagua_{r_id}")
                        u_predial = st.checkbox("Recibo de Pago de Impuesto Predial al Corriente", value=("Predial:True" in r_datos or "Predial (✓)" in r_datos), key=f"hpred_{r_id}")
                        u_siem = st.checkbox("Registro ante Cámara Empresarial (SIEM)", value=("SIEM:True" in r_datos or "SIEM (✓)" in r_datos), key=f"hsiem_{r_id}")
                        u_pago_der = st.checkbox("Pago de Derechos / Recepción de Trámite Tesorería", value=("PagoDer:True" in r_datos), key=f"hpagoder_{r_id}")

                    st.markdown("<div class='sub-caja'>📄 Bloque 2: Acreditación Legal del Inmueble y del Arrendador</div>", unsafe_allow_html=True)
                    u_prop = st.text_input("Título / Régimen de Propiedad Registrado", value=val_prop, key=f"hprp_{r_id}")
                    u_ine_arr = st.checkbox("Copia de Identificación Oficial del Arrendador / Propietario", value=("INEArr:True" in r_datos or "INEArrendador:True" in r_datos), key=f"hine_arr_{r_id}")

                    st.markdown("<div class='sub-caja'>📐 Bloque 3: Evidencia Gráfica y Planimetría</div>", unsafe_allow_html=True)
                    hb1, hb2 = st.columns(2)
                    with hb1:
                        u_croquis = st.checkbox("Croquis de Localización (Mz, Lt y Clave Catastral)", value=("Croquis:True" in r_datos or "Croquis (✓)" in r_datos), key=f"hcro_{r_id}")
                    with hb2:
                        u_fotos = st.checkbox("Fotografías del Exterior e Interior (con Sanitarios)", value=("Fotos:True" in r_datos or "Fachada:True" in r_datos or "FotosExt:True" in r_datos), key=f"hfotos_{r_id}")

                    st.markdown("<div class='sub-caja'>🏛️ Desarrollo Urbano (Licencia de Uso de Suelo)</div>", unsafe_allow_html=True)
                    u_suelo_sol = st.checkbox("Solicitud Oficial de Uso de Suelo debidamente firmada", value=("SueloSol:True" in r_datos), key=f"hssol_{r_id}")
                    u_suelo_rpp = st.checkbox("Copia de Escrituras Completas con Sello del Registro Público (RPP)", value=("SueloRPP:True" in r_datos or "SueloAcred:True" in r_datos), key=f"hsrpp_{r_id}")
                    u_suelo_der = st.checkbox("Dictamen de Uso de Suelo Favorable o Recibo de Pago de Derechos", value=("SueloDer:True" in r_datos or "Suelo:True" in r_datos), key=f"hsder_{r_id}")

                    st.markdown("<div class='sub-caja'>🚨 Protección Civil Municipal</div>", unsafe_allow_html=True)
                    u_pc_sol = st.checkbox("Solicitud Oficial de Inspección Firmada (Original y 2 copias) y PDF", value=("PCSol:True" in r_datos), key=f"hpcsol_{r_id}")
                    u_pc_pago = st.checkbox("Recibo Oficial de Pago del Servicio de Inspección Municipal", value=("PCPago:True" in r_datos or "PC:True" in r_datos), key=f"hpcpag_{r_id}")
                    u_pc_ext = st.checkbox("Extintores vigentes, Detectores de Humo y Señalética Normativa", value=("PCExt:True" in r_datos or "PCVoBo:True" in r_datos), key=f"hpcext_{r_id}")
                    u_pc_inst = st.checkbox("Bitácoras de Mantenimiento de Instalaciones Eléctricas y Gas LP", value=("PCInst:True" in r_datos), key=f"hpcins_{r_id}")

                    st.markdown("<div class='sub-caja'>🌿 Ecología y Medio Ambiente (Dictamen Ambiental)</div>", unsafe_allow_html=True)
                    u_eco_sol = st.checkbox("Solicitud Oficial de Dictamen Ambiental Firmada y Pago de Derechos", value=("EcoSol:True" in r_datos or "Eco:True" in r_datos), key=f"hecsol_{r_id}")
                    u_eco_agua = st.checkbox("Factibilidad / Recibo de Agua OOMSAPAS vigente (< 2 meses)", value=("EcoAgua:True" in r_datos), key=f"hecagua_{r_id}")
                    u_eco_rsu = st.checkbox("Contrato y Factura de Recolección de Residuos RSU y Especiales (< 3 meses)", value=("EcoRSU:True" in r_datos or "EcoResiduos:True" in r_datos), key=f"hecrsu_{r_id}")
                    u_eco_fum = st.checkbox("Contrato y Póliza/Certificado Vigente de Fumigación (< 3 meses)", value=("EcoFum:True" in r_datos or "EcoFumig:True" in r_datos), key=f"hecfum_{r_id}")
                    u_eco_pel = st.checkbox("Contrato / Manifiesto de Residuos Peligrosos y Grasas", value=("EcoPel:True" in r_datos), key=f"hecpel_{r_id}")
                    u_eco_mem = st.checkbox("Memoria Descriptiva del Proceso Operativo y Croquis Interior", value=("EcoMem:True" in r_datos), key=f"hecmem_{r_id}")

                    st.markdown("<div class='sub-caja'>💧 OOMSAPAS (Descarga de Aguas Residuales y Trampas de Grasa)</div>", unsafe_allow_html=True)
                    u_ooms_sol = st.checkbox("Solicitud Oficial de Permiso de Descarga a la Red (PDAR) y Pago", value=("OomsSol:True" in r_datos), key=f"homs_s_{r_id}")
                    u_ooms_plan = st.checkbox("Plano / Croquis Hidrosanitario y Pluvial del Establecimiento", value=("OomsPlan:True" in r_datos), key=f"homs_p_{r_id}")
                    u_ooms_tramp = st.checkbox("Trampas de Grasa Instaladas con Bitácora OOMSAPASLC Semanal", value=("OomsTramp:True" in r_datos), key=f"homs_t_{r_id}")
                    u_ooms_nom = st.checkbox("Estudio de Laboratorio Acreditado (NOM-002-SEMARNAT-1996)", value=("OomsNom:True" in r_datos), key=f"homs_n_{r_id}")
                    u_ooms_reg = st.checkbox("Registro Exterior de Muestreo al Límite del Predio Accesible (Foto)", value=("OomsReg:True" in r_datos), key=f"homs_r_{r_id}")

                    st.markdown("<div class='sub-caja'>🎨 Imagen Urbana (Licencia de Anuncio y Número Oficial)</div>", unsafe_allow_html=True)
                    u_img_urb = st.checkbox("Solicitud de Anuncio, Memoria de Dimensiones, Croquis y Fotos Color", value=("ImgUrb:True" in r_datos or "ImgVoBo:True" in r_datos), key=f"himg_{r_id}")
                    u_img_numof = st.checkbox("Recibo Oficial de Pago de Número Oficial (Liquidado en Imagen Urbana)", value=("ImgNumOf:True" in r_datos), key=f"himg_nof_{r_id}")

                    st.markdown("<div class='sub-caja'>🩺 Salud (COEPRIS) y 📜 Gobernación</div>", unsafe_allow_html=True)
                    u_coepris = st.checkbox("Aviso de Funcionamiento Sanitario Sellado y Cumplimiento Higiénico", value=("COEPRIS:True" in r_datos or "COFEPRIS:True" in r_datos), key=f"hcoepris_{r_id}")
                    u_deleg = st.checkbox("Acta de Anuencia Ciudadana Vecinal y Constancia Delegacional", value=("Delegacion:True" in r_datos or "VecActa:True" in r_datos), key=f"hdel_{r_id}")
                    st.markdown("</div>", unsafe_allow_html=True)

                    u_obs = st.text_area("Bitácora de Observaciones y Faltantes:", value=r_obs if r_obs else "", key=f"hobs_{r_id}")

                with h_col_der:
                    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📸 Fachada Registrada</div></div>", unsafe_allow_html=True)
                    
                    archivo_a_mostrar = None
                    if val_foto:
                        r_potencial = os.path.join(CARPETA_FOTOS, val_foto)
                        if os.path.exists(r_potencial):
                            archivo_a_mostrar = r_potencial
                    
                    if not archivo_a_mostrar:
                        nombre_por_folio = re.sub(r'[^a-zA-Z0-9]', '_', str(r_folio)) + ".jpg"
                        r_folio_potencial = os.path.join(CARPETA_FOTOS, nombre_por_folio)
                        if os.path.exists(r_folio_potencial):
                            archivo_a_mostrar = r_folio_potencial

                    if archivo_a_mostrar:
                        try:
                            st.image(archivo_a_mostrar, caption=f"Fachada de {val_nom_com if val_nom_com else r_cont}", use_container_width=True)
                        except Exception:
                            st.info("No se pudo cargar la imagen.")
                    else:
                        st.info("Sin archivo de fachada registrado en disco.")

                    foto_nueva_hist = st.file_uploader("Actualizar Fotografía de Fachada", type=["jpg", "png", "jpeg"], key=f"up_foto_hist_{r_id}")
                    if foto_nueva_hist is not None:
                        try:
                            nombre_f_nueva = re.sub(r'[^a-zA-Z0-9]', '_', str(h_folio_actual)) + ".jpg"
                            ruta_dest_nueva = os.path.join(CARPETA_FOTOS, nombre_f_nueva)
                            img_n = Image.open(foto_nueva_hist)
                            img_n.convert('RGB').save(ruta_dest_nueva, "JPEG")
                            val_foto = nombre_f_nueva
                            archivo_a_mostrar = ruta_dest_nueva
                            st.success("Fotografía actualizada en disco.")
                        except Exception:
                            pass

                    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📍 Visor Satelital Registrado</div></div>", unsafe_allow_html=True)
                    try:
                        import folium
                        from streamlit_folium import st_folium
                        
                        h_lat = float(h_lat_actual) if h_lat_actual else 22.8905
                        h_lon = float(h_lon_actual) if h_lon_actual else -109.9167
                        
                        m_h = folium.Map(location=[h_lat, h_lon], zoom_start=16, tiles=None)
                        folium.TileLayer(
                            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                            attr='Esri',
                            name='Satélite',
                            overlay=False,
                            control=True
                        ).add_to(m_h)
                        
                        folium.TileLayer(
                            tiles='https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
                            attr='Labels',
                            name='Vialidades',
                            overlay=True,
                            control=True
                        ).add_to(m_h)

                        nombre_pin_hist = h_nomcom_actual if h_nomcom_actual else h_cont_actual

                        if h_lat_actual and h_lon_actual:
                            color_pin = "red" if "Minisuper" in str(h_tipo_actual) else "blue"
                            folium.Marker(
                                [h_lat, h_lon],
                                popup=f"<b>{nombre_pin_hist}</b><br>{h_tipo_actual}<br>Folio: {h_folio_actual}",
                                tooltip=nombre_pin_hist,
                                icon=folium.Icon(color=color_pin, icon="info-sign")
                            ).add_to(m_h)

                        st_folium(m_h, width=380, height=350, returned_objects=[], key=f"hist_map_{r_id}")
                    except Exception:
                        st.info("Visor satelital en espera.")

                # BOTÓN PARA GUARDAR AVANCES Y ACTUALIZAR EXPEDIENTE
                st.markdown("---")
                col_save_h, col_imp_h, col_del_h = st.columns([2, 3, 1])
                
                with col_save_h:
                    if st.button("💾 Guardar Avance / Actualizar", key=f"btn_actualizar_{r_id}", use_container_width=True):
                        nuevo_detalle = (
                            f"Fecha: {val_fecha if val_fecha else datetime.date.today().strftime('%d/%m/%Y')} | Tel: {h_tel_actual} | Dir: {h_dir_actual} | NomCom: {h_nomcom_actual} | "
                            f"Cat: {h_cat_actual} | Propiedad: {u_prop} | Lat: {h_lat_actual} | Lon: {h_lon_actual} | Link: {h_link_actual} | Foto: {val_foto} | "
                            f"SolGiros:{u_sol_giros} INE:{u_ine} Acta:{u_acta} RFC:{u_rfc} Dom:{u_dom} Agua:{u_agua} Predial:{u_predial} SIEM:{u_siem} PagoDer:{u_pago_der} | "
                            f"INEArr:{u_ine_arr} | "
                            f"Croquis:{u_croquis} Fotos:{u_fotos} | "
                            f"SueloSol:{u_suelo_sol} SueloRPP:{u_suelo_rpp} SueloDer:{u_suelo_der} | "
                            f"PCSol:{u_pc_sol} PCPago:{u_pc_pago} PCExt:{u_pc_ext} PCInst:{u_pc_inst} | "
                            f"EcoSol:{u_eco_sol} EcoAgua:{u_eco_agua} EcoRSU:{u_eco_rsu} EcoFum:{u_eco_fum} EcoPel:{u_eco_pel} EcoMem:{u_eco_mem} | "
                            f"OomsSol:{u_ooms_sol} OomsPlan:{u_ooms_plan} OomsTramp:{u_ooms_tramp} OomsNom:{u_ooms_nom} OomsReg:{u_ooms_reg} | "
                            f"ImgUrb:{u_img_urb} ImgNumOf:{u_img_numof} COEPRIS:{u_coepris} Delegacion:{u_deleg}"
                        )
                        try:
                            con_up = obtener_conexion()
                            cur_up = con_up.cursor()
                            cur_up.execute(
                                "UPDATE tramites SET tipo = %s, folio = %s, contribuyente = %s, dato_actualizado = %s, observaciones = %s WHERE id = %s",
                                (h_tipo_actual, h_folio_actual, h_cont_actual, nuevo_detalle, u_obs, r_id)
                            )
                            con_up.commit()
                            cur_up.close()
                            con_up.close()
                            st.success("✅ ¡Expediente actualizado exitosamente en la nube!")
                            st.rerun()
                        except Exception as e_up:
                            st.error(f"Error al actualizar: {e_up}")

                with col_imp_h:
                    dict_hist = {
                        'sol_giros': u_sol_giros, 'ine': u_ine, 'acta_poder': u_acta, 'rfc': u_rfc, 'dom': u_dom, 'agua': u_agua, 'predial': u_predial, 'siem': u_siem, 'pago_der': u_pago_der,
                        'prop_legal': bool(u_prop), 'ine_arr': u_ine_arr,
                        'croquis': u_croquis, 'fotos': u_fotos,
                        'suelo_sol': u_suelo_sol, 'suelo_rpp': u_suelo_rpp, 'suelo_der': u_suelo_der,
                        'pc_sol': u_pc_sol, 'pc_pago': u_pc_pago, 'pc_ext': u_pc_ext, 'pc_inst': u_pc_inst,
                        'eco_sol': u_eco_sol, 'eco_agua': u_eco_agua, 'eco_rsu': u_eco_rsu, 'eco_fum': u_eco_fum, 'eco_pel': u_eco_pel, 'eco_mem': u_eco_mem,
                        'ooms_sol': u_ooms_sol, 'ooms_plan': u_ooms_plan, 'ooms_tramp': u_ooms_tramp, 'ooms_nom': u_ooms_nom, 'ooms_reg': u_ooms_reg,
                        'img_urbana': u_img_urb, 'img_numof': u_img_numof, 'coepris': u_coepris, 'delegacion': u_deleg
                    }

                    partes_tipo = str(h_tipo_actual).split(" - ")
                    t_trm = partes_tipo[0] if len(partes_tipo) > 0 else str(h_tipo_actual)
                    t_gir = partes_tipo[1] if len(partes_tipo) > 1 else ""

                    html_btn_imprimir_hist = generar_impresion_expediente(
                        folio_p=str(h_folio_actual),
                        cont_p=str(h_cont_actual),
                        nom_com_p=h_nomcom_actual,
                        tram_p=t_trm,
                        giro_p=t_gir,
                        fecha_p=val_fecha if val_fecha else "REGISTRADA",
                        dir_p=h_dir_actual,
                        cat_datos_p=h_cat_actual,
                        tel_p=h_tel_actual,
                        lat_p=h_lat_actual,
                        lon_p=h_lon_actual,
                        prop_p=u_prop,
                        req_dict=dict_hist,
                        obs_p=str(u_obs),
                        ruta_foto_p=archivo_a_mostrar if archivo_a_mostrar else ""
                    )
                    st.components.v1.html(html_btn_imprimir_hist, height=50)

                with col_del_h:
                    if st.button("🗑️ Eliminar Expediente", key=f"btn_iniciar_del_{r_id}", use_container_width=True):
                        st.session_state[f"mostrar_borrado_{r_id}"] = True

                if st.session_state.get(f"mostrar_borrado_{r_id}", False):
                    st.markdown("<div style='background-color:#ffebe8; border:1px solid #c00; padding:10px; border-radius:5px; margin-top:8px;'>", unsafe_allow_html=True)
                    st.markdown(f"<b>⚠️ Confirmación de Seguridad Requerida para Folio: {h_folio_actual}</b>", unsafe_allow_html=True)
                    clave_baja = st.text_input("Introduce tu Clave Institucional:", type="password", key=f"pwd_baja_{r_id}")
                    
                    b_conf1, b_conf2 = st.columns(2)
                    with b_conf1:
                        if st.button("✔️ Confirmar Baja Permanente", key=f"btn_confirmar_baja_{r_id}", use_container_width=True):
                            if clave_baja == st.session_state.clave_actual:
                                try:
                                    con_del = obtener_conexion()
                                    cur_del = con_del.cursor()
                                    cur_del.execute("DELETE FROM tramites WHERE id = %s", (r_id,))
                                    con_del.commit()
                                    cur_del.close()
                                    con_del.close()
                                    
                                    if archivo_a_mostrar and os.path.exists(archivo_a_mostrar):
                                        try: os.remove(archivo_a_mostrar)
                                        except Exception: pass
                                        
                                    st.session_state[f"mostrar_borrado_{r_id}"] = False
                                    st.success(f"Expediente {h_folio_actual} eliminado correctamente de la base de datos.")
                                    st.rerun()
                                except Exception as err_del:
                                    st.error(f"Error al eliminar de la base de datos: {err_del}")
                            else:
                                st.error("❌ Clave no válida. Operación cancelada.")
                    with b_conf2:
                        if st.button("❌ Cancelar", key=f"btn_cancelar_baja_{r_id}", use_container_width=True):
                            st.session_state[f"mostrar_borrado_{r_id}"] = False
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

    except Exception as ex:
        st.error(f"Error consultando el archivero: {ex}")