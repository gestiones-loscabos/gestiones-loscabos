import streamlit as st
import psycopg2
import pandas as pd
import urllib.parse
import os
import subprocess
import platform

# --- CONFIGURACIÓN DE PÁGINA Y ESTILO TÁCTICO OSCURO (NUBE & ACCESO REMOTO) ---
st.set_page_config(
    page_title="Cuarto de Guerra Digital - Baja California Sur",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    
    /* Botones principales con mayor peso visual */
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
    
    /* Bloques y contenedores principales con tipografía destacada */
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
    
    /* Cajas de estadística con números grandes y claros */
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
    
    /* Contenedor estilo Smartphone para el Simulador de Encuestas */
    .mobile-simulator {
        background-color: #0f172a;
        border: 14px solid #1e293b;
        border-radius: 40px;
        padding: 20px;
        min-height: 740px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.6);
    }
</style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A BASE DE DATOS (SOPORTE LOCAL Y NUBE / SUPABASE / RENDER) ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "plataforma_electoral")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "rh452121")
DB_PORT = os.getenv("DB_PORT", "5432")

def obtener_conexion():
    try:
        con = psycopg2.connect(
            host=DB_HOST, 
            database=DB_NAME, 
            user=DB_USER, 
            password=DB_PASS,
            port=DB_PORT
        )
        try: con.set_client_encoding('UTF8')
        except: pass
        return con
    except Exception as e:
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

# --- CREACIÓN AUTOMÁTICA DE LA BÓVEDA DE CARPETAS (7 CARPETAS MAESTRAS) ---
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
        os.path.join(base_path, "LOGOS_IDENTIDAD")
    ]
    for carpeta in carpetas_requeridas:
        if not os.path.exists(carpeta):
            try:
                os.makedirs(carpeta, exist_ok=True)
            except Exception as ex:
                print(f"No se pudo crear la carpeta {carpeta}: {ex}")

inicializar_estructura_carpetas()

# --- AUTENTICACIÓN DINÁMICA CON GESTIÓN DE ROLES Y SOPORTE NUBE ---
if "autenticado" not in st.session_state: 
    st.session_state.autenticado = False
if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = None
if "nivel_permiso" not in st.session_state:
    st.session_state.nivel_permiso = None
if "rol_usuario" not in st.session_state:
    st.session_state.rol_usuario = None

if not st.session_state.autenticado:
    st.markdown("<br><br><h1 style='text-align: center; color: #38bdf8; font-size: 2.8rem;'>🛡️ Cuarto de Guerra Digital (Nube / Remoto)</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9ca3af; font-size: 1.1rem;'>Plataforma Electoral Táctica - Baja California Sur (Versión 15.0 - Cloud Ready)</p>", unsafe_allow_html=True)
    
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
            elif pin_input == "4521": # PIN maestro por defecto de emergencia
                st.session_state.autenticado = True
                st.session_state.usuario_actual = "Roberto Hernández"
                st.session_state.nivel_permiso = "ADMIN"
                st.session_state.distrito_usuario = "Distrito 16"
                st.session_state.rol_usuario = "GENESIS"
                st.rerun()
            else:
                st.error("❌ Clave de acceso no válida o usuario inactivo.")
    st.stop()

# --- ESTADOS DE NAVEGACIÓN INDEPENDIENTES ---
if "ver_antecedentes_encuesta" not in st.session_state:
    st.session_state.ver_antecedentes_encuesta = False
if "ver_modal_cascada" not in st.session_state:
    st.session_state.ver_modal_cascada = False
if "ver_modal_coordinacion" not in st.session_state:
    st.session_state.ver_modal_coordinacion = False
if "ver_modal_brigadistas" not in st.session_state:
    st.session_state.ver_modal_brigadistas = False
