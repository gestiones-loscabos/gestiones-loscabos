import streamlit as st
import streamlit.components.v1 as components
import psycopg2
import pandas as pd
import urllib.parse
import os
import subprocess
import platform
import re
import math
from datetime import date, timedelta, datetime
from PIL import Image, ImageEnhance

# --- DETECCIÓN INTELIGENTE DE ENTORNO: HOST LOCAL VS NUBE ---
ES_LOCAL = platform.system() == "Windows"
ETIQUETA_ENTORNO = "🛡️ Cuarto de Guerra Digital - Versión Host Local (Master)" if ES_LOCAL else "☁️ Cuarto de Guerra Digital - Versión Nube (BCS)"
COLOR_PRIMARIO_ENTORNO = "#10b981" if ES_LOCAL else "#38bdf8"

# --- IMPORTACIÓN DE TESSERACT ---
try:
    import pytesseract
    if ES_LOCAL:
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    OCR_DISPONIBLE = True
except ImportError:
    OCR_DISPONIBLE = False

# --- IMPORTACIÓN DE GEOLOCALIZACIÓN ---
try:
    from streamlit_geolocation import streamlit_geolocation
    GEOLOC_DISPONIBLE = True
except ImportError:
    GEOLOC_DISPONIBLE = False

# --- CONFIGURACIÓN DE PÁGINA Y ESTILO TÁCTICO OSCURO SIMÉTRICO ---
st.set_page_config(
    page_title=ETIQUETA_ENTORNO,
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(f"""
<style>
    .stApp {{ background-color: #07090e; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
    label, .stTextInput label, .stSelectbox label, .stRadio label, .stDateInput label {{ 
        color: #38bdf8 !important; 
        font-weight: bold !important; 
        font-size: 14px !important; 
    }}
    p, span, div, h3, h4, h5 {{ color: #f8fafc !important; }}
    input, textarea {{ 
        color: #ffffff !important; 
        background-color: #111827 !important; 
        border: 1px solid #38bdf8 !important;
        border-radius: 6px !important;
    }}
    div.stButton > button:first-child {{ 
        background: linear-gradient(135deg, #0284c7 0%, #1d4ed8 100%); 
        color: #ffffff !important; 
        border-radius: 6px; 
        font-weight: bold; 
        font-size: 14px;
        border: 1px solid #38bdf8;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
        width: 100%;
    }}
    div.stButton > button:first-child:hover {{ 
        background: linear-gradient(135deg, #0369a1 0%, #1e40af 100%); 
        border-color: #7dd3fc; 
    }}
    .caja-bloque {{ 
        background-color: #0f172a; 
        border-left: 4px solid {COLOR_PRIMARIO_ENTORNO}; 
        padding: 16px; 
        margin-top: 12px; 
        margin-bottom: 12px; 
        border-radius: 8px; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        border-top: 1px solid #1e293b;
        border-right: 1px solid #1e293b;
        border-bottom: 1px solid #1e293b;
    }}
    .titulo-caja {{ color: #38bdf8; font-weight: bold; font-size: 1.1rem; margin-bottom: 8px; letter-spacing: 0.3px; }}
    .stat-box {{ 
        background-color: #0f172a; 
        padding: 14px; 
        border-radius: 8px; 
        text-align: center; 
        border: 1px solid #334155; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        margin-bottom: 8px;
    }}
    .stat-num {{ font-size: 22px; font-weight: bold; color: {COLOR_PRIMARIO_ENTORNO}; margin-top: 4px; }}
    .stat-label {{ font-size: 11px; color: #cbd5e1; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }}
    [data-testid="stSidebar"] {{
        background-color: #090d16 !important;
        border-right: 1px solid #1e293b;
    }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {{
        color: #f1f5f9 !important;
    }}
    .mobile-simulator {{
        background-color: #0f172a;
        border: 14px solid #1e293b;
        border-radius: 30px;
        padding: 16px;
        min-height: 720px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.6);
    }}
    .card-nodo {{ background-color: #1e293b; border: 1px solid #334155; border-left: 4px solid #10b981; padding: 12px; margin-bottom: 10px; border-radius: 6px; font-size: 13px; color: #fff; }}
    .card-subnodo {{ background-color: #0f172a; border: 1px solid #1e293b; border-left: 4px solid #3b82f6; padding: 10px; margin-left: 15px; margin-bottom: 8px; border-radius: 6px; font-size: 12px; color: #fff; }}
    .card-simp {{ background-color: #07090e; border: 1px solid #1e293b; border-left: 4px solid #6366f1; padding: 8px; margin-left: 30px; margin-bottom: 6px; border-radius: 6px; font-size: 11px; color: #cbd5e1; }}
    .teleprompter-box {{ background-color: #000000; border: 3px solid #ef4444; border-radius: 8px; padding: 18px; margin-top: 12px; }}
</style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A BASE DE DATOS Y GESTIÓN DE CARPETAS ---
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
    base_path = r"C:\Users\Usuario\Desktop\Plataforma_Electoral" if ES_LOCAL else "/tmp/Plataforma_Electoral"
    carpetas_requeridas = [
        base_path,
        os.path.join(base_path, "ESTRATEGIA"),
        os.path.join(base_path, "UBICACION CASILLAS"),
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
# DETECCIÓN AUTÓNOMA DE ARCHIVOS EN UBICACION CASILLAS
# =============================================================================
def encontrar_archivo_cartografia():
    carpetas_busqueda = [
        r"C:\Users\Usuario\Desktop\Plataforma_Electoral\UBICACION CASILLAS" if ES_LOCAL else "/tmp/Plataforma_Electoral/UBICACION_CASILLAS",
        r"C:\Users\Usuario\Desktop\Plataforma_Electoral\Cartografia_INE" if ES_LOCAL else "/tmp/Plataforma_Electoral/Cartografia_INE",
        "."
    ]
    for carpeta in carpetas_busqueda:
        if os.path.exists(carpeta):
            for f in os.listdir(carpeta):
                if f.lower().endswith(('.xlsx', '.xls', '.csv')) and not f.startswith('~$'):
                    return os.path.join(carpeta, f)
    return None

@st.cache_data(ttl=300)
def cargar_cartografia_ine_dinamica(distrito_filtro_nombre):
    ruta_archivo = encontrar_archivo_cartografia()
    casillas_cargadas = []
    c_urb = 0
    c_rur = 0
    
    if ruta_archivo and os.path.exists(ruta_archivo):
        try:
            if ruta_archivo.lower().endswith('.csv'):
                df_ine = pd.read_csv(ruta_archivo)
            else:
                xls = pd.ExcelFile(ruta_archivo)
                hoja_sel = [h for h in xls.sheet_names if 'CASILLA' in h.upper() or 'TODAS' in h.upper()]
                nombre_hoja = hoja_sel[0] if hoja_sel else xls.sheet_names[0]
                
                df_ine = pd.read_excel(ruta_archivo, sheet_name=nombre_hoja, header=3)
                if not any('SECCI' in str(c).upper() for c in df_ine.columns):
                    df_ine = pd.read_excel(ruta_archivo, sheet_name=nombre_hoja, header=0)
            
            df_ine.columns = [str(c).strip() for c in df_ine.columns]
            cols_dist = [c for c in df_ine.columns if 'DISTRITO' in c.upper()]
            col_distrito = cols_dist[1] if len(cols_dist) > 1 else cols_dist[0] if cols_dist else df_ine.columns[1]
            
            if "TODOS" in str(distrito_filtro_nombre).upper():
                df_filtrado = df_ine
            else:
                match_num = re.search(r'\d+', str(distrito_filtro_nombre))
                num_distrito = match_num.group(0) if match_num else "16"
                df_filtrado = df_ine[df_ine[col_distrito].astype(str).str.contains(num_distrito, case=False, na=False)]
                if df_filtrado.empty:
                    df_filtrado = df_ine
                    
            for _, row in df_filtrado.iterrows():
                try:
                    col_sec_nom = [c for c in df_filtrado.columns if 'SECCI' in c.upper()]
                    seccion_val = row[col_sec_nom[0]] if col_sec_nom else row.get('Sección', 400)
                    seccion = str(int(float(seccion_val))).zfill(4) if pd.notna(seccion_val) else "0400"
                    
                    col_tipo_nom = [c for c in df_filtrado.columns if 'TIPO' in c.upper() and 'SECC' in c.upper()]
                    tipo_sec = str(row[col_tipo_nom[0]]) if col_tipo_nom else "URBANA"
                    zona = "Urbana" if "URBANA" in tipo_sec.upper() and "NO" not in tipo_sec.upper() else "Rural"
                    
                    dom = str(row.get('Domicilio', '')) if pd.notna(row.get('Domicilio', '')) else ""
                    ubica = str(row.get('Ubicación', '')) if pd.notna(row.get('Ubicación', '')) else ""
                    col_nom = str(row.get('Colonia', 'Col. Centro')) if pd.notna(row.get('Colonia', '')) else "Col. Centro"
                    ubicacion = f"{ubica} - {dom}".strip(" - ")
                    
                    lat = float(row['Latitud']) if 'Latitud' in df_filtrado.columns and pd.notna(row['Latitud']) else 22.8905
                    lon = float(row['Longitud']) if 'Longitud' in df_filtrado.columns and pd.notna(row['Longitud']) else -109.9167
                    
                    col_cas_inst = [c for c in df_filtrado.columns if 'INSTALAR' in c.upper() or 'CASILLAS' in c.upper()]
                    casillas_str = str(row[col_cas_inst[0]]) if col_cas_inst else "B1"
                    
                    casillas_arr = casillas_str.split(',')
                    for c_tipo in casillas_arr:
                        c_tipo = c_tipo.strip()
                        if c_tipo and c_tipo != "nan":
                            casillas_cargadas.append({
                                "id_casilla": f"CAS-{seccion}-{c_tipo}",
                                "seccion": seccion,
                                "tipo_casilla": c_tipo,
                                "zona": zona,
                                "ubicacion": ubicacion,
                                "colonia": col_nom,
                                "lat": lat,
                                "lon": lon
                            })
                            if zona == "Urbana": c_urb += 1
                            else: c_rur += 1
                except Exception:
                    continue
        except Exception as e:
            print(f"Error procesando cartografía: {e}")
            
    if not casillas_cargadas:
        casillas_cargadas = [
            {"id_casilla": "CAS-0318-B1", "seccion": "0318", "tipo_casilla": "Básica", "zona": "Urbana", "ubicacion": "Primaria 18 de Marzo - Carranza y Matamoros", "colonia": "Centro", "lat": 22.8905, "lon": -109.9167},
            {"id_casilla": "CAS-0318-C1", "seccion": "0318", "tipo_casilla": "Contigua 1", "zona": "Urbana", "ubicacion": "Primaria 18 de Marzo - Carranza y Matamoros", "colonia": "Centro", "lat": 22.8907, "lon": -109.9169},
            {"id_casilla": "CAS-0400-B1", "seccion": "0400", "tipo_casilla": "Básica", "zona": "Urbana", "ubicacion": "Primaria Leona Vicario - Av. Morelos", "colonia": "Centro", "lat": 22.8915, "lon": -109.9175},
            {"id_casilla": "CAS-0401-B1", "seccion": "0401", "tipo_casilla": "Básica", "zona": "Urbana", "ubicacion": "Jardín de Niños Los Mangos - Aguajitos", "colonia": "Los Mangos", "lat": 22.8950, "lon": -109.9200},
            {"id_casilla": "CAS-0420-B1", "seccion": "0420", "tipo_casilla": "Básica", "zona": "Rural", "ubicacion": "Escuela Rural Vicente Guerrero - Domicilio Conocido", "colonia": "La Candelaria", "lat": 22.9200, "lon": -109.8900}
        ]
        c_urb = 4
        c_rur = 1
        
    return casillas_cargadas, c_urb, c_rur

# =============================================================================
# INICIALIZACIÓN TEMPRANA DE ESTADOS GLOBALES
# =============================================================================
if "distrito_activo_sel" not in st.session_state:
    st.session_state.distrito_activo_sel = "Distrito 16 (Cabo San Lucas - Principal)"

cat_init, urb_init, rur_init = cargar_cartografia_ine_dinamica(st.session_state.distrito_activo_sel)
if "cat_casillas_ine" not in st.session_state: st.session_state.cat_casillas_ine = cat_init
if "conteo_casillas_urbanas" not in st.session_state: st.session_state.conteo_casillas_urbanas = urb_init
if "conteo_casillas_rurales" not in st.session_state: st.session_state.conteo_casillas_rurales = rur_init

if "modo_calibracion_juridica" not in st.session_state: st.session_state.modo_calibracion_juridica = "Automático (Lectura de Archivo INE)"
if "manual_c_urb" not in st.session_state: st.session_state.manual_c_urb = urb_init
if "manual_c_rur" not in st.session_state: st.session_state.manual_c_rur = rur_init

# MEMORIA GLOBAL TERRITORIAL Y ESTADO DE VOTACIÓN (GOTV)
if "registro_territorial_global" not in st.session_state:
    st.session_state.registro_territorial_global = [
        {"id_reg": "REG-01", "id_ca": "CA-01", "rol": "Anfitrión (CA)", "nombre": "Roberto Hernández", "seccion": "0318", "domicilio": "C Carranza / Matamoros e HIDALGO DEPT308", "celular": "6681140172", "redes": "Facebook: RobertoHC", "referencia": "CA", "lat": 22.8905, "lon": -109.9167, "tipo_voto": "Duro", "voto_emitido": False, "hora_voto": ""},
        {"id_reg": "REG-02", "id_ca": "CA-01", "rol": "Simpatizante", "nombre": "Rosa Elena", "seccion": "0318", "domicilio": "Col. Centro", "celular": "6241110000", "redes": "Facebook: RosaE", "referencia": "CA", "lat": 22.8906, "lon": -109.9168, "tipo_voto": "Duro", "voto_emitido": True, "hora_voto": "09:30"},
        {"id_reg": "REG-03", "id_ca": "CA-01", "rol": "Simpatizante", "nombre": "Jorge M.", "seccion": "0318", "domicilio": "Col. Centro", "celular": "6241110001", "redes": "Facebook: JorgeM", "referencia": "CA", "lat": 22.8907, "lon": -109.9169, "tipo_voto": "Duro", "voto_emitido": False, "hora_voto": ""},
        {"id_reg": "REG-04", "id_ca": "CA-01", "rol": "Coanfitrión", "nombre": "Jesús Martínez", "seccion": "0400", "domicilio": "Col. Centro", "celular": "6241234567", "redes": "Instagram: @jesus_m", "referencia": "C1", "lat": 22.8910, "lon": -109.9170, "tipo_voto": "Duro", "voto_emitido": False, "hora_voto": ""},
        {"id_reg": "REG-05", "id_ca": "CA-01", "rol": "Simpatizante", "nombre": "Carlos López", "seccion": "0400", "domicilio": "Calle Sol 12", "celular": "6249876543", "redes": "Facebook: CarlosL", "referencia": "C1", "lat": 22.8915, "lon": -109.9175, "tipo_voto": "Duro", "voto_emitido": True, "hora_voto": "10:15"},
        {"id_reg": "REG-06", "id_ca": "CA-01", "rol": "Simpatizante", "nombre": "Sofía R.", "seccion": "0400", "domicilio": "Calle Sol 14", "celular": "6249876544", "redes": "Facebook: SofiaR", "referencia": "C1", "lat": 22.8916, "lon": -109.9176, "tipo_voto": "Duro", "voto_emitido": False, "hora_voto": ""},
        {"id_reg": "REG-07", "id_ca": "CA-01", "rol": "Promotor / Enlace", "nombre": "Mario Rivas", "seccion": "0400", "domicilio": "Col. Centro CSL", "celular": "6241556677", "redes": "Facebook: MarioR", "referencia": "C1", "lat": 22.8912, "lon": -109.9172, "tipo_voto": "Duro", "voto_emitido": False, "hora_voto": ""},
        {"id_reg": "REG-08", "id_ca": "CA-01", "rol": "Simpatizante", "nombre": "Ana P.", "seccion": "0400", "domicilio": "Col. Centro", "celular": "6241556678", "redes": "Facebook: AnaP", "referencia": "Promotor C1", "lat": 22.8913, "lon": -109.9173, "tipo_voto": "Duro", "voto_emitido": False, "hora_voto": ""},
        {"id_reg": "REG-09", "id_ca": "CA-01", "rol": "Simpatizante", "nombre": "Luis G.", "seccion": "0400", "domicilio": "Col. Centro", "celular": "6241556679", "redes": "Facebook: LuisG", "referencia": "Promotor C1", "lat": 22.8914, "lon": -109.9174, "tipo_voto": "Duro", "voto_emitido": True, "hora_voto": "11:00"},
        {"id_reg": "REG-10", "id_ca": "CA-01", "rol": "Simpatizante Común", "nombre": "Guillermo Pérez", "seccion": "0318", "domicilio": "Calle Morelos 45", "celular": "6241112233", "redes": "Facebook: MemoPerez", "referencia": "Redes Sociales", "lat": 22.8920, "lon": -109.9180, "tipo_voto": "Aire", "voto_emitido": False, "hora_voto": ""},
        {"id_reg": "REG-11", "id_ca": "CA-02", "rol": "Simpatizante Común", "nombre": "Beatriz V.", "seccion": "0401", "domicilio": "Col. Cangrejos", "celular": "6241118899", "redes": "TikTok: @beatrizv", "referencia": "Link Registro Web", "lat": 22.8985, "lon": -109.9260, "tipo_voto": "Aire", "voto_emitido": True, "hora_voto": "08:45"},
        {"id_reg": "REG-12", "id_ca": "CA-02", "rol": "Anfitrión (CA)", "nombre": "María González", "seccion": "0401", "domicilio": "Col. Cangrejos, CSL", "celular": "6242223344", "redes": "Instagram: @maria_g", "referencia": "CA", "lat": 22.8980, "lon": -109.9250, "tipo_voto": "Duro", "voto_emitido": False, "hora_voto": ""},
        {"id_reg": "REG-13", "id_ca": "CA-02-ESP", "rol": "Anfitrión (CA)", "nombre": "Sofía Castro", "seccion": "0401", "domicilio": "Col. Cangrejos Norte", "celular": "6242229988", "redes": "Facebook: SofiaC", "referencia": "CA-02", "lat": 22.9020, "lon": -109.9280, "tipo_voto": "Duro", "voto_emitido": False, "hora_voto": ""},
        {"id_reg": "REG-14", "id_ca": "DEFENSA", "rol": "RG", "nombre": "Fernando Castro", "seccion": "0400", "domicilio": "Av. Las Palmas", "celular": "6243334455", "redes": "Facebook: FCastro", "referencia": "Bloque Urbano", "id_casilla": "CAS-0400-B1", "calidad": "Propietario", "lat": 22.8950, "lon": -109.9200, "tipo_voto": "Duro", "voto_emitido": True, "hora_voto": "08:15"},
        {"id_reg": "REG-15", "id_ca": "DEFENSA", "rol": "RC", "nombre": "Lucía Morales", "seccion": "0400", "domicilio": "Col. Centro", "celular": "6244445566", "redes": "Instagram: @lucia_m", "referencia": "Casilla 0400 Básica", "id_casilla": "CAS-0400-B1", "calidad": "Propietario", "lat": 22.8905, "lon": -109.9167, "tipo_voto": "Duro", "voto_emitido": True, "hora_voto": "08:10"}
    ]

# REPOSITORIO LEGAL DE INCIDENCIAS
if "repositorio_incidencias_legal" not in st.session_state:
    st.session_state.repositorio_incidencias_legal = [
        {"Folio": "INC-0400-0810", "Hora": "08:10 hrs", "Casilla": "CAS-0400-B1", "Sección": "0400", "Tipo Incidencia": "Apertura tardía de casilla", "Reportante": "Lucía Morales (RC)", "Estatus": "Atendida"},
        {"Folio": "INC-0318-0940", "Hora": "09:40 hrs", "Casilla": "CAS-0318-B1", "Sección": "0318", "Tipo Incidencia": "Presencia de propaganda en perímetro", "Reportante": "Fernando Castro (RG)", "Estatus": "En Proceso"}
    ]

if "mostrar_teleprompter_activo" not in st.session_state: st.session_state.mostrar_teleprompter_activo = False
if "teleprompter_datos" not in st.session_state: st.session_state.teleprompter_datos = {}

# =============================================================================
# DEFINICIÓN GLOBAL DE DF_PADRÓN
# =============================================================================
df_padrón = pd.DataFrame(st.session_state.registro_territorial_global)
df_terr_def = df_padrón

# =============================================================================
# ENRUTAMIENTO DINÁMICO POR PARÁMETROS URL (?view=...)
# =============================================================================
query_params = st.query_params
if "view" in query_params:
    vista_solicitada = query_params["view"]
    if vista_solicitada == "voto_emitido":
        st.session_state.seccion_activa = "DIA_D"
    elif vista_solicitada == "simpatizante":
        st.session_state.seccion_activa = "TERRITORIAL"
    elif vista_solicitada == "tracking_poll":
        st.session_state.seccion_activa = "SIMULADOR"
    elif vista_solicitada == "reporte_sos":
        st.session_state.seccion_activa = "DIA_D"

# CÁLCULOS MATEMÁTICOS GLOBALES Y CALIBRACIÓN JURÍDICA
if st.session_state.modo_calibracion_juridica == "Automático (Lectura de Archivo INE)":
    c_urb = st.session_state.conteo_casillas_urbanas
    c_rur = st.session_state.conteo_casillas_rurales
else:
    c_urb = st.session_state.manual_c_urb
    c_rur = st.session_state.manual_c_rur

total_casillas_distrito = c_urb + c_rur

meta_rc_total = total_casillas_distrito * 2
bloques_rg_urb = math.ceil(c_urb / 10) * 2 if c_urb > 0 else 0
bloques_rg_rur = math.ceil(c_rur / 5) * 2 if c_rur > 0 else 0
meta_rg_total = bloques_rg_urb + bloques_rg_rur
meta_obs_total = meta_rg_total
meta_defensa_global = meta_rc_total + meta_rg_total + meta_obs_total

rc_registrados = len(df_padrón[df_padrón['rol'] == 'RC']) if not df_padrón.empty else 0
rg_registrados = len(df_padrón[df_padrón['rol'] == 'RG']) if not df_padrón.empty else 0
obs_registrados = len(df_padrón[df_padrón['rol'] == 'Observador Electoral']) if not df_padrón.empty else 0
total_defensa_actual = rc_registrados + rg_registrados + obs_registrados

if "contador_casas_amigas" not in st.session_state: st.session_state.contador_casas_amigas = 3
if "num_seccionales" not in st.session_state: st.session_state.num_seccionales = 27
if "casas_por_seccional" not in st.session_state: st.session_state.casas_por_seccional = 4
if "factor_votos_casa" not in st.session_state: st.session_state.factor_votos_casa = 88

# Buffer de captura OCR
if "ocr_nombre_capturado" not in st.session_state: st.session_state.ocr_nombre_capturado = ""
if "ocr_seccion_capturada" not in st.session_state: st.session_state.ocr_seccion_capturada = ""
if "ocr_domicilio_capturado" not in st.session_state: st.session_state.ocr_domicilio_capturado = ""
if "ocr_imagen_path" not in st.session_state: st.session_state.ocr_imagen_path = None

if "gps_lat_temp" not in st.session_state: st.session_state.gps_lat_temp = 22.8905
if "gps_lon_temp" not in st.session_state: st.session_state.gps_lon_temp = -109.9167
if "gps_lat_esp_temp" not in st.session_state: st.session_state.gps_lat_esp_temp = 22.8980
if "gps_lon_esp_temp" not in st.session_state: st.session_state.gps_lon_esp_temp = -109.9250

def limpiar_buffer_registro():
    st.session_state.ocr_nombre_capturado = ""
    st.session_state.ocr_seccion_capturada = ""
    st.session_state.ocr_domicilio_capturado = ""
    st.session_state.ocr_imagen_path = None
    st.session_state.gps_lat_temp = 22.8905
    st.session_state.gps_lon_temp = -109.9167
    st.session_state.gps_lat_esp_temp = 22.8980
    st.session_state.gps_lon_esp_temp = -109.9250

def guardar_registro_dual(id_ca, rol, nombre, seccion, domicilio, celular, red_social="", usuario_red="", referencia="", lat=22.8905, lon=-109.9167, id_casilla="", calidad="Propietario", tipo_voto="Duro"):
    redes_completo = f"{red_social}: {usuario_red}" if red_social and usuario_red else ""
    nuevo_id_reg = f"REG-{len(st.session_state.registro_territorial_global) + 1:02d}"
    nuevo_reg = {
        "id_reg": nuevo_id_reg, "id_ca": id_ca, "rol": rol, "nombre": nombre,
        "seccion": seccion, "domicilio": domicilio, "celular": celular, "redes": redes_completo, 
        "referencia": referencia, "lat": float(lat), "lon": float(lon), "id_casilla": id_casilla, 
        "calidad": calidad, "tipo_voto": tipo_voto, "voto_emitido": False, "hora_voto": ""
    }
    st.session_state.registro_territorial_global.append(nuevo_reg)

def obtener_lista_casas_amigas():
    casas = [f"{r['id_ca']} - {r['nombre']}" for r in st.session_state.registro_territorial_global if r['rol'] == 'Anfitrión (CA)' and not "-ESP" in str(r['id_ca'])]
    if not casas:
        casas = ["CA-01 - (Sin anfitriones aún)"]
    return casas

def obtener_lista_casas_todas():
    casas = [f"{r['id_ca']} - {r['nombre']}" for r in st.session_state.registro_territorial_global if r['rol'] == 'Anfitrión (CA)']
    if not casas:
        casas = ["CA-01 - (Sin anfitriones aún)"]
    return casas

# --- CONSTANTES Y TABLA DE FASES DE AGENDA ---
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

# --- DIRECTORIO DE MANDO EDITABLE ---
if "directorio_mando_estrategico" not in st.session_state:
    st.session_state.directorio_mando_estrategico = pd.DataFrame([
        {"Puesto": "Candidato(a)", "Nombre": "Candidato Titular", "Tel": "6241000001"},
        {"Puesto": "Secretario(a) Particular", "Nombre": "Lic. Despacho", "Tel": "6241000002"},
        {"Puesto": "Coordinador General de Campaña", "Nombre": "Coordinador General", "Tel": "6241000003"},
        {"Puesto": "Coordinador de Distrito 16", "Nombre": "Coordinador Distrital", "Tel": "6241000004"},
        {"Puesto": "Encargado(a) Electoral / Jurídico", "Nombre": "Abogado General", "Tel": "6241000005"},
        {"Puesto": "Encargado(a) Administrativo", "Nombre": "Administración y Finanzas", "Tel": "6241000006"},
        {"Puesto": "Logística (Elemento 1)", "Nombre": "Operaciones Campo 1", "Tel": "6241000007"},
        {"Puesto": "Logística (Elemento 2)", "Nombre": "Operaciones Campo 2", "Tel": "6241000008"}
    ])

opciones_contactos_mando = []
dict_contactos_mando = {}

for _, r_mando in st.session_state.directorio_mando_estrategico.iterrows():
    if pd.notna(r_mando['Puesto']) and pd.notna(r_mando['Tel']):
        etiq = f"{r_mando['Puesto']}: {r_mando['Nombre']} ({r_mando['Tel']})"
        opciones_contactos_mando.append(etiq)
        dict_contactos_mando[etiq] = str(r_mando['Tel'])

if not df_padrón.empty:
    for _, r in df_padrón.iterrows():
        if r['rol'] in ['Anfitrión (CA)', 'RG']:
            etiq_est = f"[{r['rol']}] {r['nombre']} (Sec: {r['seccion']}) - Cel: {r['celular']}"
            if etiq_est not in dict_contactos_mando:
                opciones_contactos_mando.append(etiq_est)
                dict_contactos_mando[etiq_est] = str(r['celular'])

# --- AUTENTICACIÓN DINÁMICA ---
if "autenticado" not in st.session_state: st.session_state.autenticado = False
if "usuario_actual" not in st.session_state: st.session_state.usuario_actual = None
if "nivel_permiso" not in st.session_state: st.session_state.nivel_permiso = None
if "rol_usuario" not in st.session_state: st.session_state.rol_usuario = None

if not st.session_state.autenticado:
    st.markdown(f"<br><br><h1 style='text-align: center; color: {COLOR_PRIMARIO_ENTORNO}; font-size: 2.5rem;'>{ETIQUETA_ENTORNO}</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #cbd5e1; font-size: 1.1rem;'>Plataforma Electoral Táctica - Baja California Sur</p>", unsafe_allow_html=True)
    
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

# --- DETERMINACIÓN DINÁMICA DE URL BASE PARA ENLACES ---
URL_BASE_SISTEMA = "http://localhost:8502" if ES_LOCAL else "https://silver-journey-wvgjx59pjp4wc5p4v-8501.app.github.dev"

# --- ESTADOS DE NAVEGACIÓN ---
if "ver_antecedentes_encuesta" not in st.session_state: st.session_state.ver_antecedentes_encuesta = False
if "ver_modal_cascada" not in st.session_state: st.session_state.ver_modal_cascada = False
if "ver_modal_coordinacion" not in st.session_state: st.session_state.ver_modal_coordinacion = False
if "ver_modal_brigadistas" not in st.session_state: st.session_state.ver_modal_brigadistas = False
if "seccion_activa" not in st.session_state: st.session_state.seccion_activa = "TABLERO"

# ==========================================
# MENÚ LATERAL: CENTRAL DE LINKS MAESTROS
# ==========================================
with st.sidebar:
    st.markdown(f"### 👤 Usuario: {st.session_state.usuario_actual}")
    st.markdown(f"🛡️ **Rol:** `{st.session_state.rol_usuario}`")
    st.caption(f"Distrito: {st.session_state.get('distrito_usuario', 'General')} | Entorno: {'Local' if ES_LOCAL else 'Nube'}")
    st.markdown("---")
    
    st.markdown("### 🧭 Navegación Táctica")
    rol = st.session_state.rol_usuario
    
    if rol in ["GENESIS", "COORDINADOR_GENERAL", "COORDINADOR_DISTRITO"]:
        if st.button("📊 Tablero de Control", use_container_width=True):
            st.session_state.seccion_activa = "TABLERO"; st.rerun()
            
        if st.button("📅 Agenda Estratégica y Fases", use_container_width=True):
            st.session_state.seccion_activa = "AGENDA"; st.rerun()
            
    if rol in ["GENESIS", "COORDINADOR_GENERAL", "COORDINADOR_DISTRITO", "ANFITRION_CA"]:
        if st.button("👥 Módulo Territorial", use_container_width=True):
            st.session_state.seccion_activa = "TERRITORIAL"; st.rerun()
            
    if rol in ["GENESIS", "COORDINADOR_GENERAL"]:
        if st.button("🎪 Evento Masivo / Cierre", use_container_width=True):
            st.session_state.seccion_activa = "EVENTO"; st.rerun()
            
    if rol in ["GENESIS", "COORDINADOR_GENERAL", "COORDINADOR_DISTRITO", "DEFENSA_VOTO"]:
        if st.button("🚨 Operación Día D (GOTV)", use_container_width=True):
            st.session_state.seccion_activa = "DIA_D"; st.rerun()
            
    if rol in ["GENESIS", "COORDINADOR_GENERAL", "ENCARGADO_REDES"]:
        if st.button("📱 Redes y Difusión", use_container_width=True):
            st.session_state.seccion_activa = "REDES"; st.rerun()

    if rol in ["GENESIS", "COORDINADOR_GENERAL"]:
        if st.button("📱 Simulador Tracking Poll (Móvil)", use_container_width=True):
            st.session_state.seccion_activa = "SIMULADOR"; st.rerun()

    st.markdown("---")
    st.markdown("### 🔗 5 Enlaces Prioritarios (Sincronizados)")
    
    dict_links_maestros = {
        "[1] Plataforma PC (Terceros)": f"{URL_BASE_SISTEMA}/",
        "[2] Captación Voto Aire": f"{URL_BASE_SISTEMA}/?view=simpatizante",
        "[3] Tracking Poll Campo": f"{URL_BASE_SISTEMA}/?view=tracking_poll",
        "[4] Voto Emitido (GOTV)": f"{URL_BASE_SISTEMA}/?view=voto_emitido",
        "[5] Reporte SOS Incidencias": f"{URL_BASE_SISTEMA}/?view=reporte_sos"
    }

    link_seleccionado_key = st.selectbox("Copiar Enlace Oficial:", list(dict_links_maestros.keys()), key="sb_link_sel_m")
    url_url_destino = dict_links_maestros[link_seleccionado_key]
    st.code(url_url_destino, language="text")
    
    contacto_sb_dest = st.selectbox("Enviar a Mando / Anfitrión:", options=opciones_contactos_mando if opciones_contactos_mando else ["Sin contactos"], key="sb_destinatario_mando")
    celular_destino_hub = dict_contactos_mando.get(contacto_sb_dest, "6240000000")
    
    mensaje_hub = f"¡Hola! Te comparto el enlace operativo oficial: {link_seleccionado_key}. Accede aquí: {url_url_destino}"
    link_hub_w = f"https://wa.me/52{celular_destino_hub}?text={urllib.parse.quote(mensaje_hub)}"
    st.markdown(f'<a href="{link_hub_w}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 6px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: bold;">📲 Enviar Link Maestro por WhatsApp</a>', unsafe_allow_html=True)

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
    st.markdown(f"<h1 style='color: {COLOR_PRIMARIO_ENTORNO}; margin-top: 5px; font-size: 1.8rem;'>{ETIQUETA_ENTORNO}</h1>", unsafe_allow_html=True)
with col_logo:
    if "logo_actual" in st.session_state and st.session_state.logo_actual is not None:
        st.image(st.session_state.logo_actual, width=90)
    else:
        st.markdown("<div style='text-align: right; color: #cbd5e1; font-size: 10px; padding-top: 10px;'>[ Sin logotipo cargado ]</div>", unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# VISTA 1: TABLERO CENTRAL PRINCIPAL (REBALANCEADO EXACTO)
# ==========================================
if st.session_state.seccion_activa == "TABLERO":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL", "COORDINADOR_DISTRITO"]:
        st.warning("⚠️ Acceso restringido al Tablero de Control."); st.stop()

    casas_anfitriones = df_padrón[df_padrón['rol'] == 'Anfitrión (CA)'] if not df_padrón.empty else pd.DataFrame()
    total_casas = len(casas_anfitriones)

    col_sel_distrito, col_ano_eleccion = st.columns([3, 1])
    with col_sel_distrito:
        distritos_bcs = [
            "Distrito 16 (Cabo San Lucas - Principal)",
            "Distrito 1 (Los Cabos - Cabecera)", "Distrito 2 (La Paz)", "Distrito 3 (La Paz)", "Distrito 4 (La Paz)",
            "Distrito 5 (La Paz)", "Distrito 6 (La Paz)", "Distrito 7 (San José del Cabo)", "Distrito 8 (Cabo San Lucas)",
            "Distrito 9 (Loreto/Comondú)", "Distrito 10 (Mulegé)", "Distrito 11 (La Paz)", "Distrito 12 (Los Cabos)",
            "Distrito 13 (La Paz)", "Distrito 14 (La Paz)", "Distrito 15 (La Paz)", "TODOS"
        ]
        distrito_seleccionado = st.selectbox("📍 Selector de Distrito Electoral (BCS - Catálogo INE):", options=distritos_bcs, index=0, key="tablero_distrito_sel")
        
        if st.session_state.get("distrito_activo_sel", "") != distrito_seleccionado:
            st.session_state.distrito_activo_sel = distrito_seleccionado
            st.session_state.cat_casillas_ine, st.session_state.conteo_casillas_urbanas, st.session_state.conteo_casillas_rurales = cargar_cartografia_ine_dinamica(distrito_seleccionado)
            st.session_state.modo_calibracion_juridica = "Automático (Lectura de Archivo INE)"
            st.rerun()

    with col_ano_eleccion:
        st.markdown("<div class='stat-box' style='padding: 6px;'><div class='stat-label'>📅 Año Elección</div><div class='stat-num' style='font-size: 18px;'>2027</div></div>", unsafe_allow_html=True)

    with st.expander("⚙️ Configuración Dinámica de Metas Distritales (Seccionales y Células 1x5x5x2)", expanded=False):
        st.markdown("##### Ajuste de Parámetros Operativos del Distrito")
        cf_s1, cf_s2, cf_s3 = st.columns(3)
        with cf_s1: n_secc = st.number_input("Número de Seccionales en el Distrito:", min_value=1, max_value=100, value=st.session_state.num_seccionales, key="input_num_secc")
        with cf_s2: casas_min_sec = st.number_input("Células Mínimas por Seccional (Blindaje Cardenal):", min_value=1, max_value=10, value=st.session_state.casas_por_seccional, key="input_casas_sec")
        with cf_s3: fact_votos = st.number_input("Factor de Votos por Célula (Estructura 1x5x5x2):", min_value=50, max_value=150, value=st.session_state.factor_votos_casa, key="input_fact_votos")

        st.session_state.num_seccionales = n_secc
        st.session_state.casas_por_seccional = casas_min_sec
        st.session_state.factor_votos_casa = fact_votos

        meta_casas_calculada = n_secc * casas_min_sec
        meta_votos_calculada = meta_casas_calculada * fact_votos
        st.info(f"📐 **Cálculo Automático Proyectado:** {n_secc} seccionales × {casas_min_sec} células = **{meta_casas_calculada} Casas Amigas objetivo**. Meta de votos: **{meta_votos_calculada:,} votos**.")

    meta_casas_objetivo = st.session_state.num_seccionales * st.session_state.casas_por_seccional
    factor_meta = st.session_state.factor_votos_casa
    meta_votos_distrito = meta_casas_objetivo * factor_meta

    with st.expander("🛠️ Asistente de Arranque y Configuración de Directorios (Paso a Paso)", expanded=False):
        st.markdown("##### Guía Operativa para la Carga de Estrategia y Cartografía por Distrito")
        st.markdown("""
        * **Paso 1:** Coloca tu archivo de casillas (ej. `casillas electorales.xlsx` o cualquier `.xlsx`, `.csv`) en la carpeta `UBICACION CASILLAS`.
        * **Paso 2:** El sistema lo detectará y leerá automáticamente sin importar el nombre exacto que le pongas.
        * **Paso 3:** Selecciona tu distrito en el menú superior para proyectar las casillas y sincronizar las metas de defensa.
        """)
        col_as1, col_as2, col_as3 = st.columns(3)
        with col_as1:
            if ES_LOCAL and st.button("📂 Abrir Carpeta UBICACION CASILLAS", use_container_width=True, key="btn_asistente_ubicacion_pc_v_rest"):
                abrir_carpeta_pc(r"C:\Users\Usuario\Desktop\Plataforma_Electoral\UBICACION CASILLAS")
        with col_as2:
            if ES_LOCAL and st.button("📂 Abrir Carpeta LOGOS", use_container_width=True, key="btn_asistente_logos_pc_v_rest"):
                abrir_carpeta_pc(r"C:\Users\Usuario\Desktop\Plataforma_Electoral\LOGOS_IDENTIDAD")
        with col_as3: st.success("✅ Directorio Base Activo.")

    hoy = date.today()
    df_fases = st.session_state.df_fases_config
    fase2_row = df_fases[df_fases["Fase / Etapa del Proyecto"].str.startswith("2.")]
    if not fase2_row.empty:
        f_ini_precamp = pd.to_datetime(fase2_row["Fecha Inicio"].values[0]).date()
        f_fin_precamp = pd.to_datetime(fase2_row["Fecha Fin"].values[0]).date()
        txt_reloj_rp = f"Faltan {(f_ini_precamp - hoy).days} Días" if hoy < f_ini_precamp else f"En Curso (Resta {(f_fin_precamp - hoy).days} d)" if f_ini_precamp <= hoy <= f_fin_precamp else "Concluida"
    else: txt_reloj_rp = "Sin fecha"

    fase9_row = df_fases[df_fases["Fase / Etapa del Proyecto"].str.startswith("9.")]
    if not fase9_row.empty:
        f_eleccion = pd.to_datetime(fase9_row["Fecha Inicio"].values[0]).date()
        dias_para_eleccion = (f_eleccion - hoy).days
        txt_reloj_rce = f"Faltan {dias_para_eleccion} Días" if dias_para_eleccion > 0 else "¡Jornada Hoy!"
    else: txt_reloj_rce = "6 de Junio 2027"

    voto_duro_registrados = len(df_padrón[df_padrón['tipo_voto'] == 'Duro']) if not df_padrón.empty else 0
    voto_duro_emitidos = len(df_padrón[(df_padrón['tipo_voto'] == 'Duro') & (df_padrón['voto_emitido'] == True)]) if not df_padrón.empty else 0
    voto_aire_registrados = len(df_padrón[df_padrón['tipo_voto'] == 'Aire']) if not df_padrón.empty else 0
    voto_aire_emitidos = len(df_padrón[(df_padrón['tipo_voto'] == 'Aire') & (df_padrón['voto_emitido'] == True)]) if not df_padrón.empty else 0
    total_votos_computados = voto_duro_emitidos + voto_aire_emitidos
    pct_participacion = round((total_votos_computados / meta_votos_distrito) * 100, 2) if meta_votos_distrito > 0 else 0

    # FILA 1: COLUMNA IZQUIERDA (METAS + VOTOS + RANKING) VS COLUMNA DERECHA (MAPA + DEFENSA)
    col_izq_1, col_der_1 = st.columns(2)
    with col_izq_1:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>⏱️ Relojes Operativos y Metas Distritales</div></div>", unsafe_allow_html=True)
        c_rp, c_rce = st.columns(2)
        with c_rp: st.markdown(f"<div class='stat-box'><div class='stat-label'>RP (Precampaña - Fase 2)</div><div class='stat-num' style='font-size: 15px;'>{txt_reloj_rp}</div></div>", unsafe_allow_html=True)
        with c_rce: st.markdown(f"<div class='stat-box'><div class='stat-label'>RCE (Día D - Fase 9)</div><div class='stat-num' style='font-size: 15px; color:#ef4444;'>{txt_reloj_rce}</div></div>", unsafe_allow_html=True)

        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>🗳️ Monitor Dual de Contabilidad de Votos</div></div>", unsafe_allow_html=True)
        c_mduro, c_maire = st.columns(2)
        with c_mduro:
            st.markdown(f"""
            <div class='stat-box' style='border-left: 4px solid #10b981;'>
                <div class='stat-label'>🏛️ Voto Duro (Estructura 1x5x5x2)</div>
                <div class='stat-num' style='color:#10b981;'>{voto_duro_emitidos} / {voto_duro_registrados}</div>
                <div style='font-size:11px; color:#cbd5e1;'>Emitidos vs Registrados</div>
            </div>
            """, unsafe_allow_html=True)
        with c_maire:
            st.markdown(f"""
            <div class='stat-box' style='border-left: 4px solid #38bdf8;'>
                <div class='stat-label'>🌐 Voto de Aire (Redes / Digital)</div>
                <div class='stat-num' style='color:#38bdf8;'>{voto_aire_emitidos} / {voto_aire_registrados}</div>
                <div style='font-size:11px; color:#cbd5e1;'>Emitidos vs Registros Web</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"**🌡️ Termómetro General de Participación:** `{total_votos_computados}` de `{meta_votos_distrito}` votos meta ({pct_participacion}%)")
        st.progress(min(pct_participacion / 100.0, 1.0))

        vm_1, vm_2 = st.columns(2)
        with vm_1: st.markdown(f"<div class='stat-box'><div class='stat-label'>🏠 Meta Casas (M/CA)</div><div class='stat-num'>{total_casas} / {meta_casas_objetivo}</div><div style='font-size: 10px; color: #38bdf8;'>{round((total_casas/meta_casas_objetivo)*100, 1) if meta_casas_objetivo > 0 else 0}% Células</div></div>", unsafe_allow_html=True)
        with vm_2: st.markdown(f"<div class='stat-box'><div class='stat-label'>🛡️ Blindaje Jurídico Casillas</div><div class='stat-num'>{rc_registrados} / {meta_rc_total}</div><div style='font-size: 10px; color: #10b981;'>RCs Acreditados</div></div>", unsafe_allow_html=True)

        # RANKING AL 100% SUBIDO A LA COLUMNA IZQUIERDA
        st.markdown("<div class='caja-bloque' style='margin-top: 10px;'><div class='titulo-caja'>🏆 Células con Meta 100% Cumplida (Factor 88)</div></div>", unsafe_allow_html=True)
        celulas_cumplidas_dinamicas = []
        if not df_padrón.empty:
            for id_c in df_padrón['id_ca'].unique():
                if id_c != "DEFENSA":
                    miembros_c = df_padrón[df_padrón['id_ca'] == id_c]
                    anf = miembros_c[miembros_c['rol'] == 'Anfitrión (CA)']
                    nom_anf = anf['nombre'].values[0] if not anf.empty else id_c
                    cel_anf = anf['celular'].values[0] if not anf.empty else "6240000000"
                    celulas_cumplidas_dinamicas.append({
                        "id_ca": id_c, "nombre": f"Casa Amiga {id_c}", 
                        "responsable": nom_anf, "tel": cel_anf, "integrantes": len(miembros_c)
                    })
        if celulas_cumplidas_dinamicas:
            for casa in celulas_cumplidas_dinamicas:
                col_c_info, col_c_btn = st.columns([2, 1])
                with col_c_info: st.markdown(f"**{casa['nombre']} - {casa['responsable']}** ({casa['integrantes']}/{factor_meta})")
                with col_c_btn:
                    link_w = f"https://wa.me/52{casa['tel']}?text=Felicidades%20por%20cumplir%20la%20meta."
                    st.markdown(f'<a href="{link_w}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 4px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">📲 Felicitar</a>', unsafe_allow_html=True)
        else:
            st.info("Sin células al 100% registradas aún.")

    with col_der_1:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>🗺️ Visor Cartográfico Dual (Nativo e INE)</div></div>", unsafe_allow_html=True)
        tab_mapa_nativo, tab_mapa_google = st.tabs(["🗺️ Plano Táctico (4 Colores)", "🏛️ Cartografía INE (Google Maps)"])
        with tab_mapa_nativo:
            puntos_plano = []
            if not df_padrón.empty:
                for _, r in df_padrón.iterrows():
                    if r['rol'] == 'Anfitrión (CA)':
                        color_nodo = "#eab308" if "-ESP" in str(r.get('id_ca', '')) else "#ef4444"
                        puntos_plano.append({"lat": float(r.get("lat", 22.8905)), "lon": float(r.get("lon", -109.9167)), "color": color_nodo})
            for c_ine in st.session_state.cat_casillas_ine:
                puntos_plano.append({"lat": float(c_ine["lat"]), "lon": float(c_ine["lon"]), "color": "#10b981"})
            puntos_seccionales = [
                {"lat": 22.8930, "lon": -109.9180, "color": "#3b82f6"},
                {"lat": 22.8970, "lon": -109.9220, "color": "#3b82f6"},
                {"lat": 22.9300, "lon": -109.8700, "color": "#3b82f6"}
            ]
            puntos_plano.extend(puntos_seccionales)
            st.map(pd.DataFrame(puntos_plano), zoom=11, use_container_width=True, color="color", height=320)
            
            # LEYENDA HORIZONTAL RECUPERADA
            st.markdown("""
            <div style='background-color:#0f172a; padding:8px 12px; border-radius:6px; font-size:12px; border:1px solid #1e293b; display:flex; justify-content:space-around; margin-top:6px;'>
                <span>🔴 <b>Casa Amiga</b></span>
                <span>🟡 <b>Casa Espejo</b></span>
                <span>🟢 <b>Casillas INE</b></span>
                <span>🔵 <b>Seccionales</b></span>
            </div>
            """, unsafe_allow_html=True)
            
        with tab_mapa_google:
            components.html('<iframe src="https://www.google.com/maps/d/embed?mid=1Dqm9Q-tm-B9X3YNJzsMLIWYD2fdFxag" width="100%" height="360" style="border:0; border-radius:8px;"></iframe>', height=360)

        # COBERTURA Y ASIGNACIÓN DE DEFENSA EN LA DERECHA (RELLENA EL HUECO NEGRO)
        with st.expander("🛡️ Cobertura y Asignación de Defensa Electoral (Medidor Táctico Oficial)", expanded=True):
            modo_cal = st.radio("Modo de Cálculo del Padrón de Casillas:", ["Automático (Lectura de Archivo INE)", "Manual / Ajuste Fino"], horizontal=True, key="modo_cal_radio_tab_bal")
            if modo_cal == "Manual / Ajuste Fino":
                c_cal_1, c_cal_2 = st.columns(2)
                with c_cal_1: urb_val = st.number_input("Casillas Urbanas (Básicas/Contiguas/Esp):", min_value=0, value=st.session_state.manual_c_urb, key="man_urb_tab_bal")
                with c_cal_2: rur_val = st.number_input("Casillas Rurales / No Urbanas:", min_value=0, value=st.session_state.manual_c_rur, key="man_rur_tab_bal")
                if st.button("💾 Aplicar Calibración Manual", key="btn_guardar_calib_bal"):
                    st.session_state.modo_calibracion_juridica = "Manual / Ajuste Fino"
                    st.session_state.manual_c_urb = urb_val
                    st.session_state.manual_c_rur = rur_val
                    st.rerun()
            else:
                if st.session_state.modo_calibracion_juridica != "Automático (Lectura de Archivo INE)":
                    st.session_state.modo_calibracion_juridica = "Automático (Lectura de Archivo INE)"
                    st.rerun()

            st.markdown(f"##### 📊 Padrón Oficial: **{total_casillas_distrito} Casillas** ({c_urb} Urbanas | {c_rur} Rurales) en **{distrito_seleccionado}**")
            m_c1, m_c2, m_c3 = st.columns(3)
            with m_c1:
                pct_rc = round((rc_registrados / meta_rc_total) * 100, 1) if meta_rc_total > 0 else 0
                st.markdown(f"<div class='stat-box'><div class='stat-label'>🗳️ RC (CASILLA)</div><div class='stat-num' style='font-size:16px;'>{rc_registrados}/{meta_rc_total}</div><div style='font-size:9px;'>{pct_rc}%</div></div>", unsafe_allow_html=True)
            with m_c2:
                pct_rg = round((rg_registrados / meta_rg_total) * 100, 1) if meta_rg_total > 0 else 0
                st.markdown(f"<div class='stat-box'><div class='stat-label'>🛡️ RG (GENERALES)</div><div class='stat-num' style='font-size:16px;'>{rg_registrados}/{meta_rg_total}</div><div style='font-size:9px;'>{pct_rg}%</div></div>", unsafe_allow_html=True)
            with m_c3:
                pct_obs = round((obs_registrados / meta_obs_total) * 100, 1) if meta_obs_total > 0 else 0
                st.markdown(f"<div class='stat-box'><div class='stat-label'>👁️ OBSERVADORES</div><div class='stat-num' style='font-size:16px;'>{obs_registrados}/{meta_obs_total}</div><div style='font-size:9px;'>{pct_obs}%</div></div>", unsafe_allow_html=True)

            st.caption(f"🎯 **Meta Global de Blindaje Jurídico:** {total_defensa_actual} / {meta_defensa_global} acreditados ({round((total_defensa_actual/meta_defensa_global)*100, 1) if meta_defensa_global > 0 else 0}%).")
            
            df_def_registrada = df_padrón[df_padrón['rol'].isin(["RG", "RC", "Observador Electoral"])] if not df_padrón.empty else pd.DataFrame()
            if not df_def_registrada.empty:
                st.dataframe(df_def_registrada[['rol', 'calidad', 'nombre', 'seccion', 'id_casilla', 'celular']], use_container_width=True)
            else:
                st.info("Sin representantes registrados aún.")

    # =========================================================================
    # FILA 2 REESTRUCTURADA: BRIGADISTAS RELLENAN HUECO DEBAJO DEL TRACKING POLL
    # =========================================================================
    col_izq_2, col_der_2 = st.columns(2)
    with col_izq_2:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📈 Tracking Poll (Tendencia Electoral)</div></div>", unsafe_allow_html=True)
        st.line_chart(pd.DataFrame({
            'Mes': ['Oct 2026', 'Nov 2026', 'Dic 2026', 'Ene 2027', 'Feb 2027', 'Mar 2027', 'Abr 2027', 'May 2027', 'Jun 2027'],
            'Conocimiento (%)': [15, 22, 30, 42, 55, 68, 76, 84, 92],
            'Aceptación (%)': [10, 16, 25, 35, 48, 60, 69, 78, 88]
        }).set_index('Mes'), height=130)

        st.markdown("<div class='caja-bloque' style='margin-top: 8px;'><div class='titulo-caja'>📋 Cédulas, Criterios de Campo & Gestión de Brigadistas</div></div>", unsafe_allow_html=True)
        col_acc_b1, col_acc_b2 = st.columns(2)
        with col_acc_b1:
            if st.button("👥 Abrir / Cerrar Panel Brigadistas", use_container_width=True, key="btn_toggle_brig_f2"):
                st.session_state.ver_modal_brigadistas = not st.session_state.ver_modal_brigadistas
        with col_acc_b2:
            if ES_LOCAL and st.button("📂 Abrir Carpeta 'ENCUESTAS' PC", use_container_width=True, key="btn_encuestas_folder_f2"):
                abrir_carpeta_pc(r"C:\Users\Usuario\Desktop\Plataforma_Electoral\ENCUESTAS")

        if st.session_state.ver_modal_brigadistas:
            with st.form("form_alta_brigadista_desplegable_f2"):
                fb1, fb2 = st.columns(2)
                with fb1:
                    nombre_brig = st.text_input("Nombre del Brigadista:", key="brig_nombre_f2")
                    cel_brig = st.text_input("Celular del Brigadista:", key="brig_cel_f2")
                with fb2:
                    secc_asignadas = st.text_input("Seccionales Asignadas:", key="brig_secc_f2")
                    tarea_brig = st.text_input("Tarea:", "Barrido casa por casa.", key="brig_tarea_f2")
                st.form_submit_button("💾 Guardar Brigadista")

    with col_der_2:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>⚖️ Legislación y Asistente Jurídico Gemini</div></div>", unsafe_allow_html=True)
        st.markdown("[🔗 Abrir Cuaderno NotebookLM: Ley Electoral de BCS](https://gemini.google.com/notebook/3ec8d28b-6376-4f20-9b86-d997726b6792)", unsafe_allow_html=True)
        consulta_juridica = st.text_input("💬 Pregúntale a Gemini sobre blindaje electoral BCS:", placeholder="Ej. ¿Plazos para el recurso de inconformidad?", key="input_ia_legal_bal")
        if st.button("🤖 Consultar Criterio Legal", use_container_width=True, key="btn_ia_legal_bal"):
            if consulta_juridica: st.success("⚖️ Criterio Jurídico (BCS): Conforme a la Ley de Medios de Impugnación, el término general es de 4 días.")
        if ES_LOCAL and st.button("📂 Abrir Carpeta 'REPOSITORIO LEGAL' en PC", use_container_width=True, key="btn_rep_legal_bal"):
            abrir_carpeta_pc(r"C:\Users\Usuario\Desktop\Plataforma_Electoral\REPOSITORIO LEGAL")

        st.markdown("<div class='caja-bloque' style='margin-top: 8px;'><div class='titulo-caja'>📍 Directorio y Ubicación de Casillas</div></div>", unsafe_allow_html=True)
        col_c_ant1, col_c_ant2 = st.columns(2)
        with col_c_ant1:
            if st.button("📋 Ver Antecedentes Encuestas", use_container_width=True, key="btn_antecedentes_bal"):
                st.session_state.ver_antecedentes_encuesta = not st.session_state.ver_antecedentes_encuesta
        with col_c_ant2:
            if ES_LOCAL and st.button("📂 Abrir UBICACION CASILLAS PC", use_container_width=True, key="btn_ubicacion_casillas_pc_bal"):
                abrir_carpeta_pc(r"C:\Users\Usuario\Desktop\Plataforma_Electoral\UBICACION CASILLAS")

    if st.session_state.ver_antecedentes_encuesta:
        data_encuestas = [
            {"Folio": "ENC-001", "Fecha": "2026-10-15", "Seccional": "400", "Colonia": "Cangrejos", "Encuestador": "Carlos Mendoza", "Ciudadanos": 18, "Estatus": "Validado"},
            {"Folio": "ENC-002", "Fecha": "2026-10-20", "Seccional": "401", "Colonia": "Las Palmas", "Encuestador": "Ana Luisa P.", "Ciudadanos": 24, "Estatus": "Validado"}
        ]
        st.dataframe(pd.DataFrame(data_encuestas), use_container_width=True)

    # FILA 3: DIFUSIÓN MASIVA Y DIRECTORIO DE MANDO
    st.markdown("<div class='caja-bloque' style='margin-top: 12px;'><div class='titulo-caja'>📱 Centro de Difusión Masiva y Directorio de Mando Estratégico</div></div>", unsafe_allow_html=True)
    msg_c1, msg_c2 = st.columns(2)
    with msg_c1:
        if st.button("📲 Abrir Panel Cascadas y Difusión", use_container_width=True, key="btn_cascadas_bal"):
            st.session_state.ver_modal_cascada = not st.session_state.ver_modal_cascada
    with msg_c2:
        if st.button("📲 Abrir Mando / Directorio Estratégico", use_container_width=True, key="btn_mando_bal"):
            st.session_state.ver_modal_coordinacion = not st.session_state.ver_modal_coordinacion

    if st.session_state.ver_modal_cascada:
        mensaje_masivo = st.text_area("Redactar Comunicado Oficial de Campaña:", "¡Atención equipo! Compartimos el material de hoy.", key="text_msg_masivo_bal")
        st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(mensaje_masivo)}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 8px; border-radius: 6px; text-decoration: none; font-weight: bold;">🚀 Disparar Difusión por WhatsApp</a>', unsafe_allow_html=True)

    if st.session_state.ver_modal_coordinacion:
        st.session_state.directorio_mando_estrategico = st.data_editor(st.session_state.directorio_mando_estrategico, num_rows="dynamic", use_container_width=True, key="editor_tabla_mando_estrategico_bal")

    # FILA 4: ACCESOS A MÓDULOS INFERIORES
    st.markdown("<div class='caja-bloque' style='margin-top: 12px;'><div class='titulo-caja'>🎛️ Módulos de Operación Táctica e Inferiores</div></div>", unsafe_allow_html=True)
    op_1, op_2, op_3, op_4 = st.columns(4)
    with op_1:
        if st.button("👥 Abrir Módulo Territorial (CA)", use_container_width=True, key="btn_mod_terr_bal"):
            st.session_state.seccion_activa = "TERRITORIAL"; st.rerun()
    with op_2:
        if st.button("🎪 Abrir Control de Evento Masivo", use_container_width=True, key="btn_mod_evento_bal"):
            st.session_state.seccion_activa = "EVENTO"; st.rerun()
    with op_3:
        if st.button("🚨 Abrir Módulo Día D", use_container_width=True, key="btn_mod_diad_bal"):
            st.session_state.seccion_activa = "DIA_D"; st.rerun()
    with op_4:
        if st.button("📅 Abrir Módulo de Agenda", use_container_width=True, key="btn_mod_agenda_bal"):
            st.session_state.seccion_activa = "AGENDA"; st.rerun()

