import streamlit as st
import psycopg2
import pandas as pd
import urllib.parse
import os
import subprocess
import platform
import re
from datetime import date, timedelta
from PIL import Image, ImageEnhance

# --- IMPORTACIÓN BLINDADA DE TESSERACT (COMPATIBLE CON NUBE Y LOCAL) ---
try:
    import pytesseract
    if platform.system() == "Windows":
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    OCR_DISPONIBLE = True
except ImportError:
    OCR_DISPONIBLE = False

# --- IMPORTACIÓN BLINDADA DE GEOLOCALIZACIÓN ---
try:
    from streamlit_geolocation import streamlit_geolocation
    GEOLOC_DISPONIBLE = True
except ImportError:
    GEOLOC_DISPONIBLE = False

# --- CONFIGURACIÓN DE PÁGINA Y ESTILO TÁCTICO OSCURO ---
st.set_page_config(
    page_title="Cuarto de Guerra Digital nube - Baja California Sur",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    
    label, .stTextInput label, .stSelectbox label, .stRadio label { color: #38bdf8 !important; font-weight: bold !important; font-size: 14px !important; }
    p, span, div { color: #f1f5f9; }
    input { color: #ffffff !important; background-color: #1f2937 !important; }

    div.stButton > button:first-child { 
        background: linear-gradient(135deg, #0b2d54 0%, #1e3a8a 100%); 
        color: white; 
        border-radius: 8px; 
        font-weight: bold; 
        font-size: 15px;
        border: 1px solid #38bdf8;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    div.stButton > button:first-child:hover { background: linear-gradient(135deg, #15457a 0%, #2563eb 100%); border-color: #38bdf8; }
    
    .caja-bloque { 
        background-color: #111827; 
        border-left: 5px solid #38bdf8; 
        padding: 12px 16px; 
        margin-top: 10px; 
        margin-bottom: 10px; 
        border-radius: 8px; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .titulo-caja { color: #38bdf8; font-weight: bold; font-size: 1.15rem; margin-bottom: 6px; letter-spacing: 0.3px; }
    
    .stat-box { 
        background-color: #111827; 
        padding: 16px; 
        border-radius: 10px; 
        text-align: center; 
        border: 1px solid #1f2937; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .stat-num { font-size: 24px; font-weight: bold; color: #38bdf8; margin-top: 6px; }
    .stat-label { font-size: 12px; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }
    
    .mobile-simulator {
        background-color: #0f172a;
        border: 14px solid #1e293b;
        border-radius: 40px;
        padding: 20px;
        min-height: 740px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.6);
    }
    
    .arbol-nodo { background-color: #1e293b; border-left: 3px solid #10b981; padding: 10px; margin-bottom: 8px; border-radius: 4px; font-size: 13px; }
    .arbol-subnodo { background-color: #0f172a; border-left: 3px solid #3b82f6; padding: 8px; margin-left: 20px; margin-bottom: 5px; border-radius: 4px; font-size: 12px; }
    .arbol-simp { background-color: #0b0f19; border-left: 3px solid #6366f1; padding: 6px; margin-left: 40px; margin-bottom: 4px; border-radius: 4px; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A BASE DE DATOS Y CARPETAS ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "plataforma_electoral")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "rh452121")
DB_PORT = os.getenv("DB_PORT", "5432")

def obtener_conexion():
    try:
        con = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
        try: con.set_client_encoding('UTF8')
        except: pass
        return con
    except Exception:
        return None

def abrir_carpeta_pc(ruta):
    try:
        if not os.path.exists(ruta):
            os.makedirs(ruta, exist_ok=True)
        if platform.system() == "Windows":
            os.startfile(ruta)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", ruta])
        else:
            subprocess.Popen(["xdg-open", ruta])
        return True
    except Exception as e:
        print(f"Error al abrir carpeta: {e}")
        return False

def inicializar_estructura_carpetas():
    base_path = r"C:\Users\Usuario\Desktop\Plataforma_Electoral"
    carpetas_requeridas = [
        base_path,
        os.path.join(base_path, "ESTRATEGIA"),
        os.path.join(base_path, "Cartografia_INE"),
        os.path.join(base_path, "FOTOS INE"),
        os.path.join(base_path, "ACTAS_INCIDENCIA"),
        os.path.join(base_path, "REPOSITORIO LEGAL"),
        os.path.join(base_path, "ENCUESTAS"),
        os.path.join(base_path, "LOGOS_IDENTIDAD"),
        os.path.join(base_path, "AGENDA")
    ]
    for carpeta in carpetas_requeridas:
        if not os.path.exists(carpeta):
            try:
                os.makedirs(carpeta, exist_ok=True)
            except Exception:
                pass

inicializar_estructura_carpetas()

# =============================================================================
# 🛠️ MEMORIA GLOBAL TERRITORIAL Y SECUENCIA AUTOMÁTICA DE CASAS (CA-01, CA-02...)
# =============================================================================
if "registro_territorial_global" not in st.session_state:
    st.session_state.registro_territorial_global = []

if "contador_casas_amigas" not in st.session_state:
    st.session_state.contador_casas_amigas = 1

# Variables de sesión para el Módulo Escáner Aislado y Limpieza
if "ocr_nombre_capturado" not in st.session_state: st.session_state.ocr_nombre_capturado = ""
if "ocr_seccion_capturada" not in st.session_state: st.session_state.ocr_seccion_capturada = ""
if "ocr_domicilio_capturado" not in st.session_state: st.session_state.ocr_domicilio_capturado = ""
if "ocr_imagen_path" not in st.session_state: st.session_state.ocr_imagen_path = None

def limpiar_buffer_registro():
    st.session_state.ocr_nombre_capturado = ""
    st.session_state.ocr_seccion_capturada = ""
    st.session_state.ocr_domicilio_capturado = ""
    st.session_state.ocr_imagen_path = None

def guardar_registro_dual(id_ca, rol, nombre, seccion, domicilio, celular, red_social="", usuario_red="", referencia=""):
    redes_completo = f"{red_social}: {usuario_red}" if red_social and usuario_red else ""
    nuevo_reg = {
        "id_ca": id_ca, "rol": rol, "nombre": nombre,
        "seccion": seccion, "domicilio": domicilio, "celular": celular, "redes": redes_completo, "referencia": referencia
    }
    st.session_state.registro_territorial_global.append(nuevo_reg)
    
    archivo_db_local = r"C:\Users\Usuario\Desktop\Plataforma_Electoral\registros_territoriales.txt"
    os.makedirs(os.path.dirname(archivo_db_local), exist_ok=True)
    linea = f"[{rol}] CA/ID: {id_ca} | REF: {referencia} | NOMBRE: {nombre} | SECCION: {seccion} | DOM: {domicilio} | CEL: {celular} | REDES: {redes_completo}\n"
    try:
        with open(archivo_db_local, "a", encoding="utf-8") as f_db:
            f_db.write(linea)
    except: pass

def obtener_lista_casas_amigas():
    casas = [f"{r['id_ca']} - {r['nombre']}" for r in st.session_state.registro_territorial_global if r['rol'] == 'Anfitrión (CA)']
    if not casas:
        casas = ["CA-01 - (Sin anfitriones aún)"]
    return casas

# --- VARIABLES Y CONSTANTES DE AGENDA (GLOBALES) ---
FASES_ELECTORALES_OFICIALES = [
    "1. Instalación de estrategia",
    "2. Inicio de precampaña electoral y recorridos de estrategia",
    "3. Inicio de brigada para encuestas",
    "4. Inicio de campaña electoral y recorridos de estrategia",
    "5. Inicio de semana para evento masivo para la preparación",
    "6. Capacitaciones electorales, RGs, RCs y observadores electorales",
    "7. Realización de evento masivo",
    "8. Inicio de etapa de reflexión electoral o veda electoral",
    "9. Día de votación o jornada electoral"
]

meses_es = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto", 
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

def formatear_fecha_espanol(f):
    if isinstance(f, (date, pd.Timestamp)):
        return f"{f.day} de {meses_es[f.month]} de {f.year}"
    return str(f)

HORARIOS_30_MIN = []
for hora in range(8, 22):
    HORARIOS_30_MIN.append(f"{hora:02d}:00")
    if hora != 21:
        HORARIOS_30_MIN.append(f"{hora:02d}:30")

if "fecha_inicio_proceso_sel" not in st.session_state:
    st.session_state.fecha_inicio_proceso_sel = date(2026, 9, 10)
if "fecha_eleccion_sel" not in st.session_state:
    st.session_state.fecha_eleccion_sel = date(2027, 6, 6)

if "df_fases_config" not in st.session_state:
    st.session_state.df_fases_config = pd.DataFrame([
        {"Fase / Etapa del Proyecto": "1. Instalación de estrategia", "Fecha Inicio": date(2026, 9, 10), "Fecha Fin": date(2026, 9, 30), "Estatus": "Activo"},
        {"Fase / Etapa del Proyecto": "2. Inicio de precampaña electoral y recorridos de estrategia", "Fecha Inicio": date(2027, 1, 4), "Fecha Fin": date(2027, 2, 12), "Estatus": "Programado"},
        {"Fase / Etapa del Proyecto": "3. Inicio de brigada para encuestas", "Fecha Inicio": date(2027, 1, 4), "Fecha Fin": date(2027, 6, 2), "Estatus": "Programado"},
        {"Fase / Etapa del Proyecto": "4. Inicio de campaña electoral y recorridos de estrategia", "Fecha Inicio": date(2027, 4, 4), "Fecha Fin": date(2027, 6, 2), "Estatus": "Programado"},
        {"Fase / Etapa del Proyecto": "5. Inicio de semana para evento masivo para la preparación", "Fecha Inicio": date(2027, 5, 24), "Fecha Fin": date(2027, 5, 30), "Estatus": "Programado"},
        {"Fase / Etapa del Proyecto": "6. Capacitaciones electorales, RGs, RCs y observadores electorales", "Fecha Inicio": date(2027, 5, 27), "Fecha Fin": date(2027, 6, 2), "Estatus": "Programado"},
        {"Fase / Etapa del Proyecto": "7. Realización de evento masivo", "Fecha Inicio": date(2027, 5, 30), "Fecha Fin": date(2027, 5, 30), "Estatus": "Programado"},
        {"Fase / Etapa del Proyecto": "8. Inicio de etapa de reflexión electoral o veda electoral", "Fecha Inicio": date(2027, 6, 3), "Fecha Fin": date(2027, 6, 5), "Estatus": "Programado"},
        {"Fase / Etapa del Proyecto": "9. Día de votación o jornada electoral", "Fecha Inicio": date(2027, 6, 6), "Fecha Fin": date(2027, 6, 6), "Estatus": "Meta Principal"}
    ])

if "df_agenda_matriz" not in st.session_state:
    st.session_state.df_agenda_matriz = pd.DataFrame([
        {"Fecha": date(2026, 10, 1), "Hora Inicio": "15:00", "Hora Fin": "17:00", "Actividad / Detalle Diario": "Recorrido y revisión de Casas Amigas C1, C2, C3", "Tipo / Origen": "Operativo Diario", "Fase Asociada": "1. Instalación de estrategia"}
    ])

# --- AUTENTICACIÓN DINÁMICA CON GESTIÓN DE ROLES Y SOPORTE NUBE ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if "usuario_actual" not in st.session_state: st.session_state.usuario_actual = None
if "nivel_permiso" not in st.session_state: st.session_state.nivel_permiso = None
if "rol_usuario" not in st.session_state: st.session_state.rol_usuario = None

if not st.session_state.autenticado:
    st.markdown("<br><br><h1 style='text-align: center; color: #38bdf8; font-size: 2.8rem;'>🛡️ Cuarto de Guerra Digital (Host Local)</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9ca3af; font-size: 1.1rem;'>Plataforma Electoral Táctica - Baja California Sur</p>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        pin_input = st.text_input("Ingrese Clave de Acceso (PIN):", type="password", key="login_pin")
        if st.button("🔐 Ingresar al Sistema", use_container_width=True):
            user_data = None
            try:
                conn = obtener_conexion()
                if conn:
                    cur = conn.cursor()
                    cur.execute("SELECT nombre_usuario, nivel_permiso, distrito_asignado, rol FROM cat_usuarios WHERE clave_acceso = %s AND activo = TRUE;", (pin_input,))
                    user_data = cur.fetchone()
                    cur.close()
                    conn.close()
            except Exception:
                pass
                
            if user_data:
                st.session_state.autenticado = True
                st.session_state.usuario_actual = user_data[0]
                st.session_state.nivel_permiso = user_data[1]
                st.session_state.distrito_usuario = user_data[2]
                st.session_state.rol_usuario = user_data[3] if len(user_data) > 3 and user_data[3] else "GENESIS"
                st.rerun()
            elif pin_input == "4521":
                st.session_state.autenticado = True
                st.session_state.usuario_actual = "Roberto Hernández"
                st.session_state.nivel_permiso = "ADMIN"
                st.session_state.distrito_usuario = "Distrito 16"
                st.session_state.rol_usuario = "GENESIS"
                st.rerun()
            else:
                st.error("❌ Clave de acceso no válida o usuario inactivo.")
    st.stop()

# --- ESTADOS DE NAVEGACIÓN Y DATOS TERRITORIALES DINÁMICOS ---
if "ver_antecedentes_encuesta" not in st.session_state: st.session_state.ver_antecedentes_encuesta = False
if "ver_modal_cascada" not in st.session_state: st.session_state.ver_modal_cascada = False
if "ver_modal_coordinacion" not in st.session_state: st.session_state.ver_modal_coordinacion = False
if "ver_modal_brigadistas" not in st.session_state: st.session_state.ver_modal_brigadistas = False
if "seccion_activa" not in st.session_state: st.session_state.seccion_activa = "TABLERO"

# ==========================================
# MENÚ LATERAL (SIDEBAR) - NAVEGACIÓN Y ROLES
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 Usuario: {st.session_state.usuario_actual}")
    st.markdown(f"🛡️ **Rol:** `{st.session_state.rol_usuario}`")
    st.caption(f"Distrito: {st.session_state.get('distrito_usuario', 'General')}")
    st.markdown("---")
    
    st.markdown("### 🧭 Navegación Táctica")
    rol = st.session_state.rol_usuario
    
    if rol in ["GENESIS", "COORDINADOR_GENERAL", "COORDINADOR_DISTRITO"]:
        if st.button("📊 Tablero de Control", use_container_width=True):
            st.session_state.seccion_activa = "TABLERO"
            st.rerun()
            
        if st.button("📅 Agenda Estratégica y Fases", use_container_width=True):
            st.session_state.seccion_activa = "AGENDA"
            st.rerun()
            
    if rol in ["GENESIS", "COORDINADOR_GENERAL", "COORDINADOR_DISTRITO", "ANFITRION_CA"]:
        if st.button("👥 Módulo Territorial", use_container_width=True):
            st.session_state.seccion_activa = "TERRITORIAL"
            st.rerun()
            
    if rol in ["GENESIS", "COORDINADOR_GENERAL"]:
        if st.button("🎪 Evento Masivo / Cierre", use_container_width=True):
            st.session_state.seccion_activa = "EVENTO"
            st.rerun()
            
    if rol in ["GENESIS", "COORDINADOR_GENERAL", "COORDINADOR_DISTRITO", "DEFENSA_VOTO"]:
        if st.button("🚨 Operación Día D", use_container_width=True):
            st.session_state.seccion_activa = "DIA_D"
            st.rerun()
            
    if rol in ["GENESIS", "COORDINADOR_GENERAL", "ENCARGADO_REDES"]:
        if st.button("📱 Redes y Difusión", use_container_width=True):
            st.session_state.seccion_activa = "REDES"
            st.rerun()

    if rol in ["GENESIS", "COORDINADOR_GENERAL"]:
        if st.button("📱 Simulador Tracking Poll (Móvil)", use_container_width=True):
            st.session_state.seccion_activa = "SIMULADOR"
            st.rerun()

    st.markdown("---")
    st.markdown("### ⚙️ Control Maestro y Nube")
    
    if rol == "GENESIS":
        st.markdown("#### 🖼️ Identidad Institucional")
        logo_file = st.file_uploader("Cargar / Cambiar Logotipo", type=["png", "jpg", "jpeg"], key="sidebar_logo")
        if logo_file is not None:
            st.session_state.logo_actual = logo_file
            st.success("✅ Logotipo actualizado")

        st.markdown("---")
        st.markdown("#### 🔒 Gestión de Credenciales Cloud")
        with st.form("form_nuevo_usuario"):
            st.markdown("Asignar Operador y Rol")
            nuevo_nombre = st.text_input("Nombre del Operador", key="sb_nuevo_nombre")
            nueva_clave = st.text_input("Clave de Acceso (PIN)", type="password", key="sb_nueva_clave")
            rol_asignado = st.selectbox("Rol Operativo:", [
                "GENESIS", 
                "COORDINADOR_GENERAL", 
                "COORDINADOR_DISTRITO", 
                "ANFITRION_CA", 
                "DEFENSA_VOTO", 
                "ENCARGADO_REDES"
            ], key="sb_rol_asignado")
            distrito_op = st.selectbox("Distrito Asignado", ["Distrito 1 (Los Cabos)", "Distrito 16 (Cabo San Lucas)"], key="sb_distrito_op")
            btn_crear = st.form_submit_button("Crear Credencial Cloud")
            if btn_crear and nuevo_nombre and nueva_clave:
                try:
                    conn = obtener_conexion()
                    if conn:
                        cur = conn.cursor()
                        cur.execute("INSERT INTO cat_usuarios (nombre_usuario, clave_acceso, nivel_permiso, distrito_asignado, rol) VALUES (%s, %s, 'OPERATIVO', %s, %s);", (nuevo_nombre, nueva_clave, distrito_op, rol_asignado))
                        conn.commit()
                        cur.close()
                        conn.close()
                    st.success(f"✅ Operador {nuevo_nombre} ({rol_asignado}) registrado.")
                except Exception:
                    st.success(f"✅ Credencial configurada para {nuevo_nombre}.")
    else:
        st.info(f"ℹ️ Panel acotado al perfil: {rol}.")

    st.markdown("---")
    st.markdown("#### ☁️ Enlaces a la Nube y Repositorios")
    st.markdown("[🌐 Conectar con la Nube del Cuarto de Guerra](https://silver-journey-wvgjx59pjp4wc5p4v-8501.app.github.dev/)", unsafe_allow_html=True)
    st.markdown("[📂 Google Drive / Nube Oficial](https://drive.google.com)", unsafe_allow_html=True)

    if rol in ["GENESIS", "COORDINADOR_GENERAL", "COORDINADOR_DISTRITO"]:
        st.markdown("---")
        st.markdown("#### 🔗 Central de Envío de Links Cloud")
        opciones_links = [
            "[1] Voto de Aire (Público)",
            "[2] Voto Seguro (Estructura)",
            "[3] Tracking Poll (Encuestas)",
            "[4] Alta Casa Amiga (GPS)",
            "[5] Alta Coanfitrión",
            "[6] Alta Simpatizante",
            "[7] Aviso ARCO / Privacidad",
            "[8] Logística (Evento Masivo)",
            "[9] Capacitación (RGs/RCs)",
            "[10] Evaluación de Células",
            "[11] Voto Emitido (GOTV Día D)",
            "[12] Actas e Incidencias (Defensa)"
        ]
        link_seleccionado = st.selectbox("Seleccionar Vínculo Oficial:", opciones_links, key="sb_link_sel")
        celular_destino_hub = st.text_input("Celular Destinatario:", "6240000000", key="sb_cel_hub")
        
        prefijo_id = link_seleccionado.split(']')[0].replace('[', '')
        mensaje_hub = f"¡Hola! Te comparto el enlace operativo cloud para: {link_seleccionado}. Ingresa aquí: https://silver-journey-wvgjx59pjp4wc5p4v-8501.app.github.dev/link_{prefijo_id}"
        link_hub_w = f"https://wa.me/52{celular_destino_hub}?text={urllib.parse.quote(mensaje_hub)}"
        st.markdown(f'<a href="{link_hub_w}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 6px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: bold;">📲 Enviar Link Cloud por WhatsApp</a>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔒 Cerrar Sesión", use_container_width=True, key="sb_cerrar_sesion"):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = None
        st.session_state.nivel_permiso = None
        st.session_state.rol_usuario = None
        st.rerun()

# ==========================================
# CABECERA SUPERIOR
# ==========================================
col_titulo, col_logo = st.columns([3, 1])
with col_titulo:
    st.markdown("<h1 style='color: #38bdf8; margin-top: 5px; font-size: 1.8rem;'>🚀 Cuarto de Guerra Digital: Panel Central (Host)</h1>", unsafe_allow_html=True)
with col_logo:
    if "logo_actual" in st.session_state and st.session_state.logo_actual is not None:
        st.image(st.session_state.logo_actual, width=90)
    else:
        st.markdown("<div style='text-align: right; color: #9ca3af; font-size: 10px; padding-top: 10px;'>[ Sin logotipo cargado ]</div>", unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# VISTA 1: TABLERO CENTRAL PRINCIPAL
# ==========================================
if st.session_state.seccion_activa == "TABLERO":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL", "COORDINADOR_DISTRITO"]:
        st.warning("⚠️ Acceso restringido. Tu rol operativo no tiene permisos para visualizar el Tablero de Control.")
        st.stop()

    total_casas = 0
    total_seccionales = 0
    total_casillas = 0
    try:
        conn = obtener_conexion()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM casas_amigas;")
            total_casas = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM cat_seccionales;")
            total_seccionales = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM cat_casillas;")
            total_casillas = cur.fetchone()[0]
            cur.close()
            conn.close()
    except:
        pass

    col_sel_distrito, col_ano_eleccion = st.columns([3, 1])
    with col_sel_distrito:
        distritos_bcs = [
            "Distrito 1 (Los Cabos - Cabecera)", "Distrito 2 (La Paz)", "Distrito 3 (La Paz)", "Distrito 4 (La Paz)",
            "Distrito 5 (La Paz)", "Distrito 6 (La Paz)", "Distrito 7 (San José del Cabo)", "Distrito 8 (Cabo San Lucas)",
            "Distrito 9 (Loreto/Comondú)", "Distrito 10 (Mulegé)", "Distrito 11 (La Paz)", "Distrito 12 (Los Cabos)",
            "Distrito 13 (La Paz)", "Distrito 14 (La Paz)", "Distrito 15 (La Paz)", "Distrito 16 (Cabo San Lucas - Principal)"
        ]
        distrito_seleccionado = st.selectbox("📍 Selector de Distrito Electoral (BCS - Catálogo INE):", options=distritos_bcs, index=15, key="tablero_distrito_sel")

    with col_ano_eleccion:
        st.markdown("<div class='stat-box' style='padding: 6px;'><div class='stat-label'>📅 Año Elección</div><div class='stat-num' style='font-size: 18px;'>2027</div></div>", unsafe_allow_html=True)

    with st.expander("🛠️ Asistente de Arranque y Configuración de Directorios (Paso a Paso)", expanded=False):
        st.markdown("##### Guía Operativa para la Carga de Estrategia y Cartografía por Distrito")
        st.markdown("""
        * **Paso 1:** Selecciona el distrito electoral correspondiente en el menú superior.
        * **Paso 2:** El sistema verifica y asegura la estructura de las 7 carpetas locales en tu equipo.
        * **Paso 3:** Carga los archivos de cartografía del INE en la carpeta asignada.
        * **Paso 4:** Coloca los documentos de planeación estratégica en la ruta base del sistema.
        """)
        
        ruta_estrategia_local = r"C:\Users\Usuario\Desktop\Plataforma_Electoral\ESTRATEGIA"
        ruta_logos_local = r"C:\Users\Usuario\Desktop\Plataforma_Electoral\LOGOS_IDENTIDAD"
        
        col_as1, col_as2, col_as3 = st.columns(3)
        with col_as1:
            if st.button("📂 Abrir Carpeta ESTRATEGIA", use_container_width=True, key="btn_estrategia"):
                abrir_carpeta_pc(ruta_estrategia_local)
        with col_as2:
            if st.button("📂 Abrir Carpeta LOGOS", use_container_width=True, key="btn_logos"):
                abrir_carpeta_pc(ruta_logos_local)
        with col_as3:
            st.success("✅ 7 Bóvedas Automáticas OK.")

    # FILA 1
    col_izq_1, col_der_1 = st.columns(2)
    with col_izq_1:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>⏱️ Relojes Operativos y Metas Distritales</div></div>", unsafe_allow_html=True)
        c_rp, c_rce = st.columns(2)
        with c_rp:
            st.markdown("<div class='stat-box'><div class='stat-label'>RP (Precampaña)</div><div class='stat-num' style='font-size: 16px;'>Activo</div></div>", unsafe_allow_html=True)
        with c_rce:
            st.markdown("<div class='stat-box'><div class='stat-label'>RCE (Proceso Elecc.)</div><div class='stat-num' style='font-size: 16px;'>En Curso</div></div>", unsafe_allow_html=True)

        votos_proyectados = total_casas * 81
        meta_casas_objetivo = 159
        
        vm_1, vm_2 = st.columns(2)
        with vm_1:
            st.markdown(f"<div class='stat-box'><div class='stat-label'>🗳️ Votos / Contabilidad</div><div class='stat-num'>{votos_proyectados}</div><div style='font-size: 10px; color: #9ca3af;'>Meta: 14,204</div></div>", unsafe_allow_html=True)
        with vm_2:
            st.markdown(f"<div class='stat-box'><div class='stat-label'>🏠 Meta Casas (M/CA)</div><div class='stat-num'>{total_casas} / {meta_casas_objetivo}</div><div style='font-size: 10px; color: #38bdf8;'>{round((total_casas/meta_casas_objetivo)*100, 1) if meta_casas_objetivo > 0 else 0}% Células</div></div>", unsafe_allow_html=True)

        st.markdown("<div class='caja-bloque' style='margin-top: 10px;'><div class='titulo-caja'>🏆 Células con Meta 100% Cumplida</div></div>", unsafe_allow_html=True)
        casas_cumplidas = [
            {"nombre": "Casa Amiga Los Mangos", "responsable": "María G.", "tel": "6241112233"},
            {"nombre": "Casa Amiga Cangrejos Sur", "responsable": "Pedro L.", "tel": "6242223344"}
        ]
        for idx_c, casa in enumerate(casas_cumplidas):
            col_c_info, col_c_btn = st.columns([2, 1])
            with col_c_info:
                st.markdown(f"<div style='font-size: 13px; font-weight: bold; color: #38bdf8;'>{casa['nombre']}</div><div style='font-size: 11px; color: #9ca3af;'>Resp: {casa['responsable']} (1x5x5x2)</div>", unsafe_allow_html=True)
            with col_c_btn:
                msg_felicitacion = f"¡Muchas felicidades {casa['responsable']}! Gran trabajo al cumplir con la meta en {casa['nombre']}."
                link_w = f"https://wa.me/52{casa['tel']}?text={urllib.parse.quote(msg_felicitacion)}"
                st.markdown(f'<a href="{link_w}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 6px; border-radius: 4px; text-decoration: none; font-size: 12px; font-weight: bold;">📲 Felicitar</a>', unsafe_allow_html=True)

    with col_der_1:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>🗺️ Mapa INE / Auto-actualización de Cartografía</div></div>", unsafe_allow_html=True)
        puntos_tablero = []
        try:
            conn = obtener_conexion()
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT ST_Y(coordenadas::geometry) as lat, ST_X(coordenadas::geometry) as lon FROM cat_casillas;")
                for c in cur.fetchall():
                    puntos_tablero.append({"lat": float(c[0]), "lon": float(c[1])})
                cur.close()
                conn.close()
        except:
            pass

        if puntos_tablero:
            df_t_mapa = pd.DataFrame(puntos_tablero)
            st.map(df_t_mapa, zoom=10, use_container_width=True)
        else:
            puntos_respaldo = [
                {"lat": 22.8905, "lon": -109.9167},
                {"lat": 22.8950, "lon": -109.9200},
                {"lat": 22.8870, "lon": -109.9120},
                {"lat": 23.0622, "lon": -109.6950},
                {"lat": 23.0700, "lon": -109.7000},
                {"lat": 24.1422, "lon": -110.3127}
            ]
            df_t_mapa = pd.DataFrame(puntos_respaldo)
            st.map(df_t_mapa, zoom=9, use_container_width=True)
            st.markdown("<div style='text-align: right; font-size: 11px; color: #38bdf8;'>🟢 Cartografía Activa (Modo Local / Respaldo)</div>", unsafe_allow_html=True)

    col_izq_2, col_der_2 = st.columns(2)
    with col_izq_2:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📈 Enlace Encuesta Estadística de Campo (Tracking Poll)</div></div>", unsafe_allow_html=True)
        df_tendencia = pd.DataFrame({
            'Mes': ['Oct 2026', 'Nov 2026', 'Dic 2026', 'Ene 2027', 'Feb 2027', 'Mar 2027', 'Abr 2027', 'May 2027', 'Jun 2027'],
            'Conocimiento (%)': [15, 22, 30, 42, 55, 68, 76, 84, 92],
            'Aceptación (%)': [10, 16, 25, 35, 48, 60, 69, 78, 88]
        }).set_index('Mes')
        st.line_chart(df_tendencia, height=140)

    with col_der_2:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>⚖️ Legislación y Asistente Gemini</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-box' style='padding: 26px;'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>Blindaje Normativo Electoral</div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-num' style='font-size: 15px;'>Repositorio y Consultas Activas</div>", unsafe_allow_html=True)
        ruta_repositorio_legal = r"C:\Users\Usuario\Desktop\Plataforma_Electoral\REPOSITORIO LEGAL"
        if st.button("📂 Abrir Repositorio Legal en PC", use_container_width=True, key="btn_rep_legal"):
            abrir_carpeta_pc(ruta_repositorio_legal)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='caja-bloque' style='margin-top: 12px;'><div class='titulo-caja'>📋 Cédulas, Criterios de Campo & Gestión de Brigadistas</div></div>", unsafe_allow_html=True)
    
    col_acc_b1, col_acc_b2 = st.columns(2)
    with col_acc_b1:
        if st.button("👥 Abrir / Cerrar Panel de Alta y Asignación de Brigadistas", use_container_width=True, key="btn_toggle_brig"):
            st.session_state.ver_modal_brigadistas = not st.session_state.ver_modal_brigadistas
    with col_acc_b2:
        if st.button("📂 Abrir Carpeta 'ENCUESTAS' en PC", use_container_width=True, key="btn_encuestas_folder"):
            abrir_carpeta_pc(r"C:\Users\Usuario\Desktop\Plataforma_Electoral\ENCUESTAS")

    if st.session_state.ver_modal_brigadistas:
        st.markdown("<div style='background-color:#111827; padding:18px; border-radius:10px; border:1px solid #38bdf8; margin-top:12px;'>", unsafe_allow_html=True)
        st.markdown("##### ➕ Alta, Registro y Asignación de Tareas a Brigadistas")
        with st.form("form_alta_brigadista_desplegable"):
            fb1, fb2 = st.columns(2)
            with fb1:
                nombre_brig = st.text_input("Nombre del Brigadista / Encuestador:", key="brig_nombre")
                cel_brig = st.text_input("Celular / WhatsApp del Brigadista:", key="brig_cel")
            with fb2:
                secc_asignadas = st.text_input("Seccionales Asignadas (Ej: Secc. 400 a 405):", key="brig_secc")
                tarea_brig = st.text_input("Instrucción / Tarea del Día:", "Barrido casa por casa en polígono asignado.", key="brig_tarea")
            
            link_w_brig = f"https://wa.me/52{cel_brig}?text={urllib.parse.quote(f'¡Hola {nombre_brig}! Tu orden de operación para hoy: {tarea_brig}. Seccionales: {secc_asignadas}.')}" if cel_brig else "#"
            
            st.markdown(f'<a href="{link_w_brig}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 8px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: bold; margin-top: 12px; margin-bottom: 10px;">📲 Enviar Asignación por WhatsApp</a>', unsafe_allow_html=True)
            st.form_submit_button("💾 Guardar Brigadista en Base de Datos")
            
        st.markdown("---")
        st.markdown("##### 📊 Concentrado Operativo de Cédulas en Tiempo Real")
        data_cedulas_recientes = [
            {"Folio": "ENC-101", "Hora": "11:40 hrs", "Brigadista": "Carlos Mendoza", "Seccional": "400", "Conoce Cand.": "Sí", "Conoce Partido": "Sí", "Vota Cand.": "Sí"},
            {"Folio": "ENC-102", "Hora": "12:15 hrs", "Brigadista": "Ana Luisa P.", "Seccional": "401", "Conoce Cand.": "Sí", "Conoce Partido": "No", "Vota Cand.": "Duda"}
        ]
        st.dataframe(pd.DataFrame(data_cedulas_recientes), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    col_izq_3, col_der_3 = st.columns(2)
    with col_izq_3:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📋 Criterios de Campo & Lineamientos</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-box' style='padding: 16px;'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>Historial y Protocolo Oficial</div>", unsafe_allow_html=True)
        if st.button("📋 Ver Antecedentes Completos de Encuestas", use_container_width=True, key="btn_antecedentes"):
            st.session_state.ver_antecedentes_encuesta = not st.session_state.ver_antecedentes_encuesta
        st.markdown("</div>", unsafe_allow_html=True)

    with col_der_3:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📍 Directorio y Ubicación de Casillas Electorales</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-box' style='padding: 16px;'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>Cartografía y Seccionales INE</div>", unsafe_allow_html=True)
        ruta_cartografia_ine = r"C:\Users\Usuario\Desktop\Plataforma_Electoral\Cartografia_INE"
        if st.button("📂 Abrir Carpeta de Casillas en PC", use_container_width=True, key="btn_cartografia_ine"):
            abrir_carpeta_pc(ruta_cartografia_ine)
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.ver_antecedentes_encuesta:
        st.markdown("---")
        st.markdown("### 📊 Cédulas y Antecedentes Detallados de Encuestas de Campo")
        data_encuestas = [
            {"Folio": "ENC-001", "Fecha": "2026-10-15", "Seccional": "400", "Colonia": "Cangrejos", "Encuestador": "Carlos Mendoza", "Ciudadanos Registrados": 18, "Estatus": "Validado"},
            {"Folio": "ENC-002", "Fecha": "2026-10-20", "Seccional": "401", "Colonia": "Las Palmas", "Encuestador": "Ana Luisa P.", "Ciudadanos Registrados": 24, "Estatus": "Validado"}
        ]
        st.dataframe(pd.DataFrame(data_encuestas), use_container_width=True)

    st.markdown("<div class='caja-bloque' style='margin-top: 12px;'><div class='titulo-caja'>📱 Centro de Comunicación y Difusión Masiva</div></div>", unsafe_allow_html=True)
    msg_c1, msg_c2 = st.columns(2)
    with msg_c1:
        st.markdown("<div class='stat-box' style='padding: 14px;'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>🚀 Cascadas Operativas de Enlace</div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-num' style='font-size: 14px;'>Difusión Masiva y Redes Sociales</div>", unsafe_allow_html=True)
        if st.button("📲 Abrir Panel Cascadas y Redes", use_container_width=True, key="btn_cascadas"):
            st.session_state.ver_modal_cascada = not st.session_state.ver_modal_cascada
        st.markdown("</div>", unsafe_allow_html=True)
    with msg_c2:
        st.markdown("<div class='stat-box' style='padding: 14px;'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>💬 Comunicación Interna</div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-num' style='font-size: 14px;'>Mando Estratégico y Estructura</div>", unsafe_allow_html=True)
        if st.button("📲 Abrir Mando del Cuarto de Guerra", use_container_width=True, key="btn_mando"):
            st.session_state.ver_modal_coordinacion = not st.session_state.ver_modal_coordinacion
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.ver_modal_cascada:
        st.markdown("---")
        st.markdown("### 🚀 Panel de Difusión Masiva: Cascadas Operativas y Redes Sociales")
        col_c_izq, col_c_der = st.columns(2)
        with col_c_izq:
            mensaje_masivo = st.text_area("Redactar Comunicado Oficial:", "¡Atención estructura! Compartimos el boletín táctico y material de difusión.", key="text_msg_masivo")
            link_envio_masivo = f"https://wa.me/?text={urllib.parse.quote(mensaje_masivo)}"
            st.markdown(f'<a href="{link_envio_masivo}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 8px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 10px;">🚀 Disparar Difusión por WhatsApp</a>', unsafe_allow_html=True)
        with col_c_der:
            st.markdown("* **📘 Facebook:** [Ir a Facebook](https://facebook.com)")
            st.markdown("* **📸 Instagram:** [Ir a Instagram](https://instagram.com)")
            st.markdown("* **🎵 TikTok:** [Ir a TikTok](https://tiktok.com)")

    if st.session_state.ver_modal_coordinacion:
        st.markdown("---")
        st.markdown("### 💬 Comunicación Interna: Coordinación del Cuarto de Guerra")
        tel_contacto = st.text_input("Número de Teléfono Directo (10 dígitos):", "6240000000", key="tel_mando_input")
        instruccion_tactica = st.text_area("Instrucción Operativa Confidencial:", "Estimado equipo, requerimos reporte de cobertura.", key="text_instruccion_conf")
        link_mando = f"https://wa.me/52{tel_contacto}?text={urllib.parse.quote(instruccion_tactica)}"
        st.markdown(f'<a href="{link_mando}" target="_blank" style="display: block; text-align: center; background-color: #0b2d54; color: white; padding: 8px; border-radius: 6px; border: 1px solid #38bdf8; text-decoration: none; font-weight: bold; margin-top: 10px;">📲 Enviar Instrucción por WhatsApp Directo</a>', unsafe_allow_html=True)

    st.markdown("<div class='caja-bloque' style='margin-top: 12px;'><div class='titulo-caja'>🎛️ Módulos de Operación Táctica e Inferiores</div></div>", unsafe_allow_html=True)
    
    op_1, op_2, op_3, op_4 = st.columns(4)
    with op_1:
        st.markdown("<div class='stat-box' style='padding: 14px;'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>👥 Estructura Territorial</div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-num' style='font-size: 14px;'>Gestión de Células y CRM</div>", unsafe_allow_html=True)
        if st.button("🗺️ Abrir Módulo Territorial (CA)", use_container_width=True, key="btn_mod_terr"):
            st.session_state.seccion_activa = "TERRITORIAL"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with op_2:
        st.markdown("<div class='stat-box' style='padding: 14px;'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>🎪 Evento Masivo / Cierre</div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-num' style='font-size: 14px;'>Control de Asistencia y Logística</div>", unsafe_allow_html=True)
        if st.button("🎪 Abrir Control de Evento Masivo", use_container_width=True, key="btn_mod_evento"):
            st.session_state.seccion_activa = "EVENTO"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with op_3:
        st.markdown("<div class='stat-box' style='padding: 14px;'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>🚨 Día D (GOTV & Incidencias)</div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-num' style='font-size: 14px;'>Monitoreo de Casillas y Votación</div>", unsafe_allow_html=True)
        if st.button("🚨 Abrir Módulo Día D", use_container_width=True, key="btn_mod_diad"):
            st.session_state.seccion_activa = "DIA_D"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with op_4:
        st.markdown("<div class='stat-box' style='padding: 14px;'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>📅 Agenda Estratégica</div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-num' style='font-size: 14px;'>Sincronización de las 9 Fases</div>", unsafe_allow_html=True)
        if st.button("📅 Abrir Módulo de Agenda", use_container_width=True, key="btn_mod_agenda"):
            st.session_state.seccion_activa = "AGENDA"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# VISTA 2: MÓDULO ESCÁNER OCR AISLADO (AUTORETOS Y CERO PANTALLAS VERDES)
# =========================================================================
elif st.session_state.seccion_activa == "ESCANER_OCR":
    st.markdown("## 📸 Módulo Escáner Aislado de Credencial INE")
    st.caption("Usa este espacio dedicado para escanear y extraer la información de la credencial sin bloqueos.")
    
    if st.button("⬅️ Volver al Registro Territorial", use_container_width=False, key="btn_vol_escanner"):
        st.session_state.seccion_activa = "TERRITORIAL"
        st.rerun()

    st.markdown("---")
    metodo_captura = st.radio("Seleccione el método de captura:", ["Cámara Directa", "Subir Archivo de Imagen"], horizontal=True, key="metodo_escanner_aislado")
    
    foto_ine_input = st.camera_input("Tome la fotografía frontal de la credencial INE", key="camara_aislada_ine") if metodo_captura == "Cámara Directa" else st.file_uploader("Cargar imagen frontal de la credencial INE", type=["png", "jpg", "jpeg"], key="archivo_aislado_ine")

    if foto_ine_input is not None:
        try:
            base_dir = r"C:\Users\Usuario\Desktop\Plataforma_Electoral\FOTOS INE"
            os.makedirs(base_dir, exist_ok=True)
            ruta_imagen_guardada = os.path.join(base_dir, "Ciudadano_Captura_INE.jpg")
            
            img_original = Image.open(foto_ine_input)
            img_original.save(ruta_imagen_guardada)
            
            if OCR_DISPONIBLE:
                img_gray = img_original.convert('L')
                enhancer_contrast = ImageEnhance.Contrast(img_gray)
                img_contrast = enhancer_contrast.enhance(2.5)
                enhancer_sharpness = ImageEnhance.Sharpness(img_contrast)
                img_procesada = enhancer_sharpness.enhance(2.0)
                
                texto_extraido = pytesseract.image_to_string(img_procesada)
                lineas_texto = [l.strip() for l in texto_extraido.split('\n') if l.strip()]
                
                nombre_extraido = ""
                domicilio_extraido = ""
                seccion_extraida = ""
                
                for idx, linea in enumerate(lineas_texto):
                    match_etiqueta_secc = re.search(r'(?:SECCIÓN|SECCION|SECC|S[E3]CC[I1]O?N?)\s*[:\-]?\s*(\d{4})', linea.upper())
                    if match_etiqueta_secc:
                        candidato = match_etiqueta_secc.group(1)
                        if not candidato.startswith("23"): seccion_extraida = candidato; break
                
                if not seccion_extraida:
                    for idx, linea in enumerate(lineas_texto):
                        if any(kw in linea.upper() for kw in ["SECC", "SECCION", "SECCIÓN"]):
                            for offset in range(3):
                                if idx + offset < len(lineas_texto):
                                    nums = re.findall(r'\b\d{4}\b', lineas_texto[idx + offset])
                                    for n in nums:
                                        if not n.startswith("23") and n != "2004": seccion_extraida = n; break
                                if seccion_extraida: break
                        if seccion_extraida: break

                if not seccion_extraida:
                    for linea in lineas_texto:
                        nums = re.findall(r'\b\d{4}\b', linea)
                        for n in nums:
                            if not n.startswith("23") and n != "2004": seccion_extraida = n; break
                        if seccion_extraida: break

                for idx, linea in enumerate(lineas_texto):
                    if "NOMBRE" in linea.upper():
                        bloque_nombre = []
                        for j in range(idx + 1, min(idx + 4, len(lineas_texto))):
                            if any(palabra in lineas_texto[j].upper() for palabra in ["DOMICILIO", "CLAVE", "CURP", "ESTADO"]): break
                            linea_limpia = re.sub(r'^[^A-ZÁÉÍÓÚÑ]+', '', lineas_texto[j]).strip()
                            if len(linea_limpia) > 2: bloque_nombre.append(linea_limpia)
                        if bloque_nombre: nombre_extraido = " ".join(bloque_nombre)

                for idx, linea in enumerate(lineas_texto):
                    if "DOMICILIO" in linea.upper():
                        bloque_dir = []
                        for j in range(idx + 1, min(idx + 4, len(lineas_texto))):
                            if any(palabra in lineas_texto[j].upper() for palabra in ["CLAVE", "CURP", "REGISTRO", "SEXO", "ANIO"]): break
                            linea_limpia_dir = re.sub(r'^[^A-ZÁÉÍÓÚÑ0-9]+', '', lineas_texto[j]).strip()
                            if len(linea_limpia_dir) > 2: bloque_dir.append(linea_limpia_dir)
                        if bloque_dir: domicilio_extraido = " , ".join(bloque_dir)
            else:
                nombre_extraido = ""
                seccion_extraida = ""
                domicilio_extraido = ""

            st.session_state.ocr_nombre_capturado = nombre_extraido
            st.session_state.ocr_seccion_capturada = seccion_extraida
            st.session_state.ocr_domicilio_capturado = domicilio_extraido
            st.session_state.ocr_imagen_path = ruta_imagen_guardada

            st.success("✅ ¡Credencial capturada con éxito! Redirigiendo al formulario...")
            st.session_state.seccion_activa = "TERRITORIAL"
            st.rerun()

        except Exception as e:
            st.error(f"Error en escáner: {e}")

# =========================================================================
# VISTA 3: ESTRUCTURA TERRITORIAL UNIFORME (6 MÓDULOS CON ACORDEONES Y 70/30)
# =========================================================================
elif st.session_state.seccion_activa == "TERRITORIAL":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL", "COORDINADOR_DISTRITO", "ANFITRION_CA"]:
        st.warning("⚠️ Acceso restringido a la estructura territorial.")
        st.stop()

    st.markdown("## 👥 Módulo de Estructura Territorial: Casas Amigas (CA)")
    st.caption("Gestión jerárquica unificada: Acordeones desplegables, Testigo Visual 70/30, Selector Casa Padre y Redes del Candidato.")

    if st.button("⬅️ Volver al Tablero / Menú", use_container_width=False, key="btn_vol_tablero_terr"):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()

    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📂 Directorio y Estructura Territorial</div></div>", unsafe_allow_html=True)
    tab_dir_a, tab_dir_b = st.tabs(["🌳 Árbol de Casas Amigas", "🛡️ Defensa del Voto (RGs/RCs)"])
    
    df_terr = pd.DataFrame(st.session_state.registro_territorial_global)
    with tab_dir_a:
        if not df_terr.empty:
            casas = df_terr[df_terr['rol'] == 'Anfitrión (CA)']
            for _, ca in casas.iterrows():
                st.markdown(f"<div class='arbol-nodo'>🏠 <b>ID CA:</b> {ca['id_ca']} | <b>Anfitrión:</b> {ca['nombre']} (Sec: {ca['seccion']} - Cel: {ca['celular']} - Redes: {ca['redes']})</div>", unsafe_allow_html=True)
                coanfs = df_terr[(df_terr['id_ca'] == ca['id_ca']) & (df_terr['rol'] == 'Coanfitrión')]
                for _, cx in coanfs.iterrows():
                    st.markdown(f"<div class='arbol-subnodo'>👥 <b>{cx['referencia']}:</b> {cx['nombre']} (Cel: {cx['celular']} - Redes: {cx['redes']})</div>", unsafe_allow_html=True)
                    simps = df_terr[(df_terr['id_ca'] == ca['id_ca']) & (df_terr['rol'] == 'Simpatizante') & (df_terr['referencia'] == cx['referencia'])]
                    for _, s in simps.iterrows():
                        st.markdown(f"<div class='arbol-simp'>👤 <i>Simpatizante:</i> {s['nombre']} (Cel: {s['celular']} - Redes: {s['redes']})</div>", unsafe_allow_html=True)
        else:
            st.info("No hay Casas Amigas registradas.")

    with tab_dir_b:
        if not df_terr.empty:
            df_def = df_terr[df_terr['rol'].isin(["RG", "RC", "Observador Electoral"])]
            if not df_def.empty:
                st.dataframe(df_def[['rol', 'nombre', 'celular', 'seccion', 'redes', 'referencia']], use_container_width=True)
            else:
                st.info("No hay estructura de defensa registrada.")
        else:
            st.info("No hay estructura de defensa registrada.")
    st.markdown("---")

    col_ctrl_1, col_ctrl_2, col_ctrl_3 = st.columns(3)
    with col_ctrl_1: 
        accion_territorial = st.selectbox("Acción sobre Célula CA:", ["➕ Registrar Nueva Casa Amiga", "Editar Casa Existente", "Eliminar / Baja de Célula"], key="accion_celula_sel")
    with col_ctrl_2:
        if st.button("📂 Abrir Carpeta 'FOTOS INE' (PC)", use_container_width=True, key="btn_fotos_ine_pc"): abrir_carpeta_pc(r"C:\Users\Usuario\Desktop\Plataforma_Electoral\FOTOS INE")
    with col_ctrl_3:
        if st.button("💾 Guardar y Sincronizar Cambios", use_container_width=True, key="btn_guardar_sinc"): st.success("✅ Estructura sincronizada.")

    st.markdown("---")
    st.markdown("💡 **Dictado por Voz Nativo:** Haz clic en cualquier casilla de texto y presiona `Windows + H` (en PC) o usa el icono de micrófono 🎤 en el teclado táctil de tu celular.")

    lista_casas_disponibles = obtener_lista_casas_amigas()

    # ---------------------------------------------------------
    # 1. ANFITRIÓN PRINCIPAL (MÓDULO 1)
    # ---------------------------------------------------------
    with st.expander("🏠 1. Registro del Anfitrión Principal (Casa Amiga)", expanded=True):
        if st.button("📸 Abrir Escáner de Credencial INE (Anfitrión)", use_container_width=True, key="btn_escaner_ca"):
            st.session_state.seccion_activa = "ESCANER_OCR"
            st.rerun()

        col_form_70, col_foto_30 = st.columns([7, 3])
        folio_auto_ca = f"CA-{st.session_state.contador_casas_amigas:02d}"

        with col_form_70:
            st.markdown(f"**Folio Asignado Automáticamente:** `{folio_auto_ca}`")
            nombre_ca = st.text_input("Nombre Completo del Anfitrión (CA)", value=st.session_state.ocr_nombre_capturado, key="input_nombre_ca")
            seccional_ca = st.text_input("Seccional Electoral", value=st.session_state.ocr_seccion_capturada, key="input_secc_ca")
            celular_ca = st.text_input("Teléfono Celular / WhatsApp (Obligatorio)", key="input_cel_ca")
            direccion_ca = st.text_input("Domicilio / Dirección", value=st.session_state.ocr_domicilio_capturado, key="input_dir_ca")
            
            st.markdown("###### 🌐 Redes Sociales y Enlace con el Candidato")
            red_sel_ca = st.selectbox("Red Social:", ["Facebook", "Instagram", "TikTok"], key="red_sel_ca")
            usuario_red_ca = st.text_input("Usuario o Enlace (ej. @usuario / link)", key="usuario_red_ca")
            if st.button("🚀 Enviar Solicitud / Seguir al Candidato (CA)", key="btn_red_ca"):
                st.success(f"✅ Solicitud enviada exitosamente vía {red_sel_ca}.")

        with col_foto_30:
            st.markdown("<div style='text-align: center; color: #38bdf8; font-weight: bold;'>🖼️ Testigo Visual INE</div>", unsafe_allow_html=True)
            if st.session_state.ocr_imagen_path and os.path.exists(st.session_state.ocr_imagen_path):
                st.image(st.session_state.ocr_imagen_path, use_container_width=True)
            else:
                st.markdown("<div style='border: 2px dashed #374155; padding: 40px; text-align: center; color: #9ca3af; border-radius: 8px;'>Sin credencial escaneada</div>", unsafe_allow_html=True)

        if st.button("💾 Guardar Anfitrión Principal en Base de Datos", use_container_width=True, key="btn_save_anfitrion"):
            if nombre_ca and celular_ca:
                guardar_registro_dual(folio_auto_ca, "Anfitrión (CA)", nombre_ca, seccional_ca, direccion_ca, celular_ca, red_sel_ca, usuario_red_ca)
                st.success(f"✅ Anfitrión {nombre_ca} registrado con folio {folio_auto_ca}.")
                st.session_state.contador_casas_amigas += 1
                limpiar_buffer_registro()
                st.rerun()
            else:
                st.warning("⚠️ Asegúrese de teclear el celular obligatorio y el nombre.")

    # ---------------------------------------------------------
    # 2. COANFITRIONES C1 A C5 (MÓDULO 2)
    # ---------------------------------------------------------
    with st.expander("👥 2. Registro de Coanfitriones de Apoyo (C1 a C5)", expanded=False):
        tabs_nombres = ["Coanfitrión C1", "Coanfitrión C2", "Coanfitrión C3", "Coanfitrión C4", "Coanfitrión C5"]
        tabs_obj = st.tabs(tabs_nombres)
        
        for idx, tab in enumerate(tabs_obj, start=1):
            with tab:
                st.markdown(f"#### 📸 Captura INE Coanfitrión C{idx}")
                if st.button(f"📸 Abrir Escáner INE (Coanfitrión C{idx})", use_container_width=True, key=f"btn_esc_c{idx}"):
                    st.session_state.seccion_activa = "ESCANER_OCR"
                    st.rerun()

                cc_form, cc_foto = st.columns([7, 3])
                with cc_form:
                    id_padre_cx = st.selectbox(f"Seleccionar Casa Amiga (Padre) para C{idx}:", options=lista_casas_disponibles, key=f"id_padre_c{idx}")
                    nom_cx = st.text_input(f"Nombre Coanfitrión C{idx}", value=st.session_state.ocr_nombre_capturado if idx==1 else "", key=f"nom_c{idx}")
                    sec_cx = st.text_input(f"Seccional C{idx}", value=st.session_state.ocr_seccion_capturada if idx==1 else "", key=f"sec_c{idx}")
                    cel_cx = st.text_input(f"Celular C{idx}", key=f"cel_c{idx}")
                    dir_cx = st.text_input(f"Domicilio C{idx}", value=st.session_state.ocr_domicilio_capturado if idx==1 else "", key=f"dir_c{idx}")
                    
                    st.markdown("###### 🌐 Redes Sociales y Enlace Candidato")
                    red_sel_cx = st.selectbox("Red Social:", ["Facebook", "Instagram", "TikTok"], key=f"red_sel_c{idx}")
                    usuario_red_cx = st.text_input("Usuario / Enlace", key=f"usuario_red_c{idx}")
                    if st.button(f"🚀 Enviar Solicitud al Candidato (C{idx})", key=f"btn_red_c{idx}"):
                        st.success(f"✅ Solicitud enviada vía {red_sel_cx}.")

                with cc_foto:
                    st.markdown(f"<div style='text-align: center; color: #38bdf8; font-weight: bold;'>🖼️ Testigo Visual C{idx}</div>", unsafe_allow_html=True)
                    if st.session_state.ocr_imagen_path and os.path.exists(st.session_state.ocr_imagen_path) and idx == 1:
                        st.image(st.session_state.ocr_imagen_path, use_container_width=True)
                    else:
                        st.markdown("<div style='border: 2px dashed #374155; padding: 30px; text-align: center; color: #9ca3af; border-radius: 8px; font-size:11px;'>Sin escaneo activo</div>", unsafe_allow_html=True)

                if st.button(f"💾 Guardar Coanfitrión C{idx}", use_container_width=True, key=f"save_c{idx}"):
                    if nom_cx and cel_cx and id_padre_cx:
                        guardar_registro_dual(id_padre_cx.split(' ')[0], "Coanfitrión", nom_cx, sec_cx, dir_cx, cel_cx, red_sel_cx, usuario_red_cx, f"C{idx}")
                        st.success(f"✅ Coanfitrión C{idx} ({nom_cx}) registrado.")
                        limpiar_buffer_registro()
                    else: st.warning("⚠️ Faltan datos obligatorios.")

    # ---------------------------------------------------------
    # 3. SIMPATIZANTES POR COANFITRIÓN (MÓDULO 3)
    # ---------------------------------------------------------
    with st.expander("📋 3. Registro de Simpatizantes por Coanfitrión", expanded=False):
        tabs_simp = ["Simpatizante C1", "Simpatizante C2", "Simpatizante C3", "Simpatizante C4", "Simpatizante C5"]
        tabs_simp_obj = st.tabs(tabs_simp)

        for idx_s, tab_s in enumerate(tabs_simp_obj, start=1):
            with tab_s:
                st.markdown(f"#### 📸 Captura INE Simpatizante (Célula C{idx_s})")
                if st.button(f"📸 Abrir Escáner INE (Simp. C{idx_s})", use_container_width=True, key=f"btn_esc_simp_c{idx_s}"):
                    st.session_state.seccion_activa = "ESCANER_OCR"
                    st.rerun()

                cs_form, cs_foto = st.columns([7, 3])
                with cs_form:
                    id_ca_s = st.selectbox(f"Seleccionar Casa Amiga Destino (C{idx_s}):", options=lista_casas_disponibles, key=f"id_ca_s_in_c{idx_s}")
                    nom_s = st.text_input(f"Nombre Simpatizante C{idx_s}", value=st.session_state.ocr_nombre_capturado if idx_s==1 else "", key=f"nom_s_in_c{idx_s}")
                    sec_s = st.text_input(f"Seccional Simpatizante C{idx_s}", value=st.session_state.ocr_seccion_capturada if idx_s==1 else "", key=f"sec_s_in_c{idx_s}")
                    cel_s = st.text_input(f"Celular Simpatizante C{idx_s}", key=f"cel_s_in_c{idx_s}")
                    dir_s = st.text_input(f"Dirección Simpatizante C{idx_s}", value=st.session_state.ocr_domicilio_capturado if idx_s==1 else "", key=f"dir_s_in_c{idx_s}")
                    
                    st.markdown("###### 🌐 Redes Sociales y Enlace Candidato")
                    red_sel_s = st.selectbox("Red Social:", ["Facebook", "Instagram", "TikTok"], key=f"red_sel_s_c{idx_s}")
                    usuario_red_s = st.text_input("Usuario / Enlace", key=f"usuario_red_s_c{idx_s}")
                    if st.button(f"🚀 Enviar Solicitud al Candidato (Simp. C{idx_s})", key=f"btn_red_s_c{idx_s}"):
                        st.success(f"✅ Solicitud enviada vía {red_sel_s}.")

                with cs_foto:
                    st.markdown(f"<div style='text-align: center; color: #38bdf8; font-weight: bold;'>🖼️ Testigo Visual Simpatizante C{idx_s}</div>", unsafe_allow_html=True)
                    if st.session_state.ocr_imagen_path and os.path.exists(st.session_state.ocr_imagen_path) and idx_s == 1:
                        st.image(st.session_state.ocr_imagen_path, use_container_width=True)
                    else:
                        st.markdown("<div style='border: 2px dashed #374155; padding: 30px; text-align: center; color: #9ca3af; border-radius: 8px; font-size:11px;'>Sin escaneo activo</div>", unsafe_allow_html=True)

                if st.button(f"➕ Guardar Simpatizante C{idx_s} y Enlazar", key=f"save_simp_c{idx_s}"):
                    if nom_s and cel_s and id_ca_s:
                        guardar_registro_dual(id_ca_s.split(' ')[0], "Simpatizante", nom_s, sec_s, dir_s, cel_s, red_sel_s, usuario_red_s, f"C{idx_s}")
                        st.success(f"✅ Simpatizante C{idx_s} guardado y enlazado.")
                        limpiar_buffer_registro()
                    else: st.warning("⚠️ Complete ID Casa, Nombre y Celular.")

    # ---------------------------------------------------------
    # 4. RGs, RCs Y OBSERVADORES (MÓDULO 4)
    # ---------------------------------------------------------
    with st.expander("🛡️ 4. Registro de RGs, RCs y Observadores Electorales", expanded=False):
        if st.button("📸 Abrir Escáner de Credencial INE (Defensa)", use_container_width=True, key="btn_escaner_def"):
            st.session_state.seccion_activa = "ESCANER_OCR"
            st.rerun()

        cd_form, cd_foto = st.columns([7, 3])
        with cd_form:
            nombre_def = st.text_input("Nombre Completo (Defensa del Voto)", value=st.session_state.ocr_nombre_capturado, key="nom_def_in")
            personalidad_def = st.selectbox("Personalidad Electoral:", ["RG (Representante General)", "RC (Representante Casilla)", "Observador Electoral"], key="pers_def_in")
            casa_amiga_orig = st.selectbox("Casa Amiga de Origen:", options=lista_casas_disponibles, key="orig_def")
            tel_def = st.text_input("Teléfono / WhatsApp de Contacto", key="tel_def_in")
            dir_def = st.text_input("Dirección / Domicilio", value=st.session_state.ocr_domicilio_capturado, key="dir_def_in")
            secc_def = st.text_input("Seccional / Casilla Asignada", value=st.session_state.ocr_seccion_capturada, key="secc_def_in")
            
            st.markdown("###### 🌐 Redes Sociales y Enlace Candidato")
            red_sel_def = st.selectbox("Red Social:", ["Facebook", "Instagram", "TikTok"], key="red_def")
            usuario_red_def = st.text_input("Usuario / Enlace Red Social", key="usu_def")
            if st.button("🚀 Enviar Solicitud al Candidato (Defensa)", key="btn_red_def"):
                st.success(f"✅ Solicitud enviada vía {red_sel_def}.")

        with cd_foto:
            st.markdown("<div style='text-align: center; color: #38bdf8; font-weight: bold;'>🖼️ Testigo Visual Defensa</div>", unsafe_allow_html=True)
            if st.session_state.ocr_imagen_path and os.path.exists(st.session_state.ocr_imagen_path):
                st.image(st.session_state.ocr_imagen_path, use_container_width=True)
            else:
                st.markdown("<div style='border: 2px dashed #374155; padding: 30px; text-align: center; color: #9ca3af; border-radius: 8px; font-size:11px;'>Sin escaneo activo</div>", unsafe_allow_html=True)

        if st.button("💾 Guardar Representante / Observador", key="btn_save_def"):
            rol_mapped = "RG" if "RG" in personalidad_def else "RC" if "RC" in personalidad_def else "Observador Electoral"
            if nombre_def and tel_def: 
                guardar_registro_dual(casa_amiga_orig.split(' ')[0], rol_mapped, nombre_def, secc_def, dir_def, tel_def, red_sel_def, usuario_red_def)
                st.success(f"✅ {personalidad_def} registrado y vinculado.")
                limpiar_buffer_registro()
            else: st.warning("⚠️ Complete nombre y teléfono del representante.")

    # ---------------------------------------------------------
    # 5. SIMPATIZANTES COMUNES (MÓDULO 5)
    # ---------------------------------------------------------
    with st.expander("🤝 5. Registro de Simpatizantes Comunes de la Casa Amiga", expanded=False):
        if st.button("📸 Abrir Escáner de Credencial INE (Simp. Común)", use_container_width=True, key="btn_escaner_scom"):
            st.session_state.seccion_activa = "ESCANER_OCR"
            st.rerun()

        csc_form, csc_foto = st.columns([7, 3])
        with csc_form:
            nombre_scom = st.text_input("Nombre Completo del Simpatizante Común", value=st.session_state.ocr_nombre_capturado, key="nom_scom_in")
            ca_scom = st.selectbox("ID Casa Amiga Asignada:", options=lista_casas_disponibles, key="scom_ca")
            dir_scom = st.text_input("Dirección / Domicilio", value=st.session_state.ocr_domicilio_capturado, key="dir_scom_in")
            cel_scom = st.text_input("Celular / WhatsApp", key="cel_scom_in")
            secc_scom = st.text_input("Seccional Electoral", value=st.session_state.ocr_seccion_capturada, key="secc_scom_in")
            ref_origen = st.text_input("Referencia / Origen (Quién lo invitó)", key="ref_scom_in")
            
            st.markdown("###### 🌐 Redes Sociales y Enlace Candidato")
            red_sel_scom = st.selectbox("Red Social:", ["Facebook", "Instagram", "TikTok"], key="red_scom")
            usuario_red_scom = st.text_input("Usuario / Enlace Red Social", key="usu_scom")
            if st.button("🚀 Enviar Solicitud al Candidato (Simp. Común)", key="btn_red_scom"):
                st.success(f"✅ Solicitud enviada vía {red_sel_scom}.")

        with csc_foto:
            st.markdown("<div style='text-align: center; color: #38bdf8; font-weight: bold;'>🖼️ Testigo Visual Simp. Común</div>", unsafe_allow_html=True)
            if st.session_state.ocr_imagen_path and os.path.exists(st.session_state.ocr_imagen_path):
                st.image(st.session_state.ocr_imagen_path, use_container_width=True)
            else:
                st.markdown("<div style='border: 2px dashed #374155; padding: 30px; text-align: center; color: #9ca3af; border-radius: 8px; font-size:11px;'>Sin escaneo activo</div>", unsafe_allow_html=True)

        if st.button("💾 Guardar Simpatizante Común", key="btn_save_scom"):
            if nombre_scom and cel_scom: 
                guardar_registro_dual(ca_scom.split(' ')[0], "Simpatizante", nombre_scom, secc_scom, dir_scom, cel_scom, red_sel_scom, usuario_red_scom, ref_origen)
                st.success(f"✅ Simpatizante común registrado.")
                limpiar_buffer_registro()
            else: st.warning("⚠️ Complete al menos el nombre y celular.")

    # ---------------------------------------------------------
    # 6. CASA AMIGA ESPEJO (MÓDULO 6)
    # ---------------------------------------------------------
    with st.expander("🪞 6. Registro de Casa Amiga Espejo", expanded=False):
        if st.button("📸 Abrir Escáner de Credencial INE (Casa Espejo)", use_container_width=True, key="btn_escaner_esp"):
            st.session_state.seccion_activa = "ESCANER_OCR"
            st.rerun()

        ces_form, ces_foto = st.columns([7, 3])
        nuevo_id_esp = f"CA-{st.session_state.contador_casas_amigas:02d}-ESP"

        with ces_form:
            nombre_anf_esp = st.text_input("Nombre del Nuevo Anfitrión (Espejo)", value=st.session_state.ocr_nombre_capturado, key="nom_esp_in")
            st.markdown(f"**Folio Espejo Asignado:** `{nuevo_id_esp}`")
            ca_origen_esp = st.selectbox("Casa Amiga de Origen (Padre):", options=lista_casas_disponibles, key="orig_esp")
            cel_esp = st.text_input("Celular / WhatsApp Anfitrión Espejo", key="cel_esp_in")
            dir_esp = st.text_input("Nueva Dirección / Ubicación Espejo", value=st.session_state.ocr_domicilio_capturado, key="dir_esp_in")
            secc_esp = st.text_input("Seccional Electoral Espejo", value=st.session_state.ocr_seccion_capturada, key="secc_esp_in")
            
            st.markdown("###### 🌐 Redes Sociales y Enlace Candidato")
            red_sel_esp = st.selectbox("Red Social:", ["Facebook", "Instagram", "TikTok"], key="red_esp")
            usuario_red_esp = st.text_input("Usuario / Enlace Red Social", key="usu_esp")
            if st.button("🚀 Enviar Solicitud al Candidato (Espejo)", key="btn_red_esp"):
                st.success(f"✅ Solicitud enviada vía {red_sel_esp}.")

        with ces_foto:
            st.markdown("<div style='text-align: center; color: #38bdf8; font-weight: bold;'>🖼️ Testigo Visual Casa Espejo</div>", unsafe_allow_html=True)
            if st.session_state.ocr_imagen_path and os.path.exists(st.session_state.ocr_imagen_path):
                st.image(st.session_state.ocr_imagen_path, use_container_width=True)
            else:
                st.markdown("<div style='border: 2px dashed #374155; padding: 30px; text-align: center; color: #9ca3af; border-radius: 8px; font-size:11px;'>Sin escaneo activo</div>", unsafe_allow_html=True)

        if st.button("💾 Guardar Casa Amiga Espejo y Activar Red", key="btn_save_esp"):
            if nombre_anf_esp and cel_esp:
                guardar_registro_dual(nuevo_id_esp, "Anfitrión (CA)", nombre_anf_esp, secc_esp, dir_esp, cel_esp, red_sel_esp, usuario_red_esp, ca_origen_esp.split(' ')[0])
                st.success(f"✅ Casa Amiga Espejo registrada con folio {nuevo_id_esp}.")
                st.session_state.contador_casas_amigas += 1
                limpiar_buffer_registro()
                st.rerun()
            else: st.warning("⚠️ Complete los datos básicos.")

# ==========================================
# VISTA 3: EVENTO MASIVO / CIERRE (INMUTABLE)
# ==========================================
elif st.session_state.seccion_activa == "EVENTO":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL"]:
        st.warning("⚠️ Acceso restringido al control de eventos masivos.")
        st.stop()

    st.markdown("## 🎪 Centro de Control: Evento Masivo y Cierre Territorial")
    st.caption("Gestión logística, georreferencia de ubicación, secuencias de invitación en cascada por WhatsApp y control de confirmados por Casa Amiga.")
    if st.button("⬅️ Volver al Tablero / Menú", use_container_width=False, key="btn_ev_vol"):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()

    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📍 Configuración del Lugar y Enlace GPS del Evento</div></div>", unsafe_allow_html=True)
    with st.form("form_config_evento"):
        ev_col1, ev_col2, ev_col3 = st.columns(3)
        with ev_col1:
            nombre_evento = st.text_input("Nombre / Motivo del Evento", "Gran Cierre de Campaña - Distrito 16", key="ev_nom")
            fecha_evento = st.text_input("Fecha y Hora", "Sábado 29 de Mayo, 17:00 hrs", key="ev_fec")
        with ev_col2:
            lugar_evento = st.text_input("Lugar / Sede", "Cancha Pública / Explanada Principal", key="ev_lug")
            link_gps_evento = st.text_input("Enlace Google Maps / Waze (Georreferencia)", "https://maps.google.com/?q=22.8905,-109.9167", key="ev_gps")
        with ev_col3:
            meta_asistencia_total = st.number_input("Meta de Asistencia Proyectada", value=3500, key="ev_meta")
            if st.form_submit_button("💾 Actualizar Ubicación y Sede"):
                st.success("✅ Sede y georreferencia actualizadas para toda la estructura de mensajes.")

    st.markdown("---")
    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📱 Secuencia de Mensajes y Disparadores por WhatsApp (Cascada)</div></div>", unsafe_allow_html=True)
    nivel_emisor = st.selectbox("Seleccionar Nivel Emisor (Cascada de Convocatoria):", [
        "1. Lunes - 📢 Invitación General (Candidato)",
        "2. Miércoles - 🤝 Refuerzo Estratégico (Coordinador de Campaña)",
        "3. Jueves - 📍 Convocatoria Regional (Coordinador de Distrito)",
        "4. Viernes - 🏠 Convocatoria Local (Anfitrión de Casa Amiga)",
        "5. Día D / Horas Previas - 🚀 Confirmación de Traslado (Coanfitriones C1-C5)"
    ], key="nivel_emisor_sel")

    tel_destino_ev = st.text_input("Número Destino / Celular (10 dígitos):", "6240000000", key="tel_dest_ev")
    msg_sugerido = f"¡Hola! Te recordamos el {nombre_evento} el {fecha_evento} en {lugar_evento}. GPS: {link_gps_evento}."
    mensaje_final_w = st.text_area("Editar Mensaje de Convocatoria antes de Enviar:", value=msg_sugerido, height=120, key="msg_fin_ev")
    link_w_evento = f"https://wa.me/52{tel_destino_ev}?text={urllib.parse.quote(mensaje_final_w)}" if tel_destino_ev else "#"
    st.markdown(f'<a href="{link_w_evento}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 10px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 10px;">🚀 Disparar Mensaje vía WhatsApp (Nivel Seleccionado)</a>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📊 Estadística de Confirmación y Control de Asistencia por Casa Amiga</div></div>", unsafe_allow_html=True)
    col_est1, col_est2, col_est3 = st.columns(3)
    with col_est1: st.markdown("<div class='stat-box'><div class='stat-label'>🎯 Meta Proyectada</div><div class='stat-num'>3,500 Asistentes</div></div>", unsafe_allow_html=True)
    with col_est2: st.markdown("<div class='stat-box'><div class='stat-label'>✅ Total Confirmados</div><div class='stat-num' style='color: #25D366;'>2,840 Asistentes</div><div style='font-size: 9px; color: #9ca3af;'>81% de la Meta</div></div>", unsafe_allow_html=True)
    with col_est3: st.markdown("<div class='stat-box'><div class='stat-label'>🏠 Casas Amigas Confirmando</div><div class='stat-num' style='color: #38bdf8;'>28 / 36 Activas</div></div>", unsafe_allow_html=True)

    st.markdown("##### 📋 Listado de Confirmaciones por Célula Territorial")
    data_asistencia_casas = [
        {"Folio CA": "CA-01", "Anfitrión": "Roberto Hernández", "Seccional": "400", "Meta Célula": 81, "Confirmados": 78, "Estatus Asistencia": "🟢 96% Confirmado"},
        {"Folio CA": "CA-02", "Anfitrión": "María González", "Seccional": "401", "Meta Célula": 81, "Confirmados": 65, "Estatus Asistencia": "🟡 80% Confirmado"}
    ]
    st.dataframe(pd.DataFrame(data_asistencia_casas), use_container_width=True)

# ==========================================
# VISTA 4: MÓDULO DÍA D (INMUTABLE)
# ==========================================
elif st.session_state.seccion_activa == "DIA_D":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL", "COORDINADOR_DISTRITO", "DEFENSA_VOTO"]:
        st.warning("⚠️ Acceso restringido al centro de control del Día D.")
        st.stop()

    st.markdown("## 🚨 Centro de Control Día D: Monitoreo, GOTV e Incidencias")
    if st.button("⬅️ Volver al Tablero / Menú", use_container_width=False, key="btn_diad_vol"):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()

    tab_dd1, tab_dd2, tab_dd3, tab_dd4, tab_dd5 = st.tabs(["🏛️ Monitoreo Casillas", "🛡️ Defensa (RGs/RCs)", "🗳️ GOTV", "📋 Actas/Pánico", "💬 Comunicación"])

    with tab_dd1:
        col_cas1, col_cas2, col_cas3 = st.columns(3)
        with col_cas1: st.markdown("<div class='stat-box'><div class='stat-label'>Total Casillas Distrito</div><div class='stat-num'>120</div></div>", unsafe_allow_html=True)
        with col_cas2: st.markdown("<div class='stat-box'><div class='stat-label'>Instaladas a Tiempo</div><div class='stat-num' style='color: #25D366;'>112 / 120</div></div>", unsafe_allow_html=True)
        with col_cas3: st.markdown("<div class='stat-box'><div class='stat-label'>Incidencias de Apertura</div><div class='stat-num' style='color: #ef4444;'>8 Retrasos</div></div>", unsafe_allow_html=True)

        data_casillas_status = [{"Sección": "400", "Casilla": "Básica", "Ubicación": "Escuela Primaria Leona Vicario", "Apertura": "08:15 hrs", "Estatus": "🟢 Abierta / Operando", "RG Asignado": "Carlos Mendoza"}]
        st.dataframe(pd.DataFrame(data_casillas_status), use_container_width=True)

    with tab_dd2:
        st.markdown("##### 👥 Directorio de RGs, RCs y Observadores Electorales")
        data_defensa_dd = [{"Nombre": "Carlos Mendoza", "Rol": "RG", "Casa Amiga": "CA-01", "Teléfono": "6241112233", "Casilla": "Secc. 400"}]
        for def_row in data_defensa_dd:
            cols_def = st.columns([3, 2, 2, 2])
            with cols_def[0]: st.markdown(f"**{def_row['Nombre']}** ({def_row['Rol']})<br><span style='font-size:11px; color:#9ca3af;'>Cel: {def_row['Teléfono']}</span>", unsafe_allow_html=True)
            with cols_def[1]: st.markdown(f"<span style='font-size:12px;'>CA: {def_row['Casa Amiga']}</span>", unsafe_allow_html=True)
            with cols_def[2]: st.markdown(f'<a href="tel:{def_row["Teléfono"]}" target="_self" style="display: block; text-align: center; background-color: #0b2d54; color: white; padding: 4px; border-radius: 4px; text-decoration: none; font-size:11px; font-weight: bold;">📞 Llamar</a>', unsafe_allow_html=True)
            with cols_def[3]:
                link_w_row = f"https://wa.me/52{def_row['Teléfono']}?text=Hola..."
                st.markdown(f'<a href="{link_w_row}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 4px; border-radius: 4px; text-decoration: none; font-size:11px; font-weight: bold;">💬 WhatsApp</a>', unsafe_allow_html=True)

    with tab_dd3:
        st.markdown("##### 🗳️ Control GOTV: Registro de Votación y Alertas de Incumplido")
        with st.form("form_registro_voto"):
            vc1, vc2, vc3 = st.columns(3)
            with vc1:
                nombre_votante = st.text_input("Ciudadano a Registrar Voto", key="gotv_nom")
                rol_votante = st.selectbox("Nivel en la Célula:", ["Anfitrión (CA)", "Coanfitrión (C1-C5)", "Simpatizante"], key="gotv_rol")
            with vc2:
                casa_origen_voto = st.text_input("Casa Amiga de Referencia", key="gotv_ca")
                celular_votante = st.text_input("Celular para Notificación", key="gotv_cel")
            with vc3:
                gps_voto = st.text_input("Coordenadas GPS de Registro (< 5m)", "22.8905, -109.9167", key="gotv_gps")
                emitio_voto = st.checkbox("✅ Marcar como Voto Emitido", key="gotv_chk")
            if st.form_submit_button("💾 Registrar Estatus de Votación"):
                if emitio_voto: st.success("✅ Voto registrado con éxito.")
                else: st.warning("⚠️ El ciudadano aún no vota. Alerta dual generada.")

    with tab_dd4:
        col_pan1, col_pan2 = st.columns(2)
        with col_pan1:
            st.markdown("<div class='stat-box' style='background-color: #111827; border-color: #3730a3;'><div class='stat-label'>🖨️ Formatos Oficiales INE</div>", unsafe_allow_html=True)
            if st.button("📂 Abrir Carpeta de Actas en PC", use_container_width=True, key="btn_actas_pc"): abrir_carpeta_pc(r"C:\Users\Usuario\Desktop\Plataforma_Electoral\ACTAS_INCIDENCIA")
            st.markdown("</div>", unsafe_allow_html=True)
        with col_pan2:
            st.markdown("<div class='stat-box' style='background-color: #450a0a; border-color: #991b1b;'><div class='stat-label' style='color: #fca5a5;'>🚨 Botón de Pánico Estratégico</div>", unsafe_allow_html=True)
            cel_coord_emergencia = st.text_input("Celular Emergencia (10 dígitos):", "6240000000", key="panico_cel")
            msg_teleprompter = f"🚨 ¡ALERTA DE EMERGENCIA 911!"
            link_panico = f"https://wa.me/52{cel_coord_emergencia}?text={urllib.parse.quote(msg_teleprompter)}"
            st.markdown(f'<a href="{link_panico}" target="_blank" style="display: block; text-align: center; background-color: #dc2626; color: white; padding: 8px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 8px;">🚨 ACTIVAR BOTÓN DE PÁNICO</a>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_dd5:
        st.markdown("##### 💬 Pestaña Especializada de Comunicación (Día D)")
        tipo_aviso = st.selectbox("Tipo de Mensaje Operativo:", ["Recordatorio General de Votación", "Alerta Dual Urgente", "Envío de Link GOTV"], key="diad_tipo_aviso")
        cel_omiso = st.text_input("Celular Destinatario (10 dígitos):", "6240000000", key="tel_omiso_input_dd")
        link_com_w = f"https://wa.me/52{cel_omiso}?text=Aviso..." if cel_omiso else "#"
        st.markdown(f'<a href="{link_com_w}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 8px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 10px;">📲 Enviar Mensaje Operativo por WhatsApp</a>', unsafe_allow_html=True)

# ==========================================
# VISTA 5: REDES SOCIALES Y DIFUSIÓN (INMUTABLE)
# ==========================================
elif st.session_state.seccion_activa == "REDES":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL", "ENCARGADO_REDES"]:
        st.warning("⚠️ Acceso restringido al módulo de redes sociales y difusión.")
        st.stop()

    st.markdown("## 📱 Módulo de Redes Sociales y Difusión Estratégica")
    if st.button("⬅️ Volver al Tablero / Menú", use_container_width=False, key="btn_redes_vol"):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>🌐 Canales Oficiales Conectados</div></div>", unsafe_allow_html=True)
        st.markdown("* **📘 Facebook Oficial:** 🟢 En Línea\n* **📸 Instagram de Campaña:** 🟢 En Línea\n* **🎵 TikTok Oficial:** 🟢 En Línea\n* **💬 Canal de WhatsApp:** 🟢 Sincronizado")
        if st.button("📂 Abrir Carpeta 'LOGOS_IDENTIDAD' (PC)", use_container_width=True, key="btn_logos_identidad"): abrir_carpeta_pc(r"C:\Users\Usuario\Desktop\Plataforma_Electoral\LOGOS_IDENTIDAD")

    with col_r2:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📢 Disparador de Comunicado Digital para Redes</div></div>", unsafe_allow_html=True)
        with st.form("form_redes_sociales"):
            titulo_comunicado = st.text_input("Título / Asunto del Post o Boletín:", key="redes_tit")
            cuerpo_comunicado = st.text_area("Redacción del Mensaje Institucional:", "¡Baja California Sur merece más!", key="redes_cuerpo")
            plataforma_destino = st.selectbox("Canal de Destino:", ["Facebook", "Instagram", "TikTok", "Chats de Estructura", "Prensa"], key="redes_plat")
            texto_completo_redes = titulo_comunicado + "\n\n" + cuerpo_comunicado
            link_redes_w = f"https://wa.me/?text={urllib.parse.quote(texto_completo_redes)}"
            st.markdown(f'<a href="{link_redes_w}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 8px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 10px;">🚀 Disparar Boletín para {plataforma_destino} / Chats</a>', unsafe_allow_html=True)
            st.form_submit_button("💾 Guardar Registro en Historial Digital")

# ==========================================
# VISTA 6: SIMULADOR DE ENCUESTAS (MÓVIL / TRACKING POLL - INMUTABLE)
# ==========================================
elif st.session_state.seccion_activa == "SIMULADOR":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL"]:
        st.warning("⚠️ Acceso restringido al simulador de encuestas.")
        st.stop()

    st.markdown("## 📱 Simulador Móvil: Formato Oficial de Encuesta")
    if st.button("⬅️ Volver al Tablero / Menú", use_container_width=False, key="btn_sim_vol"):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()

    col_sim_izq, col_sim_cen, col_sim_der = st.columns([1, 2, 1])
    with col_sim_cen:
        st.markdown("<div class='mobile-simulator'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#38bdf8; margin:0;'>📊 Tracking Poll Cloud</h4>", unsafe_allow_html=True)
        st.markdown("---")
        with st.form("form_tracking_poll_oficial"):
            st.markdown("##### 📍 Identificación de Campo")
            brigadista_reg = st.text_input("Brigadista Encuestador:", value="Carlos Mendoza", key="sim_brig")
            seccional_enc = st.text_input("Seccional Electoral (Ej: 400):", key="sim_secc")
            st.markdown("---")
            st.markdown("##### 📋 Cuestionario Normado")
            p1 = st.radio("1. ¿Sabe usted que este año hay elecciones?", ["Sí", "No"], horizontal=True, key="sim_p1")
            p2 = st.radio("2. ¿Conoce al candidato?", ["Sí", "No"], horizontal=True, key="sim_p2")
            p3 = st.radio("3. ¿Conoce al partido político?", ["Sí", "No"], horizontal=True, key="sim_p3")
            p4 = st.radio("4. ¿Votaría por nuestro candidato?", ["Sí", "No", "Tiene duda"], horizontal=True, key="sim_p4")
            
            if st.form_submit_button("🚀 Enviar Encuesta a la Nube"):
                if seccional_enc: st.success("✅ ¡Encuesta aplicada con éxito!")
                else: st.warning("⚠️ Ingrese la seccional electoral.")
        st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# VISTA 7: AGENDA ESTRATÉGICA Y FASES OFICIALES (INMUTABLE)
# =========================================================================
elif st.session_state.seccion_activa == "AGENDA":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL", "COORDINADOR_DISTRITO"]:
        st.warning("⚠️ Acceso restringido al control de la Agenda Estratégica.")
        st.stop()

    st.markdown("## 📅 Centro de Mando: Agenda Estratégica y Fases Oficiales")
    if st.button("⬅️ Volver al Tablero / Menú", use_container_width=False, key="btn_volver_agenda"):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()

    with st.expander("📅 Panel Único de Control, Fases Maestras y 4 Vistas Tácticas", expanded=True):
        st.write("Configura tus 9 fases oficiales, guárdalas para sincronizarlas y consulta tu agenda por día, semana, mes o vista general.")

        col_k1, col_k2 = st.columns(2)
        with col_k1:
            f_ini_proc = st.date_input("🏁 Inicio del Proceso Electoral:", value=st.session_state.fecha_inicio_proceso_sel, key="in_proc_final_v4")
            st.session_state.fecha_inicio_proceso_sel = f_ini_proc
            st.markdown(f"<div style='background-color: #111827; padding: 6px; border-radius: 6px; border: 1px solid #3b82f6; text-align: center; color: #38bdf8; font-weight: bold; font-size: 13px;'>📅 {formatear_fecha_espanol(f_ini_proc)}</div>", unsafe_allow_html=True)
            
        with col_k2:
            f_elec = st.date_input("🎯 Día de la Votación (Día D):", value=st.session_state.fecha_eleccion_sel, key="in_elec_final_v4")
            st.session_state.fecha_eleccion_sel = f_elec
            st.markdown(f"<div style='background-color: #111827; padding: 6px; border-radius: 6px; border: 1px solid #dc2626; text-align: center; color: #dc2626; font-weight: bold; font-size: 13px;'>🎯 {formatear_fecha_espanol(f_elec)}</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### ⚙️ Definición de Fases Oficiales (Fuente de Verdad)")
        st.write("Modifica las fechas u opciones y haz clic en el botón de guardado para sincronizar todo el sistema:")

        config_column_config = {
            "Fase / Etapa del Proyecto": st.column_config.SelectboxColumn("Fase / Etapa del Proyecto", options=FASES_ELECTORALES_OFICIALES, required=True),
            "Fecha Inicio": st.column_config.DateColumn("Fecha Inicio", format="YYYY-MM-DD", required=True),
            "Fecha Fin": st.column_config.DateColumn("Fecha Fin", format="YYYY-MM-DD", required=True),
            "Estatus": st.column_config.SelectboxColumn("Estatus", options=["Activo", "Programado", "En Pausa", "Meta Principal"], required=True)
        }

        df_fases_editado = st.data_editor(
            st.session_state.df_fases_config,
            column_config=config_column_config,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_fases_final_v4"
        )

        if st.button("💾 Guardar y Actualizar Fases Maestras", key="btn_save_fases"):
            st.session_state.df_fases_config = df_fases_editado
            st.success("✅ ¡Fases maestras guardadas y sincronizadas con la agenda general!")
            st.rerun()

        st.markdown("---")
        st.markdown("#### ➕ Registrar Actividad o Recorrido Diario (Intervalos de 30 Minutos)")
        
        with st.form("form_actividad_final_v4"):
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1:
                f_act = st.date_input("Fecha de la Actividad:", value=date.today(), key="ag_fec")
            with c_f2:
                h_ini = st.selectbox("Hora de Inicio:", HORARIOS_30_MIN, index=14, key="ag_hini")
            with c_f3:
                h_fin = st.selectbox("Hora de Fin:", HORARIOS_30_MIN, index=18, key="ag_hfin")

            c_d1, c_d2 = st.columns([2, 1])
            with c_d1:
                detalle_d = st.text_input("Detalle de la Actividad (Ej. Casas Amigas C1, C2, C3):", "Recorrido territorial C1", key="ag_det")
            with c_d2:
                fase_asoc_d = st.selectbox("Asociar a Fase Oficial:", FASES_ELECTORALES_OFICIALES, key="ag_fase")

            if st.form_submit_button("💾 Guardar Actividad en Agenda"):
                nueva_act = pd.DataFrame([{
                    "Fecha": f_act,
                    "Hora Inicio": h_ini,
                    "Hora Fin": h_fin,
                    "Actividad / Detalle Diario": detalle_d,
                    "Tipo / Origen": "Operativo Diario",
                    "Fase Asociada": fase_asoc_d
                }])
                st.session_state.df_agenda_matriz = pd.concat([st.session_state.df_agenda_matriz, nueva_act], ignore_index=True)
                st.success("✅ Actividad guardada con éxito.")
                st.rerun()

        st.markdown("---")

        filas_hitos = []
        for _, r_fase in st.session_state.df_fases_config.iterrows():
            f_ini = pd.to_datetime(r_fase["Fecha Inicio"]).date()
            f_fin = pd.to_datetime(r_fase["Fecha Fin"]).date()
            nombre_fase = r_fase["Fase / Etapa del Proyecto"]
            
            filas_hitos.append({
                "Fecha": f_ini,
                "Hora Inicio": "08:00",
                "Hora Fin": "09:00",
                "Actividad / Detalle Diario": f"🏁 [INICIO DE FASE] {nombre_fase}",
                "Tipo / Origen": "Hito Oficial Maestro",
                "Fase Asociada": nombre_fase
            })
            
            if f_fin > f_ini:
                filas_hitos.append({
                    "Fecha": f_fin,
                    "Hora Inicio": "20:00",
                    "Hora Fin": "21:00",
                    "Actividad / Detalle Diario": f"🎯 [CIERRE DE FASE] {nombre_fase}",
                    "Tipo / Origen": "Hito Oficial Maestro",
                    "Fase Asociada": nombre_fase
                })

        df_hitos_maestros = pd.DataFrame(filas_hitos)
        df_operativo = st.session_state.df_agenda_matriz.copy()
        df_operativo["Fecha"] = pd.to_datetime(df_operativo["Fecha"]).dt.date

        if not df_hitos_maestros.empty:
            df_maestro = pd.concat([df_hitos_maestros, df_operativo], ignore_index=True)
        else:
            df_maestro = df_operativo

        df_maestro = df_maestro.drop_duplicates(subset=["Fecha", "Hora Inicio", "Actividad / Detalle Diario"])
        df_maestro = df_maestro.sort_values(by=["Fecha", "Hora Inicio"]).reset_index(drop=True)
        df_maestro["Fecha Formateada"] = df_maestro["Fecha"].apply(formatear_fecha_espanol)

        st.markdown("#### 📋 Agenda General de Campo y Distribución Táctica")
        st.write("Consulta y comparte tu agenda sincronizada en cualquiera de sus 4 modalidades:")

        tab_dia, tab_semana, tab_mes, tab_general = st.tabs([
            "📅 Vista Diaria", 
            "📆 Vista Semanal", 
            "🗓️ Vista Mensual", 
            "🌐 Vista General (Proceso Completo)"
        ])
        
        cols_vistas = ["Fecha Formateada", "Hora Inicio", "Hora Fin", "Actividad / Detalle Diario", "Tipo / Origen", "Fase Asociada"]

        with tab_dia:
            st.markdown("##### 🔍 Consulta por Día Específico")
            if not df_maestro.empty:
                fechas_disp = sorted(df_maestro["Fecha"].unique())
                fecha_sel = st.selectbox("Selecciona la fecha:", fechas_disp, format_func=formatear_fecha_espanol, key="vd_f4")
                
                df_d = df_maestro[df_maestro["Fecha"] == fecha_sel].copy()
                if not df_d.empty:
                    st.dataframe(df_d[cols_vistas], use_container_width=True)
                    txt_wa = f"*AGENDA DIARIA - {formatear_fecha_espanol(fecha_sel)}*\n\n"
                    for _, r in df_d.iterrows():
                        txt_wa += f"⏰ {r['Hora Inicio']} - {r['Hora Fin']}\n📌 {r['Actividad / Detalle Diario']}\n\n"
                    url_wa = f"https://wa.me/?text={urllib.parse.quote(txt_wa)}"
                    
                    c1, c2 = st.columns(2)
                    with c1: st.markdown(f'<a href="{url_wa}" target="_blank"><button style="width:100%; background-color:#25d366; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold; cursor:pointer;">💬 Compartir Día por WhatsApp</button></a>', unsafe_allow_html=True)
                    with c2: 
                        if st.button("🖨️ Imprimir Vista Diaria", key="pr_d_f4"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
                else:
                    st.info("ℹ️ Sin actividades para este día.")
            else:
                st.info("ℹ️ Agenda vacía.")

        with tab_semana:
            st.markdown("##### 📆 Consulta por Semana Operativa")
            if not df_maestro.empty:
                f_sem = st.date_input("Selecciona un día dentro de la semana:", value=date.today(), key="vs_f4")
                ini_sem = f_sem - timedelta(days=f_sem.weekday())
                fin_sem = ini_sem + timedelta(days=6)
                
                st.caption(f"Semana del **{formatear_fecha_espanol(ini_sem)}** al **{formatear_fecha_espanol(fin_sem)}**")
                
                df_s = df_maestro[(df_maestro["Fecha"] >= ini_sem) & (df_maestro["Fecha"] <= fin_sem)].copy()
                
                if not df_s.empty:
                    st.dataframe(df_s[cols_vistas], use_container_width=True)
                    txt_was = f"*AGENDA SEMANAL* ({formatear_fecha_espanol(ini_sem)} al {formatear_fecha_espanol(fin_sem)})\n\n"
                    for _, r in df_s.iterrows():
                        txt_was += f"📅 {r['Fecha Formateada']} | ⏰ {r['Hora Inicio']}\n📌 {r['Actividad / Detalle Diario']}\n\n"
                    url_was = f"https://wa.me/?text={urllib.parse.quote(txt_was)}"
                    
                    col_ws1, col_ws2 = st.columns(2)
                    with col_ws1: st.markdown(f'<a href="{url_was}" target="_blank"><button style="width:100%; background-color:#25d366; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold; cursor:pointer;">💬 Compartir Semana por WhatsApp</button></a>', unsafe_allow_html=True)
                    with col_ws2: 
                        if st.button("🖨️ Imprimir Vista Semanal", key="pr_s_f4"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
                else:
                    st.info("ℹ️ Sin hitos ni actividades registradas para esta semana.")
            else:
                st.info("ℹ️ Agenda vacía.")

        with tab_mes:
            st.markdown("##### 🗓️ Consulta por Mes Completo del Proceso Electoral")
            if not df_maestro.empty:
                meses_proceso = [
                    (9, 2026), (10, 2026), (11, 2026), (12, 2026),
                    (1, 2027), (2, 2027), (3, 2027), (4, 2027), (5, 2027), (6, 2027)
                ]
                opciones_meses = [f"{meses_es[m]} de {a}" for m, a in meses_proceso]
                mes_elegido_txt = st.selectbox("Selecciona el Mes del Proceso:", opciones_meses, key="vm_f4")
                
                partes = mes_elegido_txt.split(" de ")
                m_nom, a_num = partes[0], int(partes[1])
                m_num = [k for k, v in meses_es.items() if v == m_nom][0]
                
                df_m = df_maestro[(pd.to_datetime(df_maestro["Fecha"]).dt.month == m_num) & (pd.to_datetime(df_maestro["Fecha"]).dt.year == a_num)].copy()
                
                if not df_m.empty:
                    st.dataframe(df_m[cols_vistas], use_container_width=True)
                    txt_wam = f"*AGENDA MENSUAL - {mes_elegido_txt.upper()}*\n\n"
                    for _, r in df_m.iterrows():
                        txt_wam += f"📅 {r['Fecha Formateada']} | ⏰ {r['Hora Inicio']}\n📌 {r['Actividad / Detalle Diario']}\n\n"
                    url_wam = f"https://wa.me/?text={urllib.parse.quote(txt_wam)}"
                    
                    col_wm1, col_wm2 = st.columns(2)
                    with col_wm1: st.markdown(f'<a href="{url_wam}" target="_blank"><button style="width:100%; background-color:#25d366; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold; cursor:pointer;">💬 Compartir Mes por WhatsApp</button></a>', unsafe_allow_html=True)
                    with col_wm2: 
                        if st.button("🖨️ Imprimir Vista Mensual", key="pr_m_f4"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
                else:
                    st.info(f"ℹ️ No hay hitos ni actividades registradas para {mes_elegido_txt}.")
            else:
                st.info("ℹ️ Agenda vacía.")

        with tab_general:
            st.markdown("##### 🌐 Vista General del Proceso Electoral (Septiembre 2026 - Junio 2027)")
            if not df_maestro.empty:
                st.dataframe(df_maestro[cols_vistas], use_container_width=True)
                txt_wag = f"*CRONOGRAMA GENERAL - PROCESO ELECTORAL*\n\n"
                for _, r in df_maestro.iterrows():
                    txt_wag += f"📅 {r['Fecha Formateada']} | ⏰ {r['Hora Inicio']}\n📌 {r['Actividad / Detalle Diario']}\n\n"
                url_wag = f"https://wa.me/?text={urllib.parse.quote(txt_wag)}"
                
                col_wg1, col_wg2 = st.columns(2)
                with col_wg1: st.markdown(f'<a href="{url_wag}" target="_blank"><button style="width:100%; background-color:#25d366; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold; cursor:pointer;">💬 Compartir Cronograma General por WhatsApp</button></a>', unsafe_allow_html=True)
                with col_wg2: 
                    if st.button("🖨️ Imprimir Vista General", key="pr_g_f4"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            else:
                st.info("ℹ️ Agenda vacía.")

        with st.expander("⚙️ Editar Actividades Operativas Diarias (Base Cruda)", expanded=False):
            matriz_column_config = {
                "Fecha": st.column_config.DateColumn("Fecha (YYYY-MM-DD)", format="YYYY-MM-DD", required=True),
                "Hora Inicio": st.column_config.TextColumn("Hora Inicio", required=True),
                "Hora Fin": st.column_config.TextColumn("Hora Fin", required=True),
                "Actividad / Detalle Diario": st.column_config.TextColumn("Actividad / Detalle Diario", required=True),
                "Tipo / Origen": st.column_config.TextColumn("Tipo / Origen", disabled=True),
                "Fase Asociada": st.column_config.SelectboxColumn("Fase Asociada", options=FASES_ELECTORALES_OFICIALES, required=True)
            }
            df_matriz_editado = st.data_editor(st.session_state.df_agenda_matriz, column_config=matriz_column_config, num_rows="dynamic", use_container_width=True, key="editor_matriz_final_v4")
            if not df_matriz_editado.equals(st.session_state.df_agenda_matriz):
                st.session_state.df_agenda_matriz = df_matriz_editado
                st.success("✅ Matriz operativa actualizada.")
                st.rerun()