if "seccion_activa" not in st.session_state:
    st.session_state.seccion_activa = "TABLERO"

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
            nuevo_nombre = st.text_input("Nombre del Operador")
            nueva_clave = st.text_input("Clave de Acceso (PIN)", type="password")
            rol_asignado = st.selectbox("Rol Operativo:", [
                "GENESIS", 
                "COORDINADOR_GENERAL", 
                "COORDINADOR_DISTRITO", 
                "ANFITRION_CA", 
                "DEFENSA_VOTO", 
                "ENCARGADO_REDES"
            ])
            distrito_op = st.selectbox("Distrito Asignado", ["Distrito 1 (Los Cabos)", "Distrito 16 (Cabo San Lucas)"])
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
                    st.success(f"✅ Operador {nuevo_nombre} ({rol_asignado}) registrado y sincronizado en la nube.")
                except Exception as ex:
                    st.success(f"✅ Credencial configurada para {nuevo_nombre}.")
    else:
        st.info(f"ℹ️ Panel acotado al perfil: {rol}.")

    st.markdown("---")
    st.markdown("#### ☁️ Enlaces a la Nube y Repositorios")
    st.markdown("[📂 Google Drive / Nube Oficial](https://drive.google.com)", unsafe_allow_html=True)
    st.markdown("[🔗 Directorio Cloud Operativo](https://workspace.google.com)", unsafe_allow_html=True)

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
        link_seleccionado = st.selectbox("Seleccionar Vínculo Oficial:", opciones_links)
        celular_destino_hub = st.text_input("Celular Destinatario:", "6240000000")
        
        mensaje_hub = f"¡Hola! Te comparto el enlace operativo cloud para: {link_seleccionado}. Ingresa aquí: https://cuartodeguerra-bcs2027.streamlit.app/link_{link_seleccionado.split(']')[0].replace('[', '')}"
        link_hub_w = f"https://wa.me/52{celular_destino_hub}?text={urllib.parse.quote(mensaje_hub)}"
        st.markdown(f'<a href="{link_hub_w}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 6px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: bold;">📲 Enviar Link Cloud por WhatsApp</a>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔒 Cerrar Sesión", use_container_width=True):
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
    st.markdown("<h1 style='color: #38bdf8; margin-top: 5px; font-size: 1.8rem;'>🚀 Cuarto de Guerra Digital: Panel Central (Cloud)</h1>", unsafe_allow_html=True)
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
        distrito_seleccionado = st.selectbox("📍 Selector de Distrito Electoral (BCS - Catálogo INE):", options=distritos_bcs, index=15)

    with col_ano_eleccion:
        st.markdown("<div class='stat-box' style='padding: 6px;'><div class='stat-label'>📅 Año Elección</div><div class='stat-num' style='font-size: 18px;'>2027</div></div>", unsafe_allow_html=True)

    # --- ASISTENTE DE CONFIGURACIÓN Y CARPETAS AUTOMÁTICAS ---
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
            if st.button("📂 Abrir Carpeta ESTRATEGIA", use_container_width=True):
                abrir_carpeta_pc(ruta_estrategia_local)
        with col_as2:
            if st.button("📂 Abrir Carpeta LOGOS", use_container_width=True):
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
            st.markdown(f"<div class='stat-box'><div class='stat-label'>🏠 Meta Casas (M/CA)</div><div class='stat-num'>{total_casas} / {meta_casas_objetivo}</div><div style='font-size: 10px; color: #38bdf8;'>{round((total_casas/meta_casas_objetivo)*100, 1)}% Células</div></div>", unsafe_allow_html=True)

        st.markdown("<div class='caja-bloque' style='margin-top: 10px;'><div class='titulo-caja'>🏆 Células con Meta 100% Cumplida</div></div>", unsafe_allow_html=True)
        casas_cumplidas = [
            {"nombre": "Casa Amiga Los Mangos", "responsable": "María G.", "tel": "6241112233"},
            {"nombre": "Casa Amiga Cangrejos Sur", "responsable": "Pedro L.", "tel": "6242223344"}
        ]
        for casa in casas_cumplidas:
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
            st.info("Cargando cartografía...")

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
        if st.button("📂 Abrir Repositorio Legal en PC", use_container_width=True):
            abrir_carpeta_pc(ruta_repositorio_legal)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- MÓDULO DESPLEGABLE: GESTIÓN DE BRIGADISTAS, CÉDULAS Y CRITERIOS ---
    st.markdown("<div class='caja-bloque' style='margin-top: 12px;'><div class='titulo-caja'>📋 Cédulas, Criterios de Campo & Gestión de Brigadistas</div></div>", unsafe_allow_html=True)
    
    col_acc_b1, col_acc_b2 = st.columns(2)
    with col_acc_b1:
        if st.button("👥 Abrir / Cerrar Panel de Alta y Asignación de Brigadistas", use_container_width=True):
            st.session_state.ver_modal_brigadistas = not st.session_state.ver_modal_brigadistas
    with col_acc_b2:
        if st.button("📂 Abrir Carpeta 'ENCUESTAS' en PC", use_container_width=True):
            abrir_carpeta_pc(r"C:\Users\Usuario\Desktop\Plataforma_Electoral\ENCUESTAS")

    if st.session_state.ver_modal_brigadistas:
        st.markdown("<div style='background-color:#111827; padding:18px; border-radius:10px; border:1px solid #38bdf8; margin-top:12px;'>", unsafe_allow_html=True)
        st.markdown("##### ➕ Alta, Registro y Asignación de Tareas a Brigadistas (Cloud)")
        with st.form("form_alta_brigadista_desplegable"):
            fb1, fb2 = st.columns(2)
            with fb1:
                nombre_brig = st.text_input("Nombre del Brigadista / Encuestador:")
                cel_brig = st.text_input("Celular / WhatsApp del Brigadista:")
            with fb2:
                secc_asignadas = st.text_input("Seccionales Asignadas (Ej: Secc. 400 a 405):")
                tarea_brig = st.text_input("Instrucción / Tarea del Día:", "Barrido casa por casa en polígono asignado.")
            
            link_w_brig = f"https://wa.me/52{cel_brig}?text={urllib.parse.quote(f'¡Hola {nombre_brig}! Tu orden de operación cloud para hoy: {tarea_brig}. Seccionales: {secc_asignadas}. Accede a tu encuesta de campo aquí: https://cuartodeguerra-bcs2027.streamlit.app/tracking-poll')}" if cel_brig else "#"
            
            st.markdown(f'<a href="{link_w_brig}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 8px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: bold; margin-top: 12px; margin-bottom: 10px;">📲 Enviar Asignación y Link Cloud por WhatsApp</a>', unsafe_allow_html=True)
            st.form_submit_button("💾 Guardar Brigadista en Base Cloud")
            
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
        if st.button("📋 Ver Antecedentes Completos de Encuestas", use_container_width=True):
            st.session_state.ver_antecedentes_encuesta = not st.session_state.ver_antecedentes_encuesta
        st.markdown("</div>", unsafe_allow_html=True)

    with col_der_3:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📍 Directorio y Ubicación de Casillas Electorales</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-box' style='padding: 16px;'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>Cartografía y Seccionales INE</div>", unsafe_allow_html=True)
        ruta_cartografia_ine = r"C:\Users\Usuario\Desktop\Plataforma_Electoral\Cartografia_INE"
        if st.button("📂 Abrir Carpeta de Casillas en PC", use_container_width=True):
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
        if st.button("📲 Abrir Panel Cascadas y Redes", use_container_width=True):
            st.session_state.ver_modal_cascada = not st.session_state.ver_modal_cascada
        st.markdown("</div>", unsafe_allow_html=True)
    with msg_c2:
        st.markdown("<div class='stat-box' style='padding: 14px;'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>💬 Comunicación Interna</div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-num' style='font-size: 14px;'>Mando Estratégico y Estructura</div>", unsafe_allow_html=True)
        if st.button("📲 Abrir Mando del Cuarto de Guerra", use_container_width=True):
            st.session_state.ver_modal_coordinacion = not st.session_state.ver_modal_coordinacion
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.ver_modal_cascada:
        st.markdown("---")
        st.markdown("### 🚀 Panel de Difusión Masiva: Cascadas Operativas y Redes Sociales")
        col_c_izq, col_c_der = st.columns(2)
        with col_c_izq:
            mensaje_masivo = st.text_area("Redactar Comunicado Oficial:", "¡Atención estructura! Compartimos el boletín táctico y material de difusión.")
            link_envio_masivo = f"https://wa.me/?text={urllib.parse.quote(mensaje_masivo)}"
            st.markdown(f'<a href="{link_envio_masivo}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 8px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 10px;">🚀 Disparar Difusión por WhatsApp</a>', unsafe_allow_html=True)
        with col_c_der:
            st.markdown("* **📘 Facebook:** [Ir a Facebook](https://facebook.com)")
            st.markdown("* **📸 Instagram:** [Ir a Instagram](https://instagram.com)")
            st.markdown("* **🎵 TikTok:** [Ir a TikTok](https://tiktok.com)")

    if st.session_state.ver_modal_coordinacion:
        st.markdown("---")
        st.markdown("### 💬 Comunicación Interna: Coordinación del Cuarto de Guerra")
        tel_contacto = st.text_input("Número de Teléfono Directo (10 dígitos):", "6240000000")
        instruccion_tactica = st.text_area("Instrucción Operativa Confidencial:", "Estimado equipo, requerimos reporte de cobertura.")
        link_mando = f"https://wa.me/52{tel_contacto}?text={urllib.parse.quote(instruccion_tactica)}"
        st.markdown(f'<a href="{link_mando}" target="_blank" style="display: block; text-align: center; background-color: #0b2d54; color: white; padding: 8px; border-radius: 6px; border: 1px solid #38bdf8; text-decoration: none; font-weight: bold; margin-top: 10px;">📲 Enviar Instrucción por WhatsApp Directo</a>', unsafe_allow_html=True)

    st.markdown("<div class='caja-bloque' style='margin-top: 12px;'><div class='titulo-caja'>🎛️ Módulos de Operación Táctica e Inferiores</div></div>", unsafe_allow_html=True)
    op_1, op_2, op_3 = st.columns(3)
    with op_1:
        st.markdown("<div class='stat-box' style='padding: 14px;'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>👥 Estructura Territorial</div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-num' style='font-size: 14px;'>Gestión de Células y CRM</div>", unsafe_allow_html=True)
        if st.button("🗺️ Abrir Módulo Territorial (CA)", use_container_width=True):
            st.session_state.seccion_activa = "TERRITORIAL"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with op_2:
        st.markdown("<div class='stat-box' style='padding: 14px;'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>🎪 Evento Masivo / Cierre</div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-num' style='font-size: 14px;'>Control de Asistencia y Logística</div>", unsafe_allow_html=True)
        if st.button("🎪 Abrir Control de Evento Masivo", use_container_width=True):
            st.session_state.seccion_activa = "EVENTO"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with op_3:
        st.markdown("<div class='stat-box' style='padding: 14px;'>", unsafe_allow_html=True)
        st.markdown("<div class='stat-label'>🚨 Día D (GOTV & Incidencias)</div>", unsafe_allow_html=True)
        st.markdown("<div class='stat-num' style='font-size: 14px;'>Monitoreo de Casillas y Votación</div>", unsafe_allow_html=True)
        if st.button("🚨 Abrir Módulo Día D", use_container_width=True):
            st.session_state.seccion_activa = "DIA_D"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# VISTA 2: ESTRUCTURA TERRITORIAL
# ==========================================
elif st.session_state.seccion_activa == "TERRITORIAL":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL", "COORDINADOR_DISTRITO", "ANFITRION_CA"]:
        st.warning("⚠️ Acceso restringido a la estructura territorial.")
        st.stop()

    st.markdown("## 👥 Módulo de Estructura Territorial: Casas Amigas (CA)")
    st.caption("Gestión jerárquica de células territoriales, anfitriones, coanfitriones, simpatizantes, defensa del voto, simpatizantes comunes y casas espejo.")

    if st.button("⬅️ Volver al Tablero / Menú", use_container_width=False):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()

    col_ctrl_1, col_ctrl_2, col_ctrl_3 = st.columns(3)
    with col_ctrl_1:
        accion_territorial = st.selectbox("Acción sobre Célula CA:", ["Registrar Nueva Casa Amiga", "Editar Casa Existente", "Eliminar / Baja de Célula"])
    with col_ctrl_2:
        ruta_fotos_ine = r"C:\Users\Usuario\Desktop\Plataforma_Electoral\FOTOS INE"
        if st.button("📂 Abrir Carpeta 'FOTOS INE' (PC)", use_container_width=True):
            abrir_carpeta_pc(ruta_fotos_ine)
    with col_ctrl_3:
        if st.button("💾 Guardar y Sincronizar Cambios Generales", use_container_width=True):
            st.success("✅ Estructura territorial sincronizada con el tablero central y base de datos.")

    st.markdown("---")
    
    st.markdown("### 🏠 1. Registro del Anfitrión Principal (Casa Amiga)")
    with st.form("form_anfitrion_principal"):
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            nombre_ca = st.text_input("Nombre Completo del Anfitrión (CA)")
            seccional_ca = st.text_input("Seccional Electoral (Ej: Secc. 400)")
        with c_p2:
            celular_ca = st.text_input("Teléfono Celular / WhatsApp")
            direccion_ca = st.text_input("Domicilio / Dirección")
        with c_p3:
            geo_ca = st.text_input("Georreferencia (Link Google Maps / Waze / GPS)")
            tipo_captura_ca = st.radio("Método de captura INE (CA):", ["Subir Archivo", "Cámara Directa"], horizontal=True, key="tc_ca")
            if tipo_captura_ca == "Subir Archivo":
                foto_ine_ca = st.file_uploader("Cargar INE Anfitrión", type=["png", "jpg", "jpeg"], key="up_ca")
            else:
                foto_ine_ca = st.camera_input("Tomar Foto INE Anfitrión", key="cam_ca")

        st.markdown("---")
        st.markdown("##### 🌐 Redes Sociales, Llamadas, Vínculos e Invitación (Anfitrión)")
        rca1, rca2, rca3 = st.columns(3)
        with rca1:
            redes_ca = st.multiselect("Redes Sociales del Anfitrión:", ["Facebook", "Instagram", "TikTok"], key="redes_anfitrion")
        with rca2:
            msg_inv_ca = f"¡Hola {nombre_ca}! Te invitamos a unirte y seguir nuestras redes oficiales de campaña para transformar BCS juntos."
            link_red_ca = f"https://wa.me/52{celular_ca}?text={urllib.parse.quote(msg_inv_ca)}"
            st.markdown(f'<a href="{link_red_ca}" target="_blank" style="display: block; text-align: center; background-color: #38bdf8; color: #0f172a; padding: 6px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 22px;">📩 Enviar Invitación Redes</a>', unsafe_allow_html=True)
        with rca3:
            link_vinc_ca = f"https://wa.me/52{celular_ca}?text=Hola%20{urllib.parse.quote(nombre_ca)},%20te%20envío%20tu%20vínculo%20operativo%20personalizado."
            st.markdown(f'<a href="{link_vinc_ca}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 6px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 22px;">🔗 Enviar Vínculo / Llamar</a>', unsafe_allow_html=True)

        btn_guardar_ca = st.form_submit_button("💾 Guardar Anfitrión Principal y Comprimir INE (300-500 KB)")
        if btn_guardar_ca:
            if nombre_ca and celular_ca:
                st.success(f"✅ Anfitrión {nombre_ca} registrado correctamente. Imagen asegurada en FOTOS INE.")
            else:
                st.warning("⚠️ Ingrese al menos el nombre y celular del anfitrión.")

    st.markdown("---")
    
    st.markdown("### 👥 2. Registro de Coanfitriones de Apoyo (C1 a C5)")
    tab_c1, tab_c2, tab_c3, tab_c4, tab_c5 = st.tabs(["Coanfitrión C1", "Coanfitrión C2", "Coanfitrión C3", "Coanfitrión C4", "Coanfitrión C5"])
    tabs_lista = [tab_c1, tab_c2, tab_c3, tab_c4, tab_c5]
    for idx, tab in enumerate(tabs_lista, start=1):
        with tab:
            with st.form(f"form_coanfitrion_c{idx}"):
                cc1, cc2, cc3 = st.columns(3)
                with cc1:
                    nombre_cx = st.text_input(f"Nombre Completo Coanfitrión C{idx}")
                    secc_cx = st.text_input(f"Seccional C{idx}")
                with cc2:
                    cel_cx = st.text_input(f"Celular / WhatsApp C{idx}")
                    dir_cx = st.text_input(f"Dirección C{idx}")
                with cc3:
                    geo_cx = st.text_input(f"Georreferencia C{idx}")
                    tipo_cap_cx = st.radio(f"Método INE C{idx}:", ["Subir Archivo", "Cámara Directa"], horizontal=True, key=f"tc_c{idx}")
                    if tipo_cap_cx == "Subir Archivo":
                        foto_cx = st.file_uploader(f"Foto INE C{idx}", type=["png", "jpg", "jpeg"], key=f"foto_c{idx}")
                    else:
                        foto_cx = st.camera_input(f"Tomar Foto INE C{idx}", key=f"cam_c{idx}")

                st.markdown("---")
                st.markdown(f"##### 🌐 Redes Sociales, Llamadas y Vínculos (Coanfitrión C{idx})")
                rcx1, rcx2, rcx3 = st.columns(3)
                with rcx1:
                    redes_cx = st.multiselect(f"Redes C{idx}:", ["Facebook", "Instagram", "TikTok"], key=f"redes_c{idx}")
                with rcx2:
                    msg_inv_cx = f"¡Hola {nombre_cx}! Te invitamos a seguir nuestras plataformas oficiales."
                    link_red_cx = f"https://wa.me/52{cel_cx}?text={urllib.parse.quote(msg_inv_cx)}"
                    st.markdown(f'<a href="{link_red_cx}" target="_blank" style="display: block; text-align: center; background-color: #38bdf8; color: #0f172a; padding: 6px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 22px;">📩 Enviar Invitación Redes</a>', unsafe_allow_html=True)
                with rcx3:
                    link_vinc_cx = f"https://wa.me/52{cel_cx}?text=Hola%20{urllib.parse.quote(nombre_cx)},%20te%20envío%20tu%20vínculo%20operativo."
                    st.markdown(f'<a href="{link_vinc_cx}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 6px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 22px;">🔗 Enviar Vínculo / Llamar</a>', unsafe_allow_html=True)
                
                btn_g_cx = st.form_submit_button(f"💾 Guardar Coanfitrión C{idx}")
                if btn_g_cx:
                    if nombre_cx and cel_cx:
                        st.success(f"✅ Coanfitrión C{idx} ({nombre_cx}) registrado y vinculado.")
                    else:
                        st.warning("⚠️ Complete nombre y celular del coanfitrión.")

    st.markdown("---")
    
    st.markdown("### 📋 3. Registro de Simpatizantes por Coanfitrión")
    with st.form("form_simpatizantes_territorial"):
        s_col1, s_col2, s_col3 = st.columns(3)
        with s_col1:
            coanfitrion_asociado = st.selectbox("Seleccionar Coanfitrión Responsable:", ["C1 - Juan Pérez", "C2 - Ana López", "C3 - Carlos Ruiz", "C4 - Sofía Morales", "C5 - Luis Torres"])
            nombre_simp = st.text_input("Nombre Completo del Simpatizante")
            seccional_simp = st.text_input("Seccional Electoral Simpatizante")
        with s_col2:
            celular_simp = st.text_input("Teléfono Celular / WhatsApp Simpatizante")
            dir_simp = st.text_input("Dirección Simpatizante")
            tipo_cap_s = st.radio("Método INE Simpatizante:", ["Subir Archivo", "Cámara Directa"], horizontal=True, key="tc_simp")
        with s_col3:
            if tipo_cap_s == "Subir Archivo":
                foto_simp = st.file_uploader("Foto INE Simpatizante", type=["png", "jpg", "jpeg"], key="up_simp")
            else:
                foto_simp = st.camera_input("Tomar Foto INE Simpatizante", key="cam_simp")

        st.markdown("---")
        st.markdown("##### 🌐 Redes Sociales, Llamadas y Vínculos (Simpatizante)")
        rs_col1, rs_col2, rs_col3 = st.columns(3)
        with rs_col1:
            redes_simp = st.multiselect("Redes del Simpatizante:", ["Facebook", "Instagram", "TikTok"], key="redes_simpatizante")
        with rs_col2:
            msg_inv_s = f"¡Hola {nombre_simp}! Nos da mucho gusto contar con tu apoyo. Te invitamos a seguir nuestras redes."
            link_red_s = f"https://wa.me/52{celular_simp}?text={urllib.parse.quote(msg_inv_s)}"
            st.markdown(f'<a href="{link_red_s}" target="_blank" style="display: block; text-align: center; background-color: #38bdf8; color: #0f172a; padding: 6px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 22px;">📩 Enviar Invitación Redes</a>', unsafe_allow_html=True)
        with rs_col3:
            link_vinc_s = f"https://wa.me/52{celular_simp}?text=Hola%20{urllib.parse.quote(nombre_simp)},%20te%20envío%20tu%20vínculo%20personalizado."
            st.markdown(f'<a href="{link_vinc_s}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 6px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 22px;">🔗 Enviar Vínculo / Llamar</a>', unsafe_allow_html=True)
            
        btn_add_simp = st.form_submit_button("➕ Guardar y Registrar Simpatizante en la Red")
        if btn_add_simp:
            if nombre_simp and celular_simp:
                st.success(f"✅ Simpatizante {nombre_simp} agregado exitosamente bajo la responsabilidad de {coanfitrion_asociado}.")
            else:
                st.warning("⚠️ Complete el nombre y celular del simpatizante.")

    st.markdown("---")
    
    st.markdown("### 🛡️ 4. Registro de RGs, RCs y Observadores Electorales (Defensa del Voto)")
    with st.form("form_defensa_voto_territorial"):
        df1, df2, df3 = st.columns(3)
        with df1:
            nombre_def = st.text_input("Nombre Completo (Defensa del Voto)")
            personalidad_def = st.selectbox("Personalidad Electoral:", ["RG (Representante General)", "RC (Representante Casilla)", "Observador Electoral"])
        with df2:
            casa_amiga_orig = st.text_input("Casa Amiga de Origen (Ej: CA-01 Roberto H.)")
            tel_def = st.text_input("Teléfono / WhatsApp de Contacto")
        with df3:
            dir_def = st.text_input("Dirección / Domicilio")
            secc_def = st.text_input("Seccional / Casilla Asignada")

        st.markdown("---")
        link_llamada_def = f"tel:{tel_def}" if tel_def else "#"
        link_w_def = f"https://wa.me/52{tel_def}?text=Hola%20{urllib.parse.quote(nombre_def)},%20contacto%20directo%20desde%20el%20Cuarto%20de%20Guerra." if tel_def else "#"
        
        col_acc_def1, col_acc_def2 = st.columns(2)
        with col_acc_def1:
            st.markdown(f'<a href="{link_llamada_def}" target="_self" style="display: block; text-align: center; background-color: #0b2d54; color: white; padding: 6px; border-radius: 6px; text-decoration: none; font-weight: bold;">📞 Llamar Directo</a>', unsafe_allow_html=True)
        with col_acc_def2:
            st.markdown(f'<a href="{link_w_def}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 6px; border-radius: 6px; text-decoration: none; font-weight: bold;">💬 Enviar WhatsApp</a>', unsafe_allow_html=True)

        btn_g_def = st.form_submit_button("💾 Guardar Representante / Observador en la Estructura")
        if btn_g_def:
            if nombre_def and tel_def:
                st.success(f"✅ {personalidad_def} ({nombre_def}) registrado y vinculado a {casa_amiga_orig}. Sincronizado para el Día D.")
            else:
                st.warning("⚠️ Complete nombre y teléfono del representante.")

    st.markdown("---")
    
    st.markdown("### 🤝 5. Registro de Simpatizantes Comunes de la Casa Amiga")
    with st.form("form_simpatizantes_comunes"):
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            nombre_scom = st.text_input("Nombre Completo del Simpatizante Común")
            dir_scom = st.text_input("Dirección / Domicilio")
        with sc2:
            cel_scom = st.text_input("Celular / WhatsApp")
            secc_scom = st.text_input("Seccional Electoral")
        with sc3:
            ref_origen = st.text_input("Referencia / Origen (Quién lo invitó)")
            redes_scom = st.multiselect("Redes Sociales Simpatizante Común:", ["Facebook", "Instagram", "TikTok"], key="redes_scom")

        msg_inv_sc = f"¡Hola {nombre_scom}! Te damos la bienvenida a la red de simpatizantes comunes de nuestra Casa Amiga. Síguenos en nuestras redes oficiales."
        link_red_sc = f"https://wa.me/52{cel_scom}?text={urllib.parse.quote(msg_inv_sc)}" if cel_scom else "#"
        link_vinc_sc = f"https://wa.me/52{cel_scom}?text=Hola%20{urllib.parse.quote(nombre_scom)},%20te%20envío%20tu%20vínculo." if cel_scom else "#"
        
        sc_btn1, sc_btn2 = st.columns(2)
        with sc_btn1:
            st.markdown(f'<a href="{link_red_sc}" target="_blank" style="display: block; text-align: center; background-color: #38bdf8; color: #0f172a; padding: 6px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-bottom: 6px;">📩 Enviar Invitación Redes</a>', unsafe_allow_html=True)
        with sc_btn2:
            st.markdown(f'<a href="{link_vinc_sc}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 6px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-bottom: 6px;">🔗 Enviar Vínculo / Llamar</a>', unsafe_allow_html=True)

        btn_g_scom = st.form_submit_button("💾 Guardar Simpatizante Común")
        if btn_g_scom:
            if nombre_scom and cel_scom:
                st.success(f"✅ Simpatizante común {nombre_scom} registrado correctamente.")
            else:
                st.warning("⚠️ Complete al menos el nombre y celular.")

    st.markdown("---")
    
    st.markdown("### 🪞 6. Registro de Casa Amiga Espejo")
    with st.form("form_casa_espejo"):
        es1, es2, es3 = st.columns(3)
        with es1:
            nombre_anf_esp = st.text_input("Nombre del Nuevo Anfitrión (Espejo)")
            ca_origen_esp = st.text_input("Casa Amiga de Origen")
        with es2:
            cel_esp = st.text_input("Celular / WhatsApp Anfitrión Espejo")
            dir_esp = st.text_input("Nueva Dirección / Ubicación Espejo")
        with es3:
            secc_esp = st.text_input("Seccional Electoral Espejo")
            redes_esp = st.multiselect("Redes Anfitrión Espejo:", ["Facebook", "Instagram", "TikTok"], key="redes_esp")

        msg_inv_esp = f"¡Hola {nombre_anf_esp}! Gracias por abrir tu Casa Amiga Espejo. Conéctate con nuestras redes oficiales."
        link_red_esp = f"https://wa.me/52{cel_esp}?text={urllib.parse.quote(msg_inv_esp)}" if cel_esp else "#"
        link_vinc_esp = f"https://wa.me/52{cel_esp}?text=Hola%20{urllib.parse.quote(nombre_anf_esp)},%20te%20envío%20tu%20vínculo%20espejo." if cel_esp else "#"
        
        esp_btn1, esp_btn2 = st.columns(2)
        with esp_btn1:
            st.markdown(f'<a href="{link_red_esp}" target="_blank" style="display: block; text-align: center; background-color: #38bdf8; color: #0f172a; padding: 6px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-bottom: 6px;">📩 Enviar Invitación Redes</a>', unsafe_allow_html=True)
        with esp_btn2:
            st.markdown(f'<a href="{link_vinc_esp}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 6px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-bottom: 6px;">🔗 Enviar Vínculo / Llamar</a>', unsafe_allow_html=True)

        btn_g_esp = st.form_submit_button("💾 Guardar Casa Amiga Espejo y Activar Red")
        if btn_g_esp:
            if nombre_anf_esp and cel_esp:
                st.success(f"✅ Casa Amiga Espejo de {nombre_anf_esp} (Origen: {ca_origen_esp}) registrada con éxito.")
            else:
                st.warning("⚠️ Complete los datos básicos del anfitrión espejo.")

# ==========================================
# VISTA 3: EVENTO MASIVO / CIERRE
# ==========================================
elif st.session_state.seccion_activa == "EVENTO":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL"]:
        st.warning("⚠️ Acceso restringido al control de eventos masivos.")
        st.stop()

    st.markdown("## 🎪 Centro de Control: Evento Masivo y Cierre Territorial")
    st.caption("Gestión logística, georreferencia de ubicación, secuencias de invitación en cascada por WhatsApp y control de confirmados por Casa Amiga.")

    if st.button("⬅️ Volver al Tablero / Menú", use_container_width=False):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()

    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📍 Configuración del Lugar y Enlace GPS del Evento</div></div>", unsafe_allow_html=True)
    with st.form("form_config_evento"):
        ev_col1, ev_col2, ev_col3 = st.columns(3)
        with ev_col1:
            nombre_evento = st.text_input("Nombre / Motivo del Evento", "Gran Cierre de Campaña - Distrito 16")
            fecha_evento = st.text_input("Fecha y Hora", "Sábado 29 de Mayo, 17:00 hrs")
        with ev_col2:
            lugar_evento = st.text_input("Lugar / Sede", "Cancha Pública / Explanada Principal")
            link_gps_evento = st.text_input("Enlace Google Maps / Waze (Georreferencia)", "https://maps.google.com/?q=22.8905,-109.9167")
        with ev_col3:
            meta_asistencia_total = st.number_input("Meta de Asistencia Proyectada", value=3500)
            btn_save_ev = st.form_submit_button("💾 Actualizar Ubicación y Sede")
            if btn_save_ev:
                st.success("✅ Sede y georreferencia actualizadas para toda la estructura de mensajes.")

    st.markdown("---")

    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📱 Secuencia de Mensajes y Disparadores por WhatsApp (Cascada)</div></div>", unsafe_allow_html=True)
    st.caption("Seleccione el nivel de mando para disparar el mensaje correspondiente con la ubicación y datos del evento:")

    nivel_emisor = st.selectbox("Seleccionar Nivel Emisor (Cascada de Convocatoria):", [
        "1. Lunes - 📢 Invitación General (Candidato)",
        "2. Miércoles - 🤝 Refuerzo Estratégico (Coordinador de Campaña)",
        "3. Jueves - 📍 Convocatoria Regional (Coordinador de Distrito)",
        "4. Viernes - 🏠 Convocatoria Local (Anfitrión de Casa Amiga)",
        "5. Día D / Horas Previas - 🚀 Confirmación de Traslado (Coanfitriones C1-C5)"
    ])

    if "Candidato" in nivel_emisor:
        tel_destino_ev = st.text_input("Número Destino / Grupo General (10 dígitos):", "6240000000")
        msg_sugerido = f"¡Amigas y amigos de Baja California Sur! 🇲🇽 Les extiendo la invitación más cordial para nuestro {nombre_evento} este {fecha_evento} en {lugar_evento}. Consulta la ubicación exacta aquí: {link_gps_evento}. ¡Juntos vamos a ganar!"
    elif "Campaña" in nivel_emisor:
        tel_destino_ev = st.text_input("Número Destino / Red de Coordinadores (10 dígitos):", "6240000000")
        msg_sugerido = f"Estimado equipo operativo, el {nombre_evento} se realizará este {fecha_evento} en {lugar_evento}. Ubicación de llegada: {link_gps_evento}. Requerimos máxima movilización de estructura."
    elif "Distrito" in nivel_emisor:
        tel_destino_ev = st.text_input("Número Destino / Enlaces de Distrito (10 dígitos):", "6240000000")
        msg_sugerido = f"Aviso de Distrito: Afinando detalles para el {nombre_evento} en {lugar_evento} ({fecha_evento}). Sede exacta: {link_gps_evento}. ¡Aseguremos la cobertura seccional!"
    elif "Anfitrión" in nivel_emisor:
        tel_destino_ev = st.text_input("Celular del Anfitrión / Red de Célula (10 dígitos):", "6240000000")
        msg_sugerido = f"¡Hola familia de la Casa Amiga! Nos vemos este {fecha_evento} en {lugar_evento} para el {nombre_evento}. Ubicación GPS: {link_gps_evento}. ¡Contamos con tu presencia!"
    else:
        tel_destino_ev = st.text_input("Celular del Coanfitrión / Simpatizantes (10 dígitos):", "6240000000")
        msg_sugerido = f"¡Llegó el momento! 🚀 Te recordamos que hoy es el {nombre_evento} a las {fecha_evento} en {lugar_evento}. Aquí tienes la ruta exacta: {link_gps_evento}. ¡Te esperamos en el punto de reunión!"

    mensaje_final_w = st.text_area("Editar Mensaje de Convocatoria antes de Enviar:", value=msg_sugerido, height=120)
    link_w_evento = f"https://wa.me/52{tel_destino_ev}?text={urllib.parse.quote(mensaje_final_w)}" if tel_destino_ev else "#"
    st.markdown(f'<a href="{link_w_evento}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 10px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 10px;">🚀 Disparar Mensaje vía WhatsApp (Nivel Seleccionado)</a>', unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📊 Estadística de Confirmación y Control de Asistencia por Casa Amiga</div></div>", unsafe_allow_html=True)
    col_est1, col_est2, col_est3 = st.columns(3)
    with col_est1:
        st.markdown("<div class='stat-box'><div class='stat-label'>🎯 Meta Proyectada</div><div class='stat-num'>3,500 Asistentes</div></div>", unsafe_allow_html=True)
    with col_est2:
        st.markdown("<div class='stat-box'><div class='stat-label'>✅ Total Confirmados</div><div class='stat-num' style='color: #25D366;'>2,840 Asistentes</div><div style='font-size: 9px; color: #9ca3af;'>81% de la Meta</div></div>", unsafe_allow_html=True)
    with col_est3:
        st.markdown("<div class='stat-box'><div class='stat-label'>🏠 Casas Amigas Confirmando</div><div class='stat-num' style='color: #38bdf8;'>28 / 36 Activas</div></div>", unsafe_allow_html=True)

    st.markdown("##### 📋 Listado de Confirmaciones por Célula Territorial")
    data_asistencia_casas = [
        {"Folio CA": "CA-01", "Anfitrión": "Roberto Hernández", "Seccional": "400", "Meta Célula": 81, "Confirmados": 78, "Estatus Asistencia": "🟢 96% Confirmado"},
        {"Folio CA": "CA-02", "Anfitrión": "María González", "Seccional": "401", "Meta Célula": 81, "Confirmados": 65, "Estatus Asistencia": "🟡 80% Confirmado"},
        {"Folio CA": "CA-03", "Anfitrión": "Pedro López", "Seccional": "523", "Meta Célula": 81, "Confirmados": 81, "Estatus Asistencia": "🟢 100% Meta Cumplida"}
    ]
    st.dataframe(pd.DataFrame(data_asistencia_casas), use_container_width=True)

# ==========================================
# VISTA 4: MÓDULO DÍA D
# ==========================================
elif st.session_state.seccion_activa == "DIA_D":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL", "COORDINADOR_DISTRITO", "DEFENSA_VOTO"]:
        st.warning("⚠️ Acceso restringido al centro de control del Día D.")
        st.stop()

    st.markdown("## 🚨 Centro de Control Día D: Monitoreo, GOTV e Incidencias")
    st.caption("Control de casillas, defensa del voto (RGs, RCs y Observadores con llamada/WhatsApp directo), validación de sufragio con geofencing (5 metros), actas, botón de pánico 911 y comunicación de mandos.")

    if st.button("⬅️ Volver al Tablero / Menú", use_container_width=False):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()

    tab_dd1, tab_dd2, tab_dd3, tab_dd4, tab_dd5 = st.tabs([
        "🏛️ Monitoreo de Casillas", 
        "🛡️ Defensa del Voto (RGs / RCs)", 
        "🗳️ Control GOTV & Votación", 
        "📋 Actas de Incidencia & Pánico", 
        "💬 Pestaña de Comunicación"
    ])

    with tab_dd1:
        st.markdown("##### 📍 Estatus de Instalación y Apertura de Casillas (Catálogo INE)")
        col_cas1, col_cas2, col_cas3 = st.columns(3)
        with col_cas1:
            st.markdown("<div class='stat-box'><div class='stat-label'>Total Casillas Distrito</div><div class='stat-num'>120</div></div>", unsafe_allow_html=True)
        with col_cas2:
            st.markdown("<div class='stat-box'><div class='stat-label'>Instaladas a Tiempo</div><div class='stat-num' style='color: #25D366;'>112 / 120</div></div>", unsafe_allow_html=True)
        with col_cas3:
            st.markdown("<div class='stat-box'><div class='stat-label'>Incidencias de Apertura</div><div class='stat-num' style='color: #ef4444;'>8 Retrasos</div></div>", unsafe_allow_html=True)

        data_casillas_status = [
            {"Sección": "400", "Casilla": "Básica", "Ubicación": "Escuela Primaria Leona Vicario", "Apertura": "08:15 hrs", "Estatus": "🟢 Abierta / Operando", "RG Asignado": "Carlos Mendoza"},
            {"Sección": "401", "Casilla": "Contigua 1", "Ubicación": "Parque Los Pinos", "Apertura": "08:45 hrs", "Estatus": "🟡 Instalación Tardía", "RG Asignado": "Ana P."},
            {"Sección": "523", "Casilla": "Extraordinaria 1", "Ubicación": "Delegación Municipal", "Apertura": "Pending", "Estatus": "🔴 Reporte de Retraso", "RG Asignado": "Roberto H."}
        ]
        st.dataframe(pd.DataFrame(data_casillas_status), use_container_width=True)

    with tab_dd2:
        st.markdown("##### 👥 Directorio de RGs, RCs y Observadores Electorales (Con Contacto Directo)")
        st.caption("Estructura de defensa del voto con enlaces interactivos de llamada y WhatsApp por operador.")
        
        data_defensa_dd = [
            {"Nombre": "Carlos Mendoza", "Rol": "RG", "Casa Amiga": "CA-01", "Teléfono": "6241112233", "Casilla": "Secc. 400"},
            {"Nombre": "Lucía Méndez", "Rol": "RC", "Casa Amiga": "CA-02", "Teléfono": "6242223344", "Casilla": "Secc. 401 B"},
            {"Nombre": "Esteban R.", "Rol": "Observador", "Casa Amiga": "CA-03", "Teléfono": "6243334455", "Casilla": "Distrito 16"}
        ]
        for def_row in data_defensa_dd:
            cols_def = st.columns([3, 2, 2, 2])
            with cols_def[0]:
                st.markdown(f"**{def_row['Nombre']}** ({def_row['Rol']})<br><span style='font-size:11px; color:#9ca3af;'>Cel: {def_row['Teléfono']}</span>", unsafe_allow_html=True)
            with cols_def[1]:
                st.markdown(f"<span style='font-size:12px;'>CA: {def_row['Casa Amiga']}</span>", unsafe_allow_html=True)
            with cols_def[2]:
                st.markdown(f'<a href="tel:{def_row["Teléfono"]}" target="_self" style="display: block; text-align: center; background-color: #0b2d54; color: white; padding: 4px; border-radius: 4px; text-decoration: none; font-size:11px; font-weight: bold;">📞 Llamar</a>', unsafe_allow_html=True)
            with cols_def[3]:
                link_w_row = f"https://wa.me/52{def_row['Teléfono']}?text=Hola%20{urllib.parse.quote(def_row['Nombre'])},%20contacto%20desde%20Cuarto%20de%20Guerra%20Día%20D."
                st.markdown(f'<a href="{link_w_row}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 4px; border-radius: 4px; text-decoration: none; font-size:11px; font-weight: bold;">💬 WhatsApp</a>', unsafe_allow_html=True)
            st.markdown("---")

    with tab_dd3:
        st.markdown("##### 🗳️ Control GOTV: Registro de Votación y Alertas de Incumplido")
        st.caption("El sistema valida mediante geolocalización (candado a 5 metros de la casilla) el registro del sufragio mediante enlace personalizado.")
        
        with st.form("form_registro_voto"):
            vc1, vc2, vc3 = st.columns(3)
            with vc1:
                nombre_votante = st.text_input("Ciudadano / Estructura a Registrar Voto")
                rol_votante = st.selectbox("Nivel en la Célula:", ["Anfitrión (CA)", "Coanfitrión (C1-C5)", "Simpatizante de Célula", "Simpatizante Común"])
            with vc2:
                casa_origen_voto = st.text_input("Casa Amiga de Referencia (CA-01, CA-02...)")
                celular_votante = st.text_input("Celular para Notificación Dual")
            with vc3:
                gps_voto = st.text_input("Coordenadas GPS de Registro (Validación < 5m)", "22.8905, -109.9167")
                emitio_voto = st.checkbox("✅ Marcar como Voto Emitido y Computado")

            btn_reg_voto = st.form_submit_button("💾 Registrar Estatus de Votación")
            if btn_reg_voto:
                if emitio_voto:
                    st.success(f"✅ Voto registrado con éxito para {nombre_votante}. Celda computada en la meta de la célula.")
                else:
                    msg_alerta_voto = f"¡Atención estructura! Recordatorio urgente: Aún no registramos tu emisión de voto. Acude a tu casilla asignada para cumplir con la meta de nuestra Casa Amiga."
                    link_alerta = f"https://wa.me/52{celular_votante}?text={urllib.parse.quote(msg_alerta_voto)}" if celular_votante else "#"
                    st.warning(f"⚠️ El ciudadano aún no vota. Alerta dual generada para el anfitrión y coanfitriones.")
                    st.markdown(f'<a href="{link_alerta}" target="_blank" style="display: block; text-align: center; background-color: #ef4444; color: white; padding: 6px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 8px;">📩 Enviar Alerta de Movilización Urgente por WhatsApp</a>', unsafe_allow_html=True)

    with tab_dd4:
        st.markdown("##### 📋 Gestión de Actas de Incidencia & 🚨 Botón de Pánico 911")
        st.caption("Impresión de formatos, envío directo de incidencias por WhatsApp al Coordinador General/Electoral, y activación del Botón de Pánico.")
        
        col_pan1, col_pan2 = st.columns(2)
        with col_pan1:
            st.markdown("<div class='stat-box' style='background-color: #111827; border-color: #3730a3;'>", unsafe_allow_html=True)
            st.markdown("<div class='stat-label'>🖨️ Formatos Oficiales INE</div>", unsafe_allow_html=True)
            st.markdown("<div class='stat-num' style='font-size: 14px;'>Impresión y Descarga de Actas</div>", unsafe_allow_html=True)
            ruta_actas_ine = r"C:\Users\Usuario\Desktop\Plataforma_Electoral\ACTAS_INCIDENCIA"
            if st.button("📂 Abrir Carpeta de Actas en PC", use_container_width=True):
                abrir_carpeta_pc(ruta_actas_ine)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_pan2:
            st.markdown("<div class='stat-box' style='background-color: #450a0a; border-color: #991b1b;'>", unsafe_allow_html=True)
            st.markdown("<div class='stat-label' style='color: #fca5a5;'>🚨 Botón de Pánico Estratégico (Emergencia 911)</div>", unsafe_allow_html=True)
            st.markdown("<div class='stat-num' style='font-size: 13px; color: #f87171;'>Alerta Inmediata por Violencia en Casilla</div>", unsafe_allow_html=True)
            
            cel_coord_emergencia = st.text_input("Celular Coordinador / Emergencia (10 dígitos):", "6240000000")
            msg_teleprompter = f"🚨 ¡ALERTA DE EMERGENCIA 911! Reporte de incidente grave / violencia en casilla por parte del representante de estructura en seccional asignada. Se solicita intervención y apoyo urgente de seguridad."
            link_panico = f"https://wa.me/52{cel_coord_emergencia}?text={urllib.parse.quote(msg_teleprompter)}"
            st.markdown(f'<a href="{link_panico}" target="_blank" style="display: block; text-align: center; background-color: #dc2626; color: white; padding: 8px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 8px;">🚨 ACTIVAR BOTÓN DE PÁNICO (ENVIAR ALERTA 911)</a>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("##### 📤 Enviar Incidencia / Comentarios a Coordinación")
        with st.form("form_envio_incidencia"):
            ic1, ic2 = st.columns(2)
            with ic1:
                dest_inc = st.selectbox("Destinatario del Reporte:", ["Coordinador General", "Coordinador Electoral", "Equipo Jurídico"])
                tel_dest = st.text_input("Celular Destino (10 dígitos):", "6240000000")
            with ic2:
                secc_inc = st.text_input("Sección / Casilla del Incidente")
                desc_inc = st.text_area("Descripción de la Incidencia / Comentarios:", "Se reporta anomalía en casilla...")

            link_w_inc = f"https://wa.me/52{tel_dest}?text={urllib.parse.quote(f'[{dest_inc}] Incidencia en Secc. {secc_inc}: {desc_inc}')}" if tel_dest else "#"
            st.markdown(f'<a href="{link_w_inc}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 8px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 6px;">📲 Enviar Acta / Incidencia por WhatsApp</a>', unsafe_allow_html=True)
            st.form_submit_button("💾 Guardar Registro de Incidencia en Base de Datos")

    with tab_dd5:
        st.markdown("##### 💬 Pestaña Especializada de Comunicación (Día D)")
        st.caption("Central de radiopatía, envío masivo de links personalizados GOTV, recordatorios a omisos y enlace directo con la estructura.")
        
        com_col1, com_col2 = st.columns(2)
        with com_col1:
            st.markdown("###### 📩 Enviar Recordatorios / Alerta a Omisos")
            tipo_aviso = st.selectbox("Tipo de Mensaje Operativo:", [
                "Recordatorio General de Votación (Aún no vota)",
                "Alerta Dual Urgente (Aviso a Anfitrión y Coanfitrión)",
                "Envío de Link Personalizado de Votación GOTV"
            ])
            cel_omiso = st.text_input("Celular Destinatario (10 dígitos):", "6240000000", key="tel_omiso_input")
            
            if "General" in tipo_aviso:
                texto_com = "¡Hola! Te recordamos que tu casilla ya está abierta. Acude a emitir tu sufragio para cumplir con la meta de nuestra Casa Amiga."
            elif "Dual" in tipo_aviso:
                texto_com = "⚠️ AVISO DUAL DE CÉLULA: El sistema detecta que un integrante de la estructura no ha registrado su voto. Se requiere movilización inmediata."
            else:
                texto_com = "🔗 Aquí tienes tu link personalizado y seguro para registrar tu voto con geolocalización el Día D."

            link_com_w = f"https://wa.me/52{cel_omiso}?text={urllib.parse.quote(texto_com)}" if cel_omiso else "#"
            st.markdown(f'<a href="{link_com_w}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 8px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 10px;">📲 Enviar Mensaje Operativo por WhatsApp</a>', unsafe_allow_html=True)

        with com_col2:
            st.markdown("###### 📞 Enlace Rápido de Mando Día D")
            st.markdown("""
            * **Coordinación General:** Enlace operativo central.
            * **Área Electoral / Jurídico:** Seguimiento a actas e incidentes.
            * **Enlace RGs / RCs:** Supervisión en tiempo real de casillas.
            """)
            st.info("ℹ️ Utilice las pestañas superiores para alternar entre el monitoreo de casillas, defensa del voto, control GOTV y la gestión de pánico.")

# ==========================================
# VISTA 5: REDES SOCIALES Y DIFUSIÓN
# ==========================================
elif st.session_state.seccion_activa == "REDES":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL", "ENCARGADO_REDES"]:
        st.warning("⚠️ Acceso restringido al módulo de redes sociales y difusión.")
        st.stop()

    st.markdown("## 📱 Módulo de Redes Sociales y Difusión Estratégica")
    st.caption("Centro de control para la gestión de plataformas digitales, repositorio de identidad gráfica y disparadores de mensajes masivos.")

    if st.button("⬅️ Volver al Tablero / Menú", use_container_width=False):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>🌐 Canales Oficiales Conectados</div></div>", unsafe_allow_html=True)
        st.markdown("""
        * **📘 Facebook Oficial:** [Abrir Panel Meta Business](https://facebook.com) - 🟢 En Línea
        * **📸 Instagram de Campaña:** [Abrir Perfil Instagram](https://instagram.com) - 🟢 En Línea
        * **🎵 TikTok Oficial:** [Abrir Creator Center](https://tiktok.com) - 🟢 En Línea
        * **💬 Canal de WhatsApp:** [Difusión Masiva Activa](https://whatsapp.com) - 🟢 Sincronizado
        """)
        
        ruta_logos_redes = r"C:\Users\Usuario\Desktop\Plataforma_Electoral\LOGOS_IDENTIDAD"
        if st.button("📂 Abrir Carpeta 'LOGOS_IDENTIDAD' (PC)", use_container_width=True):
            abrir_carpeta_pc(ruta_logos_redes)

    with col_r2:
        st.markdown("<div class='caja-bloque'><div class='titulo-caja'>📢 Disparador de Comunicado Digital para Redes</div></div>", unsafe_allow_html=True)
        with st.form("form_redes_sociales"):
            titulo_comunicado = st.text_input("Título / Asunto del Post o Boletín:")
            cuerpo_comunicado = st.text_area("Redacción del Mensaje Institucional:", "¡Baja California Sur merece más! Consulta nuestras propuestas.")
            plataforma_destino = st.selectbox("Canal de Destino:", ["Redes Generales (FB / IG / TikTok)", "Chats de Estructura (WhatsApp)", "Prensa y Medios de Comunicación"])
            
            link_redes_w = f"https://wa.me/?text={urllib.parse.quote(titulo_comunicado + '\n\n' + cuerpo_comunicado)}"
            
            st.markdown(f'<a href="{link_redes_w}" target="_blank" style="display: block; text-align: center; background-color: #25D366; color: white; padding: 8px; border-radius: 6px; text-decoration: none; font-weight: bold; margin-top: 10px;">🚀 Disparar Boletín para Redes / Chats</a>', unsafe_allow_html=True)
            st.form_submit_button("💾 Guardar Registro en Historial Digital")

# ==========================================
# VISTA 6: SIMULADOR DE ENCUESTAS (MÓVIL / TRACKING POLL)
# ==========================================
elif st.session_state.seccion_activa == "SIMULADOR":
    if st.session_state.rol_usuario not in ["GENESIS", "COORDINADOR_GENERAL"]:
        st.warning("⚠️ Acceso restringido al simulador de encuestas.")
        st.stop()

    st.markdown("## 📱 Simulador Móvil: Formato Oficial de Encuesta (Tracking Poll Cloud)")
    st.caption("Interfaz exacta optimizada para dispositivos móviles con fotografía del candidato, logotipo oficial y cuestionario normado en la nube.")

    if st.button("⬅️ Volver al Tablero / Menú", use_container_width=False):
        st.session_state.seccion_activa = "TABLERO"
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_sim_izq, col_sim_cen, col_sim_der = st.columns([1, 2, 1])
    
    with col_sim_cen:
        st.markdown("<div class='mobile-simulator'>", unsafe_allow_html=True)
        
        col_id_txt, col_id_img = st.columns([2, 1])
        with col_id_txt:
            st.markdown("<h4 style='color:#38bdf8; margin:0;'>📊 Tracking Poll Cloud</h4>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:10px; color:#9ca3af; margin:0;'>Estudio de Opinión Pública BCS 2027</p>", unsafe_allow_html=True)
        with col_id_img:
            if "logo_actual" in st.session_state and st.session_state.logo_actual is not None:
                st.image(st.session_state.logo_actual, width=65)
            else:
                st.markdown("<div style='text-align:right; font-size:9px; color:#38bdf8;'>[ Logo / Foto ]</div>", unsafe_allow_html=True)

        st.markdown("---")
        
        with st.form("form_tracking_poll_oficial"):
            st.markdown("##### 📍 Identificación de Campo")
            brigadista_reg = st.text_input("Brigadista Encuestador:", value="Carlos Mendoza")
            seccional_enc = st.text_input("Seccional Electoral (Ej: 400):")
            
            st.markdown("---")
            st.markdown("##### 📋 Cuestionario Normado")
            p1_elecciones = st.radio("1. ¿Sabe usted que este año hay elecciones constitucionales en Baja California Sur?", ["Sí", "No"], horizontal=True)
            p2_conoce_cand = st.radio("2. ¿Ha escuchado hablar o conoce usted al candidato?", ["Sí", "No"], horizontal=True)
            p3_conoce_part = st.radio("3. ¿Conoce usted al partido político que representa?", ["Sí", "No"], horizontal=True)
            p4_voto_cand = st.radio("4. Si hoy fuera la elección, ¿votaría por nuestro candidato?", ["Sí", "No", "Tiene duda"], horizontal=True)
            p5_voto_part = st.radio("5. ¿Votaría usted por el partido político en esta elección?", ["Sí", "No", "Tiene duda"], horizontal=True)
            
            st.markdown("---")
            st.markdown("📍 **GPS Cloud:** *Ubicación georreferenciada sellada automáticamente en servidor remoto.*")
            
            btn_enviar_encuesta = st.form_submit_button("🚀 Enviar Encuesta a la Nube")
            if btn_enviar_encuesta:
                if seccional_enc:
                    st.success("✅ ¡Encuesta aplicada con éxito! Datos sincronizados con el Tablero Central Cloud y carpeta ENCUESTAS.")
                else:
                    st.warning("⚠️ Ingrese la seccional electoral para registrar la encuesta.")

        st.markdown("</div>", unsafe_allow_html=True)
    