# =========================================================================
# VISTA 2: MÓDULO ESCÁNER OCR AISLADO
# =========================================================================
elif st.session_state.seccion_activa == "ESCANER_OCR":
    st.markdown("## 📸 Módulo Escáner Aislado de Credencial INE")
    if st.button("⬅️ Volver al Registro Territorial", use_container_width=False, key="btn_vol_escanner"):
        st.session_state.seccion_activa = "TERRITORIAL"; st.rerun()

    metodo_captura = st.radio("Seleccione el método de captura:", ["Cámara Directa", "Subir Archivo de Imagen"], horizontal=True, key="metodo_escanner_aislado")
    foto_ine_input = st.camera_input("Tome la fotografía frontal de la credencial INE", key="camara_aislada_ine") if metodo_captura == "Cámara Directa" else st.file_uploader("Cargar imagen frontal de la credencial INE", type=["png", "jpg", "jpeg"], key="archivo_aislado_ine")

    if foto_ine_input is not None:
        try:
            base_dir = r"C:\Users\Usuario\Desktop\Plataforma_Electoral\FOTOS INE" if ES_LOCAL else "/tmp/Plataforma_Electoral/FOTOS_INE"
            os.makedirs(base_dir, exist_ok=True)
            ruta_imagen_guardada = os.path.join(base_dir, "Ciudadano_Captura_INE.jpg")
            img_original = Image.open(foto_ine_input)
            img_original.save(ruta_imagen_guardada)
            
            nombre_extraido, seccion_extraida, domicilio_extraido = "", "", ""
            if OCR_DISPONIBLE:
                texto_extraido = pytesseract.image_to_string(img_original)
                lineas = [l.strip() for l in texto_extraido.split('\n') if l.strip()]
                for idx, l in enumerate(lineas):
                    m_sec = re.search(r'(?:SECCIÓN|SECCION|SECC)\s*[:\-]?\s*(\d{4})', l.upper())
                    if m_sec: seccion_extraida = m_sec.group(1); break
                for idx, l in enumerate(lineas):
                    if "NOMBRE" in l.upper() and idx + 1 < len(lineas):
                        nombre_extraido = lineas[idx + 1]
                    if "DOMICILIO" in l.upper() and idx + 1 < len(lineas):
                        domicilio_extraido = lineas[idx + 1]

            st.session_state.ocr_nombre_capturado = nombre_extraido
            st.session_state.ocr_seccion_capturada = seccion_extraida
            st.session_state.ocr_domicilio_capturado = domicilio_extraido
            st.session_state.ocr_imagen_path = ruta_imagen_guardada
            st.success("✅ ¡Credencial capturada con éxito! Redirigiendo...")
            st.session_state.seccion_activa = "TERRITORIAL"; st.rerun()
        except Exception as e:
            st.error(f"Error en escáner: {e}")

# =========================================================================
# VISTA 3: MÓDULO TERRITORIAL (1x5x5x2 + 7 MÓDULOS DE REGISTRO)
# =========================================================================
elif st.session_state.seccion_activa == "TERRITORIAL":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL", "COORDINADOR_DISTRITO", "ANFITRION_CA"]:
        st.warning("⚠️ Acceso restringido a la estructura territorial."); st.stop()

    st.markdown("## 👥 Módulo de Estructura Territorial (Casas Amigas 1x5x5x2)")
    if st.button("⬅️ Volver al Tablero / Menú", use_container_width=False, key="btn_vol_tab_terr"):
        st.session_state.seccion_activa = "TABLERO"; st.rerun()

    tab_m1, tab_m2, tab_m3, tab_m4 = st.tabs([
        "🌳 Árbol de Casas Amigas (1x5x5x2)", 
        "🤝 Simpatizantes Comunes y Redes", 
        "🪞 Casas Amigas Espejo", 
        "🛡️ Defensa del Voto (RGs/RCs)"
    ])

    with tab_m1:
        st.markdown("##### 🌳 Estructura Orgánica de Células")
        if not df_padrón.empty:
            casas = df_padrón[(df_padrón['rol'] == 'Anfitrión (CA)') & (~df_padrón['id_ca'].astype(str).str.contains("-ESP"))]
            for _, ca in casas.iterrows():
                link_mapa_gps = f"https://maps.google.com/?q={ca['lat']},{ca['lon']}"
                msg_ubicacion_wa = urllib.parse.quote(f"📍 Ubicación de Casa Amiga {ca['id_ca']} ({ca['nombre']}):\nDomicilio: {ca['domicilio']}\nGPS: {link_mapa_gps}")
                link_enviar_ub_wa = f"https://wa.me/?text={msg_ubicacion_wa}"
                
                with st.expander(f"🏠 {ca['id_ca']} - {ca['nombre']} (Sección: {ca['seccion']})", expanded=False):
                    st.markdown(f"**Domicilio:** {ca['domicilio']} | **Celular:** {ca['celular']} | **GPS:** {ca['lat']}, {ca['lon']}")
                    c_act1, c_act2, c_act3, c_act4 = st.columns(4)
                    with c_act1: st.link_button("📞 Llamar", f"tel:{ca['celular']}", use_container_width=True)
                    with c_act2: st.link_button("💬 WhatsApp", f"https://wa.me/52{ca['celular']}", use_container_width=True)
                    with c_act3: st.link_button("🗺️ Abrir GPS", link_mapa_gps, use_container_width=True)
                    with c_act4: st.link_button("📍 Enviar Ubicación", link_enviar_ub_wa, use_container_width=True)

                    st.markdown("---")
                    st.markdown("###### 👥 2 Simpatizantes Directos del Anfitrión:")
                    simps_ca = df_padrón[(df_padrón['id_ca'] == ca['id_ca']) & (df_padrón['rol'] == 'Simpatizante') & (df_padrón['referencia'] == 'CA')]
                    if not simps_ca.empty:
                        for _, sca in simps_ca.iterrows():
                            col_s1, col_s2, col_s3 = st.columns([3, 1, 1])
                            with col_s1: st.write(f"👤 **{sca['nombre']}** ({sca['celular']})")
                            with col_s2: st.link_button("📞 Llamar", f"tel:{sca['celular']}", key=f"call_{sca['id_reg']}")
                            with col_s3: st.link_button("💬 WhatsApp", f"https://wa.me/52{sca['celular']}", key=f"wa_{sca['id_reg']}")
                    else: st.caption("Sin simpatizantes directos asignados.")

                    st.markdown("---")
                    st.markdown("###### 👥 Coanfitriones de Célula (C1 a C5):")
                    tabs_coanf = st.tabs(["Coanfitrión C1", "Coanfitrión C2", "Coanfitrión C3", "Coanfitrión C4", "Coanfitrión C5"])
                    for idx_c, tab_c in enumerate(tabs_coanf, start=1):
                        with tab_c:
                            ref_c_slug = f"C{idx_c}"
                            coanf_row = df_padrón[(df_padrón['id_ca'] == ca['id_ca']) & (df_padrón['rol'] == 'Coanfitrión') & (df_padrón['referencia'] == ref_c_slug)]
                            if not coanf_row.empty:
                                cx = coanf_row.iloc[0]
                                st.write(f"**Coanfitrión {ref_c_slug}:** {cx['nombre']} | **Celular:** {cx['celular']}")
                                c_cx1, c_cx2 = st.columns(2)
                                with c_cx1: st.link_button("📞 Llamar Coanfitrión", f"tel:{cx['celular']}", key=f"c_call_{cx['id_reg']}")
                                with c_cx2: st.link_button("💬 WhatsApp Coanfitrión", f"https://wa.me/52{cx['celular']}", key=f"c_wa_{cx['id_reg']}")

                                st.markdown(f"**👥 Simpatizantes Directos de {ref_c_slug}:**")
                                simps_cx = df_padrón[(df_padrón['id_ca'] == ca['id_ca']) & (df_padrón['rol'] == 'Simpatizante') & (df_padrón['referencia'] == ref_c_slug)]
                                if not simps_cx.empty:
                                    for _, scx in simps_cx.iterrows():
                                        col_sc1, col_sc2, col_sc3 = st.columns([3, 1, 1])
                                        with col_sc1: st.write(f"👤 {scx['nombre']} ({scx['celular']})")
                                        with col_sc2: st.link_button("📞 Llamar", f"tel:{scx['celular']}", key=f"call_{scx['id_reg']}")
                                        with col_sc3: st.link_button("💬 WhatsApp", f"https://wa.me/52{scx['celular']}", key=f"wa_{scx['id_reg']}")

                                st.markdown(f"**📌 Promotores de {ref_c_slug}:**")
                                proms_cx = df_padrón[(df_padrón['id_ca'] == ca['id_ca']) & (df_padrón['rol'] == 'Promotor / Enlace') & (df_padrón['referencia'] == ref_c_slug)]
                                if not proms_cx.empty:
                                    for _, pr in proms_cx.iterrows():
                                        st.write(f"🎯 **Promotor:** {pr['nombre']} ({pr['celular']})")
                                        simps_pr = df_padrón[(df_padrón['id_ca'] == ca['id_ca']) & (df_padrón['rol'] == 'Simpatizante') & (df_padrón['referencia'] == f"Promotor {ref_c_slug}")]
                                        if not simps_pr.empty:
                                            for _, spr in simps_pr.iterrows():
                                                st.caption(f"↳ 👤 Simpatizante de Promotor: {spr['nombre']} ({spr['celular']})")
                            else: st.info(f"Sin Coanfitrión {ref_c_slug} registrado.")
        else: st.info("No hay Casas Amigas registradas.")

    with tab_m2:
        st.markdown("##### 🤝 Padrón Abierto: Simpatizantes Comunes (Voto de Aire)")
        simps_aire = df_padrón[df_padrón['rol'] == 'Simpatizante Común']
        if not simps_aire.empty:
            for _, sa in simps_aire.iterrows():
                col_sa1, col_sa2, col_sa3 = st.columns([3, 1, 1])
                with col_sa1: st.write(f"🌐 **{sa['nombre']}** (Sec: {sa['seccion']})")
                with col_sa2: st.link_button("📞 Llamar", f"tel:{sa['celular']}", key=f"sa_call_{sa['id_reg']}")
                with col_sa3: st.link_button("💬 WhatsApp", f"https://wa.me/52{sa['celular']}", key=f"sa_wa_{sa['id_reg']}")
        else: st.info("Sin registros de voto de aire.")

    with tab_m3:
        st.markdown("##### 🪞 Casas Amigas Espejo (Sedes Satélites)")
        espejos = df_padrón[df_padrón['id_ca'].astype(str).str.contains("-ESP")]
        if not espejos.empty:
            for _, esp in espejos.iterrows():
                st.write(f"🪞 **{esp['id_ca']}** | Anfitrión: {esp['nombre']} | Cel: {esp['celular']}")
                st.link_button("🗺️ Abrir GPS Espejo", f"https://maps.google.com/?q={esp['lat']},{esp['lon']}")
        else: st.info("Sin casas espejo registradas.")

    with tab_m4:
        st.markdown("##### 🛡️ Defensa del Voto Registrada")
        defensa = df_padrón[df_padrón['rol'].isin(["RG", "RC", "Observador Electoral"])]
        if not defensa.empty:
            st.dataframe(defensa[['rol', 'calidad', 'nombre', 'seccion', 'id_casilla', 'celular', 'referencia']], use_container_width=True)
        else: st.info("Sin representantes registrados.")

    st.markdown("---")
    st.markdown("### 📝 Centro de Captura y Altas Territoriales (7 Módulos)")
    lista_casas_disponibles = obtener_lista_casas_amigas()
    lista_casas_todas = obtener_lista_casas_todas()
    lista_opciones_casillas = ["[Pendiente / Asignación por Proximidad]"] + [f"{c['id_casilla']} ({c['seccion']} - {c['tipo_casilla']} - {c['zona']})" for c in st.session_state.cat_casillas_ine]

    with st.expander("🏠 1. Registro del Anfitrión Principal (Casa Amiga)", expanded=False):
        if st.button("📸 Abrir Escáner de Credencial INE (Anfitrión)", use_container_width=True, key="btn_esc_ca"):
            st.session_state.seccion_activa = "ESCANER_OCR"; st.rerun()
        folio_auto_ca = f"CA-{st.session_state.contador_casas_amigas:02d}"
        nombre_ca = st.text_input("Nombre Completo (CA):", value=st.session_state.ocr_nombre_capturado, key="nom_ca_in")
        seccional_ca = st.text_input("Seccional Electoral:", value=st.session_state.ocr_seccion_capturada, key="sec_ca_in")
        celular_ca = st.text_input("Teléfono Celular (Obligatorio):", key="cel_ca_in")
        direccion_ca = st.text_input("Domicilio / Dirección:", value=st.session_state.ocr_domicilio_capturado, key="dir_ca_in")
        lat_in = st.number_input("Latitud GPS:", value=float(st.session_state.gps_lat_temp), format="%.6f", key="lat_ca_in")
        lon_in = st.number_input("Longitud GPS:", value=float(st.session_state.gps_lon_temp), format="%.6f", key="lon_ca_in")
        if st.button("💾 Guardar Anfitrión Principal", key="btn_save_ca_reg"):
            if nombre_ca and celular_ca:
                guardar_registro_dual(folio_auto_ca, "Anfitrión (CA)", nombre_ca, seccional_ca, direccion_ca, celular_ca, lat=lat_in, lon=lon_in)
                st.session_state.contador_casas_amigas += 1
                limpiar_buffer_registro(); st.rerun()
            else: st.warning("Complete nombre y celular.")

    with st.expander("👥 2. Registro de Coanfitriones de Apoyo (C1 a C5)", expanded=False):
        tabs_c_reg = st.tabs(["C1", "C2", "C3", "C4", "C5"])
        for idx, tab in enumerate(tabs_c_reg, start=1):
            with tab:
                id_p_c = st.selectbox(f"Casa Amiga Padre (C{idx}):", options=lista_casas_disponibles, key=f"ca_p_c{idx}")
                nom_c = st.text_input(f"Nombre Coanfitrión C{idx}:", key=f"nom_c{idx}")
                sec_c = st.text_input(f"Seccional C{idx}:", key=f"sec_c{idx}")
                cel_c = st.text_input(f"Celular C{idx}:", key=f"cel_c{idx}")
                if st.button(f"💾 Guardar C{idx}", key=f"save_c{idx}_btn"):
                    if nom_c and cel_c:
                        guardar_registro_dual(id_p_c.split(' ')[0], "Coanfitrión", nom_c, sec_c, "", cel_c, referencia=f"C{idx}")
                        st.rerun()

    with st.expander("📌 3. Registro de Promotores / Enlaces de Célula", expanded=False):
        id_ca_p = st.selectbox("Casa Amiga Destino:", options=lista_casas_disponibles, key="prom_ca_sel")
        ref_coanf = st.selectbox("Coanfitrión Responsable:", ["C1", "C2", "C3", "C4", "C5"], key="prom_ref_coanf")
        nom_p = st.text_input("Nombre del Promotor:", key="prom_nom_in")
        cel_p = st.text_input("Celular del Promotor:", key="prom_cel_in")
        if st.button("💾 Guardar Promotor", key="save_prom_btn"):
            if nom_p and cel_p:
                guardar_registro_dual(id_ca_p.split(' ')[0], "Promotor / Enlace", nom_p, "", "", cel_p, referencia=ref_coanf)
                st.rerun()

    with st.expander("📋 4. Registro de Simpatizantes de Estructura", expanded=False):
        id_ca_s = st.selectbox("Seleccionar Casa Amiga (Simpatizante):", options=lista_casas_disponibles, key="simp_ca_sel")
        resp_adsc = st.selectbox("Asignar a:", ["Anfitrión (CA)", "C1", "C2", "C3", "C4", "C5", "Promotor C1", "Promotor C2", "Promotor C3", "Promotor C4", "Promotor C5"], key="simp_adsc_sel")
        nom_s = st.text_input("Nombre del Simpatizante:", key="simp_nom_in")
        cel_s = st.text_input("Celular:", key="simp_cel_in")
        if st.button("💾 Guardar Simpatizante Estructura", key="save_simp_btn"):
            if nom_s and cel_s:
                slug = "CA" if "Anfitrión" in resp_adsc else resp_adsc
                guardar_registro_dual(id_ca_s.split(' ')[0], "Simpatizante", nom_s, "", "", cel_s, referencia=slug)
                st.rerun()

    with st.expander("🛡️ 5. Registro de RGs, RCs y Observadores", expanded=False):
        nom_def = st.text_input("Nombre Representante:", key="def_nom_in")
        rol_def = st.selectbox("Rol:", ["RC", "RG", "Observador Electoral"], key="def_rol_in")
        cas_def = st.selectbox("Casilla Asignada:", options=lista_opciones_casillas, key="def_cas_in")
        cel_def = st.text_input("Celular Contacto:", key="def_cel_in")
        if st.button("💾 Guardar Representante", key="save_def_btn"):
            if nom_def and cel_def:
                id_c = "PENDIENTE" if "Pendiente" in cas_def else cas_def.split(' ')[0]
                guardar_registro_dual("DEFENSA", rol_def, nom_def, "", "", cel_def, id_casilla=id_c)
                st.rerun()

    with st.expander("🤝 6. Registro de Simpatizantes Comunes (Voto de Aire)", expanded=False):
        nom_scom = st.text_input("Nombre Ciudadano:", key="scom_nom_in")
        ca_scom = st.selectbox("Casa Amiga Vinculada:", options=lista_casas_disponibles, key="scom_ca_in")
        cel_scom = st.text_input("Celular Ciudadano:", key="scom_cel_in")
        if st.button("💾 Guardar Simpatizante Común", key="save_scom_btn"):
            if nom_scom and cel_scom:
                guardar_registro_dual(ca_scom.split(' ')[0], "Simpatizante Común", nom_scom, "", "", cel_scom, tipo_voto="Aire")
                st.rerun()

    with st.expander("🪞 7. Registro de Casa Amiga Espejo", expanded=False):
        nuevo_id_esp = f"CA-{st.session_state.contador_casas_amigas:02d}-ESP"
        nom_esp = st.text_input("Nombre Anfitrión Espejo:", key="nom_esp_in")
        ca_orig = st.selectbox("Casa Padre:", options=lista_casas_todas, key="orig_esp_in")
        cel_esp = st.text_input("Celular:", key="cel_esp_in")
        if st.button("💾 Guardar Casa Espejo", key="save_esp_btn"):
            if nom_esp and cel_esp:
                guardar_registro_dual(nuevo_id_esp, "Anfitrión (CA)", nom_esp, "", "", cel_esp, referencia=ca_orig.split(' ')[0])
                st.session_state.contador_casas_amigas += 1
                st.rerun()

# =========================================================================
# VISTA 4: OPERACIÓN DÍA D (GOTV, CONTROL DE OMISOS Y PÁNICO 911)
# =========================================================================
elif st.session_state.seccion_activa == "DIA_D":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL", "COORDINADOR_DISTRITO", "DEFENSA_VOTO"]:
        st.warning("⚠️ Acceso restringido al centro de control del Día D."); st.stop()

    st.markdown("## 🚨 Operación Día D: Monitoreo en Vivo, GOTV y Pánico 911")
    if st.button("⬅️ Volver al Tablero / Menú"):
        st.session_state.seccion_activa = "TABLERO"; st.rerun()

    tab_dd1, tab_dd2, tab_dd3, tab_dd4, tab_dd5 = st.tabs([
        "🏛️ Monitoreo de Casillas (Semáforo)", 
        "🛡️ Directorio de Defensa (RGs/RCs)", 
        "🗳️ Control de Omisos (GOTV)", 
        "🚨 Botón de Pánico 911 & Teleprompter", 
        "💬 Comunicación Táctica"
    ])

    with tab_dd1:
        st.markdown(f"##### 🏛️ Padrón Oficial: {total_casillas_distrito} Casillas ({c_urb} Urbanas / {c_rur} Rurales) en {st.session_state.distrito_activo_sel}")
        lista_monitoreo_casillas = []
        for c_row in st.session_state.cat_casillas_ine:
            id_c = c_row["id_casilla"]
            rcs_casilla = df_padrón[(df_padrón['rol'] == 'RC') & (df_padrón['id_casilla'] == id_c)]
            tiene_prop = not rcs_casilla[rcs_casilla['calidad'] == 'Propietario'].empty
            tiene_supl = not rcs_casilla[rcs_casilla['calidad'] == 'Suplente'].empty
            estado_blindaje = "🟢 Blindada" if tiene_prop and tiene_supl else "🟡 Parcial" if tiene_prop or tiene_supl else "🔴 Descubierta"
            lista_monitoreo_casillas.append({
                "Casilla": id_c, "Sección": c_row["seccion"], "Tipo/Zona": f"{c_row['tipo_casilla']} ({c_row['zona']})",
                "Blindaje": estado_blindaje, "Ubicación": c_row["ubicacion"]
            })
        st.dataframe(pd.DataFrame(lista_monitoreo_casillas), use_container_width=True)

    with tab_dd2:
        st.markdown("##### 👥 Directorio de Contacto de Representantes")
        df_def_dir = df_padrón[df_padrón['rol'].isin(["RG", "RC", "Observador Electoral"])]
        if not df_def_dir.empty:
            for _, def_row in df_def_dir.iterrows():
                cols_d = st.columns([3, 2, 2, 2])
                with cols_d[0]: st.write(f"**{def_row['nombre']}** ({def_row['rol']} - {def_row.get('calidad', 'Titular')})")
                with cols_d[1]: st.write(f"Cel: {def_row['celular']}")
                with cols_d[2]: st.link_button("📞 Llamar", f"tel:{def_row['celular']}", key=f"d_call_{def_row['id_reg']}")
                with cols_d[3]: st.link_button("💬 WhatsApp", f"https://wa.me/52{def_row['celular']}", key=f"d_wa_{def_row['id_reg']}")
        else: st.info("Sin registros de defensa.")

    with tab_dd3:
        st.markdown("##### 🗳️ Control Semafórico de Omisos (Padrón en Vivo)")
        filtro_estatus = st.radio("Filtrar Padrón por Estatus:", ["Todos", "🔴 Pendientes de Votar (Omisos)", "🟢 Voto Emitido"], horizontal=True)
        
        df_gotv = pd.DataFrame(st.session_state.registro_territorial_global)
        if filtro_estatus == "🔴 Pendientes de Votar (Omisos)": df_gotv = df_gotv[df_gotv['voto_emitido'] == False]
        elif filtro_estatus == "🟢 Voto Emitido": df_gotv = df_gotv[df_gotv['voto_emitido'] == True]

        for idx, row in df_gotv.iterrows():
            color_borde = "#ef4444" if not row['voto_emitido'] else "#10b981"
            txt_estatus = "🔴 PENDIENTE" if not row['voto_emitido'] else f"🟢 VOTÓ ({row['hora_voto']})"
            
            c_g1, c_g2, c_g3, c_g4, c_g5 = st.columns([3, 2, 1.5, 1, 1])
            with c_g1: st.markdown(f"**{row['nombre']}** ({row['rol']})<br><span style='font-size:11px;'>Secc: {row['seccion']} | {row['id_ca']} ({row['tipo_voto']})</span>", unsafe_allow_html=True)
            with c_g2: st.markdown(f"<span style='color:{color_borde}; font-weight:bold;'>{txt_estatus}</span>", unsafe_allow_html=True)
            with c_g3:
                if not row['voto_emitido']:
                    if st.button("✅ Marcar Voto", key=f"btn_voto_{row['id_reg']}"):
                        for r_item in st.session_state.registro_territorial_global:
                            if r_item['id_reg'] == row['id_reg']:
                                r_item['voto_emitido'] = True
                                r_item['hora_voto'] = datetime.now().strftime("%H:%M")
                        st.rerun()
                else: st.caption("Confirmado")
            with c_g4: st.link_button("📞 Llamar", f"tel:{row['celular']}", key=f"g_call_{row['id_reg']}")
            with c_g5:
                msg_movil = urllib.parse.quote(f"Estimado(a) {row['nombre']}, te recordamos nuestro compromiso cívico de hoy. Las casillas cierran a las 18:00 hrs. ¡Tu participación es clave!")
                st.link_button("💬 Recordar", f"https://wa.me/52{row['celular']}?text={msg_movil}", key=f"g_wa_{row['id_reg']}")
            st.markdown("---")

    with tab_dd4:
        st.markdown("##### 🚨 Botón de Pánico 911 con Teleprompter Guiado y Alta Automática")
        lista_casillas_nombres = [f"{c['id_casilla']} - {c['ubicacion']}" for c in st.session_state.cat_casillas_ine]
        casilla_conflicto = st.selectbox("Seleccionar Casilla con Incidente Grave:", lista_casillas_nombres)
        c_obj = [c for c in st.session_state.cat_casillas_ine if c['id_casilla'] == casilla_conflicto.split(' ')[0]][0]

        if st.button("🚨 LLAMAR AL 911 Y ACTIVAR TELEPROMPTER", use_container_width=True):
            st.session_state.mostrar_teleprompter_activo = True
            st.session_state.teleprompter_datos = c_obj
            nuevo_folio_inc = f"INC-PANICO-{c_obj['seccion']}-{datetime.now().strftime('%H%M')}"
            st.session_state.repositorio_incidencias_legal.append({
                "Folio": nuevo_folio_inc, "Hora": datetime.now().strftime("%H:%M hrs"), "Casilla": c_obj['id_casilla'],
                "Sección": c_obj['seccion'], "Tipo Incidencia": "Violencia / Coacción (Detonación 911)",
                "Reportante": "Mando Operativo", "Estatus": "🔴 Urgente / En Proceso"
            })

        if st.session_state.mostrar_teleprompter_activo:
            c_pan = st.session_state.teleprompter_datos
            st.markdown(f"""
            <div class='teleprompter-box'>
                <h3 style='color:#ef4444; margin-top:0;'>📢 TELEPROMPTER PARA LECTURA AL OPERADOR DEL 911:</h3>
                <p style='font-size:18px; line-height:1.5; color:#ffffff;'>
                    "Estoy reportando un incidente grave de violencia y coacción electoral. Me encuentro en la casilla instalada en 
                    <b style='color:#facc15;'>{c_pan['ubicacion']}</b>, en la colonia <b style='color:#facc15;'>{c_pan.get('colonia', 'Centro')}</b>, 
                    delegación <b style='color:#facc15;'>Cabo San Lucas</b>. Requerimos auxilio y presencia inmediata de la fuerza pública."
                </p>
                <a href="tel:911" style="display:block; text-align:center; background-color:#dc2626; color:white; font-size:18px; font-weight:bold; padding:10px; border-radius:6px; text-decoration:none;">📞 CONECTAR LLAMADA AL 911 AHORA</a>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("##### 📋 Reservorio Legal de Incidencias Registradas")
        st.dataframe(pd.DataFrame(st.session_state.repositorio_incidencias_legal), use_container_width=True)

    with tab_dd5:
        st.markdown("##### 💬 Comunicación Operativa Día D")
        contacto_dd_dest = st.selectbox("Destinatario de Mando:", options=opciones_contactos_mando if opciones_contactos_mando else ["Sin contactos"], key="sb_dest_dd")
        cel_omiso = dict_contactos_mando.get(contacto_dd_dest, "6240000000")
        link_com_w = f"https://wa.me/52{cel_omiso}?text=Aviso..." if cel_omiso else "#"
        st.markdown(f'<a href="{link_com_w}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 8px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 10px;">📲 Enviar Mensaje Operativo por WhatsApp</a>', unsafe_allow_html=True)

# =========================================================================
# VISTA 5: AGENDA ESTRATÉGICA Y FASES OFICIALES (4 VISTAS Y EXHAUSTIVA)
# =========================================================================
elif st.session_state.seccion_activa == "AGENDA":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL", "COORDINADOR_DISTRITO"]:
        st.warning("⚠️ Acceso restringido al control de la Agenda Estratégica."); st.stop()

    st.markdown("## 📅 Centro de Mando: Agenda Estratégica y Fases Oficiales")
    if st.button("⬅️ Volver al Tablero / Menú"):
        st.session_state.seccion_activa = "TABLERO"; st.rerun()

    with st.expander("📅 Panel Único de Control, Fases Maestras y 4 Vistas Tácticas", expanded=True):
        col_k1, col_k2 = st.columns(2)
        with col_k1:
            f_ini_proc = st.date_input("🏁 Inicio del Proceso Electoral:", value=st.session_state.fecha_inicio_proceso_sel, key="in_proc_final_f")
            st.session_state.fecha_inicio_proceso_sel = f_ini_proc
            st.markdown(f"<div style='background-color: #0f172a; padding: 6px; border-radius: 6px; border: 1px solid #3b82f6; text-align: center; color: #38bdf8; font-weight: bold; font-size: 13px;'>📅 {formatear_fecha_espanol(f_ini_proc)}</div>", unsafe_allow_html=True)
            
        with col_k2:
            f_elec = st.date_input("🎯 Día de la Votación (Día D):", value=st.session_state.fecha_eleccion_sel, key="in_elec_final_f")
            st.session_state.fecha_eleccion_sel = f_elec
            st.markdown(f"<div style='background-color: #0f172a; padding: 6px; border-radius: 6px; border: 1px solid #dc2626; text-align: center; color: #dc2626; font-weight: bold; font-size: 13px;'>🎯 {formatear_fecha_espanol(f_elec)}</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### ⚙️ Definición de Fases Oficiales (Fuente de Verdad)")
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
            key="editor_fases_final_f"
        )

        if st.button("💾 Guardar y Actualizar Fases Maestras", key="btn_save_fases_f"):
            st.session_state.df_fases_config = df_fases_editado
            st.success("✅ ¡Fases maestras guardadas y sincronizadas!")
            st.rerun()

        st.markdown("---")
        st.markdown("#### ➕ Registrar Actividad o Recorrido Diario (Intervalos de 30 Minutos)")
        with st.form("form_actividad_final_f"):
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1: f_act = st.date_input("Fecha de la Actividad:", value=date.today(), key="ag_fec_f")
            with c_f2: h_ini = st.selectbox("Hora de Inicio:", HORARIOS_30_MIN, index=14, key="ag_hini_f")
            with c_f3: h_fin = st.selectbox("Hora de Fin:", HORARIOS_30_MIN, index=18, key="ag_hfin_f")

            c_d1, c_d2 = st.columns([2, 1])
            with c_d1: detalle_d = st.text_input("Detalle de la Actividad:", "Recorrido territorial C1", key="ag_det_f")
            with c_d2: fase_asoc_d = st.selectbox("Asociar a Fase Oficial:", FASES_ELECTORALES_OFICIALES, key="ag_fase_f")

            if st.form_submit_button("💾 Guardar Actividad en Agenda"):
                nueva_act = pd.DataFrame([{
                    "Fecha": f_act, "Hora Inicio": h_ini, "Hora Fin": h_fin,
                    "Actividad / Detalle Diario": detalle_d, "Tipo / Origen": "Operativo Diario", "Fase Asociada": fase_asoc_d
                }])
                st.session_state.df_agenda_matriz = pd.concat([st.session_state.df_agenda_matriz, nueva_act], ignore_index=True)
                st.success("✅ Actividad guardada con éxito."); st.rerun()

        st.markdown("---")

        filas_hitos = []
        for _, r_fase in st.session_state.df_fases_config.iterrows():
            f_ini = pd.to_datetime(r_fase["Fecha Inicio"]).date()
            f_fin = pd.to_datetime(r_fase["Fecha Fin"]).date()
            nombre_fase = r_fase["Fase / Etapa del Proyecto"]
            filas_hitos.append({
                "Fecha": f_ini, "Hora Inicio": "08:00", "Hora Fin": "09:00",
                "Actividad / Detalle Diario": f"🏁 [INICIO DE FASE] {nombre_fase}", "Tipo / Origen": "Hito Oficial Maestro", "Fase Asociada": nombre_fase
            })
            if f_fin > f_ini:
                filas_hitos.append({
                    "Fecha": f_fin, "Hora Inicio": "20:00", "Hora Fin": "21:00",
                    "Actividad / Detalle Diario": f"🎯 [CIERRE DE FASE] {nombre_fase}", "Tipo / Origen": "Hito Oficial Maestro", "Fase Asociada": nombre_fase
                })

        df_hitos_maestros = pd.DataFrame(filas_hitos)
        df_operativo = st.session_state.df_agenda_matriz.copy()
        df_operativo["Fecha"] = pd.to_datetime(df_operativo["Fecha"]).dt.date

        df_maestro = pd.concat([df_hitos_maestros, df_operativo], ignore_index=True) if not df_hitos_maestros.empty else df_operativo
        df_maestro = df_maestro.drop_duplicates(subset=["Fecha", "Hora Inicio", "Actividad / Detalle Diario"]).sort_values(by=["Fecha", "Hora Inicio"]).reset_index(drop=True)
        df_maestro["Fecha Formateada"] = df_maestro["Fecha"].apply(formatear_fecha_espanol)

        st.markdown("#### 📋 Agenda General de Campo y Distribución Táctica")
        tab_dia, tab_semana, tab_mes, tab_general = st.tabs([
            "📅 Vista Diaria", "📆 Vista Semanal", "🗓️ Vista Mensual", "🌐 Vista General"
        ])
        
        cols_vistas = ["Fecha Formateada", "Hora Inicio", "Hora Fin", "Actividad / Detalle Diario", "Tipo / Origen", "Fase Asociada"]

        with tab_dia:
            if not df_maestro.empty:
                fechas_disp = sorted(df_maestro["Fecha"].unique())
                fecha_sel = st.selectbox("Selecciona la fecha:", fechas_disp, format_func=formatear_fecha_espanol, key="vd_f")
                df_d = df_maestro[df_maestro["Fecha"] == fecha_sel].copy()
                st.dataframe(df_d[cols_vistas], use_container_width=True)

        with tab_semana:
            if not df_maestro.empty:
                f_sem = st.date_input("Selecciona un día dentro de la semana:", value=date.today(), key="vs_f")
                ini_sem = f_sem - timedelta(days=f_sem.weekday())
                fin_sem = ini_sem + timedelta(days=6)
                df_s = df_maestro[(df_maestro["Fecha"] >= ini_sem) & (df_maestro["Fecha"] <= fin_sem)].copy()
                st.dataframe(df_s[cols_vistas], use_container_width=True)

        with tab_mes:
            if not df_maestro.empty:
                meses_proceso = [(9, 2026), (10, 2026), (11, 2026), (12, 2026), (1, 2027), (2, 2027), (3, 2027), (4, 2027), (5, 2027), (6, 2027)]
                opciones_meses = [f"{meses_es[m]} de {a}" for m, a in meses_proceso]
                mes_elegido_txt = st.selectbox("Selecciona el Mes del Proceso:", opciones_meses, key="vm_f")
                partes = mes_elegido_txt.split(" de ")
                m_nom, a_num = partes[0], int(partes[1])
                m_num = [k for k, v in meses_es.items() if v == m_nom][0]
                df_m = df_maestro[(pd.to_datetime(df_maestro["Fecha"]).dt.month == m_num) & (pd.to_datetime(df_maestro["Fecha"]).dt.year == a_num)].copy()
                st.dataframe(df_m[cols_vistas], use_container_width=True)

        with tab_general:
            if not df_maestro.empty:
                st.dataframe(df_maestro[cols_vistas], use_container_width=True)

# =========================================================================
# VISTA 6: EVENTO MASIVO / CIERRE (LOGÍSTICA COMPLETA)
# =========================================================================
elif st.session_state.seccion_activa == "EVENTO":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL"]:
        st.warning("⚠️ Acceso restringido al control de eventos masivos."); st.stop()

    st.markdown("## 🎪 Centro de Control: Evento Masivo y Cierre Territorial")
    if st.button("⬅️ Volver al Tablero / Menú", use_container_width=False, key="btn_ev_vol_f"):
        st.session_state.seccion_activa = "TABLERO"; st.rerun()

    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📍 Configuración del Lugar y Enlace GPS del Evento</div></div>", unsafe_allow_html=True)
    with st.form("form_config_evento_f"):
        ev_col1, ev_col2, ev_col3 = st.columns(3)
        with ev_col1:
            nombre_evento = st.text_input("Nombre / Motivo del Evento", "Gran Cierre de Campaña - Distrito 16", key="ev_nom_f")
            fecha_evento = st.text_input("Fecha y Hora", "Sábado 29 de Mayo, 17:00 hrs", key="ev_fec_f")
        with ev_col2:
            lugar_evento = st.text_input("Lugar / Sede", "Cancha Pública / Explanada Principal", key="ev_lug_f")
            link_gps_evento = st.text_input("Enlace Google Maps (Georreferencia)", "https://maps.google.com/?q=22.8905,-109.9167", key="ev_gps_f")
        with ev_col3:
            meta_asistencia_total = st.number_input("Meta de Asistencia Proyectada", value=3500, key="ev_meta_f")
            if st.form_submit_button("💾 Actualizar Ubicación y Sede"):
                st.success("✅ Sede y georreferencia actualizadas.")

    st.markdown("---")
    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📱 Convocatoria por WhatsApp (Cascada)</div></div>", unsafe_allow_html=True)
    contacto_ev_dest = st.selectbox("Destinatario (Mando & Anfitriones):", options=opciones_contactos_mando if opciones_contactos_mando else ["Sin contactos"], key="sb_dest_ev_f")
    tel_destino_ev = dict_contactos_mando.get(contacto_ev_dest, "6240000000")
    
    msg_sugerido = f"¡Hola! Te recordamos el {nombre_evento} el {fecha_evento} en {lugar_evento}. GPS: {link_gps_evento}."
    mensaje_final_w = st.text_area("Editar Mensaje de Convocatoria antes de Enviar:", value=msg_sugerido, height=100, key="msg_fin_ev_f")
    link_w_evento = f"https://wa.me/52{tel_destino_ev}?text={urllib.parse.quote(mensaje_final_w)}" if tel_destino_ev else "#"
    st.markdown(f'<a href="{link_w_evento}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 10px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 10px;">🚀 Disparar Mensaje vía WhatsApp</a>', unsafe_allow_html=True)

# =========================================================================
# VISTA 7: REDES SOCIALES Y DIFUSIÓN ESTRATÉGICA
# =========================================================================
elif st.session_state.seccion_activa == "REDES":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL", "ENCARGADO_REDES"]:
        st.warning("⚠️ Acceso restringido al módulo de redes sociales y difusión."); st.stop()

    st.markdown("## 📱 Módulo de Redes Sociales y Difusión Estratégica")
    if st.button("⬅️ Volver al Tablero / Menú", use_container_width=False, key="btn_redes_vol_f"):
        st.session_state.seccion_activa = "TABLERO"; st.rerun()

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>🌐 Canales Oficiales Conectados</div></div>", unsafe_allow_html=True)
        st.markdown("* **📘 Facebook Oficial:** 🟢 En Línea\n* **📸 Instagram de Campaña:** 🟢 En Línea\n* **🎵 TikTok Oficial:** 🟢 En Línea\n* **💬 Canal de WhatsApp:** 🟢 Sincronizado")
        if ES_LOCAL and st.button("📂 Abrir Carpeta 'LOGOS_IDENTIDAD' (PC)", use_container_width=True, key="btn_logos_redes_directo_f"): 
            abrir_carpeta_pc(r"C:\Users\Usuario\Desktop\Plataforma_Electoral\LOGOS_IDENTIDAD")

    with col_r2:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📢 Disparador de Boletín a Redes y Estructura</div></div>", unsafe_allow_html=True)
        with st.form("form_redes_sociales_f"):
            titulo_comunicado = st.text_input("Título / Asunto del Post o Boletín:", key="redes_tit_f")
            cuerpo_comunicado = st.text_area("Redacción del Mensaje Institucional:", "¡Baja California Sur merece más!", key="redes_cuerpo_f")
            plataforma_destino = st.selectbox("Canal de Destino:", ["Facebook", "Instagram", "TikTok", "Chats de Estructura", "Prensa"], key="redes_plat_f")
            texto_completo_redes = titulo_comunicado + "\n\n" + cuerpo_comunicado
            link_redes_w = f"https://wa.me/?text={urllib.parse.quote(texto_completo_redes)}"
            st.markdown(f'<a href="{link_redes_w}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 8px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 10px;">🚀 Disparar Boletín para {plataforma_destino} / Chats</a>', unsafe_allow_html=True)
            st.form_submit_button("💾 Guardar Registro en Historial Digital")

# =========================================================================
# VISTA 8: SIMULADOR DE ENCUESTAS (TRACKING POLL EN SMARTPHONE)
# =========================================================================
elif st.session_state.seccion_activa == "SIMULADOR":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL"]:
        st.warning("⚠️ Acceso restringido al simulador de encuestas."); st.stop()

    st.markdown("## 📱 Simulador Móvil: Formato Oficial de Encuesta")
    if st.button("⬅️ Volver al Tablero / Menú", use_container_width=False, key="btn_sim_vol_f"):
        st.session_state.seccion_activa = "TABLERO"; st.rerun()

    col_sim_izq, col_sim_cen, col_sim_der = st.columns([1, 2, 1])
    with col_sim_cen:
        st.markdown("<div class='mobile-simulator'>", unsafe_allow_html=True)
        st.markdown("<h4 style='color:#38bdf8; margin:0;'>📊 Tracking Poll Cloud</h4>", unsafe_allow_html=True)
        st.markdown("---")
        with st.form("form_tracking_poll_oficial_f"):
            st.markdown("##### 📍 Identificación de Campo")
            brigadista_reg = st.text_input("Brigadista Encuestador:", value="Carlos Mendoza", key="sim_brig_f")
            seccional_enc = st.text_input("Seccional Electoral (Ej: 400):", key="sim_secc_f")
            st.markdown("---")
            st.markdown("##### 📋 Cuestionario Normado")
            p1 = st.radio("1. ¿Sabe usted que este año hay elecciones?", ["Sí", "No"], horizontal=True, key="sim_p1_f")
            p2 = st.radio("2. ¿Conoce al candidato?", ["Sí", "No"], horizontal=True, key="sim_p2_f")
            p3 = st.radio("3. ¿Conoce al partido político?", ["Sí", "No"], horizontal=True, key="sim_p3_f")
            p4 = st.radio("4. ¿Votaría por nuestro candidato?", ["Sí", "No", "Tiene duda"], horizontal=True, key="sim_p4_f")
            
            if st.form_submit_button("🚀 Enviar Encuesta a la Nube"):
                if seccional_enc: st.success("✅ ¡Encuesta aplicada con éxito!")
                else: st.warning("⚠️ Ingrese la seccional electoral.")
        st.markdown("</div>", unsafe_allow_html=True)